"""Utilidades compartidas por las pruebas (SSOT de rutas y de archivos reales)."""
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATA = os.path.join(RAIZ, "data")
DIR_SIM_COD = os.path.join(RAIZ, "sim", "codificacion")
DIR_SIM_DEC = os.path.join(RAIZ, "sim", "decodificacion")
DIR_SIM_LOGS = os.path.join(RAIZ, "sim", "logs")
SCRIPT_CODIFICADOR = os.path.join(RAIZ, "huffman_codificador.py")

# Archivos del instructivo (subcarpeta de data/, nombre)
ARCHIVOS_REALES = [
    ("texto", "solo_abc_cien.txt"),
    ("texto", "shannon_intro.txt"),
    ("binarios", "todo_ascii_cien.bin"),
    ("binarios", "h_cero.bin"),
    ("imagenes", "4.1.01.tiff"),
    ("imagenes", "7.1.02.tiff"),
    ("imagenes", "5.1.11.tiff"),
    ("imagenes", "5.1.13.tiff"),
    ("imagenes", "4.2.03.tiff"),
    ("imagenes", "7.1.02_loss.jpg"),
]

LOG = logging.getLogger("huffman.tests")


def _corto(valor, maximo=110):
    texto = repr(valor)
    return texto if len(texto) <= maximo else texto[:maximo] + "...(%d chars)" % len(texto)


class LoggedTestCase(unittest.TestCase):
    """TestCase con verificaciones que dejan esperado/obtenido en el log."""

    def verificar(self, descripcion, obtenido, esperado, tol=None):
        if tol is None:
            ok = obtenido == esperado
        else:
            ok = abs(obtenido - esperado) <= tol
        LOG.info("    [%s] %s | esperado=%s | obtenido=%s%s",
                 "ok" if ok else "FALLA", descripcion, _corto(esperado), _corto(obtenido),
                 "" if tol is None else " | tol=%g" % tol)
        if not ok:
            self.fail("%s: esperado=%s, obtenido=%s"
                      % (descripcion, _corto(esperado), _corto(obtenido)))

    def verificar_cierto(self, descripcion, condicion, detalle=""):
        LOG.info("    [%s] %s %s", "ok" if condicion else "FALLA", descripcion, detalle)
        if not condicion:
            self.fail("%s %s" % (descripcion, detalle))

    def verificar_error(self, descripcion, excepcion, funcion, *args):
        """Verifica que funcion(*args) lance 'excepcion'."""
        try:
            funcion(*args)
        except excepcion as e:
            LOG.info("    [ok] %s | lanzó %s: %s", descripcion, excepcion.__name__, e)
            return
        except Exception as e:  # excepción de otro tipo
            LOG.info("    [FALLA] %s | lanzó %s en vez de %s", descripcion,
                     type(e).__name__, excepcion.__name__)
            raise
        LOG.info("    [FALLA] %s | no lanzó %s", descripcion, excepcion.__name__)
        self.fail("%s: no lanzó %s" % (descripcion, excepcion.__name__))

    def directorio_temporal(self):
        ruta = tempfile.mkdtemp(prefix="huffman_test_")
        self.addCleanup(shutil.rmtree, ruta, ignore_errors=True)
        return ruta

    def escribir_temporal(self, nombre, contenido):
        ruta = os.path.join(self.directorio_temporal(), nombre)
        with open(ruta, "wb") as f:
            f.write(contenido)
        return ruta

    def codificar(self, nombre, contenido, *extra):
        """Escribe 'contenido' en un temporal y corre el codificador sobre él.

        Devuelve (proceso, ruta_entrada, métricas_parseadas).
        """
        ruta = self.escribir_temporal(nombre, contenido)
        proc = ejecutar_codificador(ruta, *extra)
        LOG.info("    codificador -> returncode=%d", proc.returncode)
        if proc.returncode != 0:
            self.fail("el codificador terminó con código %d:\n%s" % (proc.returncode, proc.stderr))
        return proc, ruta, parsear_salida(proc.stdout)


# ----------------------------------------------------------------------------
# huffman_codificador.py se ejecuta como proceso: el script corre todo al
# importarse y escribe .huffman/.diccionario.csv junto al archivo de entrada.
# ----------------------------------------------------------------------------
_ETIQUETAS = {
    "N": "Símbolos totales (N)",
    "M": "Símbolos distintos (M)",
    "H": "Entropía H(X)",
    "H_max": "Entropía máxima log2(M)",
    "L": "Longitud media Huffman L",
    "var": "Varianza del código Huffman",
    "eta_original_pct": "Eficiencia código original",
    "eta_huffman_pct": "Eficiencia código Huffman",
    "original": "Tamaño original",
    "bits_utiles": "Bits Huffman útiles",
    "comprimido": "Tamaño comprimido (.huffman)",
    "diccionario": "Tamaño diccionario (.csv)",
    "tasa": "Tasa de compresión",
    "tasa_total": "Tasa incl. diccionario",
    "ahorro_pct": "Ahorro de espacio",
}


def ejecutar_codificador(ruta_entrada, *extra):
    """Corre `python3 huffman_codificador.py -i <ruta> [extra]` y devuelve el proceso."""
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, SCRIPT_CODIFICADOR, "-i", ruta_entrada, *extra],
                          capture_output=True, text=True, encoding="utf-8",
                          cwd=RAIZ, env=entorno)


def ejecutar_codificador_sin_i(*args):
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, SCRIPT_CODIFICADOR, *args],
                          capture_output=True, text=True, encoding="utf-8",
                          cwd=RAIZ, env=entorno)


def parsear_salida(stdout):
    """Extrae las métricas impresas por el codificador a un diccionario de floats."""
    res = {}
    for linea in stdout.splitlines():
        for clave, etiqueta in _ETIQUETAS.items():
            if linea.startswith(etiqueta):
                res[clave] = float(linea.split(":", 1)[1].split()[0])
        if linea.startswith("Límite teórico"):
            res["tasa_teorica"] = float(linea.split("tasa máx.")[1].split()[0])
    return res
