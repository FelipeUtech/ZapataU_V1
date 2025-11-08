#!/usr/bin/env python3
"""
Conversor de malla GMSH a formato OpenSees.
Lee archivos .vtu o .msh generados por generate_mesh_from_config.py
y genera archivos de entrada para OpenSees.

Uso:
    python gmsh_to_opensees.py <archivo_malla.vtu> [--output-dir directorio]

El script genera:
    - nodes.tcl: Definición de nodos (node <tag> <x> <y> <z>)
    - elements.tcl: Definición de elementos tetraédricos
    - materials.tcl: Template de materiales (a completar manualmente)
    - mesh_info.txt: Información sobre la malla
"""

import sys
import argparse
import numpy as np
import pyvista as pv
from pathlib import Path


def load_mesh(mesh_file):
    """Carga malla desde archivo VTU o MSH."""
    mesh_path = Path(mesh_file)

    if not mesh_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {mesh_file}")

    print(f"📂 Cargando malla desde: {mesh_path}")

    # PyVista puede leer tanto VTU como MSH
    mesh = pv.read(str(mesh_path))

    print(f"✅ Malla cargada:")
    print(f"   Nodos: {mesh.n_points:,}")
    print(f"   Elementos: {mesh.n_cells:,}")

    return mesh


def extract_mesh_data(mesh):
    """Extrae nodos, elementos y materiales de la malla."""

    # Extraer nodos
    points = mesh.points
    num_nodes = len(points)

    # Extraer elementos (tetraedros)
    cells = []
    cell_materials = []

    # Obtener material_id si existe (campo 'dominio' o 'material_id')
    if 'dominio' in mesh.cell_data:
        materials = mesh.cell_data['dominio']
        print("✓ Usando campo 'dominio' como material_id")
    elif 'material_id' in mesh.cell_data:
        materials = mesh.cell_data['material_id']
        print("✓ Usando campo 'material_id'")
    else:
        print("⚠️  Advertencia: No se encontró 'dominio' ni 'material_id', usando material 1 para todos")
        materials = np.ones(mesh.n_cells, dtype=int)

    # Extraer conectividad de elementos
    for i in range(mesh.n_cells):
        cell = mesh.get_cell(i)

        # Verificar que sea tetraedro (4 nodos)
        if cell.n_points == 4:
            # Obtener índices de nodos (PyVista usa indexación base 0)
            node_ids = cell.point_ids
            cells.append(node_ids)
            cell_materials.append(materials[i])
        else:
            print(f"⚠️  Advertencia: Elemento {i} tiene {cell.n_points} nodos (esperado 4), ignorando")

    cells = np.array(cells)
    cell_materials = np.array(cell_materials)

    print(f"\n📊 Datos extraídos:")
    print(f"   Nodos: {num_nodes:,}")
    print(f"   Elementos tetraédricos: {len(cells):,}")
    print(f"   Materiales únicos: {np.unique(cell_materials)}")

    return points, cells, cell_materials


def write_opensees_nodes(points, output_dir):
    """Escribe archivo nodes.tcl con definición de nodos."""

    nodes_file = output_dir / "nodes.tcl"

    print(f"\n📝 Escribiendo nodos a: {nodes_file}")

    with open(nodes_file, 'w') as f:
        f.write("# ============================================\n")
        f.write("# DEFINICIÓN DE NODOS\n")
        f.write("# Generado por: gmsh_to_opensees.py\n")
        f.write("# ============================================\n")
        f.write(f"# Total de nodos: {len(points):,}\n")
        f.write("# Formato: node <tag> <x> <y> <z>\n")
        f.write("# ============================================\n\n")

        for i, point in enumerate(points):
            # OpenSees usa indexación base 1
            node_tag = i + 1
            x, y, z = point
            f.write(f"node {node_tag} {x:.6f} {y:.6f} {z:.6f}\n")

    print(f"✅ {len(points):,} nodos escritos")


def write_opensees_elements(cells, cell_materials, output_dir):
    """Escribe archivo elements.tcl con definición de elementos."""

    elements_file = output_dir / "elements.tcl"

    print(f"📝 Escribiendo elementos a: {elements_file}")

    with open(elements_file, 'w') as f:
        f.write("# ============================================\n")
        f.write("# DEFINICIÓN DE ELEMENTOS TETRAÉDRICOS\n")
        f.write("# Generado por: gmsh_to_opensees.py\n")
        f.write("# ============================================\n")
        f.write(f"# Total de elementos: {len(cells):,}\n")
        f.write("# Tipo: FourNodeTetrahedron\n")
        f.write("# Formato: element FourNodeTetrahedron <tag> <n1> <n2> <n3> <n4> <matTag>\n")
        f.write("# ============================================\n\n")

        # Agrupar por material
        unique_materials = np.unique(cell_materials)

        for mat_id in unique_materials:
            indices = np.where(cell_materials == mat_id)[0]

            f.write(f"\n# -----------------------------------------\n")
            f.write(f"# Material {mat_id} ({len(indices):,} elementos)\n")
            f.write(f"# -----------------------------------------\n\n")

            for idx in indices:
                elem_tag = idx + 1  # Base 1
                # Convertir nodos a base 1
                n1, n2, n3, n4 = cells[idx] + 1

                f.write(f"element FourNodeTetrahedron {elem_tag} {n1} {n2} {n3} {n4} {mat_id}\n")

    print(f"✅ {len(cells):,} elementos escritos")
    print(f"   Distribución por material:")
    for mat_id in unique_materials:
        count = np.sum(cell_materials == mat_id)
        print(f"     Material {mat_id}: {count:,} elementos")


def write_materials_template(cell_materials, output_dir):
    """Escribe template de archivo materials.tcl."""

    materials_file = output_dir / "materials.tcl"

    print(f"📝 Escribiendo template de materiales a: {materials_file}")

    unique_materials = np.unique(cell_materials)

    with open(materials_file, 'w') as f:
        f.write("# ============================================\n")
        f.write("# DEFINICIÓN DE MATERIALES\n")
        f.write("# Generado por: gmsh_to_opensees.py\n")
        f.write("# ============================================\n")
        f.write("# IMPORTANTE: Este es un template!\n")
        f.write("# Debes completar los parámetros según tu proyecto\n")
        f.write("# ============================================\n\n")

        for mat_id in unique_materials:
            count = np.sum(cell_materials == mat_id)

            f.write(f"\n# -----------------------------------------\n")
            f.write(f"# Material {mat_id} ({count:,} elementos)\n")
            f.write(f"# -----------------------------------------\n")

            if mat_id == 4:  # Asumiendo que 4 es zapata
                f.write("# Zapata de concreto\n")
                f.write(f"# nDMaterial ElasticIsotropic {mat_id} <E> <nu> <rho>\n")
                f.write(f"nDMaterial ElasticIsotropic {mat_id} 2.5e7 0.2 2.4\n")
            else:
                f.write(f"# Estrato de suelo {mat_id}\n")
                f.write(f"# nDMaterial PressureDependMultiYield {mat_id} <nd> <rho> <refShearModul> <refBulkModul> <cohesi> <peakShearStra> ...\n")
                f.write(f"# O usar ElasticIsotropic para análisis simplificado:\n")
                f.write(f"# nDMaterial ElasticIsotropic {mat_id} <E> <nu> <rho>\n")
                f.write(f"nDMaterial ElasticIsotropic {mat_id} 3.0e4 0.3 1.8  ;# COMPLETAR PARÁMETROS\n")

    print(f"✅ Template de materiales creado")
    print(f"⚠️  IMPORTANTE: Edita {materials_file} con los parámetros correctos!")


def write_mesh_info(points, cells, cell_materials, mesh_file, output_dir):
    """Escribe archivo de información sobre la malla."""

    info_file = output_dir / "mesh_info.txt"

    print(f"📝 Escribiendo información a: {info_file}")

    with open(info_file, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("INFORMACIÓN DE LA MALLA CONVERTIDA\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"Archivo origen: {mesh_file}\n")
        f.write(f"Fecha conversión: {Path(__file__).stat().st_mtime}\n\n")

        f.write("ESTADÍSTICAS:\n")
        f.write(f"  Número de nodos: {len(points):,}\n")
        f.write(f"  Número de elementos: {len(cells):,}\n")
        f.write(f"  Tipo de elemento: FourNodeTetrahedron\n\n")

        f.write("LÍMITES DE LA MALLA:\n")
        f.write(f"  X: [{points[:, 0].min():.3f}, {points[:, 0].max():.3f}] m\n")
        f.write(f"  Y: [{points[:, 1].min():.3f}, {points[:, 1].max():.3f}] m\n")
        f.write(f"  Z: [{points[:, 2].min():.3f}, {points[:, 2].max():.3f}] m\n\n")

        f.write("DISTRIBUCIÓN POR MATERIAL:\n")
        for mat_id in np.unique(cell_materials):
            count = np.sum(cell_materials == mat_id)
            percentage = 100.0 * count / len(cells)
            f.write(f"  Material {mat_id}: {count:,} elementos ({percentage:.1f}%)\n")

        f.write("\n" + "=" * 70 + "\n")
        f.write("ARCHIVOS GENERADOS:\n")
        f.write("=" * 70 + "\n")
        f.write("  nodes.tcl      - Definición de nodos\n")
        f.write("  elements.tcl   - Definición de elementos\n")
        f.write("  materials.tcl  - Template de materiales (EDITAR)\n")
        f.write("  mesh_info.txt  - Este archivo\n")
        f.write("\n" + "=" * 70 + "\n")
        f.write("USO EN OPENSEES:\n")
        f.write("=" * 70 + "\n")
        f.write("# En tu script .tcl principal:\n")
        f.write("source materials.tcl\n")
        f.write("source nodes.tcl\n")
        f.write("source elements.tcl\n")
        f.write("=" * 70 + "\n")

    print(f"✅ Información escrita")


def main():
    """Función principal."""

    parser = argparse.ArgumentParser(
        description="Convierte malla GMSH a formato OpenSees",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    python gmsh_to_opensees.py mallas/zapata_3D_cuarto_refined.vtu
    python gmsh_to_opensees.py mallas/zapata_3D.msh --output-dir opensees_input
        """
    )

    parser.add_argument('mesh_file', help='Archivo de malla (.vtu o .msh)')
    parser.add_argument('--output-dir', '-o', default='opensees_input',
                       help='Directorio de salida (default: opensees_input)')

    args = parser.parse_args()

    print("=" * 70)
    print("CONVERSOR GMSH → OpenSees")
    print("=" * 70 + "\n")

    try:
        # Crear directorio de salida
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        print(f"📁 Directorio de salida: {output_dir}\n")

        # Cargar malla
        mesh = load_mesh(args.mesh_file)

        # Extraer datos
        points, cells, cell_materials = extract_mesh_data(mesh)

        # Escribir archivos OpenSees
        write_opensees_nodes(points, output_dir)
        write_opensees_elements(cells, cell_materials, output_dir)
        write_materials_template(cell_materials, output_dir)
        write_mesh_info(points, cells, cell_materials, args.mesh_file, output_dir)

        print("\n" + "=" * 70)
        print("✅ CONVERSIÓN COMPLETADA")
        print("=" * 70)
        print(f"\n📂 Archivos generados en: {output_dir}/")
        print("\n⚠️  SIGUIENTE PASO:")
        print(f"   Edita {output_dir}/materials.tcl con los parámetros correctos")
        print(f"   de materiales para tu proyecto.\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
