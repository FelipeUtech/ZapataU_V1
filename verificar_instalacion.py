#!/usr/bin/env python3
"""
Script de verificación de instalación para ZapataU_V1.
Verifica que todas las dependencias estén instaladas correctamente.

Uso:
    python verificar_instalacion.py
"""

import sys
import os


def print_header(text):
    """Imprime encabezado con formato."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_section(text):
    """Imprime sección con formato."""
    print(f"\n{'─'*70}")
    print(f"  {text}")
    print('─'*70)


def check_python_version():
    """Verifica la versión de Python."""
    print_section("1. Verificando Versión de Python")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    print(f"   Versión detectada: Python {version_str}")

    # Verificar rango compatible
    if version.major != 3:
        print("   ❌ ERROR: Se requiere Python 3.x")
        return False
    elif version.minor < 9:
        print("   ❌ ERROR: Se requiere Python 3.9 o superior")
        return False
    elif version.minor >= 12:
        print("   ⚠️  ADVERTENCIA: Python 3.12+ puede no ser compatible con OpenSeesPy")
        print("   💡 Recomendación: Usar Python 3.9, 3.10 o 3.11")
        return True  # No es un error fatal, pero advertir
    else:
        print(f"   ✅ Versión compatible: Python {version_str}")
        return True


def check_virtual_env():
    """Verifica si se está usando un entorno virtual."""
    print_section("2. Verificando Entorno Virtual")

    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if in_venv:
        print(f"   ✅ Entorno virtual activo")
        print(f"   📁 Ubicación: {sys.prefix}")
        return True
    else:
        print("   ⚠️  No se detectó entorno virtual")
        print("   💡 Recomendación: Usar un entorno virtual (venv)")
        print("   💡 Comando: python -m venv venv && source venv/bin/activate")
        return True  # No es error fatal


def check_package(module_name, display_name, import_test=None):
    """
    Verifica si un paquete está instalado.

    Args:
        module_name: Nombre del módulo a importar
        display_name: Nombre para mostrar
        import_test: Función adicional de prueba (opcional)

    Returns:
        tuple: (success: bool, version: str, details: str)
    """
    try:
        # Importar módulo
        if '.' in module_name:
            # Para importaciones anidadas como 'openseespy.opensees'
            parts = module_name.split('.')
            module = __import__(parts[0])
            for part in parts[1:]:
                module = getattr(module, part)
        else:
            module = __import__(module_name)

        # Obtener versión
        version = 'desconocida'
        if hasattr(module, '__version__'):
            version = module.__version__
        elif hasattr(module, 'VERSION'):
            version = module.VERSION

        # Prueba adicional si se proporciona
        details = ""
        if import_test:
            try:
                details = import_test(module)
            except Exception as e:
                details = f"⚠️  Advertencia en prueba: {str(e)}"

        return True, version, details

    except ImportError as e:
        return False, None, str(e)
    except Exception as e:
        return False, None, f"Error inesperado: {str(e)}"


def test_opensees(module):
    """Prueba adicional para OpenSeesPy."""
    try:
        # Intentar operación básica
        module.wipe()
        module.model('basic', '-ndm', 2, '-ndf', 2)
        module.wipe()
        return "✓ Funciones básicas OK"
    except Exception as e:
        return f"⚠️  Error en prueba básica: {str(e)}"


def test_gmsh(module):
    """Prueba adicional para GMSH."""
    try:
        module.initialize()
        module.finalize()
        return "✓ Inicialización OK"
    except Exception as e:
        return f"⚠️  Error en prueba: {str(e)}"


def test_pyvista(module):
    """Prueba adicional para PyVista."""
    try:
        # Verificar backends disponibles
        backend = module.global_theme.jupyter_backend
        return f"✓ Backend: {backend}"
    except Exception as e:
        return f"⚠️  {str(e)}"


def check_all_packages():
    """Verifica todos los paquetes necesarios."""
    print_section("3. Verificando Paquetes de Python")

    packages = [
        # (módulo, nombre, función_prueba)
        ('numpy', 'NumPy', None),
        ('openseespy.opensees', 'OpenSeesPy', test_opensees),
        ('gmsh', 'GMSH', test_gmsh),
        ('pyvista', 'PyVista', test_pyvista),
        ('meshio', 'meshio', None),
        ('matplotlib', 'Matplotlib', None),
        ('scipy', 'SciPy', None),
        ('pandas', 'Pandas (opcional)', None),
    ]

    all_ok = True
    results = []

    for module_name, display_name, test_func in packages:
        success, version, details = check_package(module_name, display_name, test_func)
        results.append((display_name, success, version, details))

        if not success:
            if 'opcional' not in display_name.lower():
                all_ok = False

    # Imprimir resultados
    print(f"\n{'Paquete':<20} {'Estado':<10} {'Versión':<15} {'Detalles'}")
    print('─'*70)

    for name, success, version, details in results:
        status = "✅ OK" if success else "❌ FALTA"
        ver_str = version if version else "N/A"
        print(f"{name:<20} {status:<10} {ver_str:<15} {details}")

    return all_ok


def check_system_dependencies():
    """Verifica dependencias del sistema (solo informativo)."""
    print_section("4. Información del Sistema")

    print(f"   Sistema operativo: {sys.platform}")
    print(f"   Arquitectura: {os.uname().machine if hasattr(os, 'uname') else 'Windows'}")

    if sys.platform.startswith('linux'):
        print("\n   💡 En Linux, asegúrate de tener instalado:")
        print("      - build-essential")
        print("      - gfortran")
        print("      - liblapack-dev, libblas-dev")
        print("      - tcl-dev, tk-dev")
        print("\n   Comando:")
        print("   sudo apt install build-essential gfortran liblapack-dev libblas-dev tcl-dev tk-dev")

    elif sys.platform == 'darwin':
        print("\n   💡 En macOS, asegúrate de tener instalado:")
        print("      - Xcode Command Line Tools")
        print("      - Homebrew packages: gcc, gfortran, openblas")
        print("\n   Comandos:")
        print("   xcode-select --install")
        print("   brew install gcc gfortran openblas lapack tcl-tk")

    elif sys.platform == 'win32':
        print("\n   💡 En Windows:")
        print("      - Considera usar WSL2 para mejor compatibilidad")
        print("      - O usa Python wheels precompilados")


def check_project_files():
    """Verifica archivos importantes del proyecto."""
    print_section("5. Verificando Archivos del Proyecto")

    required_files = [
        'config.py',
        'run_opensees_analysis.py',
        'generate_mesh_from_config.py',
        'gmsh_to_opensees.py',
        'visualizar_resultados_opensees.py',
        'mesh_config.json',
    ]

    optional_files = [
        'run_pipeline.py',
        'utils.py',
    ]

    all_ok = True

    print("\n   Archivos requeridos:")
    for filename in required_files:
        exists = os.path.isfile(filename)
        status = "✅" if exists else "❌"
        print(f"      {status} {filename}")
        if not exists:
            all_ok = False

    print("\n   Archivos opcionales:")
    for filename in optional_files:
        exists = os.path.isfile(filename)
        status = "✅" if exists else "⚠️ "
        print(f"      {status} {filename}")

    return all_ok


def check_directories():
    """Verifica directorios necesarios."""
    print_section("6. Verificando Directorios")

    required_dirs = [
        'opensees_input',
        'resultados_opensees',
        'mallas',
    ]

    print("\n   Directorios del proyecto:")
    for dirname in required_dirs:
        exists = os.path.isdir(dirname)
        status = "✅" if exists else "💡"
        msg = "existe" if exists else "se creará automáticamente"
        print(f"      {status} {dirname:<20} ({msg})")


def print_summary(checks_passed):
    """Imprime resumen final."""
    print_header("RESUMEN")

    if all(checks_passed.values()):
        print("\n   🎉 ¡Todo está correctamente configurado!")
        print("   ✅ Puedes comenzar a usar el proyecto")
        print("\n   Comandos sugeridos:")
        print("      python run_pipeline.py")
        print("      python visualizar_resultados_opensees.py")
    else:
        print("\n   ⚠️  Se encontraron algunos problemas:")
        for check, passed in checks_passed.items():
            status = "✅" if passed else "❌"
            print(f"      {status} {check}")

        print("\n   📚 Consulta INSTALACION.md para instrucciones detalladas")
        print("   💡 Ejecuta: cat INSTALACION.md | less")

    print("\n" + "="*70 + "\n")


def main():
    """Función principal."""
    print_header("VERIFICACIÓN DE INSTALACIÓN - ZapataU_V1")

    checks = {}

    # Ejecutar todas las verificaciones
    checks['Python'] = check_python_version()
    checks['Entorno Virtual'] = check_virtual_env()
    checks['Paquetes'] = check_all_packages()
    check_system_dependencies()
    checks['Archivos'] = check_project_files()
    check_directories()

    # Resumen final
    print_summary(checks)

    # Código de salida
    if all(checks.values()):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
