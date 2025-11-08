import gmsh
import numpy as np
import pyvista as pv
import meshio

# ---------------------------------
# Parámetros geométricos (EXACTOS del script original)
# ---------------------------------
Lx, Ly, Lz = 6.0, 6.0, 10.0
B, Df, tz = 3.0, 1.5, 0.5
H1, H2 = 5.0, 4.0
H3 = Lz - (H1 + H2)
x0, y0 = Lx - B / 2, Ly - B / 2
z_base, z_top = -Df - tz, -Df

# --- Solo 1/4 del dominio ---
Lx /= 2
Ly /= 2

# ---------------------------------
# Parámetros de refinamiento
# ---------------------------------
lc_footing = 0.15      # Tamaño fino en zapata (15 cm)
lc_near = 0.3          # Tamaño cerca de zapata (30 cm)
lc_far = 1.2           # Tamaño en fronteras lejanas (1.2 m)
growth_rate = 1.3      # Tasa de crecimiento geométrico

print("="*60)
print("Generando malla tetraédrica refinada para OpenSees")
print("="*60)
print(f"Refinamiento en zapata: {lc_footing} m")
print(f"Tamaño cerca de zapata: {lc_near} m")
print(f"Tamaño en fronteras: {lc_far} m")
print(f"Tasa de crecimiento: {growth_rate}")

# ---------------------------------
# Inicializar Gmsh
# ---------------------------------
gmsh.initialize()
gmsh.model.add("zapata_3D_cuarto_refined")

# ---------------------------------
# Crear sólidos (GEOMETRÍA EXACTA)
# ---------------------------------
soil1 = gmsh.model.occ.addBox(0, 0, -H1, Lx, Ly, H1)
soil2 = gmsh.model.occ.addBox(0, 0, -(H1 + H2), Lx, Ly, H2)
soil3 = gmsh.model.occ.addBox(0, 0, -Lz, Lx, Ly, H3)
excav = gmsh.model.occ.addBox(x0 / 2, y0 / 2, z_base, B / 4, B / 4, tz + Df)
foot = gmsh.model.occ.addBox(x0 / 2, y0 / 2, z_base, B / 4, B / 4, tz)
gmsh.model.occ.synchronize()

# Cortar la excavación
soil1_cut, _ = gmsh.model.occ.cut([(3, soil1)], [(3, excav)], removeObject=True, removeTool=False)
soil2_cut, _ = gmsh.model.occ.cut([(3, soil2)], [(3, excav)], removeObject=True, removeTool=False)
soil3_cut, _ = gmsh.model.occ.cut([(3, soil3)], [(3, excav)], removeObject=True, removeTool=True)
gmsh.model.occ.synchronize()

# Etiquetas
soil1_tag = soil1_cut[0][1]
soil2_tag = soil2_cut[0][1]
soil3_tag = soil3_cut[0][1]

# ---------------------------------
# Grupos físicos
# ---------------------------------
phys_s1 = gmsh.model.addPhysicalGroup(3, [soil1_tag])
gmsh.model.setPhysicalName(3, phys_s1, "SOIL_1")
phys_s2 = gmsh.model.addPhysicalGroup(3, [soil2_tag])
gmsh.model.setPhysicalName(3, phys_s2, "SOIL_2")
phys_s3 = gmsh.model.addPhysicalGroup(3, [soil3_tag])
gmsh.model.setPhysicalName(3, phys_s3, "SOIL_3")
phys_foot = gmsh.model.addPhysicalGroup(3, [foot])
gmsh.model.setPhysicalName(3, phys_foot, "FOOTING")
gmsh.model.occ.synchronize()

# ---------------------------------
# Configurar tamaño de malla con refinamiento gradual
# ---------------------------------
print("\nConfigurando refinamiento gradual con callback...")

# Centro de la zapata
x_center = (x0 / 2 + x0 / 2 + B / 4) / 2
y_center = (y0 / 2 + y0 / 2 + B / 4) / 2
z_center = (z_base + z_top) / 2

def size_callback(dim, tag, x, y, z, lc):
    """
    Calcula el tamaño de elemento según distancia a la zapata.
    Refinamiento fino en zapata, crecimiento geométrico hacia fronteras.
    """
    # Distancia 3D desde el centro de la zapata
    dx = x - x_center
    dy = y - y_center
    dz = z - z_center
    dist = np.sqrt(dx**2 + dy**2 + dz**2)

    # Función de crecimiento geométrico
    if dist < 0.5:
        # Muy cerca de zapata: refinamiento fino
        return lc_footing
    elif dist < 2.0:
        # Zona intermedia: transición con crecimiento geométrico
        # Interpolación exponencial
        t = (dist - 0.5) / 1.5  # Normalizar entre 0 y 1
        return lc_footing + (lc_near - lc_footing) * (t ** growth_rate)
    elif dist < 5.0:
        # Zona lejana: transición a tamaño grueso
        t = (dist - 2.0) / 3.0
        return lc_near + (lc_far - lc_near) * (t ** (growth_rate * 0.8))
    else:
        # Fronteras: tamaño grueso
        return lc_far

gmsh.model.mesh.setSizeCallback(size_callback)

# Opciones de malla
gmsh.option.setNumber("Mesh.Algorithm", 5)  # Delaunay
gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # Delaunay 3D
gmsh.option.setNumber("Mesh.Optimize", 1)
gmsh.option.setNumber("Mesh.OptimizeNetgen", 1)

# ---------------------------------
# Generar malla tetraédrica
# ---------------------------------
print("\nGenerando malla tetraédrica 3D...")
print("Esto puede tardar algunos minutos...")
gmsh.model.mesh.generate(3)

print("Optimizando malla...")
gmsh.model.mesh.optimize("Netgen")

gmsh.write("mallas/zapata_3D_cuarto_refined.msh")
print("✅ Guardado Gmsh: mallas/zapata_3D_cuarto_refined.msh")

# ---------------------------------
# Conversión a PyVista y exportes
# ---------------------------------
print("\nExtrayendo datos de malla...")
node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
points = node_coords.reshape(-1, 3)

# Obtener elementos tetraédricos (tipo 4)
etags, ntags = gmsh.model.mesh.getElementsByType(4)
connectivity = ntags - 1
tet_tags = etags

# Identificar dominio de cada elemento
domain_id = np.zeros(len(tet_tags), dtype=int)
color_map = {phys_s1: 1, phys_s2: 2, phys_s3: 3, phys_foot: 4}

for pg, color in color_map.items():
    ents = gmsh.model.getEntitiesForPhysicalGroup(3, pg)
    for ent in ents:
        etags_local, _ = gmsh.model.mesh.getElementsByType(4, ent)
        for eid in etags_local:
            idx = np.where(tet_tags == eid)[0]
            if len(idx) > 0:
                domain_id[idx] = color

# Crear grid PyVista
cells = np.insert(connectivity.reshape(-1, 4), 0, 4, axis=1).ravel()
celltypes = np.full(len(connectivity) // 4, pv.CellType.TETRA, dtype=np.uint8)
grid = pv.UnstructuredGrid(cells, celltypes, points)
grid.cell_data["dominio"] = domain_id

# Guardar VTU
vtu_path = "mallas/zapata_3D_cuarto_refined.vtu"
grid.save(vtu_path)
print(f"✅ Guardado VTK: {vtu_path}")

# Guardar XDMF
xdmf_path = "mallas/zapata_3D_cuarto_refined.xdmf"
cells_xdmf = connectivity.reshape(-1, 4) + 1
mesh = meshio.Mesh(points, [("tetra", cells_xdmf)], cell_data={"dominio": [domain_id.astype(np.int32)]})
meshio.write(xdmf_path, mesh)
print(f"✅ Guardado XDMF: {xdmf_path}")

gmsh.finalize()

# ---------------------------------
# Estadísticas de la malla
# ---------------------------------
print("\n" + "="*60)
print("ESTADÍSTICAS DE LA MALLA REFINADA")
print("="*60)
print(f"Número de nodos: {len(points):,}")
print(f"Número de tetraedros: {len(tet_tags):,}")
print(f"\nDistribución por material:")
print(f"  SOIL_1: {np.sum(domain_id == 1):,} elementos")
print(f"  SOIL_2: {np.sum(domain_id == 2):,} elementos")
print(f"  SOIL_3: {np.sum(domain_id == 3):,} elementos")
print(f"  FOOTING: {np.sum(domain_id == 4):,} elementos")

# Análisis de calidad de elementos
elem_volumes = []
for i in range(0, len(connectivity), 4):
    nodes = points[connectivity[i:i+4]]
    # Calcular volumen del tetraedro
    v1 = nodes[1] - nodes[0]
    v2 = nodes[2] - nodes[0]
    v3 = nodes[3] - nodes[0]
    vol = abs(np.dot(v1, np.cross(v2, v3))) / 6.0
    elem_volumes.append(vol)

elem_volumes = np.array(elem_volumes)
print(f"\nCalidad de elementos:")
print(f"  Volumen mínimo: {elem_volumes.min():.6f} m³")
print(f"  Volumen máximo: {elem_volumes.max():.6f} m³")
print(f"  Volumen promedio: {elem_volumes.mean():.6f} m³")
print(f"  Ratio max/min: {elem_volumes.max()/elem_volumes.min():.2f}")

print(f"\n📍 Límites de la malla:")
print(f"  X: [{points[:, 0].min():.3f}, {points[:, 0].max():.3f}]")
print(f"  Y: [{points[:, 1].min():.3f}, {points[:, 1].max():.3f}]")
print(f"  Z: [{points[:, 2].min():.3f}, {points[:, 2].max():.3f}]")

print(f"\n✅ Malla tetraédrica refinada generada exitosamente")
print(f"   Tipo: FourNodeTetrahedron (compatible con OpenSees)")
print(f"   Refinamiento: Fino en zapata → Crecimiento geométrico → Grueso en fronteras")
print(f"\n📊 Para visualizar en ParaView:")
print(f"   paraview {vtu_path}")
print("="*60)
