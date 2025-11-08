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

# Coordenadas de la zapata en 1/4 del dominio
x_foot_start = x0 / 2
x_foot_end = x_foot_start + B / 4
y_foot_start = y0 / 2
y_foot_end = y_foot_start + B / 4

# ---------------------------------
# Parámetros de discretización para malla cúbica
# ---------------------------------
# Usar un tamaño de elemento objetivo
elem_size = 0.5  # Tamaño objetivo del elemento (medio metro)

# Calcular número de divisiones para mantener elementos cúbicos
nx = int(np.round(Lx / elem_size))
ny = int(np.round(Ly / elem_size))

# Para Z, dividir por capas manteniendo elementos cúbicos
nz1 = int(np.round(H1 / elem_size))  # SOIL_1
nz2 = int(np.round(H2 / elem_size))  # SOIL_2
nz3 = int(np.round(H3 / elem_size))  # SOIL_3

# Divisiones en la zapata (mantener cúbicos)
nz_foot = int(np.round(tz / elem_size))
if nz_foot < 1:
    nz_foot = 1

print(f"Generando malla cúbica estructurada...")
print(f"  Tamaño de elemento objetivo: {elem_size} m")
print(f"  Divisiones: nx={nx}, ny={ny}, nz1={nz1}, nz2={nz2}, nz3={nz3}")

# ---------------------------------
# Generar coordenadas estructuradas
# ---------------------------------
x_coords = np.linspace(0, Lx, nx + 1)
y_coords = np.linspace(0, Ly, ny + 1)

# Coordenadas Z por capas
z_coords_soil3 = np.linspace(-Lz, -(H1 + H2), nz3 + 1)
z_coords_soil2 = np.linspace(-(H1 + H2), -H1, nz2 + 1)
z_coords_soil1 = np.linspace(-H1, 0, nz1 + 1)

# ---------------------------------
# Función para crear hexaedros estructurados
# ---------------------------------
def create_structured_hex_mesh(x_coords, y_coords, z_coords):
    """Crea nodos y elementos hexaédricos estructurados"""
    nodes = []
    nx_local = len(x_coords)
    ny_local = len(y_coords)
    nz_local = len(z_coords)

    # Crear nodos (k=z, j=y, i=x)
    for k in range(nz_local):
        for j in range(ny_local):
            for i in range(nx_local):
                nodes.append([x_coords[i], y_coords[j], z_coords[k]])

    nodes = np.array(nodes)

    # Crear elementos hexaédricos (8 nodos por elemento)
    elements = []
    for k in range(nz_local - 1):
        for j in range(ny_local - 1):
            for i in range(nx_local - 1):
                # Índices de los 8 nodos del hexaedro
                # Capa inferior (z=k)
                n0 = k * ny_local * nx_local + j * nx_local + i
                n1 = n0 + 1
                n2 = n0 + nx_local + 1
                n3 = n0 + nx_local
                # Capa superior (z=k+1)
                n4 = n0 + ny_local * nx_local
                n5 = n4 + 1
                n6 = n4 + nx_local + 1
                n7 = n4 + nx_local

                elements.append([n0, n1, n2, n3, n4, n5, n6, n7])

    return nodes, np.array(elements)

# ---------------------------------
# Generar malla del suelo completo
# ---------------------------------
all_nodes = []
all_elements = []
all_domains = []
node_offset = 0

# SOIL_3 (capa inferior)
nodes_s3, elements_s3 = create_structured_hex_mesh(x_coords, y_coords, z_coords_soil3)
all_nodes.append(nodes_s3)
all_elements.append(elements_s3)
all_domains.append(np.full(len(elements_s3), 3, dtype=int))  # Dominio 3
node_offset += len(nodes_s3)

# SOIL_2 (capa media)
nodes_s2, elements_s2 = create_structured_hex_mesh(x_coords, y_coords, z_coords_soil2)
# Compartir nodos en la interfaz
nodes_s2_unique = nodes_s2[nx * ny:]  # Omitir primera capa (compartida con SOIL_3)
all_nodes.append(nodes_s2_unique)
elements_s2_adjusted = elements_s2.copy()
# Ajustar índices para compartir nodos
for i in range(len(elements_s2)):
    for j in range(8):
        if elements_s2[i, j] < nx * ny:
            # Nodo en la interfaz, apuntar a SOIL_3
            elements_s2_adjusted[i, j] = node_offset - nx * ny + elements_s2[i, j]
        else:
            # Nodo propio de SOIL_2
            elements_s2_adjusted[i, j] = node_offset + elements_s2[i, j] - nx * ny

all_elements.append(elements_s2_adjusted)
all_domains.append(np.full(len(elements_s2), 2, dtype=int))  # Dominio 2
node_offset += len(nodes_s2_unique)

# SOIL_1 (capa superior) - aquí tenemos que excluir la zona de la zapata
nodes_s1, elements_s1 = create_structured_hex_mesh(x_coords, y_coords, z_coords_soil1)
nodes_s1_unique = nodes_s1[nx * ny:]  # Omitir primera capa (compartida con SOIL_2)
all_nodes.append(nodes_s1_unique)

# Filtrar elementos que NO están en la zona de la zapata
elements_s1_filtered = []
domains_s1_filtered = []

for elem_idx, elem in enumerate(elements_s1):
    # Obtener coordenadas del centro del elemento
    elem_nodes_coords = nodes_s1[elem]
    center = elem_nodes_coords.mean(axis=0)

    # Verificar si está en la zona de la zapata
    in_footing_zone = (x_foot_start <= center[0] <= x_foot_end and
                      y_foot_start <= center[1] <= y_foot_end and
                      z_base <= center[2] <= z_top)

    if not in_footing_zone:
        # Ajustar índices para compartir nodos
        elem_adjusted = elem.copy()
        for j in range(8):
            if elem[j] < nx * ny:
                # Nodo en la interfaz con SOIL_2
                elem_adjusted[j] = node_offset - nx * ny + elem[j]
            else:
                # Nodo propio de SOIL_1
                elem_adjusted[j] = node_offset + elem[j] - nx * ny

        elements_s1_filtered.append(elem_adjusted)
        domains_s1_filtered.append(1)  # Dominio 1

if elements_s1_filtered:
    all_elements.append(np.array(elements_s1_filtered))
    all_domains.append(np.array(domains_s1_filtered, dtype=int))
node_offset += len(nodes_s1_unique)

# ---------------------------------
# Generar malla de la zapata
# ---------------------------------
# Encontrar índices de x, y que corresponden a la zapata
x_indices = np.where((x_coords >= x_foot_start - elem_size/2) &
                     (x_coords <= x_foot_end + elem_size/2))[0]
y_indices = np.where((y_coords >= y_foot_start - elem_size/2) &
                     (y_coords <= y_foot_end + elem_size/2))[0]

x_foot_coords = x_coords[x_indices]
y_foot_coords = y_coords[y_indices]
z_foot_coords = np.linspace(z_base, z_top, nz_foot + 1)

nodes_foot, elements_foot = create_structured_hex_mesh(x_foot_coords, y_foot_coords, z_foot_coords)
all_nodes.append(nodes_foot)

# Ajustar índices de elementos de zapata
elements_foot_adjusted = elements_foot + node_offset
all_elements.append(elements_foot_adjusted)
all_domains.append(np.full(len(elements_foot), 4, dtype=int))  # Dominio 4 (FOOTING)

# ---------------------------------
# Combinar todo
# ---------------------------------
points = np.vstack(all_nodes)
elements_all = np.vstack(all_elements)
domain_id_combined = np.concatenate(all_domains)

print(f"\n✅ Malla cúbica generada:")
print(f"   - Total de nodos: {len(points)}")
print(f"   - Total de elementos: {len(elements_all)}")
print(f"   - SOIL_3: {np.sum(domain_id_combined == 3)} elementos")
print(f"   - SOIL_2: {np.sum(domain_id_combined == 2)} elementos")
print(f"   - SOIL_1: {np.sum(domain_id_combined == 1)} elementos")
print(f"   - FOOTING: {np.sum(domain_id_combined == 4)} elementos")

# ---------------------------------
# Verificar proporciones de elementos
# ---------------------------------
elem_dims = []
for elem in elements_all[:100]:  # Verificar primeros 100 elementos
    coords = points[elem]
    dx = coords[:, 0].max() - coords[:, 0].min()
    dy = coords[:, 1].max() - coords[:, 1].min()
    dz = coords[:, 2].max() - coords[:, 2].min()
    elem_dims.append([dx, dy, dz])

elem_dims = np.array(elem_dims)
aspect_ratio = elem_dims.max(axis=1) / elem_dims.min(axis=1)
print(f"\n📊 Análisis de forma de elementos (muestra de 100):")
print(f"   - Aspect ratio promedio: {aspect_ratio.mean():.2f}")
print(f"   - Aspect ratio máximo: {aspect_ratio.max():.2f}")
print(f"   - Aspect ratio mínimo: {aspect_ratio.min():.2f}")

# ---------------------------------
# Exportar a PyVista y archivos
# ---------------------------------
cells_list = []
for elem in elements_all:
    cells_list.append(8)  # 8 nodos por hexaedro
    cells_list.extend(elem)

cells = np.array(cells_list)
celltypes = np.full(len(elements_all), pv.CellType.HEXAHEDRON, dtype=np.uint8)

grid = pv.UnstructuredGrid(cells, celltypes, points)
grid.cell_data["dominio"] = domain_id_combined

# Guardar VTU para ParaView
vtu_path = "mallas/zapata_3D_cuarto_hex_cubic.vtu"
grid.save(vtu_path)
print(f"\n✅ Guardado VTK: {vtu_path}")

# Guardar XDMF con meshio
xdmf_path = "mallas/zapata_3D_cuarto_hex_cubic.xdmf"
meshio_cells = [("hexahedron", elements_all + 1)]  # meshio usa índices basados en 1
mesh = meshio.Mesh(points, meshio_cells, cell_data={"dominio": [domain_id_combined.astype(np.int32)]})
meshio.write(xdmf_path, mesh)
print(f"✅ Guardado XDMF: {xdmf_path}")

print("\n✅ Malla cúbica estructurada generada exitosamente")
print(f"   - Dominios: SOIL_1, SOIL_2, SOIL_3, FOOTING")
print(f"\n📊 Para visualizar en ParaView:")
print(f"   paraview {vtu_path}")
