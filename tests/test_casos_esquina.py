"""Casos esquina (instructivo 2.3.4 y h_cero.bin): entropía cero, vacío, mínimos."""
import os
import unittest

import huffman_codificador as cod
import huffman_decodificador as dec
from tests.base import LoggedTestCase


class TestCasosEsquina(LoggedTestCase):
    def _ida_y_vuelta(self, contenido, nombre="e.bin"):
        entrada = self.escribir_temporal(nombre, contenido)
        out_cod = self.directorio_temporal()
        out_dec = self.directorio_temporal()
        r = cod.procesar(entrada, out_cod)
        d = dec.procesar(r["file_huffman_comprimido"], out_dec, entrada)
        with open(d["recovered_path"], "rb") as f:
            return r, d, f.read()

    def test_archivo_vacio(self):
        """Archivo vacío: procesar devuelve None y no escribe salidas."""
        entrada = self.escribir_temporal("vacio.bin", b"")
        salida = os.path.join(self.directorio_temporal(), "out")
        self.verificar("resultado", cod.procesar(entrada, salida), None)
        self.verificar_cierto("no se crea la carpeta de salida", not os.path.exists(salida))

    def test_h_cero_mil_bytes_iguales(self):
        """1000 bytes iguales (como h_cero.bin): H=0, 1 bit/símbolo, tasa 8:1."""
        r, d, rec = self._ida_y_vuelta(b"\x00" * 1000)
        self.verificar("M", r["metricas"]["M"], 1)
        self.verificar("H", r["metricas"]["H"], 0.0)
        self.verificar("L", r["metricas"]["L"], 1.0)
        self.verificar("eficiencia Huffman", r["metricas"]["eta_huffman"], 0.0)
        self.verificar("bits útiles", r["bits_utiles"], 1000)
        self.verificar("bytes comprimidos", r["tamanos"]["comprimido"], 125)
        self.verificar("tasa", r["tamanos"]["tasa"], 8.0, tol=1e-12)
        self.verificar("tasa teórica", r["tamanos"]["tasa_teorica"], float('inf'))
        self.verificar("bandera caso un símbolo", r["caso_un_simbolo"], True)
        self.verificar("recuperado == original", rec, b"\x00" * 1000)

    def test_un_solo_byte(self):
        """Archivo de 1 byte: 1 bit útil, 1 byte comprimido, se recupera."""
        r, d, rec = self._ida_y_vuelta(b"\x41")
        self.verificar("bits útiles", r["bits_utiles"], 1)
        self.verificar("bytes comprimidos", r["tamanos"]["comprimido"], 1)
        self.verificar("recuperado", rec, b"\x41")

    def test_un_solo_simbolo_distinto_de_cero(self):
        """Un único símbolo 0xFF repetido (7 veces, bits no múltiplo de 8)."""
        r, d, rec = self._ida_y_vuelta(b"\xff" * 7)
        self.verificar("bits útiles", r["bits_utiles"], 7)
        self.verificar("recuperado", rec, b"\xff" * 7)

    def test_dos_simbolos(self):
        """Dos símbolos: 1 bit cada uno, eficiencia Huffman depende de H."""
        r, d, rec = self._ida_y_vuelta(b"ab" * 50 + b"a" * 10)
        self.verificar("longitudes", sorted(len(c) for c in r["codigos"].values()), [1, 1])
        self.verificar("recuperado", rec, b"ab" * 50 + b"a" * 10)

    def test_los_256_valores_de_byte(self):
        """Todos los valores 0..255 (como todo_ascii_cien.bin): H=8, L=8, eficiencia 100%."""
        contenido = bytes(range(256)) * 4
        r, d, rec = self._ida_y_vuelta(contenido)
        self.verificar("M", r["metricas"]["M"], 256)
        self.verificar("H", r["metricas"]["H"], 8.0, tol=1e-9)
        self.verificar("L", r["metricas"]["L"], 8.0, tol=1e-9)
        self.verificar("eficiencia Huffman", r["metricas"]["eta_huffman"], 1.0, tol=1e-9)
        self.verificar("recuperado", rec, contenido)

    def test_bits_multiplo_de_8_sin_padding(self):
        """Cuando los bits son múltiplo de 8 no hay relleno."""
        r, d, rec = self._ida_y_vuelta(bytes([0, 1, 2, 3]) * 2)  # 8 símbolos x 2 bits = 16
        self.verificar("bits útiles", r["bits_utiles"], 16)
        self.verificar("bytes comprimidos", r["tamanos"]["comprimido"], 2)
        self.verificar("recuperado", rec, bytes([0, 1, 2, 3]) * 2)

    def test_decodificador_detecta_csv_o_huffman_corrupto(self):
        """Si el .huffman se trunca, el decodificador falla con ValueError."""
        entrada = self.escribir_temporal("c.bin", bytes(range(30)) * 5)
        r = cod.procesar(entrada, self.directorio_temporal())
        with open(r["file_huffman_comprimido"], "rb") as f:
            datos = f.read()
        with open(r["file_huffman_comprimido"], "wb") as f:
            f.write(datos[:-3])
        self.verificar_error(".huffman truncado", ValueError, dec.procesar,
                             r["file_huffman_comprimido"], self.directorio_temporal())


if __name__ == "__main__":
    unittest.main()
