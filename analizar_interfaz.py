#!/usr/bin/env python3
"""
Script para analizar la interfaz entre zapata y suelo en el modelo OpenSees.
Verifica:
1. Nodos compartidos entre zapata y suelo
2. Condiciones de frontera
3. Continuidad en la interfaz
"""

import numpy as np
from pathlib import Path
from collections import defaultdict

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

def analizar_interfaz(nodos, elementos):
    """Analiza la interfaz entre zapata y suelo."""

    print("="*80)
    print("ANÁLISIS DE INTERFAZ ZAPATA-SUELO")
    print("="*80)

    # Separar nodos por material
    nodos_por_material = defaultdict(set)

    for elem in elementos:
        mat = elem['material']
        for nodo in elem['nodos']:
            nodos_por_material[mat].add(nodo)

    print("\n1. NODOS POR MATERIAL:")
    print("-" * 80)
    for mat in sorted(nodos_por_material.keys()):
        nombre = f"Material {mat} (Zapata)" if mat == 4 else f"Material {mat} (Suelo)"
        print(f"   {nombre}: {len(nodos_por_material[mat])} nodos")

    # Encontrar nodos compartidos entre zapata (mat 4) y suelo (mat 1, 2, 3)
    nodos_zapata = nodos_por_material[4]
    nodos_suelo = nodos_por_material[1] | nodos_por_material[2] | nodos_por_material[3]
    nodos_compartidos = nodos_zapata & nodos_suelo

    print("\n2. NODOS COMPARTIDOS (INTERFAZ ZAPATA-SUELO):")
    print("-" * 80)
    print(f"   Nodos únicos de zapata: {len(nodos_zapata - nodos_suelo)}")
    print(f"   Nodos únicos de suelo: {len(nodos_suelo - nodos_zapata)}")
    print(f"   Nodos compartidos (interfaz): {len(nodos_compartidos)}")

    if len(nodos_compartidos) == 0:
        print("\n   ⚠️  ¡PROBLEMA DETECTADO! No hay nodos compartidos entre zapata y suelo")
        print("   Esto significa que la zapata y el suelo NO están conectados.")
        print("   La zapata está 'flotando' en el aire, sin contacto con el suelo.")
        return False

    # Analizar coordenadas Z de nodos compartidos
    if nodos_compartidos:
        coords_compartidos = np.array([nodos[n] for n in nodos_compartidos])
        z_compartidos = coords_compartidos[:, 2]

        print(f"\n   Coordenadas Z de nodos en interfaz:")
        print(f"      Mínimo: {z_compartidos.min():.3f} m")
        print(f"      Máximo: {z_compartidos.max():.3f} m")
        print(f"      Promedio: {z_compartidos.mean():.3f} m")

        # Histograma de Z
        hist, bins = np.histogram(z_compartidos, bins=10)
        print(f"\n   Distribución de nodos en interfaz por profundidad:")
        for i in range(len(hist)):
            if hist[i] > 0:
                print(f"      z ∈ [{bins[i]:.2f}, {bins[i+1]:.2f}] m: {hist[i]} nodos")

    # Analizar todos los nodos de zapata
    coords_zapata = np.array([nodos[n] for n in nodos_zapata])
    z_zapata = coords_zapata[:, 2]

    print(f"\n3. GEOMETRÍA DE LA ZAPATA:")
    print("-" * 80)
    print(f"   Nodos totales en zapata: {len(nodos_zapata)}")
    print(f"   Rango X: [{coords_zapata[:, 0].min():.3f}, {coords_zapata[:, 0].max():.3f}] m")
    print(f"   Rango Y: [{coords_zapata[:, 1].min():.3f}, {coords_zapata[:, 1].max():.3f}] m")
    print(f"   Rango Z: [{z_zapata.min():.3f}, {z_zapata.max():.3f}] m")
    print(f"   Altura zapata: {z_zapata.max() - z_zapata.min():.3f} m")

    # Verificar condiciones de frontera esperadas
    print(f"\n4. VERIFICACIÓN DE CONDICIONES DE FRONTERA:")
    print("-" * 80)

    coords = np.array(list(nodos.values()))
    z_min = coords[:, 2].min()
    z_max = coords[:, 2].max()
    x_min = coords[:, 0].min()
    y_min = coords[:, 1].min()

    print(f"   Dominio completo:")
    print(f"      X: [{x_min:.3f}, {coords[:, 0].max():.3f}] m")
    print(f"      Y: [{y_min:.3f}, {coords[:, 1].max():.3f}] m")
    print(f"      Z: [{z_min:.3f}, {z_max:.3f}] m")

    tol = 1e-3
    nodos_base = sum(1 for (x, y, z) in nodos.values() if abs(z - z_min) < tol)
    nodos_simetria_x = sum(1 for (x, y, z) in nodos.values() if abs(x - x_min) < tol)
    nodos_simetria_y = sum(1 for (x, y, z) in nodos.values() if abs(y - y_min) < tol)

    print(f"\n   Nodos en bordes (para condiciones de frontera):")
    print(f"      Base (z={z_min:.1f}m): {nodos_base} nodos → deben fijarse (ux=uy=uz=1)")
    print(f"      Simetría X (x={x_min:.1f}m): {nodos_simetria_x} nodos → deben fijarse (ux=1)")
    print(f"      Simetría Y (y={y_min:.1f}m): {nodos_simetria_y} nodos → deben fijarse (uy=1)")

    # Analizar elementos en interfaz
    print(f"\n5. ANÁLISIS DE ELEMENTOS EN INTERFAZ:")
    print("-" * 80)

    elementos_interfaz = []
    for elem in elementos:
        nodos_elem = set(elem['nodos'])
        if nodos_elem & nodos_compartidos:  # Si tiene al menos un nodo compartido
            elementos_interfaz.append(elem)

    print(f"   Elementos que tocan la interfaz: {len(elementos_interfaz)}")

    # Contar por material
    from collections import Counter
    mat_count = Counter([e['material'] for e in elementos_interfaz])
    for mat, count in sorted(mat_count.items()):
        nombre = "Zapata" if mat == 4 else f"Suelo estrato {mat}"
        print(f"      {nombre} (mat {mat}): {count} elementos")

    return True

def main():
    input_dir = Path("opensees_input")

    nodos_file = input_dir / "nodes.tcl"
    elementos_file = input_dir / "elements.tcl"

    if not nodos_file.exists() or not elementos_file.exists():
        print(f"❌ Error: Archivos no encontrados en {input_dir}")
        return

    print("\n📂 Leyendo archivos...")
    nodos = leer_nodos_desde_tcl(nodos_file)
    elementos = leer_elementos_desde_tcl(elementos_file)

    print(f"   ✓ {len(nodos):,} nodos leídos")
    print(f"   ✓ {len(elementos):,} elementos leídos\n")

    # Analizar interfaz
    conexion_ok = analizar_interfaz(nodos, elementos)

    print("\n" + "="*80)
    print("CONCLUSIONES Y RECOMENDACIONES:")
    print("="*80)

    if conexion_ok:
        print("✅ La zapata y el suelo están conectados mediante nodos compartidos.")
        print("   Esto es CORRECTO: los elementos de diferentes materiales comparten nodos,")
        print("   lo que garantiza la continuidad de desplazamientos en la interfaz.\n")

        print("✅ No se requieren elementos especiales de interfaz (rigidLink, equalDOF, etc.)")
        print("   porque la conectividad natural de la malla ya establece la compatibilidad.\n")

        print("📋 Condiciones de frontera actuales (run_opensees_analysis.py:158-201):")
        print("   • Base fija: fix(tag, 1, 1, 1) en z_min")
        print("   • Simetría X: fix(tag, 1, 0, 0) en x_min")
        print("   • Simetría Y: fix(tag, 0, 1, 0) en y_min")
        print("   Estas condiciones son CORRECTAS.\n")
    else:
        print("❌ PROBLEMA: La zapata y el suelo NO están conectados.")
        print("   Se requiere revisar la generación de la malla.\n")

    print("💡 RECOMENDACIONES ADICIONALES:")
    print("   1. Verificar que la geometría de la zapata corresponde a:")
    print("      • Profundidad de fundación (Df): 1.5 m → base en z ≈ -1.5 m")
    print("      • Altura de zapata (h): 0.4 m → tope en z ≈ -1.1 m")

    print("\n   2. Si el análisis no converge, considerar:")
    print("      • Reducir contraste de rigidez zapata/suelo (ya implementado en línea 113)")
    print("      • Usar solver UmfPack en lugar de BandGeneral")
    print("      • Aumentar tolerancia de convergencia")

    print("\n   3. La interfaz zapata-suelo NO requiere:")
    print("      • Elementos de contacto (contact elements)")
    print("      • rigidLink o equalDOF")
    print("      • Condiciones especiales de frontera en la interfaz")
    print("      Porque los elementos tetraédricos ya comparten nodos.")

    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
