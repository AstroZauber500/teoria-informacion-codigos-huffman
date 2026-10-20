"""Decodificador de Huffman - Proyecto 3 (Teoría de la Información).

Uso:
    python3 huffman_decodificador.py -i <archivo.huffman> [-r <original>] [-o <directorio_salida>]

Lee <archivo.huffman> y su <nombre>.diccionario.csv (en la misma carpeta),
reconstruye el árbol, decodifica y escribe recovered_<nombre> en la carpeta de
salida (por defecto sim/decodificacion/). Con -r compara bit a bit contra el
original (instructivo 2.4.2).

Flujo de ejecución (sección 2.4 del reporte):
    1.  parse_args lee -i/-r/-o/-h, valida la entrada y configura las rutas.
    2.  procesar llama a rutas_derivadas para deducir el .csv y la salida.
    3.  leer_diccionario extrae bits_utiles y los códigos (con validaciones).
    4.  construir_arbol_desde_diccionario reconstruye el árbol en memoria.
    5.  procesar lee todos los bytes del .huffman.
    6.  bytes_a_bits los convierte a texto y trunca exactamente en bits_utiles.
    7.  decodificar_bits recorre el árbol; las hojas se detectan con
        type(nodo) is int y cada hoja emite un byte.
    8.  procesar crea la carpeta de salida y escribe el archivo recuperado.
    9.  Si se pasó -r, la verificación es comparación DIRECTA byte a byte;
        el SHA-256 solo se imprime como evidencia.
    10. imprimir_reporte muestra tamaños, hashes y estado; main retorna 0,
        o 1 si la comparación falló.
"""
import csv
import getopt
import hashlib
import os
import sys

# Constantes (deben coincidir con las del codificador; las valida test_roundtrip)
SUFIJO_HUFFMAN = ".huffman"
SUFIJO_DICCIONARIO = ".diccionario.csv"
PREFIJO_RECUPERADO = "recovered_"
DIR_SALIDA_DEFECTO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "sim", "decodificacion")


# Árbol (misma estructura que huffman_base.py)
class NodeTree(object):
    """Nodo INTERNO del árbol binario de Huffman.

    Importante: un NodeTree NUNCA es una hoja. Las hojas son los enteros
    (los bytes originales, 0-255) que se guardan directamente en los
    atributos `left` o `right` de un nodo interno.
    """
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def children(self):
        return (self.left, self.right)

    def nodes(self):
        return (self.left, self.right)

    def __str__(self):
        return '%s_%s' % (self.left, self.right)


def insert_in_tree(raiz, ruta, valor):
    """Inserta 'valor' (hoja entera) siguiendo la 'ruta' del código binario.

    Recorre el código binario (ej. '101') sobre el árbol: '0' baja a la
    izquierda y '1' a la derecha. Si en el camino no existe el nodo interno,
    lo crea. Al final del camino inserta el símbolo entero (la hoja).
    """
    if len(ruta) == 1:
        if ruta == '0':
            raiz.left = valor
        else:
            raiz.right = valor
    else:
        if ruta[0] == '0':
            if raiz.left is None:
                raiz.left = NodeTree(None, None)
            insert_in_tree(raiz.left, ruta[1:], valor)
        else:
            if raiz.right is None:
                raiz.right = NodeTree(None, None)
            insert_in_tree(raiz.right, ruta[1:], valor)


# Pasos de la descompresión
def rutas_derivadas(file_huffman, out_dir=DIR_SALIDA_DEFECTO):
    """Devuelve (ruta_diccionario, recovered_path) a partir del .huffman.

    Valida que el archivo termine en '.huffman' y calcula las rutas del
    diccionario (.diccionario.csv, en la misma carpeta) y del archivo de
    salida (recovered_<nombre> en out_dir).

    Nota: esta función SOLO calcula las rutas; la carpeta de salida se
    crea físicamente en la función procesar().
    """
    carpeta, nombre = os.path.split(os.path.normpath(file_huffman))
    if not nombre.endswith(SUFIJO_HUFFMAN):
        raise ValueError("El archivo comprimido debe terminar en '%s': %s"
                         % (SUFIJO_HUFFMAN, nombre))
    base = nombre[:-len(SUFIJO_HUFFMAN)]
    ruta_diccionario = os.path.join(carpeta, base + SUFIJO_DICCIONARIO)
    recovered_path = os.path.join(out_dir, PREFIJO_RECUPERADO + base)
    return ruta_diccionario, recovered_path


def leer_diccionario(ruta):
    """Lee el CSV. Devuelve (bits_utiles, {símbolo: código}).

    Aplica validaciones estrictas (lanza ValueError claro si algo falla):
      - Exige que la primera fila tenga la forma '<n>,bits'.
      - Ignora filas en blanco.
      - Cada símbolo debe ser un entero en [0, 255].
      - Verifica que haya al menos un código y que ningún código esté vacío
        ni contenga caracteres distintos a '0' o '1'.
    """
    with open(ruta, 'r', newline='') as csvfile:
        filas = [fila for fila in csv.reader(csvfile) if fila]
    if not filas:
        raise ValueError("Diccionario vacío: %s" % ruta)
    cabecera = filas[0]
    if len(cabecera) != 2 or cabecera[1] != "bits" or not cabecera[0].isdigit():
        raise ValueError("Primera fila inválida (se esperaba '<bits>,bits'): %r" % cabecera)
    bits_utiles = int(cabecera[0])
    codigos = {}
    for fila in filas[1:]:
        if len(fila) != 2 or not fila[0].isdigit() or not (0 <= int(fila[0]) <= 255):
            raise ValueError("Fila de símbolo inválida: %r" % fila)
        if not fila[1] or set(fila[1]) - {'0', '1'}:
            raise ValueError("Código inválido (solo 0/1, no vacío): %r" % fila)
        codigos[int(fila[0])] = fila[1]
    if not codigos:
        raise ValueError("El diccionario no contiene códigos")
    return bits_utiles, codigos


def construir_arbol_desde_diccionario(codigos):
    """Reconstruye el árbol de Huffman completo.

    Itera sobre el diccionario leído del CSV y llama a insert_in_tree para
    cada par (símbolo, código), reconstruyendo así el árbol binario.

    Caso esquina (h_cero.bin): con un solo símbolo, el árbol queda con la
    raíz y una única hoja en `left` (código '0'). Cada bit 0 leído produce
    un byte en la salida, funcionando correctamente.
    """
    raiz = NodeTree(None, None)
    for simbolo, codigo in codigos.items():
        insert_in_tree(raiz, codigo, simbolo)
    return raiz


def bytes_a_bits(datos, bits_utiles):
    """Convierte bytes a cadena de bits y descarta el relleno (padding).

    Importante: CORTA la cadena conservando exactamente los primeros
    `bits_utiles` bits. NO "elimina ceros del final", lo cual destruiría
    datos si el mensaje real termina en ceros.

    Validaciones (lanza ValueError):
      - bits_utiles no puede ser mayor que el total de bits disponibles.
      - No pueden sobrar 8 bits o más (detectaría archivos truncados o
        un CSV incorrecto, pues el relleno legítimo es de 0 a 7 bits).
    """
    disponibles = len(datos) * 8
    if bits_utiles > disponibles:
        raise ValueError("El diccionario indica %d bits pero el archivo solo tiene %d"
                         % (bits_utiles, disponibles))
    if disponibles - bits_utiles >= 8:
        raise ValueError("Relleno inconsistente: sobran %d bits (máximo 7)"
                         % (disponibles - bits_utiles))
    return "".join(format(b, '08b') for b in datos)[:bits_utiles]


def decodificar_bits(bits, raiz):
    """Recorre el árbol bit a bit; al llegar a una hoja emite el símbolo.

    Núcleo de la decodificación: si lee un '0' va a la izquierda, si lee un
    '1' va a la derecha. Cuando llega a un nodo que es un entero
    (type(nodo) is int), guarda ese byte en la salida y regresa a la raíz.

    Lanza ValueError si la secuencia de bits no corresponde a ningún código
    (llega a None) o si el mensaje termina a mitad de un código.
    """
    salida = bytearray()
    nodo = raiz
    for bit in bits:
        nodo = nodo.left if bit == '0' else nodo.right
        if nodo is None:
            raise ValueError("Secuencia de bits no corresponde a ningún código")
        if type(nodo) is int:
            salida.append(nodo)
            nodo = raiz
    if nodo is not raiz:
        raise ValueError("Los bits terminan a mitad de un código")
    return bytes(salida)


def hash_sha256(datos):
    """Calcula el SHA-256 SOLO como evidencia para el reporte.

    El hash se calcula e imprime, pero NO es el criterio que decide si la
    verificación es exitosa (esa decisión es de verificar_integridad).
    """
    return hashlib.sha256(datos).hexdigest()


def verificar_integridad(original, recuperado):
    """True si ambos son idénticos byte a byte.

    Importante: la verificación de integridad se realiza EXCLUSIVAMENTE
    mediante comparación directa byte a byte (original == recuperado).
    """
    return original == recuperado


def procesar(file_huffman, out_dir=DIR_SALIDA_DEFECTO, original=None):
    """Orquesta el flujo completo de descompresión.

    Deduce rutas, lee el diccionario, reconstruye el árbol, lee el .huffman,
    convierte a bits y decodifica. Luego CREA la carpeta de salida
    (os.makedirs), escribe el archivo final (recovered_path) y retorna las
    estadísticas. Si se da 'original', además verifica la integridad.
    """
    ruta_diccionario, recovered_path = rutas_derivadas(file_huffman, out_dir)
    bits_utiles, codigos = leer_diccionario(ruta_diccionario)
    raiz = construir_arbol_desde_diccionario(codigos)
    with open(file_huffman, "rb") as f:
        comprimido = f.read()
    bits = bytes_a_bits(comprimido, bits_utiles)
    recuperado = decodificar_bits(bits, raiz)

    os.makedirs(out_dir, exist_ok=True)
    with open(recovered_path, "wb") as f:
        f.write(recuperado)

    resultado = {
        "file_huffman": file_huffman,
        "ruta_diccionario": ruta_diccionario,
        "recovered_path": recovered_path,
        "bits_utiles": bits_utiles,
        "simbolos": len(codigos),
        "tam_comprimido": len(comprimido),
        "tam_recuperado": len(recuperado),
        "sha256_recuperado": hash_sha256(recuperado),
        "tam_original": None,
        "sha256_original": None,
        "coincide": None,
    }
    if original is not None:
        with open(original, "rb") as f:
            datos_original = f.read()
        resultado["tam_original"] = len(datos_original)
        resultado["sha256_original"] = hash_sha256(datos_original)
        resultado["coincide"] = verificar_integridad(datos_original, recuperado)
    return resultado


# Presentación y línea de comandos
def imprimir_reporte(r):
    """Muestra en consola tamaños, hashes SHA-256 y el estado final.

    El renglón de verificación (COINCIDE / NO COINCIDE) refleja la
    comparación directa byte a byte; el SHA-256 se imprime solo como
    evidencia para el reporte.
    """
    print("====== Descompresión:", os.path.basename(r["file_huffman"]), "======")
    print("Diccionario leído                  : %s (%d símbolos)"
          % (r["ruta_diccionario"], r["simbolos"]))
    print("Bits útiles                        : %d bits" % r["bits_utiles"])
    print("Tamaño comprimido                  : %d bytes" % r["tam_comprimido"])
    print("Tamaño recuperado                  : %d bytes" % r["tam_recuperado"])
    print("SHA-256 recuperado                 : %s" % r["sha256_recuperado"])
    print("Archivo recuperado                 : %s" % r["recovered_path"])
    if r["coincide"] is None:
        print("Verificación                       : omitida (use -r <original>)")
    else:
        print("Tamaño original                    : %d bytes" % r["tam_original"])
        print("SHA-256 original                   : %s" % r["sha256_original"])
        print("Verificación bit a bit             : %s"
              % ("COINCIDE" if r["coincide"] else "NO COINCIDE"))


def parse_args(argv):
    """Lee -i (.huffman), -r (original), -o (directorio de salida) y -h.

    Atiende -h (ayuda) y opciones inválidas o falta de -i saliendo con
    código 2. Establece la carpeta sim/decodificacion/ como salida por
    defecto cuando no se pasa -o.
    """
    arg_help = ("{0} -i <archivo.huffman> [-r <original>] [-o <directorio_salida>]"
                .format(argv[0]))
    try:
        opts, args = getopt.getopt(argv[1:], "hi:r:o:",
                                   ["help", "input=", "reference=", "output="])
    except getopt.GetoptError:
        print(arg_help)
        sys.exit(2)
    config = {"input": "", "original": None, "output": DIR_SALIDA_DEFECTO}
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(arg_help)
            sys.exit(2)
        elif opt in ("-i", "--input"):
            config["input"] = arg
        elif opt in ("-r", "--reference"):
            config["original"] = arg
        elif opt in ("-o", "--output"):
            config["output"] = arg
    if not config["input"]:
        print(arg_help)
        sys.exit(2)
    return config


def main(argv):
    """Punto de entrada: parsea argumentos, procesa e imprime el reporte.

    Retorna 0 si todo salió bien (o si no se pidió verificación), y 1 si
    la comparación byte a byte contra el original falló.
    """
    config = parse_args(argv)
    resultado = procesar(config["input"], config["output"], config["original"])
    imprimir_reporte(resultado)
    return 1 if resultado["coincide"] is False else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
