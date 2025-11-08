# 🚀 Inicio Rápido - ZapataU_V1

Guía ultra-rápida para poner en marcha el proyecto en 5 minutos.

---

## ⚡ Instalación Express

### Linux/macOS (Automatizada)

```bash
# 1. Clonar proyecto (si no lo tienes)
git clone <url-del-repo>
cd ZapataU_V1

# 2. Ejecutar instalación automatizada
chmod +x setup.sh
./setup.sh

# ¡Listo! El script hace todo por ti
```

### Windows

```powershell
# Opción A: Instalación automatizada (PowerShell)
.\setup.ps1

# Opción B: WSL2 (RECOMENDADO)
# 1. Instalar WSL2
wsl --install

# 2. Abrir Ubuntu y seguir pasos de Linux
```

### Instalación Manual Rápida

```bash
# 1. Crear entorno virtual
python3.10 -m venv venv
source venv/bin/activate  # Linux/macOS
# .\venv\Scripts\activate  # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Verificar
python verificar_instalacion.py
```

---

## 🎯 Primeros Pasos

### Verificar Instalación

```bash
# Activar entorno virtual
source venv/bin/activate  # Linux/macOS

# Ejecutar verificación
python verificar_instalacion.py
```

### Ejecutar Análisis Completo

```bash
# Pipeline completo (recomendado para empezar)
python run_pipeline.py

# Esto ejecuta:
# 1. Generación de malla con GMSH
# 2. Conversión a formato OpenSees
# 3. Análisis de elementos finitos
# 4. Exportación de resultados
```

### Visualizar Resultados

```bash
# Visualización 3D interactiva
python visualizar_resultados_opensees.py

# O exportar a ParaView sin visualizar
python visualizar_resultados_opensees.py --export-only
```

---

## 📊 Flujo de Trabajo Típico

```bash
# 1. Activar entorno (siempre primero)
source venv/bin/activate

# 2. Editar configuración (opcional)
nano mesh_config.json

# 3. Generar malla
python generate_mesh_from_config.py

# 4. Convertir a OpenSees
python gmsh_to_opensees.py

# 5. Ejecutar análisis
python run_opensees_analysis.py

# 6. Ver resultados
python visualizar_resultados_opensees.py

# 7. Desactivar cuando termines
deactivate
```

---

## 🔑 Comandos Esenciales

| Comando | Descripción |
|---------|-------------|
| `source venv/bin/activate` | Activar entorno virtual |
| `python verificar_instalacion.py` | Verificar configuración |
| `python run_pipeline.py` | Pipeline completo automatizado |
| `python visualizar_resultados_opensees.py` | Ver resultados 3D |
| `deactivate` | Desactivar entorno virtual |

---

## ⚠️ Problemas Comunes

### Error: ModuleNotFoundError

```bash
# Solución: Activar entorno virtual
source venv/bin/activate
```

### Error con OpenSeesPy en Linux

```bash
# Instalar dependencias del sistema
sudo apt install build-essential gfortran liblapack-dev libblas-dev

# Reinstalar OpenSeesPy
pip uninstall openseespy
pip install openseespy==3.5.1.11
```

### PyVista no muestra ventanas

```bash
# Usar modo sin pantalla
python visualizar_resultados_opensees.py --no-interactive
```

---

## 📂 Estructura de Archivos

```
ZapataU_V1/
├── INSTALACION.md          # Guía de instalación completa
├── QUICKSTART.md           # Esta guía rápida (estás aquí)
├── README.md               # Documentación principal
│
├── setup.sh                # Script de instalación (Linux/macOS)
├── setup.ps1               # Script de instalación (Windows)
├── verificar_instalacion.py # Verificador de dependencias
├── requirements.txt        # Dependencias de Python
│
├── config.py               # Configuración del proyecto
├── mesh_config.json        # Configuración de mallas
│
├── run_pipeline.py         # Pipeline automatizado
├── generate_mesh_from_config.py  # Generador de mallas
├── gmsh_to_opensees.py     # Convertidor a OpenSees
├── run_opensees_analysis.py      # Análisis FEM
├── visualizar_resultados_opensees.py  # Visualización
│
├── mallas/                 # Mallas generadas
├── opensees_input/         # Archivos de entrada OpenSees
└── resultados_opensees/    # Resultados del análisis
```

---

## 🎓 Aprende Más

- **Instalación detallada**: Ver `INSTALACION.md`
- **Documentación completa**: Ver `README.md`
- **Visualización**: Ver `VISUALIZACION.md`
- **Solución de problemas**: Ver sección en `INSTALACION.md`

---

## 💡 Consejos Pro

### Análisis Rápido (malla gruesa)

```bash
# Editar mesh_config.json
# Aumentar tamaños de elemento:
# "footing_size": 0.5
# "soil_size": 2.0

python run_pipeline.py
```

### Análisis Detallado (malla fina)

```bash
# Editar mesh_config.json
# Reducir tamaños de elemento:
# "footing_size": 0.15
# "soil_size": 0.5

python run_pipeline.py
```

### Exportar a ParaView

```bash
# Los resultados se exportan automáticamente a:
# resultados_opensees/resultados_opensees.vtu

# Abrir con ParaView:
paraview resultados_opensees/resultados_opensees.vtu
```

---

## 🐛 Debug

### Ver logs detallados

Los archivos de análisis guardan información en:
- `analisis_output.log`
- `resultados_opensees/*.txt`

### Verificar malla generada

```bash
# Visualizar malla antes del análisis
python visualizar_problema.py
```

---

## 📞 Ayuda

Si encuentras problemas:

1. ✅ Revisa `INSTALACION.md` - Solución de problemas
2. ✅ Ejecuta `python verificar_instalacion.py`
3. ✅ Verifica que el entorno virtual esté activado
4. ✅ Revisa las versiones con `pip list`

---

**¡Listo para empezar!** 🚀

```bash
source venv/bin/activate
python run_pipeline.py
```
