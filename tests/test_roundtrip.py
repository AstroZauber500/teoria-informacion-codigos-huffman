"""Ida y vuelta (codificar -> decodificar) con datos sintéticos y archivos reales.

Los archivos reales dejan sus resultados en sim/codificacion y sim/decodificacion
y registran las métricas en el log (insumo para las tablas del reporte).
"""
import os
import random
import shutil
import unittest

import huffman_decodificador as dec
from tests.base import (ARCHIVOS_REALES, DIR_DATA, DIR_SIM_COD, DIR_SIM_DEC, LOG,
                        LoggedTestCase, ejecutar_codificador, parsear_salida)


class TestContratoEntreScripts(LoggedTestCase):
    def test_nombres_de_salida_coinciden(self):
        """El codificador genera <x>.huffman/.diccionario.csv y el decodificador deriva esos nombres."""
        _, ruta, _ = self.codificar("contrato.bin", b"abcabc", "-q")
        csv_path, recovered = dec.rutas_derivadas(ruta + ".huffman", "salida")
        self.verificar("diccionario derivado", csv_path, ruta + ".diccionario.csv")
        self.verificar_cierto("el diccionario derivado existe", os.path.isfile(csv_path))
        self.verificar("recovered_path", recovered, os.path.join("salida", "recovered_contrato.bin"))


class TestRoundtripSintetico(LoggedTestCase):
    def _roundtrip(self, contenido):
        proc, ruta, m = self.codificar("dato.bin", contenido, "-q")
        d = dec.procesar(ruta + ".huffman", self.directorio_temporal(), ruta)
        with open(d["recovered_path"], "rb") as f:
            recuperado = f.read()
        return m, d, recuperado

    def test_texto_ascii(self):
        """Texto repetido: recuperado idéntico y compresión > 1."""
        contenido = b"Teoria de la Informacion y codigos de Huffman. " * 40
        m, d, rec = self._roundtrip(contenido)
        self.verificar("recuperado == original", rec, contenido)
        self.verificar("coincide (decodificador)", d["coincide"], True)
        self.verificar_cierto("tasa > 1", m["tasa"] > 1, "tasa=%.4f" % m["tasa"])

    def test_bytes_aleatorios(self):
        """Bytes pseudoaleatorios (semilla fija) se recuperan idénticos."""
        rng = random.Random(1234)
        contenido = bytes(rng.randrange(256) for _ in range(5000))
        m, d, rec = self._roundtrip(contenido)
        self.verificar("recuperado == original", rec, contenido)
        self.verificar("SHA-256 igual", d["sha256_recuperado"], d["sha256_original"])

    def test_distribucion_sesgada(self):
        """Distribución sesgada: H <= L < H+1 y recuperación exacta."""
        rng = random.Random(7)
        contenido = bytes(rng.choices(range(8), weights=[64, 32, 16, 8, 4, 2, 1, 1], k=4000))
        m, d, rec = self._roundtrip(contenido)
        self.verificar("recuperado == original", rec, contenido)
        self.verificar_cierto("H <= L < H+1", m["H"] <= m["L"] + 5e-6 and m["L"] < m["H"] + 1,
                              "H=%.6f L=%.6f" % (m["H"], m["L"]))

    def test_bits_no_superan_cota_de_huffman(self):
        """Bits útiles <= N*(H+1)."""
        contenido = b"abcabcabcaabbbbcccddddddddeeeeeeeeeeeeeeee" * 10
        m, d, rec = self._roundtrip(contenido)
        cota = m["N"] * (m["H"] + 1)
        self.verificar_cierto("bits <= N*(H+1)", m["bits_utiles"] <= cota,
                              "bits=%d cota=%.1f" % (m["bits_utiles"], cota))


class TestRoundtripArchivosReales(LoggedTestCase):
    def test_archivos_del_instructivo(self):
        """Codifica y decodifica cada archivo real; recuperado == original bit a bit.

        El codificador deja sus salidas junto a la entrada, así que cada archivo se
        copia a sim/codificacion/, se codifica ahí y se borra la copia (quedan solo
        el .huffman y el .diccionario.csv). Lo recuperado va a sim/decodificacion/.
        """
        os.makedirs(DIR_SIM_COD, exist_ok=True)
        procesados = 0
        for subcarpeta, nombre in ARCHIVOS_REALES:
            ruta = os.path.join(DIR_DATA, subcarpeta, nombre)
            with self.subTest(archivo=nombre):
                if not os.path.isfile(ruta):
                    LOG.warning("    [SKIP] %s no está en data/%s/", nombre, subcarpeta)
                    continue
                copia = os.path.join(DIR_SIM_COD, nombre)
                shutil.copyfile(ruta, copia)
                try:
                    proc = ejecutar_codificador(copia, "-q")
                finally:
                    os.remove(copia)
                self.verificar("%s: código de salida del codificador" % nombre, proc.returncode, 0)
                m = parsear_salida(proc.stdout)
                d = dec.procesar(copia + ".huffman", DIR_SIM_DEC, ruta)
                LOG.info("    %-20s N=%-8d M=%-3d H=%.6f L=%.6f var=%.6f eta_orig=%.4f%% "
                         "eta_huff=%.4f%% | comp=%d dicc=%d tasa=%.4f tasa_total=%.4f ahorro=%.2f%% | %s",
                         nombre, m["N"], m["M"], m["H"], m["L"], m["var"],
                         m["eta_original_pct"], m["eta_huffman_pct"], m["comprimido"],
                         m["diccionario"], m["tasa"], m["tasa_total"], m["ahorro_pct"],
                         "COINCIDE" if d["coincide"] else "NO COINCIDE")
                self.verificar("%s: recuperado == original" % nombre, d["coincide"], True)
                self.verificar("%s: tamaño recuperado" % nombre, d["tam_recuperado"], int(m["N"]))
                if m["M"] > 1:  # con un solo símbolo L=1 está forzado y H=0
                    self.verificar_cierto("%s: H <= L < H+1" % nombre,
                                          m["H"] <= m["L"] + 5e-6 and m["L"] < m["H"] + 1,
                                          "H=%.6f L=%.6f" % (m["H"], m["L"]))
                else:
                    self.verificar("%s: caso un símbolo, L forzado" % nombre, m["L"], 1.0)
                procesados += 1
        if procesados == 0:
            self.skipTest("No hay archivos reales en data/")
        LOG.info("    archivos procesados: %d de %d", procesados, len(ARCHIVOS_REALES))


if __name__ == "__main__":
    unittest.main()
