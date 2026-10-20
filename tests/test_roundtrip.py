"""Ida y vuelta (codificar -> decodificar) con datos sintéticos y archivos reales.

Los archivos reales dejan sus resultados en sim/codificacion y sim/decodificacion
y registran las métricas en el log (insumo para las tablas del reporte).
"""
import os
import random
import unittest

import huffman_codificador as cod
import huffman_decodificador as dec
from tests.base import (ARCHIVOS_REALES, DIR_DATA, DIR_SIM_COD, DIR_SIM_DEC, LOG,
                        LoggedTestCase)


class TestContratoEntreScripts(LoggedTestCase):
    def test_constantes_coinciden(self):
        """Sufijos de archivos idénticos en codificador y decodificador (SSOT del contrato)."""
        self.verificar("sufijo .huffman", dec.SUFIJO_HUFFMAN, cod.SUFIJO_HUFFMAN)
        self.verificar("sufijo diccionario", dec.SUFIJO_DICCIONARIO, cod.SUFIJO_DICCIONARIO)


class TestRoundtripSintetico(LoggedTestCase):
    def _roundtrip(self, contenido):
        entrada = self.escribir_temporal("dato.bin", contenido)
        r = cod.procesar(entrada, self.directorio_temporal())
        d = dec.procesar(r["file_huffman_comprimido"], self.directorio_temporal(), entrada)
        with open(d["recovered_path"], "rb") as f:
            recuperado = f.read()
        return r, d, recuperado

    def test_texto_ascii(self):
        """Texto repetido: recuperado idéntico y compresión > 1."""
        contenido = b"Teoria de la Informacion y codigos de Huffman. " * 40
        r, d, rec = self._roundtrip(contenido)
        self.verificar("recuperado == original", rec, contenido)
        self.verificar("coincide (decodificador)", d["coincide"], True)
        self.verificar_cierto("tasa > 1", r["tamanos"]["tasa"] > 1, "tasa=%.3f" % r["tamanos"]["tasa"])

    def test_bytes_aleatorios(self):
        """Bytes pseudoaleatorios (semilla fija) se recuperan idénticos."""
        rng = random.Random(1234)
        contenido = bytes(rng.randrange(256) for _ in range(5000))
        r, d, rec = self._roundtrip(contenido)
        self.verificar("recuperado == original", rec, contenido)
        self.verificar("SHA-256 igual", d["sha256_recuperado"], d["sha256_original"])

    def test_distribucion_sesgada(self):
        """Distribución muy sesgada: Huffman comprime cerca del límite teórico."""
        rng = random.Random(7)
        contenido = bytes(rng.choices(range(8), weights=[64, 32, 16, 8, 4, 2, 1, 1], k=4000))
        r, d, rec = self._roundtrip(contenido)
        self.verificar("recuperado == original", rec, contenido)
        m = r["metricas"]
        self.verificar_cierto("H <= L < H+1", m["H"] <= m["L"] + 1e-12 and m["L"] < m["H"] + 1,
                              "H=%.4f L=%.4f" % (m["H"], m["L"]))

    def test_comprimido_no_supera_limite_teorico_mas_un_bit_por_simbolo(self):
        """Bits útiles <= N*(H+1) (cota de Huffman)."""
        contenido = b"abcabcabcaabbbbcccddddddddeeeeeeeeeeeeeeee" * 10
        r, d, rec = self._roundtrip(contenido)
        cota = r["N"] * (r["metricas"]["H"] + 1)
        self.verificar_cierto("bits <= N*(H+1)", r["bits_utiles"] <= cota,
                              "bits=%d cota=%.1f" % (r["bits_utiles"], cota))


class TestRoundtripArchivosReales(LoggedTestCase):
    def test_archivos_del_instructivo(self):
        """Codifica y decodifica cada archivo real; recuperado == original bit a bit."""
        filas = []
        for subcarpeta, nombre in ARCHIVOS_REALES:
            ruta = os.path.join(DIR_DATA, subcarpeta, nombre)
            with self.subTest(archivo=nombre):
                if not os.path.isfile(ruta):
                    LOG.warning("    [SKIP] %s no está en data/%s/", nombre, subcarpeta)
                    continue
                r = cod.procesar(ruta, DIR_SIM_COD)
                self.assertIsNotNone(r, "%s está vacío" % nombre)
                d = dec.procesar(r["file_huffman_comprimido"], DIR_SIM_DEC, ruta)
                m, t = r["metricas"], r["tamanos"]
                LOG.info("    %-20s N=%-8d M=%-3d H=%.4f L=%.4f var=%.4f "
                         "eta_orig=%.2f%% eta_huff=%.2f%% | comp=%d dicc=%d tasa=%.4f ahorro=%.2f%% | %s",
                         nombre, r["N"], m["M"], m["H"], m["L"], m["var"],
                         100 * m["eta_original"], 100 * m["eta_huffman"],
                         t["comprimido"], t["diccionario"], t["tasa"], t["ahorro"],
                         "COINCIDE" if d["coincide"] else "NO COINCIDE")
                self.verificar("%s: recuperado == original" % nombre, d["coincide"], True)
                self.verificar("%s: tamaño recuperado" % nombre, d["tam_recuperado"], r["N"])
                if m["M"] > 1:  # con un solo símbolo L=1 está forzado y H=0
                    self.verificar_cierto("%s: H <= L < H+1" % nombre,
                                          (m["H"] <= m["L"] + 1e-9 and m["L"] < m["H"] + 1),
                                          "H=%.4f L=%.4f" % (m["H"], m["L"]))
                else:
                    self.verificar("%s: caso un símbolo, L forzado" % nombre, m["L"], 1.0)
                filas.append(nombre)
        if not filas:
            self.skipTest("No hay archivos reales en data/")
        LOG.info("    archivos procesados: %d de %d", len(filas), len(ARCHIVOS_REALES))


if __name__ == "__main__":
    unittest.main()
