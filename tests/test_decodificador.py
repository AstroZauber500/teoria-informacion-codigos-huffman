"""Pruebas unitarias de huffman_decodificador.py (instructivo 2.4)."""
import os
import unittest

import huffman_decodificador as dec
from tests.base import LoggedTestCase

CODIGOS = {65: '0', 66: '10', 67: '11'}


class TestRutas(LoggedTestCase):
    def test_rutas_derivadas(self):
        """Del .huffman se derivan el CSV y recovered_<nombre>."""
        csv_path, recovered = dec.rutas_derivadas(os.path.join("a", "x.txt.huffman"), "salida")
        self.verificar("diccionario", csv_path, os.path.join("a", "x.txt.diccionario.csv"))
        self.verificar("recovered_path", recovered, os.path.join("salida", "recovered_x.txt"))

    def test_extension_invalida(self):
        """Un archivo que no termina en .huffman se rechaza."""
        self.verificar_error("extensión inválida", ValueError, dec.rutas_derivadas, "x.txt")


class TestLeerDiccionario(LoggedTestCase):
    def _csv(self, texto):
        return self.escribir_temporal("d.csv", texto.encode())

    def test_lectura_correcta(self):
        """Lee bits útiles y la tabla de códigos."""
        bits, codigos = dec.leer_diccionario(self._csv("11,bits\r\n65,0\r\n66,10\r\n67,11\r\n"))
        self.verificar("bits útiles", bits, 11)
        self.verificar("códigos", codigos, CODIGOS)

    def test_cabecera_invalida(self):
        """Primera fila distinta de '<n>,bits' se rechaza."""
        self.verificar_error("cabecera", ValueError, dec.leer_diccionario, self._csv("65,0\n66,1\n"))

    def test_codigo_invalido(self):
        """Códigos con caracteres distintos de 0/1 se rechazan."""
        self.verificar_error("código con '2'", ValueError, dec.leer_diccionario,
                             self._csv("3,bits\n65,02\n"))

    def test_simbolo_fuera_de_rango(self):
        """Símbolo > 255 se rechaza."""
        self.verificar_error("símbolo 300", ValueError, dec.leer_diccionario,
                             self._csv("3,bits\n300,0\n"))

    def test_sin_codigos(self):
        """Un CSV con solo la cabecera se rechaza."""
        self.verificar_error("solo cabecera", ValueError, dec.leer_diccionario, self._csv("3,bits\n"))

    def test_archivo_vacio(self):
        """Un CSV vacío se rechaza."""
        self.verificar_error("vacío", ValueError, dec.leer_diccionario, self._csv(""))


class TestArbol(LoggedTestCase):
    def test_reconstruccion(self):
        """El árbol reconstruido tiene cada símbolo en la ruta de su código."""
        raiz = dec.construir_arbol_desde_diccionario(CODIGOS)
        self.verificar("raíz.left (código '0')", raiz.left, 65)
        self.verificar("raíz.right.left (código '10')", raiz.right.left, 66)
        self.verificar("raíz.right.right (código '11')", raiz.right.right, 67)

    def test_simbolo_cero_es_valido(self):
        """El byte 0x00 es un símbolo válido (no se confunde con 'vacío')."""
        raiz = dec.construir_arbol_desde_diccionario({0: '0', 1: '1'})
        self.verificar("hoja izquierda", raiz.left, 0)
        self.verificar("hoja derecha", raiz.right, 1)


class TestBits(LoggedTestCase):
    def test_descarta_padding(self):
        """0xA0 con 3 bits útiles -> '101'."""
        self.verificar("bits", dec.bytes_a_bits(b"\xa0", 3), "101")

    def test_bits_exactos(self):
        """Dos bytes completos con 16 bits útiles."""
        self.verificar("bits", dec.bytes_a_bits(b"\xff\x00", 16), "1111111100000000")

    def test_mas_bits_que_los_disponibles(self):
        """Bits útiles mayor al tamaño del archivo -> ValueError."""
        self.verificar_error("17 bits en 2 bytes", ValueError, dec.bytes_a_bits, b"\xff\x00", 17)

    def test_relleno_excesivo(self):
        """Más de 7 bits de relleno indica archivo/CSV inconsistente."""
        self.verificar_error("relleno de 8+", ValueError, dec.bytes_a_bits, b"\xff\x00", 3)


class TestDecodificar(LoggedTestCase):
    def test_decodifica_secuencia(self):
        """'0' '10' '11' '0' -> A B C A."""
        raiz = dec.construir_arbol_desde_diccionario(CODIGOS)
        self.verificar("salida", dec.decodificar_bits("010110", raiz), b"ABCA")

    def test_bits_a_mitad_de_codigo(self):
        """Terminar en un nodo interno es un error."""
        raiz = dec.construir_arbol_desde_diccionario(CODIGOS)
        self.verificar_error("termina en '1'", ValueError, dec.decodificar_bits, "01", raiz)

    def test_ruta_inexistente(self):
        """Camino que sale del árbol es un error."""
        raiz = dec.construir_arbol_desde_diccionario({0: '0'})  # un solo símbolo
        self.verificar_error("bit '1' sin código", ValueError, dec.decodificar_bits, "1", raiz)

    def test_un_solo_simbolo(self):
        """Caso h_cero: código '0' repetido."""
        raiz = dec.construir_arbol_desde_diccionario({0: '0'})
        self.verificar("salida", dec.decodificar_bits("0000", raiz), b"\x00\x00\x00\x00")

    def test_entrada_vacia(self):
        """Sin bits no hay símbolos."""
        raiz = dec.construir_arbol_desde_diccionario(CODIGOS)
        self.verificar("salida", dec.decodificar_bits("", raiz), b"")


class TestIntegridad(LoggedTestCase):
    def test_iguales(self):
        """Datos idénticos coinciden."""
        self.verificar("coincide", dec.verificar_integridad(b"abc", b"abc"), True)

    def test_un_byte_distinto(self):
        """Un solo byte distinto se detecta."""
        self.verificar("coincide", dec.verificar_integridad(b"abc", b"abd"), False)

    def test_longitud_distinta(self):
        """Distinta longitud no coincide."""
        self.verificar("coincide", dec.verificar_integridad(b"abc", b"ab"), False)

    def test_sha256_conocido(self):
        """SHA-256 de 'abc' es el valor estándar."""
        self.verificar("hash", dec.hash_sha256(b"abc"),
                       "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


class TestLineaDeComandos(LoggedTestCase):
    def test_argumentos(self):
        """-i, -r y -o se interpretan."""
        c = dec.parse_args(["x.py", "-i", "a.huffman", "-r", "a", "-o", "out"])
        self.verificar("config", c, {"input": "a.huffman", "original": "a", "output": "out"})

    def test_sin_input(self):
        """Sin -i termina con código 2."""
        with self.assertRaises(SystemExit) as ctx:
            dec.parse_args(["x.py"])
        self.verificar("código de salida", ctx.exception.code, 2)

    def test_defecto_salida(self):
        """Sin -o la salida es sim/decodificacion."""
        c = dec.parse_args(["x.py", "-i", "a.huffman"])
        self.verificar_cierto("termina en sim/decodificacion",
                              c["output"].endswith(os.path.join("sim", "decodificacion")), c["output"])


if __name__ == "__main__":
    unittest.main()
