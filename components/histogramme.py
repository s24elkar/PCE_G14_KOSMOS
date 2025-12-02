"""
Composant Histogramme
Affiche l'histogramme RGB avec informations de la caméra
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QPolygon
import random


class HistogramWidget(QWidget):
    """Widget personnalisé pour dessiner l'histogramme RGB"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150) # Réduit de 200 à 150
        self.data_r = self.generate_sample_data()
        self.data_g = self.generate_sample_data()
        self.data_b = self.generate_sample_data()
        self.data_density = self._compute_density_from_channels()
        
    def generate_sample_data(self, points=256):
        """Génère des données d'exemple pour l'histogramme"""
        data = []
        for i in range(points):
            # Simule une distribution avec des pics
            value = random.randint(20, 180)
            if 60 < i < 100 or 150 < i < 200:
                value += random.randint(0, 80)
            data.append(value)
        return data

    def _compute_density_from_channels(self):
        """Moyenne simple des trois canaux pour afficher la densité."""
        if not (self.data_r and self.data_g and self.data_b):
            return self.generate_sample_data()
        return [int((r + g + b) / 3) for r, g, b in zip(self.data_r, self.data_g, self.data_b)]
        
    def update_data(self, data_r=None, data_g=None, data_b=None, data_density=None):
        """Met à jour les données de l'histogramme"""
        if data_r is not None:
            self.data_r = data_r
        if data_g is not None:
            self.data_g = data_g
        if data_b is not None:
            self.data_b = data_b
        if data_density is not None:
            self.data_density = data_density
        else:
            # Recalculer la densité si de nouvelles données de canaux sont fournies
            self.data_density = self._compute_density_from_channels()
        self.update()
        
    def paintEvent(self, event):
        """Dessine l'histogramme"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fond dégradé sombre
        painter.fillRect(self.rect(), QColor(12, 18, 32))
        
        # Dimensions
        width = self.width()
        height = self.height() - 30  # Réserver de l'espace pour les labels
        
        # Dessiner la grille
        painter.setPen(QPen(QColor(90, 90, 90), 1))
        painter.setPen(QPen(QColor(32, 46, 70), 1))
        for i in range(0, width, 50): painter.drawLine(i, 0, i, height)
        for i in range(0, height, 40): painter.drawLine(0, i, width, i)

        # Fonction pour dessiner des barres semi-transparentes
        def draw_bars(data, color, alpha_fill=80, alpha_line=180):
            if not data:
                return
            
            step = max(1, int(width / max(1, len(data))))
            max_value = max(data) if data else 1

            fill_color = QColor(color)
            fill_color.setAlpha(alpha_fill)
            pen_color = QColor(color)
            pen_color.setAlpha(alpha_line)
            painter.setPen(QPen(pen_color, 1))
            painter.setBrush(fill_color)

            for i, value in enumerate(data):
                x = int(i * step)
                bar_height = int((value / max_value) * height)
                bar_rect = QRect(x, height - bar_height, int(step * 0.9), bar_height)
                painter.drawRect(bar_rect)

        # Dessiner les barres (densité en fond, puis RVB)
        draw_bars(self.data_density, "#FFFFFF", alpha_fill=40, alpha_line=120)
        draw_bars(self.data_r, "#EF4444", alpha_fill=70, alpha_line=180)      # Rouge
        draw_bars(self.data_g, "#22C55E", alpha_fill=70, alpha_line=180)      # Vert
        draw_bars(self.data_b, "#3B82F6", alpha_fill=70, alpha_line=180)      # Bleu
        
        # Triangle rouge en haut à droite
        triangle_size = 15
        triangle_points = [
            QPoint(width - 5, 5),
            QPoint(width - 5, 5 + triangle_size),
            QPoint(width - 5 - triangle_size, 5)
        ]
        painter.setBrush(QColor(255, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(QPolygon(triangle_points))
        
        # Labels en bas
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(10, height + 20, "ISO 250")
        painter.drawText(width // 2 - 20, height + 20, "14 mm")
        painter.drawText(width - 60, height + 20, "f/11")
        painter.drawText(width - 160, height + 20, "1/160 s")


class Histogram(QWidget):
    """
    Composant Histogramme
    Affiche l'histogramme RGB avec les informations de la caméra
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # En-tête (TRÈS RÉDUIT)
        header = QLabel("Histogramme")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(24)  # Hauteur fixe réduite
        header.setStyleSheet("""
            QLabel {
                background-color: #111827;
                color: #e5e7eb;
                font-size: 11px;
                font-weight: 700;
                padding: 0px;
                border-bottom: 1px solid #1f2937;
            }
        """)
        main_layout.addWidget(header)
        
        # Widget histogramme
        self.histogram_widget = HistogramWidget()
        
        # Container pour l'histogramme
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(2, 2, 2, 2) # Marges réduites
        container_layout.addWidget(self.histogram_widget)
        container.setLayout(container_layout)
        container.setStyleSheet("background-color: transparent;")

        
        main_layout.addWidget(container, 1) # Stretch 1 pour occuper l'espace
        
        self.setLayout(main_layout)
        self.setObjectName("Histogram")
        self.setStyleSheet("""
            #Histogram {
                background-color: transparent;
                font-family: 'Montserrat', 'Segoe UI', sans-serif;
            }
        """)
        
    def update_histogram(self, data_r=None, data_g=None, data_b=None, data_density=None):
        """Met à jour les données de l'histogramme"""
        self.histogram_widget.update_data(data_r, data_g, data_b, data_density)
        
    def refresh(self):
        """Rafraîchit l'histogramme avec de nouvelles données aléatoires"""
        self.histogram_widget.data_r = self.histogram_widget.generate_sample_data()
        self.histogram_widget.data_g = self.histogram_widget.generate_sample_data()
        self.histogram_widget.data_b = self.histogram_widget.generate_sample_data()
        self.histogram_widget.data_density = self.histogram_widget._compute_density_from_channels()
        self.histogram_widget.update()


# Exemple d'utilisation
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setGeometry(100, 100, 430, 400)
    window.setStyleSheet("background-color: #2a2a2a;")
    
    histogram = Histogram()
    
    window.setCentralWidget(histogram)
    window.show()
    
    sys.exit(app.exec())