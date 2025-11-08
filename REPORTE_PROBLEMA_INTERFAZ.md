# REPORTE: Problema de Conexión Zapata-Suelo

## 📋 RESUMEN EJECUTIVO

**Problema identificado:** La zapata y el suelo NO están conectados en el modelo de elementos finitos.

**Impacto:** El análisis OpenSees es inválido porque la zapata está "flotando" sin contacto con el suelo.

**Causa raíz:** Nodos duplicados en la interfaz zapata-suelo generados por GMSH.

**Solución:** Modificar el generador de malla para fusionar los volúmenes usando `fragment()`.

---

## 🔍 EVIDENCIA DEL PROBLEMA

### 1. Análisis de Nodos

**Nodos totales:** 969
- Nodos de zapata (Material 4): 58 nodos únicos
- Nodos de suelo (Materiales 1,2,3): 911 nodos únicos
- **Nodos compartidos:** 0 ❌

### 2. Nodos Duplicados Detectados

Ejemplo de nodos en la misma posición espacial pero con diferentes IDs:

| Nodo | Material | Posición (x, y, z) | Distancia |
|------|----------|-------------------|-----------|
| 144  | Zapata (4) | (4.0, 4.0, -1.9) | 0.000 m |
| 128  | Suelo (1)  | (4.0, 4.0, -1.9) | 0.000 m |

**Conclusión:** Hay nodos duplicados (distancia = 0.0 m) que deberían ser el mismo nodo.

### 3. Geometría de los Dominios

**Zapata (Material 4):**
- Nodos: 58
- Rango X: [4.000, 4.500] m
- Rango Y: [3.750, 4.500] m
- Rango Z: [-1.900, -1.500] m ← **0.4 m de altura (correcto)**

**Suelo (Materiales 1,2,3):**
- Nodos: 911
- Rango X: [0.000, 4.500] m
- Rango Y: [0.000, 4.500] m
- Rango Z: [-20.000, 0.000] m

**Superposición:**
- Z máximo del suelo: 0.000 m
- Z mínimo de la zapata: -1.900 m
- Los rangos SE SUPERPONEN, pero NO comparten nodos ❌

---

## 🐛 CAUSA RAÍZ

### Archivo: `generate_mesh_from_config.py`

**Líneas problemáticas: 176-189**

```python
# Se crean volúmenes separados
excav = gmsh.model.occ.addBox(x0/2, y0/2, z_base, excav_width, excav_length, tz+Df)
foot = gmsh.model.occ.addBox(x0/2, y0/2, z_base, foot_width, foot_length, tz)
gmsh.model.occ.synchronize()

# Se corta el suelo con la excavación
for i, soil_vol in enumerate(soil_volumes):
    soil_cut, _ = gmsh.model.occ.cut(
        [(3, soil_vol['tag'])],
        [(3, excav)],
        removeObject=True,
        removeTool=(i == len(soil_volumes) - 1)
    )
    soil_volumes[i]['tag_cut'] = soil_cut[0][1]

# ❌ PROBLEMA: La zapata (foot) nunca se fusiona con el suelo
# Los volúmenes están en la misma posición pero son independientes
```

**Por qué esto causa el problema:**

1. **`cut()`** corta el suelo para crear la excavación
2. **`foot`** se crea como volumen independiente en la misma ubicación
3. GMSH genera **superficies duplicadas** en la interfaz
4. Durante el meshing, GMSH crea **nodos separados** para cada superficie
5. Resultado: **Zapata y suelo desconectados**

---

## ✅ SOLUCIÓN

### Opción 1: Usar `fragment()` (RECOMENDADO)

Reemplazar el proceso de corte con fragmentación:

```python
# Después de crear todos los volúmenes (suelo + zapata)
all_volumes = [(3, v['tag']) for v in soil_volumes] + [(3, foot)]

# Fragmentar todos los volúmenes para que compartan interfaces
fragmented, _ = gmsh.model.occ.fragment(all_volumes, [])

# Actualizar referencias de volúmenes
# ... (procesar fragmented para identificar cada volumen)
```

**Ventajas de `fragment()`:**
- Fusiona automáticamente superficies coincidentes
- Garantiza que los volúmenes adyacentes compartan nodos
- Preserva todos los volúmenes originales

### Opción 2: Usar `fuse()` en etapas

```python
# Después de cortar el suelo
# Fusionar la zapata con la capa de suelo correspondiente

# Identificar capa que contiene la zapata
for i, soil_vol in enumerate(soil_volumes):
    if soil_vol['z_bottom'] <= z_base and soil_vol['z_top'] >= z_top:
        # Esta capa contiene la zapata
        fused, _ = gmsh.model.occ.fuse(
            [(3, soil_vol['tag_cut'])],
            [(3, foot)]
        )
        # Actualizar referencia
        break
```

---

## 🔧 VERIFICACIÓN POST-CORRECCIÓN

Después de corregir el generador de malla, ejecutar:

```bash
python generate_mesh_from_config.py
python gmsh_to_opensees.py mallas/zapata_3D_cuarto_refined.vtu
python analizar_interfaz.py
```

**Criterios de éxito:**

✅ Nodos compartidos > 0 (típicamente 20-50 nodos en interfaz)
✅ Distancia mínima entre zapata y suelo = 0.0 m (nodos coinciden)
✅ Mensaje: "La zapata y el suelo están conectados"

---

## 📊 IMPACTO EN EL ANÁLISIS

### Estado actual (CON el problema):
- ❌ Zapata flotante sin contacto con suelo
- ❌ Cargas no se transfieren al suelo
- ❌ Resultados no realistas (asentamientos artificiales)
- ❌ Análisis INVÁLIDO

### Estado esperado (SIN el problema):
- ✅ Zapata conectada al suelo mediante nodos compartidos
- ✅ Continuidad de desplazamientos en la interfaz
- ✅ Transferencia correcta de cargas
- ✅ Resultados físicamente consistentes

---

## 📝 CONDICIONES DE FRONTERA (CORRECTAS)

Las condiciones de frontera en `run_opensees_analysis.py:158-201` son **CORRECTAS**:

```python
# Base fija (z = z_min): empotrada
ops.fix(tag, 1, 1, 1)  # ux=1, uy=1, uz=1

# Simetría en X (x = 0): restringir desplazamiento en X
ops.fix(tag, 1, 0, 0)  # ux=1, uy=0, uz=0

# Simetría en Y (y = 0): restringir desplazamiento en Y
ops.fix(tag, 0, 1, 0)  # ux=0, uy=1, uz=0
```

**NO se requieren condiciones especiales en la interfaz zapata-suelo** porque:
- Los elementos tetraédricos comparten nodos naturalmente
- La continuidad está implícita en la malla
- No se necesitan `rigidLink`, `equalDOF`, ni elementos de contacto

---

## 🎯 ACCIONES REQUERIDAS

### Prioridad ALTA:
1. ✅ **Identificar el problema** (COMPLETADO)
2. 🔨 **Modificar `generate_mesh_from_config.py`** para usar `fragment()`
3. 🔨 **Regenerar la malla** con nodos compartidos
4. ✅ **Verificar la conexión** con `analizar_interfaz.py`

### Prioridad MEDIA:
5. 🔄 **Re-ejecutar análisis OpenSees** con malla corregida
6. 📊 **Validar resultados** (asentamientos razonables)

### Archivos afectados:
- `generate_mesh_from_config.py` (MODIFICAR)
- Malla generada en `mallas/` (REGENERAR)
- `opensees_input/*.tcl` (REGENERAR)

---

## 📚 REFERENCIAS TÉCNICAS

### GMSH OCC Boolean Operations:

- **`cut(object, tool)`**: Corta object con tool, crea nuevas superficies
- **`fuse(object, tool)`**: Fusiona volúmenes, comparte superficies comunes
- **`fragment(objects, [])`**: Fragmenta múltiples volúmenes, comparte todas las interfaces

**Documentación:**
- GMSH API: https://gmsh.info/doc/texinfo/gmsh.html#Geometry-module
- Sección: 9.2.3 Boolean operations

### OpenSees FourNodeTetrahedron:

No requiere tratamiento especial de interfaces cuando los nodos son compartidos.
La continuidad de desplazamientos está garantizada por la conectividad de la malla.

---

**Generado:** 2025-11-08
**Analista:** Claude Code
**Scripts de diagnóstico:**
- `analizar_interfaz.py`
- `visualizar_problema.py`
