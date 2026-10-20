# Proyecto 3: Teoría de la Información — Códigos de Huffman

## 1. Descripción
Este proyecto explora la relación entre la Teoría de la Información y los códigos de Huffman. Consiste en implementar un codificador y decodificador de Huffman en Python para comprimir y restaurar datos de diversas fuentes (texto, binarios e imágenes), calculando métricas teóricas como la entropía, longitud media, varianza y eficiencia, y analizando el impacto de la redundancia en la compresión sin pérdida.

## 2. Objetivos
*   **Objetivo General:** Comprender y aplicar el algoritmo de Huffman para la compresión de datos sin pérdida, analizando su rendimiento teórico y práctico frente a diferentes distribuciones de probabilidad (entropía de la fuente).
*   **Objetivos Específicos:**
    *   Implementar la generación del árbol y diccionario de códigos de Huffman.
    *   Calcular métricas de información: entropía, longitud media, varianza y eficiencias.
    *   Comprimir datos generando archivos binarios (`.huffman`) y diccionarios (`.csv`).
    *   Descomprimir los datos y verificar la integridad bit a bit de la información original.
    *   Analizar casos esquina (como fuentes con entropía cero) y comparar resultados entre formatos de imagen (TIFF vs. JPG).

## 3. Metas
*   Desarrollar un script funcional de codificación (`huffman_codificador.py`) y otro de decodificación (`huffman_decodificador.py`).
*   Procesar y comparar los resultados de los archivos: `solo_abc_cien.txt`, `shannon_intro.txt`, `todo_ascii_cien.bin`, `h_cero.bin`, y las imágenes (`4.1.01.tiff`, `7.1.02.tiff`, `5.1.11.tiff`, `5.1.13.tiff`, `4.2.03.tiff`, `7.1.02_loss.jpg`).
*   Entregar un reporte final con tablas sumarizadas de codificación, decodificación y análisis de resultados.

---

## 4. Responsabilidades del Grupo

*   **Persona 1 (Codificador):** Desarrollo y validación de `huffman_codificador.py`. Cálculo de métricas y generación de los archivos `.huffman` y `.diccionario.csv`.
*   **Persona 2 (Decodificador):** Desarrollo y validación de `huffman_decodificador.py`. Reconstrucción del árbol desde el `.csv`, lectura del `.huffman` y verificación de integridad (archivo original vs. recuperado).
*   **Persona 3 (Documentación y Resultados del Codificador):** Redacción en el reporte de la sección de codificación. Creación de tablas comparativas de entropía, longitud media, varianza y eficiencias.
*   **Persona 4 (Documentación y Resultados del Decodificador):** Redacción en el reporte de la sección de descompresión y verificación. Creación de tablas de tamaño original vs. recuperado. Investigación sobre TIFF vs. JPG.
*   **Personas 1 y 2 (Conclusiones):** Redacción conjunta de las conclusiones finales basadas en los resultados de ambos scripts (validez del algoritmo, casos esquina y comparativa de imágenes).

---

## 5. Instructivo del Proyecto

### 2.1. Preparación
Descomprima los archivos fuente provistos. Descargue y descomprima los archivos de prueba en: https://sipi.usc.edu/database/misc.zip. Requiere Python 3 y uso de consola.

### 2.2. Algoritmo de Huffman
1. Revise `huffman_base.py`. ¿Cómo se implementa el algoritmo?
2. Revise `solo_abc_cien.txt`. ¿Cómo está codificado? ¿Cuántos bits por carácter? ¿Qué espera observar al correr Huffman?
3. Corra: `python3 huffman_base.py -i solo_abc_cien.txt`. Anote observaciones.
4. Revise `todo_ascii_cien.bin`, `shannon_intro.txt`, los TIFFs y `h_cero.bin` (use visor hexadecimal para los `.bin`). Genere hipótesis de salida.
5. Modifique el script para calcular: Entropía, Longitud media, Varianza, Eficiencia original y Eficiencia del nuevo código. Muestre en consola.
6. Corra el script con todos los archivos del punto 4. Explique los resultados.

### 2.3. Compresión por medio del código de Huffman
1. Genere el vector binario a partir del diccionario de Huffman. Explique el código provisto (relleno/padding a múltiplos de 8).
2. Convierta a bytes y escriba el archivo binario usando la variable `file_huffman_comprimido`.
3. Agregue el código para escribir el diccionario en CSV (`ruta_diccionario`). ¿Qué propósito tiene?
4. Calcule tamaño original, tamaño comprimido y tasa de compresión. Prevenga el caso esquina de entropía/longitud media cero.
5. Analice y discuta los resultados contra la teoría.

### 2.4. Restablecimiento de los datos originales - Descompresión
1. Agregue el código de lectura del CSV y reconstrucción del árbol. Explique su propósito.
2. Verifique que los datos estimados coinciden con los originales.
3. Escriba los datos estimados en un binario usando `recovered_path`.
4. Comente los resultados.

### 2.5. Efecto de la entropía de la fuente
1. Revise `7.1.02.tiff` y `7.1.02_loss.jpg`. ¿Qué diferencias hay? Investigue TIFF vs JPG.
2. Corra los scripts para ambos.
3. ¿Qué diferencias hay en los resultados? ¿Por qué el cambio es tan grande?

### 3. Evaluación
*   **Inicio:** 6.10.2026
*   **Fin:** 20.10.2026
*   **Valor:** 2% de la nota final.
*   **Entrega:** Reporte con resultados, análisis y conclusiones, incluyendo tablas sumarizadas de codificación y decodificación.

---

## 6. Archivos Actuales del Proyecto

*   **`huffman_base.py`**: Script original proporcionado por el profesor. Sirve como base teórica y estructural (clase `NodeTree`, lectura binaria, generación del árbol).
*   **`huffman_codificador.py`**: Script desarrollado por la Persona 1. Es un reemplazo/evolución de `huffman_base.py` que incluye cálculo de métricas, compresión y escritura de archivos.
*   **`solo_abc_cien.txt`**: Archivo de texto con el abecedario repetido 100 veces (distribución uniforme).
*   **`shannon_intro.txt`**: Texto de la introducción del paper de Shannon (texto real, alta redundancia).
*   **`h_cero.bin`**: Archivo binario de prueba (caso esquina de entropía cero, contiene un solo tipo de byte).
*   **`todo_ascii_cien.bin`**: Archivo binario con todos los caracteres ASCII.
*   **`4.1.01.tiff`, `7.1.02.tiff`, `5.1.11.tiff`, `5.1.13.tiff`, `4.2.03.tiff`**: Imágenes de prueba del dataset SIPI.
*   **`7.1.02_loss.jpg`**: Imagen con compresión lossy para comparar contra su versión TIFF.

---

## 7. Estado Actual del Proyecto (Codificador)

El script `huffman_codificador.py` ha sido desarrollado y validado. **No llama a `huffman_base.py`, sino que lo reemplaza**, tal como indica el punto 2.2.5 del instructivo ("Modifique el script").

### Características implementadas:
*   **Lectura y Frecuencias:** Lee el archivo en binario y calcula las probabilidades reales.
*   **Métricas (Sección 2.2.5):** Calcula Entropía (`H`), Entropía máxima (`log2(M)`), Longitud media (`L`), Varianza (`var`), Eficiencia original (`H/8`) y Eficiencia Huffman (`H/L`).
*   **Compresión (Sección 2.3):** Genera el vector binario, aplica el *padding* a múltiplos de 8, convierte a bytes y escribe el archivo `file_huffman_comprimido` (`.huffman`).
*   **Diccionario (Sección 2.3.3):** Escribe el archivo `ruta_diccionario` (`.diccionario.csv`) con el formato requerido (bits útiles + tabla de códigos).
*   **Tasas de Compresión (Sección 2.3.4):** Calcula tamaño original, comprimido, del diccionario, tasa de compresión, ahorro de espacio y límite teórico.
*   **Manejo de Casos Esquina:**
    *   Si el archivo está vacío, termina limpiamente.
    *   Si el archivo tiene un solo símbolo (`h_cero.bin`), fuerza un código de 1 bit (`'0'`) para evitar fallos y explica por qué la eficiencia es 0 pero la compresión es máxima.
    *   Evita divisiones por cero en los cálculos de tasas y eficiencias.

### Instrucciones de Ejecución:
Para texto o binarios:
```bash
python3 huffman_codificador.py -i shannon_intro.txt
```
Para imágenes (con bandera `-q` para modo silencioso y no saturar la consola):
```bash
python3 huffman_codificador.py -i 7.1.02.tiff -q
```
**Salidas generadas:** `shannon_intro.txt.huffman` y `shannon_intro.txt.diccionario.csv`.

### Próximos pasos:
El equipo queda a la espera del script `huffman_decodificador.py` (Persona 2), el cual deberá leer el archivo `.csv`, reconstruir el árbol con `insert_in_tree` y decodificar el archivo `.huffman` usando exactamente la cantidad de bits indicada en la primera línea del CSV, guardando el resultado en `recovered_path`.
```