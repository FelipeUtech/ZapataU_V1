# Sistema de Generación de Mallas para Análisis de Zapatas con OpenSees

Sistema completo para generar mallas tetraédricas 3D de zapatas en suelo estratificado y convertirlas a formato OpenSees para análisis de elementos finitos.

## 🎯 Características

- ✅ Generación automática de mallas tetraédricas 3D con GMSH
- ✅ Soporte para **N estratos de suelo** configurable via JSON
- ✅ Soporte para **zapatas rectangulares** (B × L) y cuadradas
- ✅ Modelo de cuarto de dominio con simetría para optimización
- ✅ Refinamiento gradual adaptativo cerca de la zapata
- ✅ Conversión automática a formato OpenSees (TCL)
- ✅ Pipeline completo automatizado
- ✅ Múltiples formatos de salida (MSH, VTU, XDMF)

## 📋 Tabla de Contenidos

1. [Instalación](#instalación)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Guía de Uso Rápido](#guía-de-uso-rápido)
4. [Pipeline Completo](#pipeline-completo)
5. [Configuración](#configuración)
6. [Scripts Principales](#scripts-principales)
7. [Formato de Salida OpenSees](#formato-de-salida-opensees)
8. [Ejemplos](#ejemplos)
9. [Flujo de Trabajo](#flujo-de-trabajo)
10. [Solución de Problemas](#solución-de-problemas)

---

## 🔧 Instalación

### Requisitos

```bash
# Python 3.8+
python >= 3.8

# Dependencias principales
gmsh >= 4.9.0
numpy >= 1.20.0
pyvista >= 0.38.0
meshio >= 5.0.0
openseespy >= 3.4.0 (opcional, para análisis)
```

### Instalación de dependencias

```bash
# Opción 1: Usando pip
pip install gmsh numpy pyvista meshio openseespy matplotlib

# Opción 2: Usando conda
conda install -c conda-forge gmsh numpy pyvista meshio
pip install openseespy
```

---

## 📁 Estructura del Proyecto

```
ZapataU_V1/
│
├── 🎯 SCRIPTS PRINCIPALES (PIPELINE)
│   ├── run_pipeline.py                    # ⭐ Script central que ejecuta todo
│   ├── generate_mesh_from_config.py       # Generador de malla GMSH
│   ├── gmsh_to_opensees.py               # Conversor GMSH → OpenSees
│   └── sync_config_to_json.py            # Sincronizador de configuración
│
├── ⚙️ CONFIGURACIÓN
│   ├── mesh_config.json                   # Configuración de malla (JSON)
│   └── config.py                         # Configuración en Python
│
├── 🔬 ANÁLISIS Y VISUALIZACIÓN
│   ├── run_analysis.py                    # Análisis con OpenSees
│   ├── visualize_mesh.py                  # Visualización de mallas
│   ├── visualize_pyvista.py              # Visualización con PyVista
│   └── extract_3d_settlements.py         # Extracción de resultados
│
├── 📂 DIRECTORIOS DE SALIDA
│   ├── mallas/                           # Mallas generadas (.msh, .vtu, .xdmf)
│   ├── opensees_input/                   # Archivos para OpenSees (.tcl)
│   └── images/                           # Imágenes de visualización
│
└── 📚 DOCUMENTACIÓN
    ├── README.md                         # Este archivo
    ├── README_mesh_config.md             # Configuración de mallas
    ├── README_ZAPATA_RECTANGULAR.md      # Zapatas rectangulares
    └── MALLAS_HEXAEDRICAS.md            # Mallas hexaédricas
```

---

## 🚀 Guía de Uso Rápido

### Opción 1: Pipeline Completo (Recomendado)

```bash
# Ejecutar todo el pipeline automáticamente
python run_pipeline.py

# O con opciones adicionales
python run_pipeline.py --visualize --run-analysis
```

Esto ejecutará automáticamente:
1. ✅ Sincronización de configuración
2. ✅ Generación de malla GMSH
3. ✅ Conversión a OpenSees
4. ✅ (Opcional) Visualización
5. ✅ (Opcional) Análisis

### Opción 2: Paso a Paso Manual

```bash
# 1. Generar malla
python generate_mesh_from_config.py mesh_config.json

# 2. Convertir a OpenSees
python gmsh_to_opensees.py mallas/zapata_3D_cuarto_refined.vtu

# 3. Editar materiales
nano opensees_input/materials.tcl

# 4. Ejecutar análisis
python run_analysis.py
```

---

## 🔄 Pipeline Completo

El script `run_pipeline.py` automatiza todo el flujo de trabajo:

### Uso Básico

```bash
# Pipeline completo con configuración default
python run_pipeline.py

# Con configuración personalizada
python run_pipeline.py --config mi_configuracion.json

# Con visualización y análisis
python run_pipeline.py --visualize --run-analysis

# Saltar regeneración de malla (usar existente)
python run_pipeline.py --skip-mesh

# Personalizar directorio de salida OpenSees
python run_pipeline.py --output-dir mi_directorio
```

### Opciones Disponibles

| Opción | Descripción |
|--------|-------------|
| `--config FILE` | Archivo de configuración JSON (default: mesh_config.json) |
| `--skip-mesh` | Saltar generación de malla (usar existente) |
| `--skip-conversion` | Saltar conversión a OpenSees |
| `--visualize` | Generar visualización de la malla |
| `--run-analysis` | Ejecutar análisis de OpenSees |
| `--output-dir DIR` | Directorio para archivos OpenSees (default: opensees_input) |

### Salida del Pipeline

```
opensees_input/
├── nodes.tcl          # Definición de todos los nodos
├── elements.tcl       # Definición de elementos tetraédricos
├── materials.tcl      # Template de materiales (EDITAR)
└── mesh_info.txt      # Información sobre la malla
```

---

## ⚙️ Configuración

### Archivo `mesh_config.json`

Este archivo define toda la configuración de la malla:

```json
{
  "geometry": {
    "domain": {
      "Lx": 9.0,           // Ancho total del dominio (m)
      "Ly": 9.0,           // Largo total del dominio (m)
      "Lz": 20.0,          // Profundidad del dominio (m)
      "quarter_domain": true  // Usar cuarto de modelo (simetría)
    },
    "footing": {
      "B": 2.0,            // Ancho de zapata en X (m)
      "L": 3.0,            // Largo de zapata en Y (m)
      "Df": 1.5,           // Profundidad de desplante (m)
      "tz": 0.4            // Espesor de zapata (m)
    }
  },

  "soil_layers": [
    {
      "name": "SOIL_1",
      "thickness": 3.0,
      "material_id": 1,
      "description": "Estrato superior"
    },
    {
      "name": "SOIL_2",
      "thickness": 10.0,
      "material_id": 2,
      "description": "Estrato intermedio"
    },
    {
      "name": "SOIL_3",
      "thickness": 7.0,
      "material_id": 3,
      "description": "Estrato profundo"
    }
  ],

  "footing_material": {
    "name": "FOOTING",
    "material_id": 4,
    "description": "Zapata de concreto"
  },

  "mesh_refinement": {
    "lc_footing": 0.333,   // Tamaño cerca de zapata
    "lc_near": 0.4,        // Tamaño zona cercana
    "lc_far": 2.0,         // Tamaño fronteras
    "growth_rate": 1.2,    // Tasa de crecimiento
    "optimize_netgen": true
  },

  "output": {
    "filename": "zapata_3D_cuarto_refined",
    "formats": ["msh", "vtu", "xdmf"]
  }
}
```

### Parámetros Clave

#### Geometría del Dominio

- **Lx, Ly**: Calculados típicamente como `factor × max(B, L)` donde factor = 3-5
- **Lz**: Suma de espesores de estratos
- **quarter_domain**: `true` usa simetría (1/4 del modelo), `false` usa modelo completo

#### Zapata

- **B**: Ancho (dimensión en X)
- **L**: Largo (dimensión en Y)
- Si `B = L`: zapata cuadrada
- Si `B ≠ L`: zapata rectangular
- **Df**: Profundidad de desplante desde superficie
- **tz**: Espesor de la zapata

#### Estratos de Suelo

Puedes definir **N estratos** con diferentes propiedades:

```json
{
  "name": "SOIL_N",
  "thickness": 5.0,       // Espesor en metros
  "material_id": N,       // ID único para OpenSees
  "description": "..."    // Descripción
}
```

**IMPORTANTE**: La suma de espesores debe igualar `Lz`

#### Refinamiento

- **lc_footing**: Tamaño de elemento cerca de zapata (típicamente `min(B,L)/5`)
- **lc_near**: Tamaño en zona de influencia
- **lc_far**: Tamaño en fronteras lejanas
- **growth_rate**: Tasa de transición (1.0-2.0)

---

## 📜 Scripts Principales

### 1. `generate_mesh_from_config.py`

Genera malla tetraédrica 3D usando GMSH.

```bash
# Uso básico
python generate_mesh_from_config.py

# Con configuración personalizada
python generate_mesh_from_config.py mi_config.json
```

**Entrada**: `mesh_config.json`
**Salida**: Archivos en `mallas/`:
- `*.msh` (GMSH)
- `*.vtu` (VTK/ParaView)
- `*.xdmf` (XDMF/HDF5)

**Características**:
- Refinamiento gradual adaptativo
- Soporte para N estratos
- Geometrías rectangulares y cuadradas
- Cuarto de dominio con simetría

### 2. `gmsh_to_opensees.py`

Convierte malla GMSH a formato OpenSees.

```bash
# Convertir malla
python gmsh_to_opensees.py mallas/zapata_3D_cuarto_refined.vtu

# Especificar directorio de salida
python gmsh_to_opensees.py mallas/mi_malla.vtu --output-dir mi_salida
```

**Entrada**: Archivo `.vtu` o `.msh`
**Salida**: Archivos `.tcl` en `opensees_input/`

**Archivos generados**:
- `nodes.tcl`: Definición de nodos
- `elements.tcl`: Elementos tetraédricos
- `materials.tcl`: Template de materiales
- `mesh_info.txt`: Estadísticas

### 3. `run_pipeline.py`

Ejecuta pipeline completo automatizado.

```bash
# Pipeline básico
python run_pipeline.py

# Pipeline completo con análisis
python run_pipeline.py --visualize --run-analysis
```

Ver sección [Pipeline Completo](#pipeline-completo) para más detalles.

### 4. `sync_config_to_json.py`

Sincroniza `config.py` a `mesh_config.json`.

```bash
python sync_config_to_json.py
```

---

## 📄 Formato de Salida OpenSees

### Archivo `nodes.tcl`

```tcl
# Definición de nodos
# Formato: node <tag> <x> <y> <z>

node 1 0.000000 0.000000 0.000000
node 2 0.450000 0.000000 0.000000
node 3 0.000000 0.450000 0.000000
...
```

### Archivo `elements.tcl`

```tcl
# Definición de elementos tetraédricos
# Formato: element FourNodeTetrahedron <tag> <n1> <n2> <n3> <n4> <matTag>

# Material 1 (SOIL_1)
element FourNodeTetrahedron 1 45 78 102 156 1
element FourNodeTetrahedron 2 45 89 102 123 1
...

# Material 2 (SOIL_2)
element FourNodeTetrahedron 523 234 456 789 901 2
...

# Material 4 (FOOTING)
element FourNodeTetrahedron 2341 1567 1890 2001 2134 4
...
```

### Archivo `materials.tcl` (Template)

```tcl
# IMPORTANTE: Editar con parámetros correctos!

# Material 1 - Estrato de suelo 1
# nDMaterial ElasticIsotropic <matTag> <E> <nu> <rho>
nDMaterial ElasticIsotropic 1 3.0e4 0.3 1.8  ;# COMPLETAR

# Material 2 - Estrato de suelo 2
nDMaterial ElasticIsotropic 2 5.0e4 0.3 1.9  ;# COMPLETAR

# Material 3 - Estrato de suelo 3
nDMaterial ElasticIsotropic 3 8.0e4 0.3 2.0  ;# COMPLETAR

# Material 4 - Zapata de concreto
nDMaterial ElasticIsotropic 4 2.5e7 0.2 2.4
```

### Uso en OpenSees

```tcl
# En tu script principal de OpenSees
wipe
model BasicBuilder -ndm 3 -ndf 3

# Cargar definiciones
source opensees_input/materials.tcl
source opensees_input/nodes.tcl
source opensees_input/elements.tcl

# Definir condiciones de frontera
# fixZ 0.0 1 1 1  ;# Ejemplo: base fija
# fixX 0.0 1 0 0  ;# Ejemplo: simetría en X=0
# fixY 0.0 0 1 0  ;# Ejemplo: simetría en Y=0

# Aplicar cargas
# pattern Plain 1 Linear {
#     load <nodeTag> 0.0 0.0 -100.0  ;# Carga vertical
# }

# Análisis
# constraints Plain
# numberer RCM
# system BandGeneral
# test NormDispIncr 1.0e-6 100
# algorithm Newton
# integrator LoadControl 0.1
# analysis Static
# analyze 10

# Resultados
# ...
```

---

## 💡 Ejemplos

### Ejemplo 1: Zapata Cuadrada Simple (1 estrato)

```json
{
  "geometry": {
    "domain": {"Lx": 10.0, "Ly": 10.0, "Lz": 10.0, "quarter_domain": true},
    "footing": {"B": 2.0, "L": 2.0, "Df": 1.0, "tz": 0.3}
  },
  "soil_layers": [
    {"name": "SOIL_1", "thickness": 10.0, "material_id": 1}
  ],
  "footing_material": {"name": "FOOTING", "material_id": 2},
  "mesh_refinement": {
    "lc_footing": 0.4, "lc_near": 0.6, "lc_far": 2.0, "growth_rate": 1.2
  },
  "output": {"filename": "zapata_simple", "formats": ["vtu", "msh"]}
}
```

### Ejemplo 2: Zapata Rectangular (3 estratos)

```json
{
  "geometry": {
    "domain": {"Lx": 15.0, "Ly": 15.0, "Lz": 20.0, "quarter_domain": true},
    "footing": {"B": 2.0, "L": 4.0, "Df": 1.5, "tz": 0.4}
  },
  "soil_layers": [
    {"name": "ARENA_SUELTA", "thickness": 5.0, "material_id": 1},
    {"name": "ARCILLA", "thickness": 10.0, "material_id": 2},
    {"name": "ARENA_DENSA", "thickness": 5.0, "material_id": 3}
  ],
  "footing_material": {"name": "CONCRETO", "material_id": 4},
  "mesh_refinement": {
    "lc_footing": 0.4, "lc_near": 0.6, "lc_far": 2.5, "growth_rate": 1.3
  },
  "output": {"filename": "zapata_rectangular_3estratos", "formats": ["vtu"]}
}
```

Ejecutar:

```bash
# Generar y convertir
python run_pipeline.py --config ejemplo2.json --visualize

# Editar materiales
nano opensees_input/materials.tcl

# Ejecutar análisis
python run_analysis.py
```

### Ejemplo 3: Pipeline con Análisis Completo

```bash
# 1. Crear configuración (editar mesh_config.json)
nano mesh_config.json

# 2. Ejecutar pipeline completo
python run_pipeline.py --visualize --run-analysis

# 3. Ver resultados
ls opensees_input/
ls mallas/
```

---

## 🔁 Flujo de Trabajo

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUJO DE TRABAJO                         │
└─────────────────────────────────────────────────────────────┘

1. CONFIGURACIÓN
   ├── Editar mesh_config.json
   │   ├── Definir geometría (dominio, zapata)
   │   ├── Definir estratos de suelo
   │   ├── Ajustar refinamiento
   │   └── Especificar salida
   │
   └── (Opcional) sync_config_to_json.py

2. GENERACIÓN DE MALLA
   ├── python generate_mesh_from_config.py
   │   ├── Lee mesh_config.json
   │   ├── Crea geometría con GMSH
   │   ├── Genera malla tetraédrica
   │   └── Exporta: .msh, .vtu, .xdmf
   │
   └── Salida: mallas/*.{msh,vtu,xdmf}

3. CONVERSIÓN A OPENSEES
   ├── python gmsh_to_opensees.py mallas/archivo.vtu
   │   ├── Lee malla VTU/MSH
   │   ├── Extrae nodos y elementos
   │   ├── Identifica materiales
   │   └── Genera archivos TCL
   │
   └── Salida: opensees_input/*.tcl

4. CONFIGURACIÓN DE MATERIALES
   ├── Editar opensees_input/materials.tcl
   │   ├── Definir propiedades de suelos
   │   ├── Definir propiedades de zapata
   │   └── Elegir modelo constitutivo
   │
   └── Opciones:
       ├── ElasticIsotropic (simple)
       ├── PressureDependMultiYield (avanzado)
       └── Otros modelos de OpenSees

5. ANÁLISIS EN OPENSEES
   ├── Crear script principal .tcl
   │   ├── source materials.tcl
   │   ├── source nodes.tcl
   │   ├── source elements.tcl
   │   ├── Definir condiciones de frontera
   │   ├── Aplicar cargas
   │   └── Resolver
   │
   └── python run_analysis.py (o OpenSees directo)

6. POST-PROCESAMIENTO
   ├── python extract_3d_settlements.py
   ├── python visualize_pyvista.py
   └── Análisis de resultados

┌─────────────────────────────────────────────────────────────┐
│           O usar: python run_pipeline.py                    │
│           para ejecutar pasos 1-3 automáticamente           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Solución de Problemas

### Error: "No se encontró el archivo mesh_config.json"

**Solución**:
```bash
# Crear desde config.py
python sync_config_to_json.py

# O crear manualmente
cp mesh_config.json.example mesh_config.json
nano mesh_config.json
```

### Error: "Espesores de capas no suman Lz"

**Solución**: Verificar que:
```python
sum(layer['thickness'] for layer in soil_layers) == Lz
```

Ejemplo:
```json
"Lz": 20.0,
"soil_layers": [
  {"thickness": 5.0},   // 0-5m
  {"thickness": 10.0},  // 5-15m
  {"thickness": 5.0}    // 15-20m  ✅ Total = 20m
]
```

### Advertencia: "Elemento tiene N nodos (esperado 4)"

**Causa**: Malla contiene elementos no tetraédricos.

**Solución**: Verificar opciones de malla en `mesh_config.json`:
```json
"mesh_refinement": {
  "lc_footing": 0.3,  // Reducir para más refinamiento
  ...
}
```

### Malla muy grande / lenta

**Soluciones**:
1. Aumentar tamaños de elemento:
```json
"lc_footing": 0.5,  // en vez de 0.3
"lc_far": 3.0       // en vez de 2.0
```

2. Usar cuarto de dominio:
```json
"quarter_domain": true
```

3. Reducir dominio:
```json
"Lx": 12.0,  // en vez de 15.0
"Ly": 12.0
```

### OpenSees: "Invalid material tag"

**Causa**: `materials.tcl` no editado o IDs inconsistentes.

**Solución**:
1. Editar `opensees_input/materials.tcl`
2. Verificar que material_id en config coincida con elementos

---

## 📊 Estadísticas Típicas

| Configuración | Nodos | Elementos | Tiempo Generación |
|---------------|-------|-----------|-------------------|
| Zapata 2×2m, 1 estrato, cuarto | ~500 | ~2,000 | ~5s |
| Zapata 2×3m, 3 estratos, cuarto | ~1,500 | ~7,000 | ~15s |
| Zapata 3×4m, 3 estratos, completo | ~8,000 | ~40,000 | ~60s |

---

## 🎓 Recursos Adicionales

### Documentación Relacionada

- `README_mesh_config.md` - Configuración detallada de mallas
- `README_ZAPATA_RECTANGULAR.md` - Zapatas rectangulares
- `MALLAS_HEXAEDRICAS.md` - Mallas hexaédricas estructuradas

### Enlaces Externos

- [OpenSees Documentation](https://opensees.berkeley.edu/)
- [GMSH Documentation](https://gmsh.info/)
- [PyVista Documentation](https://docs.pyvista.org/)

---

## 📝 Licencia

Este proyecto es parte de ZapataU - Sistema de análisis de zapatas con OpenSees.

---

## 👥 Contribuciones

Para reportar problemas o sugerir mejoras, crear un issue en el repositorio.

---

## 🚀 Inicio Rápido (Resumen)

```bash
# 1. Instalar dependencias
pip install gmsh numpy pyvista meshio openseespy

# 2. Ejecutar pipeline completo
python run_pipeline.py

# 3. Editar materiales
nano opensees_input/materials.tcl

# 4. Ejecutar análisis (crear tu script de OpenSees)
# O usar: python run_analysis.py

# 5. Visualizar resultados
python visualize_pyvista.py
```

---

**¡Listo para generar mallas y analizar zapatas! 🎉**
