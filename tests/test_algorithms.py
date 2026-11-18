"""Pruebas automatizadas (unittest; tambien compatibles con pytest)."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import redirect_stdout
from io import StringIO

from src.algorithms.approximate import best_fit_decreasing, first_fit_decreasing
from src.algorithms.exact import bin_packing_exacto
from src.generator import generar_instancia
from src.main import main
from src.validation import validate_solution
from src.upload_to_ec2 import plan_files, remote_free_bytes, remote_sha256


class TestBinPacking(unittest.TestCase):
    def test_instancia_basica(self):
        archivos, capacidad = [4, 3, 2.5, 2, 1.5, 1], 5
        for algoritmo in (first_fit_decreasing, best_fit_decreasing, bin_packing_exacto):
            with self.subTest(algoritmo=algoritmo.__name__):
                solucion = algoritmo(archivos, capacidad)
                self.assertEqual(len(solucion), 3)
                self.assertTrue(validate_solution(archivos, capacidad, solucion)[0])

    def test_vacio_y_archivo_igual_a_capacidad(self):
        for algoritmo in (first_fit_decreasing, best_fit_decreasing, bin_packing_exacto):
            with self.subTest(algoritmo=algoritmo.__name__):
                self.assertEqual(algoritmo([], 10), [])
                self.assertEqual(algoritmo([10, 10], 10), [[10], [10]])

    def test_referencia_manual_y_caso_adverso(self):
        archivos = [6, 6, 6, 4, 4, 4]  # suma=30, C=10: optimo manual de 3 discos
        exacta = bin_packing_exacto(archivos, 10)
        self.assertEqual(len(exacta), 3)
        for algoritmo in (first_fit_decreasing, best_fit_decreasing):
            solucion = algoritmo(archivos, 10)
            self.assertGreaterEqual(len(solucion), len(exacta))
            self.assertTrue(validate_solution(archivos, 10, solucion)[0])

    def test_desbalanceado(self):
        archivos = [9, 8, 7, 6, 5, 4, 3, 2, 1]
        for algoritmo in (first_fit_decreasing, best_fit_decreasing, bin_packing_exacto):
            self.assertTrue(validate_solution(archivos, 10, algoritmo(archivos, 10))[0])

    def test_rechaza_entradas_invalidas(self):
        for archivos, capacidad in (([11], 10), ([0], 10), ([-1], 10), ([1], 0), ([float("nan")], 10)):
            with self.subTest(archivos=archivos, capacidad=capacidad):
                with self.assertRaises(ValueError):
                    first_fit_decreasing(archivos, capacidad)

    def test_limite_de_exactos(self):
        with self.assertRaisesRegex(ValueError, "hasta 2 archivos"):
            bin_packing_exacto([1, 1, 1], 2, max_items=2)

    def test_timeout_exacto(self):
        with self.assertRaises(TimeoutError):
            bin_packing_exacto([6, 6, 4, 4], 10, timeout_s=1e-15)
        with self.assertRaises(ValueError):
            bin_packing_exacto([1], 2, timeout_s=0)

    def test_plan_transferencia_con_tamanos_repetidos(self):
        with TemporaryDirectory() as folder:
            source = Path(folder)
            for name, size in (("a.dat", 6), ("b.dat", 6), ("c.dat", 4), ("d.dat", 4)):
                (source / name).write_bytes(b"x" * size)
            bins = plan_files(source, 10, "ffd")
            self.assertEqual(len(bins), 2)
            self.assertEqual(sorted(path.name for disk in bins for path in disk), ["a.dat", "b.dat", "c.dat", "d.dat"])
            self.assertTrue(all(sum(path.stat().st_size for path in disk) <= 10 for disk in bins))

    def test_espacio_remoto_exige_montaje(self):
        class Stream:
            def __init__(self, status, data=b""):
                self.status, self.data, self.channel = status, data, self

            def recv_exit_status(self):
                return self.status

            def read(self):
                return self.data

        class Client:
            def __init__(self, mounted):
                self.mounted = mounted

            def exec_command(self, command, timeout):
                if command.startswith("mountpoint"):
                    return None, Stream(0 if self.mounted else 1), Stream(0)
                return None, Stream(0, b"100 4096\n"), Stream(0)

        self.assertEqual(remote_free_bytes(Client(True), "/disco1"), 409600)
        with self.assertRaisesRegex(ValueError, "no es un disco montado"):
            remote_free_bytes(Client(False), "/disco1")

    def test_hash_remoto_se_consulta_en_servidor(self):
        class Stream:
            channel = None

            def __init__(self):
                self.channel = self

            def recv_exit_status(self):
                return 0

            def read(self):
                return ("a" * 64 + "  /disco1/archivo.bin\n").encode()

        class Client:
            def exec_command(self, command, timeout):
                self.command = command
                return None, Stream(), Stream()

        client = Client()
        self.assertEqual(remote_sha256(client, "/disco1/archivo.bin"), "a" * 64)
        self.assertIn("sha256sum", client.command)

    def test_generador_reproducible(self):
        self.assertEqual(generar_instancia(20, 100, 7), generar_instancia(20, 100, 7))
        self.assertTrue(all(1 <= x <= 50 for x in generar_instancia(20, 100, 7)))
        self.assertEqual(generar_instancia(0, 1), [])

    def test_cli_compara_alternativas(self):
        salida = StringIO()
        with redirect_stdout(salida):
            codigo = main(["--files", "4,3,2.5,2,1.5,1", "--capacity", "5", "--algorithm", "compare"])
        self.assertEqual(codigo, 0)
        texto = salida.getvalue()
        self.assertIn("FFD | discos: 3", texto)
        self.assertIn("BFD | discos: 3", texto)
        self.assertIn("EXACT | discos: 3", texto)
        self.assertIn("Validacion: OK", texto)

    def test_cli_genera_instancia(self):
        salida = StringIO()
        with redirect_stdout(salida):
            codigo = main(["--generate", "8", "--capacity", "10", "--seed", "7", "--algorithm", "compare"])
        self.assertEqual(codigo, 0)
        self.assertIn("Instancia: archivos=", salida.getvalue())
        self.assertIn("Validacion: OK", salida.getvalue())

    def test_cli_carga_json(self):
        salida = StringIO()
        with redirect_stdout(salida):
            codigo = main(["--instance", "data/instances/instancia_pequena.json", "--algorithm", "exact"])
        self.assertEqual(codigo, 0)
        self.assertIn("EXACT | discos: 2", salida.getvalue())


if __name__ == "__main__":
    unittest.main()
