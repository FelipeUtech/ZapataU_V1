#!/usr/bin/env python3
"""
===================================================================================
SCRIPT PRINCIPAL - ANÁLISIS DE ZAPATAS CON OPENSEESPY
===================================================================================
Este script integra todo el flujo de trabajo para análisis de zapatas:
  1. Lee configuración desde config.py
  2. Genera malla según tipo especificado
  3. Crea modelo en OpenSeesPy
  4. Aplica cargas y condiciones de borde
  5. Ejecuta análisis
  6. Extrae y visualiza resultados
  7. Genera reportes

USO:
    python run_analysis.py

CONFIGURACIÓN:
    Modifica los parámetros en config.py antes de ejecutar
===================================================================================
"""

import openseespy.opensees as ops
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys

# Importar configuración y utilidades
import config
import utils

# ===================================================================================
# FUNCIÓN PRINCIPAL
# ===================================================================================

def main():
    """Función principal que ejecuta el análisis completo."""

    print("\n" + "="*80)
    print("ANÁLISIS DE ZAPATA CON OPENSEESPY - VERSIÓN INTEGRADA")
    print("="*80)
    print(f"\nFecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # -------------------------
    # 1. VALIDAR CONFIGURACIÓN
    # -------------------------
    print("\n" + "="*80)
    print("PASO 1: VALIDANDO CONFIGURACIÓN")
    print("="*80)

    config.imprimir_resumen()

    if not config.validar_configuracion():
        print("\n❌ Errores en la configuración. Por favor corrige config.py")
        sys.exit(1)

    # -------------------------
    # 2. PREPARAR PARÁMETROS
    # -------------------------
    print("\n" + "="*80)
    print("PASO 2: PREPARANDO MODELO")
    print("="*80)

    # Extraer parámetros
    zapata = config.ZAPATA
    dominio_cfg = config.DOMINIO
    malla_cfg = config.MALLA
    mat_suelo = config.MATERIAL_SUELO
    estratos_suelo = config.ESTRATOS_SUELO
    mat_zapata = config.MATERIAL_ZAPATA
    cargas = config.CARGAS
    salida = config.SALIDA

    # Calcular dimensiones del dominio
    usar_cuarto = dominio_cfg['usar_cuarto_modelo']
    factor = dominio_cfg['factor_horizontal']

    if usar_cuarto:
        # Modelo 1/4
        Lx = factor * zapata['B'] / 2.0
        Ly = factor * zapata['L'] / 2.0
        B_modelo = zapata['B'] / 2.0
        L_modelo = zapata['L'] / 2.0
        print(f"✓ Usando modelo 1/4 con simetría")
        print(f"  Dominio 1/4: {Lx}m × {Ly}m × {dominio_cfg['profundidad']}m")
    else:
        # Modelo completo
        Lx = factor * zapata['B']
        Ly = factor * zapata['L']
        B_modelo = zapata['B']
        L_modelo = zapata['L']
        print(f"✓ Usando modelo completo")
        print(f"  Dominio completo: {Lx}m × {Ly}m × {dominio_cfg['profundidad']}m")

    Lz = dominio_cfg['profundidad']

    dominio = {'Lx': Lx, 'Ly': Ly, 'Lz': Lz}
    zapata_modelo = {'B': B_modelo, 'L': L_modelo, 'h': zapata['h'],
                     'Df': zapata['Df'],  # Agregar profundidad de desplante
                     'x_min': 0.0, 'y_min': 0.0}

    # -------------------------
    # 3. GENERAR MALLA CON GMSH
    # -------------------------
    print("\n" + "="*80)
    print("PASO 3: GENERANDO MALLA CON GMSH")
    print("="*80)

    print("Ejecutando generate_mesh_quarter.py...")
    print("(Esto generará una malla tetraédrica con Gmsh)")

    import subprocess
    result = subprocess.run(
        ['python3', 'generate_mesh_quarter.py'],
        capture_output=True,
        text=True,
        timeout=300  # 5 minutos máximo
    )

    if result.returncode != 0:
        print(f"❌ Error al generar malla:")
        print(result.stderr)
        sys.exit(1)

    # Mostrar salida del generador de malla
    print(result.stdout)

    # Leer malla generada desde archivo .vtu
    import pyvista as pv
    mesh_file = "mallas/zapata_3D_cuarto.vtu"

    print(f"\nLeyendo malla desde {mesh_file}...")
    grid = pv.read(mesh_file)

    # Extraer información de la malla
    points = grid.points
    cells = grid.cells
    material_ids = grid.cell_data.get('dominio', None)

    # Contar elementos por tipo
    num_elements = grid.n_cells
    num_nodes = grid.n_points

    print(f"✓ Malla cargada:")
    print(f"  Nodos: {num_nodes:,}")
    print(f"  Elementos tetraédricos: {num_elements:,}")

    # Verificar que hay material_ids
    if material_ids is None:
        print("❌ Error: No se encontraron material_ids en la malla")
        sys.exit(1)

    # Mostrar distribución de materiales
    unique_mats = np.unique(material_ids)
    print(f"  Materiales encontrados: {unique_mats}")
    for mat_id in unique_mats:
        count = np.sum(material_ids == mat_id)
        if mat_id == len(estratos_suelo) + 1:
            print(f"    Material {mat_id} (ZAPATA): {count:,} elementos")
        else:
            print(f"    Material {mat_id} (ESTRATO {mat_id}): {count:,} elementos")

    # -------------------------
    # 4. CREAR MODELO EN OPENSEESPY
    # -------------------------
    print("\n" + "="*80)
    print("PASO 4: CREANDO MODELO EN OPENSEESPY")
    print("="*80)

    # Inicializar
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 3)
    print("✓ Modelo inicializado (3D, 3 DOF)")

    # Crear nodos desde la malla de Gmsh
    print("\nCreando nodos...")
    node_coords = {}
    for node_id, (x, y, z) in enumerate(points, start=1):
        ops.node(node_id, float(x), float(y), float(z))
        node_coords[node_id] = np.array([x, y, z])

    print(f"✓ {len(node_coords)} nodos creados")

    # Identificar nodos en superficie (z máxima)
    z_max = points[:, 2].max()
    surface_nodes = [nid for nid, coords in node_coords.items() if abs(coords[2] - z_max) < 0.01]
    print(f"✓ {len(surface_nodes)} nodos en superficie (z={z_max:.2f}m)")

    # Identificar nodos en el tope de la zapata
    Df = zapata['Df']
    h_zapata = zapata['h']
    z_tope_zapata = -Df  # Tope de zapata (fondo de excavación)
    z_base_zapata = -Df - h_zapata  # Base de zapata

    # Límites de la zapata en planta (modelo 1/4)
    # Para modelo 1/4, la zapata empieza en el origen (0, 0)
    x_min_zapata = 0.0
    x_max_zapata = B_modelo / 2
    y_min_zapata = 0.0
    y_max_zapata = L_modelo / 2

    zapata_nodes = []
    for nid, coords in node_coords.items():
        x, y, z = coords
        # Nodo está en el tope de la zapata
        if (abs(z - z_tope_zapata) < 0.1 and
            x_min_zapata <= x <= x_max_zapata and
            y_min_zapata <= y <= y_max_zapata):
            zapata_nodes.append(nid)

    print(f"✓ {len(zapata_nodes)} nodos en tope de zapata (z≈{z_tope_zapata:.2f}m)")

    # Aplicar condiciones de borde
    print("\nAplicando condiciones de borde...")

    # Fondo: empotrado (z mínima)
    z_min = points[:, 2].min()
    fixed_nodes = [nid for nid, coords in node_coords.items() if abs(coords[2] - z_min) < 0.01]
    for nid in fixed_nodes:
        ops.fix(nid, 1, 1, 1)
    print(f"  ✓ {len(fixed_nodes)} nodos fijados en fondo (z={z_min:.2f}m)")

    # Planos de simetría (modelo 1/4)
    if usar_cuarto:
        # Plano x=0: desplazamiento en X = 0
        x_min_tol = points[:, 0].min()
        x_symmetry_nodes = [nid for nid, coords in node_coords.items() if abs(coords[0] - x_min_tol) < 0.01]
        for nid in x_symmetry_nodes:
            if nid not in fixed_nodes:  # No re-aplicar si ya está fijado
                ops.fix(nid, 1, 0, 0)
        print(f"  ✓ {len(x_symmetry_nodes)} nodos en plano X=0 (simetría)")

        # Plano y=0: desplazamiento en Y = 0
        y_min_tol = points[:, 1].min()
        y_symmetry_nodes = [nid for nid, coords in node_coords.items() if abs(coords[1] - y_min_tol) < 0.01]
        for nid in y_symmetry_nodes:
            if nid not in fixed_nodes:
                ops.fix(nid, 0, 1, 0)
        print(f"  ✓ {len(y_symmetry_nodes)} nodos en plano Y=0 (simetría)")

    # Definir materiales
    print("\nDefiniendo materiales...")

    # Materiales de estratos de suelo
    for i, estrato in enumerate(estratos_suelo, 1):
        mat_tag = i
        ops.nDMaterial('ElasticIsotropic', mat_tag,
                       estrato['E'], estrato['nu'], estrato['rho'])
        print(f"✓ {estrato['nombre']} (tag={mat_tag}): E={estrato['E']/1000:.0f} MPa")

    # Material concreto (zapata)
    mat_tag_zapata = len(estratos_suelo) + 1
    ops.nDMaterial('ElasticIsotropic', mat_tag_zapata,
                   mat_zapata['E'], mat_zapata['nu'], mat_zapata['rho'])
    print(f"✓ Material concreto (tag={mat_tag_zapata}): E={mat_zapata['E']/1e6:.0f} GPa")

    # Crear elementos tetraédricos
    print("\nCreando elementos tetraédricos...")

    # Extraer conectividad de tetraedros
    # En PyVista, cells tiene formato: [n_points, p0, p1, ..., n_points, p0, p1, ...]
    element_id = 1
    cell_idx = 0
    element_counts = {mat_id: 0 for mat_id in unique_mats}

    while cell_idx < len(cells):
        n_points = cells[cell_idx]
        if n_points != 4:
            print(f"⚠️  Advertencia: Elemento con {n_points} nodos (esperado 4)")
            cell_idx += n_points + 1
            continue

        # Nodos del tetraedro (PyVista usa indexación 0-based, OpenSees usa 1-based)
        n1 = int(cells[cell_idx + 1]) + 1
        n2 = int(cells[cell_idx + 2]) + 1
        n3 = int(cells[cell_idx + 3]) + 1
        n4 = int(cells[cell_idx + 4]) + 1

        # Material del elemento
        mat_id = int(material_ids[element_id - 1])

        # Crear elemento en OpenSees
        ops.element('FourNodeTetrahedron', element_id, n1, n2, n3, n4, mat_id)

        element_counts[mat_id] += 1
        element_id += 1
        cell_idx += n_points + 1

    total_elements = element_id - 1
    print(f"✓ {total_elements:,} elementos tetraédricos creados")

    # Reportar por material
    for mat_id in sorted(element_counts.keys()):
        count = element_counts[mat_id]
        if mat_id == mat_tag_zapata:
            print(f"  Material {mat_id} (ZAPATA): {count:,} elementos")
        else:
            estrato_idx = mat_id - 1
            if 0 <= estrato_idx < len(estratos_suelo):
                print(f"  Material {mat_id} ({estratos_suelo[estrato_idx]['nombre']}): {count:,} elementos")

    # -------------------------
    # 5. APLICAR CARGAS
    # -------------------------
    print("\n" + "="*80)
    print("PASO 5: APLICANDO CARGAS")
    print("="*80)

    ops.timeSeries('Linear', 1)
    ops.pattern('Plain', 1, 1)

    # Ajustar carga si es modelo 1/4
    P_column = cargas['P_column']
    if usar_cuarto:
        P_column = P_column / 4.0
        print(f"Modelo 1/4: Carga ajustada a {P_column:.2f} kN")

    # Calcular peso propio de la zapata
    peso_zapata = 0.0
    if cargas['incluir_peso_propio']:
        # Volumen de la zapata (modelo 1/4)
        vol_zapata = (B_modelo / 2) * (L_modelo / 2) * h_zapata
        peso_zapata = vol_zapata * mat_zapata['rho'] * 9.81 / 1000.0  # kN
        print(f"Peso propio zapata: {peso_zapata:.2f} kN")

    # Carga total
    carga_total = P_column + peso_zapata

    # Distribuir carga entre nodos del tope de zapata
    if len(zapata_nodes) == 0:
        print("⚠️  Advertencia: No se encontraron nodos en el tope de la zapata")
        print("    Aplicando carga en nodos de superficie dentro de área de zapata")

        # Buscar nodos de superficie en área de zapata
        for nid in surface_nodes:
            coords = node_coords[nid]
            x, y = coords[0], coords[1]
            if (x_min_zapata <= x <= x_max_zapata and
                y_min_zapata <= y <= y_max_zapata):
                zapata_nodes.append(nid)

    if len(zapata_nodes) > 0:
        carga_por_nodo = -carga_total / len(zapata_nodes)  # Negativa (hacia abajo)

        for nid in zapata_nodes:
            ops.load(nid, 0.0, 0.0, carga_por_nodo)

        print(f"✓ Carga total aplicada: {carga_total:.2f} kN")
        print(f"  Carga columna: {P_column:.2f} kN")
        print(f"  Peso zapata: {peso_zapata:.2f} kN")
        print(f"  Nodos cargados: {len(zapata_nodes)}")
        print(f"  Carga por nodo: {carga_por_nodo:.4f} kN")
    else:
        print("❌ Error: No se pudieron identificar nodos para aplicar cargas")
        sys.exit(1)

    # Calcular presión
    area_zapata = zapata['B'] * zapata['L']
    if usar_cuarto:
        area_zapata = area_zapata / 4.0
    presion = carga_total / area_zapata
    print(f"  Presión contacto: {presion:.2f} kPa")

    # -------------------------
    # 6. EJECUTAR ANÁLISIS
    # -------------------------
    print("\n" + "="*80)
    print("PASO 6: EJECUTANDO ANÁLISIS")
    print("="*80)

    analisis_cfg = config.ANALISIS

    ops.system(analisis_cfg['solver'])
    ops.numberer(analisis_cfg['numberer'])
    ops.constraints(analisis_cfg['constraints'])
    ops.integrator('LoadControl', 1.0)
    ops.algorithm(analisis_cfg['algorithm'])
    ops.analysis(analisis_cfg['tipo'])

    print(f"Configuración:")
    print(f"  Solver: {analisis_cfg['solver']}")
    print(f"  Algorithm: {analisis_cfg['algorithm']}")

    print("\nEjecutando análisis...")
    ok = ops.analyze(1)

    if ok == 0:
        print("✓ Análisis completado exitosamente")
    else:
        print("❌ Error en el análisis")
        sys.exit(1)

    # -------------------------
    # 7. EXTRAER RESULTADOS
    # -------------------------
    print("\n" + "="*80)
    print("PASO 7: EXTRAYENDO RESULTADOS")
    print("="*80)

    # Extraer asentamientos de todos los nodos
    df_settlements = utils.extraer_asentamientos(node_coords)
    print(f"✓ {len(df_settlements)} puntos con asentamientos extraídos")

    # Estadísticas de superficie
    df_surface = df_settlements[df_settlements['Z'] == df_settlements['Z'].max()]

    s_max = df_surface['Settlement_mm'].max()
    s_min = df_surface['Settlement_mm'].min()
    s_mean = df_surface['Settlement_mm'].mean()
    s_std = df_surface['Settlement_mm'].std()
    s_diff = s_max - s_min

    print(f"\nEstadísticas de asentamientos en superficie:")
    print(f"  Máximo: {s_max:.4f} mm")
    print(f"  Mínimo: {s_min:.4f} mm")
    print(f"  Promedio: {s_mean:.4f} mm")
    print(f"  Desv. estándar: {s_std:.4f} mm")
    print(f"  Diferencial: {s_diff:.4f} mm")

    # Verificar criterios
    print("\nVerificación de criterios:")
    criterios = config.CRITERIOS

    if s_max > criterios['asentamiento_maximo_admisible']:
        print(f"  ⚠️  Asentamiento máximo {s_max:.2f} mm > {criterios['asentamiento_maximo_admisible']} mm (REVISAR)")
    else:
        print(f"  ✓ Asentamiento máximo OK ({s_max:.2f} mm < {criterios['asentamiento_maximo_admisible']} mm)")

    rel_diff = s_diff / s_max if s_max > 0 else 0
    if rel_diff > criterios['asentamiento_diferencial_admisible']:
        print(f"  ⚠️  Diferencial {rel_diff:.4f} > {criterios['asentamiento_diferencial_admisible']} (REVISAR)")
    else:
        print(f"  ✓ Asentamiento diferencial OK ({rel_diff:.4f} < {criterios['asentamiento_diferencial_admisible']})")

    # -------------------------
    # 8. GUARDAR RESULTADOS
    # -------------------------
    print("\n" + "="*80)
    print("PASO 8: GUARDANDO RESULTADOS")
    print("="*80)

    # Guardar CSV
    if salida['guardar_csv']:
        csv_file = salida['csv_settlements']
        df_settlements.to_csv(csv_file, index=False)
        print(f"✓ Asentamientos 3D guardados: {csv_file}")

        csv_surface_file = salida['csv_surface']
        df_surface.to_csv(csv_surface_file, index=False)
        print(f"✓ Asentamientos superficie guardados: {csv_surface_file}")

    # Exportar a VTU para ParaView
    print("\nGenerando archivo VTU para ParaView...")
    try:
        # Extraer desplazamientos de todos los nodos desde OpenSees
        displacements = np.zeros((len(node_coords), 3))
        settlement_mm = np.zeros(len(node_coords))

        for idx, nid in enumerate(sorted(node_coords.keys())):
            disp = ops.nodeDisp(nid)
            displacements[idx] = disp
            settlement_mm[idx] = -disp[2] * 1000.0  # Convertir a mm (negativo = asentamiento)

        # Crear copia del grid original y agregar resultados
        result_grid = grid.copy()
        result_grid.point_data['Displacement_X_m'] = displacements[:, 0]
        result_grid.point_data['Displacement_Y_m'] = displacements[:, 1]
        result_grid.point_data['Displacement_Z_m'] = displacements[:, 2]
        result_grid.point_data['Settlement_mm'] = settlement_mm
        result_grid.point_data['Displacement_Magnitude_m'] = np.linalg.norm(displacements, axis=1)

        # Guardar archivo VTU
        vtu_file = 'resultados_analysis.vtu'
        result_grid.save(vtu_file)
        print(f"✓ Archivo VTU generado: {vtu_file}")
        print(f"  Para visualizar: paraview {vtu_file}")
    except Exception as e:
        print(f"⚠️  Error al generar VTU: {e}")

    # Generar reporte
    if salida['generar_reporte']:
        # Descripción de estratos para reporte
        estratos_desc = ', '.join([f"{e['nombre']} (E={e['E']/1000:.0f} MPa, h={e['espesor']}m)"
                                   for e in estratos_suelo])

        datos_modelo = {
            'Zapata': f"{zapata['B']}m × {zapata['L']}m × {zapata['h']}m",
            'Dominio': f"{Lx}m × {Ly}m × {Lz}m",
            'Modelo': 'Cuarto con simetría' if usar_cuarto else 'Completo',
            'Malla': 'GMSH Tetraédrica',
            'Elementos': f"{len(cells)} elementos tetraédricos",
            'Nodos': len(node_coords),
            'Estratos suelo': estratos_desc,
            'Carga total': f"{carga_total:.2f} kN",
            'Presión contacto': f"{presion:.2f} kPa",
        }

        datos_resultados = {
            'Asentamiento máximo': f"{s_max:.4f} mm",
            'Asentamiento mínimo': f"{s_min:.4f} mm",
            'Asentamiento promedio': f"{s_mean:.4f} mm",
            'Desviación estándar': f"{s_std:.4f} mm",
            'Diferencial': f"{s_diff:.4f} mm",
            'Relación diferencial': f"{rel_diff:.4f}",
        }

        utils.generar_reporte(datos_modelo, datos_resultados, salida['nombre_reporte'])

    # -------------------------
    # 9. GENERAR VISUALIZACIONES
    # -------------------------
    if salida['generar_graficas']:
        print("\n" + "="*80)
        print("PASO 9: GENERANDO VISUALIZACIONES")
        print("="*80)

        # Ejecutar visualizador definitivo
        print("\nEjecutando visualizador completo...")
        try:
            import subprocess
            result = subprocess.run(['python', 'visualize_zapata.py'],
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print("✓ Visualización completa generada: modelo_quarter_isometrico_graded.png")
            else:
                print("⚠️  Error al generar visualización completa")
                if result.stderr:
                    print(f"   {result.stderr[:200]}")
        except Exception as e:
            print(f"⚠️  No se pudo ejecutar visualize_zapata.py: {e}")

    # -------------------------
    # 10. RESUMEN FINAL
    # -------------------------
    print("\n" + "="*80)
    print("ANÁLISIS COMPLETADO EXITOSAMENTE")
    print("="*80)
    print(f"\nTiempo: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nArchivos generados:")
    if salida['guardar_csv']:
        print(f"  • {salida['csv_settlements']}")
        print(f"  • {salida['csv_surface']}")
    print(f"  • resultados_analysis.vtu (ParaView)")
    if salida['generar_reporte']:
        print(f"  • {salida['nombre_reporte']}")
    if salida['generar_graficas']:
        print(f"  • modelo_quarter_isometrico_graded.png (visualización completa)")

    print("\n" + "="*80 + "\n")


# ===================================================================================
# EJECUTAR
# ===================================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Análisis interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error durante el análisis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
