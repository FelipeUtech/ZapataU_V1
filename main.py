#!/usr/bin/env python3
"""
Programa Principal - Simulación de Ensayo de Carga de Zapata
=============================================================

Este programa simula un ensayo de carga de una zapata empotrada en un
suelo estratificado con comportamiento no lineal usando OpenSeesPy.

Autor: Claude AI
Fecha: 2025
"""

import sys
import time
import argparse
from config import *
from model_builder import ModelBuilder
from load_test_analyzer import LoadTestAnalyzer
from post_processor import PostProcessor

def print_header():
    """Imprime encabezado del programa"""
    print("\n" + "="*75)
    print(" "*15 + "SIMULACIÓN DE ENSAYO DE CARGA DE ZAPATA")
    print(" "*25 + "OpenSeesPy 3D FEM")
    print("="*75)
    print("\nPrograma para simular ensayos de carga en zapatas empotradas")
    print("en suelos estratificados con comportamiento no lineal.\n")

def print_footer(elapsed_time):
    """Imprime pie de página con tiempo de ejecución"""
    print("\n" + "="*75)
    print(f"{'SIMULACIÓN COMPLETADA EXITOSAMENTE':^75}")
    print(f"{'Tiempo de ejecución: ' + f'{elapsed_time:.2f}' + ' segundos':^75}")
    print("="*75 + "\n")

def run_simulation(show_plots=True, export_results=True):
    """
    Ejecuta la simulación completa

    Parameters:
    -----------
    show_plots : bool
        Si True, muestra las gráficas
    export_results : bool
        Si True, exporta resultados a archivos

    Returns:
    --------
    dict : Diccionario con resultados del análisis
    """
    start_time = time.time()

    try:
        # 1. Mostrar configuración
        print_header()
        print_configuration()

        # 2. Construir modelo
        print("\n" + "="*75)
        print("ETAPA 1: CONSTRUCCIÓN DEL MODELO")
        print("="*75)

        builder = ModelBuilder()
        builder.build_model()

        if export_results:
            builder.export_model_info('results/model_info.txt')

        # 3. Ejecutar ensayo de carga
        print("\n" + "="*75)
        print("ETAPA 2: SIMULACIÓN DEL ENSAYO DE CARGA")
        print("="*75)

        analyzer = LoadTestAnalyzer(builder)
        results = analyzer.run_load_test()

        # 4. Post-procesamiento
        print("\n" + "="*75)
        print("ETAPA 3: POST-PROCESAMIENTO Y VISUALIZACIÓN")
        print("="*75)

        post = PostProcessor(analyzer, output_dir='results')

        if export_results:
            post.generate_all_plots()
            post.export_csv_results()

        # Tiempo de ejecución
        elapsed_time = time.time() - start_time
        print_footer(elapsed_time)

        return results

    except Exception as e:
        print(f"\n❌ ERROR durante la simulación: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Simulación de ensayo de carga de zapata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py                    # Ejecuta simulación completa
  python main.py --no-plots         # Sin mostrar gráficos
  python main.py --no-export        # Sin exportar resultados
  python main.py --config           # Muestra configuración y sale

Para modificar los parámetros, edita el archivo config.py
        """
    )

    parser.add_argument('--no-plots', action='store_true',
                       help='No mostrar gráficos')
    parser.add_argument('--no-export', action='store_true',
                       help='No exportar resultados a archivos')
    parser.add_argument('--config', action='store_true',
                       help='Mostrar configuración actual y salir')

    args = parser.parse_args()

    # Solo mostrar configuración
    if args.config:
        print_header()
        print_configuration()
        from materials import print_material_info
        print_material_info()
        sys.exit(0)

    # Ejecutar simulación
    results = run_simulation(
        show_plots=not args.no_plots,
        export_results=not args.no_export
    )

    if results is None:
        sys.exit(1)

    # Resumen final
    if len(results['loads']) > 0:
        print("\n📊 RESUMEN DE RESULTADOS:")
        print(f"  • Carga máxima: {max(results['loads']):.2f} kN")
        print(f"  • Asentamiento máximo: {max(results['settlements']):.4f} mm")
        print(f"  • Presión de contacto máxima: {max(results['loads'])/(FOOTING_WIDTH*FOOTING_LENGTH):.2f} kPa")
        print(f"  • Pasos convergidos: {sum(results['converged'])}/{len(results['converged'])}")
        print(f"\n📁 Resultados guardados en: results/\n")

if __name__ == '__main__':
    main()
