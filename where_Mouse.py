import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtGui import QPainter, QPen, QBrush, QFont
from PyQt5.QtCore import Qt, QTimer

class Yer_istasyonu(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.showFullScreen()  # full ekran
        self.setWindowTitle('Yer İstasyonu')  # title

        # Takımımızın adını ekle
        self.OurName = QLabel("Turkish Defenders", self)
        self.OurName.setFont(QFont('Algerian', 36))
        self.OurName.move(10, 10)
        self.OurName.adjustSize()
        self.OurName.show()

        # Label to show coordinates
        self.coord_label = QLabel(self)
        self.coord_label.setFont(QFont('Arial', 20))
        self.coord_label.move(10, 100)  # Adjust position as needed
        self.coord_label.adjustSize()
        self.coord_label.show()

        # Initialize the timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_coordinates)
        self.timer.start(100)  # Update every 100 milliseconds

    def update_data_label(self, data):
        current_text = self.data_text.toPlainText()
        updated_text = f"{data}\n{current_text}"
        self.data_text.setPlainText(updated_text)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.drawBackground(qp)
        self.drawLine(qp)
        qp.end()

    def drawBackground(self, qp):
        qp.fillRect(self.rect(), QBrush(Qt.white))

    def drawLine(self, qp):
        pen = QPen(Qt.black, 5, Qt.SolidLine)
        qp.setPen(pen)
        qp.drawLine(0, 200, 1920, 200)
        qp.drawLine(1100, 600, 1920, 600)
        qp.drawLine(0, 850, 1920, 850)
        qp.drawLine(1100, 200, 1100, 850)
        qp.drawLine(1510, 200, 1510, 600)

    def update_coordinates(self):
        cursor_pos = self.mapFromGlobal(self.cursor().pos())
        x = cursor_pos.x()
        y = cursor_pos.y()
        self.coord_label.setText(f"Coordinates: ({x}, {y})")
        self.coord_label.adjustSize()

app = QApplication(sys.argv)
window = Yer_istasyonu()
window.show()
sys.exit(app.exec_())
