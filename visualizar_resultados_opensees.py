#!/usr/bin/env python3
"""
Visualización de resultados de OpenSees con PyVista.

Este script:
1. Lee resultados de OpenSees (desplazamientos, tensiones, deformaciones)
2. Genera visualización 3D interactiva
3. Exporta a formato VTU para ParaView
4. Muestra campos de resultados con colormaps

Uso:
    python visualizar_resultados_opensees.py [--no-interactive] [--export-only]

Opciones:
    --no-interactive: No mostrar ventana interactiva
    --export-only: Solo exportar a VTU sin visualizar
"""

import numpy as np
import sys
from pathlib import Path

try:
    import pyvista as pv
except ImportError:
    print("❌ Error: PyVista no está instalado")
    print("   Instala con: pip install pyvista")
    sys.exit(1)


def leer_nodos_desde_tcl(archivo_tcl):
    """Lee nodos desde archivo TCL."""
    nodos = {}
    print(f"📖 Leyendo nodos desde: {archivo_tcl}")

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

    print(f"✅ {len(nodos):,} nodos leídos")
    return nodos


def leer_elementos_desde_tcl(archivo_tcl):
    """Lee elementos tetraédricos desde archivo TCL."""
    elementos = []
    print(f"📖 Leyendo elementos desde: {archivo_tcl}")

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

    print(f"✅ {len(elementos):,} elementos leídos")
    return elementos


def leer_desplazamientos_csv(archivo_csv):
    """Lee desplazamientos desde archivo CSV."""
    desplazamientos = {}
    print(f"📖 Leyendo desplazamientos desde: {archivo_csv}")

    with open(archivo_csv, 'r') as f:
        for linea in f:
            linea = linea.strip()
            if linea.startswith('#') or not linea:
                continue

            partes = linea.split(',')
            if len(partes) >= 8:
                tag = int(partes[0])
                ux = float(partes[4])
                uy = float(partes[5])
                uz = float(partes[6])
                u_total = float(partes[7])
                desplazamientos[tag] = {
                    'ux': ux,
                    'uy': uy,
                    'uz': uz,
                    'u_total': u_total
                }

    print(f"✅ {len(desplazamientos):,} desplazamientos leídos")
    return desplazamientos


def leer_tensiones_csv(archivo_csv):
    """Lee tensiones desde archivo CSV si existe."""
    if not Path(archivo_csv).exists():
        print(f"⚠️  Archivo de tensiones no encontrado: {archivo_csv}")
        return None

    tensiones = {}
    print(f"📖 Leyendo tensiones desde: {archivo_csv}")

    with open(archivo_csv, 'r') as f:
        for linea in f:
            linea = linea.strip()
            if linea.startswith('#') or not linea:
                continue

            partes = linea.split(',')
            if len(partes) >= 8:
                tag = int(partes[0])
                sxx = float(partes[1])
                syy = float(partes[2])
                szz = float(partes[3])
                sxy = float(partes[4])
                syz = float(partes[5])
                szx = float(partes[6])
                von_mises = float(partes[7])
                tensiones[tag] = {
                    'sxx': sxx,
                    'syy': syy,
                    'szz': szz,
                    'sxy': sxy,
                    'syz': syz,
                    'szx': szx,
                    'von_mises': von_mises
                }

    print(f"✅ {len(tensiones):,} tensiones leídas")
    return tensiones


def crear_malla_pyvista(nodos_dict, elementos_list):
    """
    Crea malla PyVista UnstructuredGrid a partir de nodos y elementos.

    Returns:
        pv.UnstructuredGrid: Malla con geometría de tetraedros
    """
    print("\n🔨 Creando malla PyVista...")

    # Crear mapeo de tags de nodos a índices consecutivos
    node_tags = sorted(nodos_dict.keys())
    tag_to_idx = {tag: idx for idx, tag in enumerate(node_tags)}

    # Array de puntos (coordenadas de nodos)
    points = np.array([nodos_dict[tag] for tag in node_tags])
    n_points = len(points)

    # Crear conectividad de celdas para PyVista
    # Formato: [n_nodes, node0, node1, ..., n_nodes, node0, node1, ...]
    cells = []
    cell_types = []

    for elem in elementos_list:
        # Número de nodos por elemento (4 para tetraedro)
        cells.append(4)
        # Índices de nodos (convertir tags a índices)
        for node_tag in elem['nodos']:
            cells.append(tag_to_idx[node_tag])

        # Tipo de celda: 10 = VTK_TETRA
        cell_types.append(10)

    cells = np.array(cells)
    cell_types = np.array(cell_types)

    # Crear UnstructuredGrid
    mesh = pv.UnstructuredGrid(cells, cell_types, points)

    # Agregar IDs de material como campo de celda
    material_ids = np.array([elem['material'] for elem in elementos_list])
    mesh.cell_data['Material_ID'] = material_ids

    print(f"✅ Malla creada: {n_points:,} puntos, {len(elementos_list):,} celdas (tetraedros)")

    return mesh, tag_to_idx


def mapear_desplazamientos(mesh, tag_to_idx, desplazamientos_dict):
    """Mapea desplazamientos a la malla como campos de puntos."""
    print("📊 Mapeando desplazamientos...")

    n_points = mesh.n_points

    # Arrays para desplazamientos
    disp_vector = np.zeros((n_points, 3))
    disp_magnitude = np.zeros(n_points)

    # Mapear desplazamientos
    for tag, idx in tag_to_idx.items():
        if tag in desplazamientos_dict:
            disp = desplazamientos_dict[tag]
            disp_vector[idx] = [disp['ux'], disp['uy'], disp['uz']]
            disp_magnitude[idx] = disp['u_total']

    # Agregar a la malla
    mesh.point_data['Displacement'] = disp_vector
    mesh.point_data['Displacement_Magnitude'] = disp_magnitude

    # Componentes individuales
    mesh.point_data['Ux'] = disp_vector[:, 0]
    mesh.point_data['Uy'] = disp_vector[:, 1]
    mesh.point_data['Uz'] = disp_vector[:, 2]

    print(f"✅ Desplazamientos mapeados")
    print(f"   Magnitud máxima: {disp_magnitude.max()*1000:.3f} mm")


def mapear_tensiones(mesh, tensiones_dict, elementos_list, tag_to_idx):
    """Mapea tensiones a la malla como campos de celda."""
    if tensiones_dict is None:
        return

    print("📊 Mapeando tensiones...")

    n_cells = mesh.n_cells

    # Arrays para tensiones (campos de celda)
    sxx = np.zeros(n_cells)
    syy = np.zeros(n_cells)
    szz = np.zeros(n_cells)
    sxy = np.zeros(n_cells)
    syz = np.zeros(n_cells)
    szx = np.zeros(n_cells)
    von_mises = np.zeros(n_cells)

    # Mapear tensiones
    for i, elem in enumerate(elementos_list):
        elem_tag = elem['tag']
        if elem_tag in tensiones_dict:
            tens = tensiones_dict[elem_tag]
            sxx[i] = tens['sxx']
            syy[i] = tens['syy']
            szz[i] = tens['szz']
            sxy[i] = tens['sxy']
            syz[i] = tens['syz']
            szx[i] = tens['szx']
            von_mises[i] = tens['von_mises']

    # Agregar a la malla
    mesh.cell_data['Stress_XX'] = sxx
    mesh.cell_data['Stress_YY'] = syy
    mesh.cell_data['Stress_ZZ'] = szz
    mesh.cell_data['Stress_XY'] = sxy
    mesh.cell_data['Stress_YZ'] = syz
    mesh.cell_data['Stress_ZX'] = szx
    mesh.cell_data['Von_Mises_Stress'] = von_mises

    print(f"✅ Tensiones mapeadas")
    print(f"   Tensión de von Mises máxima: {von_mises.max():.2f} kPa")


def exportar_vtu(mesh, output_file):
    """Exporta malla a formato VTU para ParaView."""
    print(f"\n💾 Exportando a VTU: {output_file}")
    mesh.save(output_file)
    print(f"✅ Archivo VTU guardado: {output_file}")


def visualizar_interactivo(mesh, escala_deformacion=1.0):
    """
    Visualiza malla de forma interactiva.

    Args:
        mesh: Malla PyVista
        escala_deformacion: Factor de escala para deformaciones
    """
    print("\n🎨 Iniciando visualización interactiva...")

    # Crear plotter
    plotter = pv.Plotter()
    plotter.add_text("Resultados OpenSees - Zapata 3D", font_size=12)

    # Determinar qué campo mostrar
    if 'Uz' in mesh.point_data:
        scalar_field = 'Uz'
        cmap = 'coolwarm'
        title = 'Desplazamiento Vertical (Uz) [m]'
    elif 'Displacement_Magnitude' in mesh.point_data:
        scalar_field = 'Displacement_Magnitude'
        cmap = 'viridis'
        title = 'Magnitud de Desplazamiento [m]'
    else:
        scalar_field = None
        cmap = 'viridis'
        title = 'Malla'

    # Crear malla deformada si hay desplazamientos
    if 'Displacement' in mesh.point_data:
        mesh_deformed = mesh.copy()
        mesh_deformed.points += mesh_deformed.point_data['Displacement'] * escala_deformacion
        print(f"   Escala de deformación: {escala_deformacion}x")
        mesh_to_plot = mesh_deformed
    else:
        mesh_to_plot = mesh

    # Agregar malla al plotter
    plotter.add_mesh(
        mesh_to_plot,
        scalars=scalar_field,
        cmap=cmap,
        show_edges=True,
        scalar_bar_args={'title': title, 'vertical': True}
    )

    # Configurar cámara
    plotter.camera_position = 'iso'
    plotter.add_axes()
    plotter.show_grid()

    print("✅ Ventana de visualización abierta")
    print("\nControles:")
    print("   - Click izquierdo + arrastrar: Rotar")
    print("   - Scroll: Zoom")
    print("   - Click derecho + arrastrar: Pan")
    print("   - 'q': Cerrar ventana")

    # Mostrar
    plotter.show()


def main():
    """Función principal."""
    print("="*80)
    print("  VISUALIZACIÓN DE RESULTADOS OPENSEES CON PYVISTA")
    print("="*80)

    # Argumentos de línea de comandos
    import argparse
    parser = argparse.ArgumentParser(description='Visualizar resultados de OpenSees')
    parser.add_argument('--no-interactive', action='store_true',
                       help='No mostrar ventana interactiva')
    parser.add_argument('--export-only', action='store_true',
                       help='Solo exportar a VTU sin visualizar')
    parser.add_argument('--scale', type=float, default=100.0,
                       help='Factor de escala para deformaciones (default: 100)')
    args = parser.parse_args()

    # Directorios
    input_dir = Path("opensees_input")
    results_dir = Path("resultados_opensees")
    output_dir = Path("resultados_opensees")

    if not input_dir.exists():
        print(f"❌ Error: Directorio {input_dir} no encontrado")
        sys.exit(1)

    if not results_dir.exists():
        print(f"❌ Error: Directorio {results_dir} no encontrado")
        print("   Ejecuta primero: python run_opensees_analysis.py")
        sys.exit(1)

    # Archivos de entrada
    nodos_file = input_dir / "nodes.tcl"
    elementos_file = input_dir / "elements.tcl"
    desplazamientos_file = results_dir / "desplazamientos.csv"
    tensiones_file = results_dir / "tensiones.csv"

    try:
        # 1. Leer malla
        print("\n" + "="*80)
        print("PASO 1: LECTURA DE MALLA")
        print("="*80)
        nodos = leer_nodos_desde_tcl(nodos_file)
        elementos = leer_elementos_desde_tcl(elementos_file)

        # 2. Leer resultados
        print("\n" + "="*80)
        print("PASO 2: LECTURA DE RESULTADOS")
        print("="*80)
        desplazamientos = leer_desplazamientos_csv(desplazamientos_file)
        tensiones = leer_tensiones_csv(tensiones_file)

        # 3. Crear malla PyVista
        print("\n" + "="*80)
        print("PASO 3: CREACIÓN DE MALLA PYVISTA")
        print("="*80)
        mesh, tag_to_idx = crear_malla_pyvista(nodos, elementos)

        # 4. Mapear resultados
        print("\n" + "="*80)
        print("PASO 4: MAPEO DE RESULTADOS")
        print("="*80)
        mapear_desplazamientos(mesh, tag_to_idx, desplazamientos)
        mapear_tensiones(mesh, tensiones, elementos, tag_to_idx)

        # 5. Exportar a VTU
        print("\n" + "="*80)
        print("PASO 5: EXPORTACIÓN A VTU")
        print("="*80)
        vtu_file = output_dir / "resultados_opensees.vtu"
        exportar_vtu(mesh, str(vtu_file))

        # 6. Visualización interactiva
        if not args.export_only and not args.no_interactive:
            print("\n" + "="*80)
            print("PASO 6: VISUALIZACIÓN INTERACTIVA")
            print("="*80)
            visualizar_interactivo(mesh, escala_deformacion=args.scale)

        # Resumen final
        print("\n" + "="*80)
        print("✅ VISUALIZACIÓN COMPLETADA")
        print("="*80)
        print(f"\n📂 Archivos generados:")
        print(f"   - {vtu_file}")
        print(f"\n💡 Para abrir en ParaView:")
        print(f"   paraview {vtu_file}")
        print("\n🎨 Campos disponibles:")
        print("   Puntos (nodos):")
        print("      - Displacement (vector)")
        print("      - Displacement_Magnitude")
        print("      - Ux, Uy, Uz (componentes)")
        if tensiones:
            print("   Celdas (elementos):")
            print("      - Von_Mises_Stress")
            print("      - Stress_XX, Stress_YY, Stress_ZZ")
            print("      - Stress_XY, Stress_YZ, Stress_ZX")
        print("      - Material_ID")
        print("\n" + "="*80)

    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
