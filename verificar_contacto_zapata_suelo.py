#!/usr/bin/env python3
"""
Verifica que la zapata y el suelo compartan nodos en la interfaz.

Este script:
1. Lee la malla VTU generada
2. Identifica elementos de zapata (material 4) y elementos de suelo (materiales 1-3)
3. Encuentra nodos en la interfaz zapata-suelo
4. Verifica que haya nodos compartidos
5. Analiza la conectividad

Uso:
    python verificar_contacto_zapata_suelo.py
"""

import numpy as np
import pyvista as pv
from pathlib import Path
import json


def cargar_configuracion():
    """Carga configuración de la malla."""
    with open('mesh_config.json', 'r') as f:
        config = json.load(f)
    return config


def cargar_malla(archivo_vtu):
    """Carga malla desde archivo VTU."""
    if not Path(archivo_vtu).exists():
        raise FileNotFoundError(f"No se encontró: {archivo_vtu}")

    mesh = pv.read(archivo_vtu)
    print(f"📂 Malla cargada: {archivo_vtu}")
    print(f"   Nodos: {mesh.n_points:,}")
    print(f"   Elementos: {mesh.n_cells:,}")

    return mesh


def analizar_elementos_por_material(mesh):
    """Agrupa elementos por material y extrae sus nodos."""

    # Obtener material_id
    if 'material_id' in mesh.cell_data:
        materials = mesh.cell_data['material_id']
    else:
        print("❌ No se encontró campo 'material_id'")
        return None

    elementos_por_material = {}
    nodos_por_material = {}

    # Agrupar elementos y nodos por material
    for i in range(mesh.n_cells):
        cell = mesh.get_cell(i)
        mat_id = materials[i]

        if mat_id not in elementos_por_material:
            elementos_por_material[mat_id] = []
            nodos_por_material[mat_id] = set()

        elementos_por_material[mat_id].append(i)

        # Agregar nodos del elemento
        for node_id in cell.point_ids:
            nodos_por_material[mat_id].add(node_id)

    # Resumen
    print("\n📊 Distribución por material:")
    for mat_id in sorted(elementos_por_material.keys()):
        n_elem = len(elementos_por_material[mat_id])
        n_nodos = len(nodos_por_material[mat_id])
        print(f"   Material {mat_id}: {n_elem:,} elementos, {n_nodos:,} nodos únicos")

    return elementos_por_material, nodos_por_material


def encontrar_interfaz_zapata_suelo(mesh, nodos_por_material, config):
    """Identifica nodos en la interfaz zapata-suelo."""

    # Identificar material de zapata (normalmente el 4)
    mat_zapata = config['footing_material']['material_id']
    materiales_suelo = [layer['material_id'] for layer in config['soil_layers']]

    print(f"\n🔍 Buscando interfaz:")
    print(f"   Material zapata: {mat_zapata}")
    print(f"   Materiales suelo: {materiales_suelo}")

    # Nodos de zapata
    nodos_zapata = nodos_por_material.get(mat_zapata, set())

    # Nodos de suelo (unión de todos los estratos)
    nodos_suelo = set()
    for mat_id in materiales_suelo:
        if mat_id in nodos_por_material:
            nodos_suelo.update(nodos_por_material[mat_id])

    # Nodos compartidos = interfaz
    nodos_interfaz = nodos_zapata.intersection(nodos_suelo)

    print(f"\n📈 Estadísticas de conectividad:")
    print(f"   Nodos de zapata: {len(nodos_zapata):,}")
    print(f"   Nodos de suelo: {len(nodos_suelo):,}")
    print(f"   Nodos compartidos (interfaz): {len(nodos_interfaz):,}")

    if len(nodos_interfaz) == 0:
        print("\n⚠️  ¡ADVERTENCIA! No hay nodos compartidos entre zapata y suelo")
        print("   Esto significa que la zapata NO está conectada al suelo")
        print("   Posible problema en la generación de malla con fragment()")
        return None, nodos_zapata, nodos_suelo

    # Analizar posición de nodos de interfaz
    coords_interfaz = mesh.points[list(nodos_interfaz)]

    print(f"\n📍 Análisis de nodos de interfaz:")
    print(f"   Límites X: [{coords_interfaz[:, 0].min():.3f}, {coords_interfaz[:, 0].max():.3f}] m")
    print(f"   Límites Y: [{coords_interfaz[:, 1].min():.3f}, {coords_interfaz[:, 1].max():.3f}] m")
    print(f"   Límites Z: [{coords_interfaz[:, 2].min():.3f}, {coords_interfaz[:, 2].max():.3f}] m")

    # Verificar que la interfaz está donde esperamos
    # La zapata está enterrada, así que la interfaz debe estar alrededor de z = -Df-tz (base)
    # y también en los laterales a z = -Df (tope)

    Df = config['geometry']['footing']['Df']
    tz = config['geometry']['footing']['tz']
    z_base_zapata = -Df - tz
    z_tope_zapata = -Df

    print(f"\n✓ Profundidades esperadas:")
    print(f"   Tope de zapata (z = -Df): {z_tope_zapata:.3f} m")
    print(f"   Base de zapata (z = -Df-tz): {z_base_zapata:.3f} m")

    # Contar nodos de interfaz por zona
    tol = 0.1
    nodos_base = np.sum(np.abs(coords_interfaz[:, 2] - z_base_zapata) < tol)
    nodos_laterales = np.sum((coords_interfaz[:, 2] > z_base_zapata + tol) &
                             (coords_interfaz[:, 2] < z_tope_zapata - tol))
    nodos_tope = np.sum(np.abs(coords_interfaz[:, 2] - z_tope_zapata) < tol)

    print(f"\n📊 Distribución de nodos de interfaz:")
    print(f"   En base (z ≈ {z_base_zapata:.1f} m): {nodos_base}")
    print(f"   En laterales: {nodos_laterales}")
    print(f"   En tope (z ≈ {z_tope_zapata:.1f} m): {nodos_tope}")

    return nodos_interfaz, nodos_zapata, nodos_suelo


def verificar_elementos_adyacentes(mesh, nodos_interfaz):
    """Verifica que los nodos de interfaz conecten elementos de zapata y suelo."""

    if nodos_interfaz is None or len(nodos_interfaz) == 0:
        return

    materials = mesh.cell_data['material_id']

    print(f"\n🔗 Verificando elementos adyacentes en interfaz...")

    # Para cada nodo de interfaz, encontrar elementos que lo contienen
    verificacion = []

    for node_id in list(nodos_interfaz)[:10]:  # Verificar primeros 10 nodos
        elementos_adyacentes = []
        materiales_adyacentes = []

        for i in range(mesh.n_cells):
            cell = mesh.get_cell(i)
            if node_id in cell.point_ids:
                elementos_adyacentes.append(i)
                materiales_adyacentes.append(materials[i])

        # Verificar si hay al menos un elemento de zapata (4) y uno de suelo (1,2,3)
        tiene_zapata = 4 in materiales_adyacentes
        tiene_suelo = any(m in [1, 2, 3] for m in materiales_adyacentes)

        if tiene_zapata and tiene_suelo:
            verificacion.append(True)
        else:
            verificacion.append(False)

    n_correctos = sum(verificacion)
    n_total = len(verificacion)

    print(f"   Nodos verificados: {n_total}")
    print(f"   Nodos con elementos de zapata Y suelo: {n_correctos}")

    if n_correctos == n_total:
        print(f"   ✅ ¡Perfecto! Los nodos de interfaz conectan zapata y suelo")
    elif n_correctos > 0:
        print(f"   ⚠️  Solo {n_correctos}/{n_total} nodos verificados conectan correctamente")
    else:
        print(f"   ❌ ¡Error! Los nodos de interfaz NO conectan zapata y suelo")


def analizar_condiciones_frontera(mesh, config):
    """Analiza las condiciones de frontera del modelo."""

    print(f"\n🔒 Analizando condiciones de frontera...")

    points = mesh.points
    tol = 1e-3

    # Límites del dominio
    x_min = points[:, 0].min()
    y_min = points[:, 1].min()
    z_min = points[:, 2].min()

    # Contar nodos en cada frontera
    nodos_base = np.sum(np.abs(points[:, 2] - z_min) < tol)
    nodos_simetria_x = np.sum(np.abs(points[:, 0] - x_min) < tol)
    nodos_simetria_y = np.sum(np.abs(points[:, 1] - y_min) < tol)

    print(f"\n   Límites del dominio:")
    print(f"      X: [{x_min:.3f}, {points[:, 0].max():.3f}] m")
    print(f"      Y: [{y_min:.3f}, {points[:, 1].max():.3f}] m")
    print(f"      Z: [{z_min:.3f}, {points[:, 2].max():.3f}] m")

    print(f"\n   Nodos en fronteras:")
    print(f"      Base (z={z_min:.1f} m): {nodos_base} nodos → Fijos (ux=uy=uz=0)")
    print(f"      Simetría X (x={x_min:.1f} m): {nodos_simetria_x} nodos → Restringidos (ux=0)")
    print(f"      Simetría Y (y={y_min:.1f} m): {nodos_simetria_y} nodos → Restringidos (uy=0)")

    # Verificar que no haya superposición problemática
    nodos_base_y_sim_x = np.sum((np.abs(points[:, 2] - z_min) < tol) &
                                 (np.abs(points[:, 0] - x_min) < tol))
    nodos_base_y_sim_y = np.sum((np.abs(points[:, 2] - z_min) < tol) &
                                 (np.abs(points[:, 1] - y_min) < tol))

    print(f"\n   Nodos en esquinas:")
    print(f"      Base ∩ Simetría X: {nodos_base_y_sim_x}")
    print(f"      Base ∩ Simetría Y: {nodos_base_y_sim_y}")
    print(f"      (Estos nodos tendrán condiciones combinadas)")


def main():
    """Función principal."""
    print("="*80)
    print("  VERIFICACIÓN DE CONTACTO ZAPATA-SUELO")
    print("="*80)

    try:
        # Cargar configuración
        config = cargar_configuracion()

        # Determinar archivo de malla
        archivo_vtu = Path("mallas") / f"{config['output']['filename']}.vtu"

        if not archivo_vtu.exists():
            # Buscar cualquier archivo VTU en mallas/
            archivos_vtu = list(Path("mallas").glob("*.vtu"))
            if archivos_vtu:
                # Usar el más reciente
                archivo_vtu = max(archivos_vtu, key=lambda p: p.stat().st_mtime)
                print(f"⚠️  Usando archivo más reciente: {archivo_vtu}")
            else:
                print(f"❌ No se encontraron archivos VTU en mallas/")
                return

        # Cargar malla
        mesh = cargar_malla(archivo_vtu)

        # Analizar elementos por material
        print("\n" + "="*80)
        print("PASO 1: ANÁLISIS POR MATERIAL")
        print("="*80)
        elementos_por_material, nodos_por_material = analizar_elementos_por_material(mesh)

        if elementos_por_material is None:
            return

        # Encontrar interfaz zapata-suelo
        print("\n" + "="*80)
        print("PASO 2: IDENTIFICACIÓN DE INTERFAZ ZAPATA-SUELO")
        print("="*80)
        nodos_interfaz, nodos_zapata, nodos_suelo = encontrar_interfaz_zapata_suelo(
            mesh, nodos_por_material, config
        )

        # Verificar elementos adyacentes
        if nodos_interfaz is not None and len(nodos_interfaz) > 0:
            print("\n" + "="*80)
            print("PASO 3: VERIFICACIÓN DE ELEMENTOS ADYACENTES")
            print("="*80)
            verificar_elementos_adyacentes(mesh, nodos_interfaz)

        # Analizar condiciones de frontera
        print("\n" + "="*80)
        print("PASO 4: CONDICIONES DE FRONTERA")
        print("="*80)
        analizar_condiciones_frontera(mesh, config)

        # Resumen final
        print("\n" + "="*80)
        print("RESUMEN DE VERIFICACIÓN")
        print("="*80)

        if nodos_interfaz is not None and len(nodos_interfaz) > 0:
            print(f"✅ La malla tiene {len(nodos_interfaz)} nodos compartidos entre zapata y suelo")
            print(f"✅ El método fragment() funcionó correctamente")
            print(f"✅ La zapata está conectada al suelo mediante nodos compartidos")
            print(f"\n💡 La conectividad es correcta para el análisis de OpenSees")
        else:
            print(f"❌ No hay nodos compartidos entre zapata y suelo")
            print(f"❌ La malla necesita ser regenerada con fragment()")
            print(f"\n⚠️  Solución:")
            print(f"   1. Verifica que generate_mesh_from_config.py use fragment()")
            print(f"   2. Regenera la malla: python generate_mesh_from_config.py")
            print(f"   3. Vuelve a convertir: python gmsh_to_opensees.py mallas/*.vtu")

        print("="*80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
