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
        
        # Marges pour les axes
        margin_left = 35
        margin_bottom = 25
        margin_top = 10
        margin_right = 10
        
        # Zone de dessin du graphique
        graph_rect = QRect(
            margin_left, 
            margin_top, 
            self.width() - margin_left - margin_right, 
            self.height() - margin_top - margin_bottom
        )
        
        # Dessiner les axes
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        # Axe Y
        painter.drawLine(graph_rect.topLeft(), graph_rect.bottomLeft())
        # Axe X
        painter.drawLine(graph_rect.bottomLeft(), graph_rect.bottomRight())
        
        # Labels Axe X (0, 64, 128, 192, 255)
        font = painter.font()
        font.setPointSize(7)
        painter.setFont(font)
        
        x_labels = [0, 64, 128, 192, 255]
        for val in x_labels:
            x_pos = graph_rect.left() + (val / 255) * graph_rect.width()
            painter.drawText(
                int(x_pos - 10), 
                graph_rect.bottom() + 15, 
                20, 
                10, 
                Qt.AlignmentFlag.AlignCenter, 
                str(val)
            )
            # Petit tick
            painter.drawLine(int(x_pos), graph_rect.bottom(), int(x_pos), graph_rect.bottom() + 3)

        # Labels Axe Y (0, 50%, 100%) - Approximatif car dépend des données
        y_labels = ["0", "50%", "100%"]
        for i, label in enumerate(y_labels):
            y_pos = graph_rect.bottom() - (i / 2) * graph_rect.height()
            painter.drawText(
                0, 
                int(y_pos - 5), 
                margin_left - 5, 
                10, 
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, 
                label
            )
            # Petit tick
            painter.drawLine(graph_rect.left() - 3, int(y_pos), graph_rect.left(), int(y_pos))

        # Grille légère
        painter.setPen(QPen(QColor(50, 50, 50), 1, Qt.PenStyle.DotLine))
        # Lignes verticales
        for val in x_labels[1:-1]:
            x_pos = int(graph_rect.left() + (val / 255) * graph_rect.width())
            painter.drawLine(x_pos, graph_rect.top(), x_pos, graph_rect.bottom())
        # Ligne horizontale (50%)
        y_mid = int(graph_rect.bottom() - 0.5 * graph_rect.height())
        painter.drawLine(graph_rect.left(), y_mid, graph_rect.right(), y_mid)

        # Fonction pour dessiner des barres semi-transparentes
        def draw_bars(data, color, alpha_fill=80, alpha_line=180):
            if not data:
                return
            
            step = max(1, graph_rect.width() / max(1, len(data)))
            max_value = max(data) if data else 1

            fill_color = QColor(color)
            fill_color.setAlpha(alpha_fill)
            pen_color = QColor(color)
            pen_color.setAlpha(alpha_line)
            painter.setPen(QPen(pen_color, 1))
            painter.setBrush(fill_color)

            for i, value in enumerate(data):
                # Ajustement pour rester dans graph_rect
                if i >= len(data): break
                
                x = int(graph_rect.left() + i * (graph_rect.width() / len(data)))
                bar_height = int((value / max_value) * graph_rect.height())
                
                # Largeur de barre ajustée pour ne pas dépasser
                bar_width = max(1, int(graph_rect.width() / len(data)) + 1)
                
                bar_rect = QRect(x, graph_rect.bottom() - bar_height, bar_width, bar_height)
                painter.drawRect(bar_rect)

        # Dessiner les barres (densité en fond, puis RVB)
        draw_bars(self.data_density, "#FFFFFF", alpha_fill=40, alpha_line=120)
        draw_bars(self.data_r, "#EF4444", alpha_fill=70, alpha_line=180)      # Rouge
        draw_bars(self.data_g, "#22C55E", alpha_fill=70, alpha_line=180)      # Vert
        draw_bars(self.data_b, "#3B82F6", alpha_fill=70, alpha_line=180)      # Bleu
        
        # Triangle rouge en haut à droite (indicateur clipping)
        triangle_size = 10
        triangle_points = [
            QPoint(graph_rect.right() - 2, graph_rect.top() + 2),
            QPoint(graph_rect.right() - 2, graph_rect.top() + 2 + triangle_size),
            QPoint(graph_rect.right() - 2 - triangle_size, graph_rect.top() + 2)
        ]
        painter.setBrush(QColor(255, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(QPolygon(triangle_points))


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