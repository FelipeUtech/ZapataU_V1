@echo off
REM ============================================================================
REM SCRIPT DE INSTALACIÓN AUTOMÁTICA PARA WINDOWS
REM Sistema de Análisis de Zapatas 3D
REM ============================================================================
REM
REM Este script automatiza la instalación de dependencias en Windows
REM
REM PREREQUISITOS:
REM   - Python 3.10 instalado y en PATH
REM   - Visual C++ Redistributable instalado
REM
REM USO:
REM   Ejecutar como Administrador (click derecho -> Ejecutar como administrador)
REM   setup_windows.bat
REM
REM ============================================================================

echo.
echo ================================================================================
echo   INSTALACION AUTOMATICA - SISTEMA DE ANALISIS DE ZAPATAS 3D
echo ================================================================================
echo.

REM Verificar que Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado en PATH
    echo.
    echo Por favor instala Python 3.10 desde: https://www.python.org/downloads/
    echo Asegurate de marcar "Add Python to PATH" durante la instalacion
    echo.
    pause
    exit /b 1
)

REM Mostrar versión de Python
echo [INFO] Detectado:
python --version
echo.

REM Verificar versión de Python (debe ser 3.9, 3.10 o 3.11)
python -c "import sys; v=sys.version_info; exit(0 if v.major==3 and 9<=v.minor<=11 else 1)" >nul 2>&1
if errorlevel 1 (
    echo [ADVERTENCIA] Python 3.10 es la version recomendada
    echo Tu version puede causar problemas con OpenSeesPy
    echo.
    choice /C SN /M "Continuar de todos modos? (S/N)"
    if errorlevel 2 exit /b 1
)

echo [PASO 1/7] Actualizando pip y herramientas...
echo --------------------------------------------------------------------------------
python -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] Fallo al actualizar pip
    pause
    exit /b 1
)

python -m pip install --upgrade setuptools wheel
echo [OK] Herramientas actualizadas
echo.

echo [PASO 2/7] Instalando NumPy (base numerica)...
echo --------------------------------------------------------------------------------
pip install numpy==1.24.3
if errorlevel 1 (
    echo [ERROR] Fallo al instalar NumPy
    pause
    exit /b 1
)
echo [OK] NumPy instalado
echo.

echo [PASO 3/7] Instalando librerias cientificas...
echo --------------------------------------------------------------------------------
pip install scipy==1.10.1
pip install pandas==2.0.3
echo [OK] Librerias cientificas instaladas
echo.

echo [PASO 4/7] Instalando GMSH (generacion de mallas)...
echo --------------------------------------------------------------------------------
pip install gmsh==4.11.1
if errorlevel 1 (
    echo [ERROR] Fallo al instalar GMSH
    pause
    exit /b 1
)
echo [OK] GMSH instalado
echo.

echo [PASO 5/7] Instalando VTK y PyVista (visualizacion)...
echo --------------------------------------------------------------------------------
pip install vtk==9.2.6
if errorlevel 1 (
    echo [ADVERTENCIA] Problema con VTK - puede ser problema de drivers graficos
    echo Continuando...
)

pip install pyvista==0.43.0
pip install pillow==10.0.0
pip install imageio==2.31.1
echo [OK] Herramientas de visualizacion instaladas
echo.

echo [PASO 6/7] Instalando MeshIO y Matplotlib...
echo --------------------------------------------------------------------------------
pip install meshio==5.3.4
pip install h5py
pip install matplotlib==3.7.1
pip install tqdm colorama
echo [OK] Utilidades instaladas
echo.

echo [PASO 7/7] Instalando OpenSeesPy (CRITICO)...
echo --------------------------------------------------------------------------------
echo IMPORTANTE: Este paso puede tardar y puede fallar si no tienes
echo Visual C++ Redistributable instalado
echo.

pip install openseespy==3.5.1.11
if errorlevel 1 (
    echo.
    echo [ERROR] Fallo al instalar OpenSeesPy
    echo.
    echo SOLUCIONES:
    echo   1. Instala Visual C++ Redistributable desde:
    echo      https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo   2. Reinicia la computadora
    echo   3. Intenta version anterior: pip install openseespy==3.4.0.1
    echo   4. Considera usar Conda en lugar de pip
    echo.
    pause
    exit /b 1
)
echo [OK] OpenSeesPy instalado
echo.

echo.
echo ================================================================================
echo   VERIFICANDO INSTALACION
echo ================================================================================
echo.

REM Verificar que se pueden importar los módulos
echo [TEST] Verificando imports de Python...
python -c "import numpy; print('  [OK] NumPy')" || echo   [FALLO] NumPy
python -c "import scipy; print('  [OK] SciPy')" || echo   [FALLO] SciPy
python -c "import gmsh; print('  [OK] GMSH')" || echo   [FALLO] GMSH
python -c "import pyvista; print('  [OK] PyVista')" || echo   [FALLO] PyVista
python -c "import meshio; print('  [OK] MeshIO')" || echo   [FALLO] MeshIO
python -c "import matplotlib; print('  [OK] Matplotlib')" || echo   [FALLO] Matplotlib
python -c "import openseespy.opensees as ops; print('  [OK] OpenSeesPy')" || (
    echo   [FALLO] OpenSeesPy - VER INSTRUCCIONES ARRIBA
    goto :error_opensees
)

echo.
echo ================================================================================
echo   INSTALACION COMPLETADA EXITOSAMENTE!
echo ================================================================================
echo.
echo Todas las dependencias han sido instaladas correctamente.
echo.
echo SIGUIENTES PASOS:
echo   1. Lee el manual: MANUAL_USO.md
echo   2. Revisa la configuracion: mesh_config.json
echo   3. Ejecuta un analisis de prueba: python run_full_analysis.py
echo.
echo Para visualizar resultados, instala ParaView desde:
echo   https://www.paraview.org/download/
echo.
echo ================================================================================
echo.
pause
exit /b 0

:error_opensees
echo.
echo ================================================================================
echo   INSTALACION PARCIAL - OpenSeesPy FALLO
echo ================================================================================
echo.
echo La mayoria de dependencias estan instaladas, pero OpenSeesPy fallo.
echo.
echo Para solucionar:
echo   1. Verifica que Visual C++ Redistributable este instalado
echo   2. Reinicia Windows
echo   3. Ejecuta: pip install openseespy==3.4.0.1
echo.
echo O considera usar Conda:
echo   conda install -c conda-forge openseespy
echo.
echo Ver INSTALL_WINDOWS.md para mas detalles
echo.
pause
exit /b 1
