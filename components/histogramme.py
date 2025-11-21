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
        self.setMinimumHeight(200)
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
        if data_r:
            self.data_r = data_r
        if data_g:
            self.data_g = data_g
        if data_b:
            self.data_b = data_b
        if data_density:
            self.data_density = data_density
        else:
            self.data_density = self._compute_density_from_channels()
        self.update()
        
    def paintEvent(self, event):
        """Dessine l'histogramme"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fond gris
        painter.fillRect(self.rect(), QColor(70, 70, 70))
        
        # Dimensions
        width = self.width()
        height = self.height() - 30  # Réserver de l'espace pour les labels
        
        # Dessiner la grille
        painter.setPen(QPen(QColor(90, 90, 90), 1))
        for i in range(0, width, 50):
            painter.drawLine(i, 0, i, height)
        for i in range(0, height, 40):
            painter.drawLine(0, i, width, i)
        
        # Fonction pour dessiner une courbe
        def draw_curve(data, color, alpha=180):
            if not data:
                return
            
            points = []
            step = width / len(data)
            max_value = max(data) if data else 1
            
            for i, value in enumerate(data):
                x = int(i * step)
                y = height - int((value / max_value) * height)
                points.append(QPoint(x, y))
            
            if len(points) > 1:
                # Créer un polygone pour remplir sous la courbe
                fill_points = [QPoint(0, height)] + points + [QPoint(width, height)]
                polygon = QPolygon(fill_points)
                
                # Remplissage avec transparence
                fill_color = QColor(color)
                fill_color.setAlpha(alpha // 3)
                painter.setBrush(fill_color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPolygon(polygon)
                
                # Dessiner la ligne
                pen_color = QColor(color)
                pen_color.setAlpha(alpha)
                painter.setPen(QPen(pen_color, 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i + 1])
        
        # Dessiner les courbes RGB avec mélange
        draw_curve(self.data_density, "#FFFFFF", 180)  # Courbe blanche (densité)
        draw_curve(self.data_r, "#FF1744", 150)      # Rouge
        draw_curve(self.data_g, "#00E676", 150)      # Vert
        draw_curve(self.data_b, "#2979FF", 150)      # Bleu
        
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
        header.setFixedHeight(40)  # Hauteur fixe
        header.setStyleSheet("""
            QLabel {
                background-color: white;
                color: black;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                border-bottom: 1px solid #ddd;
            }
        """)
        main_layout.addWidget(header)
        
        # Widget histogramme
        self.histogram_widget = HistogramWidget()
        
        # Container pour l'histogramme
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.addWidget(self.histogram_widget)
        container.setLayout(container_layout)
        container.setStyleSheet("background-color: black;")
        
        main_layout.addWidget(container)
        
        self.setLayout(main_layout)
        self.setObjectName("Histogram")
        self.setStyleSheet("""
            #Histogram {
                background-color: black;
                border: 2px solid white;
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
