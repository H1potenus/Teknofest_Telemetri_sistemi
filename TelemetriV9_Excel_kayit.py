import sys
import random
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout, QSizePolicy, QTextEdit, QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QPainter, QPen, QBrush, QPixmap, QFont, QImage
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import cv2
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import serial
import time
import math
import os

class Yer_istasyonu(QWidget): #ana kodumuzun yer aldığı class
    def __init__(self):
        super().__init__()
        self.initUI()
        self.serial_thread = SerialData()
        self.serial_thread.data_received.connect(self.update_data_label)
        self.serial_thread.start()

        self.camera_thread = Camera()
        self.camera_thread.frame_ready.connect(self.update_camera_label)
        self.camera_thread.start()

    def closeEvent(self, event):
        self.serial_thread.stop()
        self.camera_thread.stop()
        event.accept()

    def initUI(self):
        # Main interface setup
        self.showFullScreen()
        self.setWindowTitle('Yer İstasyonu') #titlew

        # kamera
        self.camera_label = QLabel(self)
        self.camera_label.setGeometry(1150, 200, 300, 200)  # Adjust size and position as needed
        self.camera_label.show()

        #2d simulasyon
        self.simulation2D = Simulation2D(self)
        self.simulation2D.setGeometry(950, 200, 150, 150)  # Adjust size and position as needed
        self.simulation2D.show()

        # Arduinodan gelen datayı yansıtmak için
        self.data_table = QTableWidget(self)
        self.data_table.setGeometry(1, 752, 1900, 420)
        self.data_table.setColumnCount(22)
        self.data_table.setHorizontalHeaderLabels([
            'Pnum', 'Statü', 'HataK', 'Date', 'Time', 'Basinc1', 'Basinc2', 'Yüks1',
            'Yüks2', 'Irtifia', 'İnişH', 'Sıcak', 'PilGer', 'GpsEnlem', 'GpsBoylam', 'GpsYüks',
            'Pitch', 'Roll', 'Yaw', 'rhrh', 'IotD', 'TakımNo'
        ])

        # Set column widths (adjust values as needed)
        column_widths = [50, 30, 60, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 80]
        for i, width in enumerate(column_widths):
            self.data_table.setColumnWidth(i, width)

        self.data_table.show()

        # Create text area for displaying data
        self.data_text = QTextEdit(self)
        self.data_text.setGeometry(10, 10, 400, 200)
        self.data_text.setReadOnly(True)
        #self.data_text.show() #artık gerekli değil ama lazım olur

        # grafikleri oluştur
        self.sicaklikGrafik = Grafikler(self, title="sicaklik graf", xlabel="zaman", ylabel="sicaklik",     x=10, y=210, width=300, height=200)
        self.basincGrafik = Grafikler(self, title="basinc graf", xlabel="zaman", ylabel="basinc",           x=320, y=210, width=300, height=200)
        self.hizGrafik = Grafikler(self, title="hiz graf", xlabel="zaman", ylabel="hiz",                    x=630, y=210, width=300, height=200)
        self.yükseklikGrafik = Grafikler(self, title="Yükseklik graf", xlabel="zaman", ylabel="yükseklik",  x=10, y=420, width=300, height=200)
        self.pilGerilimGrafik = Grafikler(self, title="Pil Gerilimi graf", xlabel="zaman", ylabel="gerilim",x=320, y=420, width=300, height=200)

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
        self.kodlabel.move(1310,40)
        self.kodlabel.adjustSize()
        self.kodlabel.show()

        # Buttonları ekle


        #Ayrilma Butonu
        self.SeperateButton = QPushButton('Ayrilma', self)
        self.SeperateButton.setFixedSize(150, 100)
        self.SeperateButton.move(1100, 80)
        self.SeperateButton.setFont(QFont('Arial', 15))
        self.SeperateButton.clicked.connect(self.button1Clicked)
        self.SeperateButton.show()

        #yazi girme yeri, 4 haneli
        self.textInput = QLineEdit(self)
        self.textInput.setGeometry(1310, 135, 100, 40)
        self.textInput.show()

        #gönderme butonu
        self.SendButton = QPushButton('SEND', self)
        self.SendButton.setFixedSize(150, 40)
        self.SendButton.move(1310,80)
        self.SendButton.setFont(QFont('Arial', 15))
        self.SendButton.clicked.connect(self.button2Clicked)
        self.SendButton.show()

    def update_camera_label(self, image):
        try:
            scaled_image = image.scaled(self.camera_label.size(), Qt.AspectRatioMode.KeepAspectRatio)
            self.camera_label.setPixmap(QPixmap.fromImage(scaled_image))
        except Exception as e:
            print(f"Error scaling image: {e}")

    def update_data_label(self, data):
        current_text = self.data_text.toPlainText()
        updated_text = f"{data}\n{current_text}"
        self.data_text.setPlainText(updated_text)

        try:
            values = data.split(',')
            if len(values) >= 21:
                pressure = float(values[5])
                temp = float(values[11])
                speed = float(values[10])
                altitude = float(values[7])
                voltage = float(values[12])

                pitch = float(values[16])
                roll = float(values[17])
                yaw = float(values[18])

                self.sicaklikGrafik.add_data(temp)
                self.basincGrafik.add_data(pressure)
                self.hizGrafik.add_data(speed)
                self.yükseklikGrafik.add_data(altitude)
                self.pilGerilimGrafik.add_data(voltage)

                self.simulation2D.set_yaw(yaw)

                # Insert data into the table at the top
                self.data_table.insertRow(0)
                for i, value in enumerate(values[:22]):
                    self.data_table.setItem(0, i, QTableWidgetItem(value))
        except ValueError:
            print("Invalid data received")

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
    def __init__(self, parent, title, xlabel, ylabel, x, y, width, height):
        super().__init__(parent)
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.setGeometry(x, y, width, height)
        self.initUI2()

    def initUI2(self):

        plt.style.use('seaborn-v0_8')
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.x_data, self.y_data = [], []
        self.line, = self.ax.plot(self.x_data, self.y_data, 'r-')
        self.ax.set_title(self.title)
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.canvas)

    def update_plot(self):
        self.line.set_data(self.x_data, self.y_data)
        self.ax.set_xlim(self.x_data[0] if self.x_data else 0, self.x_data[-1] if self.x_data else 1)
        self.ax.set_ylim(min(self.y_data) if self.y_data else 0, max(self.y_data) if self.y_data else 1)
        self.canvas.draw()

    def add_data(self, y):
        if len(self.x_data) == 0:
            self.x_data.append(0)
        else:
            self.x_data.append(self.x_data[-1] + 1)
        self.y_data.append(y)
        self.x_data = self.x_data[-20:]
        self.y_data = self.y_data[-20:]
        self.update_plot()

class Camera(QThread):
    frame_ready = pyqtSignal(QImage)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.capture = None

    def run(self):
        # Open the HDMI video stream (this might vary depending on your setup)
        self.capture = cv2.VideoCapture(0)  # Change 0 to the appropriate device index or HDMI source

        while self.running:
            ret, frame = self.capture.read()
            if ret:
                # Convert the frame to RGB format
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert to QImage
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

                # Emit the signal with the frame
                self.frame_ready.emit(qt_image)

    def stop(self):
        self.running = False
        if self.capture.isOpened():
            self.capture.release()

    def __del__(self):
        self.stop()


class Simulation2D(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.yaw = 0  # Initialize yaw angle
        self.setMinimumSize(200, 200)  # Ensure the widget is large enough

    def set_yaw(self, yaw):
        print(f"Setting yaw: {yaw}")  # Debug output
        self.yaw = yaw
        self.update()  # Update the widget to trigger a repaint

    def paintEvent(self, event):
        print("Paint event triggered")  # Debug output
        qp = QPainter(self)
        self.drawSatellite(qp)

    def drawSatellite(self, qp):
        size = self.size()
        w = size.width()
        h = size.height()

        qp.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Clear background
        qp.fillRect(0, 0, w, h, QBrush(Qt.GlobalColor.white))

        # Translate to the center and rotate
        qp.translate(w / 2, h / 2)
        qp.rotate(self.yaw)

        # Draw satellite body
        rect_width = 100
        rect_height = 30
        qp.setBrush(QBrush(Qt.GlobalColor.blue))
        qp.drawRect(-rect_width / 2, -rect_height / 2, rect_width, rect_height)

        # Draw directional indicator (front)
        qp.setBrush(QBrush(Qt.GlobalColor.red))
        qp.drawRect(-5, -rect_height / 2 - 10, 10, 10)

        # Draw solar panels
        panel_width = 80
        panel_height = 10
        qp.setBrush(QBrush(Qt.GlobalColor.gray))
        qp.drawRect(-rect_width / 2 - panel_width, -panel_height / 2, panel_width, panel_height)
        qp.drawRect(rect_width / 2, -panel_height / 2, panel_width, panel_height)

        # Draw an outline for better visibility
        qp.setPen(QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.SolidLine))
        qp.setBrush(Qt.BrushStyle.NoBrush)
        qp.drawRect(-rect_width / 2, -rect_height / 2, rect_width, rect_height)
        qp.drawRect(-5, -rect_height / 2 - 10, 10, 10)
        qp.drawRect(-rect_width / 2 - panel_width, -panel_height / 2, panel_width, panel_height)
        qp.drawRect(rect_width / 2, -panel_height / 2, panel_width, panel_height)

        # Reset transformation
        qp.resetTransform()

class Harita(QWidget):
    pass

class SerialData(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, port='COM6', baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.excel_file = self.get_unique_filename()  # Use unique file name function
        self.init_excel_file()
        self.running = True

    def get_unique_filename(self):
        base_name = 'serial_data'
        ext = '.xlsx'
        counter = 1

        while os.path.exists(f"{base_name}{counter}{ext}"):
            counter += 1

        return f"{base_name}{counter}{ext}"

    def init_excel_file(self):
        try:
            df = pd.DataFrame(columns=[
                'Pnum', 'Statü', 'HataK', 'Date', 'Time', 'Basinc1', 'Basinc2', 'Yüks1',
                'Yüks2', 'Irtifia', 'İnişH', 'Sıcak', 'PilGer', 'GpsEnlem', 'GpsBoylam', 'GpsYüks',
                'Pitch', 'Roll', 'Yaw', 'rhrh', 'IotD', 'TakımNo'
            ])
            df.to_excel(self.excel_file, index=False)
        except Exception as e:
            print(f"Error initializing Excel file: {e}")

    def run(self):
        while self.running:
            try:
                if self.ser is None or not self.ser.is_open:
                    print("Opening serial port...")
                    self.ser = serial.Serial(self.port, self.baudrate, timeout=10)  # Increased timeout to 10 seconds
                    time.sleep(2)  # Wait for the connection to establish
                if self.ser.in_waiting > 0:
                    print("Reading from serial port...")
                    line = self.ser.readline().decode('utf-8').rstrip()
                    print(f"Received data: {line}")
                    self.data_received.emit(line)
                    self.save_to_excel(line)
            except serial.SerialException as e:
                print(f"Serial error: {e}")
                if self.ser:
                    self.ser.close()
                time.sleep(3)

    def save_to_excel(self, data):
        try:
            values = data.split(',')
            if len(values) >= 22:
                df = pd.read_excel(self.excel_file)
                new_data = pd.DataFrame([values[:22]], columns=df.columns)
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_excel(self.excel_file, index=False)
        except Exception as e:
            print(f"Error saving to Excel: {e}")

    def stop(self):
        self.running = False
        if self.ser:
            self.ser.close()

    def __del__(self):
        self.stop()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        ex = Yer_istasyonu()
        ex.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Exception occurred: {e}")