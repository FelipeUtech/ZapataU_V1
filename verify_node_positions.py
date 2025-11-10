#!/usr/bin/env python3
"""
Script para verificar las posiciones Z de nodos en la malla.
Verifica específicamente:
1. Nodos de la base de la zapata
2. Nodos del tope de la zapata
3. Nodos del tope del suelo excavado (contacto con zapata)
"""

import pyvista as pv
import numpy as np
import config

# Leer malla
mesh_file = "mallas/zapata_3D_cuarto.vtu"
print(f"Leyendo malla: {mesh_file}")
grid = pv.read(mesh_file)

points = grid.points
material_ids = grid.cell_data.get('dominio', None)

# Parámetros desde config
Df = config.ZAPATA['Df']
h_zapata = config.ZAPATA['h']
B = config.ZAPATA['B']
L = config.ZAPATA['L']

print("\n" + "="*80)
print("PARÁMETROS DE CONFIGURACIÓN")
print("="*80)
print(f"Profundidad de desplante (Df): {Df} m")
print(f"Espesor de zapata (h): {h_zapata} m")
print(f"Dimensiones zapata: {B}m × {L}m")

# Según el generador de malla
print("\n" + "="*80)
print("COORDENADAS Z ESPERADAS (según generate_mesh_quarter.py)")
print("="*80)
z_base_expected = -Df - h_zapata
z_top_expected = -Df
print(f"Base de zapata: z = -Df - h = -{Df} - {h_zapata} = {z_base_expected} m")
print(f"Tope de zapata (fondo excavación): z = -Df = -{Df} = {z_top_expected} m")
print(f"Superficie del terreno: z = 0.0 m")

# Analizar distribución Z de todos los nodos
print("\n" + "="*80)
print("ANÁLISIS DE COORDENADAS Z EN LA MALLA")
print("="*80)
z_coords = points[:, 2]
print(f"Total de nodos: {len(points):,}")
print(f"Z mínimo: {z_coords.min():.4f} m")
print(f"Z máximo: {z_coords.max():.4f} m")

# Encontrar valores Z únicos cerca de niveles importantes
tolerance = 0.05  # 5 cm de tolerancia

print("\n" + "="*80)
print("VERIFICACIÓN DE NODOS EN NIVELES CLAVE")
print("="*80)

# 1. Nodos en la base de la zapata
z_base_check = z_base_expected
nodes_base = np.where(np.abs(z_coords - z_base_check) < tolerance)[0]
print(f"\n1. NODOS EN BASE DE ZAPATA (z ≈ {z_base_check:.2f} m):")
print(f"   Encontrados: {len(nodes_base)} nodos")
if len(nodes_base) > 0:
    z_values_base = z_coords[nodes_base]
    print(f"   Rango Z real: [{z_values_base.min():.4f}, {z_values_base.max():.4f}] m")
    print(f"   Z promedio: {z_values_base.mean():.4f} m")

    # Mostrar algunos nodos de ejemplo
    print(f"\n   Ejemplos de nodos (primeros 5):")
    for i, node_idx in enumerate(nodes_base[:5]):
        x, y, z = points[node_idx]
        print(f"   Nodo {node_idx+1}: x={x:.4f}, y={y:.4f}, z={z:.4f}")

# 2. Nodos en el tope de la zapata / fondo de excavación
z_top_check = z_top_expected
nodes_top = np.where(np.abs(z_coords - z_top_check) < tolerance)[0]
print(f"\n2. NODOS EN TOPE DE ZAPATA / FONDO EXCAVACIÓN (z ≈ {z_top_check:.2f} m):")
print(f"   Encontrados: {len(nodes_top)} nodos")
if len(nodes_top) > 0:
    z_values_top = z_coords[nodes_top]
    print(f"   Rango Z real: [{z_values_top.min():.4f}, {z_values_top.max():.4f}] m")
    print(f"   Z promedio: {z_values_top.mean():.4f} m")

    # Filtrar por área de zapata (modelo 1/4)
    # Para modelo 1/4, la zapata está centrada y ocupa B/4 × L/4
    # Según el generador, está en (x0/2, y0/2)
    Lx_completo = config.obtener_dimensiones_dominio()['Lx']
    Ly_completo = config.obtener_dimensiones_dominio()['Ly']
    x0 = Lx_completo - B / 2
    y0 = Ly_completo - L / 2

    x_min_zapata = x0 / 2
    y_min_zapata = y0 / 2
    x_max_zapata = x0 / 2 + B / 4
    y_max_zapata = y0 / 2 + L / 4

    nodes_top_in_footing = []
    for node_idx in nodes_top:
        x, y, z = points[node_idx]
        if (x_min_zapata <= x <= x_max_zapata and
            y_min_zapata <= y <= y_max_zapata):
            nodes_top_in_footing.append(node_idx)

    print(f"\n   Nodos dentro del área de zapata:")
    print(f"   Área zapata: x=[{x_min_zapata:.2f}, {x_max_zapata:.2f}], y=[{y_min_zapata:.2f}, {y_max_zapata:.2f}]")
    print(f"   Encontrados: {len(nodes_top_in_footing)} nodos")

    if len(nodes_top_in_footing) > 0:
        print(f"\n   Ejemplos de nodos en tope de zapata (primeros 5):")
        for i, node_idx in enumerate(nodes_top_in_footing[:5]):
            x, y, z = points[node_idx]
            print(f"   Nodo {node_idx+1}: x={x:.4f}, y={y:.4f}, z={z:.4f}")

# 3. Nodos en superficie (z ≈ 0)
z_surface_check = 0.0
nodes_surface = np.where(np.abs(z_coords - z_surface_check) < tolerance)[0]
print(f"\n3. NODOS EN SUPERFICIE (z ≈ {z_surface_check:.2f} m):")
print(f"   Encontrados: {len(nodes_surface)} nodos")
if len(nodes_surface) > 0:
    z_values_surface = z_coords[nodes_surface]
    print(f"   Rango Z real: [{z_values_surface.min():.4f}, {z_values_surface.max():.4f}] m")
    print(f"   Z promedio: {z_values_surface.mean():.4f} m")

# 4. Analizar elementos por material para confirmar
print("\n" + "="*80)
print("ANÁLISIS POR MATERIAL")
print("="*80)

num_estratos = len(config.ESTRATOS_SUELO)
mat_id_zapata = num_estratos + 1

# Obtener nodos de elementos de zapata
zapata_elements = np.where(material_ids == mat_id_zapata)[0]
print(f"\nElementos de ZAPATA (material_id={mat_id_zapata}): {len(zapata_elements)}")

# Extraer todos los nodos únicos de elementos de zapata
zapata_node_indices = set()
cell_idx = 0
cells = grid.cells
for elem_idx in zapata_elements:
    # Buscar este elemento en el array de cells
    current_elem = 0
    cell_idx = 0
    while current_elem <= elem_idx and cell_idx < len(cells):
        n_points = cells[cell_idx]
        if current_elem == elem_idx:
            # Este es nuestro elemento
            for i in range(1, n_points + 1):
                zapata_node_indices.add(cells[cell_idx + i])
            break
        cell_idx += n_points + 1
        current_elem += 1

zapata_nodes = list(zapata_node_indices)
print(f"Nodos únicos en elementos de zapata: {len(zapata_nodes)}")

if len(zapata_nodes) > 0:
    z_zapata_nodes = z_coords[zapata_nodes]
    print(f"Rango Z de nodos de zapata: [{z_zapata_nodes.min():.4f}, {z_zapata_nodes.max():.4f}] m")
    print(f"  -> Base esperada: {z_base_expected:.2f} m, Real: {z_zapata_nodes.min():.4f} m")
    print(f"  -> Tope esperado: {z_top_expected:.2f} m, Real: {z_zapata_nodes.max():.4f} m")

# Resumen y diagnóstico
print("\n" + "="*80)
print("DIAGNÓSTICO Y RECOMENDACIONES")
print("="*80)

print("\n✓ CORRECTO en generate_mesh_quarter.py:")
print(f"  Base zapata: z = {z_base_expected} m")
print(f"  Tope zapata: z = {z_top_expected} m")

print("\n❌ ERROR en run_analysis.py línea 194:")
print(f"  Código actual: z_tope_zapata = -Df + h_zapata = {-Df + h_zapata:.2f} m")
print(f"  Debería ser:   z_tope_zapata = -Df = {-Df:.2f} m")

print("\n📋 EXPLICACIÓN:")
print(f"  • La zapata está ENTERRADA")
print(f"  • Excavación va desde z=0 hasta z=-Df ({-Df}m)")
print(f"  • Zapata se apoya en el FONDO de la excavación (z=-Df)")
print(f"  • Por tanto:")
print(f"    - Tope de zapata = Fondo excavación = -Df = {-Df} m")
print(f"    - Base de zapata = -Df - h = {z_base_expected} m")

print("\n🔧 SOLUCIÓN:")
print("  Cambiar en run_analysis.py línea 194:")
print(f"  De:  z_tope_zapata = -Df + h_zapata  # ❌ Incorrecto")
print(f"  A:   z_tope_zapata = -Df              # ✓ Correcto")

print("\n" + "="*80 + "\n")
