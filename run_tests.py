"""Corre todas las pruebas y escribe un log descriptivo en sim/logs/.

Uso:
    python3 run_tests.py                       # todas
    python3 run_tests.py test_decodificador.py # solo un archivo (patrón glob)
"""
import logging
import os
import sys
import time
import unittest
from datetime import datetime

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)

from tests.base import DIR_SIM_LOGS, LOG  # noqa: E402


class ResultadoConLog(unittest.TestResult):
    """Registra cada prueba como PASS / FAIL / ERROR / SKIP con su motivo."""

    def __init__(self):
        super().__init__()
        self._inicio = {}
        self.pasaron = 0

    @staticmethod
    def _nombre(test):
        return "%s.%s" % (type(test).__name__, test._testMethodName)

    @staticmethod
    def _desc(test):
        return test.shortDescription() or ""

    def startTest(self, test):
        super().startTest(test)
        self._inicio[test] = time.perf_counter()
        LOG.info("[RUN ] %s - %s", self._nombre(test), self._desc(test))

    def _dur(self, test):
        return time.perf_counter() - self._inicio.get(test, time.perf_counter())

    def addSuccess(self, test):
        super().addSuccess(test)
        self.pasaron += 1
        LOG.info("[PASS] %s (%.3fs)", self._nombre(test), self._dur(test))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        LOG.error("[FAIL] %s (%.3fs)\n    motivo: %s", self._nombre(test), self._dur(test), err[1])

    def addError(self, test, err):
        super().addError(test, err)
        LOG.error("[ERROR] %s (%.3fs)\n%s", self._nombre(test), self._dur(test),
                  self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        LOG.warning("[SKIP] %s - %s", self._nombre(test), reason)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            LOG.error("[FAIL] subprueba %s\n%s", subtest._subDescription(),
                      self._exc_info_to_string(err, test))


def configurar_log():
    os.makedirs(DIR_SIM_LOGS, exist_ok=True)
    ruta = os.path.join(DIR_SIM_LOGS, "tests_%s.log" % datetime.now().strftime("%Y%m%d_%H%M%S"))
    LOG.setLevel(logging.INFO)
    LOG.handlers.clear()
    formato = logging.Formatter("%(asctime)s %(message)s", "%H:%M:%S")
    for handler in (logging.FileHandler(ruta, encoding="utf-8"),
                    logging.StreamHandler(sys.stdout)):
        handler.setFormatter(formato)
        LOG.addHandler(handler)
    return ruta


def main(argv):
    patron = argv[1] if len(argv) > 1 else "test_*.py"
    ruta_log = configurar_log()
    LOG.info("===== Pruebas Huffman | Python %s | patrón %s =====",
             sys.version.split()[0], patron)
    suite = unittest.defaultTestLoader.discover(
        os.path.join(RAIZ, "tests"), pattern=patron, top_level_dir=RAIZ)
    resultado = ResultadoConLog()
    suite.run(resultado)
    LOG.info("===== RESUMEN: %d ejecutadas | %d PASS | %d FAIL | %d ERROR | %d SKIP =====",
             resultado.testsRun, resultado.pasaron, len(resultado.failures),
             len(resultado.errors), len(resultado.skipped))
    LOG.info("Log guardado en: %s", ruta_log)
    return 0 if resultado.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
