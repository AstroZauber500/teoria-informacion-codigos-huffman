# Teoría de la Información — Códigos de Huffman

Implementación en Python de un **codificador y decodificador de Huffman** para compresión sin pérdida, con cálculo de métricas de teoría de la información (entropía, longitud media, varianza y eficiencia) y análisis del efecto de la redundancia en distintas fuentes de datos (texto, binarios e imágenes).

## Estructura del proyecto

```
├── huffman_codificador.py    # Codificador: árbol, diccionario, métricas y archivo .huffman
├── huffman_decodificador.py  # Decodificador: reconstrucción y verificación de integridad
├── run_tests.py              # Ejecutor de la suite de pruebas
├── instructivo.md            # Instructivo del proyecto
├── data/                     # Archivos de prueba (texto/, binarios/, imagenes/)
├── sim/                      # Salidas de simulación (codificación, decodificación, logs)
├── reporte/                  # Reporte final
└── tests/                    # Suite de pruebas unitarias
```

## Uso

Codificar un archivo:

```powershell
python huffman_codificador.py -i data/texto/solo_abc_cien.txt
```

Decodificar un archivo comprimido:

```powershell
python huffman_decodificador.py -i sim/codificacion/solo_abc_cien.huffman
```

Ejecutar las pruebas:

```powershell
python run_tests.py
```

## Métricas calculadas

- **Entropía** $H(X) = -\sum p_i \log_2 p_i$
- **Longitud media** del código $L = \sum p_i \, l_i$
- **Varianza** de las longitudes del código
- **Eficiencia** $\eta = H(X)/L$
- **Tasa de compresión**

Se contemplan casos esquina como fuentes de entropía cero (`h_cero.bin`), donde se fuerza un código de 1 bit por símbolo.
