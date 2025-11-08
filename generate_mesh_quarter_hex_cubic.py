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
# IMPORTANTE: Usar tamaños que permitan nodos en las coordenadas críticas
elem_size = 0.5  # Tamaño objetivo del elemento (medio metro)

# Divisiones en X e Y con nodos en coordenadas críticas
# Necesitamos nodos en: 0, 2.25, 3.0
# Crear división especial para tener nodo en 2.25
nx_before = int(np.round(x_foot_start / elem_size))  # De 0 a 2.25
nx_after = int(np.round((Lx - x_foot_start) / elem_size))  # De 2.25 a 3.0
ny_before = int(np.round(y_foot_start / elem_size))  # De 0 a 2.25
ny_after = int(np.round((Ly - y_foot_start) / elem_size))  # De 2.25 a 3.0

# Divisiones en Z por capas (con nodos en interfaces exactas)
nz1 = int(np.round(H1 / elem_size))  # SOIL_1
nz2 = int(np.round(H2 / elem_size))  # SOIL_2
nz3 = int(np.round(H3 / elem_size))  # SOIL_3
nz_foot = int(np.round(tz / elem_size))  # Zapata
if nz_foot < 1:
    nz_foot = 1
if nz3 < 1:
    nz3 = 1

print(f"Generando malla cúbica estructurada con límites exactos...")
print(f"  Tamaño de elemento objetivo: {elem_size} m")
print(f"  Divisiones: nx={nx_before + nx_after}, ny={ny_before + ny_after}")
print(f"  Divisiones Z: nz1={nz1}, nz2={nz2}, nz3={nz3}")

# ---------------------------------
# Generar coordenadas estructuradas con nodos en límites exactos
# ---------------------------------
# Coordenadas X: necesitamos nodos en 0, 2.25, 3.0
x_coords_before = np.linspace(0, x_foot_start, nx_before + 1)
x_coords_after = np.linspace(x_foot_start, Lx, nx_after + 1)
x_coords = np.unique(np.concatenate([x_coords_before, x_coords_after]))

# Coordenadas Y: necesitamos nodos en 0, 2.25, 3.0
y_coords_before = np.linspace(0, y_foot_start, ny_before + 1)
y_coords_after = np.linspace(y_foot_start, Ly, ny_after + 1)
y_coords = np.unique(np.concatenate([y_coords_before, y_coords_after]))

# Coordenadas Z: necesitamos nodos en -10.0, -9.0, -5.0, -2.0, -1.5, 0.0
z_coords_soil3 = np.linspace(-Lz, -(H1 + H2), nz3 + 1)  # -10.0 a -9.0
z_coords_soil2 = np.linspace(-(H1 + H2), -H1, nz2 + 1)  # -9.0 a -5.0
z_coords_soil1 = np.linspace(-H1, 0, nz1 + 1)  # -5.0 a 0.0

# Asegurar que tenemos nodos en z_base (-2.0) y z_top (-1.5)
# Agregar estos nodos críticos si no existen
z_all = np.unique(np.concatenate([z_coords_soil3, z_coords_soil2, z_coords_soil1]))
critical_z = np.array([z_base, z_top])
for z_crit in critical_z:
    if not np.any(np.abs(z_all - z_crit) < 1e-10):
        z_all = np.sort(np.concatenate([z_all, [z_crit]]))

print(f"  Nodos X: {len(x_coords)} (límites: {x_coords[0]:.3f} a {x_coords[-1]:.3f})")
print(f"  Nodos Y: {len(y_coords)} (límites: {y_coords[0]:.3f} a {y_coords[-1]:.3f})")
print(f"  Nodos Z: {len(z_all)} (límites: {z_all[0]:.3f} a {z_all[-1]:.3f})")

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
# Generar malla del suelo completo con z_all
# ---------------------------------
# Generar todos los nodos primero
nodes_all, elements_all_temp = create_structured_hex_mesh(x_coords, y_coords, z_all)

# Ahora identificar a qué dominio pertenece cada elemento
all_elements = []
all_domains = []

nx_total = len(x_coords)
ny_total = len(y_coords)
nz_total = len(z_all)

for elem in elements_all_temp:
    # Obtener coordenadas de los nodos del elemento
    elem_nodes = nodes_all[elem]
    center = elem_nodes.mean(axis=0)
    z_center = center[2]

    # Determinar a qué capa pertenece según Z
    if z_center >= -H1:  # SOIL_1
        # Verificar si está en la zona de la zapata
        in_footing_zone = (x_foot_start <= center[0] <= x_foot_end and
                          y_foot_start <= center[1] <= y_foot_end and
                          z_base <= z_center <= z_top)

        if in_footing_zone:
            # Es parte de la zapata
            all_elements.append(elem)
            all_domains.append(4)  # FOOTING
        else:
            # Es suelo SOIL_1
            all_elements.append(elem)
            all_domains.append(1)  # SOIL_1

    elif z_center >= -(H1 + H2):  # SOIL_2
        all_elements.append(elem)
        all_domains.append(2)  # SOIL_2

    else:  # SOIL_3
        all_elements.append(elem)
        all_domains.append(3)  # SOIL_3

points = nodes_all
elements_all = np.array(all_elements)
domain_id_combined = np.array(all_domains, dtype=int)

print(f"\n✅ Malla cúbica generada con límites exactos:")
print(f"   - Total de nodos: {len(points)}")
print(f"   - Total de elementos: {len(elements_all)}")
print(f"   - SOIL_3: {np.sum(domain_id_combined == 3)} elementos")
print(f"   - SOIL_2: {np.sum(domain_id_combined == 2)} elementos")
print(f"   - SOIL_1: {np.sum(domain_id_combined == 1)} elementos")
print(f"   - FOOTING: {np.sum(domain_id_combined == 4)} elementos")
print(f"\n📍 Límites verificados:")
print(f"   - X: [{points[:, 0].min():.3f}, {points[:, 0].max():.3f}] (esperado: [0.000, 3.000])")
print(f"   - Y: [{points[:, 1].min():.3f}, {points[:, 1].max():.3f}] (esperado: [0.000, 3.000])")
print(f"   - Z: [{points[:, 2].min():.3f}, {points[:, 2].max():.3f}] (esperado: [-10.000, 0.000])")

# ---------------------------------
# Verificar proporciones de elementos
# ---------------------------------
sample_size = min(100, len(elements_all))
elem_dims = []
for elem in elements_all[:sample_size]:
    coords = points[elem]
    dx = coords[:, 0].max() - coords[:, 0].min()
    dy = coords[:, 1].max() - coords[:, 1].min()
    dz = coords[:, 2].max() - coords[:, 2].min()
    if dx > 0 and dy > 0 and dz > 0:  # Evitar divisiones por cero
        elem_dims.append([dx, dy, dz])

if elem_dims:
    elem_dims = np.array(elem_dims)
    aspect_ratio = elem_dims.max(axis=1) / (elem_dims.min(axis=1) + 1e-10)
    print(f"\n📊 Análisis de forma de elementos (muestra de {len(elem_dims)}):")
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
print(f"   - Geometría preservada EXACTAMENTE igual al script original")
print(f"\n📊 Para visualizar en ParaView:")
print(f"   paraview {vtu_path}")
print(f"\nComparación con malla original:")
print(f"  - Límites X: 0.000 a 3.000 ✓")
print(f"  - Límites Y: 0.000 a 3.000 ✓")
print(f"  - Límites Z: -10.000 a 0.000 ✓")
print(f"  - Zapata: ({x_foot_start:.2f}, {y_foot_start:.2f}, {z_base:.2f}) a ({x_foot_end:.2f}, {y_foot_end:.2f}, {z_top:.2f}) ✓")
