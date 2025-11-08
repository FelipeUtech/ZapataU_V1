# Generador de Mallas Configurables para OpenSees

Sistema flexible para generar mallas tetraédricas 3D con N estratos de suelo mediante archivos de configuración JSON.

## 🚀 Uso Rápido

```bash
# Usar configuración por defecto (mesh_config.json)
python3 generate_mesh_from_config.py

# Usar configuración personalizada
python3 generate_mesh_from_config.py config_examples/config_2_layers.json
```

## 📋 Estructura del Archivo de Configuración

### 1. Geometría del Dominio

```json
"geometry": {
  "domain": {
    "Lx": 6.0,        // Longitud en X (metros)
    "Ly": 6.0,        // Longitud en Y (metros)
    "Lz": 10.0,       // Profundidad total (metros)
    "quarter_domain": true  // true = 1/4 dominio, false = dominio completo
  },
  "footing": {
    "B": 3.0,         // Ancho de zapata (metros)
    "Df": 1.5,        // Profundidad de fundación (metros)
    "tz": 0.5         // Espesor de zapata (metros)
  }
}
```

### 2. Estratos de Suelo

Define N capas de suelo de arriba hacia abajo. La suma de espesores debe igualar `Lz`.

```json
"soil_layers": [
  {
    "name": "SOIL_1",           // Nombre del estrato
    "thickness": 5.0,           // Espesor en metros
    "material_id": 1,           // ID de material para OpenSees
    "description": "Capa superior de suelo"
  },
  {
    "name": "SOIL_2",
    "thickness": 4.0,
    "material_id": 2,
    "description": "Capa intermedia de suelo"
  }
  // ... más capas según necesites
]
```

### 3. Material de Zapata

```json
"footing_material": {
  "name": "FOOTING",
  "material_id": 4,             // ID de material para OpenSees
  "description": "Zapata de concreto"
}
```

### 4. Refinamiento de Malla

```json
"mesh_refinement": {
  "lc_footing": 0.15,    // Tamaño fino en zapata (metros)
  "lc_near": 0.3,        // Tamaño en zona cercana (metros)
  "lc_far": 1.2,         // Tamaño en fronteras (metros)
  "growth_rate": 1.3,    // Tasa de crecimiento geométrico (>1.0)
  "optimize_netgen": true  // Optimizar malla con Netgen
}
```

**Guía de tamaños:**
- `lc_footing`: 0.10 - 0.20 m (refinamiento fino)
- `lc_near`: 0.25 - 0.40 m (transición)
- `lc_far`: 0.80 - 1.50 m (fronteras)
- `growth_rate`: 1.2 - 1.5 (suave a agresivo)

### 5. Configuración de Salida

```json
"output": {
  "filename": "mi_malla",              // Nombre base del archivo
  "formats": ["msh", "vtu", "xdmf"]    // Formatos a exportar
}
```

**Formatos disponibles:**
- `msh`: Gmsh (para visualización en Gmsh)
- `vtu`: VTK Unstructured Grid (para ParaView)
- `xdmf`: XDMF + HDF5 (para lectura en Python/FEniCS)

## 📁 Ejemplos Incluidos

### Configuración de 2 Estratos
```bash
python3 generate_mesh_from_config.py config_examples/config_2_layers.json
```

Genera malla con:
- 2 estratos de suelo (arena limosa + arcilla)
- Dominio: 8×8×6 m (cuarto)
- Zapata: 2.5×2.5×0.4 m

### Configuración de 5 Estratos
```bash
python3 generate_mesh_from_config.py config_examples/config_5_layers.json
```

Genera malla con:
- 5 estratos de suelo (relleno, arena fina, arcilla, arena gruesa, roca)
- Dominio: 10×10×15 m (cuarto)
- Zapata: 4×4×0.6 m

### Configuración por Defecto (3 Estratos)
```bash
python3 generate_mesh_from_config.py
# O equivalente:
python3 generate_mesh_from_config.py mesh_config.json
```

## 🔧 Crear Tu Propia Configuración

1. **Copia un ejemplo:**
   ```bash
   cp mesh_config.json mi_proyecto.json
   ```

2. **Edita el archivo JSON:**
   - Ajusta dimensiones del dominio
   - Define tus estratos de suelo
   - Configura refinamiento según precisión deseada

3. **Valida la configuración:**
   - La suma de espesores debe igualar `Lz`
   - Los IDs de materiales deben ser únicos
   - Los tamaños de refinamiento deben ser lógicos (fino < grueso)

4. **Genera la malla:**
   ```bash
   python3 generate_mesh_from_config.py mi_proyecto.json
   ```

## 📊 Salida Generada

Los archivos se guardan en la carpeta `mallas/`:

```
mallas/
├── mi_malla.msh       # Gmsh
├── mi_malla.vtu       # ParaView
├── mi_malla.xdmf      # XDMF metadata
└── mi_malla.h5        # HDF5 data
```

## 🔍 Visualización

**ParaView:**
```bash
paraview mallas/mi_malla.vtu
```

**Gmsh:**
```bash
gmsh mallas/mi_malla.msh
```

## ⚙️ Uso en OpenSees

La malla genera elementos `FourNodeTetrahedron` compatibles con OpenSees.

```tcl
# Ejemplo de uso en OpenSees
element FourNodeTetrahedron $eleTag $node1 $node2 $node3 $node4 $matTag
```

Los `material_id` del JSON corresponden a los `matTag` en OpenSees.

## 📝 Validaciones Automáticas

El script valida:
- ✅ Existencia de todos los campos requeridos
- ✅ Al menos una capa de suelo definida
- ✅ Espesores de capas suman `Lz`
- ✅ Archivo JSON válido

## 🐛 Solución de Problemas

**Error: "Espesores no suman Lz"**
```
Solución: Verifica que la suma de thickness de todas las capas = Lz
```

**Error: "No se encontró el archivo"**
```
Solución: Verifica la ruta del archivo JSON
```

**Malla muy gruesa/fina**
```
Solución: Ajusta lc_footing, lc_near, lc_far en mesh_refinement
```

## 📚 Referencias

- Elementos tetraédricos: `FourNodeTetrahedron` (OpenSees)
- Refinamiento: Crecimiento geométrico desde zapata
- Optimización: Algoritmo Netgen de Gmsh

## 💡 Consejos

1. **Precisión vs Tiempo:**
   - Mallas finas (lc < 0.15 m): Muy precisas pero lentas
   - Mallas gruesas (lc > 0.5 m): Rápidas pero menos precisas

2. **Estratos Delgados:**
   - Capas < 0.5 m requieren refinamiento fino (lc < 0.2 m)

3. **Dominios Grandes:**
   - Para Lx, Ly > 10 m, usar lc_far > 1.0 m

4. **Optimización:**
   - `optimize_netgen: true` mejora calidad pero tarda más
   - Desactivar para pruebas rápidas
