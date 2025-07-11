import sys
import socket
import json
import threading
import time
import bluetooth
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, QTimer, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QImage, QPainter, QColor
import os
import signal

os.environ['DISPLAY'] = ':0'

header_font_size = 110
header_size = 180
order_font_size = 70
order_widget_size = 120


class CustomerDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Customer View")

        self.background = None
        self.scaled_background = None
        self.active_orders = []
        self.completed_orders = []

        self.load_background()
        self.init_ui()
        self.setCursor(Qt.BlankCursor)

        self.connectivity = Connectivity()
        self.connectivity.data_received.connect(self.update_display)
        self.connectivity.start()

        self.showFullScreen()

    def load_background(self):
        background_path = "Tellimuse_ekraani_taust.jpg"
        self.background = QImage(background_path)
        if self.background.isNull():
            print(f"Failed to load background image: {background_path}")

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.active_widget = QWidget()
        self.active_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.active_layout = QVBoxLayout(self.active_widget)
        self.active_layout.setAlignment(Qt.AlignTop)
        self.active_layout.setSpacing(10)
        self.active_layout.setContentsMargins(5, 5, 5, 5)

        self.completed_widget = QWidget()
        self.completed_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.completed_layout = QVBoxLayout(self.completed_widget)
        self.completed_layout.setAlignment(Qt.AlignTop)
        self.completed_layout.setSpacing(10)
        self.completed_layout.setContentsMargins(5, 5, 5, 5)

        main_layout.addWidget(self.active_widget, 1)
        main_layout.addWidget(self.completed_widget, 1)

        self.active_header = self.create_header_label("Küpseb")
        self.completed_header = self.create_header_label("Valmis")

        self.active_layout.addWidget(self.active_header)
        self.completed_layout.addWidget(self.completed_header)

        self.active_order_container, self.active_columns = self.create_order_container_with_columns()
        self.completed_order_container, self.completed_columns = self.create_order_container_with_columns()

        self.active_layout.addWidget(self.active_order_container)
        self.completed_layout.addWidget(self.completed_order_container)

    def create_header_label(self, text):
        label = QLabel(text)
        label.setFont(QFont("Bebas neue", header_font_size, QFont.Bold))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 100); border-radius: 10px; padding: 5px;")
        label.setFixedHeight(header_size)
        return label

    def create_order_container_with_columns(self):
        container = QWidget()
        container.setAttribute(Qt.WA_TranslucentBackground)
        container.setStyleSheet("background: transparent;")

        container.setFixedHeight(4 * order_widget_size + 4 * 5 + 20)
        
        # Create the main horizontal layout
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        columns = []
        for i in range(3):
            column_widget = QWidget()
            column_widget.setAttribute(Qt.WA_TranslucentBackground)
            column_layout = QVBoxLayout(column_widget)
            column_layout.setAlignment(Qt.AlignTop)
            column_layout.setSpacing(5)
            column_layout.setContentsMargins(0, 0, 0, 0)
            columns.append((column_widget, column_layout))
            main_layout.addWidget(column_widget)

            column_widget.hide()
        
        return container, columns

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.background.isNull():
            if self.scaled_background is None or self.scaled_background.size() != self.size():
                self.scale_background()
            painter.drawImage(self.rect(), self.scaled_background)
        else:
            painter.fillRect(self.rect(), QColor(200, 200, 200))

    def scale_background(self):
        if not self.background.isNull():
            self.scaled_background = self.background.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )

    def update_display(self, raw_data=None):
        try:
            orders_data = json.loads(raw_data)
            self.active_orders = orders_data.get('active_orders', [])
            self.completed_orders = orders_data.get('completed_orders', [])
            print(f"Parsed data: {len(self.active_orders)} active, {len(self.completed_orders)} completed")
        except json.JSONDecodeError as e:
            print(f"Failed to parse order data: {e}")
            return
        except KeyError as e:
            print(f"Missing key in order data: {e}")
            return
        
        self.update_orders(self.active_columns, self.active_orders)
        self.update_orders(self.completed_columns, self.completed_orders)

    def update_orders(self, columns, numbers):
        for column_widget, column_layout in columns:
            self.clear_layout(column_layout)
            column_widget.hide()
        
        visible_orders = numbers[:12]
        
        if not visible_orders:
            return
        
        order_count = len(visible_orders)
        if order_count <= 4:
            num_columns = 1
        elif order_count <= 8:
            num_columns = 2
        else:
            num_columns = 3
        
        orders_per_column = 4
        
        for col_idx in range(num_columns):
            column_widget, column_layout = columns[col_idx]
            column_widget.show()
            
            start_idx = col_idx * orders_per_column
            end_idx = min(start_idx + orders_per_column, len(visible_orders))
            
            for order_idx in range(start_idx, end_idx):
                if order_idx < len(visible_orders):
                    order_widget = self.create_order_widget(visible_orders[order_idx])
                    column_layout.addWidget(order_widget)
            
            column_layout.addStretch(1)

    def create_order_widget(self, order_number):
        order_widget = QFrame()
        order_widget.setStyleSheet("background-color: rgba(255, 255, 255, 200); border-radius: 10px; padding: 2px;")
        order_layout = QVBoxLayout(order_widget)
        order_layout.setContentsMargins(5, 5, 5, 5)
        order_label = QLabel(f"{str(order_number).zfill(3)}")
        order_label.setFont(QFont("Bebas neue", order_font_size))
        order_label.setAlignment(Qt.AlignCenter)
        order_layout.addWidget(order_label)
        order_widget.setFixedHeight(order_widget_size)
        return order_widget

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def cleanup(self):
        print("Cleaning up...")
        if hasattr(self, 'connectivity'):
            self.connectivity.stop()
            self.connectivity.wait()
        self.close()
        QApplication.quit()


class Connectivity(QThread):
    # Signal to send data to the main thread
    data_received = pyqtSignal(str)  # Emits the raw JSON string
    
    def __init__(self):
        super().__init__()
        self.running = True
        
        self.bluetooth_socket = None
        self.bluetooth_client = None
        self.bluetooth_port = 1
        
        self.network_socket = None
        self.network_port = 5000
        
    def run(self):
        self.setup_bluetooth_server()
        self.setup_network_server()
        
        bluetooth_thread = threading.Thread(target=self.bluetooth_loop, daemon=True)
        network_thread = threading.Thread(target=self.network_loop, daemon=True)
        
        bluetooth_thread.start()
        network_thread.start()
        
        while self.running:
            time.sleep(0.1)
    
    def setup_bluetooth_server(self):
        try:
            self.bluetooth_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            self.bluetooth_socket.bind(("", self.bluetooth_port))
            self.bluetooth_socket.listen(1)
            print(f"Bluetooth server listening on port {self.bluetooth_port}")
        except Exception as e:
            print(f"Failed to setup Bluetooth server: {e}")
            self.bluetooth_socket = None
    
    def setup_network_server(self):
        try:
            self.network_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.network_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.network_socket.bind(('0.0.0.0', self.network_port))
            self.network_socket.listen(1)
            print(f"Network server listening on port {self.network_port}")
        except Exception as e:
            print(f"Failed to setup network server: {e}")
            self.network_socket = None
    
    def bluetooth_loop(self):
        if not self.bluetooth_socket:
            return
            
        while self.running:
            try:
                print("Waiting for Bluetooth connection...")
                self.bluetooth_socket.settimeout(1)
                try:
                    client_socket, address = self.bluetooth_socket.accept()
                    self.bluetooth_client = client_socket
                    print(f"Bluetooth connected from {address}")
                except bluetooth.BluetoothError:
                    continue
                
                while self.running and self.bluetooth_client:
                    try:
                        self.bluetooth_client.settimeout(10)
                        data = self.bluetooth_client.recv(1024)
                        
                        if not data:
                            print("Bluetooth connection closed")
                            self.cleanup_bluetooth()
                            break
                        
                        if data == b'ping':
                            self.bluetooth_client.sendall(b'pong')
                        else:
                            raw_data = data.decode()
                            print(f"Received Bluetooth data: {raw_data}")
                            self.data_received.emit(raw_data)
                            
                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"Bluetooth error: {e}")
                        self.cleanup_bluetooth()
                        break
                        
            except Exception as e:
                print(f"Bluetooth server error: {e}")
                time.sleep(1)
    
    def network_loop(self):
        if not self.network_socket:
            return
            
        while self.running:
            try:
                self.network_socket.settimeout(1)
                try:
                    client_socket, address = self.network_socket.accept()
                    print(f"Network connection from {address}")
                    
                    try:
                        client_socket.settimeout(2)
                        data = client_socket.recv(1024)
                        
                        if data == b'ping':
                            client_socket.sendall(b'pong')
                        else:
                            raw_data = data.decode()
                            print(f"Received Network data: {raw_data}")
                            self.data_received.emit(raw_data)
                            
                    except socket.timeout:
                        pass
                    finally:
                        client_socket.close()
                        
                except socket.timeout:
                    continue
                    
            except Exception as e:
                print(f"Network server error: {e}")
                time.sleep(1)
    
    def cleanup_bluetooth(self):
        if self.bluetooth_client:
            try:
                self.bluetooth_client.close()
            except:
                pass
            self.bluetooth_client = None
    
    def stop(self):
        self.running = False
        self.cleanup_bluetooth()
        
        if self.bluetooth_socket:
            try:
                self.bluetooth_socket.close()
            except:
                pass
            self.bluetooth_socket = None
            
        if self.network_socket:
            try:
                self.network_socket.close()
            except:
                pass
            self.network_socket = None

def signal_handler(signum, frame):
    print("Ctrl+C received. Initiating cleanup...")

    window.cleanup()
    sys.exit(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CustomerDisplay()

    signal.signal(signal.SIGINT, signal_handler)
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    window.show()

    sys.exit(app.exec_())