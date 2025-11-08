# Visualización de Resultados OpenSees

Este documento describe cómo visualizar los resultados del análisis de OpenSees usando PyVista y ParaView.

## Instalación de PyVista

```bash
pip install pyvista
```

## Uso Básico

### 1. Exportar resultados a VTU (sin visualización interactiva)

```bash
python visualizar_resultados_opensees.py --export-only
```

Esto genera `resultados_opensees/resultados_opensees.vtu`

### 2. Visualización interactiva con PyVista

```bash
python visualizar_resultados_opensees.py
```

Controles de la ventana interactiva:
- **Click izquierdo + arrastrar**: Rotar modelo
- **Scroll**: Zoom in/out
- **Click derecho + arrastrar**: Pan (desplazar)
- **'q'**: Cerrar ventana

### 3. Ajustar escala de deformación

Por defecto, la escala de deformación es 100x para mejor visualización:

```bash
python visualizar_resultados_opensees.py --scale 50.0   # Escala 50x
python visualizar_resultados_opensees.py --scale 200.0  # Escala 200x
```

## Visualización en ParaView

### Abrir archivo VTU

```bash
paraview resultados_opensees/resultados_opensees.vtu
```

O desde la interfaz gráfica: `File > Open > resultados_opensees.vtu`

### Campos disponibles

#### Campos en nodos (Point Data):
- **Displacement**: Vector de desplazamiento 3D [m]
- **Displacement_Magnitude**: Magnitud del desplazamiento [m]
- **Ux, Uy, Uz**: Componentes de desplazamiento [m]

#### Campos en elementos (Cell Data):
- **Von_Mises_Stress**: Tensión de von Mises [kPa]
- **Stress_XX, Stress_YY, Stress_ZZ**: Tensiones normales [kPa]
- **Stress_XY, Stress_YZ, Stress_ZX**: Tensiones cortantes [kPa]
- **Material_ID**: ID del material del elemento

### Visualizaciones recomendadas en ParaView

#### 1. Desplazamientos verticales (Uz)

1. Aplicar filtro **Warp By Vector**:
   - `Filters > Common > Warp By Vector`
   - Vectors: `Displacement`
   - Scale Factor: `100` (ajustar según preferencia)

2. Colorear por `Uz`:
   - En el panel Properties, seleccionar `Uz` en "Coloring"
   - Ajustar escala de colores (azul = sin desplazamiento, rojo = máximo asentamiento)

#### 2. Tensión de von Mises

1. Aplicar **Warp By Vector** (opcional)
2. Colorear por `Von_Mises_Stress`
3. Ajustar rango de colores para resaltar zonas de alta tensión

#### 3. Cortes transversales

1. Aplicar filtro **Slice**:
   - `Filters > Common > Slice`
   - Plane: XY, YZ o XZ
   - Mover el plano con el slider "Origin"

2. Colorear por campo deseado (Uz, Von_Mises_Stress, etc.)

#### 4. Visualizar solo la zapata

1. Aplicar filtro **Threshold**:
   - `Filters > Common > Threshold`
   - Scalars: `Material_ID`
   - Minimum: `4`, Maximum: `4`

2. Esto muestra solo elementos con Material_ID = 4 (zapata de concreto)

#### 5. Vectores de desplazamiento

1. Aplicar filtro **Glyph**:
   - `Filters > Common > Glyph`
   - Glyph Type: `Arrow`
   - Orientation: `Displacement`
   - Scale Array: `Displacement_Magnitude`
   - Scale Factor: ajustar para visualización

## Estructura de archivos de resultados

```
resultados_opensees/
├── desplazamientos.csv       # Desplazamientos incrementales por nodo
├── reacciones.csv            # Reacciones en nodos fijos
├── tensiones.csv             # Tensiones en elementos
├── estadisticas.txt          # Resumen estadístico
└── resultados_opensees.vtu   # Archivo VTU para ParaView
```

## Notas importantes

### Desplazamientos incrementales

Los desplazamientos mostrados son **INCREMENTALES** (solo debidos a la carga de columna), no incluyen el asentamiento por gravedad. Esto es el procedimiento estándar en análisis geotécnico:

1. **Fase 1 (Gravedad)**: Establece campo de tensiones inicial
2. **Reseteo**: Desplazamientos se ponen en cero (mantiene tensiones)
3. **Fase 2 (Carga)**: Desplazamientos medidos son solo por carga aplicada

### Unidades

- **Longitudes**: metros [m]
- **Desplazamientos**: metros [m]
- **Tensiones**: kiloPascales [kPa]
- **Fuerzas**: kiloNewtons [kN]

### Interpretación de tensiones

- **Tensión de von Mises**: Tensión equivalente para criterio de falla
- **Tensiones negativas**: Compresión
- **Tensiones positivas**: Tracción
- En suelos típicamente predomina compresión (valores negativos)

## Solución de problemas

### Error: PyVista no instalado

```bash
pip install pyvista
```

### Error: No se puede abrir ventana interactiva

Usar modo export-only:
```bash
python visualizar_resultados_opensees.py --export-only
```

### ParaView no reconoce el archivo VTU

Verificar que el archivo existe:
```bash
ls -lh resultados_opensees/resultados_opensees.vtu
```

Regenerar si es necesario:
```bash
python visualizar_resultados_opensees.py --export-only
```

## Ejemplos de análisis avanzado

### Comparar desplazamientos en diferentes puntos

En Python, leer el CSV:
```python
import pandas as pd
df = pd.read_csv('resultados_opensees/desplazamientos.csv', comment='#')
print(df[['x', 'y', 'z', 'uz']].sort_values('uz'))
```

### Extraer tensiones máximas

```python
import pandas as pd
df_tensiones = pd.read_csv('resultados_opensees/tensiones.csv', comment='#')
print(f"Tensión máxima de von Mises: {df_tensiones['von_mises'].max():.2f} kPa")
print(f"Elemento con tensión máxima: {df_tensiones.loc[df_tensiones['von_mises'].idxmax(), 'elem']}")
```
