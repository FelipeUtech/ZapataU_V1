#!/usr/bin/env python3
"""
Visualiza el problema de desconexión entre zapata y suelo.
"""

import numpy as np
from pathlib import Path

def leer_nodos_desde_tcl(archivo_tcl):
    """Lee nodos desde archivo TCL."""
    nodos = {}
    with open(archivo_tcl, 'r') as f:
        for linea in f:
            linea = linea.strip()
            if linea.startswith('node '):
                partes = linea.split()
                if len(partes) >= 5:
                    tag = int(partes[1])
                    x = float(partes[2])
                    y = float(partes[3])
                    z = float(partes[4])
                    nodos[tag] = (x, y, z)
    return nodos

def leer_elementos_desde_tcl(archivo_tcl):
    """Lee elementos desde archivo TCL."""
    elementos = []
    with open(archivo_tcl, 'r') as f:
        for linea in f:
            linea = linea.strip()
            if linea.startswith('element FourNodeTetrahedron'):
                partes = linea.split()
                if len(partes) >= 8:
                    elem_tag = int(partes[2])
                    n1 = int(partes[3])
                    n2 = int(partes[4])
                    n3 = int(partes[5])
                    n4 = int(partes[6])
                    mat_tag = int(partes[7])
                    elementos.append({
                        'tag': elem_tag,
                        'nodos': [n1, n2, n3, n4],
                        'material': mat_tag
                    })
    return elementos

def main():
    input_dir = Path("opensees_input")
    nodos_file = input_dir / "nodes.tcl"
    elementos_file = input_dir / "elements.tcl"

    nodos = leer_nodos_desde_tcl(nodos_file)
    elementos = leer_elementos_desde_tcl(elementos_file)

    # Separar nodos por material
    nodos_zapata = set()
    nodos_suelo = set()

    for elem in elementos:
        if elem['material'] == 4:  # Zapata
            nodos_zapata.update(elem['nodos'])
        else:  # Suelo
            nodos_suelo.update(elem['nodos'])

    # Analizar coordenadas
    coords_zapata = np.array([nodos[n] for n in nodos_zapata])
    coords_suelo = np.array([nodos[n] for n in nodos_suelo])

    print("="*80)
    print("PROBLEMA DETECTADO: ZAPATA Y SUELO DESCONECTADOS")
    print("="*80)

    print("\n📍 NODOS DE LA ZAPATA (Material 4):")
    print(f"   Total: {len(nodos_zapata)} nodos")
    print(f"   Rango X: [{coords_zapata[:, 0].min():.3f}, {coords_zapata[:, 0].max():.3f}] m")
    print(f"   Rango Y: [{coords_zapata[:, 1].min():.3f}, {coords_zapata[:, 1].max():.3f}] m")
    print(f"   Rango Z: [{coords_zapata[:, 2].min():.3f}, {coords_zapata[:, 2].max():.3f}] m")

    print("\n🌍 NODOS DEL SUELO (Materiales 1, 2, 3):")
    print(f"   Total: {len(nodos_suelo)} nodos")
    print(f"   Rango X: [{coords_suelo[:, 0].min():.3f}, {coords_suelo[:, 0].max():.3f}] m")
    print(f"   Rango Y: [{coords_suelo[:, 1].min():.3f}, {coords_suelo[:, 1].max():.3f}] m")
    print(f"   Rango Z: [{coords_suelo[:, 2].min():.3f}, {coords_suelo[:, 2].max():.3f}] m")

    print("\n🔍 ANÁLISIS DEL PROBLEMA:")
    print(f"   • Z máximo del suelo: {coords_suelo[:, 2].max():.3f} m")
    print(f"   • Z mínimo de la zapata: {coords_zapata[:, 2].min():.3f} m")
    print(f"   • Brecha entre suelo y zapata: {coords_zapata[:, 2].min() - coords_suelo[:, 2].max():.3f} m")

    if coords_zapata[:, 2].min() > coords_suelo[:, 2].max():
        print("\n   ⚠️  La zapata está ENCIMA del suelo (flotando en el aire)")
        print("   No hay contacto físico entre ambos.")
    elif coords_zapata[:, 2].max() < coords_suelo[:, 2].min():
        print("\n   ⚠️  La zapata está DEBAJO del suelo")
        print("   No hay contacto físico entre ambos.")
    else:
        print("\n   ⚠️  Los rangos de Z se superponen, pero no hay nodos compartidos")
        print("   La malla tiene dos conjuntos separados de nodos en la misma región.")

    # Buscar nodos cercanos
    print("\n🔎 BUSCANDO NODOS CERCANOS (distancia < 0.1 m):")
    min_dist = float('inf')
    nodo_zapata_cercano = None
    nodo_suelo_cercano = None

    for nz in nodos_zapata:
        for ns in nodos_suelo:
            dist = np.linalg.norm(np.array(nodos[nz]) - np.array(nodos[ns]))
            if dist < min_dist:
                min_dist = dist
                nodo_zapata_cercano = nz
                nodo_suelo_cercano = ns

    print(f"   Distancia mínima entre zapata y suelo: {min_dist:.6f} m")
    if min_dist < 0.01:
        print(f"   Nodo zapata {nodo_zapata_cercano}: {nodos[nodo_zapata_cercano]}")
        print(f"   Nodo suelo {nodo_suelo_cercano}: {nodos[nodo_suelo_cercano]}")
        print("\n   💡 Hay nodos MUY cercanos pero NO son el mismo nodo.")
        print("   Esto indica que la malla tiene nodos duplicados en la interfaz.")

    print("\n" + "="*80)
    print("CAUSA DEL PROBLEMA:")
    print("="*80)
    print("""
La generación de malla creó dos regiones separadas:
- Una región para la zapata (Material 4)
- Una región para el suelo (Materiales 1, 2, 3)

Sin embargo, estas regiones NO comparten nodos en la interfaz.
Probablemente el generador de malla (GMSH) creó nodos duplicados.

SOLUCIÓN:
El script generate_mesh_from_config.py debe asegurar que los nodos en la
interfaz zapata-suelo sean COMPARTIDOS entre ambos volúmenes.

En GMSH, esto se logra usando:
1. Coherence o Fuse para fusionar geometrías
2. Asegurar que la interfaz geométrica sea la misma superficie
3. Usar Physical Groups correctamente para materiales
""")

    print("\n📁 Revisar archivo: generate_mesh_from_config.py")
    print("   Buscar la definición de volúmenes y asegurar que compartan superficies.")

    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
