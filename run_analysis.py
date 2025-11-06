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
                     'x_min': 0.0, 'y_min': 0.0}

    # -------------------------
    # 3. GENERAR MALLA
    # -------------------------
    print("\n" + "="*80)
    print("PASO 3: GENERANDO MALLA")
    print("="*80)

    tipo_malla = malla_cfg['tipo']
    print(f"Tipo de malla: {tipo_malla}")

    if tipo_malla == 'uniform':
        # Malla uniforme
        params = malla_cfg['uniform']
        nx = int(Lx / params['dx'])
        ny = int(Ly / params['dy'])
        nz = int(Lz / params['dz'])

        x_coords, y_coords, z_coords = utils.generar_malla_uniforme(dominio, nx, ny, nz)

    elif tipo_malla == 'refined':
        # Malla refinada
        params = malla_cfg['refined']
        x_coords, y_coords, z_coords = utils.generar_malla_refinada(
            dominio, zapata_modelo, params)

        nx = len(x_coords) - 1
        ny = len(y_coords) - 1
        nz = len(z_coords) - 1

    elif tipo_malla == 'graded':
        # Malla gradual
        params = malla_cfg['graded']
        x_coords, y_coords, z_coords = utils.generar_malla_gradual(
            dominio, zapata_modelo, params)

        nx = len(x_coords) - 1
        ny = len(y_coords) - 1
        nz = len(z_coords) - 1

    else:
        print(f"❌ Tipo de malla '{tipo_malla}' no reconocido")
        sys.exit(1)

    print(f"✓ Malla generada:")
    print(f"  Elementos: {nx} × {ny} × {nz} = {nx*ny*nz}")
    print(f"  Nodos: {len(x_coords)} × {len(y_coords)} × {len(z_coords)} = {len(x_coords)*len(y_coords)*len(z_coords)}")

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

    # Crear nodos
    print("\nCreando nodos...")
    node_coords, surface_nodes = utils.crear_nodos(x_coords, y_coords, z_coords)
    print(f"✓ {len(node_coords)} nodos creados")
    print(f"✓ {len(surface_nodes)} nodos en superficie")

    # Identificar nodos en el tope de la zapata (z = h_zapata)
    # Las cargas se aplican en z=h_zapata (no en z=0)
    h_zapata = zapata['h']
    zapata_nodes = utils.identificar_nodos_en_cota(node_coords, h_zapata, zapata_modelo, tolerancia=0.05)
    print(f"✓ {len(zapata_nodes)} nodos en tope de zapata (z={h_zapata}m)")

    # Aplicar condiciones de borde
    print("\nAplicando condiciones de borde...")
    nodes_per_layer = (nx + 1) * (ny + 1)
    utils.aplicar_condiciones_borde(nz + 1, nodes_per_layer, nx, ny, usar_cuarto)
    print("✓ Condiciones de borde aplicadas")

    # Definir materiales
    print("\nDefiniendo materiales...")

    # Material 1: Suelo
    ops.nDMaterial('ElasticIsotropic', 1,
                   mat_suelo['E'], mat_suelo['nu'], mat_suelo['rho'])
    print(f"✓ Material suelo (tag=1): E={mat_suelo['E']} kPa, ν={mat_suelo['nu']}")

    # Material 2: Concreto (zapata)
    ops.nDMaterial('ElasticIsotropic', 2,
                   mat_zapata['E'], mat_zapata['nu'], mat_zapata['rho'])
    print(f"✓ Material concreto (tag=2): E={mat_zapata['E']} kPa, ν={mat_zapata['nu']}")

    # Crear elementos de suelo y zapata
    print("\nCreando elementos...")
    n_elements_suelo, n_elements_zapata = utils.crear_elementos_con_zapata(
        nx, ny, nz, nodes_per_layer, x_coords, y_coords, z_coords,
        zapata_modelo, mat_tag_suelo=1, mat_tag_zapata=2
    )
    print(f"✓ {n_elements_suelo} elementos de suelo creados")
    print(f"✓ {n_elements_zapata} elementos de zapata rígida creados")
    print(f"✓ Total: {n_elements_suelo + n_elements_zapata} elementos")

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

    carga_total = utils.aplicar_cargas(
        zapata_nodes, P_column, zapata, mat_zapata,
        cargas['incluir_peso_propio']
    )

    print(f"✓ Carga total aplicada: {carga_total:.2f} kN")
    print(f"  Carga columna: {P_column:.2f} kN")
    print(f"  Peso zapata: {carga_total - P_column:.2f} kN")
    print(f"  Nodos cargados: {len(zapata_nodes)}")

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

    # Generar reporte
    if salida['generar_reporte']:
        datos_modelo = {
            'Zapata': f"{zapata['B']}m × {zapata['L']}m × {zapata['h']}m",
            'Dominio': f"{Lx}m × {Ly}m × {Lz}m",
            'Modelo': 'Cuarto con simetría' if usar_cuarto else 'Completo',
            'Malla': tipo_malla,
            'Elementos': f"{nx} × {ny} × {nz} = {n_elements_suelo + n_elements_zapata}",
            'Nodos': len(node_coords),
            'Material suelo': f"E={mat_suelo['E']} kPa, ν={mat_suelo['nu']}",
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
