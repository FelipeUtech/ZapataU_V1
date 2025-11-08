# Script de instalación automatizada para ZapataU_V1 en Windows
# Requiere PowerShell 5.1 o superior
#
# Uso:
#   .\setup.ps1
#
# Si hay error de ejecución de scripts, ejecutar primero como administrador:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Configurar para detener en errores
$ErrorActionPreference = "Stop"

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  INSTALACIÓN AUTOMATIZADA - ZapataU_V1 (Windows)" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar versión de PowerShell
Write-Host "Verificando PowerShell..." -ForegroundColor Yellow
$psVersion = $PSVersionTable.PSVersion
Write-Host "✓ PowerShell $psVersion" -ForegroundColor Green
Write-Host ""

# Verificar Python
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "  Verificando Python..." -ForegroundColor Yellow
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Cyan

$pythonFound = $false
$pythonCmd = ""

# Buscar Python compatible
$pythonCommands = @("python3.10", "python3.11", "python3.9", "python")

foreach ($cmd in $pythonCommands) {
    try {
        $versionOutput = & $cmd --version 2>&1
        if ($versionOutput -match "Python (\d+)\.(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]

            if ($major -eq 3 -and $minor -ge 9 -and $minor -lt 12) {
                $pythonCmd = $cmd
                $pythonFound = $true
                Write-Host "✓ Python encontrado: $cmd ($versionOutput)" -ForegroundColor Green
                break
            }
        }
    } catch {
        # Comando no encontrado, continuar buscando
        continue
    }
}

if (-not $pythonFound) {
    Write-Host "❌ No se encontró Python 3.9-3.11" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Descarga e instala Python desde:" -ForegroundColor Yellow
    Write-Host "   https://www.python.org/downloads/" -ForegroundColor White
    Write-Host ""
    Write-Host "   IMPORTANTE: Durante la instalación, marca:" -ForegroundColor Yellow
    Write-Host "   ✓ Add Python to PATH" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 Recomendación: Usa Python 3.10" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 Alternativa (RECOMENDADO): Usa WSL2 (Windows Subsystem for Linux)" -ForegroundColor Yellow
    Write-Host "   Ver: https://docs.microsoft.com/en-us/windows/wsl/install" -ForegroundColor White
    exit 1
}

Write-Host ""

# Advertencia sobre OpenSeesPy en Windows
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "  IMPORTANTE - OpenSeesPy en Windows" -ForegroundColor Yellow
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  OpenSeesPy puede tener problemas de compatibilidad en Windows" -ForegroundColor Yellow
Write-Host ""
Write-Host "Opciones recomendadas:" -ForegroundColor White
Write-Host "  1. Usar WSL2 (Windows Subsystem for Linux) - MÁS CONFIABLE" -ForegroundColor Green
Write-Host "  2. Continuar con instalación en Windows nativo - Puede funcionar" -ForegroundColor Yellow
Write-Host ""

$response = Read-Host "¿Continuar con instalación en Windows nativo? (S/N)"
if ($response -notmatch "^[SsYy]") {
    Write-Host ""
    Write-Host "Instalación cancelada." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Para usar WSL2:" -ForegroundColor Cyan
    Write-Host "  1. Ejecuta en PowerShell como administrador:" -ForegroundColor White
    Write-Host "     wsl --install" -ForegroundColor White
    Write-Host "  2. Reinicia tu computadora" -ForegroundColor White
    Write-Host "  3. Abre Ubuntu desde el menú de inicio" -ForegroundColor White
    Write-Host "  4. Sigue las instrucciones de INSTALACION.md para Linux" -ForegroundColor White
    Write-Host ""
    exit 0
}

Write-Host ""

# Crear entorno virtual
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "  Configurando entorno virtual..." -ForegroundColor Yellow
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Cyan

if (Test-Path "venv") {
    Write-Host "⚠️  El directorio 'venv' ya existe" -ForegroundColor Yellow
    $response = Read-Host "¿Deseas recrearlo? Esto eliminará el actual. (S/N)"

    if ($response -match "^[SsYy]") {
        Write-Host "Eliminando entorno virtual existente..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force "venv"
    } else {
        Write-Host "Usando entorno virtual existente" -ForegroundColor Green
    }
}

if (-not (Test-Path "venv")) {
    Write-Host "Creando entorno virtual con $pythonCmd..." -ForegroundColor Yellow
    & $pythonCmd -m venv venv
    Write-Host "✓ Entorno virtual creado" -ForegroundColor Green
} else {
    Write-Host "✓ Usando entorno virtual existente" -ForegroundColor Green
}

Write-Host ""

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Yellow

# Determinar el script de activación según el shell
$activateScript = "venv\Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    Write-Host "❌ Error: No se encuentra el script de activación" -ForegroundColor Red
    exit 1
}

# Activar
& $activateScript

Write-Host "✓ Entorno virtual activado" -ForegroundColor Green
Write-Host ""

# Actualizar pip
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "  Actualizando pip, setuptools y wheel..." -ForegroundColor Yellow
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Cyan

python -m pip install --upgrade pip setuptools wheel
Write-Host "✓ Herramientas actualizadas" -ForegroundColor Green
Write-Host ""

# Instalar dependencias de Python
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "  Instalando dependencias de Python..." -ForegroundColor Yellow
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host ""
Write-Host "Este proceso puede tardar varios minutos..." -ForegroundColor Yellow
Write-Host ""

try {
    Write-Host "[1/7] Instalando NumPy..." -ForegroundColor Cyan
    pip install numpy==1.24.3

    Write-Host "[2/7] Instalando OpenSeesPy (puede tardar)..." -ForegroundColor Cyan
    Write-Host "⚠️  Si falla, se intentará con versión alternativa" -ForegroundColor Yellow

    try {
        pip install openseespy==3.5.1.11
    } catch {
        Write-Host "⚠️  Versión 3.5.1.11 falló, intentando 3.4.0.1..." -ForegroundColor Yellow
        pip install openseespy==3.4.0.1
    }

    Write-Host "[3/7] Instalando GMSH..." -ForegroundColor Cyan
    pip install gmsh==4.11.1

    Write-Host "[4/7] Instalando PyVista..." -ForegroundColor Cyan
    pip install pyvista==0.43.0

    Write-Host "[5/7] Instalando meshio..." -ForegroundColor Cyan
    pip install meshio==5.3.4

    Write-Host "[6/7] Instalando Matplotlib..." -ForegroundColor Cyan
    pip install matplotlib==3.7.1

    Write-Host "[7/7] Instalando SciPy y Pandas..." -ForegroundColor Cyan
    pip install scipy==1.10.1 pandas==2.0.3

    Write-Host ""
    Write-Host "✓ Todas las dependencias instaladas" -ForegroundColor Green
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "❌ Error durante la instalación de dependencias" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Consulta INSTALACION.md para solución de problemas" -ForegroundColor Yellow
    exit 1
}

# Verificar instalación
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "  Verificando instalación..." -ForegroundColor Yellow
Write-Host "────────────────────────────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host ""

python verificar_instalacion.py
$verifyStatus = $LASTEXITCODE

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  INSTALACIÓN COMPLETADA" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

if ($verifyStatus -eq 0) {
    Write-Host "🎉 ¡Instalación exitosa!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Próximos pasos:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Activar el entorno virtual cada vez que trabajes:" -ForegroundColor White
    Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "2. Ejecutar el pipeline completo:" -ForegroundColor White
    Write-Host "   python run_pipeline.py" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "3. Visualizar resultados:" -ForegroundColor White
    Write-Host "   python visualizar_resultados_opensees.py" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "4. Ver documentación:" -ForegroundColor White
    Write-Host "   type INSTALACION.md" -ForegroundColor Yellow
    Write-Host "   type README.md" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "⚠️  La instalación completó con advertencias" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Revisa los mensajes arriba para más detalles." -ForegroundColor White
    Write-Host "Consulta INSTALACION.md para solución de problemas." -ForegroundColor White
    Write-Host ""
}

Write-Host "========================================================================" -ForegroundColor Cyan
