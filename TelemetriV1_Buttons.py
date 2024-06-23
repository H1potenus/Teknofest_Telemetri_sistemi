import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit
from PyQt5.QtGui import QPainter, QPen, QBrush, QPixmap ,QFont
from PyQt5.QtCore import Qt

class LineDrawingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.showFullScreen()
        self.setWindowTitle('Yer İstasyonu')
        # self.background_image = QPixmap('yildizlar.jpg')

        #lets add labels
        #ayrilma label
        self.AyrilmaLabel = QLabel("Ayrilma Bekleniyor   ",self)
        self.AyrilmaLabel.setFont(QFont('Arial',15))
        self.AyrilmaLabel.move(1100,40)
        self.AyrilmaLabel.show()
        #kod labeli
        self.kodlabel = QLabel("Bekleniyor...",self)
        self.kodlabel.setFont(QFont('Arial',15))
        self.kodlabel.move(1510,40)
        self.kodlabel.show()

        #lets add buttons
        #ayrilma butonu
        self.SeperateButton = QPushButton('Ayrilma', self)
        self.SeperateButton.setFixedSize(150, 100)  # Set button size
        self.SeperateButton.move(1100, 80)  # Set button position
        self.SeperateButton.setFont(QFont('Arial', 15))  # Set font and size
        self.SeperateButton.show()
        #kod yollama butonu
        #önce text bar
        self.textInput = QLineEdit(self)
        self.textInput.setGeometry(1510, 135, 100, 40)
        self.textInput.show()
        #send button
        self.SendButton = QPushButton('SEND',self)
        self.SendButton.setFixedSize(150,40)
        self.SendButton.move(1510,80)
        self.SendButton.setFont(QFont('Arial',15))
        self.SendButton.clicked.connect(self.button2Clicked)
        self.SendButton.show()

        #if it gets clicked
        self.SeperateButton.clicked.connect(self.button1Clicked)

    def button1Clicked(self):
        self.AyrilmaLabel.setText("Ayrilma Gerçekleşti")
    def button2Clicked(self):
        if len(self.textInput.text())==4:
            self.kodlabel.setText(self.textInput.text().upper())
        else:
            self.kodlabel.setText("4 hane girin")

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        #self.drawBackground(qp) #makes background a certain color
        self.drawLine(qp)
        qp.end()

    def drawBackground(self, qp):
        # Fill background with color
        qp.fillRect(self.rect(), QBrush(Qt.white))  # Change color if needed

        # Draw background image
        if not self.background_image.isNull():
            qp.drawPixmap(self.rect(), self.background_image)

    def drawLine(self, qp):
        #gerekli çizgileri çizmek için
        pen = QPen(Qt.black, 5, Qt.SolidLine)
        qp.setPen(pen)
        #horizontal lines
        qp.drawLine(0, 200, 1920, 200)
        qp.drawLine(1100, 600, 1920, 600)
        qp.drawLine(0, 850, 1920, 850)
        #vertical ones
        qp.drawLine(1100, 200,1100,850)
        qp.drawLine(1510,200,1510,600)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LineDrawingWidget()
    sys.exit(app.exec_())
