#!/usr/bin/env python3
"""
===================================================================================
ESTUDIO DE CONVERGENCIA AUTOMÁTICO
===================================================================================
Este script realiza un estudio de convergencia de malla automático:

METODOLOGÍA:
  1. Ejecuta análisis con mallas progresivamente más finas
  2. Compara resultados entre refinamientos sucesivos
  3. Determina cuando la solución ha convergido
  4. Genera gráficas de convergencia

CRITERIO DE CONVERGENCIA:
  Diferencia relativa entre mallas < 2% (configurable)

USO:
    python convergence_study.py
===================================================================================
"""

import openseespy.opensees as ops
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import copy

# Importar módulos
import config
import utils

# ===================================================================================
# CONFIGURACIÓN DEL ESTUDIO
# ===================================================================================

# Niveles de refinamiento a probar
MALLA_NIVELES = [
    {'nombre': 'Gruesa', 'dx_min': 0.5, 'ratio': 1.2},
    {'nombre': 'Media', 'dx_min': 0.3, 'ratio': 1.15},
    {'nombre': 'Fina', 'dx_min': 0.2, 'ratio': 1.12},
    {'nombre': 'Muy Fina', 'dx_min': 0.15, 'ratio': 1.1},
    {'nombre': 'Extra Fina', 'dx_min': 0.12, 'ratio': 1.08},
]

# Criterio de convergencia (diferencia relativa)
TOLERANCIA_CONVERGENCIA = 0.02  # 2%

# ===================================================================================
# FUNCIONES
# ===================================================================================

def ejecutar_analisis_convergencia(nivel_malla):
    """
    Ejecuta análisis con un nivel de malla específico.

    Parameters:
    -----------
    nivel_malla : dict
        Configuración del nivel de malla

    Returns:
    --------
    resultados : dict
        Resultados del análisis
    """
    # Configurar malla
    config.MALLA['tipo'] = 'graded'
    config.MALLA['graded']['dx_min'] = nivel_malla['dx_min']
    config.MALLA['graded']['ratio'] = nivel_malla['ratio']

    # Desactivar salidas
    config.SALIDA['generar_graficas'] = False
    config.SALIDA['guardar_csv'] = False
    config.SALIDA['generar_reporte'] = False

    # Preparar parámetros
    zapata = config.ZAPATA
    dominio_cfg = config.DOMINIO
    malla_cfg = config.MALLA
    mat_suelo = config.MATERIAL_SUELO
    mat_zapata = config.MATERIAL_ZAPATA
    cargas = config.CARGAS

    usar_cuarto = dominio_cfg['usar_cuarto_modelo']
    factor = dominio_cfg['factor_horizontal']

    if usar_cuarto:
        Lx = factor * zapata['B'] / 2.0
        Ly = factor * zapata['L'] / 2.0
        B_modelo = zapata['B'] / 2.0
        L_modelo = zapata['L'] / 2.0
    else:
        Lx = factor * zapata['B']
        Ly = factor * zapata['L']
        B_modelo = zapata['B']
        L_modelo = zapata['L']

    Lz = dominio_cfg['profundidad']
    dominio = {'Lx': Lx, 'Ly': Ly, 'Lz': Lz}
    zapata_modelo = {'B': B_modelo, 'L': L_modelo, 'h': zapata['h'],
                     'x_min': 0.0, 'y_min': 0.0}

    # Generar malla
    params = malla_cfg['graded']
    x_coords, y_coords, z_coords = utils.generar_malla_gradual(dominio, zapata_modelo, params)

    nx = len(x_coords) - 1
    ny = len(y_coords) - 1
    nz = len(z_coords) - 1

    # Crear modelo
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 3)

    node_coords, surface_nodes = utils.crear_nodos(x_coords, y_coords, z_coords)
    zapata_nodes = utils.identificar_nodos_zapata(surface_nodes, node_coords, zapata_modelo)

    nodes_per_layer = (nx + 1) * (ny + 1)
    utils.aplicar_condiciones_borde(nz + 1, nodes_per_layer, nx, ny, usar_cuarto)

    ops.nDMaterial('ElasticIsotropic', 1, mat_suelo['E'], mat_suelo['nu'], mat_suelo['rho'])

    n_elements = utils.crear_elementos(nx, ny, nz, nodes_per_layer, mat_tag=1)

    # Aplicar cargas
    ops.timeSeries('Linear', 1)
    ops.pattern('Plain', 1, 1)

    P_column = cargas['P_column']
    if usar_cuarto:
        P_column = P_column / 4.0

    carga_total = utils.aplicar_cargas(zapata_nodes, P_column, zapata, mat_zapata,
                                       cargas['incluir_peso_propio'])

    # Ejecutar análisis
    analisis_cfg = config.ANALISIS
    ops.system(analisis_cfg['solver'])
    ops.numberer(analisis_cfg['numberer'])
    ops.constraints(analisis_cfg['constraints'])
    ops.integrator('LoadControl', 1.0)
    ops.algorithm(analisis_cfg['algorithm'])
    ops.analysis(analisis_cfg['tipo'])

    ok = ops.analyze(1)

    if ok != 0:
        return None

    # Extraer resultados
    df_settlements = utils.extraer_asentamientos(node_coords)
    df_surface = df_settlements[df_settlements['Z'] == df_settlements['Z'].max()]

    s_max = df_surface['Settlement_mm'].max()
    s_min = df_surface['Settlement_mm'].min()
    s_mean = df_surface['Settlement_mm'].mean()

    # Asentamiento en centro
    s_center = df_surface[
        (df_surface['X'] <= zapata_modelo['B'] / 2) &
        (df_surface['Y'] <= zapata_modelo['L'] / 2)
    ]['Settlement_mm'].max()

    resultados = {
        'nombre': nivel_malla['nombre'],
        'dx_min': nivel_malla['dx_min'],
        'n_elementos': n_elements,
        'n_nodos': len(node_coords),
        'asentamiento_maximo': s_max,
        'asentamiento_minimo': s_min,
        'asentamiento_promedio': s_mean,
        'asentamiento_centro': s_center,
    }

    return resultados


def calcular_diferencia_relativa(val1, val2):
    """Calcula diferencia relativa entre dos valores."""
    if val2 == 0:
        return float('inf')
    return abs((val1 - val2) / val2)


def ejecutar_estudio_convergencia():
    """
    Ejecuta el estudio completo de convergencia.

    Returns:
    --------
    resultados_df : pd.DataFrame
        Resultados de convergencia
    convergido : bool
        True si la solución convergió
    """
    print("\n" + "="*80)
    print("ESTUDIO DE CONVERGENCIA DE MALLA")
    print("="*80)
    print(f"Niveles a probar: {len(MALLA_NIVELES)}")
    print(f"Criterio: diferencia relativa < {TOLERANCIA_CONVERGENCIA*100}%")
    print("="*80 + "\n")

    resultados_lista = []
    resultado_anterior = None
    convergido = False

    for i, nivel in enumerate(MALLA_NIVELES, 1):
        print(f"\nNivel {i}/{len(MALLA_NIVELES)}: {nivel['nombre']} (dx_min={nivel['dx_min']}m)")
        print("-" * 60)

        try:
            resultado = ejecutar_analisis_convergencia(nivel)

            if resultado is None:
                print(f"  ✗ Análisis falló")
                continue

            print(f"  Elementos: {resultado['n_elementos']}")
            print(f"  Nodos: {resultado['n_nodos']}")
            print(f"  Asentamiento máximo: {resultado['asentamiento_maximo']:.4f} mm")
            print(f"  Asentamiento centro: {resultado['asentamiento_centro']:.4f} mm")

            # Calcular diferencia con resultado anterior
            if resultado_anterior is not None:
                diff_max = calcular_diferencia_relativa(
                    resultado['asentamiento_maximo'],
                    resultado_anterior['asentamiento_maximo']
                )
                diff_center = calcular_diferencia_relativa(
                    resultado['asentamiento_centro'],
                    resultado_anterior['asentamiento_centro']
                )

                resultado['diff_max'] = diff_max * 100  # en porcentaje
                resultado['diff_center'] = diff_center * 100

                print(f"  Diferencia máximo: {diff_max*100:.2f}%")
                print(f"  Diferencia centro: {diff_center*100:.2f}%")

                # Verificar convergencia
                if diff_max < TOLERANCIA_CONVERGENCIA and diff_center < TOLERANCIA_CONVERGENCIA:
                    print(f"  ✓ ¡CONVERGIDO!")
                    convergido = True
                    resultados_lista.append(resultado)
                    break
            else:
                resultado['diff_max'] = np.nan
                resultado['diff_center'] = np.nan

            resultados_lista.append(resultado)
            resultado_anterior = resultado

        except Exception as e:
            print(f"  ✗ Error: {e}")

    resultados_df = pd.DataFrame(resultados_lista)

    return resultados_df, convergido


def plot_convergencia(resultados_df, archivo='convergence_plot.png'):
    """
    Genera gráficas de convergencia.

    Parameters:
    -----------
    resultados_df : pd.DataFrame
        Resultados del estudio
    archivo : str
        Nombre del archivo de salida
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Estudio de Convergencia de Malla', fontsize=14, fontweight='bold')

    # 1. Asentamiento vs número de elementos
    ax = axes[0, 0]
    ax.plot(resultados_df['n_elementos'], resultados_df['asentamiento_maximo'],
            'o-', linewidth=2, markersize=8, color='red', label='Máximo')
    ax.plot(resultados_df['n_elementos'], resultados_df['asentamiento_centro'],
            's-', linewidth=2, markersize=8, color='blue', label='Centro')
    ax.set_xlabel('Número de Elementos', fontsize=11)
    ax.set_ylabel('Asentamiento (mm)', fontsize=11)
    ax.set_title('Asentamiento vs Refinamiento', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Diferencia relativa vs refinamiento
    ax = axes[0, 1]
    if not resultados_df['diff_max'].isna().all():
        ax.plot(range(2, len(resultados_df)+1), resultados_df['diff_max'].iloc[1:],
                'o-', linewidth=2, markersize=8, color='green', label='Máximo')
        ax.plot(range(2, len(resultados_df)+1), resultados_df['diff_center'].iloc[1:],
                's-', linewidth=2, markersize=8, color='orange', label='Centro')
        ax.axhline(y=TOLERANCIA_CONVERGENCIA*100, color='red', linestyle='--',
                  linewidth=2, label=f'Criterio ({TOLERANCIA_CONVERGENCIA*100}%)')
        ax.set_xlabel('Nivel de Malla', fontsize=11)
        ax.set_ylabel('Diferencia Relativa (%)', fontsize=11)
        ax.set_title('Convergencia de la Solución', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)

    # 3. dx_min vs asentamiento
    ax = axes[1, 0]
    ax.plot(resultados_df['dx_min'], resultados_df['asentamiento_maximo'],
            'o-', linewidth=2, markersize=8, color='purple')
    ax.set_xlabel('Tamaño Mínimo de Elemento dx_min (m)', fontsize=11)
    ax.set_ylabel('Asentamiento Máximo (mm)', fontsize=11)
    ax.set_title('Asentamiento vs Tamaño de Elemento', fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.invert_xaxis()  # Más fino a la derecha

    # 4. Tabla de resultados
    ax = axes[1, 1]
    ax.axis('off')

    tabla_data = [['Nivel', 'Elementos', 'Asent. (mm)', 'Diff (%)']]

    for _, row in resultados_df.iterrows():
        diff_str = f"{row['diff_max']:.2f}" if not np.isnan(row['diff_max']) else '-'
        tabla_data.append([
            row['nombre'][:10],
            f"{row['n_elementos']:.0f}",
            f"{row['asentamiento_maximo']:.2f}",
            diff_str
        ])

    tabla = ax.table(cellText=tabla_data, cellLoc='center', loc='center',
                    colWidths=[0.3, 0.25, 0.25, 0.2])
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(9)
    tabla.scale(1, 1.5)

    # Estilo encabezado
    for i in range(4):
        tabla[(0, i)].set_facecolor('#4CAF50')
        tabla[(0, i)].set_text_props(weight='bold', color='white')

    ax.set_title('Tabla de Resultados', fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(archivo, dpi=300, bbox_inches='tight')
    print(f"\n✓ Gráfica guardada: {archivo}")
    plt.close()


# ===================================================================================
# FUNCIÓN PRINCIPAL
# ===================================================================================

def main():
    """Función principal."""

    print("\n" + "="*80)
    print("ESTUDIO DE CONVERGENCIA AUTOMÁTICO")
    print("="*80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Ejecutar estudio
    resultados_df, convergido = ejecutar_estudio_convergencia()

    if len(resultados_df) == 0:
        print("\n❌ No se obtuvieron resultados")
        sys.exit(1)

    # Guardar resultados
    csv_file = 'convergence_results.csv'
    resultados_df.to_csv(csv_file, index=False)
    print(f"\n✓ Resultados guardados: {csv_file}")

    # Generar gráficas
    print("\nGenerando gráficas...")
    plot_convergencia(resultados_df)

    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DEL ESTUDIO")
    print("="*80)
    print(resultados_df.to_string(index=False))

    print("\n" + "="*80)
    if convergido:
        print("✅ SOLUCIÓN CONVERGIDA")
        print(f"Malla recomendada: {resultados_df.iloc[-1]['nombre']}")
        print(f"  dx_min = {resultados_df.iloc[-1]['dx_min']}m")
        print(f"  Elementos: {resultados_df.iloc[-1]['n_elementos']:.0f}")
        print(f"  Asentamiento máximo: {resultados_df.iloc[-1]['asentamiento_maximo']:.4f} mm")
    else:
        print("⚠️  SOLUCIÓN NO CONVERGIÓ COMPLETAMENTE")
        print("Recomendaciones:")
        print("  • Agregar niveles de malla más finos")
        print("  • Verificar parámetros del modelo")
        print("  • Considerar aumentar dominio")

    print("="*80 + "\n")


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
