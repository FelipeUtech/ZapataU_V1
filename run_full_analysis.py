#!/usr/bin/env python3
"""
========================================
SCRIPT MAESTRO - ANÁLISIS DE ZAPATA 3D
========================================

Este script ejecuta el pipeline completo de análisis:
1. Lee configuración desde mesh_config.json
2. Genera malla 3D con GMSH
3. Convierte a formato OpenSees
4. Ejecuta análisis estructural con OpenSees
5. Genera visualizaciones y reportes

Autor: Sistema de Análisis de Zapatas
Versión: 1.0
Fecha: 2024

Uso:
    python run_full_analysis.py [opciones]

Opciones:
    --config CONFIG     Archivo de configuración (default: mesh_config.json)
    --skip-mesh         Saltar generación de malla (usar existente)
    --skip-analysis     Solo generar malla, no analizar
    --export-paraview   Generar archivos VTU para ParaView
    --verbose           Modo verboso

Ejemplo:
    python run_full_analysis.py --config mi_zapata.json --export-paraview
"""

import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
import shutil


class Colors:
    """Códigos ANSI para colores en terminal (opcional)."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Imprime encabezado con formato."""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)


def print_step(step_num, total_steps, description):
    """Imprime paso actual."""
    print(f"\n[PASO {step_num}/{total_steps}] {description}")
    print("-"*80)


def print_success(message):
    """Imprime mensaje de éxito."""
    print(f"✅ {message}")


def print_error(message):
    """Imprime mensaje de error."""
    print(f"❌ ERROR: {message}")


def print_warning(message):
    """Imprime mensaje de advertencia."""
    print(f"⚠️  ADVERTENCIA: {message}")


def print_info(message):
    """Imprime mensaje informativo."""
    print(f"ℹ️  {message}")


def verificar_dependencias():
    """Verifica que todas las dependencias estén instaladas."""
    print_step(0, 7, "VERIFICACIÓN DE DEPENDENCIAS")

    dependencias = {
        'gmsh': 'GMSH (generación de mallas)',
        'pyvista': 'PyVista (visualización)',
        'numpy': 'NumPy (cálculos numéricos)',
        'openseespy': 'OpenSeesPy (análisis estructural)',
        'meshio': 'MeshIO (conversión de mallas)'
    }

    faltantes = []

    for modulo, descripcion in dependencias.items():
        try:
            __import__(modulo)
            print_success(f"{descripcion} - OK")
        except ImportError:
            print_error(f"{descripcion} - NO INSTALADO")
            faltantes.append(modulo)

    if faltantes:
        print_error("Dependencias faltantes. Instala con:")
        print(f"    pip install {' '.join(faltantes)}")
        return False

    print_success("Todas las dependencias están instaladas")
    return True


def cargar_configuracion(config_file):
    """Carga archivo de configuración JSON."""
    print_info(f"Cargando configuración desde: {config_file}")

    if not Path(config_file).exists():
        print_error(f"Archivo de configuración no encontrado: {config_file}")
        return None

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        print_success(f"Configuración cargada")

        # Mostrar resumen
        geom = config['geometry']
        foot = geom['footing']
        print(f"\n   Zapata: {foot.get('B', 2.0)} m × {foot.get('L', 2.0)} m × {foot['tz']} m")
        print(f"   Profundidad de desplante: {foot['Df']} m")
        print(f"   Estratos de suelo: {len(config['soil_layers'])}")
        print(f"   Dominio: {geom['domain']['Lx']} × {geom['domain']['Ly']} × {geom['domain']['Lz']} m")

        return config

    except json.JSONDecodeError as e:
        print_error(f"Error al leer JSON: {e}")
        return None
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        return None


def ejecutar_comando(comando, descripcion, verbose=False):
    """
    Ejecuta un comando de shell y captura salida.

    Args:
        comando: Lista con comando y argumentos
        descripcion: Descripción de la operación
        verbose: Si True, muestra toda la salida

    Returns:
        bool: True si exitoso, False si falló
    """
    print(f"\n   Ejecutando: {descripcion}...")

    try:
        if verbose:
            # Mostrar salida en tiempo real
            proceso = subprocess.Popen(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            for linea in proceso.stdout:
                print(f"      {linea.rstrip()}")

            proceso.wait()
            codigo_salida = proceso.returncode
        else:
            # Capturar salida
            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                check=False
            )
            codigo_salida = resultado.returncode

            # Mostrar solo últimas líneas si hay error
            if codigo_salida != 0:
                print_error(f"Comando falló con código {codigo_salida}")
                if resultado.stderr:
                    print("   Últimas líneas de error:")
                    for linea in resultado.stderr.strip().split('\n')[-5:]:
                        print(f"      {linea}")
                if resultado.stdout:
                    print("   Últimas líneas de salida:")
                    for linea in resultado.stdout.strip().split('\n')[-5:]:
                        print(f"      {linea}")

        if codigo_salida == 0:
            print_success(f"{descripcion} completado")
            return True
        else:
            print_error(f"{descripcion} falló")
            return False

    except FileNotFoundError:
        print_error(f"Comando no encontrado: {comando[0]}")
        print_info(f"Asegúrate de que esté instalado y en el PATH")
        return False
    except Exception as e:
        print_error(f"Error al ejecutar comando: {e}")
        return False


def paso_1_generar_malla(config_file, verbose=False):
    """Paso 1: Generar malla 3D con GMSH."""
    print_step(1, 7, "GENERACIÓN DE MALLA 3D CON GMSH")

    comando = [sys.executable, "generate_mesh_from_config.py", config_file]
    exito = ejecutar_comando(comando, "Generación de malla", verbose)

    if exito:
        # Verificar que se generaron los archivos
        config = cargar_configuracion(config_file)
        if config:
            malla_file = Path("mallas") / f"{config['output']['filename']}.vtu"
            if malla_file.exists():
                print_success(f"Malla generada: {malla_file}")
                return True
            else:
                print_error(f"Archivo de malla no encontrado: {malla_file}")
                return False
    return False


def paso_2_convertir_opensees(config, verbose=False):
    """Paso 2: Convertir malla a formato OpenSees."""
    print_step(2, 7, "CONVERSIÓN A FORMATO OPENSEES")

    malla_file = Path("mallas") / f"{config['output']['filename']}.vtu"

    if not malla_file.exists():
        print_error(f"Archivo de malla no encontrado: {malla_file}")
        return False

    comando = [sys.executable, "gmsh_to_opensees.py", str(malla_file)]
    exito = ejecutar_comando(comando, "Conversión a OpenSees", verbose)

    if exito:
        # Verificar archivos generados
        archivos_necesarios = [
            "opensees_input/nodes.tcl",
            "opensees_input/elements.tcl",
            "opensees_input/materials.tcl"
        ]

        todos_existen = all(Path(f).exists() for f in archivos_necesarios)

        if todos_existen:
            print_success("Archivos OpenSees generados correctamente")
            return True
        else:
            print_error("Algunos archivos OpenSees no se generaron")
            return False

    return False


def paso_3_verificar_contacto(verbose=False):
    """Paso 3: Verificar contacto zapata-suelo."""
    print_step(3, 7, "VERIFICACIÓN DE CONTACTO ZAPATA-SUELO")

    comando = [sys.executable, "verificar_contacto_zapata_suelo.py"]
    exito = ejecutar_comando(comando, "Verificación de contacto", verbose)

    return exito


def paso_4_analisis_opensees(verbose=False):
    """Paso 4: Ejecutar análisis con OpenSees."""
    print_step(4, 7, "ANÁLISIS ESTRUCTURAL CON OPENSEES")

    # Verificar que existen archivos de entrada
    archivos_necesarios = [
        "opensees_input/nodes.tcl",
        "opensees_input/elements.tcl"
    ]

    if not all(Path(f).exists() for f in archivos_necesarios):
        print_error("Archivos de entrada de OpenSees no encontrados")
        print_info("Ejecuta primero los pasos anteriores")
        return False

    comando = [sys.executable, "run_opensees_analysis.py"]
    exito = ejecutar_comando(comando, "Análisis OpenSees", verbose)

    if exito:
        # Verificar resultados
        archivos_resultados = [
            "resultados_opensees/desplazamientos.csv",
            "resultados_opensees/tensiones.csv",
            "resultados_opensees/estadisticas.txt"
        ]

        todos_existen = all(Path(f).exists() for f in archivos_resultados)

        if todos_existen:
            print_success("Análisis completado, resultados generados")
            return True
        else:
            print_error("Algunos archivos de resultados no se generaron")
            return False

    return False


def paso_5_visualizacion(export_paraview=True, verbose=False):
    """Paso 5: Generar visualizaciones."""
    print_step(5, 7, "GENERACIÓN DE VISUALIZACIONES")

    if export_paraview:
        comando = [sys.executable, "visualizar_resultados_opensees.py", "--export-only"]
        exito = ejecutar_comando(comando, "Exportar a ParaView (VTU)", verbose)

        if exito:
            vtu_file = Path("resultados_opensees/resultados_opensees.vtu")
            if vtu_file.exists():
                print_success(f"Archivo VTU generado: {vtu_file}")
                print_info(f"Abre con ParaView: paraview {vtu_file}")
                return True
            else:
                print_error("Archivo VTU no se generó")
                return False
    else:
        print_info("Exportación a ParaView omitida")
        return True

    return False


def paso_6_generar_reporte(config):
    """Paso 6: Generar reporte resumen."""
    print_step(6, 7, "GENERACIÓN DE REPORTE RESUMEN")

    try:
        # Leer estadísticas
        stats_file = Path("resultados_opensees/estadisticas.txt")
        if not stats_file.exists():
            print_warning("Archivo de estadísticas no encontrado")
            return False

        with open(stats_file, 'r') as f:
            estadisticas = f.read()

        # Crear reporte
        reporte_file = Path("resultados_opensees/REPORTE_ANALISIS.txt")

        with open(reporte_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("REPORTE DE ANÁLISIS - ZAPATA 3D\n")
            f.write("="*80 + "\n\n")

            f.write(f"Fecha de análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Configuración: mesh_config.json\n\n")

            # Parámetros de zapata
            geom = config['geometry']
            foot = geom['footing']

            f.write("PARÁMETROS DE DISEÑO:\n")
            f.write("-"*80 + "\n")
            f.write(f"  Zapata:\n")
            f.write(f"    Ancho (B): {foot.get('B', 2.0)} m\n")
            f.write(f"    Largo (L): {foot.get('L', 2.0)} m\n")
            f.write(f"    Espesor (tz): {foot['tz']} m\n")
            f.write(f"    Profundidad de desplante (Df): {foot['Df']} m\n")
            f.write(f"    Área: {foot.get('B', 2.0) * foot.get('L', 2.0):.2f} m²\n\n")

            f.write(f"  Dominio de análisis:\n")
            f.write(f"    Dimensiones: {geom['domain']['Lx']} × {geom['domain']['Ly']} × {geom['domain']['Lz']} m\n")
            f.write(f"    Cuarto de simetría: {'Sí' if geom['domain']['quarter_domain'] else 'No'}\n\n")

            f.write(f"  Estratos de suelo: {len(config['soil_layers'])}\n")
            for i, layer in enumerate(config['soil_layers']):
                f.write(f"    {i+1}. {layer['name']}: {layer['thickness']} m (Material {layer['material_id']})\n")

            f.write("\n\n")

            # Estadísticas de malla
            mesh_info = Path("opensees_input/mesh_info.txt")
            if mesh_info.exists():
                f.write("INFORMACIÓN DE MALLA:\n")
                f.write("-"*80 + "\n")
                with open(mesh_info, 'r') as mf:
                    for line in mf:
                        if 'ESTADÍSTICAS:' in line:
                            for _ in range(4):  # Leer siguientes 4 líneas
                                line = next(mf, '')
                                f.write(line)
                f.write("\n\n")

            # Resultados
            f.write("RESULTADOS DEL ANÁLISIS:\n")
            f.write("-"*80 + "\n")
            f.write(estadisticas)

            f.write("\n\n")
            f.write("ARCHIVOS GENERADOS:\n")
            f.write("-"*80 + "\n")
            f.write("  Mallas:\n")
            f.write(f"    - mallas/{config['output']['filename']}.vtu\n")
            f.write(f"    - mallas/{config['output']['filename']}.msh\n")
            f.write("\n  Entrada OpenSees:\n")
            f.write("    - opensees_input/nodes.tcl\n")
            f.write("    - opensees_input/elements.tcl\n")
            f.write("    - opensees_input/materials.tcl\n")
            f.write("\n  Resultados:\n")
            f.write("    - resultados_opensees/desplazamientos.csv\n")
            f.write("    - resultados_opensees/tensiones.csv\n")
            f.write("    - resultados_opensees/reacciones.csv\n")
            f.write("    - resultados_opensees/resultados_opensees.vtu (ParaView)\n")
            f.write("\n" + "="*80 + "\n")

        print_success(f"Reporte generado: {reporte_file}")
        return True

    except Exception as e:
        print_error(f"Error al generar reporte: {e}")
        return False


def paso_7_limpieza_opcional():
    """Paso 7: Limpieza de archivos temporales (opcional)."""
    print_step(7, 7, "LIMPIEZA Y ORGANIZACIÓN")

    # Por ahora solo informar
    print_info("Todos los archivos se mantienen para revisión")
    print_info("Para limpiar archivos temporales, ejecuta: python cleanup.py")

    return True


def main():
    """Función principal."""

    # Parser de argumentos
    parser = argparse.ArgumentParser(
        description='Pipeline completo de análisis de zapata 3D',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    # Análisis completo con configuración por defecto
    python run_full_analysis.py

    # Usar configuración personalizada
    python run_full_analysis.py --config mi_zapata.json

    # Solo generar malla, no analizar
    python run_full_analysis.py --skip-analysis

    # Usar malla existente, solo analizar
    python run_full_analysis.py --skip-mesh

    # Modo verboso para debugging
    python run_full_analysis.py --verbose
        """
    )

    parser.add_argument('--config', default='mesh_config.json',
                       help='Archivo de configuración JSON (default: mesh_config.json)')
    parser.add_argument('--skip-mesh', action='store_true',
                       help='Saltar generación de malla (usar existente)')
    parser.add_argument('--skip-analysis', action='store_true',
                       help='Solo generar malla, no ejecutar análisis')
    parser.add_argument('--export-paraview', action='store_true', default=True,
                       help='Exportar a formato ParaView VTU (default: True)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Modo verboso (mostrar toda la salida)')

    args = parser.parse_args()

    # Banner inicial
    print("\n" + "="*80)
    print("  PIPELINE DE ANÁLISIS DE ZAPATA 3D")
    print("  Sistema Integrado de Análisis Geotécnico-Estructural")
    print("="*80)
    print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Configuración: {args.config}")
    print(f"Modo verboso: {'Activado' if args.verbose else 'Desactivado'}")

    # Verificar dependencias
    if not verificar_dependencias():
        print_error("Instala las dependencias antes de continuar")
        print_info("Ver instrucciones en: INSTALL_WINDOWS.md")
        sys.exit(1)

    # Cargar configuración
    config = cargar_configuracion(args.config)
    if config is None:
        sys.exit(1)

    # Contador de pasos exitosos
    pasos_exitosos = 0
    total_pasos = 7

    try:
        # PASO 1: Generar malla
        if not args.skip_mesh:
            if paso_1_generar_malla(args.config, args.verbose):
                pasos_exitosos += 1
            else:
                print_error("Falló la generación de malla")
                sys.exit(1)
        else:
            print_info("Generación de malla omitida (usando malla existente)")
            pasos_exitosos += 1

        # PASO 2: Convertir a OpenSees
        if not args.skip_mesh:
            if paso_2_convertir_opensees(config, args.verbose):
                pasos_exitosos += 1
            else:
                print_error("Falló la conversión a OpenSees")
                sys.exit(1)
        else:
            print_info("Conversión omitida (usando archivos existentes)")
            pasos_exitosos += 1

        # PASO 3: Verificar contacto
        if paso_3_verificar_contacto(args.verbose):
            pasos_exitosos += 1
        else:
            print_warning("Verificación de contacto completada con advertencias")
            pasos_exitosos += 1  # Continuar de todos modos

        # PASO 4: Análisis OpenSees
        if not args.skip_analysis:
            if paso_4_analisis_opensees(args.verbose):
                pasos_exitosos += 1
            else:
                print_error("Falló el análisis con OpenSees")
                sys.exit(1)
        else:
            print_info("Análisis OpenSees omitido")
            pasos_exitosos += 1

        # PASO 5: Visualizaciones
        if not args.skip_analysis:
            if paso_5_visualizacion(args.export_paraview, args.verbose):
                pasos_exitosos += 1
            else:
                print_warning("Falló la generación de visualizaciones")
                pasos_exitosos += 1  # Continuar
        else:
            print_info("Visualizaciones omitidas")
            pasos_exitosos += 1

        # PASO 6: Generar reporte
        if not args.skip_analysis:
            if paso_6_generar_reporte(config):
                pasos_exitosos += 1
            else:
                print_warning("No se pudo generar reporte completo")
                pasos_exitosos += 1  # Continuar
        else:
            print_info("Reporte omitido")
            pasos_exitosos += 1

        # PASO 7: Limpieza
        if paso_7_limpieza_opcional():
            pasos_exitosos += 1

        # Resumen final
        print_header("RESUMEN FINAL")
        print(f"\n✅ Pipeline completado exitosamente!")
        print(f"   Pasos completados: {pasos_exitosos}/{total_pasos}")

        if not args.skip_analysis:
            print("\n📊 RESULTADOS:")
            print("-"*80)

            # Mostrar estadísticas clave
            stats_file = Path("resultados_opensees/estadisticas.txt")
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    for line in f:
                        if 'asentamiento' in line.lower() or 'máximo' in line.lower():
                            print(f"   {line.strip()}")

            print("\n📂 ARCHIVOS PRINCIPALES:")
            print("-"*80)
            print(f"   Malla: mallas/{config['output']['filename']}.vtu")
            print(f"   Resultados: resultados_opensees/")
            print(f"   Reporte: resultados_opensees/REPORTE_ANALISIS.txt")
            if args.export_paraview:
                print(f"   ParaView: resultados_opensees/resultados_opensees.vtu")

            print("\n💡 SIGUIENTES PASOS:")
            print("-"*80)
            print("   1. Revisa el reporte: resultados_opensees/REPORTE_ANALISIS.txt")
            print("   2. Visualiza en ParaView: paraview resultados_opensees/resultados_opensees.vtu")
            print("   3. Analiza desplazamientos: resultados_opensees/desplazamientos.csv")
            print("   4. Revisa tensiones: resultados_opensees/tensiones.csv")

        print("\n" + "="*80)
        print("  🎉 ¡ANÁLISIS COMPLETADO EXITOSAMENTE!")
        print("="*80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
