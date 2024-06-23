import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout,QSizePolicy,QGridLayout,QHBoxLayout,QTextEdit
from PyQt5.QtGui import QPainter, QPen, QBrush, QPixmap ,QFont,QImage
from PyQt5.QtCore import Qt, pyqtSignal,QTimer,QThread,pyqtSignal
from PyQt5 import QtCore
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import cv2
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import serial
import time

#ana kodumuzun yer aldığı class
class Yer_istasyonu(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.serial_thread = SerialData()
        self.serial_thread.data_received.connect(self.update_data_label)
        self.serial_thread.start()

    def initUI(self):
        # Main interface setup
        self.showFullScreen() #full ekran
        self.setWindowTitle('Yer İstasyonu') #title

        # Arduinodan gelen datayı yansıtmak için
        self.data_text = QTextEdit(self)
        self.data_text.setGeometry(10, 860, 1900, 200)
        self.data_text.setFont(QFont('Arial', 12))
        self.data_text.setReadOnly(True)
        self.data_text.show()

        # 3d similasyon ekle
        self.simulation = Simulation3D(self, x=1100, y=200, width=410, height=400)
        self.simulation.show()

        # video için label oluştur
        self.video_label = QLabel(self)
        self.video_label.setGeometry(1510, 200, 410, 400) #videonun olacağı yer ve büyüklük

        # Create camera thread
        self.video_thread = Camera()
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.start()
        self.video_label.show() #.showlar olmassa hiç biri ekranda gözükmüyor

        # grafikleri oluştur
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

        # Takımımızın adını ekle
        self.OurName = QLabel("Turkish Defenders",self)
        self.OurName.setFont(QFont('Algerian', 36))
        self.OurName.move(10,10)
        self.OurName.adjustSize()
        self.OurName.show()

        #Ayrilma Bekleniyor labeli
        self.AyrilmaLabel = QLabel("Ayrilma Bekleniyor", self)
        self.AyrilmaLabel.setFont(QFont('Arial', 15))
        self.AyrilmaLabel.move(1100,40)
        self.AyrilmaLabel.adjustSize()
        self.AyrilmaLabel.show()

        #Bekliyor Labeli
        self.kodlabel = QLabel("Bekliyor", self)
        self.kodlabel.setFont(QFont('Arial', 15))
        self.kodlabel.move(1510,40)
        self.kodlabel.adjustSize()
        self.kodlabel.show()

        # Buttonları ekle

        # Start and Stop butonları kayıt için cv2
        self.start_button = QPushButton('Start Recording', self)
        self.start_button.setGeometry(1510, 620, 200, 40)
        self.start_button.clicked.connect(self.start_recording)
        self.start_button.show()

        self.stop_button = QPushButton('Stop Recording', self)
        self.stop_button.setGeometry(1720, 620, 200, 40)
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.show()

        #Ayrilma Butonu
        self.SeperateButton = QPushButton('Ayrilma', self)
        self.SeperateButton.setFixedSize(150, 100)
        self.SeperateButton.move(1100, 80)
        self.SeperateButton.setFont(QFont('Arial', 15))
        self.SeperateButton.clicked.connect(self.button1Clicked)
        self.SeperateButton.show()

        #yazi girme yeri, 4 haneli
        self.textInput = QLineEdit(self)
        self.textInput.setGeometry(1510, 135, 100, 40)
        self.textInput.show()

        #gönderme butonu
        self.SendButton = QPushButton('SEND', self)
        self.SendButton.setFixedSize(150, 40)
        self.SendButton.move(1510,80)
        self.SendButton.setFont(QFont('Arial', 15))
        self.SendButton.clicked.connect(self.button2Clicked)
        self.SendButton.show()

    def update_data_label(self, data): #pyserial
        current_text = self.data_text.toPlainText()
        updated_text = f"{data}\n{current_text}"
        self.data_text.setPlainText(updated_text)
        self.serial_thread.save_to_excel(data)  # Save data to Excel

    def start_recording(self): #video kaydı için
        self.video_thread.start_recording()

    def stop_recording(self): #video kaydı için
        self.video_thread.stop_recording()

    def update_image(self, cv_img): #kamera
        #bizim image labelimizdeki yeri updateliyor
        self.video_label.setPixmap(QPixmap.fromImage(cv_img))

    def updateLabelSize(self):
        #bazı yazılar sıkıntı çıkartıyor, garanti olsun diye adjssize ekledim
        self.AyrilmaLabel.adjustSize()
        self.kodlabel.adjustSize()

    def button1Clicked(self):
        #ayrilma butonu tıklandığında ne olur
        self.AyrilmaLabel.setText("Ayrilma Gerçekleşti")
        self.updateLabelSize()

    def button2Clicked(self):
        # Send buttonuna basınca ne olur
        if len(self.textInput.text()) == 4:
            self.kodlabel.setText(self.textInput.text().upper())
        else:
            self.kodlabel.setText("4 hane girin")
        self.updateLabelSize()

    def paintEvent(self, event):
        #arka plani boyamak çindi ama kullanılmıyor
        qp = QPainter()
        qp.begin(self)
        self.drawBackground(qp)
        self.drawLine(qp)
        qp.end()

    def drawBackground(self, qp):
        #arkaplanın ne renk olduğunu seç
        qp.fillRect(self.rect(), QBrush(Qt.white))

    def drawLine(self, qp):
        #sınır çizgileri
        pen = QPen(Qt.black, 5, Qt.SolidLine)
        qp.setPen(pen)
        qp.drawLine(0, 200, 1920, 200)
        qp.drawLine(1100, 600, 1920, 600)
        qp.drawLine(0, 850, 1920, 850)
        qp.drawLine(1100, 200, 1100, 850)
        qp.drawLine(1510, 200, 1510, 600)

class Grafikler(QWidget):
    # her bir grafik için verdiğimiz bilgiler
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
        self.line, = self.ax.plot(self.x_data, self.y_data, 'r-') #r = red
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)

        self.anim = FuncAnimation(self.figure, self.update_plot, init_func=self.init_plot, interval=1000, blit=True)
        #interval = salise sayisi, 1000 = 1 sn

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

        self.x_data = self.x_data[-20:] #datanın ne kadarının gösterileceğini seçiyor, 0 yaparsan hepsi gözükür ama kötü oluyo
        self.y_data = self.y_data[-20:]

        self.line.set_data(self.x_data, self.y_data)
        self.canvas.draw()
        return self.line,

class Camera(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        self.recording = False
        self.out = None

    def run(self):
        # Display video
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FPS, 60)
        while True:
            ret, cv_img = cap.read()
            if ret:
                # Convert the image to RGB format
                cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                h, w, ch = cv_img.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format_RGB888)
                p = convert_to_Qt_format.scaled(410, 400, Qt.KeepAspectRatio)
                self.change_pixmap_signal.emit(p)

                if self.recording:
                    self.out.write(cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR))

    def start_recording(self):
        self.out = cv2.VideoWriter('output.avi', cv2.VideoWriter_fourcc(*'XVID'), 20.0, (640, 480))
        self.recording = True

    def stop_recording(self):
        self.recording = False
        if self.out:
            self.out.release()

class Simulation3D(QWidget):
    def __init__(self, parent, x, y, width, height):
        super().__init__(parent)
        self.setGeometry(x, y, width, height)
        self.initUI()

    def initUI(self):
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111, projection='3d')
        self.ax.set_xlim([-1, 1])
        self.ax.set_ylim([-1, 1])
        self.ax.set_zlim([-1, 1])
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)

        # Initial plot
        self.arrow, = self.ax.plot([0, 1], [0, 0], [0, 0], 'r-')

        # Timer for updating the plot
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)
        self.timer.start(1000)  #her 1 saniyede update'le

        # Example pitch, roll, yaw values
        self.pitch = 0
        self.roll = 0
        self.yaw = 0

    def update_simulation(self):
        #burda gerekli pyserial numaralarını ileticez
        self.pitch += random.uniform(-0.1, 0.1)
        self.roll += random.uniform(-0.1, 0.1)
        self.yaw += random.uniform(-0.1, 0.1)

        # Update the arrow based on pitch, roll, yaw
        R = self.rotation_matrix(self.pitch, self.roll, self.yaw)
        v = np.array([1, 0, 0])
        v_rot = R @ v

        self.arrow.set_data([0, v_rot[0]], [0, v_rot[1]])
        self.arrow.set_3d_properties([0, v_rot[2]])
        self.canvas.draw()

    def rotation_matrix(self, pitch, roll, yaw):
        # Create rotation matrix based on pitch, roll, yaw
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(pitch), -np.sin(pitch)],
            [0, np.sin(pitch), np.cos(pitch)]
        ])
        Ry = np.array([
            [np.cos(roll), 0, np.sin(roll)],
            [0, 1, 0],
            [-np.sin(roll), 0, np.cos(roll)]
        ])
        Rz = np.array([
            [np.cos(yaw), -np.sin(yaw), 0],
            [np.sin(yaw), np.cos(yaw), 0],
            [0, 0, 1]
        ])
        return Rz @ Ry @ Rx

class Harita(QWidget):
    pass

class SerialData(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, port='COM6', baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.excel_file = 'serial_data.xlsx'
        self.init_excel_file()

    def init_excel_file(self):
        # Create a new Excel file with a header if it doesn't exist
        try:
            df = pd.read_excel(self.excel_file)
        except FileNotFoundError:
            df = pd.DataFrame(columns=['Timestamp', 'Data'])
            df.to_excel(self.excel_file, index=False)

    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Arduino'nun başlaması için bekleme süresi

            while True:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').rstrip()
                    self.data_received.emit(line)
        except serial.SerialException as e:
            print(f"Serial error: {e}")

    def save_to_excel(self, data):
        # Append data to the Excel file
        timestamp = pd.Timestamp.now()
        new_data = pd.DataFrame([[timestamp, data]], columns=['Timestamp', 'Data'])
        df = pd.read_excel(self.excel_file)
        df = pd.concat([new_data, df], ignore_index=True)
        df.to_excel(self.excel_file, index=False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Yer_istasyonu()
    ex.show()
    sys.exit(app.exec_())
