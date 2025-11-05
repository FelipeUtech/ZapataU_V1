import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# -------------------------
# INICIALIZACIÓN
# -------------------------
ops.wipe()
ops.model('basic', '-ndm', 3, '-ndf', 3)    # 3D problem, 3 DOF per node

# -------------------------
# PARÁMETROS GEOMÉTRICOS - SUELO
# -------------------------
# Dimensiones del dominio de suelo
Lx_soil = 20.0    # Longitud en x (m)
Ly_soil = 20.0    # Longitud en y (m)
Lz_soil = 20.0    # Profundidad en z (m)

# Discretización mejorada de la malla de suelo
# Malla más fina para mejor captura del comportamiento de la zapata
nx = 20      # Número de elementos en x (aumentado de 10 a 20)
ny = 20      # Número de elementos en y (aumentado de 10 a 20)
nz = 15      # Número de elementos en z (aumentado de 10 a 15)

# Calcula espaciamiento
dx = Lx_soil/nx
dy = Ly_soil/ny
dz = Lz_soil/nz

# -------------------------
# PARÁMETROS GEOMÉTRICOS - ZAPATA
# -------------------------
# Zapata cuadrada centrada en el dominio
B_zapata = 3.0    # Ancho de la zapata (m)
L_zapata = 3.0    # Largo de la zapata (m)
h_zapata = 0.6    # Espesor de la zapata (m)

# Posición centrada de la zapata
x_center = Lx_soil / 2.0
y_center = Ly_soil / 2.0
z_zapata = 0.0    # Superficie del suelo

# Límites de la zapata
x_min_zapata = x_center - B_zapata/2
x_max_zapata = x_center + B_zapata/2
y_min_zapata = y_center - L_zapata/2
y_max_zapata = y_center + L_zapata/2

print(f"\n{'='*70}")
print(f"ANÁLISIS REFINADO DE ZAPATA SOBRE SUELO 3D")
print(f"{'='*70}\n")

# -------------------------
# CREACIÓN DE NODOS - SUELO
# -------------------------
print("Generando nodos del suelo...")

nodeCounter = 1
nodeCoord = {}
surface_nodes = []  # Nodos en la superficie
zapata_nodes = []   # Nodos bajo la zapata

for k in range(nz + 1):    # z direction
    z = -k * dz
    for j in range(ny + 1):  # y direction
        y = j * dy
        for i in range(nx + 1):  # x direction
            x = i * dx
            ops.node(nodeCounter, x, y, z)
            nodeCoord[nodeCounter] = (x, y, z)

            # Identificar nodos en la superficie
            if k == 0:
                surface_nodes.append(nodeCounter)
                # Identificar nodos bajo la zapata
                if (x_min_zapata <= x <= x_max_zapata and
                    y_min_zapata <= y <= y_max_zapata):
                    zapata_nodes.append(nodeCounter)

            nodeCounter += 1

print(f"Total de nodos del suelo: {nodeCounter-1}")
print(f"Nodos en la superficie: {len(surface_nodes)}")
print(f"Nodos bajo la zapata: {len(zapata_nodes)}")
print(f"Tamaño de elemento: {dx:.2f}m × {dy:.2f}m × {dz:.2f}m")

# -------------------------
# CONDICIONES DE BORDE
# -------------------------
print("\nAplicando condiciones de borde...")

nodesPerLayer = (nx + 1) * (ny + 1)

# Diccionario para almacenar restricciones de cada nodo
node_constraints = {}

# Fijar base (z = -Lz_soil) - todos los DOF
baseNodeTags = list(range(nodesPerLayer * nz + 1, nodesPerLayer * (nz + 1) + 1))
for nodeTag in baseNodeTags:
    node_constraints[nodeTag] = [1, 1, 1]

# Fijar bordes laterales con rodillos (permiten movimiento vertical)
for k in range(nz + 1):
    currentLayer = k * nodesPerLayer

    # Borde x = 0
    for j in range(ny + 1):
        nodeTag = currentLayer + j * (nx + 1) + 1
        if nodeTag not in node_constraints:
            node_constraints[nodeTag] = [1, 0, 0]
        else:
            node_constraints[nodeTag][0] = 1

    # Borde x = Lx
    for j in range(ny + 1):
        nodeTag = currentLayer + j * (nx + 1) + (nx + 1)
        if nodeTag not in node_constraints:
            node_constraints[nodeTag] = [1, 0, 0]
        else:
            node_constraints[nodeTag][0] = 1

    # Borde y = 0
    for i in range(nx + 1):
        nodeTag = currentLayer + i + 1
        if nodeTag not in node_constraints:
            node_constraints[nodeTag] = [0, 1, 0]
        else:
            node_constraints[nodeTag][1] = 1

    # Borde y = Ly
    for i in range(nx + 1):
        nodeTag = currentLayer + ny * (nx + 1) + i + 1
        if nodeTag not in node_constraints:
            node_constraints[nodeTag] = [0, 1, 0]
        else:
            node_constraints[nodeTag][1] = 1

# Aplicar todas las restricciones
for nodeTag, constraints in node_constraints.items():
    ops.fix(nodeTag, *constraints)

print(f"Condiciones de borde aplicadas: {len(node_constraints)} nodos restringidos")
print(f"  - {len(baseNodeTags)} nodos completamente fijos en la base")

# -------------------------
# MATERIALES
# -------------------------
print("\nDefiniendo materiales...")

# Material del suelo (arena densa o arcilla firme)
E_soil = 30000.0      # Módulo de Young del suelo (kPa)
nu_soil = 0.3         # Coeficiente de Poisson
rho_soil = 1800.0     # Densidad del suelo (kg/m³)

# Material del concreto (zapata)
E_concrete = 25e6     # Módulo de Young del concreto (kPa) ~ 25 GPa
nu_concrete = 0.2     # Coeficiente de Poisson
rho_concrete = 2400.0 # Densidad del concreto (kg/m³)

ops.nDMaterial('ElasticIsotropic', 1, E_soil, nu_soil, rho_soil)
ops.nDMaterial('ElasticIsotropic', 2, E_concrete, nu_concrete, rho_concrete)

print(f"Material 1 - Suelo: E={E_soil/1000:.1f} MPa, ν={nu_soil}, ρ={rho_soil} kg/m³")
print(f"Material 2 - Concreto: E={E_concrete/1000:.1f} MPa, ν={nu_concrete}, ρ={rho_concrete} kg/m³")

# -------------------------
# ELEMENTOS - SUELO
# -------------------------
print("\nGenerando elementos del suelo...")
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

print(f"Total de elementos del suelo creados: {elementCounter-1}")

# -------------------------
# CARGAS
# -------------------------
print("\nAplicando cargas...")

# Definir series temporal
ops.timeSeries('Linear', 1)
ops.pattern('Plain', 1, 1)

# Parámetros de carga
P_column = 1000.0      # Carga de columna (kN)
P_zapata = B_zapata * L_zapata * h_zapata * rho_concrete * 9.81 / 1000  # Peso propio zapata (kN)
P_total = P_column + P_zapata  # Carga total (kN)

# Distribuir la carga entre los nodos bajo la zapata
if len(zapata_nodes) > 0:
    P_per_node = -P_total / len(zapata_nodes)  # Negativo porque es hacia abajo

    for node in zapata_nodes:
        ops.load(node, 0.0, 0.0, P_per_node)

    print(f"Carga de columna: {P_column:.2f} kN")
    print(f"Peso propio zapata: {P_zapata:.2f} kN")
    print(f"Carga total: {P_total:.2f} kN")
    print(f"Carga distribuida en {len(zapata_nodes)} nodos: {P_per_node:.4f} kN/nodo")
    print(f"Presión de contacto: {P_total/(B_zapata*L_zapata):.2f} kPa")
else:
    print("ERROR: No se encontraron nodos bajo la zapata")

# -------------------------
# ANÁLISIS
# -------------------------
print("\n" + "="*70)
print("EJECUTANDO ANÁLISIS ESTÁTICO")
print("="*70 + "\n")

# Sistema de ecuaciones
ops.system('BandGeneral')

# Numerador
ops.numberer('RCM')

# Restricciones
ops.constraints('Plain')

# Integrador
ops.integrator('LoadControl', 1.0)

# Algoritmo
ops.algorithm('Linear')

# Análisis
ops.analysis('Static')

# Ejecutar análisis
print("Analizando...")
ok = ops.analyze(1)

if ok == 0:
    print("✓ Análisis completado exitosamente\n")
else:
    print("✗ Error en el análisis\n")

# -------------------------
# EXTRACCIÓN DE RESULTADOS
# -------------------------
print("="*70)
print("RESULTADOS DEL ANÁLISIS")
print("="*70 + "\n")

# Obtener desplazamientos de nodos bajo la zapata
settlements = []
zapata_coords_settlements = []
for node in zapata_nodes:
    disp = ops.nodeDisp(node, 3)  # Desplazamiento en z
    settlement = abs(disp * 1000)  # Convertir a mm
    settlements.append(settlement)
    coord = nodeCoord[node]
    zapata_coords_settlements.append((coord[0], coord[1], settlement))

# Estadísticas de asentamiento
if settlements:
    max_settlement = max(settlements)
    min_settlement = min(settlements)
    avg_settlement = np.mean(settlements)
    std_settlement = np.std(settlements)

    print(f"ASENTAMIENTOS BAJO LA ZAPATA:")
    print(f"  Asentamiento máximo: {max_settlement:.4f} mm")
    print(f"  Asentamiento mínimo: {min_settlement:.4f} mm")
    print(f"  Asentamiento promedio: {avg_settlement:.4f} mm")
    print(f"  Desviación estándar: {std_settlement:.4f} mm")
    print(f"  Diferencial: {max_settlement - min_settlement:.4f} mm")

# Asentamiento de todos los nodos en superficie
surface_settlements = []
surface_coords = []
for node in surface_nodes:
    disp = ops.nodeDisp(node, 3)
    settlement = abs(disp * 1000)  # mm
    surface_settlements.append(settlement)
    coord = nodeCoord[node]
    surface_coords.append((coord[0], coord[1], settlement))

print(f"\nASENTAMIENTO MÁXIMO EN SUPERFICIE: {max(surface_settlements):.4f} mm")

# -------------------------
# VISUALIZACIÓN DE RESULTADOS
# -------------------------
print("\n" + "="*70)
print("GENERANDO GRÁFICAS")
print("="*70 + "\n")

# Crear figura con múltiples subplots
fig = plt.figure(figsize=(18, 14))

# 1. Mapa de contorno de asentamientos en superficie
ax1 = fig.add_subplot(2, 3, 1)
x_coords = [c[0] for c in surface_coords]
y_coords = [c[1] for c in surface_coords]
z_values = [c[2] for c in surface_coords]

# Crear grid regular para contorno
xi = np.linspace(0, Lx_soil, 100)
yi = np.linspace(0, Ly_soil, 100)
Xi, Yi = np.meshgrid(xi, yi)

from scipy.interpolate import griddata
Zi = griddata((x_coords, y_coords), z_values, (Xi, Yi), method='cubic')

contour = ax1.contourf(Xi, Yi, Zi, levels=20, cmap='jet')
plt.colorbar(contour, ax=ax1, label='Asentamiento (mm)')
ax1.set_xlabel('X (m)')
ax1.set_ylabel('Y (m)')
ax1.set_title('Mapa de Asentamientos en Superficie', fontweight='bold')
ax1.set_aspect('equal')

# Dibujar contorno de zapata
from matplotlib.patches import Rectangle
rect = Rectangle((x_min_zapata, y_min_zapata), B_zapata, L_zapata,
                 linewidth=3, edgecolor='white', facecolor='none', linestyle='--')
ax1.add_patch(rect)
ax1.text(x_center, y_center, 'ZAPATA', ha='center', va='center',
         color='white', fontweight='bold', fontsize=12,
         bbox=dict(boxstyle='round', facecolor='black', alpha=0.5))

# 2. Perfil de asentamiento central (corte X)
ax2 = fig.add_subplot(2, 3, 2)
# Nodos en y = y_center
central_nodes_x = []
for node in surface_nodes:
    coord = nodeCoord[node]
    if abs(coord[1] - y_center) < dy/2:
        disp = abs(ops.nodeDisp(node, 3) * 1000)
        central_nodes_x.append((coord[0], disp))

central_nodes_x.sort()
if central_nodes_x:
    x_profile = [c[0] for c in central_nodes_x]
    s_profile = [c[1] for c in central_nodes_x]
    ax2.plot(x_profile, s_profile, 'b-o', linewidth=2, markersize=5)
    ax2.axvspan(x_min_zapata, x_max_zapata, alpha=0.3, color='orange', label='Zapata')
    ax2.set_xlabel('X (m)')
    ax2.set_ylabel('Asentamiento (mm)')
    ax2.set_title('Perfil de Asentamiento - Corte Central en X', fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    ax2.invert_yaxis()

# 3. Perfil de asentamiento central (corte Y)
ax3 = fig.add_subplot(2, 3, 3)
# Nodos en x = x_center
central_nodes_y = []
for node in surface_nodes:
    coord = nodeCoord[node]
    if abs(coord[0] - x_center) < dx/2:
        disp = abs(ops.nodeDisp(node, 3) * 1000)
        central_nodes_y.append((coord[1], disp))

central_nodes_y.sort()
if central_nodes_y:
    y_profile = [c[0] for c in central_nodes_y]
    s_profile_y = [c[1] for c in central_nodes_y]
    ax3.plot(y_profile, s_profile_y, 'r-o', linewidth=2, markersize=5)
    ax3.axvspan(y_min_zapata, y_max_zapata, alpha=0.3, color='orange', label='Zapata')
    ax3.set_xlabel('Y (m)')
    ax3.set_ylabel('Asentamiento (mm)')
    ax3.set_title('Perfil de Asentamiento - Corte Central en Y', fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    ax3.invert_yaxis()

# 4. Vista 3D de asentamientos en superficie
ax4 = fig.add_subplot(2, 3, 4, projection='3d')
scatter = ax4.scatter(x_coords, y_coords, z_values, c=z_values,
                     cmap='jet', s=30, alpha=0.6)
ax4.set_xlabel('X (m)')
ax4.set_ylabel('Y (m)')
ax4.set_zlabel('Asentamiento (mm)')
ax4.set_title('Vista 3D de Asentamientos en Superficie', fontweight='bold')
ax4.view_init(elev=25, azim=45)
plt.colorbar(scatter, ax=ax4, label='Asentamiento (mm)', shrink=0.6)

# 5. Distribución de asentamientos bajo la zapata
ax5 = fig.add_subplot(2, 3, 5)
if zapata_coords_settlements:
    xz = [c[0] for c in zapata_coords_settlements]
    yz = [c[1] for c in zapata_coords_settlements]
    sz = [c[2] for c in zapata_coords_settlements]

    scatter_zapata = ax5.scatter(xz, yz, c=sz, cmap='viridis', s=100, edgecolors='black')
    plt.colorbar(scatter_zapata, ax=ax5, label='Asentamiento (mm)')
    ax5.set_xlabel('X (m)')
    ax5.set_ylabel('Y (m)')
    ax5.set_title('Distribución de Asentamientos Bajo la Zapata', fontweight='bold')
    ax5.set_aspect('equal')
    ax5.grid(True, alpha=0.3)

# 6. Información del análisis
ax6 = fig.add_subplot(2, 3, 6)
ax6.axis('off')

info_text = f"""
═══════════════════════════════════════
     DATOS DEL ANÁLISIS REFINADO
═══════════════════════════════════════

GEOMETRÍA DEL SUELO:
  Dimensiones: {Lx_soil}m × {Ly_soil}m × {Lz_soil}m
  Malla: {nx} × {ny} × {nz} elementos
  Tamaño elemento: {dx:.2f}m × {dy:.2f}m × {dz:.2f}m
  Total nodos: {(nx+1)*(ny+1)*(nz+1)}
  Total elementos: {nx*ny*nz}

GEOMETRÍA DE LA ZAPATA:
  Dimensiones: {B_zapata}m × {L_zapata}m × {h_zapata}m
  Área contacto: {B_zapata*L_zapata:.2f} m²
  Nodos bajo zapata: {len(zapata_nodes)}

PROPIEDADES:
  E suelo: {E_soil/1000:.0f} MPa
  ν suelo: {nu_soil}
  ρ suelo: {rho_soil} kg/m³

CARGAS:
  Carga columna: {P_column:.2f} kN
  Peso zapata: {P_zapata:.2f} kN
  Carga total: {P_total:.2f} kN
  Presión: {P_total/(B_zapata*L_zapata):.2f} kPa

RESULTADOS:
  Asentamiento máx: {max_settlement:.4f} mm
  Asentamiento prom: {avg_settlement:.4f} mm
  Desv. estándar: {std_settlement:.4f} mm
  Diferencial: {max_settlement - min_settlement:.4f} mm

VERIFICACIONES:
"""

diff_ratio = (max_settlement - min_settlement) / max_settlement * 100 if max_settlement > 0 else 0
info_text += f"  Relación dif: {diff_ratio:.2f}%\n"
if max_settlement < 25:
    info_text += f"  ✓ Asentamiento < 25mm OK\n"
else:
    info_text += f"  ⚠ Asentamiento > 25mm\n"
if diff_ratio < 10:
    info_text += f"  ✓ Diferencial < 10% OK\n"
else:
    info_text += f"  ⚠ Diferencial > 10%\n"

ax6.text(0.05, 0.95, info_text, transform=ax6.transAxes,
         fontsize=9, verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))

plt.tight_layout()
plt.savefig('zapata_analysis_refined.png', dpi=300, bbox_inches='tight')
print("✓ Gráfica guardada: zapata_analysis_refined.png")

# -------------------------
# EXPORTAR RESULTADOS A CSV
# -------------------------
print("\nExportando resultados...")

# Exportar asentamientos en superficie
with open('surface_settlements_refined.csv', 'w') as f:
    f.write('X,Y,Settlement_mm\n')
    for coord in surface_coords:
        f.write(f'{coord[0]:.4f},{coord[1]:.4f},{coord[2]:.6f}\n')
print("✓ Archivo guardado: surface_settlements_refined.csv")

# Exportar asentamientos bajo zapata
with open('zapata_settlements_refined.csv', 'w') as f:
    f.write('NodeTag,X,Y,Settlement_mm\n')
    for i, node in enumerate(zapata_nodes):
        coord = nodeCoord[node]
        f.write(f'{node},{coord[0]:.4f},{coord[1]:.4f},{settlements[i]:.6f}\n')
print("✓ Archivo guardado: zapata_settlements_refined.csv")

# Resumen del análisis
with open('analysis_summary_refined.txt', 'w') as f:
    f.write("="*70 + "\n")
    f.write("RESUMEN DEL ANÁLISIS REFINADO DE ZAPATA\n")
    f.write("="*70 + "\n\n")
    f.write(f"Fecha: {np.datetime64('today')}\n\n")
    f.write(f"GEOMETRÍA:\n")
    f.write(f"  Zapata: {B_zapata}m × {L_zapata}m × {h_zapata}m\n")
    f.write(f"  Dominio suelo: {Lx_soil}m × {Ly_soil}m × {Lz_soil}m\n")
    f.write(f"  Malla: {nx} × {ny} × {nz} elementos\n")
    f.write(f"  Nodos bajo zapata: {len(zapata_nodes)}\n\n")
    f.write(f"CARGAS:\n")
    f.write(f"  Carga total: {P_total:.2f} kN\n")
    f.write(f"  Presión contacto: {P_total/(B_zapata*L_zapata):.2f} kPa\n\n")
    f.write(f"RESULTADOS PRINCIPALES:\n")
    f.write(f"  Asentamiento máximo: {max_settlement:.4f} mm\n")
    f.write(f"  Asentamiento mínimo: {min_settlement:.4f} mm\n")
    f.write(f"  Asentamiento promedio: {avg_settlement:.4f} mm\n")
    f.write(f"  Desviación estándar: {std_settlement:.4f} mm\n")
    f.write(f"  Asentamiento diferencial: {max_settlement - min_settlement:.4f} mm\n\n")
    f.write(f"VERIFICACIÓN:\n")
    f.write(f"  Relación diferencial: {diff_ratio:.2f}%\n")
    if max_settlement < 25:
        f.write(f"  ✓ Asentamiento < 25mm (ACEPTABLE)\n")
    else:
        f.write(f"  ⚠ Asentamiento ≥ 25mm (REVISAR - límite típico para estructuras)\n")
    if diff_ratio < 10:
        f.write(f"  ✓ Asentamiento diferencial < 10% (ACEPTABLE)\n")
    else:
        f.write(f"  ⚠ Asentamiento diferencial ≥ 10% (REVISAR)\n")

    f.write(f"\nNOTAS:\n")
    f.write(f"  - Malla refinada: {nx}×{ny}×{nz} ({(nx+1)*(ny+1)*(nz+1)} nodos)\n")
    f.write(f"  - {len(zapata_nodes)} nodos bajo zapata para mejor distribución de carga\n")
    f.write(f"  - Tamaño de elemento: {dx:.2f}m × {dy:.2f}m × {dz:.2f}m\n")

print("✓ Archivo guardado: analysis_summary_refined.txt")

print("\n" + "="*70)
print("ANÁLISIS REFINADO COMPLETADO")
print("="*70)
print("\nArchivos generados:")
print("  - zapata_analysis_refined.png")
print("  - surface_settlements_refined.csv")
print("  - zapata_settlements_refined.csv")
print("  - analysis_summary_refined.txt")
print("\n")
