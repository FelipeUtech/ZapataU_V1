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
# Parámetros de discretización
# ---------------------------------
nx, ny = 12, 12  # Divisiones en X e Y
nz1, nz2, nz3 = 10, 8, 2  # Divisiones en cada capa de suelo
nz_foot = 2  # Divisiones en zapata

# Coordenadas del área de la zapata (1/4)
x_foot_start = x0 / 2
x_foot_end = x_foot_start + B / 4
y_foot_start = y0 / 2
y_foot_end = y_foot_start + B / 4

# ---------------------------------
# Generar malla estructurada hexagonal
# ---------------------------------
print("Generando malla hexagonal estructurada...")

def create_structured_hex_mesh(x_coords, y_coords, z_coords):
    """Crea nodos y elementos hexaédricos estructurados"""
    nodes = []
    nx_local = len(x_coords) - 1
    ny_local = len(y_coords) - 1
    nz_local = len(z_coords) - 1

    # Crear nodos
    for k in range(len(z_coords)):
        for j in range(len(y_coords)):
            for i in range(len(x_coords)):
                nodes.append([x_coords[i], y_coords[j], z_coords[k]])

    nodes = np.array(nodes)

    # Crear elementos hexaédricos (8 nodos por elemento)
    elements = []
    for k in range(nz_local):
        for j in range(ny_local):
            for i in range(nx_local):
                # Índices de los 8 nodos del hexaedro
                n0 = k * len(y_coords) * len(x_coords) + j * len(x_coords) + i
                n1 = n0 + 1
                n2 = n0 + len(x_coords) + 1
                n3 = n0 + len(x_coords)
                n4 = n0 + len(y_coords) * len(x_coords)
                n5 = n4 + 1
                n6 = n4 + len(x_coords) + 1
                n7 = n4 + len(x_coords)

                elements.append([n0, n1, n2, n3, n4, n5, n6, n7])

    return nodes, np.array(elements)

# Generar coordenadas
x_coords = np.linspace(0, Lx, nx + 1)
y_coords = np.linspace(0, Ly, ny + 1)

# Coordenadas Z por capas
z_coords_soil1 = np.linspace(-H1, 0, nz1 + 1)
z_coords_soil2 = np.linspace(-(H1 + H2), -H1, nz2 + 1)[:-1]  # Excluir el último nodo (compartido)
z_coords_soil3 = np.linspace(-Lz, -(H1 + H2), nz3 + 1)[:-1]  # Excluir el último nodo

# Combinar coordenadas Z
z_coords = np.concatenate([z_coords_soil3, z_coords_soil2, z_coords_soil1])

# Crear malla del suelo
nodes_soil, elements_soil = create_structured_hex_mesh(x_coords, y_coords, z_coords)

# Identificar elementos por capa
num_elem_per_layer = nx * ny
total_layers = nz1 + nz2 + nz3

domain_id_soil = np.zeros(len(elements_soil), dtype=int)
elem_idx = 0

# SOIL_3 (capa inferior)
for k in range(nz3):
    for _ in range(num_elem_per_layer):
        domain_id_soil[elem_idx] = 3  # SOIL_3
        elem_idx += 1

# SOIL_2 (capa media)
for k in range(nz2):
    for _ in range(num_elem_per_layer):
        domain_id_soil[elem_idx] = 2  # SOIL_2
        elem_idx += 1

# SOIL_1 (capa superior) - aquí necesitamos excluir la zona de la zapata
for k in range(nz1):
    layer_z = z_coords_soil1[k]
    for j in range(ny):
        y_elem = (y_coords[j] + y_coords[j + 1]) / 2
        for i in range(nx):
            x_elem = (x_coords[i] + x_coords[i + 1]) / 2

            # Verificar si está en la zona de la zapata
            in_footing_zone = (x_foot_start <= x_elem <= x_foot_end and
                              y_foot_start <= y_elem <= y_foot_end and
                              z_base <= layer_z <= z_top)

            if not in_footing_zone:
                domain_id_soil[elem_idx] = 1  # SOIL_1
            else:
                domain_id_soil[elem_idx] = 1  # Por ahora, luego lo quitamos

            elem_idx += 1

# Crear malla de la zapata
x_coords_foot = np.linspace(x_foot_start, x_foot_end, 6)
y_coords_foot = np.linspace(y_foot_start, y_foot_end, 6)
z_coords_foot = np.linspace(z_base, z_top, nz_foot + 1)

nodes_foot, elements_foot = create_structured_hex_mesh(x_coords_foot, y_coords_foot, z_coords_foot)
domain_id_foot = np.full(len(elements_foot), 4, dtype=int)  # FOOTING

# Combinar nodos y elementos
offset = len(nodes_soil)
elements_foot_offset = elements_foot + offset
points = np.vstack([nodes_soil, nodes_foot])
elements_all = np.vstack([elements_soil, elements_foot_offset])
domain_id_combined = np.concatenate([domain_id_soil, domain_id_foot])

print(f"   - Total de nodos: {len(points)}")
print(f"   - Elementos SOIL: {len(elements_soil)}")
print(f"   - Elementos FOOTING: {len(elements_foot)}")
print(f"   - Total hexahedros: {len(elements_all)}")

# ---------------------------------
# Conversión a PyVista y exportes
# ---------------------------------
cells_list = []
celltypes_list = []

# Agregar todos los elementos hexaédricos
for elem in elements_all:
    cells_list.append(8)  # 8 nodos por hexaedro
    cells_list.extend(elem)

cells = np.array(cells_list)
celltypes = np.full(len(elements_all), pv.CellType.HEXAHEDRON, dtype=np.uint8)

meshio_cells = [("hexahedron", elements_all + 1)]  # meshio usa índices basados en 1
meshio_cell_data_list = [domain_id_combined.astype(np.int32)]

# Crear grid de PyVista
grid = pv.UnstructuredGrid(cells, celltypes, points)
grid.cell_data["dominio"] = domain_id_combined

# Guardar VTU para ParaView
vtu_path = "mallas/zapata_3D_cuarto_hex.vtu"
grid.save(vtu_path)
print(f"✅ Guardado VTK: {vtu_path}")

# Guardar XDMF con meshio
if meshio_cells:
    xdmf_path = "mallas/zapata_3D_cuarto_hex.xdmf"
    mesh = meshio.Mesh(points, meshio_cells, cell_data={"dominio": meshio_cell_data_list})
    meshio.write(xdmf_path, mesh)
    print(f"✅ Guardado XDMF: {xdmf_path}")

gmsh.finalize()

# ---------------------------------
# Visualización rápida
# ---------------------------------
print("\n✅ Malla generada exitosamente")
print(f"   - Número de puntos: {len(points)}")
print(f"   - Número total de elementos: {len(domain_id_combined)}")
print(f"   - Dominios: SOIL_1, SOIL_2, SOIL_3, FOOTING")
print(f"\n📊 Para visualizar en ParaView:")
print(f"   paraview {vtu_path}")
print(f"\n💡 Nota: Gmsh puede generar mezcla de elementos (hexaedros, tetraedros, prismas)")
print(f"   según la geometría. Para malla 100% hexaédrica se requiere geometría estructurada.")

# Descomenta las siguientes líneas si quieres ver la visualización interactiva:
# plotter = pv.Plotter()
# plotter.add_mesh(grid, scalars="dominio", show_edges=True, opacity=0.85)
# plotter.add_text("Malla 3D con elementos hexaédricos - 1/4 de zapata empotrada", font_size=12)
# plotter.show_axes()
# plotter.show()
