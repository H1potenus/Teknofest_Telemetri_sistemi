import sys
import random
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout, QSizePolicy, QTextEdit, QTableWidget, QTableWidgetItem,QComboBox, QErrorMessage, QProgressBar
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
import traceback  # Hata ayıklama için
import io
import folium
from PyQt6.QtWebEngineWidgets import QWebEngineView



class Yer_istasyonu(QWidget): #ana kodun olduğu yer
    def __init__(self):
        super().__init__()
        self.initUI()
        self.serial_thread = SerialData() #serialin bağlanması
        self.serial_thread.data_received.connect(self.update_data_label)
        self.serial_thread.data_received.connect(self.update_map_position)  # Connect to map update
        self.serial_thread.error_signal.connect(self.handle_error)  # Hata sinyali bağlantısı
        self.serial_thread.start()

        self.camera_thread = Camera() #kameranın bağlanması
        self.camera_thread.frame_ready.connect(self.update_camera_label)
        self.camera_thread.start()

    def handle_error(self, error_message): #pop up erro mesajı ilerde geliştirilmeli
        # Hata mesajını GUI'de göstermek için
        error_dialog = QErrorMessage(self)
        error_dialog.showMessage(error_message)

    def closeEvent(self, event): #kapama
        self.serial_thread.stop()
        self.camera_thread.stop()
        event.accept()

    def initUI(self):
        # arayüz
        self.showFullScreen()
        self.setWindowTitle('Yer İstasyonu') #titlew

        #haritalar geldi hos geldi
        # Initialize the map
        self.harita = Harita(self)
        self.harita.setGeometry(650, 450, 600, 300)
        self.harita.show()

        self.data_count = 0

        # Add status widget
        self.statusWidget = StatusWidget(self)
        self.statusWidget.setGeometry(620, 120, 200, 100)
        self.statusWidget.show()

        # kayıt için green red mevzusu
        self.recording_status_label = QLabel(self)
        self.recording_status_label.setGeometry(1250, 540, 300, 50)  # Adjust size and position as needed
        self.recording_status_label.setStyleSheet("background-color: red;")
        self.recording_status_label.setText("Not Recording")
        self.recording_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recording_status_label.show()

        # Kamera butonları ekle
        self.start_record_button = QPushButton('Videoyu Kaydetmeye Başla', self)
        self.start_record_button.setGeometry(1250, 420, 300, 50)  # Adjust size and position as needed
        self.start_record_button.clicked.connect(self.start_recording)
        self.start_record_button.show()

        self.stop_record_button = QPushButton('Kaydı Durdur', self)
        self.stop_record_button.setGeometry(1250, 480, 300, 50)  # Adjust size and position as needed
        self.stop_record_button.clicked.connect(self.stop_recording)
        self.stop_record_button.show()

        # COM port selection
        self.comPortComboBox = QComboBox(self)
        self.comPortComboBox.addItems(["COM6", "COM5", "COM4", "COM3"])
        self.comPortComboBox.setGeometry(620, 80, 100, 40)
        self.comPortComboBox.setCurrentText("COM6")  # Default COM port
        self.comPortComboBox.show()

        # Baud rate selection
        self.baudRateComboBox = QComboBox(self)
        self.baudRateComboBox.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baudRateComboBox.setGeometry(730, 80, 100, 40)
        self.baudRateComboBox.setCurrentText("9600")  # Default baud rate
        self.baudRateComboBox.show()

        self.comPortComboBox.currentTextChanged.connect(self.update_serial_settings)
        self.baudRateComboBox.currentTextChanged.connect(self.update_serial_settings)

        # ekrana pitch roll ve yaw değerlerini ekleme
        self.pitch_label = QLabel("Pitch: 0", self)
        self.pitch_label.setFont(QFont('Arial', 10))
        self.pitch_label.setGeometry(940, 420, 200, 40)
        self.pitch_label.setStyleSheet("color: red;")
        self.pitch_label.show()

        self.roll_label = QLabel("Roll: 0", self)
        self.roll_label.setFont(QFont('Arial', 10))
        self.roll_label.setGeometry(1020, 420, 200, 40)
        self.roll_label.setStyleSheet("color: red;")
        self.roll_label.show()

        self.yaw_label = QLabel("Yaw: 0", self)
        self.yaw_label.setFont(QFont('Arial', 10))
        self.yaw_label.setGeometry(1100, 420, 200, 40)
        self.yaw_label.setStyleSheet("color: red;")
        self.yaw_label.show()

        # kamera
        self.camera_label = QLabel(self)
        self.camera_label.setGeometry(1250, 200, 300, 200)  # Adjust size and position as needed
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
        for i, width in enumerate(column_widths): #off for loopunu en guzel kullandigim 2. yer
            self.data_table.setColumnWidth(i, width)

        self.data_table.show()

        # Create text area for displaying data
        self.data_text = QTextEdit(self)
        self.data_text.setGeometry(10, 10, 400, 200)
        self.data_text.setReadOnly(True)
        #self.data_text.show() #artık gerekli değil ama lazım olur bi de tam ekran olmayınca göküyo anlamdım aq

        # grafikleri oluştur
        self.sicaklikGrafik = Grafikler(self, title="sicaklik graf", xlabel="zaman", ylabel="sicaklik",     x=10, y=210, width=300, height=200)
        self.basincGrafik = Grafikler(self, title="basinc graf", xlabel="zaman", ylabel="basinc",           x=320, y=210, width=300, height=200)
        self.hizGrafik = Grafikler(self, title="hiz graf", xlabel="zaman", ylabel="hiz",                    x=630, y=210, width=300, height=200)
        self.yükseklikGrafik = Grafikler(self, title="Yükseklik graf", xlabel="zaman", ylabel="yükseklik",  x=10, y=420, width=300, height=200)
        self.pilGerilimGrafik = Grafikler(self, title="Pil Gerilimi graf", xlabel="zaman", ylabel="gerilim",x=320, y=420, width=300, height=200)

        # Grafikleri göster ilerde daha çok grafik eklenicek
        self.sicaklikGrafik.show()
        self.basincGrafik.show()
        self.hizGrafik.show()
        self.yükseklikGrafik.show()
        self.pilGerilimGrafik.show()

        # Takımımızın adını ekle cool font eklendi
        self.OurName = QLabel("Turkish Defenders",self)
        self.OurName.setFont(QFont('Algerian', 36))
        self.OurName.move(10,10)
        self.OurName.adjustSize()
        self.OurName.show()

        #Ayrilma Bekleniyor labeli
        self.AyrilmaLabel = QLabel("Kod Bekleniyor", self)
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

        # Sayı ve harf kutuları için QComboBox widget'ları oluştur 4 haneli giriş
        self.numInput1 = QComboBox(self)
        self.numInput1.addItems([str(i) for i in range(10)])
        self.numInput1.setGeometry(1250, 135, 50, 40)
        self.numInput1.show()

        self.letterInput1 = QComboBox(self)
        self.letterInput1.addItems(["R", "G", "B", "N"])
        self.letterInput1.setGeometry(1300, 135, 50, 40)
        self.letterInput1.show()

        self.numInput2 = QComboBox(self)
        self.numInput2.addItems([str(i) for i in range(10)])
        self.numInput2.setGeometry(1350, 135, 50, 40)
        self.numInput2.show()

        self.letterInput2 = QComboBox(self)
        self.letterInput2.addItems(["R", "G", "B", "N"])
        self.letterInput2.setGeometry(1400, 135, 50, 40)
        self.letterInput2.show()

        # Buttonları ekle BUtonların tamamı


        #BUton1
        self.SeperateButton = QPushButton('Buton1', self)
        self.SeperateButton.setFixedSize(120, 80)
        self.SeperateButton.move(850, 80)
        self.SeperateButton.setFont(QFont('Arial', 15))
        self.SeperateButton.clicked.connect(self.button1Clicked)
        self.SeperateButton.show()

        #buton2
        self.SeperateButton = QPushButton('Buton2', self)
        self.SeperateButton.setFixedSize(120, 80)
        self.SeperateButton.move(975, 80)
        self.SeperateButton.setFont(QFont('Arial', 15))
        self.SeperateButton.clicked.connect(self.button2Clicked)
        self.SeperateButton.show()

        #buton3
        self.SeperateButton = QPushButton('Buton3', self)
        self.SeperateButton.setFixedSize(120, 80)
        self.SeperateButton.move(1100, 80)
        self.SeperateButton.setFont(QFont('Arial', 15))
        self.SeperateButton.clicked.connect(self.button3Clicked)
        self.SeperateButton.show()

        #gönderme butonu
        self.SendButton = QPushButton('SEND', self)
        self.SendButton.setFixedSize(150, 40)
        self.SendButton.move(1310,80)
        self.SendButton.setFont(QFont('Arial', 15))
        self.SendButton.clicked.connect(self.SendButtonClicked)
        self.SendButton.show()

    def update_map_position(self, data):
        try:
            values = data.split(',')
            enlem = float(values[13])
            boylam = float(values[14])
            self.harita.update_map(enlem, boylam)
        except (ValueError, IndexError) as e:
            print(f"Error updating map position: {e}")

    def start_recording(self):
        self.camera_thread.start_recording()
        self.update_recording_status(True)

    def stop_recording(self):
        self.camera_thread.stop_recording()
        self.update_recording_status(False)

    #serial com secme
    def update_serial_settings(self):
        # Stop the existing serial thread
        if hasattr(self, 'serial_thread'):
            self.serial_thread.stop()

        # Get selected COM port and baud rate
        com_port = self.comPortComboBox.currentText()
        baud_rate = int(self.baudRateComboBox.currentText())

        # Start a new SerialData thread with the selected settings
        self.serial_thread = SerialData(port=com_port, baudrate=baud_rate)
        self.serial_thread.data_received.connect(self.update_data_label)
        self.serial_thread.error_signal.connect(self.handle_error)
        self.serial_thread.start()

    def update_recording_status(self, is_recording):
        if is_recording:
            self.recording_status_label.setStyleSheet("background-color: green;")
            self.recording_status_label.setText("Recording")
        else:
            self.recording_status_label.setStyleSheet("background-color: red;")
            self.recording_status_label.setText("Not Recording")

    def update_camera_label(self, image): #kamera kısmı
        try:
            scaled_image = image.scaled(self.camera_label.size(), Qt.AspectRatioMode.KeepAspectRatio) #kamera artık zoomlu değil
            self.camera_label.setPixmap(QPixmap.fromImage(scaled_image))
        except Exception as e: #error kısmı
            print(f"Error scaling image: {e}")

    def update_data_label(self, data): #bura önemli, dataları dataframe e koyuyoruz
        current_text = self.data_text.toPlainText()
        updated_text = f"{data}\n{current_text}"
        self.data_text.setPlainText(updated_text)

        try:
            values = data.split(',')
            if len(values) >= 21:
                # Verileri kontrol et ve geçerli olmayan verileri ayıkla
                values = [value if self.is_float(value) else '0' for value in values]
                #verileri atama

                # Extract the status value and update the status widget
                status_value = int(values[1])
                self.statusWidget.update_status(status_value)

                pressure = float(values[5])
                temp = float(values[11])
                speed = float(values[10])
                altitude = float(values[7])
                voltage = float(values[12])

                pitch = float(values[16])
                roll = float(values[17])
                yaw = float(values[18])

                enlem = float(values[13])
                boylam = float(values[14])

                #grafiklere atama
                self.sicaklikGrafik.add_data(temp)
                self.basincGrafik.add_data(pressure)
                self.hizGrafik.add_data(speed)
                self.yükseklikGrafik.add_data(altitude)
                self.pilGerilimGrafik.add_data(voltage)
                #simulasyona atama
                self.simulation2D.set_yaw(yaw)



                # QLabel'leri güncelle
                self.pitch_label.setText(f"Pitch: {pitch}")
                self.roll_label.setText(f"Roll: {roll}")
                self.yaw_label.setText(f"Yaw: {yaw}")

                # Insert data into the table at the top excele kaydetme için öenemli
                self.data_table.insertRow(0)
                for i, value in enumerate(values[:22]):
                    self.data_table.setItem(0, i, QTableWidgetItem(value))
        except ValueError:
            print("Invalid data received")

    def is_float(self, value): #tam sayı erroru çözüm similasyonda işe yarıyo
        try:
            float(value)
            return True
        except ValueError:
            return False

    def updateLabelSize(self):
        #bazı yazılar sıkıntı çıkartıyor, garanti olsun diye adjssize ekledim
        self.AyrilmaLabel.adjustSize()
        self.kodlabel.adjustSize()

    def button1Clicked(self):
        #ayrilma butonu tıklandığında ne olur
        self.AyrilmaLabel.setText("3G7N")
        self.updateLabelSize() #ilerde buraya seriale mesaj gönderme gelicek
        try:
            if self.serial_thread.ser and self.serial_thread.ser.is_open:
                self.serial_thread.ser.write(b'3G7N')  # Ensure the message is in bytes
            else:
                print("Serial port is not open.")
        except Exception as e:
            print(f"Error sending data: {e}")

    def button2Clicked(self):
        #ayrilma butonu tıklandığında ne olur
        self.AyrilmaLabel.setText("5B5R")
        self.updateLabelSize()
        try:
            if self.serial_thread.ser and self.serial_thread.ser.is_open:
                self.serial_thread.ser.write(b'5B5R')  # Ensure the message is in bytes
            else:
                print("Serial port is not open.")
        except Exception as e:
            print(f"Error sending data: {e}")

    def button3Clicked(self):
        #ayrilma butonu tıklandığında ne olur
        self.AyrilmaLabel.setText("2G8R")
        self.updateLabelSize()
        try:
            if self.serial_thread.ser and self.serial_thread.ser.is_open:
                self.serial_thread.ser.write(b'2G8R')  # Ensure the message is in bytes
            else:
                print("Serial port is not open.")
        except Exception as e:
            print(f"Error sending data: {e}")


    def SendButtonClicked(self):
        # Kombinasyonu oluştur ,4 haneli kod
        code = self.numInput1.currentText() + self.letterInput1.currentText() + self.numInput2.currentText() + self.letterInput2.currentText()
        self.kodlabel.setText(code)
        self.updateLabelSize()
        try:
            # Encode the code and send it via serial
            self.serial_thread.ser.write(f'{code}\n'.encode('utf-8'))
            print(f"Sent: {code}")
        except Exception as e:
            error_message = f"Error sending data: {e}"
            print(error_message)
            self.serial_thread.error_signal.emit(error_message)

    def drawBackground(self, qp):
        #arkaplanın ne renk olduğunu seç
        #şuan bu metod kullanılmıyor belki lazım olur
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

class Grafikler(QWidget): #grafikler cllasss ı
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

        # Y ekseni sınırlarını belirliyoruz
        min_y = min(self.y_data) if self.y_data else 0
        max_y = max(self.y_data) if self.y_data else 1

        # Eğer min ve max y değerleri aynıysa, sınırları biraz genişletiyoruz
        if min_y == max_y:
            min_y -= 1
            max_y += 1

        self.ax.set_ylim(min_y, max_y)

        self.canvas.draw()

    def add_data(self, y): #data ekleme
        if len(self.x_data) == 0:
            self.x_data.append(0)
        else:
            self.x_data.append(self.x_data[-1] + 1)
        self.y_data.append(y)
        self.x_data = self.x_data[-20:]
        self.y_data = self.y_data[-20:]
        self.update_plot()

class Camera(QThread): #kamera kısmı
    frame_ready = pyqtSignal(QImage)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.capture = None
        self.recording = False
        self.video_writer = None

    def run(self):
        self.capture = cv2.VideoCapture(1)  # Değiştirmeniz gerekebilir

        while self.running:
            ret, frame = self.capture.read()
            if ret:
                if self.recording and self.video_writer is not None:
                    self.video_writer.write(frame)

                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.frame_ready.emit(qt_image)

    def start_recording(self):
        if not self.recording:
            try:
                filename = self.get_unique_filename()
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                self.video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))
                self.recording = True
                print(f"Recording started: {filename}")
            except Exception as e:
                print(f"Error starting recording: {e}")

    def stop_recording(self):
        if self.recording:
            try:
                self.recording = False
                self.video_writer.release()
                self.video_writer = None
                print("Recording stopped")
            except Exception as e:
                print(f"Error stopping recording: {e}")

    def stop(self):
        self.running = False
        if self.capture.isOpened():
            self.capture.release()
        if self.recording and self.video_writer is not None:
            self.video_writer.release()
            self.recording = False

    def __del__(self):
        self.stop()

    def get_unique_filename(self, base_name='video', ext='.avi'):
        counter = 1
        filename = f"{base_name}{counter}{ext}"
        while os.path.exists(filename):
            counter += 1
            filename = f"{base_name}{counter}{ext}"
        return filename


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
        qp.translate(int(w / 2), int(h / 2))
        qp.rotate(self.yaw)

        # Draw satellite body
        rect_width = 100
        rect_height = 30
        qp.setBrush(QBrush(Qt.GlobalColor.blue))
        qp.drawRect(int(-rect_width / 2), int(-rect_height / 2), int(rect_width), int(rect_height))

        # Draw directional indicator (front)
        qp.setBrush(QBrush(Qt.GlobalColor.red))
        qp.drawRect(int(-5), int(-rect_height / 2 - 10), int(10), int(10))

        # Draw solar panels
        panel_width = 80
        panel_height = 10
        qp.setBrush(QBrush(Qt.GlobalColor.gray))
        qp.drawRect(int(-rect_width / 2 - panel_width), int(-panel_height / 2), int(panel_width), int(panel_height))
        qp.drawRect(int(rect_width / 2), int(-panel_height / 2), int(panel_width), int(panel_height))

        # Draw an outline for better visibility
        qp.setPen(QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.SolidLine))
        qp.setBrush(Qt.BrushStyle.NoBrush)
        qp.drawRect(int(-rect_width / 2), int(-rect_height / 2), int(rect_width), int(rect_height))
        qp.drawRect(int(-5), int(-rect_height / 2 - 10), int(10), int(10))
        qp.drawRect(int(-rect_width / 2 - panel_width), int(-panel_height / 2), int(panel_width), int(panel_height))
        qp.drawRect(int(rect_width / 2), int(-panel_height / 2), int(panel_width), int(panel_height))

        # Reset transformation
        qp.resetTransform()

class Harita(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        self.map_view = QWebEngineView()
        self.layout.addWidget(self.map_view)
        self.setLayout(self.layout)
        self.update_map(0, 0)

    def update_map(self, lat, lon):
        map = folium.Map(location=[lat, lon], zoom_start=5)
        folium.Marker([lat, lon], tooltip="Satellite Position").add_to(map)

        data = io.BytesIO()
        map.save(data, close_file=False)
        self.map_view.setHtml(data.getvalue().decode())


class SerialData(QThread): #bura önemli, ana error handling kısmı burda
    data_received = pyqtSignal(str)
    error_signal = pyqtSignal(str)  # Hata mesajları için yeni sinyal

    def __init__(self, port='COM6', baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.excel_file = self.get_unique_filename()
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
            error_message = f"Error initializing Excel file: {e}\n{traceback.format_exc()}"
            print(error_message)
            self.error_signal.emit(error_message)

    def run(self):
        while self.running:
            try:
                if self.ser is None or not self.ser.is_open:
                    print(f"Opening serial port {self.port} with baudrate {self.baudrate}...")
                    self.ser = serial.Serial(self.port, self.baudrate, timeout=10)
                    time.sleep(2)
                if self.ser.in_waiting > 0:
                    print("Reading from serial port...")
                    line = self.ser.readline().decode('utf-8').rstrip()
                    print(f"Received data: {line}")
                    self.data_received.emit(line)
                    self.save_to_excel(line)
            except serial.SerialException as e:
                error_message = f"Serial error: {e}\n{traceback.format_exc()}"
                print(error_message)
                self.error_signal.emit(error_message)
                if self.ser:
                    self.ser.close()
                time.sleep(3)
            except Exception as e:
                error_message = f"Unexpected error: {e}\n{traceback.format_exc()}"
                print(error_message)
                self.error_signal.emit(error_message)

    def save_to_excel(self, data):
        try:
            values = data.split(',')
            if len(values) >= 22:
                # Verileri kontrol et ve geçerli olmayan verileri ayıkla
                values = [value if self.is_float(value) else 'X' for value in values]

                df = pd.read_excel(self.excel_file)
                new_data = pd.DataFrame([values[:22]], columns=df.columns)
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_excel(self.excel_file, index=False)
        except Exception as e:
            error_message = f"Error saving to Excel: {e}\n{traceback.format_exc()}"
            print(error_message)
            self.error_signal.emit(error_message)

    def is_float(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def stop(self):
        self.running = False
        if self.ser:
            self.ser.close()

    def __del__(self):
        self.stop()
class StatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        # Create and configure the progress bar
        self.progressBar = QProgressBar(self)
        self.progressBar.setRange(0, 5)
        self.layout.addWidget(self.progressBar)

        # Create and configure the label for status text
        self.statusLabel = QLabel("Statü: 0 - uçuşa hazır", self)
        self.statusLabel.setFont(QFont('Arial', 15))
        self.layout.addWidget(self.statusLabel)

        self.status_texts = {
            0: "0 - uçuşa hazır",
            1: "1 - yükselme",
            2: "2 - uydu iniş",
            3: "3 - ayrılma",
            4: "4 - görev yükü iniş",
            5: "5 - kurtarma"
        }

    def update_status(self, status_value):
        # Update the progress bar value
        self.progressBar.setValue(status_value)

        # Update the status label text
        status_text = self.status_texts.get(status_value, "Unknown status")
        self.statusLabel.setText(f"Statü: {status_text}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        ex = Yer_istasyonu()
        ex.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Exception occurred: {e}")