# 🏗️ Sistema de Análisis de Zapatas 3D con OpenSees

**Versión 1.0** | **Noviembre 2024**

Sistema integrado para el análisis geotécnico-estructural de zapatas superficiales mediante elementos finitos 3D.

---

## 📌 ACCESO RÁPIDO

| Documento | Descripción |
|-----------|-------------|
| **[INSTALL_WINDOWS.md](INSTALL_WINDOWS.md)** | 🪟 Guía completa de instalación para Windows |
| **[MANUAL_USO.md](MANUAL_USO.md)** | 📖 Manual de usuario detallado |
| **[requirements.txt](requirements.txt)** | 📦 Lista de dependencias Python |
| **[mesh_config.json](mesh_config.json)** | ⚙️ Archivo de configuración del análisis |
| **[config.py](config.py)** | 🧱 Parámetros de materiales y cargas |

---

## 🎯 CARACTERÍSTICAS PRINCIPALES

### ✨ Capacidades

- ✅ **Mallas 3D automáticas** con GMSH (tetraedros de 4 nodos)
- ✅ **Análisis de elementos finitos** con OpenSeesPy
- ✅ **Zapatas rectangulares o cuadradas**
- ✅ **Múltiples estratos de suelo**
- ✅ **Análisis bifásico** (gravedad + carga)
- ✅ **Condiciones de simetría** (modelo de cuarto)
- ✅ **Visualización 3D interactiva** con PyVista
- ✅ **Exportación a ParaView** (formato VTU)
- ✅ **Reportes automáticos** en formato texto

### 🔧 Tecnologías Utilizadas

| Componente | Librería | Función |
|------------|----------|---------|
| Generación de mallas | GMSH 4.11.1 | Crear geometría y discretización 3D |
| Análisis FEM | OpenSeesPy 3.5.1 | Análisis de elementos finitos |
| Visualización | PyVista 0.43 | Renderizado 3D y exports VTU |
| Procesamiento | NumPy/SciPy | Álgebra lineal y cálculos |
| Conversión | MeshIO 5.3 | Manejo de formatos de malla |

---

## 🚀 INICIO RÁPIDO

### 1️⃣ Instalación (Windows)

```cmd
:: Instalar Python 3.10 desde python.org

:: Instalar Visual C++ Redistributable
:: https://aka.ms/vs/17/release/vc_redist.x64.exe

:: Clonar repositorio
git clone <URL-del-repo>
cd ZapataU_V1

:: Crear entorno virtual
python -m venv venv
venv\Scripts\activate

:: Instalar dependencias
pip install -r requirements.txt
```

**Ver detalles en:** [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md)

### 2️⃣ Verificar Instalación

```cmd
python verificar_instalacion.py
```

Debe mostrar `✅` para todas las dependencias.

### 3️⃣ Ejecutar Análisis de Ejemplo

```cmd
python run_full_analysis.py
```

Esto ejecuta el pipeline completo:
1. Verificación de dependencias ✓
2. Generación de malla 3D ✓
3. Conversión a OpenSees ✓
4. Verificación de contacto zapata-suelo ✓
5. Análisis estructural ✓
6. Generación de visualizaciones ✓
7. Creación de reporte ✓

### 4️⃣ Revisar Resultados

```
resultados_opensees/
├── REPORTE_ANALISIS.txt       ← EMPIEZA AQUÍ
├── estadisticas.txt
├── desplazamientos.csv
├── tensiones.csv
└── resultados_opensees.vtu    ← Abrir con ParaView
```

---

## 📂 ESTRUCTURA DEL PROYECTO

```
ZapataU_V1/
│
├── 📄 Documentación
│   ├── README_SISTEMA_COMPLETO.md   (este archivo)
│   ├── INSTALL_WINDOWS.md           (instalación Windows)
│   ├── MANUAL_USO.md                (manual detallado)
│   └── requirements.txt             (dependencias)
│
├── ⚙️ Configuración
│   ├── mesh_config.json             (geometría y malla)
│   └── config.py                    (materiales y cargas)
│
├── 🎮 Scripts Principales
│   ├── run_full_analysis.py         ⭐ SCRIPT MAESTRO
│   ├── verificar_instalacion.py    (check instalación)
│   └── setup_windows.bat            (instalador Windows)
│
├── 🔨 Pipeline de Análisis
│   ├── generate_mesh_from_config.py (genera malla GMSH)
│   ├── gmsh_to_opensees.py          (convierte a OpenSees)
│   ├── verificar_contacto_zapata_suelo.py
│   ├── run_opensees_analysis.py     (análisis FEM)
│   └── visualizar_resultados_opensees.py
│
├── 📊 Salidas
│   ├── mallas/                      (mallas .vtu, .msh)
│   ├── opensees_input/              (archivos .tcl)
│   └── resultados_opensees/         (resultados análisis)
│
└── 🗂️ Otros
    ├── visualize_*.py               (scripts visualización)
    └── *.py                         (utilidades)
```

---

## 💻 REQUISITOS DEL SISTEMA

### Hardware Mínimo

- **CPU:** 4 cores
- **RAM:** 8 GB
- **Disco:** 5 GB libres
- **GPU:** OpenGL 3.0+

### Hardware Recomendado

- **CPU:** 8+ cores
- **RAM:** 16-32 GB
- **Disco:** SSD con 10 GB
- **GPU:** NVIDIA/AMD con OpenGL 4.5+

### Software

- **OS:** Windows 10/11, Linux (Ubuntu 20.04+)
- **Python:** 3.9, 3.10 (recomendado) o 3.11
  - ⚠️ **NO Python 3.12+** (incompatible con OpenSees)
- **Espacio:** ~3 GB para Python y librerías

---

## 📚 GUÍAS COMPLETAS

### 🪟 Para Usuarios de Windows

1. **Lee primero:** [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md)
   - Instalación paso a paso
   - Solución de problemas comunes
   - Instalación alternativa con Conda

2. **Instalación rápida:**
   ```cmd
   :: Ejecutar como Administrador
   setup_windows.bat
   ```

3. **Verificar:**
   ```cmd
   python verificar_instalacion.py
   ```

### 📖 Manual de Usuario

**Lee:** [MANUAL_USO.md](MANUAL_USO.md)

Incluye:
- Configuración de análisis
- Definición de geometría
- Parámetros de materiales
- Interpretación de resultados
- Ejemplos prácticos
- Casos de uso avanzados

---

## 🎓 EJEMPLO DE USO BÁSICO

### Configurar Análisis

**1. Editar `mesh_config.json`:**

```json
{
  "geometry": {
    "footing": {
      "B": 2.0,        // Ancho (m)
      "L": 3.0,        // Largo (m)
      "Df": 1.5,       // Profundidad de desplante (m)
      "tz": 0.4        // Espesor zapata (m)
    }
  },
  "soil_layers": [
    {"name": "SUELO_1", "thickness": 3.0, "material_id": 1},
    {"name": "SUELO_2", "thickness": 10.0, "material_id": 2},
    {"name": "SUELO_3", "thickness": 7.0, "material_id": 3}
  ]
}
```

**2. Editar `config.py`:**

```python
ESTRATOS_SUELO = [
    {'nombre': 'Arena', 'E': 5_000, 'nu': 0.3, 'rho': 1800},
    {'nombre': 'Arcilla', 'E': 20_000, 'nu': 0.3, 'rho': 1800},
    {'nombre': 'Grava', 'E': 50_000, 'nu': 0.3, 'rho': 1900}
]

CARGAS = {'P_column': 1000.0}  # kN
```

### Ejecutar

```cmd
python run_full_analysis.py
```

### Resultados

```
================================================================================
  RESUMEN FINAL
================================================================================

✅ Pipeline completado exitosamente!
   Pasos completados: 7/7

📊 RESULTADOS:
--------------------------------------------------------------------------------
   Máximo (asentamiento): 0.025639 m = 25.639 mm

📂 ARCHIVOS PRINCIPALES:
--------------------------------------------------------------------------------
   Malla: mallas/zapata_3D_cuarto_refined.vtu
   Resultados: resultados_opensees/
   Reporte: resultados_opensees/REPORTE_ANALISIS.txt
   ParaView: resultados_opensees/resultados_opensees.vtu
```

---

## 🎨 VISUALIZACIÓN DE RESULTADOS

### Opción 1: ParaView (Recomendado)

```cmd
:: Instalar desde: https://www.paraview.org/download/

:: Abrir archivo VTU
paraview resultados_opensees/resultados_opensees.vtu
```

**Campos disponibles:**
- `Uz` → Desplazamiento vertical (asentamiento)
- `Displacement_Magnitude` → Magnitud total
- `Von_Mises_Stress` → Tensión de von Mises
- `Material_ID` → Identificar zapata y estratos

### Opción 2: Python (Interactivo)

```cmd
python visualizar_resultados_opensees.py
```

Abre ventana 3D interactiva con los resultados.

---

## 🔧 OPCIONES AVANZADAS

### Análisis con Configuración Personalizada

```cmd
python run_full_analysis.py --config mi_zapata.json
```

### Solo Generar Malla (Sin Analizar)

```cmd
python run_full_analysis.py --skip-analysis
```

### Usar Malla Existente (Solo Analizar)

```cmd
python run_full_analysis.py --skip-mesh
```

### Modo Verboso (Debugging)

```cmd
python run_full_analysis.py --verbose
```

### Ejecución Manual Paso a Paso

```cmd
python generate_mesh_from_config.py mesh_config.json
python gmsh_to_opensees.py mallas/zapata_3D_cuarto_refined.vtu
python run_opensees_analysis.py
python visualizar_resultados_opensees.py --export-only
```

---

## ❓ SOLUCIÓN DE PROBLEMAS

### OpenSeesPy no se instala en Windows

**Síntoma:**
```
ERROR: Could not install openseespy
```

**Soluciones:**

1. **Instalar Visual C++ Redistributable:**
   https://aka.ms/vs/17/release/vc_redist.x64.exe

2. **Usar Python 3.10:**
   ```cmd
   python --version  # Debe ser 3.10.x
   ```

3. **Versión anterior de OpenSeesPy:**
   ```cmd
   pip install openseespy==3.4.0.1
   ```

4. **Usar Conda (más confiable):**
   ```cmd
   conda install -c conda-forge openseespy
   ```

Ver más en: [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md#-solución-de-problemas)

---

## 📊 ARCHIVOS DE RESULTADOS

| Archivo | Descripción |
|---------|-------------|
| `REPORTE_ANALISIS.txt` | Reporte completo del análisis |
| `estadisticas.txt` | Resumen de resultados clave |
| `desplazamientos.csv` | Desplazamientos de todos los nodos |
| `tensiones.csv` | Tensiones en todos los elementos |
| `reacciones.csv` | Reacciones en apoyos |
| `resultados_opensees.vtu` | Archivo para ParaView |

### Formato de Archivos CSV

**desplazamientos.csv:**
```
node,x,y,z,ux,uy,uz,u_total
1,0.0,0.0,-3.0,-0.001,0.0,-0.002,0.0022
```

**tensiones.csv:**
```
elem,sxx,syy,szz,sxy,syz,szx,von_mises
1,123.4,-56.7,-345.6,12.3,5.6,2.3,345.6
```

---

## 🎯 CASOS DE USO

### 1. Diseño de Zapata Nueva

- Configurar geometría y estratos de suelo
- Definir propiedades de materiales según ensayos
- Ejecutar análisis
- Verificar que asentamiento < límite permisible
- Ajustar dimensiones si necesario

### 2. Verificación de Zapata Existente

- Modelar geometría real
- Usar parámetros de suelo del sitio
- Aplicar cargas de servicio
- Verificar capacidad y asentamientos

### 3. Estudio Paramétrico

- Variar profundidad de desplante
- Variar dimensiones en planta
- Comparar diferentes estratigrafías
- Optimizar diseño

### 4. Análisis de Sensibilidad

- Variar módulo de elasticidad del suelo (±30%)
- Evaluar impacto en asentamientos
- Determinar parámetros más influyentes

---

## 📞 SOPORTE

### Documentación

- **README_SISTEMA_COMPLETO.md** (este archivo)
- **INSTALL_WINDOWS.md** - Instalación detallada
- **MANUAL_USO.md** - Manual completo de usuario
- **Comments en código** - Todos los scripts están comentados

### Reportar Problemas

1. Verificar instalación: `python verificar_instalacion.py`
2. Ejecutar con `--verbose` para más información
3. Revisar [INSTALL_WINDOWS.md](INSTALL_WINDOWS.md#-solución-de-problemas)
4. Documentar error completo con versiones de librerías

---

## 📝 NOTAS IMPORTANTES

### ⚠️ Limitaciones Actuales

- Modelo constitutivo: **Elástico lineal**
  - Para análisis más avanzado, modificar `run_opensees_analysis.py`
  - Considerar modelos como `PressureDependMultiYield` para suelos

- Geometría: **Solo zapatas rectangulares/cuadradas**
  - Para zapatas circulares, aproximar con cuadrado equivalente

- Carga: **Centrada y vertical**
  - Para momentos, modificar `aplicar_cargas()` en script de análisis

### ✅ Validación de Resultados

**IMPORTANTE:** Los resultados son tan buenos como:

1. **Calidad de parámetros de suelo** (lo más crítico)
   - Usar ensayos de laboratorio cuando sea posible
   - SPT, CPT, ensayos triaxiales, etc.

2. **Refinamiento de malla**
   - Hacer estudio de convergencia
   - Verificar que resultados no cambien con malla más fina

3. **Modelo constitutivo**
   - Elástico lineal es apropiado para cargas de servicio
   - Para análisis de falla, usar modelos no-lineales

---

## 🏆 VENTAJAS DE ESTE SISTEMA

✅ **Pipeline automatizado** - Un solo comando ejecuta todo
✅ **Configuración JSON** - Fácil de entender y modificar
✅ **Verificaciones integradas** - Chequea contacto zapata-suelo
✅ **Análisis bifásico** - Separa peso propio y carga aplicada
✅ **Visualización profesional** - Compatible con ParaView
✅ **Reportes automáticos** - Resumen de resultados en texto
✅ **Código abierto** - Modificable para necesidades específicas

---

## 📅 VERSIONES Y ACTUALIZACIONES

### Versión 1.0 (Noviembre 2024)

- ✅ Pipeline completo funcional
- ✅ Documentación completa
- ✅ Instalador para Windows
- ✅ Ejemplos y casos de uso
- ✅ Soporte para Python 3.9-3.11

### Próximas Mejoras (Roadmap)

- 🔲 Modelos constitutivos avanzados de suelos
- 🔲 Análisis no-lineal
- 🔲 Zapatas circulares
- 🔲 Cargas excéntricas y momentos
- 🔲 Interfaz gráfica (GUI)
- 🔲 Optimización automática de diseño

---

## 📄 LICENCIA

Ver archivo LICENSE para detalles.

## 🙏 CRÉDITOS

### Librerías de Terceros

- **OpenSeesPy** - Pacific Earthquake Engineering Research Center
- **GMSH** - Christophe Geuzaine y Jean-François Remacle
- **PyVista** - PyVista Developers
- **NumPy/SciPy** - NumPy/SciPy Communities

---

**Desarrollado para análisis geotécnico-estructural**

**Última actualización:** Noviembre 2024
**Versión:** 1.0

---

🎉 **¡Listo para analizar zapatas!**

```cmd
python run_full_analysis.py
```
