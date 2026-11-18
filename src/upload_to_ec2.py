"""Distribuye archivos locales en carpetas montadas de EC2 mediante SFTP."""
import argparse
import hashlib
from collections import defaultdict, deque
from pathlib import Path
import posixpath
import shlex
import stat
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.algorithms.approximate import best_fit_decreasing, first_fit_decreasing
from src.algorithms.exact import bin_packing_exacto

ALGORITHMS = {"ffd": first_fit_decreasing, "bfd": best_fit_decreasing, "exact": bin_packing_exacto}
MIB = 1024 * 1024


def plan_files(source, capacity_bytes, algorithm):
    files = sorted(p for p in source.iterdir() if p.is_file())
    if not files:
        raise ValueError("La carpeta de origen no contiene archivos")
    sizes = [p.stat().st_size for p in files]
    if any(size == 0 for size in sizes):
        raise ValueError("Los archivos vacios no son admitidos por el modelo")
    solution = ALGORITHMS[algorithm](sizes, capacity_bytes)
    by_size = defaultdict(deque)
    for path, size in zip(files, sizes):
        by_size[size].append(path)
    return [[by_size[size].popleft() for size in bin_sizes] for bin_sizes in solution]


def digest(stream):
    result = hashlib.sha256()
    while True:
        block = stream.read(MIB)
        if not block:
            return result.hexdigest()
        result.update(block)


def remote_sha256(client, path):
    """Calcula SHA-256 en el servidor sin descargar otra vez el archivo."""
    _, stdout, stderr = client.exec_command(f"sha256sum -- {shlex.quote(path)}", timeout=15)
    if stdout.channel.recv_exit_status() != 0:
        raise OSError(f"No se pudo verificar {path}: {stderr.read().decode(errors='replace')}")
    result = stdout.read().decode(errors="replace").split()
    if not result or len(result[0]) != 64:
        raise OSError(f"SHA-256 remoto inválido para {path}")
    return result[0]


def upload_verified(client, sftp, source, destination):
    temporary = destination + ".part-" + uuid4().hex
    local_hash = hashlib.sha256()
    transferred = 0
    next_report = 50 * MIB
    try:
        with source.open("rb") as local, sftp.open(temporary, "wb") as remote:
            while True:
                block = local.read(MIB)
                if not block:
                    break
                remote.write(block)
                local_hash.update(block)
                transferred += len(block)
                if transferred >= next_report:
                    print(f"  {source.name}: {transferred / MIB:.0f} MiB enviados", flush=True)
                    next_report += 50 * MIB
        if sftp.stat(temporary).st_size != source.stat().st_size:
            raise IOError(f"Tamaño incorrecto tras transferir {source.name}")
        print(f"  {source.name}: verificando SHA-256 en EC2...", flush=True)
        if remote_sha256(client, temporary) != local_hash.hexdigest():
            raise IOError(f"SHA-256 incorrecto tras transferir {source.name}")
        sftp.rename(temporary, destination)
    except BaseException:
        try:
            sftp.remove(temporary)
        except OSError:
            pass
        raise


def remote_free_bytes(client, directory):
    """Consulta por SSH el espacio escribible en un punto de montaje Ubuntu."""
    quoted = shlex.quote(directory)
    _, stdout, stderr = client.exec_command(f"mountpoint -q -- {quoted}", timeout=15)
    if stdout.channel.recv_exit_status() != 0:
        raise ValueError(f"La carpeta no es un disco montado: {directory}")
    _, stdout, stderr = client.exec_command(f"stat -f -c '%a %S' -- {quoted}", timeout=15)
    if stdout.channel.recv_exit_status() != 0:
        raise OSError(f"No se pudo consultar el espacio de {directory}: {stderr.read().decode(errors='replace')}")
    try:
        blocks, block_size = map(int, stdout.read().decode().split())
    except ValueError:
        raise OSError(f"Respuesta de espacio inválida para {directory}") from None
    return blocks * block_size


def main(argv=None):
    parser = argparse.ArgumentParser(description="Asigna archivos locales y los sube a carpetas montadas en EC2")
    parser.add_argument("--source", type=Path, required=True, help="carpeta local de archivos (solo nivel superior)")
    parser.add_argument("--capacity-mib", type=int, required=True, help="capacidad lógica por carpeta en MiB")
    parser.add_argument("--algorithm", choices=ALGORITHMS, default="ffd")
    parser.add_argument("--remote-dir", action="append", required=True, help="ruta absoluta de un disco montado; repetir")
    parser.add_argument("--plan-only", action="store_true", help="mostrar asignación sin conectar ni transferir")
    parser.add_argument("--host", help="IP pública o DNS de EC2")
    parser.add_argument("--user", default="ubuntu")
    parser.add_argument("--key", type=Path, help="clave privada SSH local")
    parser.add_argument("--port", type=int, default=22)
    args = parser.parse_args(argv)
    try:
        if not args.source.is_dir() or args.capacity_mib <= 0:
            raise ValueError("El origen debe existir y la capacidad debe ser positiva")
        if len(set(args.remote_dir)) != len(args.remote_dir) or any(not p.startswith("/") for p in args.remote_dir):
            raise ValueError("Las carpetas remotas deben ser rutas absolutas distintas")
        bins = plan_files(args.source, args.capacity_mib * MIB, args.algorithm)
        if len(bins) > len(args.remote_dir):
            raise ValueError(f"Se necesitan {len(bins)} carpetas; se indicaron {len(args.remote_dir)}")
        for i, files in enumerate(bins):
            print(f"Disco {i + 1}: {args.remote_dir[i]}: " + ", ".join(p.name for p in files) +
                  f" ({sum(p.stat().st_size for p in files) / MIB:.2f} MiB)")
        if args.plan_only:
            return 0
        if not args.host or not args.key or not args.key.is_file():
            raise ValueError("Para transferir se requieren --host y --key válida")
        try:
            import paramiko
        except ImportError:
            raise ValueError("Instala Paramiko: python -m pip install paramiko") from None
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        try:
            client.connect(args.host, port=args.port, username=args.user, key_filename=str(args.key),
                           look_for_keys=False, allow_agent=False, timeout=15)
            with client.open_sftp() as sftp:
                for directory, files in zip(args.remote_dir, bins):
                    attrs = sftp.stat(directory)
                    if not stat.S_ISDIR(attrs.st_mode):
                        raise ValueError(f"No es una carpeta remota: {directory}")
                    free = remote_free_bytes(client, directory)
                    needed = sum(p.stat().st_size for p in files)
                    if needed > free:
                        raise ValueError(f"Espacio insuficiente en {directory}: necesita {needed}, libre {free} bytes")
                    for path in files:
                        target = posixpath.join(directory, path.name)
                        try:
                            sftp.stat(target)
                        except FileNotFoundError:
                            pass
                        else:
                            raise ValueError(f"Ya existe {target}; no se sobrescribirá")
                for directory, files in zip(args.remote_dir, bins):
                    for path in files:
                        target = posixpath.join(directory, path.name)
                        upload_verified(client, sftp, path, target)
                        print(f"OK: {path.name} -> {target} (SHA-256 verificado)")
        finally:
            client.close()
        return 0
    except (ValueError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    sys.exit(main())
