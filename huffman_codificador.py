import os
import sys
import getopt
import csv
from math import log2


file_full_path = ""
file_split_path = []
quiet = False


# lee los argumentos -i (archivo), -q (sin tabla) y -h (ayuda)
def myfunc(argv):
    global file_full_path, file_split_path, quiet
    arg_help = "{0} -i <input> [-q]".format(argv[0])
    try:
        opts, args = getopt.getopt(argv[1:], "hi:q", ["help", "input=", "quiet"])
    except getopt.GetoptError:
        print(arg_help)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(arg_help)
            sys.exit(2)
        elif opt in ("-i", "--input"):
            file_full_path = arg
            file_split_path = os.path.split(os.path.normpath(file_full_path))
        elif opt in ("-q", "--quiet"):
            quiet = True
    if not file_full_path:
        print(arg_help)
        sys.exit(2)


if __name__ == "__main__":
    myfunc(sys.argv)

file_huffman_comprimido = file_full_path + ".huffman"
ruta_diccionario = file_full_path + ".diccionario.csv"

# lee el archivo en binario
with open(file_full_path, "rb") as f:
    string = list(f.read())

if len(string) == 0:
    print("El archivo está vacío; no hay nada que codificar.")
    sys.exit(0)


# nodo del arbol, tiene hijo izquierdo y derecho
class NodeTree(object):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right

    def children(self):
        return (self.left, self.right)

    def nodes(self):
        return (self.left, self.right)

    def __str__(self):
        return '%s_%s' % (self.left, self.right)


# recorre el arbol, 0 para la izquierda, 1 para la derecha; al llegar a una hoja guarda el codigo
def huffman_code_tree(node, left=True, binString=''):
    if type(node) is int:
        return {node: binString}
    (l, r) = node.children()
    d = dict()
    d.update(huffman_code_tree(l, True, binString + '0'))
    d.update(huffman_code_tree(r, False, binString + '1'))
    return d


# cuenta cuantas veces aparece cada byte y calcula su probabilidad
N = len(string)
cuentas = {}
for c in string:
    cuentas[c] = cuentas.get(c, 0) + 1

freq = sorted(((k, v / N) for k, v in cuentas.items()), key=lambda x: x[1], reverse=True)

# une los dos nodos con menor probabilidad hasta que quede un solo nodo 
nodes = list(freq)
while len(nodes) > 1:
    (key1, c1) = nodes[-1]
    (key2, c2) = nodes[-2]
    nodes = nodes[:-2]
    node = NodeTree(key1, key2)
    nodes.append((node, c1 + c2))
    nodes = sorted(nodes, key=lambda x: x[1], reverse=True)

huffmanCode = huffman_code_tree(nodes[0][0])

# si solo hay un simbolo el codigo quedaria vacio, entonces se le asigna un codigo de 1 bit (0)
caso_un_simbolo = False
if len(huffmanCode) == 1:
    caso_un_simbolo = True
    unico = next(iter(huffmanCode))
    huffmanCode[unico] = '0'

if not quiet:
    print(' Char | Prob.      | Huffman code ')
    print('-----------------------------------')
    for (char, p) in freq:
        print(' %-4r | %.6f   | %s' % (char, p, huffmanCode[char]))
    print()

#entropia, longitud media, varianza y eficiencias
BITS_ORIGINALES = 8
M = len(freq)

H = -sum(p * log2(p) for (_, p) in freq)
H = abs(H)
L = sum(p * len(huffmanCode[s]) for (s, p) in freq)
var = sum(p * (len(huffmanCode[s]) - L) ** 2 for (s, p) in freq)
H_max = log2(M) if M > 1 else 0.0

eta_original = H / BITS_ORIGINALES
eta_huffman = (H / L) if L > 0 else float('nan')

print("====== Métricas de la fuente:", file_split_path[1], "======")
print("Símbolos totales (N)               : %d" % N)
print("Símbolos distintos (M)             : %d" % M)
print("Entropía H(X)                      : %.6f bits/símbolo" % H)
print("Entropía máxima log2(M)            : %.6f bits/símbolo" % H_max)
print("Longitud media Huffman L           : %.6f bits/símbolo" % L)
print("Varianza del código Huffman        : %.6f bits^2" % var)
print("Eficiencia código original (H/8)   : %.4f %%" % (100 * eta_original))
print("Eficiencia código Huffman (H/L)    : %.4f %%" % (100 * eta_huffman))
if caso_un_simbolo:
    print("  * Caso esquina: un solo símbolo, H = 0. Se forzó un código de 1 bit;")
    print("    la eficiencia H/L es 0 aunque la compresión sea máxima (8:1).")

# pega los codigos de todos los simbolos en una sola lista de bits
binary_string = []
for c in string:
    binary_string += huffmanCode[c]

# guarda cuantos bits son datos reales, sin contar el relleno
compressed_length_bit = len(binary_string)

# completa con ceros hasta llegar a multiplo de 8
if compressed_length_bit % 8 > 0:
    for i in range(8 - len(binary_string) % 8):
        binary_string += '0'

# parte los bits en grupos de 8 y convierte cada grupo en un byte
byte_string = "".join([str(i) for i in binary_string])
byte_string = [byte_string[i:i + 8] for i in range(0, len(byte_string), 8)]

datos_comprimidos = bytes([int(b, 2) for b in byte_string])
with open(file_huffman_comprimido, "wb") as f:
    f.write(datos_comprimidos)

# escribe el diccionario: primera fila bits utiles, luego simbolo,codigo
csvfile = open(ruta_diccionario, 'w', newline='')
writer = csv.writer(csvfile)
writer.writerow([str(compressed_length_bit), "bits"])
for entrada in huffmanCode:
    writer.writerow([str(entrada), huffmanCode[entrada]])
csvfile.close()

# tamaños en bytes y tasas de compresion
tam_original = N
tam_comprimido = len(datos_comprimidos)
tam_diccionario = os.path.getsize(ruta_diccionario)
tam_total = tam_comprimido + tam_diccionario

# si el comprimido queda en 0 bytes, se evita dividir entre 0
if tam_comprimido > 0:
    tasa = tam_original / tam_comprimido
    tasa_total = tam_original / tam_total
else:
    tasa = float('inf')
    tasa_total = tam_original / tam_diccionario
ahorro = 100 * (1 - tam_comprimido / tam_original)
# limite teorico N*H/8 bytes
tam_teorico = N * H / 8
tasa_teorica = (tam_original / tam_teorico) if tam_teorico > 0 else float('inf')

print("\n====== Compresión ======")
print("Tamaño original                    : %d bytes" % tam_original)
print("Bits Huffman útiles                : %d bits" % compressed_length_bit)
print("Tamaño comprimido (.huffman)       : %d bytes  (en disco: %d)"
      % (tam_comprimido, os.path.getsize(file_huffman_comprimido)))
print("Tamaño diccionario (.csv)          : %d bytes" % tam_diccionario)
print("Tasa de compresión (orig/comp)     : %.4f : 1" % tasa)
print("Tasa incl. diccionario             : %.4f : 1" % tasa_total)
print("Ahorro de espacio                  : %.2f %%" % ahorro)
print("Límite teórico N*H/8               : %.1f bytes (tasa máx. %.4f : 1)"
      % (tam_teorico, tasa_teorica))
