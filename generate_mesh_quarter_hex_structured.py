"""
Generador de malla hexaédrica estructurada para modelo de zapata en OpenSees
100% elementos hexaédricos (8 nodos) - Compatible con ParaView
"""
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
# Región de la zapata
nx_foot = 4      # divisiones en X para zapata
ny_foot = 4      # divisiones en Y para zapata
nz_foot = 2      # divisiones en Z para zapata

# Región del suelo alrededor de la zapata
nx_soil_side = 8   # divisiones en X para suelo lateral
ny_soil_side = 8   # divisiones en Y para suelo lateral

# Capas de suelo verticales
nz_excav = 6    # divisiones en Z para excavación
nz1 = 10        # divisiones en Z para capa 1 de suelo
nz2 = 8         # divisiones en Z para capa 2 de suelo
nz3 = 4         # divisiones en Z para capa 3 de suelo

# ---------------------------------
# Funciones auxiliares
# ---------------------------------
def create_structured_hexmesh(x_coords, y_coords, z_coords):
    """
    Crea una malla estructurada de hexaedros
    Retorna: nodos (array Nx3), conectividad (array Mx8), dominio_id
    """
    nx, ny, nz = len(x_coords), len(y_coords), len(z_coords)

    # Crear grid de nodos
    X, Y, Z = np.meshgrid(x_coords, y_coords, z_coords, indexing='ij')
    nodes = np.column_stack([X.ravel(), Y.ravel(), Z.ravel()])

    # Función para convertir índices (i,j,k) a índice lineal
    def idx(i, j, k):
        return i * ny * nz + j * nz + k

    # Crear elementos hexaédricos
    elements = []
    for i in range(nx - 1):
        for j in range(ny - 1):
            for k in range(nz - 1):
                # Nodos del hexaedro (orden estándar VTK/OpenSees)
                n0 = idx(i, j, k)
                n1 = idx(i+1, j, k)
                n2 = idx(i+1, j+1, k)
                n3 = idx(i, j+1, k)
                n4 = idx(i, j, k+1)
                n5 = idx(i+1, j, k+1)
                n6 = idx(i+1, j+1, k+1)
                n7 = idx(i, j+1, k+1)

                elements.append([n0, n1, n2, n3, n4, n5, n6, n7])

    return nodes, np.array(elements)

def merge_meshes(mesh_list):
    """
    Fusiona múltiples mallas en una sola
    mesh_list: lista de tuplas (nodes, elements, domain_id)
    Retorna: nodes_combined, elements_combined, domain_ids_combined
    """
    all_nodes = []
    all_elements = []
    all_domains = []

    node_offset = 0

    for nodes, elements, domain_id in mesh_list:
        all_nodes.append(nodes)
        all_elements.append(elements + node_offset)
        all_domains.extend([domain_id] * len(elements))
        node_offset += len(nodes)

    nodes_combined = np.vstack(all_nodes)
    elements_combined = np.vstack(all_elements)
    domain_ids_combined = np.array(all_domains)

    return nodes_combined, elements_combined, domain_ids_combined

# ---------------------------------
# REGIÓN 1: Zapata (FOOTING)
# ---------------------------------
x_foot = np.linspace(x0/2, x0/2 + B/4, nx_foot + 1)
y_foot = np.linspace(y0/2, y0/2 + B/4, ny_foot + 1)
z_foot = np.linspace(z_base, z_top, nz_foot + 1)

nodes_foot, elems_foot = create_structured_hexmesh(x_foot, y_foot, z_foot)
mesh_foot = (nodes_foot, elems_foot, 4)  # domain_id = 4 para FOOTING

print(f"✅ Zapata: {len(nodes_foot)} nodos, {len(elems_foot)} hexaedros")

# ---------------------------------
# REGIÓN 2: Excavación alrededor de zapata (SOIL_1)
# ---------------------------------
# Zona izquierda de excavación
x_excav_left = np.linspace(0, x0/2, nx_soil_side + 1)
y_excav_left = np.linspace(0, Ly, 2*ny_soil_side + 1)
z_excav_left = np.linspace(z_base, 0, nz_excav + 1)

nodes_excav_left, elems_excav_left = create_structured_hexmesh(x_excav_left, y_excav_left, z_excav_left)

# Zona derecha de excavación (al lado de la zapata en X)
x_excav_right = np.linspace(x0/2 + B/4, Lx, nx_soil_side + 1)
y_excav_right = np.linspace(0, Ly, 2*ny_soil_side + 1)
z_excav_right = np.linspace(z_base, 0, nz_excav + 1)

nodes_excav_right, elems_excav_right = create_structured_hexmesh(x_excav_right, y_excav_right, z_excav_right)

# NO se crean zonas frontal ni trasera para dejar el hueco puro arriba de la zapata
# (sin superficies verticales en los planos de simetría)

mesh_excav_left = (nodes_excav_left, elems_excav_left, 1)  # SOIL_1
mesh_excav_right = (nodes_excav_right, elems_excav_right, 1)

print(f"✅ Excavación: {len(elems_excav_left) + len(elems_excav_right)} hexaedros")

# ---------------------------------
# REGIÓN 3: Suelo Capa 1 (SOIL_1) - debajo de excavación
# ---------------------------------
x_soil1 = np.linspace(0, Lx, 2*nx_soil_side + 1)
y_soil1 = np.linspace(0, Ly, 2*ny_soil_side + 1)
z_soil1 = np.linspace(-H1, z_base, nz1 + 1)

nodes_soil1, elems_soil1 = create_structured_hexmesh(x_soil1, y_soil1, z_soil1)
mesh_soil1 = (nodes_soil1, elems_soil1, 1)  # domain_id = 1 para SOIL_1

print(f"✅ Suelo Capa 1: {len(nodes_soil1)} nodos, {len(elems_soil1)} hexaedros")

# ---------------------------------
# REGIÓN 4: Suelo Capa 2 (SOIL_2)
# ---------------------------------
x_soil2 = np.linspace(0, Lx, 2*nx_soil_side + 1)
y_soil2 = np.linspace(0, Ly, 2*ny_soil_side + 1)
z_soil2 = np.linspace(-(H1 + H2), -H1, nz2 + 1)

nodes_soil2, elems_soil2 = create_structured_hexmesh(x_soil2, y_soil2, z_soil2)
mesh_soil2 = (nodes_soil2, elems_soil2, 2)  # domain_id = 2 para SOIL_2

print(f"✅ Suelo Capa 2: {len(nodes_soil2)} nodos, {len(elems_soil2)} hexaedros")

# ---------------------------------
# REGIÓN 5: Suelo Capa 3 (SOIL_3)
# ---------------------------------
x_soil3 = np.linspace(0, Lx, 2*nx_soil_side + 1)
y_soil3 = np.linspace(0, Ly, 2*ny_soil_side + 1)
z_soil3 = np.linspace(-Lz, -(H1 + H2), nz3 + 1)

nodes_soil3, elems_soil3 = create_structured_hexmesh(x_soil3, y_soil3, z_soil3)
mesh_soil3 = (nodes_soil3, elems_soil3, 3)  # domain_id = 3 para SOIL_3

print(f"✅ Suelo Capa 3: {len(nodes_soil3)} nodos, {len(elems_soil3)} hexaedros")

# ---------------------------------
# Fusionar todas las mallas
# ---------------------------------
print("\n🔄 Fusionando mallas...")
all_meshes = [
    mesh_soil3,
    mesh_soil2,
    mesh_soil1,
    mesh_excav_left,
    mesh_excav_right,
    mesh_foot
]

nodes_all, elems_all, domain_ids = merge_meshes(all_meshes)

print(f"✅ Malla total: {len(nodes_all)} nodos, {len(elems_all)} hexaedros")

# ---------------------------------
# Exportar a PyVista (VTU para ParaView)
# ---------------------------------
print("\n📦 Exportando malla...")

# Crear celdas para PyVista (agregar contador de nodos al inicio de cada elemento)
cells = np.insert(elems_all, 0, 8, axis=1).ravel()
celltypes = np.full(len(elems_all), pv.CellType.HEXAHEDRON, dtype=np.uint8)

# Crear grid
grid = pv.UnstructuredGrid(cells, celltypes, nodes_all)
grid.cell_data["dominio"] = domain_ids

# Guardar VTU
vtu_path = "mallas/zapata_3D_cuarto_hex_structured.vtu"
grid.save(vtu_path)
print(f"✅ Guardado VTK: {vtu_path}")

# ---------------------------------
# Exportar a XDMF (para OpenSees y otros simuladores)
# ---------------------------------
# meshio usa índices basados en 1 para algunos formatos
cells_meshio = [("hexahedron", elems_all + 1)]  # +1 para indexación basada en 1
cell_data = {"dominio": [domain_ids.astype(np.int32)]}

mesh = meshio.Mesh(nodes_all, cells_meshio, cell_data=cell_data)

xdmf_path = "mallas/zapata_3D_cuarto_hex_structured.xdmf"
meshio.write(xdmf_path, mesh)
print(f"✅ Guardado XDMF: {xdmf_path}")

# ---------------------------------
# Exportar también a formato Gmsh para compatibilidad
# ---------------------------------
msh_path = "mallas/zapata_3D_cuarto_hex_structured.msh"
meshio.write(msh_path, mesh)
print(f"✅ Guardado MSH: {msh_path}")

# ---------------------------------
# Estadísticas finales
# ---------------------------------
print("\n" + "="*60)
print("✅ MALLA HEXAÉDRICA ESTRUCTURADA GENERADA EXITOSAMENTE")
print("="*60)
print(f"   - Número de nodos:     {len(nodes_all):,}")
print(f"   - Número de hexaedros: {len(elems_all):,}")
print(f"   - Tipo de elementos:   100% HEXAEDROS (8 nodos)")
print(f"\n📊 Distribución por dominio:")
print(f"   - SOIL_1 (Capa 1):  {np.sum(domain_ids == 1):,} elementos")
print(f"   - SOIL_2 (Capa 2):  {np.sum(domain_ids == 2):,} elementos")
print(f"   - SOIL_3 (Capa 3):  {np.sum(domain_ids == 3):,} elementos")
print(f"   - FOOTING (Zapata): {np.sum(domain_ids == 4):,} elementos")
print(f"\n🎯 Archivos generados:")
print(f"   1. {vtu_path} (ParaView)")
print(f"   2. {xdmf_path} (OpenSees/FEniCS)")
print(f"   3. {msh_path} (Gmsh)")
print(f"\n📊 Para visualizar en ParaView:")
print(f"   paraview {vtu_path}")
print("="*60)

# Opcional: Visualización interactiva con PyVista
# Descomenta las siguientes líneas para ver la malla en 3D
"""
plotter = pv.Plotter()
plotter.add_mesh(grid, scalars="dominio", show_edges=True, opacity=0.85,
                 cmap='viridis', scalar_bar_args={'title': 'Dominio'})
plotter.add_text("Malla Hexaédrica Estructurada - 1/4 Zapata", font_size=12)
plotter.show_axes()
plotter.show_grid()
plotter.show()
"""
