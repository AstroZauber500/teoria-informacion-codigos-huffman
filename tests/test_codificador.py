"""Pruebas de huffman_codificador.py (instructivo 2.2.5 y 2.3).

El script se ejecuta como proceso (python3 huffman_codificador.py -i ...) y se
verifica lo que imprime y los archivos que deja junto al archivo de entrada.
"""
import csv
import math
import os
import unittest

from tests.base import (LoggedTestCase, ejecutar_codificador_sin_i, ejecutar_codificador,
                        parsear_salida)

TOL_6_DEC = 5e-6   # la consola imprime 6 decimales
TOL_PCT = 5e-3     # los porcentajes se imprimen con 4 decimales


def leer_csv(ruta):
    with open(ruta, newline='') as f:
        filas = list(csv.reader(f))
    return int(filas[0][0]), filas[0][1], {int(s): c for s, c in filas[1:]}


def es_libre_de_prefijos(codigos):
    lista = list(codigos.values())
    return not any(a != b and b.startswith(a) for a in lista for b in lista)


class TestMetricasEnConsola(LoggedTestCase):
    def test_distribucion_diadica(self):
        """P=(.5,.25,.25): H=1.5, L=1.5, var=0.25, eficiencia Huffman 100%."""
        _, _, m = self.codificar("diadica.bin", b"aabc" * 50)
        self.verificar("N", m["N"], 200)
        self.verificar("M", m["M"], 3)
        self.verificar("H", m["H"], 1.5, tol=TOL_6_DEC)
        self.verificar("L", m["L"], 1.5, tol=TOL_6_DEC)
        self.verificar("varianza", m["var"], 0.25, tol=TOL_6_DEC)
        self.verificar("eficiencia Huffman %", m["eta_huffman_pct"], 100.0, tol=TOL_PCT)
        self.verificar("eficiencia original % (H/8)", m["eta_original_pct"], 100 * 1.5 / 8, tol=TOL_PCT)
        self.verificar("H máxima log2(3)", m["H_max"], math.log2(3), tol=TOL_6_DEC)

    def test_uniforme_26_simbolos(self):
        """26 símbolos equiprobables (solo_abc): H = log2(26) = H_max."""
        _, _, m = self.codificar("abc.txt", bytes(range(65, 91)) * 100)
        self.verificar("H", m["H"], math.log2(26), tol=TOL_6_DEC)
        self.verificar("H = H_max", m["H"], m["H_max"], tol=TOL_6_DEC)
        self.verificar_cierto("L entre 4 y 5 bits", 4 <= m["L"] <= 5, "L=%.6f" % m["L"])

    def test_cota_de_shannon(self):
        """Teoría: H <= L < H + 1, eficiencia <= 100 %, varianza >= 0."""
        _, _, m = self.codificar("texto.txt", b"the quick brown fox jumps over the lazy dog " * 7)
        self.verificar_cierto("H <= L", m["H"] <= m["L"] + TOL_6_DEC, "H=%.6f L=%.6f" % (m["H"], m["L"]))
        self.verificar_cierto("L < H + 1", m["L"] < m["H"] + 1)
        self.verificar_cierto("eficiencia <= 100 %", m["eta_huffman_pct"] <= 100 + TOL_PCT)
        self.verificar_cierto("varianza >= 0", m["var"] >= 0)

    def test_tabla_de_codigos_y_quiet(self):
        """Sin -q imprime la tabla de códigos; con -q no."""
        ruta = self.escribir_temporal("t.bin", b"aabc" * 10)
        sin_q = ejecutar_codificador(ruta)
        con_q = ejecutar_codificador(ruta, "-q")
        self.verificar_cierto("sin -q: aparece la tabla", "Huffman code" in sin_q.stdout)
        self.verificar_cierto("con -q: no aparece la tabla", "Huffman code" not in con_q.stdout)
        self.verificar_cierto("ambos imprimen las métricas",
                              "Métricas de la fuente" in sin_q.stdout and "Métricas de la fuente" in con_q.stdout)


class TestArchivosGenerados(LoggedTestCase):
    def test_salidas_junto_a_la_entrada(self):
        """Se generan <entrada>.huffman y <entrada>.diccionario.csv junto al archivo."""
        _, ruta, _ = self.codificar("ejemplo.txt", b"aaabbc" * 10)
        self.verificar_cierto(".huffman existe", os.path.isfile(ruta + ".huffman"))
        self.verificar_cierto(".diccionario.csv existe", os.path.isfile(ruta + ".diccionario.csv"))

    def test_formato_del_diccionario(self):
        """Primera fila '<bits>,bits'; luego símbolo,código para cada byte distinto."""
        _, ruta, m = self.codificar("d.bin", b"aaabbc" * 10)
        bits, etiqueta, codigos = leer_csv(ruta + ".diccionario.csv")
        self.verificar("etiqueta de la primera fila", etiqueta, "bits")
        self.verificar("símbolos del diccionario", sorted(codigos), [97, 98, 99])
        self.verificar("bits útiles == impresos en consola", bits, int(m["bits_utiles"]))

    def test_codigos_validos(self):
        """Los códigos del CSV son libres de prefijos y cumplen Kraft = 1."""
        _, ruta, _ = self.codificar("k.txt", b"mississippi river " * 20)
        _, _, codigos = leer_csv(ruta + ".diccionario.csv")
        self.verificar_cierto("libre de prefijos", es_libre_de_prefijos(codigos), str(codigos))
        self.verificar("suma de Kraft", sum(2 ** -len(c) for c in codigos.values()), 1.0, tol=1e-12)

    def test_bits_comprimidos_coinciden_con_codificacion_independiente(self):
        """El .huffman == codificar los datos con el CSV, con relleno de ceros."""
        contenido = b"abracadabra alakazam " * 13
        _, ruta, _ = self.codificar("i.txt", contenido)
        bits, _, codigos = leer_csv(ruta + ".diccionario.csv")
        cadena = "".join(codigos[b] for b in contenido)
        self.verificar("bits útiles", bits, len(cadena))
        cadena += "0" * (-len(cadena) % 8)
        esperado = bytes(int(cadena[i:i + 8], 2) for i in range(0, len(cadena), 8))
        with open(ruta + ".huffman", "rb") as f:
            obtenido = f.read()
        self.verificar("contenido del .huffman", obtenido, esperado)

    def test_tamano_comprimido_es_techo_de_bits_sobre_8(self):
        """bytes del .huffman == ceil(bits_útiles / 8)."""
        _, ruta, _ = self.codificar("t.bin", bytes(range(50)) * 3)
        bits, _, _ = leer_csv(ruta + ".diccionario.csv")
        self.verificar("bytes en disco", os.path.getsize(ruta + ".huffman"), math.ceil(bits / 8))


class TestTasasDeCompresion(LoggedTestCase):
    def test_tamanos_y_tasas_coinciden_con_disco(self):
        """Los tamaños y tasas impresos coinciden con los archivos reales."""
        contenido = b"aaaaaaaabbbbccd" * 40
        _, ruta, m = self.codificar("tasa.bin", contenido)
        comp = os.path.getsize(ruta + ".huffman")
        dicc = os.path.getsize(ruta + ".diccionario.csv")
        self.verificar("tamaño original", int(m["original"]), len(contenido))
        self.verificar("tamaño comprimido", int(m["comprimido"]), comp)
        self.verificar("tamaño diccionario", int(m["diccionario"]), dicc)
        self.verificar("tasa orig/comp", m["tasa"], len(contenido) / comp, tol=5e-5)
        self.verificar("tasa con diccionario", m["tasa_total"], len(contenido) / (comp + dicc), tol=5e-5)
        self.verificar("ahorro %", m["ahorro_pct"], 100 * (1 - comp / len(contenido)), tol=5e-3)

    def test_limite_teorico(self):
        """Tasa teórica máxima = orig / (N*H/8)."""
        _, _, m = self.codificar("lim.bin", b"aabc" * 50)  # H = 1.5
        self.verificar("tasa teórica", m["tasa_teorica"], 200 / (200 * 1.5 / 8), tol=5e-4)


class TestLineaDeComandos(LoggedTestCase):
    def test_sin_input_termina_con_2(self):
        """Sin -i imprime la ayuda y termina con código 2."""
        p = ejecutar_codificador_sin_i()
        self.verificar("código de salida", p.returncode, 2)
        self.verificar_cierto("imprime el uso", "-i <input>" in p.stdout, p.stdout.strip())

    def test_ayuda_termina_con_2(self):
        """-h imprime la ayuda y termina con código 2."""
        p = ejecutar_codificador_sin_i("-h")
        self.verificar("código de salida", p.returncode, 2)
        self.verificar_cierto("imprime el uso", "-i <input>" in p.stdout)

    def test_opcion_invalida(self):
        """Una opción desconocida termina con código 2."""
        p = ejecutar_codificador_sin_i("-z")
        self.verificar("código de salida", p.returncode, 2)

    def test_archivo_inexistente(self):
        """Un archivo inexistente falla (FileNotFoundError, código != 0)."""
        p = ejecutar_codificador_sin_i("-i", "no_existe_xyz.bin")
        self.verificar_cierto("código distinto de 0", p.returncode != 0, "returncode=%d" % p.returncode)
        self.verificar_cierto("menciona FileNotFoundError", "FileNotFoundError" in p.stderr)


if __name__ == "__main__":
    unittest.main()
