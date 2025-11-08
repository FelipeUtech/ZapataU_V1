# 📦 Guía de Instalación - ZapataU_V1

Esta guía te ayudará a configurar el proyecto en tu máquina local paso a paso, incluyendo la instalación de todas las dependencias necesarias con las versiones correctas.

---

## 📋 Tabla de Contenidos

1. [Requisitos del Sistema](#-requisitos-del-sistema)
2. [Instalación de Python](#-instalación-de-python)
3. [Configuración del Entorno Virtual](#-configuración-del-entorno-virtual)
4. [Instalación de Dependencias](#-instalación-de-dependencias)
5. [Verificación de la Instalación](#-verificación-de-la-instalación)
6. [Ejecutar el Proyecto](#-ejecutar-el-proyecto)
7. [Solución de Problemas Comunes](#-solución-de-problemas-comunes)

---

## 💻 Requisitos del Sistema

### Sistemas Operativos Soportados
- **Linux**: Ubuntu 20.04+, Debian 10+, Fedora 35+ (RECOMENDADO)
- **macOS**: 10.15+ (Catalina o superior)
- **Windows**: Windows 10/11 (con WSL2 recomendado para mejor compatibilidad)

### Requisitos de Hardware
- **RAM**: Mínimo 8 GB (recomendado 16 GB para mallas grandes)
- **Espacio en disco**: 5 GB libres
- **Procesador**: CPU con 4+ núcleos recomendado

### Software Requerido
- Python 3.9 a 3.11 (IMPORTANTE: NO usar Python 3.12+)
- pip (gestor de paquetes de Python)
- git (para clonar el repositorio)

---

## 🐍 Instalación de Python

### En Linux (Ubuntu/Debian)

```bash
# Actualizar repositorios
sudo apt update

# Instalar Python 3.10 (versión recomendada)
sudo apt install python3.10 python3.10-venv python3.10-dev

# Verificar instalación
python3.10 --version
# Debe mostrar: Python 3.10.x

# Instalar pip
sudo apt install python3-pip

# Actualizar pip
python3.10 -m pip install --upgrade pip
```

### En macOS

```bash
# Instalar Homebrew si no lo tienes
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Python 3.10
brew install python@3.10

# Verificar instalación
python3.10 --version

# pip viene incluido con Python de Homebrew
```

### En Windows

**Opción A: Instalación Directa (puede tener problemas con OpenSees)**
1. Descargar Python 3.10.x desde https://www.python.org/downloads/
2. IMPORTANTE: Marcar "Add Python to PATH" durante instalación
3. Verificar en PowerShell:
   ```powershell
   python --version
   ```

**Opción B: WSL2 (RECOMENDADO para mejor compatibilidad)**
1. Instalar WSL2 siguiendo: https://docs.microsoft.com/en-us/windows/wsl/install
2. Instalar Ubuntu 22.04 desde Microsoft Store
3. Seguir instrucciones de Linux arriba

---

## 🔧 Configuración del Entorno Virtual

### ¿Por qué usar un entorno virtual?
Un entorno virtual aísla las dependencias de este proyecto de otros proyectos Python en tu sistema, evitando conflictos de versiones.

### Crear el Entorno Virtual

```bash
# 1. Navegar al directorio del proyecto
cd /ruta/a/ZapataU_V1

# 2. Crear entorno virtual llamado 'venv'
# En Linux/macOS:
python3.10 -m venv venv

# En Windows (sin WSL):
python -m venv venv

# 3. Activar el entorno virtual

# En Linux/macOS:
source venv/bin/activate

# En Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# En Windows (CMD):
.\venv\Scripts\activate.bat

# Deberías ver (venv) al inicio de tu línea de comando
# Ejemplo: (venv) usuario@computadora:~/ZapataU_V1$
```

### Desactivar el Entorno Virtual
```bash
# Cuando termines de trabajar:
deactivate
```

---

## 📦 Instalación de Dependencias

**IMPORTANTE**: Asegúrate de que el entorno virtual esté activado antes de instalar paquetes.

### Paso 1: Actualizar pip, setuptools y wheel

```bash
pip install --upgrade pip setuptools wheel
```

### Paso 2: Instalar NumPy (debe instalarse primero)

```bash
pip install numpy==1.24.3
```

### Paso 3: Instalar OpenSeesPy (CRÍTICO - lee cuidadosamente)

OpenSeesPy es la biblioteca más problemática de instalar. Aquí están las instrucciones específicas por plataforma:

#### En Linux (Ubuntu/Debian)

```bash
# Instalar dependencias del sistema primero
sudo apt install -y \
    build-essential \
    gfortran \
    liblapack-dev \
    libblas-dev \
    libopenblas-dev \
    tcl-dev \
    tk-dev

# Instalar OpenSeesPy
pip install openseespy==3.5.1.11
```

#### En macOS

```bash
# Instalar dependencias con Homebrew
brew install gcc gfortran openblas lapack tcl-tk

# Instalar OpenSeesPy
pip install openseespy==3.5.1.11
```

#### En Windows (instalación directa)

```bash
# OpenSeesPy tiene wheels precompilados para Windows
pip install openseespy==3.5.1.11

# Si falla, intenta esta versión alternativa:
pip install openseespy==3.4.0.1
```

#### En Windows con WSL2 (RECOMENDADO)

```bash
# Seguir instrucciones de Linux arriba
sudo apt install -y build-essential gfortran liblapack-dev libblas-dev
pip install openseespy==3.5.1.11
```

### Paso 4: Instalar GMSH

```bash
# GMSH es para generación de mallas
pip install gmsh==4.11.1
```

### Paso 5: Instalar PyVista (Visualización 3D)

```bash
# PyVista requiere VTK
pip install pyvista==0.43.0
```

### Paso 6: Instalar meshio

```bash
pip install meshio==5.3.4
```

### Paso 7: Instalar dependencias adicionales

```bash
# Matplotlib para gráficos 2D
pip install matplotlib==3.7.1

# SciPy para operaciones científicas
pip install scipy==1.10.1

# Pandas para manejo de datos (opcional pero útil)
pip install pandas==2.0.3
```

### Paso 8: Crear archivo requirements.txt (Opcional)

Para facilitar futuras instalaciones, puedes guardar todas las dependencias:

```bash
pip freeze > requirements.txt
```

### Instalación Rápida con requirements.txt

Si ya tienes un archivo `requirements.txt`, puedes instalar todo de una vez:

```bash
pip install -r requirements.txt
```

---

## ✅ Verificación de la Instalación

Ejecuta este script de Python para verificar que todo esté instalado correctamente:

```bash
python << 'EOF'
import sys
print(f"Python version: {sys.version}")

# Verificar cada paquete
packages = [
    ('numpy', 'NumPy'),
    ('openseespy.opensees', 'OpenSeesPy'),
    ('gmsh', 'GMSH'),
    ('pyvista', 'PyVista'),
    ('meshio', 'meshio'),
    ('matplotlib', 'Matplotlib'),
    ('scipy', 'SciPy')
]

print("\n" + "="*60)
print("VERIFICACIÓN DE PAQUETES INSTALADOS")
print("="*60)

all_ok = True
for module_name, display_name in packages:
    try:
        module = __import__(module_name)
        version = getattr(module, '__version__', 'versión desconocida')
        print(f"✅ {display_name:15} - {version}")
    except ImportError as e:
        print(f"❌ {display_name:15} - NO INSTALADO")
        all_ok = False

print("="*60)
if all_ok:
    print("🎉 ¡Todas las dependencias están instaladas correctamente!")
else:
    print("⚠️  Algunas dependencias faltan. Revisa los errores arriba.")
print("="*60)
EOF
```

---

## 🚀 Ejecutar el Proyecto

### Flujo de Trabajo Completo

El proyecto tiene un pipeline completo que genera mallas, ejecuta análisis y visualiza resultados.

#### 1. Configurar los Parámetros (Opcional)

Edita el archivo `mesh_config.json` o usa la configuración por defecto:

```bash
cat mesh_config.json
```

#### 2. Generar la Malla con GMSH

```bash
# Genera malla tetraédrica desde configuración
python generate_mesh_from_config.py

# Esto creará archivos en el directorio mallas/
```

#### 3. Convertir Malla a Formato OpenSees

```bash
# Convierte de GMSH a formato TCL de OpenSees
python gmsh_to_opensees.py

# Esto creará archivos en opensees_input/
```

#### 4. Ejecutar Análisis con OpenSees

```bash
# Ejecuta el análisis de elementos finitos
python run_opensees_analysis.py

# Los resultados se guardan en resultados_opensees/
```

#### 5. Visualizar Resultados

```bash
# Visualización interactiva con PyVista
python visualizar_resultados_opensees.py

# O solo exportar a ParaView sin ventana interactiva:
python visualizar_resultados_opensees.py --no-interactive
```

### Pipeline Automatizado

También puedes ejecutar todo el flujo automáticamente:

```bash
# Ejecuta generación de malla + conversión + análisis
python run_pipeline.py
```

### Ejemplos Específicos

#### Generar malla con configuración personalizada

```bash
python generate_mesh_from_config.py config_examples/ejemplo_2estratos.json
```

#### Análisis de convergencia

```bash
python convergence_study.py
```

#### Casos prácticos

```bash
python example_casos_practicos.py
```

---

## 🔧 Solución de Problemas Comunes

### Problema 1: Error al importar openseespy

**Error:**
```
ModuleNotFoundError: No module named 'openseespy'
```

**Soluciones:**

1. Verificar que el entorno virtual esté activado:
   ```bash
   which python  # Linux/macOS
   where python  # Windows
   # Debe mostrar ruta dentro de venv/
   ```

2. Reinstalar openseespy con versión específica:
   ```bash
   pip uninstall openseespy
   pip install openseespy==3.5.1.11
   ```

3. Si persiste en Linux, instalar dependencias del sistema:
   ```bash
   sudo apt install build-essential gfortran liblapack-dev libblas-dev
   ```

### Problema 2: Error "undefined symbol" con OpenSeesPy en Linux

**Error:**
```
ImportError: undefined symbol: _gfortran_...
```

**Solución:**
```bash
# Instalar gfortran
sudo apt install gfortran

# Reinstalar openseespy
pip uninstall openseespy
pip install openseespy==3.5.1.11
```

### Problema 3: PyVista no muestra ventanas

**En Linux sin interfaz gráfica (servidor remoto):**
```python
# Usar modo off-screen en el código
import pyvista as pv
pv.start_xvfb()  # Renderizado sin pantalla
```

O usar la opción de exportar directamente:
```bash
python visualizar_resultados_opensees.py --export-only
```

### Problema 4: Error con versión de Python

**Error:**
```
ERROR: Package 'openseespy' requires a different Python: 3.12.0 not in '>=3.9,<3.12'
```

**Solución:**
- Usar Python 3.9, 3.10 o 3.11 específicamente
- Desinstalar Python 3.12 y instalar 3.10

### Problema 5: pip no encuentra paquetes

**Solución:**
```bash
# Actualizar pip
pip install --upgrade pip

# Limpiar caché de pip
pip cache purge

# Intentar instalación de nuevo
pip install <paquete>
```

### Problema 6: Error de permisos en Linux

**Error:**
```
PermissionError: [Errno 13] Permission denied
```

**Solución:**
```bash
# NO usar sudo con pip dentro del venv
# En su lugar, asegúrate de que el venv esté activado
source venv/bin/activate

# Luego instalar normalmente
pip install <paquete>
```

### Problema 7: Problemas de memoria al ejecutar

**Si el análisis se queda sin memoria:**

1. Reducir refinamiento de malla en `mesh_config.json`:
   ```json
   "mesh_refinement": {
     "footing_size": 0.4,  // Aumentar (menos elementos)
     "soil_size": 1.0      // Aumentar (menos elementos)
   }
   ```

2. Usar modelo de cuarto de zapata (usa simetría):
   ```bash
   python generate_mesh_quarter.py
   ```

### Problema 8: GMSH no puede crear ventanas

**En servidores sin display:**
```python
# En el código, usar:
gmsh.option.setNumber("General.Terminal", 1)
# Ya está configurado en los scripts
```

### Problema 9: Versiones incompatibles

**Si hay conflictos de versiones:**

```bash
# Crear entorno virtual limpio
deactivate
rm -rf venv
python3.10 -m venv venv
source venv/bin/activate

# Instalar en orden estricto:
pip install --upgrade pip
pip install numpy==1.24.3
pip install openseespy==3.5.1.11
pip install gmsh==4.11.1
pip install pyvista==0.43.0
pip install meshio==5.3.4
pip install matplotlib==3.7.1
pip install scipy==1.10.1
```

---

## 📚 Recursos Adicionales

### Documentación de Bibliotecas

- **OpenSeesPy**: https://openseespydoc.readthedocs.io/
- **GMSH**: https://gmsh.info/doc/texinfo/gmsh.html
- **PyVista**: https://docs.pyvista.org/
- **NumPy**: https://numpy.org/doc/stable/

### Archivos de Ayuda del Proyecto

- `README.md` - Información general del proyecto
- `GUIA_RAPIDA.md` - Guía rápida de uso
- `VISUALIZACION.md` - Guía de visualización
- `REPORTE_IMPLEMENTACION.md` - Detalles técnicos

### Comunidad y Soporte

- **OpenSees Forum**: https://opensees.berkeley.edu/community/
- **GMSH Mailing List**: https://gmsh.info/

---

## 🎯 Resumen de Comandos Rápidos

### Setup Inicial (solo primera vez)

```bash
# 1. Clonar repositorio (si aún no lo tienes)
git clone <url-del-repo>
cd ZapataU_V1

# 2. Crear y activar entorno virtual
python3.10 -m venv venv
source venv/bin/activate  # Linux/macOS
# .\venv\Scripts\activate  # Windows

# 3. Instalar dependencias
pip install --upgrade pip
pip install numpy==1.24.3
pip install openseespy==3.5.1.11
pip install gmsh==4.11.1
pip install pyvista==0.43.0
pip install meshio==5.3.4
pip install matplotlib==3.7.1
pip install scipy==1.10.1

# 4. Verificar instalación
python -c "import openseespy.opensees; import gmsh; import pyvista; print('✅ Todo OK')"
```

### Workflow Diario

```bash
# 1. Activar entorno (cada vez que abres terminal)
source venv/bin/activate  # Linux/macOS

# 2. Ejecutar análisis completo
python run_pipeline.py

# 3. Ver resultados
python visualizar_resultados_opensees.py

# 4. Cuando termines
deactivate
```

---

## ⚙️ Variables de Entorno Opcionales

Para renderizado sin pantalla (servidores remotos):

```bash
# Linux
export PYVISTA_OFF_SCREEN=true
export DISPLAY=:99

# Luego ejecutar scripts normalmente
python visualizar_resultados_opensees.py
```

---

## 📝 Notas Importantes

1. **SIEMPRE activa el entorno virtual** antes de trabajar con el proyecto
2. **NO uses sudo con pip** cuando el entorno virtual esté activado
3. **Respeta las versiones especificadas** - versiones más nuevas pueden no ser compatibles
4. **Python 3.12+ NO es compatible** con OpenSeesPy actualmente
5. **En Windows, WSL2 es altamente recomendado** para evitar problemas con OpenSees

---

## 🆘 ¿Necesitas Ayuda?

Si sigues teniendo problemas después de seguir esta guía:

1. Verifica la sección de "Solución de Problemas Comunes" arriba
2. Revisa los logs de error completos
3. Verifica las versiones instaladas con `pip list`
4. Asegúrate de que el entorno virtual esté activado
5. Intenta crear un entorno virtual completamente nuevo

---

**Última actualización**: 2025-11-08
**Versión de esta guía**: 1.0
