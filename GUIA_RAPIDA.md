# 🚀 Guía Rápida del Pipeline

## Pipeline Completo Implementado

### 📦 Archivos Creados

```
├── gmsh_to_opensees.py       ⭐ Conversor GMSH → OpenSees
├── run_pipeline.py            ⭐ Script central del pipeline
├── README.md                  📚 Documentación completa
└── opensees_input/           📂 Ejemplo de salida
    ├── nodes.tcl              - 969 nodos
    ├── elements.tcl           - 3,341 elementos tetraédricos
    ├── materials.tcl          - Template de materiales
    ├── mesh_info.txt          - Estadísticas
    └── example_opensees.tcl   - Script de ejemplo OpenSees
```

---

## 🎯 Uso Rápido

### Opción 1: Pipeline Automático (Recomendado)

```bash
# Ejecutar todo automáticamente
python run_pipeline.py

# Con opciones adicionales
python run_pipeline.py --visualize --run-analysis
```

### Opción 2: Paso a Paso

```bash
# 1. Generar malla
python generate_mesh_from_config.py mesh_config.json

# 2. Convertir a OpenSees
python gmsh_to_opensees.py mallas/zapata_3D_cuarto_refined.vtu

# 3. Editar materiales
nano opensees_input/materials.tcl

# 4. Usar en OpenSees
# Crear tu script .tcl que incluya:
#   source opensees_input/materials.tcl
#   source opensees_input/nodes.tcl
#   source opensees_input/elements.tcl
```

---

## 📋 Flujo de Trabajo Completo

```
1. Configuración
   └── Editar mesh_config.json (geometría, estratos, refinamiento)

2. Generación de Malla (GMSH)
   └── python generate_mesh_from_config.py
       └── Salida: mallas/*.{msh,vtu,xdmf}

3. Conversión a OpenSees
   └── python gmsh_to_opensees.py mallas/archivo.vtu
       └── Salida: opensees_input/*.tcl

4. Configuración de Materiales
   └── Editar opensees_input/materials.tcl

5. Análisis en OpenSees
   └── Crear script principal .tcl
   └── python run_analysis.py (o OpenSees directo)

6. Post-procesamiento
   └── python visualize_pyvista.py
```

---

## 🔧 Opciones del Pipeline

```bash
# Ver ayuda completa
python run_pipeline.py --help

# Usar configuración personalizada
python run_pipeline.py --config mi_config.json

# Saltar generación de malla (usar existente)
python run_pipeline.py --skip-mesh

# Solo convertir (sin regenerar malla)
python run_pipeline.py --skip-mesh

# Con visualización
python run_pipeline.py --visualize

# Pipeline completo + análisis
python run_pipeline.py --visualize --run-analysis

# Directorio de salida personalizado
python run_pipeline.py --output-dir mi_directorio
```

---

## 📊 Ejemplo de Salida

Archivo generado: `opensees_input/nodes.tcl`
```tcl
node 1 0.000000 0.000000 -3.000000
node 2 0.000000 0.000000 -13.000000
node 3 0.000000 4.500000 -3.000000
...
```

Archivo generado: `opensees_input/elements.tcl`
```tcl
element FourNodeTetrahedron 1 711 722 692 734 1
element FourNodeTetrahedron 2 701 759 708 785 1
...
```

Archivo generado: `opensees_input/materials.tcl`
```tcl
# Material 1 - SOIL_1
nDMaterial ElasticIsotropic 1 3.0e4 0.3 1.8

# Material 4 - FOOTING
nDMaterial ElasticIsotropic 4 2.5e7 0.2 2.4
```

---

## ✅ Verificación Rápida

```bash
# 1. Verificar mallas generadas
ls -lh mallas/

# 2. Verificar archivos OpenSees
ls -lh opensees_input/

# 3. Ver estadísticas
cat opensees_input/mesh_info.txt

# 4. Verificar número de nodos/elementos
wc -l opensees_input/nodes.tcl
wc -l opensees_input/elements.tcl
```

---

## 🎓 Documentación Completa

Ver `README.md` para:
- Instalación detallada
- Configuración de `mesh_config.json`
- Ejemplos completos
- Solución de problemas
- Referencias de OpenSees

---

## 🚨 Importante

⚠️ **Antes de ejecutar análisis OpenSees:**
1. Editar `opensees_input/materials.tcl` con parámetros correctos
2. Verificar condiciones de frontera
3. Definir cargas apropiadas

---

## 📞 Ayuda Rápida

```bash
# Ayuda de cada script
python run_pipeline.py --help
python gmsh_to_opensees.py --help
python generate_mesh_from_config.py --help
```

---

**¡Pipeline listo para usar! 🎉**
