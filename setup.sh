#!/bin/bash
# Script de instalación automatizada para ZapataU_V1
# Solo para Linux y macOS
#
# Uso:
#   chmod +x setup.sh
#   ./setup.sh

set -e  # Salir si hay errores

echo "════════════════════════════════════════════════════════════════════"
echo "  INSTALACIÓN AUTOMATIZADA - ZapataU_V1"
echo "════════════════════════════════════════════════════════════════════"
echo ""

# Detectar sistema operativo
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo "✓ Sistema detectado: Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo "✓ Sistema detectado: macOS"
else
    echo "❌ Sistema operativo no soportado: $OSTYPE"
    echo "💡 Este script solo funciona en Linux y macOS"
    echo "💡 Para Windows, sigue las instrucciones en INSTALACION.md"
    exit 1
fi

echo ""

# Verificar Python
echo "────────────────────────────────────────────────────────────────────"
echo "  Verificando Python..."
echo "────────────────────────────────────────────────────────────────────"

# Buscar Python compatible
PYTHON_CMD=""
for cmd in python3.10 python3.11 python3.9 python3; do
    if command -v $cmd &> /dev/null; then
        VERSION=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        MAJOR=$(echo $VERSION | cut -d. -f1)
        MINOR=$(echo $VERSION | cut -d. -f2)

        if [ "$MAJOR" = "3" ] && [ "$MINOR" -ge 9 ] && [ "$MINOR" -lt 12 ]; then
            PYTHON_CMD=$cmd
            echo "✓ Python encontrado: $cmd ($VERSION)"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ No se encontró Python 3.9-3.11"
    echo ""
    if [ "$OS" = "linux" ]; then
        echo "💡 Instala Python con:"
        echo "   sudo apt update"
        echo "   sudo apt install python3.10 python3.10-venv python3.10-dev"
    elif [ "$OS" = "macos" ]; then
        echo "💡 Instala Python con Homebrew:"
        echo "   brew install python@3.10"
    fi
    exit 1
fi

echo ""

# Instalar dependencias del sistema
echo "────────────────────────────────────────────────────────────────────"
echo "  Instalando dependencias del sistema..."
echo "────────────────────────────────────────────────────────────────────"

if [ "$OS" = "linux" ]; then
    echo "💡 Se requiere sudo para instalar dependencias del sistema"
    echo "   Paquetes: build-essential, gfortran, liblapack-dev, etc."
    echo ""
    read -p "¿Deseas instalar dependencias del sistema? (s/n) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[SsYy]$ ]]; then
        sudo apt update
        sudo apt install -y \
            build-essential \
            gfortran \
            liblapack-dev \
            libblas-dev \
            libopenblas-dev \
            tcl-dev \
            tk-dev \
            python3-dev
        echo "✓ Dependencias del sistema instaladas"
    else
        echo "⚠️  Dependencias del sistema omitidas"
        echo "   OpenSeesPy podría no funcionar correctamente"
    fi

elif [ "$OS" = "macos" ]; then
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew no está instalado"
        echo "💡 Instala Homebrew desde: https://brew.sh"
        exit 1
    fi

    echo "Instalando dependencias con Homebrew..."
    brew install gcc gfortran openblas lapack tcl-tk
    echo "✓ Dependencias instaladas"
fi

echo ""

# Crear entorno virtual
echo "────────────────────────────────────────────────────────────────────"
echo "  Configurando entorno virtual..."
echo "────────────────────────────────────────────────────────────────────"

if [ -d "venv" ]; then
    echo "⚠️  El directorio 'venv' ya existe"
    read -p "¿Deseas recrearlo? Esto eliminará el actual. (s/n) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[SsYy]$ ]]; then
        echo "Eliminando entorno virtual existente..."
        rm -rf venv
    else
        echo "Usando entorno virtual existente"
    fi
fi

if [ ! -d "venv" ]; then
    echo "Creando entorno virtual con $PYTHON_CMD..."
    $PYTHON_CMD -m venv venv
    echo "✓ Entorno virtual creado"
else
    echo "✓ Usando entorno virtual existente"
fi

echo ""

# Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate

# Verificar activación
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Error al activar entorno virtual"
    exit 1
fi

echo "✓ Entorno virtual activado: $VIRTUAL_ENV"
echo ""

# Actualizar pip
echo "────────────────────────────────────────────────────────────────────"
echo "  Actualizando pip, setuptools y wheel..."
echo "────────────────────────────────────────────────────────────────────"

pip install --upgrade pip setuptools wheel
echo "✓ Herramientas actualizadas"
echo ""

# Instalar dependencias de Python
echo "────────────────────────────────────────────────────────────────────"
echo "  Instalando dependencias de Python..."
echo "────────────────────────────────────────────────────────────────────"
echo ""
echo "Este proceso puede tardar varios minutos..."
echo ""

# Instalar en orden específico para evitar conflictos
echo "[1/7] Instalando NumPy..."
pip install numpy==1.24.3

echo "[2/7] Instalando OpenSeesPy (puede tardar)..."
pip install openseespy==3.5.1.11

echo "[3/7] Instalando GMSH..."
pip install gmsh==4.11.1

echo "[4/7] Instalando PyVista..."
pip install pyvista==0.43.0

echo "[5/7] Instalando meshio..."
pip install meshio==5.3.4

echo "[6/7] Instalando Matplotlib..."
pip install matplotlib==3.7.1

echo "[7/7] Instalando SciPy y Pandas..."
pip install scipy==1.10.1 pandas==2.0.3

echo ""
echo "✓ Todas las dependencias instaladas"
echo ""

# Verificar instalación
echo "────────────────────────────────────────────────────────────────────"
echo "  Verificando instalación..."
echo "────────────────────────────────────────────────────────────────────"
echo ""

python verificar_instalacion.py

# Guardar estado de la verificación
VERIFY_STATUS=$?

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "  INSTALACIÓN COMPLETADA"
echo "════════════════════════════════════════════════════════════════════"
echo ""

if [ $VERIFY_STATUS -eq 0 ]; then
    echo "🎉 ¡Instalación exitosa!"
    echo ""
    echo "Próximos pasos:"
    echo ""
    echo "1. Activar el entorno virtual cada vez que trabajes:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Ejecutar el pipeline completo:"
    echo "   python run_pipeline.py"
    echo ""
    echo "3. Visualizar resultados:"
    echo "   python visualizar_resultados_opensees.py"
    echo ""
    echo "4. Ver documentación:"
    echo "   cat INSTALACION.md"
    echo "   cat README.md"
    echo ""
else
    echo "⚠️  La instalación completó con advertencias"
    echo ""
    echo "Revisa los mensajes arriba para más detalles."
    echo "Consulta INSTALACION.md para solución de problemas."
    echo ""
fi

echo "════════════════════════════════════════════════════════════════════"
