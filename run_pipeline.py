#!/usr/bin/env python3
"""
Pipeline central para generación y conversión de mallas de zapatas.

Este script ejecuta automáticamente todo el flujo de trabajo:
1. Sincroniza configuración de config.py a mesh_config.json
2. Genera malla GMSH usando generate_mesh_from_config.py
3. Convierte malla a formato OpenSees usando gmsh_to_opensees.py
4. (Opcional) Visualiza la malla generada
5. (Opcional) Ejecuta análisis de OpenSees

Uso:
    python run_pipeline.py [opciones]

Opciones:
    --config FILE          Archivo de configuración JSON (default: mesh_config.json)
    --skip-mesh           Saltar generación de malla (usar existente)
    --skip-conversion     Saltar conversión a OpenSees
    --visualize           Generar visualización de la malla
    --run-analysis        Ejecutar análisis de OpenSees después de conversión
    --output-dir DIR      Directorio para archivos OpenSees (default: opensees_input)
"""

import sys
import argparse
import subprocess
from pathlib import Path
import json


def print_header(title):
    """Imprime encabezado decorado."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_step(step_num, total_steps, description):
    """Imprime paso del pipeline."""
    print(f"\n{'='*80}")
    print(f"  PASO {step_num}/{total_steps}: {description}")
    print(f"{'='*80}\n")


def run_command(cmd, description, check=True):
    """Ejecuta comando de shell y maneja errores."""
    print(f"🔧 Ejecutando: {' '.join(cmd)}")
    print(f"   {description}\n")

    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=False,
            text=True
        )
        print(f"\n✅ {description} completado\n")
        return result.returncode == 0

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error en: {description}")
        print(f"   Código de salida: {e.returncode}\n")
        if check:
            raise
        return False


def sync_config():
    """Sincroniza config.py a mesh_config.json."""
    print_step(1, 5, "Sincronizando configuración")

    if not Path("sync_config_to_json.py").exists():
        print("⚠️  sync_config_to_json.py no encontrado, saltando...")
        return True

    return run_command(
        ["python3", "sync_config_to_json.py"],
        "Sincronizando config.py → mesh_config.json",
        check=False
    )


def generate_mesh(config_file):
    """Genera malla usando GMSH con generate_mesh_quarter.py."""
    print_step(2, 5, "Generando malla con GMSH")

    if not Path("generate_mesh_quarter.py").exists():
        print("❌ generate_mesh_quarter.py no encontrado!")
        return False

    print("ℹ️  Usando generate_mesh_quarter.py (lee parámetros desde config.py)")

    return run_command(
        ["python3", "generate_mesh_quarter.py"],
        "Generando malla tetraédrica 3D - modelo 1/4"
    )


def get_mesh_filename(config_file):
    """Obtiene nombre del archivo de malla desde configuración."""
    # generate_mesh_quarter.py siempre genera estos archivos fijos
    base_name = "zapata_3D_cuarto"

    # Verificar qué archivo existe
    vtu_path = f"mallas/{base_name}.vtu"
    msh_path = f"mallas/{base_name}.msh"

    if Path(vtu_path).exists():
        return vtu_path
    elif Path(msh_path).exists():
        return msh_path
    else:
        print(f"⚠️  No se encontró archivo de malla en mallas/")
        return None


def convert_to_opensees(mesh_file, output_dir):
    """Convierte malla a formato OpenSees."""
    print_step(3, 5, "Convirtiendo malla a formato OpenSees")

    if not Path("gmsh_to_opensees.py").exists():
        print("❌ gmsh_to_opensees.py no encontrado!")
        return False

    if not Path(mesh_file).exists():
        print(f"❌ Archivo de malla no encontrado: {mesh_file}")
        return False

    return run_command(
        ["python3", "gmsh_to_opensees.py", mesh_file, "--output-dir", output_dir],
        f"Convirtiendo {mesh_file} a OpenSees"
    )


def visualize_mesh(mesh_file):
    """Visualiza la malla generada."""
    print_step(4, 5, "Visualizando malla")

    if not Path("visualize_mesh.py").exists():
        print("⚠️  visualize_mesh.py no encontrado, saltando visualización...")
        return True

    return run_command(
        ["python3", "visualize_mesh.py", mesh_file],
        "Generando visualización de la malla",
        check=False
    )


def run_analysis(output_dir):
    """Ejecuta análisis de OpenSees."""
    print_step(5, 5, "Ejecutando análisis de OpenSees")

    # Buscar script de análisis
    analysis_scripts = ["run_analysis.py", "zapata_analysis_quarter.py"]

    for script in analysis_scripts:
        if Path(script).exists():
            print(f"📊 Usando script: {script}")
            return run_command(
                ["python3", script],
                "Ejecutando análisis estructural",
                check=False
            )

    print("⚠️  No se encontró script de análisis, saltando...")
    return True


def print_summary(config_file, output_dir, steps_completed):
    """Imprime resumen de ejecución."""
    print_header("RESUMEN DEL PIPELINE")

    print("✅ Pasos completados:")
    for step, completed in steps_completed.items():
        status = "✅" if completed else "❌"
        print(f"   {status} {step}")

    print("\n📂 Archivos generados:")

    # Archivos de malla
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        base_name = config['output']['filename']

        print(f"\n   Mallas GMSH (directorio mallas/):")
        for fmt in config['output']['formats']:
            mesh_path = Path(f"mallas/{base_name}.{fmt}")
            if mesh_path.exists():
                size = mesh_path.stat().st_size / 1024  # KB
                print(f"     ✅ {mesh_path.name} ({size:.1f} KB)")

    except Exception as e:
        print(f"   ⚠️  Error listando mallas: {e}")

    # Archivos OpenSees
    opensees_files = ["nodes.tcl", "elements.tcl", "materials.tcl", "mesh_info.txt"]
    print(f"\n   Archivos OpenSees (directorio {output_dir}/):")

    for filename in opensees_files:
        file_path = Path(output_dir) / filename
        if file_path.exists():
            size = file_path.stat().st_size / 1024  # KB
            print(f"     ✅ {filename} ({size:.1f} KB)")

    print("\n" + "=" * 80)
    print("🎯 SIGUIENTES PASOS:")
    print("=" * 80)
    print(f"1. Edita {output_dir}/materials.tcl con los parámetros de materiales correctos")
    print(f"2. Crea tu script principal de OpenSees que use:")
    print(f"     source {output_dir}/materials.tcl")
    print(f"     source {output_dir}/nodes.tcl")
    print(f"     source {output_dir}/elements.tcl")
    print("3. Define condiciones de frontera y cargas")
    print("4. Ejecuta el análisis\n")


def main():
    """Función principal."""

    parser = argparse.ArgumentParser(
        description="Pipeline completo de generación de mallas para OpenSees",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Ejecutar pipeline completo (default):
  python run_pipeline.py

  # Usar configuración personalizada:
  python run_pipeline.py --config mi_config.json

  # Solo convertir malla existente (sin regenerar):
  python run_pipeline.py --skip-mesh

  # Pipeline completo con visualización y análisis:
  python run_pipeline.py --visualize --run-analysis

  # Solo generar malla y visualizar:
  python run_pipeline.py --skip-conversion --visualize
        """
    )

    parser.add_argument('--config', default='mesh_config.json',
                       help='Archivo de configuración JSON')
    parser.add_argument('--skip-mesh', action='store_true',
                       help='Saltar generación de malla')
    parser.add_argument('--skip-conversion', action='store_true',
                       help='Saltar conversión a OpenSees')
    parser.add_argument('--visualize', action='store_true',
                       help='Generar visualización')
    parser.add_argument('--run-analysis', action='store_true',
                       help='Ejecutar análisis de OpenSees')
    parser.add_argument('--output-dir', default='opensees_input',
                       help='Directorio para archivos OpenSees')

    args = parser.parse_args()

    # Diccionario para rastrear pasos completados
    steps_completed = {}

    print_header("🚀 PIPELINE DE GENERACIÓN DE MALLAS PARA OPENSEES")

    print(f"📋 Configuración:")
    print(f"   Archivo config: {args.config}")
    print(f"   Directorio OpenSees: {args.output_dir}")
    print(f"   Generar malla: {not args.skip_mesh}")
    print(f"   Convertir a OpenSees: {not args.skip_conversion}")
    print(f"   Visualizar: {args.visualize}")
    print(f"   Ejecutar análisis: {args.run_analysis}")

    try:
        # Paso 1: Sincronizar configuración
        steps_completed['Sincronización config'] = sync_config()

        # Paso 2: Generar malla
        if not args.skip_mesh:
            steps_completed['Generación de malla'] = generate_mesh(args.config)
        else:
            print_step(2, 5, "Generación de malla (SALTADO)")
            steps_completed['Generación de malla'] = True

        # Obtener nombre de archivo de malla
        mesh_file = get_mesh_filename(args.config)
        if not mesh_file:
            print("❌ No se pudo determinar archivo de malla")
            sys.exit(1)

        print(f"\n📄 Archivo de malla: {mesh_file}")

        # Paso 3: Convertir a OpenSees
        if not args.skip_conversion:
            steps_completed['Conversión a OpenSees'] = convert_to_opensees(
                mesh_file, args.output_dir
            )
        else:
            print_step(3, 5, "Conversión a OpenSees (SALTADO)")
            steps_completed['Conversión a OpenSees'] = True

        # Paso 4: Visualizar (opcional)
        if args.visualize:
            steps_completed['Visualización'] = visualize_mesh(mesh_file)
        else:
            print_step(4, 5, "Visualización (SALTADO)")
            steps_completed['Visualización'] = True

        # Paso 5: Ejecutar análisis (opcional)
        if args.run_analysis:
            steps_completed['Análisis OpenSees'] = run_analysis(args.output_dir)
        else:
            print_step(5, 5, "Análisis OpenSees (SALTADO)")
            steps_completed['Análisis OpenSees'] = True

        # Resumen
        print_summary(args.config, args.output_dir, steps_completed)

        # Verificar si todos los pasos críticos tuvieron éxito
        critical_steps = ['Generación de malla', 'Conversión a OpenSees']
        all_success = all(steps_completed.get(step, False) for step in critical_steps)

        if all_success:
            print("=" * 80)
            print("🎉 PIPELINE COMPLETADO EXITOSAMENTE")
            print("=" * 80 + "\n")
            sys.exit(0)
        else:
            print("=" * 80)
            print("⚠️  PIPELINE COMPLETADO CON ADVERTENCIAS")
            print("=" * 80 + "\n")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrumpido por el usuario")
        sys.exit(130)

    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
