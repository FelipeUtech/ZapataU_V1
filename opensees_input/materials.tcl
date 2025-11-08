# ============================================
# DEFINICIÓN DE MATERIALES
# Generado por: gmsh_to_opensees.py
# ============================================
# IMPORTANTE: Este es un template!
# Debes completar los parámetros según tu proyecto
# ============================================


# -----------------------------------------
# Material 1 (2,056 elementos)
# -----------------------------------------
# Estrato de suelo 1
# nDMaterial PressureDependMultiYield 1 <nd> <rho> <refShearModul> <refBulkModul> <cohesi> <peakShearStra> ...
# O usar ElasticIsotropic para análisis simplificado:
# nDMaterial ElasticIsotropic 1 <E> <nu> <rho>
nDMaterial ElasticIsotropic 1 3.0e4 0.3 1.8  ;# COMPLETAR PARÁMETROS

# -----------------------------------------
# Material 2 (961 elementos)
# -----------------------------------------
# Estrato de suelo 2
# nDMaterial PressureDependMultiYield 2 <nd> <rho> <refShearModul> <refBulkModul> <cohesi> <peakShearStra> ...
# O usar ElasticIsotropic para análisis simplificado:
# nDMaterial ElasticIsotropic 2 <E> <nu> <rho>
nDMaterial ElasticIsotropic 2 3.0e4 0.3 1.8  ;# COMPLETAR PARÁMETROS

# -----------------------------------------
# Material 3 (340 elementos)
# -----------------------------------------
# Estrato de suelo 3
# nDMaterial PressureDependMultiYield 3 <nd> <rho> <refShearModul> <refBulkModul> <cohesi> <peakShearStra> ...
# O usar ElasticIsotropic para análisis simplificado:
# nDMaterial ElasticIsotropic 3 <E> <nu> <rho>
nDMaterial ElasticIsotropic 3 3.0e4 0.3 1.8  ;# COMPLETAR PARÁMETROS

# -----------------------------------------
# Material 4 (183 elementos)
# -----------------------------------------
# Zapata de concreto
# nDMaterial ElasticIsotropic 4 <E> <nu> <rho>
nDMaterial ElasticIsotropic 4 2.5e7 0.2 2.4
