"""
Post-Procesamiento y Visualización
===================================
Genera gráficos y análisis de resultados del ensayo de carga
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d import Axes3D
from config import *
import os

class PostProcessor:
    """Clase para post-procesamiento de resultados"""

    def __init__(self, analyzer, output_dir='results'):
        """
        Parameters:
        -----------
        analyzer : LoadTestAnalyzer
            Analizador con resultados del ensayo
        output_dir : str
            Directorio para guardar resultados
        """
        self.analyzer = analyzer
        self.results = analyzer.results
        self.model = analyzer.model
        self.output_dir = output_dir

        # Crear directorio de salida si no existe
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def generate_all_plots(self):
        """Genera todos los gráficos de resultados"""
        print("\n" + "="*70)
        print("GENERANDO GRÁFICOS DE RESULTADOS")
        print("="*70)

        self.plot_load_settlement()
        self.plot_pressure_settlement()
        self.plot_secant_modulus()
        self.plot_settlement_profile()
        self.create_summary_report()

        print("\n✅ Todos los gráficos generados exitosamente")
        print(f"📁 Resultados guardados en: {self.output_dir}/")

    def plot_load_settlement(self):
        """Gráfico de carga vs asentamiento"""
        if len(self.results['loads']) == 0:
            return

        plt.figure(figsize=(10, 7))

        plt.plot(self.results['settlements'], self.results['loads'],
                'b-o', linewidth=2, markersize=7, label='Ensayo de carga',
                markerfacecolor='white', markeredgewidth=2)

        plt.xlabel('Asentamiento (mm)', fontsize=13, fontweight='bold')
        plt.ylabel('Carga aplicada (kN)', fontsize=13, fontweight='bold')
        plt.title('Curva Carga-Asentamiento', fontsize=15, fontweight='bold')
        plt.grid(True, alpha=0.4, linestyle='--')
        plt.legend(fontsize=11)

        # Información
        area = FOOTING_WIDTH * FOOTING_LENGTH
        max_load = max(self.results['loads'])
        max_settlement = max(self.results['settlements'])

        info = (f'Zapata: {FOOTING_WIDTH} × {FOOTING_LENGTH} m\n'
               f'Área: {area:.2f} m²\n'
               f'Df: {EMBEDMENT_DEPTH} m\n'
               f'Carga máx: {max_load:.1f} kN\n'
               f'Asentamiento máx: {max_settlement:.2f} mm')

        plt.text(0.98, 0.02, info, transform=plt.gca().transAxes,
                fontsize=10, verticalalignment='bottom',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))

        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'load_settlement.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"  ✓ Gráfico guardado: {filename}")
        plt.close()

    def plot_pressure_settlement(self):
        """Gráfico de presión de contacto vs asentamiento"""
        if len(self.results['loads']) == 0:
            return

        area = FOOTING_WIDTH * FOOTING_LENGTH
        pressures = np.array(self.results['loads']) / area  # kPa

        plt.figure(figsize=(10, 7))

        plt.plot(self.results['settlements'], pressures,
                'r-s', linewidth=2, markersize=7, label='Presión de contacto',
                markerfacecolor='white', markeredgewidth=2)

        plt.xlabel('Asentamiento (mm)', fontsize=13, fontweight='bold')
        plt.ylabel('Presión de contacto (kPa)', fontsize=13, fontweight='bold')
        plt.title('Presión de Contacto vs Asentamiento', fontsize=15, fontweight='bold')
        plt.grid(True, alpha=0.4, linestyle='--')
        plt.legend(fontsize=11)

        # Capacidad portante teórica (aproximada)
        # q_ult ≈ c*Nc + γ*Df*Nq + 0.5*γ*B*Nγ
        # Simplificado para referencia
        first_layer = SOIL_LAYERS[0]
        c = first_layer['cohesion']
        phi = np.radians(first_layer['friction_angle'])

        # Factores de capacidad portante (Terzaghi)
        Nq = np.exp(np.pi * np.tan(phi)) * np.tan(np.pi/4 + phi/2)**2
        Nc = (Nq - 1) / np.tan(phi) if phi > 0 else 5.14
        Ng = 2 * (Nq - 1) * np.tan(phi)

        gamma = first_layer['rho'] * 9.81 / 1000  # kN/m³
        q_ult = c * Nc + gamma * EMBEDMENT_DEPTH * Nq + 0.5 * gamma * FOOTING_WIDTH * Ng

        # Factor de seguridad típico = 3
        q_adm = q_ult / 3

        plt.axhline(y=q_adm, color='g', linestyle='--', linewidth=2,
                   label=f'Presión admisible estimada (~{q_adm:.1f} kPa)')
        plt.legend(fontsize=10)

        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'pressure_settlement.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"  ✓ Gráfico guardado: {filename}")
        plt.close()

    def plot_secant_modulus(self):
        """Gráfico de módulo de reacción secante"""
        if len(self.results['loads']) < 2:
            return

        area = FOOTING_WIDTH * FOOTING_LENGTH
        pressures = np.array(self.results['loads']) / area  # kPa
        settlements_m = np.array(self.results['settlements']) / 1000  # m

        # Módulo de reacción secante: k = q / s
        k_modulus = []
        for i in range(1, len(pressures)):
            if settlements_m[i] > 0:
                k = pressures[i] / settlements_m[i]
                k_modulus.append(k)
            else:
                k_modulus.append(0)

        if len(k_modulus) == 0:
            return

        plt.figure(figsize=(10, 7))

        plt.plot(self.results['settlements'][1:], k_modulus,
                'g-^', linewidth=2, markersize=7, label='Módulo de reacción secante',
                markerfacecolor='white', markeredgewidth=2)

        plt.xlabel('Asentamiento (mm)', fontsize=13, fontweight='bold')
        plt.ylabel('Módulo de reacción k (kPa/m)', fontsize=13, fontweight='bold')
        plt.title('Módulo de Reacción del Suelo', fontsize=15, fontweight='bold')
        plt.grid(True, alpha=0.4, linestyle='--')
        plt.legend(fontsize=11)

        # Valor promedio
        k_avg = np.mean(k_modulus)
        plt.axhline(y=k_avg, color='orange', linestyle='--', linewidth=2,
                   label=f'Promedio: {k_avg:.1f} kPa/m')
        plt.legend(fontsize=10)

        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'secant_modulus.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"  ✓ Gráfico guardado: {filename}")
        plt.close()

    def plot_settlement_profile(self):
        """Gráfico de perfil de asentamientos en las esquinas"""
        if len(self.results['displacements']) == 0:
            return

        # Obtener desplazamientos de esquinas en cada paso
        num_steps = len(self.results['displacements'])
        corner_settlements = []

        for step_data in self.results['displacements']:
            if 'corners' in step_data and len(step_data['corners']) > 0:
                # Asentamiento vertical (componente z)
                settlements = [abs(disp[2]) * 1000 for disp in step_data['corners']]  # mm
                corner_settlements.append(settlements)

        if len(corner_settlements) == 0:
            return

        corner_settlements = np.array(corner_settlements)

        plt.figure(figsize=(10, 7))

        for i in range(corner_settlements.shape[1]):
            plt.plot(self.results['loads'][:len(corner_settlements)],
                    corner_settlements[:, i],
                    '-o', linewidth=2, markersize=5,
                    label=f'Esquina {i+1}')

        # Centro
        if 'center' in self.results['displacements'][0]:
            center_settlements = [abs(step['center'][2]) * 1000
                                for step in self.results['displacements']
                                if 'center' in step]
            if len(center_settlements) > 0:
                plt.plot(self.results['loads'][:len(center_settlements)],
                        center_settlements,
                        '-s', linewidth=2.5, markersize=7,
                        label='Centro', color='red')

        plt.xlabel('Carga aplicada (kN)', fontsize=13, fontweight='bold')
        plt.ylabel('Asentamiento (mm)', fontsize=13, fontweight='bold')
        plt.title('Perfil de Asentamientos en Diferentes Puntos', fontsize=15, fontweight='bold')
        plt.grid(True, alpha=0.4, linestyle='--')
        plt.legend(fontsize=10)

        plt.tight_layout()
        filename = os.path.join(self.output_dir, 'settlement_profile.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"  ✓ Gráfico guardado: {filename}")
        plt.close()

    def create_summary_report(self):
        """Crea un reporte resumen en formato de texto"""
        filename = os.path.join(self.output_dir, 'summary_report.txt')

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("REPORTE DE ENSAYO DE CARGA DE ZAPATA\n")
            f.write("="*70 + "\n\n")

            # Información del modelo
            f.write("1. INFORMACIÓN DEL MODELO\n")
            f.write("-" * 70 + "\n")
            f.write(f"Dimensiones de zapata: {FOOTING_WIDTH} m × {FOOTING_LENGTH} m × {FOOTING_THICKNESS} m\n")
            f.write(f"Área de zapata: {FOOTING_WIDTH * FOOTING_LENGTH:.2f} m²\n")
            f.write(f"Profundidad de desplante: {EMBEDMENT_DEPTH} m\n")
            f.write(f"Dominio de análisis: {SOIL_WIDTH_X} × {SOIL_WIDTH_Y} × {SOIL_DEPTH} m\n\n")

            # Estratos
            f.write("2. ESTRATIFICACIÓN DEL SUELO\n")
            f.write("-" * 70 + "\n")
            for i, layer in enumerate(SOIL_LAYERS):
                f.write(f"\nEstrato {i+1}: {layer['name']}\n")
                f.write(f"  Profundidad: {layer['depth_top']} - {layer['depth_bottom']} m\n")
                f.write(f"  E = {layer['E']/1000:.1f} MPa\n")
                f.write(f"  ν = {layer['nu']}\n")
                f.write(f"  c = {layer['cohesion']} kPa\n")
                f.write(f"  φ = {layer['friction_angle']}°\n")

            # Resultados
            if len(self.results['loads']) > 0:
                f.write("\n3. RESULTADOS DEL ENSAYO\n")
                f.write("-" * 70 + "\n")

                max_load = max(self.results['loads'])
                max_settlement = max(self.results['settlements'])
                area = FOOTING_WIDTH * FOOTING_LENGTH
                max_pressure = max_load / area

                f.write(f"Carga máxima aplicada: {max_load:.2f} kN\n")
                f.write(f"Presión máxima de contacto: {max_pressure:.2f} kPa\n")
                f.write(f"Asentamiento máximo: {max_settlement:.4f} mm\n")

                if max_settlement > 0:
                    k_modulus = max_pressure / (max_settlement / 1000)
                    f.write(f"Módulo de reacción promedio: {k_modulus:.1f} kPa/m\n")

                # Pasos que convergieron
                converged_count = sum(self.results['converged'])
                f.write(f"\nPasos convergidos: {converged_count}/{len(self.results['converged'])}\n")

            f.write("\n" + "="*70 + "\n")
            f.write("FIN DEL REPORTE\n")
            f.write("="*70 + "\n")

        print(f"  ✓ Reporte guardado: {filename}")

    def export_csv_results(self):
        """Exporta resultados detallados a CSV"""
        filename = os.path.join(self.output_dir, 'detailed_results.csv')

        import csv

        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)

            # Encabezados
            header = ['Paso', 'Carga (kN)', 'Presión (kPa)', 'Asentamiento (mm)',
                     'Centro_X (mm)', 'Centro_Y (mm)', 'Centro_Z (mm)', 'Convergió']
            writer.writerow(header)

            area = FOOTING_WIDTH * FOOTING_LENGTH

            for i, (load, settlement, conv) in enumerate(
                zip(self.results['loads'],
                    self.results['settlements'],
                    self.results['converged']), 1):

                pressure = load / area

                # Desplazamientos del centro
                if i-1 < len(self.results['displacements']):
                    disp_data = self.results['displacements'][i-1]
                    if 'center' in disp_data:
                        center = disp_data['center']
                        cx = center[0] * 1000  # mm
                        cy = center[1] * 1000
                        cz = center[2] * 1000
                    else:
                        cx = cy = cz = 0
                else:
                    cx = cy = cz = 0

                writer.writerow([i, f'{load:.4f}', f'{pressure:.4f}',
                               f'{settlement:.6f}', f'{cx:.6f}', f'{cy:.6f}',
                               f'{cz:.6f}', conv])

        print(f"  ✓ CSV guardado: {filename}")

if __name__ == '__main__':
    # Test del post-procesador
    from model_builder import ModelBuilder
    from load_test_analyzer import LoadTestAnalyzer

    print("Construyendo modelo...")
    builder = ModelBuilder()
    builder.build_model()

    print("\nEjecutando ensayo de carga...")
    analyzer = LoadTestAnalyzer(builder)
    results = analyzer.run_load_test()

    print("\nGenerando gráficos...")
    post = PostProcessor(analyzer)
    post.generate_all_plots()
    post.export_csv_results()

    print("\n✅ Post-procesamiento completado")
