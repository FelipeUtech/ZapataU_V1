import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt

# -------------------------
# INICIALIZACIÓN
# -------------------------
ops.wipe()
ops.model('basic', '-ndm', 3, '-ndf', 3)    # 3D problem, 3 DOF per node

# -------------------------
# PARÁMETROS GEOMÉTRICOS
# -------------------------# Dimensiones del dominio
Lx = 20.0    # Longitud en x (m)
Ly = 20.0    # Longitud en y (m)
Lz = 20.0    # Profundidad en z (m)

# Discretización de la malla
nx = 10      # Número de elementos en x
ny = 10      # Número de elementos en y
nz = 10      # Número de elementos en z

# Calcula espaciamiento
dx = Lx/nx
dy = Ly/ny
dz = Lz/nz

# -------------------------
# CREACIÓN DE NODOS
# -------------------------
print("Generando nodos...")

nodeCounter = 1
nodeCoord = {}

for k in range(nz + 1):    # z direction
    z = -k * dz           
    for j in range(ny + 1):  # y direction
        y = j * dy        
        for i in range(nx + 1):  # x direction
            x = i * dx    
            ops.node(nodeCounter, x, y, z)
            nodeCoord[nodeCounter] = (x, y, z)
            nodeCounter += 1

print(f"Total de nodos creados: {nodeCounter-1}")

# -------------------------
# CONDICIONES DE BORDE
# -------------------------
print("Aplicando condiciones de borde...")

nodesPerLayer = (nx + 1) * (ny + 1)

# Fijar base
baseNodeTags = list(range(nodesPerLayer * nz + 1, nodesPerLayer * (nz + 1) + 1))
for nodeTag in baseNodeTags:
    ops.fix(nodeTag, 1, 1, 1)

# Fijar bordes laterales con rodillos (excluyendo la base que ya está fija)
for k in range(nz):  # Solo hasta nz-1 para no duplicar con la base
    currentLayer = k * nodesPerLayer

    # Borde x = 0
    for j in range(ny + 1):
        nodeTag = currentLayer + j * (nx + 1) + 1
        ops.fix(nodeTag, 1, 0, 0)

    # Borde x = Lx
    for j in range(ny + 1):
        nodeTag = currentLayer + j * (nx + 1) + (nx + 1)
        ops.fix(nodeTag, 1, 0, 0)

    # Borde y = 0
    for i in range(nx + 1):
        nodeTag = currentLayer + i + 1
        ops.fix(nodeTag, 0, 1, 0)

    # Borde y = Ly
    for i in range(nx + 1):
        nodeTag = currentLayer + ny * (nx + 1) + i + 1
        ops.fix(nodeTag, 0, 1, 0)

# -------------------------
# MATERIAL
# -------------------------
print("Definiendo materiales...")

E = 30000.0      # Módulo de Young (kPa)
nu = 0.3         # Coeficiente de Poisson
rho = 1800.0     # Densidad (kg/m³)

ops.nDMaterial('ElasticIsotropic', 1, E, nu, rho)

# -------------------------
# ELEMENTOS
# -------------------------
print("Generando elementos...")
elementCounter = 1

for k in range(nz):
    for j in range(ny):
        for i in range(nx):
            node1 = 1 + i + j*(nx+1) + k*nodesPerLayer
            node2 = node1 + 1
            node3 = node2 + nx + 1
            node4 = node3 - 1
            node5 = node1 + nodesPerLayer
            node6 = node2 + nodesPerLayer
            node7 = node3 + nodesPerLayer
            node8 = node4 + nodesPerLayer
            
            ops.element('stdBrick', elementCounter, node1, node2, node3, node4, 
                       node5, node6, node7, node8, 1)
            elementCounter += 1

print(f"Total de elementos creados: {elementCounter-1}")

# -------------------------
# VISUALIZACIÓN
# -------------------------
try:
    import vfo.vfo as vfo
    
    plt.figure(figsize=(12, 10))
    vfo.plot_model(Model="3D")
    ax = plt.gca(projection='3d')
    ax.view_init(elev=30, azim=45)
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_zlabel('Z (m)')
    plt.title('Malla 3D de Suelo (20m x 20m x 20m)')
    ax.grid(True)
    plt.savefig('soil_mesh_3d.png', dpi=300, bbox_inches='tight')
    plt.show()
    
except ImportError:
    print("Para visualización, instala vfo: pip install vfo")

# -------------------------
# INFORMACIÓN DE LA MALLA
# -------------------------
print("\nInformación de la malla:")
print(f"Dimensiones del dominio: {Lx}m x {Ly}m x {Lz}m")
print(f"Número de elementos: {nx} x {ny} x {nz}")
print(f"Tamaño de elementos: {dx}m x {dy}m x {dz}m")
print(f"Número total de nodos: {(nx+1)*(ny+1)*(nz+1)}")
print(f"Número total de elementos: {nx*ny*nz}")

# Exportar coordenadas de nodos
with open('node_coordinates.csv', 'w') as f:
    f.write('NodeTag,X,Y,Z\n')
    for tag, coord in nodeCoord.items():
        f.write(f'{tag},{coord[0]},{coord[1]},{coord[2]}\n')

print("\nCoordenadas de nodos exportadas a 'node_coordinates.csv'")