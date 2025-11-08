import gmsh
import numpy as np
import pyvista as pv
import meshio

# ---------------------------------
# Parámetros geométricos
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
# Inicializar Gmsh
# ---------------------------------
gmsh.initialize()
gmsh.model.add("zapata_3D_cuarto")

# Crear sólidos
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
# Tamaño de malla
# ---------------------------------
def size_callback(dim, tag, x, y, z, lc):
    if (x0 - 0.3) <= x <= (x0 + B / 2 + 0.3) and (y0 - 0.3) <= y <= (y0 + B / 2 + 0.3) and (z_base - 1.0) <= z <= (z_top + 1.0):
        return 0.25
    return 1.0

gmsh.model.mesh.setSizeCallback(size_callback)
gmsh.model.mesh.generate(3)
gmsh.write("mallas/zapata_3D_cuarto.msh")

# ---------------------------------
# Conversión a PyVista y exportes
# ---------------------------------
node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
points = node_coords.reshape(-1, 3)

etags, ntags = gmsh.model.mesh.getElementsByType(4)
connectivity = ntags - 1
tet_tags = etags

domain_id = np.zeros(len(tet_tags), dtype=int)
color_map = {phys_s1: 1, phys_s2: 2, phys_s3: 3, phys_foot: 4}

for pg, color in color_map.items():
    ents = gmsh.model.getEntitiesForPhysicalGroup(3, pg)
    for ent in ents:
        etags_local, _ = gmsh.model.mesh.getElementsByType(4, ent)
        for eid in etags_local:
            idx = np.where(tet_tags == eid)[0]
            domain_id[idx] = color

cells = np.insert(connectivity.reshape(-1, 4), 0, 4, axis=1).ravel()
celltypes = np.full(len(connectivity) // 4, pv.CellType.TETRA, dtype=np.uint8)
grid = pv.UnstructuredGrid(cells, celltypes, points)
grid.cell_data["dominio"] = domain_id

vtu_path = "mallas/zapata_3D_cuarto.vtu"
grid.save(vtu_path)
print(f"✅ Guardado VTK: {vtu_path}")

xdmf_path = "mallas/zapata_3D_cuarto.xdmf"
cells_xdmf = connectivity.reshape(-1, 4) + 1
mesh = meshio.Mesh(points, [("tetra", cells_xdmf)], cell_data={"dominio": [domain_id.astype(np.int32)]})
meshio.write(xdmf_path, mesh)
print(f"✅ Guardado XDMF: {xdmf_path}")

gmsh.finalize()

# ---------------------------------
# Visualización rápida
# ---------------------------------
print("✅ Malla generada exitosamente")
print(f"   - Número de puntos: {len(points)}")
print(f"   - Número de elementos: {len(tet_tags)}")
print(f"   - Dominios: SOIL_1, SOIL_2, SOIL_3, FOOTING")

# Descomenta las siguientes líneas si quieres ver la visualización interactiva:
# plotter = pv.Plotter()
# plotter.add_mesh(grid, scalars="dominio", show_edges=True, opacity=0.85)
# plotter.add_text("Malla 3D - 1/4 de zapata empotrada", font_size=12)
# plotter.show_axes()
# plotter.show()
