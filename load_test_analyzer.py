"""
Analizador de Ensayo de Carga
==============================
Simula ensayo de carga con aplicación incremental de carga
"""

import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt
from config import *

class LoadTestAnalyzer:
    """Clase para realizar análisis de ensayo de carga"""

    def __init__(self, model_builder):
        """
        Parameters:
        -----------
        model_builder : ModelBuilder
            Instancia del constructor del modelo
        """
        self.model = model_builder
        self.load_nodes = model_builder.get_load_nodes()
        self.monitoring_nodes = model_builder.get_monitoring_nodes()

        # Resultados del análisis
        self.results = {
            'loads': [],              # Cargas aplicadas (kN)
            'settlements': [],        # Asentamientos en centro (m)
            'displacements': [],      # Desplazamientos de todos los nodos monitoreados
            'converged': [],          # Estado de convergencia
            'reactions': [],          # Reacciones en la base
        }

    def run_load_test(self):
        """
        Ejecuta el ensayo de carga incremental
        """
        print("\n" + "="*70)
        print("INICIANDO ENSAYO DE CARGA")
        print("="*70)

        max_load = LOAD_TEST['max_load']
        num_steps = LOAD_TEST['num_steps']
        load_increment = max_load / num_steps

        print(f"\nParámetros del ensayo:")
        print(f"  Carga máxima: {max_load} kN")
        print(f"  Número de pasos: {num_steps}")
        print(f"  Incremento de carga: {load_increment:.2f} kN/paso")
        print(f"  Nodos de carga: {len(self.load_nodes)}")

        # Carga por nodo
        load_per_node = -load_increment / len(self.load_nodes)  # Negativo = hacia abajo

        # Configurar análisis estático
        self._setup_analysis()

        # Aplicar carga incremental
        print(f"\n{'Paso':<6} {'Carga (kN)':<12} {'Asentam. (mm)':<15} {'Estado':<12}")
        print("-" * 50)

        for step in range(1, num_steps + 1):
            # Aplicar carga
            current_load = step * load_increment

            # Limpiar cargas previas
            ops.remove('loadPattern', 1)

            # Crear nuevo patrón de carga
            ops.timeSeries('Linear', 1)
            ops.pattern('Plain', 1, 1)

            # Aplicar carga en todos los nodos de carga
            for node in self.load_nodes:
                ops.load(node, 0.0, 0.0, load_per_node * step)

            # Analizar
            converged = self._analyze_step()

            # Registrar resultados
            if converged:
                settlement = self._get_center_settlement()
                self.results['loads'].append(current_load)
                self.results['settlements'].append(abs(settlement) * 1000)  # Convertir a mm
                self.results['converged'].append(True)

                status = "OK"
                print(f"{step:<6} {current_load:<12.2f} {abs(settlement)*1000:<15.4f} {status:<12}")

            else:
                print(f"{step:<6} {current_load:<12.2f} {'N/A':<15} {'NO CONVERGIÓ':<12}")
                self.results['converged'].append(False)
                print("\n⚠ Análisis no convergió. Deteniendo ensayo.")
                break

            # Guardar desplazamientos de nodos monitoreados
            self._record_displacements()

        print("\n" + "="*70)
        print("ENSAYO DE CARGA COMPLETADO")
        print("="*70)

        self._print_results_summary()

        return self.results

    def _setup_analysis(self):
        """Configura el sistema de análisis"""
        # Sistema de ecuaciones
        ops.system('BandGeneral')

        # Numerador
        ops.numberer('RCM')

        # Restricciones
        ops.constraints('Plain')

        # Integrador
        ops.integrator('LoadControl', 1.0)

        # Algoritmo
        ops.algorithm(ANALYSIS['algorithm'])

        # Test de convergencia
        ops.test('NormDispIncr', ANALYSIS['tolerance'], ANALYSIS['max_iterations'])

        # Análisis
        ops.analysis('Static')

    def _analyze_step(self):
        """
        Ejecuta un paso de análisis

        Returns:
        --------
        bool : True si convergió, False si no
        """
        try:
            ok = ops.analyze(1)
            return ok == 0
        except:
            return False

    def _get_center_settlement(self):
        """
        Obtiene el asentamiento del nodo central de la zapata

        Returns:
        --------
        float : Desplazamiento vertical (m)
        """
        center_node = self.monitoring_nodes['center']
        if center_node is None:
            # Si no hay nodo central, usar promedio de todos los nodos de carga
            settlements = [ops.nodeDisp(node, 3) for node in self.load_nodes]
            return np.mean(settlements)

        return ops.nodeDisp(center_node, 3)

    def _record_displacements(self):
        """Registra desplazamientos de nodos monitoreados"""
        displacements = {}

        if self.monitoring_nodes['center']:
            node = self.monitoring_nodes['center']
            displacements['center'] = [
                ops.nodeDisp(node, 1),
                ops.nodeDisp(node, 2),
                ops.nodeDisp(node, 3)
            ]

        corner_disps = []
        for node in self.monitoring_nodes['corners']:
            corner_disps.append([
                ops.nodeDisp(node, 1),
                ops.nodeDisp(node, 2),
                ops.nodeDisp(node, 3)
            ])
        displacements['corners'] = corner_disps

        self.results['displacements'].append(displacements)

    def _print_results_summary(self):
        """Imprime resumen de resultados"""
        if len(self.results['loads']) == 0:
            print("\nNo hay resultados para mostrar.")
            return

        print("\nRESUMEN DE RESULTADOS:")
        print(f"  Carga máxima alcanzada: {max(self.results['loads']):.2f} kN")
        print(f"  Asentamiento máximo: {max(self.results['settlements']):.4f} mm")

        if len(self.results['loads']) >= 2:
            # Estimar módulo de reacción
            area = FOOTING_WIDTH * FOOTING_LENGTH
            pressure = max(self.results['loads']) / area  # kN/m² = kPa
            settlement_m = max(self.results['settlements']) / 1000  # m

            if settlement_m > 0:
                k_modulus = pressure / settlement_m  # kPa/m
                print(f"  Presión de contacto: {pressure:.2f} kPa")
                print(f"  Módulo de reacción estimado: {k_modulus:.1f} kPa/m")

    def plot_load_settlement_curve(self, save_fig=True, filename='load_settlement.png'):
        """
        Grafica la curva carga-asentamiento

        Parameters:
        -----------
        save_fig : bool
            Si True, guarda la figura
        filename : str
            Nombre del archivo de salida
        """
        if len(self.results['loads']) == 0:
            print("No hay resultados para graficar.")
            return

        plt.figure(figsize=(10, 7))

        # Curva carga-asentamiento
        plt.plot(self.results['settlements'], self.results['loads'],
                'b-o', linewidth=2, markersize=6, label='Ensayo de carga')

        plt.xlabel('Asentamiento (mm)', fontsize=12)
        plt.ylabel('Carga aplicada (kN)', fontsize=12)
        plt.title('Curva Carga-Asentamiento del Ensayo de Placa', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=11)

        # Información adicional
        max_load = max(self.results['loads'])
        max_settlement = max(self.results['settlements'])
        area = FOOTING_WIDTH * FOOTING_LENGTH

        info_text = f'Zapata: {FOOTING_WIDTH}m × {FOOTING_LENGTH}m\n'
        info_text += f'Área: {area:.2f} m²\n'
        info_text += f'Df: {EMBEDMENT_DEPTH} m\n'
        info_text += f'Carga máx: {max_load:.1f} kN\n'
        info_text += f'Asentamiento máx: {max_settlement:.2f} mm'

        plt.text(0.98, 0.02, info_text,
                transform=plt.gca().transAxes,
                fontsize=10,
                verticalalignment='bottom',
                horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        if save_fig:
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"\n📊 Gráfica guardada en: {filename}")

        plt.show()

    def export_results(self, filename='load_test_results.csv'):
        """
        Exporta resultados a archivo CSV

        Parameters:
        -----------
        filename : str
            Nombre del archivo de salida
        """
        import csv

        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Paso', 'Carga (kN)', 'Asentamiento (mm)', 'Convergencia'])

            for i, (load, settlement, conv) in enumerate(
                zip(self.results['loads'],
                    self.results['settlements'],
                    self.results['converged']), 1):
                writer.writerow([i, f'{load:.4f}', f'{settlement:.6f}', conv])

        print(f"📄 Resultados exportados a: {filename}")

if __name__ == '__main__':
    # Test del analizador (requiere modelo construido)
    from model_builder import ModelBuilder

    print("Construyendo modelo...")
    builder = ModelBuilder()
    builder.build_model()

    print("\nEjecutando ensayo de carga...")
    analyzer = LoadTestAnalyzer(builder)
    results = analyzer.run_load_test()

    analyzer.plot_load_settlement_curve()
    analyzer.export_results()
