# Generación de Mallas Hexaédricas para OpenSees

Este documento explica los scripts disponibles para generar mallas hexaédricas del modelo de zapata empotrada.

## 📁 Scripts Disponibles

### 1. `generate_mesh_quarter_hex.py` (Gmsh con recombinación)
**Método**: Usa Gmsh con algoritmos de recombinación para convertir tetraedros en hexaedros

**Características**:
- Genera geometría con cortes booleanos (excavación)
- Intenta recombinar elementos en hexaedros
- **Resultado**: Principalmente tetraedros (725 elementos)
- Útil para geometrías complejas

**Uso**:
```bash
python generate_mesh_quarter_hex.py
```

**Archivos generados**:
- `mallas/zapata_3D_cuarto_hex.msh` (Gmsh)
- `mallas/zapata_3D_cuarto_hex.vtu` (ParaView)
- `mallas/zapata_3D_cuarto_hex.xdmf` (OpenSees)

---

### 2. `generate_mesh_quarter_hex_structured.py` (Malla estructurada) ⭐ **RECOMENDADO PARA OPENSEES**
**Método**: Genera malla estructurada con hexaedros puros usando numpy

**Características**:
- ✅ **100% elementos hexaédricos** (7,584 hexaedros)
- ✅ Malla estructurada regular
- ✅ Mejor convergencia numérica para OpenSees
- ✅ Sin elementos degenerados
- ✅ Mejor para análisis de suelos con plasticidad

**Uso**:
```bash
python generate_mesh_quarter_hex_structured.py
```

**Archivos generados**:
- `mallas/zapata_3D_cuarto_hex_structured.msh` (Gmsh)
- `mallas/zapata_3D_cuarto_hex_structured.vtu` (ParaView)
- `mallas/zapata_3D_cuarto_hex_structured.xdmf` (OpenSees/FEniCS)
- `mallas/zapata_3D_cuarto_hex_structured.h5` (HDF5)

**Malla generada**:
- Nodos: 10,072
- Hexaedros: 7,584
- Distribución:
  - SOIL_1 (Capa 1): 4,480 elementos
  - SOIL_2 (Capa 2): 2,048 elementos
  - SOIL_3 (Capa 3): 1,024 elementos
  - FOOTING (Zapata): 32 elementos

---

### 3. `visualize_hex_mesh.py` (Visualización)
**Propósito**: Visualizar la malla antes de correr análisis en OpenSees

**Características**:
- 🎨 Vista completa de la malla con dominios coloreados
- 🔍 Vista detallada de la zapata
- ✂️ Corte transversal para ver capas
- 📊 Estadísticas de la malla

**Uso**:
```bash
python visualize_hex_mesh.py
```

**Controles interactivos**:
- Click izquierdo + arrastrar: Rotar
- Click derecho + arrastrar: Zoom
- Scroll: Zoom
- 'q': Cerrar ventana

---

## 🎯 ¿Cuál script usar?

### Para OpenSees → `generate_mesh_quarter_hex_structured.py` ⭐

**Razones**:
1. **Hexaedros puros**: OpenSees tiene mejor rendimiento con hexaedros
2. **Estabilidad numérica**: Malla estructurada evita elementos distorsionados
3. **Plasticidad de suelos**: Los hexaedros son superiores para modelos constitutivos no lineales
4. **Menos problemas de convergencia**: Elementos bien condicionados

### Para geometrías complejas → `generate_mesh_quarter_hex.py`

**Razones**:
- Cuando la geometría no permite malla estructurada
- Cuando se necesita refinamiento adaptativo
- Para geometrías con múltiples cortes y formas irregulares

---

## 📊 Visualización en ParaView

### Opción 1: Comando directo
```bash
paraview mallas/zapata_3D_cuarto_hex_structured.vtu
```

### Opción 2: Script de visualización
```bash
python visualize_hex_mesh.py
```

### Dentro de ParaView:
1. Abrir archivo `.vtu`
2. Click en "Apply"
3. En "Coloring" seleccionar "dominio"
4. Activar "Surface With Edges" para ver la malla

---

## 🔧 Integración con OpenSees

### Leer malla XDMF en Python (para OpenSees)
```python
import meshio

# Cargar malla
mesh = meshio.read("mallas/zapata_3D_cuarto_hex_structured.xdmf")

# Obtener nodos
nodes = mesh.points  # shape: (n_nodes, 3)

# Obtener conectividad de hexaedros
hex_cells = mesh.cells_dict["hexahedron"]  # shape: (n_elements, 8)

# Obtener IDs de dominio
domain_ids = mesh.cell_data["dominio"][0]  # shape: (n_elements,)

# Crear nodos en OpenSees
for i, (x, y, z) in enumerate(nodes, start=1):
    # ops.node(i, x, y, z)
    pass

# Crear elementos en OpenSees
for i, connectivity in enumerate(hex_cells, start=1):
    domain = domain_ids[i-1]
    # Seleccionar material según dominio
    # ops.element('SSPbrick', i, *connectivity, mat_tag, ...)
    pass
```

---

## 📐 Geometría del Modelo

### Parámetros (1/4 de dominio)
- **Dominio total**: 3.0 m × 3.0 m × 10.0 m
- **Zapata**: 0.75 m × 0.75 m × 0.5 m
- **Profundidad de desplante**: 1.5 m
- **Capas de suelo**:
  - Capa 1: 0 a -5.0 m (H1 = 5.0 m)
  - Capa 2: -5.0 a -9.0 m (H2 = 4.0 m)
  - Capa 3: -9.0 a -10.0 m (H3 = 1.0 m)

### Dominios (IDs)
1. `SOIL_1` → domain_id = 1 (color azul/verde claro)
2. `SOIL_2` → domain_id = 2 (color verde)
3. `SOIL_3` → domain_id = 3 (color amarillo)
4. `FOOTING` → domain_id = 4 (color rojo/naranja)

---

## 🚀 Flujo de trabajo recomendado

1. **Generar malla hexaédrica**:
   ```bash
   python generate_mesh_quarter_hex_structured.py
   ```

2. **Visualizar en ParaView** (verificar antes de análisis):
   ```bash
   python visualize_hex_mesh.py
   # O directamente:
   paraview mallas/zapata_3D_cuarto_hex_structured.vtu
   ```

3. **Importar en OpenSees**:
   - Usar archivo `.xdmf` o `.msh`
   - Leer nodos y elementos
   - Asignar materiales según `domain_id`
   - Definir condiciones de frontera
   - Correr análisis

---

## 📚 Librerías Requeridas

```bash
pip install gmsh numpy pyvista meshio
```

**Versiones recomendadas**:
- `gmsh >= 4.11`
- `numpy >= 1.20`
- `pyvista >= 0.40`
- `meshio >= 5.0`

---

## ✅ Ventajas de Hexaedros vs Tetraedros para OpenSees

| Característica | Hexaedros | Tetraedros |
|----------------|-----------|------------|
| **Precisión** | Alta | Media |
| **Convergencia** | Rápida | Lenta |
| **Elementos necesarios** | Menos | Más |
| **Plasticidad** | Excelente | Buena |
| **Tiempo de cómputo** | Menor | Mayor |
| **Estabilidad numérica** | Superior | Regular |
| **Hourglass modes** | Controlables | No aplica |

---

## 📞 Soporte

Para problemas o preguntas:
1. Verificar que la malla se visualiza correctamente en ParaView
2. Revisar estadísticas de la malla (nodos duplicados, elementos degenerados)
3. Ajustar parámetros de discretización en el script si es necesario

---

**Última actualización**: 2025-11-08
**Autor**: Generado con Claude Code
