from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QPushButton, QLineEdit, QGridLayout
from PyQt6.QtCore import Qt
import sys

class Window(QWidget) : 
    def __init__(self): 
        super().__init__()

        layout = QGridLayout()
        layout.setContentsMargins(20,20,20,20)
        self.setWindowTitle("form1")
        self.setLayout(layout)

        label1 = QLabel("username")
        layout.addWidget(label1, 0, 0)

        label2 = QLabel("password")
        layout.addWidget(label2, 1, 0)

        self.input1 = QLineEdit()
        layout.addWidget(self.input1, 0, 1)

        self.input2 = QLineEdit()
        layout.addWidget(self.input2, 1, 1)

        button = QPushButton("submit")
        button.setFixedWidth(50)
        button.clicked.connect(self.display)
        layout.addWidget(button, 2,1, Qt.AlignmentFlag.AlignRight)
    
    def display (self) :
        print(self.input1.text())
        print(self.input2.text())

app = QApplication(sys.argv)

app.setStyleSheet("""
    QWidget {
        background-color: "green";
        color: "white";
    }

    QLineEdit {
        background-color: "white";
        border-radius: 5px;
        }
""")
window = Window()
window.show()
sys.exit(app.exec())


