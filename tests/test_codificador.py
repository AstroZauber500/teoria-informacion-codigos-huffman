"""Pruebas unitarias de huffman_codificador.py (instructivo 2.2.5, 2.3)."""
import csv
import math
import os
import unittest

import huffman_codificador as cod
from tests.base import LoggedTestCase


def es_libre_de_prefijos(codigos):
    lista = list(codigos.values())
    return not any(a != b and b.startswith(a) for a in lista for b in lista)


class TestFrecuencias(LoggedTestCase):
    def test_probabilidades_ordenadas(self):
        """contar_frecuencias devuelve probabilidades en orden descendente."""
        freq = cod.contar_frecuencias([1, 1, 1, 2, 2, 3])
        self.verificar("símbolos en orden", [s for s, _ in freq], [1, 2, 3])
        self.verificar("P(1)", freq[0][1], 3 / 6, tol=1e-12)
        self.verificar("P(2)", freq[1][1], 2 / 6, tol=1e-12)
        self.verificar("suma de probabilidades", sum(p for _, p in freq), 1.0, tol=1e-12)


class TestArbolYCodigos(LoggedTestCase):
    def test_longitudes_distribucion_diadica(self):
        """P=(.5,.25,.25) produce longitudes (1,2,2)."""
        freq = [(10, 0.5), (20, 0.25), (30, 0.25)]
        codigos = cod.generar_codigos(cod.construir_arbol(freq))
        longitudes = sorted(len(c) for c in codigos.values())
        self.verificar("longitudes de código", longitudes, [1, 2, 2])
        self.verificar("el símbolo más probable tiene 1 bit", len(codigos[10]), 1)

    def test_codigo_libre_de_prefijos(self):
        """Ningún código es prefijo de otro (decodificable de forma única)."""
        freq = cod.contar_frecuencias(list(b"abracadabra alakazam"))
        codigos = cod.generar_codigos(cod.construir_arbol(freq))
        self.verificar_cierto("libre de prefijos", es_libre_de_prefijos(codigos), str(codigos))

    def test_desigualdad_de_kraft(self):
        """La suma de 2^-longitud es 1 (árbol completo)."""
        freq = cod.contar_frecuencias(list(b"mississippi river"))
        codigos = cod.generar_codigos(cod.construir_arbol(freq))
        kraft = sum(2 ** -len(c) for c in codigos.values())
        self.verificar("suma de Kraft", kraft, 1.0, tol=1e-12)

    def test_uniforme_cuatro_simbolos(self):
        """4 símbolos equiprobables -> todos con 2 bits."""
        freq = cod.contar_frecuencias([0, 1, 2, 3] * 5)
        codigos = cod.generar_codigos(cod.construir_arbol(freq))
        self.verificar("longitudes", sorted(len(c) for c in codigos.values()), [2, 2, 2, 2])

    def test_un_simbolo_fuerza_codigo_cero(self):
        """Un solo símbolo: el código vacío se reemplaza por '0'."""
        codigos = cod.generar_codigos(cod.construir_arbol([(65, 1.0)]))
        self.verificar("diccionario", codigos, {65: '0'})


class TestMetricas(LoggedTestCase):
    def test_metricas_distribucion_diadica(self):
        """P=(.5,.25,.25): H=1.5, L=1.5, var=0.25, eficiencia Huffman 100%."""
        freq = [(10, 0.5), (20, 0.25), (30, 0.25)]
        codigos = cod.generar_codigos(cod.construir_arbol(freq))
        m = cod.calcular_metricas(freq, codigos)
        self.verificar("H", m["H"], 1.5, tol=1e-12)
        self.verificar("L", m["L"], 1.5, tol=1e-12)
        self.verificar("varianza", m["var"], 0.25, tol=1e-12)
        self.verificar("eficiencia Huffman H/L", m["eta_huffman"], 1.0, tol=1e-12)
        self.verificar("eficiencia original H/8", m["eta_original"], 1.5 / 8, tol=1e-12)
        self.verificar("H máxima log2(3)", m["H_max"], math.log2(3), tol=1e-12)

    def test_cota_de_shannon(self):
        """Teoría: H <= L < H + 1 y eficiencia <= 100%."""
        datos = list(b"the quick brown fox jumps over the lazy dog " * 7)
        freq = cod.contar_frecuencias(datos)
        codigos = cod.generar_codigos(cod.construir_arbol(freq))
        m = cod.calcular_metricas(freq, codigos)
        self.verificar_cierto("H <= L", m["H"] <= m["L"] + 1e-12, "H=%.4f L=%.4f" % (m["H"], m["L"]))
        self.verificar_cierto("L < H + 1", m["L"] < m["H"] + 1)
        self.verificar_cierto("eficiencia <= 1", m["eta_huffman"] <= 1 + 1e-12)
        self.verificar_cierto("varianza >= 0", m["var"] >= 0)

    def test_uniforme_26_simbolos(self):
        """26 símbolos equiprobables (solo_abc): H = log2(26)."""
        freq = cod.contar_frecuencias(list(range(65, 91)) * 100)
        codigos = cod.generar_codigos(cod.construir_arbol(freq))
        m = cod.calcular_metricas(freq, codigos)
        self.verificar("H", m["H"], math.log2(26), tol=1e-9)
        self.verificar("H = H_max", m["H"], m["H_max"], tol=1e-9)
        self.verificar("longitudes posibles", sorted(set(len(c) for c in codigos.values())), [4, 5])

    def test_un_simbolo_sin_nan_en_entropia(self):
        """Un símbolo: H=0, L=1, eficiencia 0 (no NaN ni división por cero)."""
        freq = [(0, 1.0)]
        m = cod.calcular_metricas(freq, {0: '0'})
        self.verificar("H", m["H"], 0.0)
        self.verificar("L", m["L"], 1.0)
        self.verificar("eficiencia Huffman", m["eta_huffman"], 0.0)
        self.verificar("H_max", m["H_max"], 0.0)


class TestBitsYBytes(LoggedTestCase):
    def test_padding_tres_bits(self):
        """'101' se rellena a '10100000' = 0xA0."""
        self.verificar("bytes", cod.bits_a_bytes("101"), b"\xa0")

    def test_sin_padding_multiplo_de_8(self):
        """8 bits no agregan relleno."""
        self.verificar("bytes", cod.bits_a_bytes("11111111"), b"\xff")

    def test_nueve_bits_dos_bytes(self):
        """9 bits -> 2 bytes (relleno de 7 ceros)."""
        self.verificar("bytes", cod.bits_a_bytes("111111111"), b"\xff\x80")

    def test_codificar_a_bits(self):
        """Concatena los códigos en el orden de los datos."""
        self.verificar("bits", cod.codificar_a_bits([1, 2, 1, 3], {1: '0', 2: '10', 3: '11'}),
                       "010011")


class TestDiccionarioCSV(LoggedTestCase):
    def test_formato_csv(self):
        """Primera fila 'bits_útiles,bits' y luego 'símbolo,código'."""
        ruta = os.path.join(self.directorio_temporal(), "d.csv")
        cod.escribir_diccionario(ruta, 11, {65: '0', 66: '10', 67: '11'})
        with open(ruta, newline='') as f:
            filas = list(csv.reader(f))
        self.verificar("primera fila", filas[0], ["11", "bits"])
        self.verificar("resto de filas", filas[1:], [["65", "0"], ["66", "10"], ["67", "11"]])


class TestTamanos(LoggedTestCase):
    def test_tasa_y_ahorro(self):
        """1000 bytes -> 250 bytes: tasa 4:1 y ahorro 75 %."""
        t = cod.calcular_tamanos(1000, 2.0, 250, 50)
        self.verificar("tasa", t["tasa"], 4.0, tol=1e-12)
        self.verificar("tasa con diccionario", t["tasa_total"], 1000 / 300, tol=1e-12)
        self.verificar("ahorro %", t["ahorro"], 75.0, tol=1e-12)
        self.verificar("límite teórico N*H/8", t["teorico"], 250.0, tol=1e-12)

    def test_entropia_cero_no_divide_por_cero(self):
        """H=0: tasa teórica infinita, sin ZeroDivisionError."""
        t = cod.calcular_tamanos(1000, 0.0, 125, 20)
        self.verificar("tasa teórica", t["tasa_teorica"], float('inf'))
        self.verificar("tasa", t["tasa"], 8.0, tol=1e-12)


class TestLineaDeComandos(LoggedTestCase):
    def test_argumentos_completos(self):
        """-i, -q y -o se interpretan."""
        c = cod.parse_args(["x.py", "-i", "a.txt", "-q", "-o", "salida"])
        self.verificar("config", c, {"input": "a.txt", "quiet": True, "output": "salida"})

    def test_defecto_directorio_salida(self):
        """Sin -o la salida es sim/codificacion."""
        c = cod.parse_args(["x.py", "-i", "a.txt"])
        self.verificar_cierto("termina en sim/codificacion",
                              c["output"].endswith(os.path.join("sim", "codificacion")), c["output"])
        self.verificar("quiet por defecto", c["quiet"], False)

    def test_sin_input_termina(self):
        """Sin -i el script termina con código 2."""
        with self.assertRaises(SystemExit) as ctx:
            cod.parse_args(["x.py"])
        self.verificar("código de salida", ctx.exception.code, 2)

    def test_ayuda_termina(self):
        """-h imprime ayuda y termina con código 2."""
        with self.assertRaises(SystemExit) as ctx:
            cod.parse_args(["x.py", "-h"])
        self.verificar("código de salida", ctx.exception.code, 2)


class TestProcesar(LoggedTestCase):
    def test_genera_archivos_en_salida(self):
        """procesar escribe .huffman y .diccionario.csv en out_dir."""
        entrada = self.escribir_temporal("ejemplo.txt", b"aaabbc" * 10)
        salida = os.path.join(self.directorio_temporal(), "nuevo", "dir")
        r = cod.procesar(entrada, salida)
        self.verificar_cierto(".huffman existe", os.path.isfile(os.path.join(salida, "ejemplo.txt.huffman")))
        self.verificar_cierto("csv existe", os.path.isfile(os.path.join(salida, "ejemplo.txt.diccionario.csv")))
        self.verificar("tamaño original", r["tamanos"]["original"], 60)

    def test_tamano_comprimido_consistente_con_bits(self):
        """bytes comprimidos == ceil(bits_utiles / 8)."""
        entrada = self.escribir_temporal("e.bin", bytes(range(50)) * 3)
        r = cod.procesar(entrada, self.directorio_temporal())
        self.verificar("bytes en disco", os.path.getsize(r["file_huffman_comprimido"]),
                       math.ceil(r["bits_utiles"] / 8))


if __name__ == "__main__":
    unittest.main()
