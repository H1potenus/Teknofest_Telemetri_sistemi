import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout,QSizePolicy,QGridLayout,QHBoxLayout
from PyQt5.QtGui import QPainter, QPen, QBrush, QPixmap ,QFont
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt


class Yer_istasyonu(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Main interface setup
        self.showFullScreen()
        self.setWindowTitle('Yer İstasyonu')

        # Create graphs
        self.sicaklikGrafik = Grafikler(self, title="sicaklik graf", xlabel="zaman", ylabel="sicaklik",     x=10, y=210, width=350, height=300)
        self.basincGrafik = Grafikler(self, title="basinc graf", xlabel="zaman", ylabel="basinc",           x=370, y=210, width=350, height=300)
        self.hizGrafik = Grafikler(self, title="hiz graf", xlabel="zaman", ylabel="hiz",                    x=730, y=210, width=350, height=300)
        self.yükseklikGrafik = Grafikler(self, title="Yükseklik graf", xlabel="zaman", ylabel="yükseklik",  x=10, y=520, width=350, height=300)
        self.pilGerilimGrafik = Grafikler(self, title="Pil Gerilimi graf", xlabel="zaman", ylabel="gerilim",x=370, y=520, width=350, height=300)

        # Grafikleri göster
        self.sicaklikGrafik.show()
        self.basincGrafik.show()
        self.hizGrafik.show()
        self.yükseklikGrafik.show()
        self.pilGerilimGrafik.show()

        # Add labels
        self.AyrilmaLabel = QLabel("Ayrilma Bekleniyor", self)
        self.AyrilmaLabel.setFont(QFont('Arial', 15))
        self.AyrilmaLabel.move(1100,40)
        self.AyrilmaLabel.adjustSize()
        self.AyrilmaLabel.show()

        self.kodlabel = QLabel("Bekliyor", self)
        self.kodlabel.setFont(QFont('Arial', 15))
        self.kodlabel.move(1510,40)
        self.kodlabel.adjustSize()
        self.kodlabel.show()

        # Add buttons
        self.SeperateButton = QPushButton('Ayrilma', self)
        self.SeperateButton.setFixedSize(150, 100)
        self.SeperateButton.move(1100, 80)
        self.SeperateButton.setFont(QFont('Arial', 15))
        self.SeperateButton.clicked.connect(self.button1Clicked)
        self.SeperateButton.show()

        self.textInput = QLineEdit(self)
        self.textInput.setGeometry(1510, 135, 100, 40)
        self.textInput.show()

        self.SendButton = QPushButton('SEND', self)
        self.SendButton.setFixedSize(150, 40)
        self.SendButton.move(1510,80)
        self.SendButton.setFont(QFont('Arial', 15))
        self.SendButton.clicked.connect(self.button2Clicked)
        self.SendButton.show()

    def updateLabelSize(self):
        self.AyrilmaLabel.adjustSize()
        self.kodlabel.adjustSize()

    def button1Clicked(self):
        self.AyrilmaLabel.setText("Ayrilma Gerçekleşti")
        self.updateLabelSize()

    def button2Clicked(self):
        if len(self.textInput.text()) == 4:
            self.kodlabel.setText(self.textInput.text().upper())
        else:
            self.kodlabel.setText("4 hane girin")
        self.updateLabelSize()

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

class Grafikler(QWidget):
    def __init__(self, parent, title, xlabel, ylabel, x, y, width, height):
        super().__init__(parent)
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.setGeometry(x, y, width, height)
        self.initUI2()

    def initUI2(self):
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.x_data, self.y_data = [], []
        self.line, = self.ax.plot(self.x_data, self.y_data, 'r-')
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)

        self.anim = FuncAnimation(self.figure, self.update_plot, init_func=self.init_plot, interval=1000, blit=True)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)

    def init_plot(self):
        self.line.set_data(self.x_data, self.y_data)
        return self.line,

    def update_plot(self, frame):
        if len(self.x_data) == 0:
            self.x_data.append(0)
        else:
            self.x_data.append(self.x_data[-1] + 1)
        self.y_data.append(random.randint(0, 10))

        self.ax.set_xlim(self.x_data[0], self.x_data[-1])
        self.ax.set_ylim(min(self.y_data), max(self.y_data))

        self.line.set_data(self.x_data, self.y_data)
        self.canvas.draw()
        return self.line,

class Camera(QWidget):
    pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Yer_istasyonu()
    ex.show()
    sys.exit(app.exec_())
