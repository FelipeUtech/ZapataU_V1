# ============================================
# EJEMPLO DE USO DE MALLA EN OPENSEES
# ============================================
# Este es un script de ejemplo que muestra cómo usar
# los archivos generados por gmsh_to_opensees.py
#
# Para ejecutar:
#   OpenSees example_opensees.tcl
# ============================================

# Limpiar modelo previo
wipe

# Crear modelo básico
# -ndm 3: 3 dimensiones
# -ndf 3: 3 grados de libertad por nodo (ux, uy, uz)
model BasicBuilder -ndm 3 -ndf 3

puts "Cargando definiciones de malla..."

# ============================================
# CARGAR DEFINICIONES DE MALLA
# ============================================

# 1. Materiales (EDITAR ANTES DE USAR!)
puts "  - Materiales..."
source materials.tcl

# 2. Nodos
puts "  - Nodos..."
source nodes.tcl

# 3. Elementos
puts "  - Elementos..."
source elements.tcl

puts "Malla cargada exitosamente!"
puts ""

# ============================================
# CONDICIONES DE FRONTERA
# ============================================

puts "Aplicando condiciones de frontera..."

# Base fija (z = -20.0 m)
fixZ -20.0 1 1 1
puts "  - Base fija en z = -20.0 m"

# Simetría en X = 0 (cuarto de modelo)
# Restringir desplazamiento en X
fixX 0.0 1 0 0
puts "  - Simetría en X = 0.0"

# Simetría en Y = 0 (cuarto de modelo)
# Restringir desplazamiento en Y
fixY 0.0 0 1 0
puts "  - Simetría en Y = 0.0"

puts "Condiciones de frontera aplicadas!"
puts ""

# ============================================
# CARGAS
# ============================================

puts "Aplicando cargas..."

# Crear patrón de carga
pattern Plain 1 Linear {

    # Aplicar carga vertical sobre nodos de la superficie de la zapata
    # IMPORTANTE: Ajustar estos valores según tu caso

    # Carga total Q (kN)
    set Q 500.0

    # Número aproximado de nodos en superficie (ajustar)
    set nNodesTop 20

    # Carga por nodo
    set loadPerNode [expr -$Q / $nNodesTop]

    puts "  Carga total: $Q kN"
    puts "  Carga por nodo: $loadPerNode kN"

    # OPCIÓN 1: Aplicar a nodos específicos (DESCOMENTAR Y AJUSTAR)
    # load 17 0.0 0.0 $loadPerNode
    # load 19 0.0 0.0 $loadPerNode
    # ... (agregar más nodos)

    # OPCIÓN 2: Aplicar a todos los nodos en z = 0 (superficie)
    # (Requiere identificar nodos primero)

    puts "  ⚠️  ADVERTENCIA: Debes especificar nodos de carga manualmente!"
}

puts "Cargas definidas!"
puts ""

# ============================================
# CONFIGURACIÓN DEL ANÁLISIS
# ============================================

puts "Configurando análisis..."

# Sistema de ecuaciones
constraints Plain
numberer RCM
system BandGeneral

# Convergencia
test NormDispIncr 1.0e-6 100 1

# Algoritmo de solución
algorithm Newton

# Integrador
integrator LoadControl 0.1

# Tipo de análisis
analysis Static

puts "Análisis configurado!"
puts ""

# ============================================
# EJECUTAR ANÁLISIS
# ============================================

puts "Ejecutando análisis..."

# Analizar 10 pasos (carga aplicada gradualmente)
set nSteps 10
set ok [analyze $nSteps]

if {$ok == 0} {
    puts "✅ Análisis completado exitosamente!"
} else {
    puts "❌ Error en análisis"
}
puts ""

# ============================================
# POST-PROCESAMIENTO
# ============================================

puts "Extrayendo resultados..."

# Crear archivo de desplazamientos
set outFile [open "displacements.txt" w]
puts $outFile "# Node Ux Uy Uz"

# Obtener desplazamientos de todos los nodos (ejemplo con primeros 50)
for {set i 1} {$i <= 50} {incr i} {
    set disp [nodeDisp $i]
    puts $outFile "$i [lindex $disp 0] [lindex $disp 1] [lindex $disp 2]"
}

close $outFile
puts "  - Desplazamientos guardados en displacements.txt"
puts ""

# ============================================
# RESUMEN
# ============================================

puts "=================================="
puts "ANÁLISIS COMPLETADO"
puts "=================================="
puts ""
puts "⚠️  IMPORTANTE - SIGUIENTES PASOS:"
puts "1. Editar materials.tcl con parámetros correctos"
puts "2. Identificar nodos de superficie para aplicar cargas"
puts "3. Ajustar cargas según tu caso"
puts "4. Ejecutar este script con OpenSees"
puts "5. Post-procesar resultados"
puts ""
puts "Para identificar nodos en superficie (z = 0):"
puts "  - Revisar nodes.tcl y buscar nodos con z ≈ 0.0"
puts "  - O usar script Python para filtrar automáticamente"
puts ""

# Finalizar
wipe
