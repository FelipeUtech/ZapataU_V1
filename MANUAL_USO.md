# 📖 MANUAL DE USO

## Sistema de Análisis de Zapatas 3D con OpenSees

**Versión:** 1.0
**Última actualización:** Noviembre 2024

---

## 📑 TABLA DE CONTENIDOS

1. [Introducción](#-introducción)
2. [Inicio Rápido](#-inicio-rápido)
3. [Configuración del Análisis](#-configuración-del-análisis)
4. [Ejecución del Análisis](#-ejecución-del-análisis)
5. [Interpretación de Resultados](#-interpretación-de-resultados)
6. [Visualización](#-visualización)
7. [Ejemplos](#-ejemplos)
8. [Casos de Uso Avanzados](#-casos-de-uso-avanzados)

---

## 🎯 INTRODUCCIÓN

Este sistema permite analizar el comportamiento de zapatas superficiales mediante:

- **Generación automática de mallas 3D** con GMSH
- **Análisis de elementos finitos** con OpenSees
- **Modelado de interacción suelo-estructura**
- **Visualización 3D** de resultados con PyVista/ParaView

### Capacidades del Sistema

✅ Zapatas rectangulares o cuadradas
✅ Múltiples estratos de suelo
✅ Análisis bifásico (gravedad + carga)
✅ Elementos tetraédricos de 4 nodos
✅ Condiciones de simetría (cuarto de modelo)
✅ Exportación a ParaView (VTU)
✅ Reportes automáticos

---

## 🚀 INICIO RÁPIDO

### 1. Verificar Instalación

```cmd
:: Activar entorno virtual (si usas uno)
venv\Scripts\activate

:: Verificar instalación
python verificar_instalacion.py
```

Debe mostrar `✅` para todas las dependencias.

### 2. Ejecutar Análisis de Ejemplo

```cmd
python run_full_analysis.py
```

Este comando ejecuta el análisis con la configuración por defecto en `mesh_config.json`:

- Zapata 2m × 3m × 0.4m
- Profundidad de desplante: 1.5m
- 3 estratos de suelo
- Carga de columna: 1,000 kN

### 3. Revisar Resultados

Los resultados se generan en:

```
resultados_opensees/
├── desplazamientos.csv      # Desplazamientos de todos los nodos
├── tensiones.csv             # Tensiones en elementos
├── reacciones.csv            # Reacciones en apoyos
├── estadisticas.txt          # Resumen de resultados
├── resultados_opensees.vtu   # Archivo para ParaView
└── REPORTE_ANALISIS.txt      # Reporte completo
```

---

## ⚙️ CONFIGURACIÓN DEL ANÁLISIS

### Archivo de Configuración: `mesh_config.json`

Este archivo JSON define toda la geometría y parámetros del análisis.

#### Estructura del Archivo

```json
{
  "geometry": {
    "domain": { ... },       // Dimensiones del dominio
    "footing": { ... }       // Dimensiones de la zapata
  },
  "soil_layers": [ ... ],    // Estratos de suelo
  "footing_material": { ... },  // Material de la zapata
  "mesh_refinement": { ... },   // Control de refinamiento
  "output": { ... }          // Configuración de salida
}
```

### 1. Configurar Dominio

```json
"domain": {
  "Lx": 9.0,                // Ancho total del dominio (m)
  "Ly": 9.0,                // Largo total del dominio (m)
  "Lz": 20.0,               // Profundidad del dominio (m)
  "quarter_domain": true,   // true = cuarto de simetría
  "_comment": "Lx y Ly deben ser ≥ 3×max(B,L) de la zapata"
}
```

**Reglas:**
- `Lx` y `Ly` ≥ 3 veces la dimensión máxima de la zapata
- `Lz` = suma de espesores de estratos
- `quarter_domain: true` reduce tiempo de cómputo 75%

### 2. Configurar Zapata

```json
"footing": {
  "B": 2.0,        // Ancho en dirección X (m)
  "L": 3.0,        // Largo en dirección Y (m)
  "Df": 1.5,       // Profundidad de desplante (m)
  "tz": 0.4,       // Espesor/peralte de zapata (m)
  "_comment": "B × L para zapata rectangular"
}
```

**Parámetros:**
- `B`: Ancho (menor dimensión, eje X)
- `L`: Largo (mayor dimensión, eje Y)
- Para zapata cuadrada: `B = L`
- `Df`: Profundidad desde superficie hasta tope de zapata
- `tz`: Espesor del elemento estructural de la zapata

### 3. Configurar Estratos de Suelo

```json
"soil_layers": [
  {
    "name": "SOIL_1",
    "thickness": 3.0,       // Espesor del estrato (m)
    "material_id": 1,       // ID único del material
    "description": "Arena limosa"
  },
  {
    "name": "SOIL_2",
    "thickness": 10.0,
    "material_id": 2,
    "description": "Arcilla"
  }
]
```

**Importante:**
- Estratos se apilan de arriba hacia abajo
- `Σ thickness` debe ser igual a `domain.Lz`
- IDs de material deben ser únicos y consecutivos

### 4. Configurar Material de Zapata

```json
"footing_material": {
  "name": "FOOTING",
  "material_id": 4,          // Usar ID diferente de suelos
  "description": "Concreto f'c=210 kg/cm²"
}
```

### 5. Configurar Refinamiento de Malla

```json
"mesh_refinement": {
  "lc_footing": 0.33,        // Tamaño de elemento en zapata (m)
  "lc_near": 0.40,           // Tamaño cerca de zapata (m)
  "lc_far": 2.0,             // Tamaño en fronteras lejanas (m)
  "growth_rate": 1.2,        // Tasa de crecimiento de elementos
  "optimize_netgen": true    // Optimización de malla
}
```

**Recomendaciones:**

| Nivel | lc_footing | lc_near | lc_far | Nodos aprox. | Tiempo |
|-------|------------|---------|--------|--------------|--------|
| Burdo | 0.5 | 0.8 | 3.0 | 300-500 | 1-2 min |
| Medio | 0.33 | 0.5 | 2.0 | 800-1,200 | 5-10 min |
| Fino | 0.2 | 0.3 | 1.5 | 2,000-3,000 | 15-30 min |

**Balance:** Menos tamaño = más precisión pero más tiempo de cómputo

### 6. Configurar Propiedades de Materiales: `config.py`

```python
# Estratos de suelo
ESTRATOS_SUELO = [
    {
        'nombre': 'Arena limosa',
        'E': 5_000,         # Módulo de Young (kPa)
        'nu': 0.3,          # Relación de Poisson
        'rho': 1800,        # Densidad (kg/m³)
        'descripcion': 'Estrato superficial'
    },
    {
        'nombre': 'Arcilla',
        'E': 20_000,        # kPa
        'nu': 0.3,
        'rho': 1800,
        'descripcion': 'Estrato intermedio'
    }
]

# Material de zapata
MATERIAL_ZAPATA = {
    'E': 25_000_000,        # kPa (25 GPa típico concreto)
    'nu': 0.2,
    'rho': 2400,            # kg/m³
    'fc': 210               # f'c en kg/cm² (información)
}

# Cargas
CARGAS = {
    'P_column': 1000.0,     # Carga de columna (kN)
    'distribuir_nodos': 6   # Nodos para distribuir carga
}
```

**Rangos típicos de módulos de Young para suelos (kPa):**

| Tipo de Suelo | E (kPa) |
|---------------|---------|
| Arena suelta | 10,000 - 20,000 |
| Arena densa | 50,000 - 100,000 |
| Arcilla blanda | 2,000 - 5,000 |
| Arcilla firme | 10,000 - 20,000 |
| Arcilla dura | 30,000 - 100,000 |
| Roca meteorizada | 100,000 - 500,000 |

---

## 🎮 EJECUCIÓN DEL ANÁLISIS

### Script Maestro: `run_full_analysis.py`

Este script ejecuta todo el pipeline automáticamente.

#### Uso Básico

```cmd
python run_full_analysis.py
```

Ejecuta los 7 pasos:
1. Verificación de dependencias
2. Generación de malla 3D
3. Conversión a formato OpenSees
4. Verificación de contacto zapata-suelo
5. Análisis estructural con OpenSees
6. Generación de visualizaciones
7. Creación de reporte

#### Opciones del Script

```cmd
:: Ver ayuda
python run_full_analysis.py --help

:: Usar configuración personalizada
python run_full_analysis.py --config mi_zapata.json

:: Solo generar malla (no analizar)
python run_full_analysis.py --skip-analysis

:: Usar malla existente (solo analizar)
python run_full_analysis.py --skip-mesh

:: Modo verboso (debugging)
python run_full_analysis.py --verbose
```

#### Ejecución Manual Paso a Paso

Si prefieres ejecutar cada paso manualmente:

```cmd
:: PASO 1: Generar malla
python generate_mesh_from_config.py mesh_config.json

:: PASO 2: Convertir a OpenSees
python gmsh_to_opensees.py mallas/zapata_3D_cuarto_refined.vtu

:: PASO 3: Verificar contacto
python verificar_contacto_zapata_suelo.py

:: PASO 4: Ejecutar análisis
python run_opensees_analysis.py

:: PASO 5: Exportar a ParaView
python visualizar_resultados_opensees.py --export-only
```

---

## 📊 INTERPRETACIÓN DE RESULTADOS

### 1. Estadísticas Resumen: `estadisticas.txt`

```
ESTADÍSTICAS DE RESULTADOS - DESPLAZAMIENTOS INCREMENTALES

Desplazamientos verticales (uz) - INCREMENTALES:
   Máximo (asentamiento): 0.025639 m = 25.639 mm
   Mínimo: 0.000000e+00 m
   Promedio: -7.035600e-03 m
```

**Interpretación:**
- **Asentamiento máximo**: 25.6 mm (incremental por carga de columna)
- El análisis bifásico separa:
  - Fase 1: Asentamiento por peso propio (establecer campo de tensiones)
  - Fase 2: Asentamiento incremental por carga (el que se reporta)

### 2. Desplazamientos: `desplazamientos.csv`

Formato:
```csv
# node,x,y,z,ux,uy,uz,u_total
1,0.000000,0.000000,-3.000000,-1.234e-03,5.678e-04,-2.345e-03,2.789e-03
```

Columnas:
- `node`: ID del nodo
- `x, y, z`: Coordenadas originales (m)
- `ux, uy, uz`: Desplazamientos en cada dirección (m)
- `u_total`: Magnitud total del desplazamiento (m)

**Análisis:**
- Filtrar nodos en superficie de zapata para asentamiento
- Verificar que desplazamientos laterales sean pequeños
- Identificar zonas de máximo asentamiento

### 3. Tensiones: `tensiones.csv`

Formato:
```csv
# elem,sxx,syy,szz,sxy,syz,szx,von_mises
1,1.234e+02,-5.678e+01,-3.456e+02,1.234e+01,5.678e+00,2.345e+00,3.456e+02
```

Componentes del tensor de tensiones (kPa):
- `sxx, syy, szz`: Tensiones normales en X, Y, Z
- `sxy, syz, szx`: Tensiones cortantes
- `von_mises`: Tensión de von Mises (criterio de falla)

**Criterios de Evaluación:**

Para suelos:
- Tensión vertical (`szz`) debe ser compresiva (negativa)
- Verificar que no exceda capacidad portante
- Comparar tensión de von Mises con resistencia del suelo

Para zapata de concreto:
- Tensión de von Mises < 0.85 f'c
- Ejemplo: f'c = 210 kg/cm² → σ_max ≈ 17,850 kPa

### 4. Reacciones: `reacciones.csv`

```csv
# node,x,y,z,Rx,Ry,Rz,R_total
10,0.000,0.000,-20.000,12.34,5.67,-89.01,90.12
```

- Reacciones en nodos de base fija
- Suma de `Rz` ≈ Carga aplicada + Peso propio
- Verificar equilibrio global

---

## 🎨 VISUALIZACIÓN

### Opción 1: ParaView (Recomendado)

**Instalación:**
- Descargar desde: https://www.paraview.org/download/
- Instalar versión estable

**Uso:**

1. Abrir ParaView
2. `File → Open → resultados_opensees/resultados_opensees.vtu`
3. Hacer click en `Apply`
4. Seleccionar campo a visualizar:
   - **Uz**: Desplazamiento vertical (asentamiento)
   - **Displacement_Magnitude**: Magnitud total
   - **Von_Mises_Stress**: Tensión de von Mises
   - **Material_ID**: Identificar materiales

**Tips ParaView:**

```
# Ver malla deformada (Factor de escala para amplificar desplazamientos)
Filters → Common → Warp By Vector
  - Vectors: Displacement
  - Scale Factor: 100 (amplifica x100)

# Crear corte en plano
Filters → Common → Slice
  - Plane: XY (Z normal)
  - Origin: z = -1.5 (nivel de zapata)

# Mostrar solo zapata
Threshold filter:
  - Scalars: Material_ID
  - Min: 4, Max: 4
```

### Opción 2: Visualización con Python (Interactiva)

```cmd
:: Con ventana interactiva
python visualizar_resultados_opensees.py

:: Solo exportar VTU (sin ventana)
python visualizar_resultados_opensees.py --export-only

:: Cambiar factor de escala de deformaciones
python visualizar_resultados_opensees.py --scale 200
```

---

## 💡 EJEMPLOS

### Ejemplo 1: Zapata Cuadrada en Suelo Homogéneo

**Configuración (`mesh_config.json`):**

```json
{
  "geometry": {
    "domain": {
      "Lx": 9.0, "Ly": 9.0, "Lz": 20.0,
      "quarter_domain": true
    },
    "footing": {
      "B": 2.5, "L": 2.5,  // Zapata cuadrada 2.5×2.5
      "Df": 1.0,           // 1m de profundidad
      "tz": 0.35
    }
  },
  "soil_layers": [
    {
      "name": "SUELO_UNIFORME",
      "thickness": 20.0,   // Todo el dominio
      "material_id": 1
    }
  ],
  "footing_material": {
    "name": "FOOTING",
    "material_id": 2
  },
  "mesh_refinement": {
    "lc_footing": 0.4,
    "lc_near": 0.6,
    "lc_far": 2.5
  }
}
```

**Material (`config.py`):**

```python
ESTRATOS_SUELO = [
    {
        'nombre': 'Arena densa',
        'E': 60_000,      // Arena densa
        'nu': 0.3,
        'rho': 1900
    }
]

CARGAS = {
    'P_column': 800.0     // 800 kN
}
```

**Ejecución:**

```cmd
python run_full_analysis.py
```

### Ejemplo 2: Zapata Rectangular en Suelo Estratificado

**Configuración:**

```json
{
  "geometry": {
    "footing": {
      "B": 1.5,  // Ancho 1.5m
      "L": 3.0,  // Largo 3.0m (rectangular)
      "Df": 1.2,
      "tz": 0.30
    }
  },
  "soil_layers": [
    {
      "name": "RELLENO",
      "thickness": 2.0,
      "material_id": 1
    },
    {
      "name": "ARCILLA",
      "thickness": 8.0,
      "material_id": 2
    },
    {
      "name": "ARENA",
      "thickness": 10.0,
      "material_id": 3
    }
  ]
}
```

**Material:**

```python
ESTRATOS_SUELO = [
    {'nombre': 'Relleno', 'E': 3_000, 'nu': 0.35, 'rho': 1600},
    {'nombre': 'Arcilla', 'E': 15_000, 'nu': 0.4, 'rho': 1750},
    {'nombre': 'Arena', 'E': 50_000, 'nu': 0.3, 'rho': 1900}
]

CARGAS = {'P_column': 1200.0}
```

---

## 🔬 CASOS DE USO AVANZADOS

### Estudio Paramétrico: Variar Profundidad de Desplante

Crear múltiples configuraciones:

```cmd
:: Copiar configuración base
copy mesh_config.json zapata_Df1.0.json
copy mesh_config.json zapata_Df1.5.json
copy mesh_config.json zapata_Df2.0.json

:: Editar cada archivo cambiando "Df"

:: Ejecutar cada caso
python run_full_analysis.py --config zapata_Df1.0.json
python run_full_analysis.py --config zapata_Df1.5.json
python run_full_analysis.py --config zapata_Df2.0.json

:: Comparar resultados en estadisticas.txt
```

### Análisis de Convergencia de Malla

Ejecutar con diferentes refinamientos:

| Caso | lc_footing | Nodos | Asentamiento (mm) |
|------|------------|-------|-------------------|
| 1 | 0.8 | ~300 | 27.5 |
| 2 | 0.5 | ~600 | 26.2 |
| 3 | 0.33 | ~900 | 25.8 |
| 4 | 0.25 | ~1,500 | 25.7 |

Convergencia cuando diferencia < 5%

### Exportar Datos para Análisis Externo

```python
# script_exportar.py
import pandas as pd

# Leer desplazamientos
df_disp = pd.read_csv('resultados_opensees/desplazamientos.csv', comment='#')

# Filtrar nodos en superficie de zapata (z ≈ -Df)
zapata_surface = df_disp[abs(df_disp['z'] + 1.5) < 0.1]

# Calcular asentamiento promedio
asentamiento_prom = zapata_surface['uz'].mean() * 1000  # mm

print(f"Asentamiento promedio zapata: {asentamiento_prom:.2f} mm")

# Exportar a Excel
zapata_surface.to_excel('analisis_zapata.xlsx', index=False)
```

---

## 📞 SOPORTE Y DOCUMENTACIÓN ADICIONAL

### Archivos de Referencia

- **README.md** - Descripción general
- **INSTALL_WINDOWS.md** - Instalación detallada
- **requirements.txt** - Dependencias
- **config.py** - Parámetros de materiales

### Flujo de Trabajo Típico

```
1. Definir geometría → mesh_config.json
2. Definir materiales → config.py
3. Ejecutar análisis → run_full_analysis.py
4. Revisar reporte → resultados_opensees/REPORTE_ANALISIS.txt
5. Visualizar → ParaView (resultados_opensees.vtu)
6. Analizar datos → desplazamientos.csv, tensiones.csv
7. Ajustar y re-analizar si necesario
```

### Preguntas Frecuentes

**P: ¿Cuánto tarda un análisis típico?**
R: Entre 2-15 minutos dependiendo del refinamiento:
   - Malla burda: 2-5 min
   - Malla media: 5-10 min
   - Malla fina: 10-30 min

**P: ¿Puedo analizar zapatas circulares?**
R: Actualmente solo rectangulares/cuadradas. Para circular, aproximar con zapata cuadrada equivalente.

**P: ¿Cómo modelo zapatas con pedestales?**
R: Aumentar `tz` y asignar material más rígido en `config.py`.

**P: ¿Los resultados son confiables?**
R: Depende de:
   - Calidad de parámetros de suelo (lo más crítico)
   - Refinamiento de malla (hacer estudio de convergencia)
   - Modelo constitutivo (actualmente elástico lineal)

---

**Fin del Manual de Uso**

**Versión:** 1.0
**Última actualización:** Noviembre 2024
