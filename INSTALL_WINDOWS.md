# 📦 GUÍA DE INSTALACIÓN PARA WINDOWS

## Sistema de Análisis de Zapatas 3D con OpenSees

**Versión:** 1.0
**Fecha:** Noviembre 2024
**Compatible con:** Windows 10 y Windows 11

---

## 📋 TABLA DE CONTENIDOS

1. [Requisitos del Sistema](#-requisitos-del-sistema)
2. [Instalación Paso a Paso](#-instalación-paso-a-paso)
3. [Verificación de Instalación](#-verificación-de-instalación)
4. [Solución de Problemas](#-solución-de-problemas)
5. [Instalación Alternativa (Conda)](#-instalación-alternativa-conda)
6. [Primeros Pasos](#-primeros-pasos)

---

## 💻 REQUISITOS DEL SISTEMA

### Hardware Mínimo

- **CPU:** Intel Core i5 o AMD Ryzen 5 (4 cores)
- **RAM:** 8 GB mínimo, 16 GB recomendado
- **Disco:** 5 GB de espacio libre
- **GPU:** Compatible con OpenGL 3.0+ (para visualización)

### Hardware Recomendado

- **CPU:** Intel Core i7/i9 o AMD Ryzen 7/9 (8+ cores)
- **RAM:** 16-32 GB
- **Disco:** SSD con 10 GB libres
- **GPU:** NVIDIA/AMD dedicada con OpenGL 4.5+

### Software Base

- **Windows:** 10 (versión 1903 o superior) o Windows 11
- **Python:** 3.10.x (RECOMENDADO) o 3.9.x / 3.11.x
  - ⚠️ **NO usar Python 3.12+** (incompatible con OpenSeesPy)
- **Espacio:** ~2-3 GB para Python y librerías

---

## 🚀 INSTALACIÓN PASO A PASO

### PASO 1: Instalar Python 3.10

1. **Descargar Python 3.10:**
   - Ve a: https://www.python.org/downloads/release/python-31011/
   - Descarga: "Windows installer (64-bit)"

2. **Instalar Python:**
   ```
   ✅ Marcar "Add Python 3.10 to PATH"
   ✅ Marcar "Install for all users" (opcional)
   ✅ Usar "Customize installation"
   ✅ Marcar "pip", "tcl/tk", "Python test suite"
   ✅ Marcar "Associate files with Python"
   ```

3. **Verificar instalación:**
   ```cmd
   python --version
   ```
   Debe mostrar: `Python 3.10.11` (o similar)

### PASO 2: Instalar Visual C++ Redistributable

**⚠️ CRÍTICO:** OpenSeesPy requiere Visual C++ para funcionar en Windows.

1. **Descargar:**
   - Enlace directo: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - O buscar: "Visual C++ Redistributable 2015-2022"

2. **Instalar:**
   - Ejecutar el instalador descargado
   - Reiniciar Windows si lo solicita

3. **Verificar:**
   - Buscar en "Agregar o quitar programas"
   - Debe aparecer: "Microsoft Visual C++ 2015-2022 Redistributable (x64)"

### PASO 3: Actualizar pip y herramientas

Abrir **PowerShell** o **CMD** como **Administrador** y ejecutar:

```cmd
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel
```

### PASO 4: Crear entorno virtual (RECOMENDADO)

Es altamente recomendable usar un entorno virtual para evitar conflictos:

```cmd
cd C:\Users\TuUsuario\Documents
mkdir ZapataU_V1
cd ZapataU_V1

python -m venv venv

:: Activar entorno virtual
venv\Scripts\activate
```

Verás `(venv)` al inicio de la línea de comandos.

### PASO 5: Clonar o descargar el proyecto

**Opción A - Con Git:**

```cmd
git clone <URL-del-repositorio> .
```

**Opción B - Sin Git (manual):**

1. Descargar el proyecto como ZIP
2. Extraer en `C:\Users\TuUsuario\Documents\ZapataU_V1`

### PASO 6: Instalar dependencias Python

**Método Recomendado** (paso a paso, más seguro):

```cmd
:: Instalar numpy primero (base de todo)
pip install numpy==1.24.3

:: Instalar librerías científicas
pip install scipy==1.10.1
pip install pandas==2.0.3

:: Instalar GMSH (generación de mallas)
pip install gmsh==4.11.1

:: Instalar VTK y PyVista (visualización)
pip install vtk==9.2.6
pip install pyvista==0.43.0

:: Instalar MeshIO (conversión de mallas)
pip install meshio==5.3.4
pip install h5py

:: Instalar Matplotlib (gráficos)
pip install matplotlib==3.7.1

:: Instalar utilidades
pip install tqdm colorama

:: FINALMENTE instalar OpenSeesPy (lo más problemático)
pip install openseespy==3.5.1.11
```

**Método Rápido** (puede dar errores):

```cmd
pip install -r requirements.txt
```

Si da error, volver al método paso a paso.

### PASO 7: Verificar instalación de OpenSeesPy

Este es el paso más crítico. Ejecutar:

```cmd
python -c "import openseespy.opensees as ops; print('OpenSees OK')"
```

**Si funciona:** Verás `OpenSees OK` ✅

**Si falla:** Ver sección [Solución de Problemas](#-solución-de-problemas)

### PASO 8: Verificar todas las dependencias

Ejecutar el verificador automático:

```cmd
python run_full_analysis.py --help
```

Debe mostrar ayuda sin errores.

O crear un script de verificación:

```python
# verificar_instalacion.py
import sys

modules = [
    'numpy',
    'scipy',
    'gmsh',
    'pyvista',
    'vtk',
    'meshio',
    'matplotlib',
    'openseespy.opensees'
]

print("Verificando instalación...\n")
todos_ok = True

for module in modules:
    try:
        __import__(module)
        print(f"✅ {module}")
    except ImportError as e:
        print(f"❌ {module}: {e}")
        todos_ok = False

if todos_ok:
    print("\n🎉 ¡Todas las dependencias instaladas correctamente!")
else:
    print("\n⚠️  Algunas dependencias faltan. Ver errores arriba.")

```

Ejecutar:

```cmd
python verificar_instalacion.py
```

---

## ✅ VERIFICACIÓN DE INSTALACIÓN

### Test rápido completo

```cmd
:: Activar entorno virtual
venv\Scripts\activate

:: Ejecutar análisis de ejemplo
python run_full_analysis.py --help
```

Debe mostrar el menú de ayuda completo.

### Test de análisis completo

```cmd
python run_full_analysis.py
```

Debe ejecutar todo el pipeline:
1. ✅ Verificar dependencias
2. ✅ Generar malla 3D
3. ✅ Convertir a OpenSees
4. ✅ Verificar contacto
5. ✅ Ejecutar análisis
6. ✅ Generar visualizaciones
7. ✅ Crear reporte

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### Problema 1: "Python no se reconoce como comando"

**Síntoma:**
```
'python' no se reconoce como un comando interno o externo...
```

**Solución:**

1. Reinstalar Python marcando "Add to PATH"
2. O agregar manualmente a PATH:
   ```
   C:\Users\TuUsuario\AppData\Local\Programs\Python\Python310
   C:\Users\TuUsuario\AppData\Local\Programs\Python\Python310\Scripts
   ```

### Problema 2: "Microsoft Visual C++ 14.0 is required"

**Síntoma:**
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**Solución:**

Instalar Visual C++ Redistributable (ver PASO 2) y reiniciar.

### Problema 3: OpenSeesPy no se instala

**Síntoma:**
```
ERROR: Could not find a version that satisfies the requirement openseespy
```

**Soluciones:**

**Opción 1:** Usar versión anterior de OpenSeesPy:

```cmd
pip install openseespy==3.4.0.1
```

**Opción 2:** Verificar versión de Python:

```cmd
python --version
```

Si es 3.12+, desinstalar e instalar Python 3.10.

**Opción 3:** Usar Conda (ver sección [Instalación Alternativa](#-instalación-alternativa-conda))

**Opción 4:** Compilar desde fuente (avanzado):

```cmd
pip install --no-binary :all: openseespy
```

### Problema 4: "DLL load failed" al importar OpenSeesPy

**Síntoma:**
```
ImportError: DLL load failed while importing opensees
```

**Soluciones:**

1. **Instalar Visual C++ Redistributable** (PASO 2)
2. **Reiniciar la computadora**
3. **Verificar arquitectura:**
   ```cmd
   python -c "import sys; print(sys.maxsize > 2**32)"
   ```
   Debe ser `True` (64-bit)

4. **Reinstalar OpenSeesPy:**
   ```cmd
   pip uninstall openseespy
   pip install openseespy==3.5.1.11
   ```

### Problema 5: VTK/PyVista dan errores de OpenGL

**Síntoma:**
```
ERROR: VTK/OpenGL not found or insufficient version
```

**Soluciones:**

1. **Actualizar drivers de GPU:**
   - NVIDIA: https://www.nvidia.com/Download/index.aspx
   - AMD: https://www.amd.com/support
   - Intel: https://www.intel.com/content/www/us/en/download-center/home.html

2. **Usar modo software rendering:**
   ```cmd
   set MESA_GL_VERSION_OVERRIDE=3.3
   python run_full_analysis.py
   ```

3. **Usar solo exportación (sin visualización interactiva):**
   ```cmd
   python run_full_analysis.py --export-only
   ```

### Problema 6: Errores de memoria en mallas grandes

**Síntoma:**
```
MemoryError: Unable to allocate array
```

**Soluciones:**

1. **Reducir refinamiento** en `mesh_config.json`:
   ```json
   "mesh_refinement": {
       "lc_footing": 0.5,    // aumentar (menos elementos)
       "lc_near": 0.8,
       "lc_far": 3.0
   }
   ```

2. **Cerrar otras aplicaciones**

3. **Usar computadora con más RAM**

4. **Analizar por partes** (dividir el modelo)

### Problema 7: Firewall o Antivirus bloquean Python

**Síntoma:**
Scripts se cierran inesperadamente o dan timeout.

**Solución:**

Agregar excepciones en Windows Defender:

1. Configuración → Privacidad y seguridad → Seguridad de Windows
2. Protección contra virus y amenazas → Configuración
3. Agregar exclusión → Carpeta
4. Seleccionar: `C:\Users\TuUsuario\Documents\ZapataU_V1`

---

## 🐍 INSTALACIÓN ALTERNATIVA (CONDA)

Si tienes problemas con pip, usar **Anaconda** o **Miniconda**:

### Instalar Miniconda

1. Descargar: https://docs.conda.io/en/latest/miniconda.html
2. Instalar (marcar "Add to PATH")

### Crear entorno con Conda

```cmd
:: Crear entorno con Python 3.10
conda create -n zapatau python=3.10

:: Activar entorno
conda activate zapatau

:: Instalar dependencias principales desde conda-forge
conda install -c conda-forge numpy scipy matplotlib pandas
conda install -c conda-forge gmsh pyvista vtk meshio h5py

:: Instalar OpenSeesPy desde conda-forge (más confiable que pip)
conda install -c conda-forge openseespy

:: Verificar
python -c "import openseespy.opensees as ops; print('OK')"
```

### Ventajas de Conda

✅ Manejo automático de dependencias binarias
✅ No requiere Visual C++ compilar
✅ Entornos aislados más robustos
✅ Mejor compatibilidad con OpenSeesPy en Windows

---

## 🎓 PRIMEROS PASOS

Una vez instalado todo:

### 1. Abrir terminal en la carpeta del proyecto

```cmd
cd C:\Users\TuUsuario\Documents\ZapataU_V1
venv\Scripts\activate    :: o: conda activate zapatau
```

### 2. Verificar configuración

```cmd
python run_full_analysis.py --help
```

### 3. Ejecutar análisis de ejemplo

```cmd
python run_full_analysis.py
```

Esto ejecutará un análisis completo con la configuración por defecto en `mesh_config.json`.

### 4. Revisar resultados

Archivos generados en:
- `mallas/` - Mallas 3D generadas
- `opensees_input/` - Archivos de entrada OpenSees
- `resultados_opensees/` - Resultados del análisis
  - `desplazamientos.csv`
  - `tensiones.csv`
  - `resultados_opensees.vtu` (abrir con ParaView)
  - `REPORTE_ANALISIS.txt`

### 5. Visualizar en ParaView (opcional)

1. Instalar ParaView: https://www.paraview.org/download/
2. Abrir archivo: `resultados_opensees/resultados_opensees.vtu`
3. Seleccionar campo a visualizar (Uz, Von_Mises_Stress, etc.)

---

## 📞 SOPORTE

### Documentación Adicional

- **README.md** - Descripción general del proyecto
- **MANUAL_USO.md** - Manual de usuario detallado
- **mesh_config.json** - Configuración de mallas (comentado)
- **config.py** - Parámetros de materiales y cargas

### Problemas Comunes

Consultar: [Solución de Problemas](#-solución-de-problemas)

### Reporte de Errores

Si encuentras un error no documentado:

1. Verificar que todas las dependencias están instaladas
2. Ejecutar con `--verbose` para más información
3. Guardar el mensaje de error completo
4. Revisar compatibilidad de versiones

---

## 📝 NOTAS IMPORTANTES

### Versiones de Python

- ✅ **Python 3.9.x** - Funciona
- ✅ **Python 3.10.x** - **RECOMENDADO**
- ✅ **Python 3.11.x** - Funciona (puede tener problemas con OpenSeesPy)
- ❌ **Python 3.12+** - **NO COMPATIBLE** con OpenSeesPy

### Compatibilidad de Windows

- ✅ Windows 10 (build 1903+)
- ✅ Windows 11
- ⚠️ Windows 7/8 - No probado, puede requerir ajustes

### Requisitos de OpenGL

PyVista requiere OpenGL 3.0+:
- Verificar con: `python -c "import pyvista; pv.Report()"`
- Si no funciona, usar `--export-only` (sin visualización interactiva)

---

## ✨ LICENCIA Y CRÉDITOS

Sistema desarrollado para análisis geotécnico-estructural de zapatas superficiales.

**Librerías utilizadas:**
- OpenSeesPy - Análisis de elementos finitos
- GMSH - Generación de mallas
- PyVista - Visualización 3D
- NumPy, SciPy - Computación científica

---

**Fecha de actualización:** Noviembre 2024
**Versión del documento:** 1.0
