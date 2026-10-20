"""Utilidades compartidas por las pruebas (SSOT de rutas y de archivos reales)."""
import logging
import os
import shutil
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATA = os.path.join(RAIZ, "data")
DIR_SIM_COD = os.path.join(RAIZ, "sim", "codificacion")
DIR_SIM_DEC = os.path.join(RAIZ, "sim", "decodificacion")
DIR_SIM_LOGS = os.path.join(RAIZ, "sim", "logs")

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
