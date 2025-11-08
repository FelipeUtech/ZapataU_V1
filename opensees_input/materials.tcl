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
# Estrato de suelo 1: E=5 MPa (suelo blando)
# Parámetros: E=5000 kPa, nu=0.3, rho=1800 kg/m³ (1.8 ton/m³)
nDMaterial ElasticIsotropic 1 5.0e3 0.3 1.8

# -----------------------------------------
# Material 2 (961 elementos)
# -----------------------------------------
# Estrato de suelo 2: E=20 MPa (suelo medio)
# Parámetros: E=20000 kPa, nu=0.3, rho=1800 kg/m³ (1.8 ton/m³)
nDMaterial ElasticIsotropic 2 2.0e4 0.3 1.8

# -----------------------------------------
# Material 3 (340 elementos)
# -----------------------------------------
# Estrato de suelo 3: E=50 MPa (suelo denso/roca blanda)
# Parámetros: E=50000 kPa, nu=0.3, rho=1800 kg/m³ (1.8 ton/m³)
nDMaterial ElasticIsotropic 3 5.0e4 0.3 1.8

# -----------------------------------------
# Material 4 (183 elementos)
# -----------------------------------------
# Zapata de concreto
# nDMaterial ElasticIsotropic 4 <E> <nu> <rho>
nDMaterial ElasticIsotropic 4 2.5e7 0.2 2.4
