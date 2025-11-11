#!/usr/bin/env python3
"""
Verificar calidad de elementos tetraédricos
"""
import pyvista as pv
import numpy as np

print("="*80)
print("VERIFICACIÓN DE CALIDAD DE MALLA")
print("="*80)

mesh_file = "mallas/zapata_3D_cuarto.vtu"
grid = pv.read(mesh_file)

print(f"\nEstadísticas de malla:")
print(f"  Nodos: {grid.n_points}")
print(f"  Elementos: {grid.n_cells}")

# Calcular volúmenes de elementos
points = np.array(grid.points)
cells = np.array(grid.cells)

print("\nVerificando volúmenes de elementos tetraédricos...")

element_id = 0
cell_idx = 0
volumes = []
negative_count = 0

while cell_idx < len(cells):
    n_points = cells[cell_idx]
    if n_points != 4:
        cell_idx += n_points + 1
        continue

    # Extraer índices de nodos
    n1 = int(cells[cell_idx + 1])
    n2 = int(cells[cell_idx + 2])
    n3 = int(cells[cell_idx + 3])
    n4 = int(cells[cell_idx + 4])

    # Coordenadas de los 4 nodos
    p1 = points[n1]
    p2 = points[n2]
    p3 = points[n3]
    p4 = points[n4]

    # Calcular volumen del tetraedro
    # V = (1/6) * |det([p2-p1, p3-p1, p4-p1])|
    v1 = p2 - p1
    v2 = p3 - p1
    v3 = p4 - p1

    # Volumen con signo
    vol = np.dot(v1, np.cross(v2, v3)) / 6.0

    volumes.append(vol)

    if vol < 0:
        negative_count += 1
        if negative_count <= 5:
            print(f"  ⚠️  Elemento {element_id}: volumen negativo = {vol:.6f}")

    element_id += 1
    cell_idx += n_points + 1

volumes = np.array(volumes)

print(f"\nResumen de volúmenes:")
print(f"  Total elementos: {len(volumes)}")
print(f"  Volumen mínimo: {volumes.min():.6f} m³")
print(f"  Volumen máximo: {volumes.max():.6f} m³")
print(f"  Volumen promedio: {volumes.mean():.6f} m³")
print(f"  Elementos con volumen negativo: {negative_count}")

if negative_count > 0:
    print(f"\n❌ PROBLEMA: {negative_count} elementos con volumen negativo")
    print("   Esto causa una matriz de rigidez singular")
    print("   Solución: Invertir el orden de nodos en estos elementos")
else:
    print(f"\n✓ Todos los elementos tienen volumen positivo")

# Calcular aspect ratio (calidad)
print(f"\nDistribución de calidad de elementos:")
quality = grid.compute_cell_quality()
q_values = quality['CellQuality']
print(f"  Calidad mínima: {q_values.min():.4f}")
print(f"  Calidad máxima: {q_values.max():.4f}")
print(f"  Calidad promedio: {q_values.mean():.4f}")

# Contar elementos de baja calidad
poor_quality = np.sum(q_values < 0.2)
print(f"  Elementos con calidad < 0.2: {poor_quality}")

print("\n" + "="*80)
