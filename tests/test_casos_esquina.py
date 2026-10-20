"""Casos esquina (instructivo 2.3.4 y h_cero.bin): entropía cero, vacío, mínimos."""
import os
import unittest

import huffman_decodificador as dec
from tests.base import LoggedTestCase, ejecutar_codificador


class TestCasosEsquina(LoggedTestCase):
    def _ida_y_vuelta(self, contenido, nombre="e.bin"):
        proc, ruta, m = self.codificar(nombre, contenido, "-q")
        d = dec.procesar(ruta + ".huffman", self.directorio_temporal(), ruta)
        with open(d["recovered_path"], "rb") as f:
            return proc, m, d, f.read()

    def test_archivo_vacio(self):
        """Archivo vacío: mensaje, código 0 y no se escriben salidas."""
        ruta = self.escribir_temporal("vacio.bin", b"")
        p = ejecutar_codificador(ruta)
        self.verificar("código de salida", p.returncode, 0)
        self.verificar_cierto("mensaje de archivo vacío", "vacío" in p.stdout, p.stdout.strip())
        self.verificar_cierto("no hay .huffman", not os.path.exists(ruta + ".huffman"))
        self.verificar_cierto("no hay .csv", not os.path.exists(ruta + ".diccionario.csv"))

    def test_h_cero_mil_bytes_iguales(self):
        """1000 bytes iguales (como h_cero.bin): H=0, 1 bit/símbolo, tasa 8:1."""
        proc, m, d, rec = self._ida_y_vuelta(b"\x00" * 1000)
        self.verificar("M", m["M"], 1)
        self.verificar("H", m["H"], 0.0)
        self.verificar("L", m["L"], 1.0)
        self.verificar("eficiencia Huffman %", m["eta_huffman_pct"], 0.0)
        self.verificar("bits útiles", m["bits_utiles"], 1000)
        self.verificar("bytes comprimidos", m["comprimido"], 125)
        self.verificar("tasa", m["tasa"], 8.0, tol=5e-5)
        self.verificar("tasa teórica", m["tasa_teorica"], float('inf'))
        self.verificar_cierto("explica el caso esquina", "Caso esquina" in proc.stdout)
        self.verificar("recuperado == original", rec, b"\x00" * 1000)

    def test_un_solo_byte(self):
        """Archivo de 1 byte: 1 bit útil, 1 byte comprimido, se recupera."""
        _, m, d, rec = self._ida_y_vuelta(b"\x41")
        self.verificar("bits útiles", m["bits_utiles"], 1)
        self.verificar("bytes comprimidos", m["comprimido"], 1)
        self.verificar("recuperado", rec, b"\x41")

    def test_un_simbolo_no_cero_con_padding(self):
        """0xFF repetido 7 veces (7 bits, no múltiplo de 8)."""
        _, m, d, rec = self._ida_y_vuelta(b"\xff" * 7)
        self.verificar("bits útiles", m["bits_utiles"], 7)
        self.verificar("recuperado", rec, b"\xff" * 7)

    def test_dos_simbolos(self):
        """Dos símbolos: 1 bit cada uno, L = 1."""
        contenido = b"ab" * 50 + b"a" * 10
        _, m, d, rec = self._ida_y_vuelta(contenido)
        self.verificar("L", m["L"], 1.0, tol=5e-6)
        self.verificar("recuperado", rec, contenido)

    def test_los_256_valores_de_byte(self):
        """Valores 0..255 (como todo_ascii_cien.bin): H=8, L=8, eficiencia 100 %."""
        contenido = bytes(range(256)) * 4
        _, m, d, rec = self._ida_y_vuelta(contenido)
        self.verificar("M", m["M"], 256)
        self.verificar("H", m["H"], 8.0, tol=5e-6)
        self.verificar("L", m["L"], 8.0, tol=5e-6)
        self.verificar("eficiencia Huffman %", m["eta_huffman_pct"], 100.0, tol=5e-3)
        self.verificar("recuperado", rec, contenido)

    def test_bits_multiplo_de_8_sin_padding(self):
        """16 bits útiles -> 2 bytes, sin relleno."""
        contenido = bytes([0, 1, 2, 3]) * 2
        _, m, d, rec = self._ida_y_vuelta(contenido)
        self.verificar("bits útiles", m["bits_utiles"], 16)
        self.verificar("bytes comprimidos", m["comprimido"], 2)
        self.verificar("recuperado", rec, contenido)

    def test_decodificador_detecta_huffman_truncado(self):
        """Si el .huffman se trunca, el decodificador falla con ValueError."""
        _, ruta, _ = self.codificar("c.bin", bytes(range(30)) * 5, "-q")
        with open(ruta + ".huffman", "rb") as f:
            datos = f.read()
        with open(ruta + ".huffman", "wb") as f:
            f.write(datos[:-3])
        self.verificar_error(".huffman truncado", ValueError, dec.procesar,
                             ruta + ".huffman", self.directorio_temporal())


if __name__ == "__main__":
    unittest.main()
