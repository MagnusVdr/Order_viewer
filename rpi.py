import sys
import socket
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, QTimer, QSize
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
        self.load_background()
        self.active_orders = []
        self.completed_orders = []
        self.init_ui()
        self.server_socket = None
        self.start_server()
        self.setCursor(Qt.BlankCursor)
        self.showFullScreen()

    def load_background(self):
        background_path = "Tellimuse_ekraani_taust.jpg"  # Make sure this file exists in the same directory
        self.background = QImage(background_path)
        if self.background.isNull():
            print(f"Failed to load background image: {background_path}")

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create left side (active orders)
        self.active_widget = QWidget()
        self.active_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.active_layout = QVBoxLayout(self.active_widget)
        self.active_layout.setAlignment(Qt.AlignTop)
        self.active_layout.setSpacing(10)

        # Create right side (completed orders)
        self.completed_widget = QWidget()
        self.completed_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.completed_layout = QVBoxLayout(self.completed_widget)
        self.completed_layout.setAlignment(Qt.AlignTop)
        self.completed_layout.setSpacing(10)

        # Add both widgets to main layout with equal stretch (50% each)
        main_layout.addWidget(self.active_widget, 1)  # stretch factor 1 = 50%
        main_layout.addWidget(self.completed_widget, 1)  # stretch factor 1 = 50%

        # Create headers
        self.active_header = self.create_header_label("Küpseb")
        self.completed_header = self.create_header_label("Valmis")

        self.active_layout.addWidget(self.active_header)
        self.completed_layout.addWidget(self.completed_header)

        # Create fixed column structures
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
        """Create a fixed-height container with 3 pre-made columns"""
        container = QWidget()
        container.setAttribute(Qt.WA_TranslucentBackground)
        container.setStyleSheet("background: transparent;")
        # Set a fixed height that can accommodate 4 orders + spacing
        container.setFixedHeight(4 * order_widget_size + 4 * 5 + 20)  # 4 orders + gaps + padding
        
        # Create the main horizontal layout
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create 3 columns (we'll show/hide them as needed)
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
            # Initially hide all columns
            column_widget.hide()
        
        return container, columns

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.background.isNull():
            if self.scaled_background is None or self.scaled_background.size() != self.size():
                self.scale_background()
            painter.drawImage(self.rect(), self.scaled_background)
        else:
            painter.fillRect(self.rect(), QColor(200, 200, 200))  # Light gray background

    def scale_background(self):
        if not self.background.isNull():
            self.scaled_background = self.background.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )

    def update_display(self):
        self.update_orders(self.active_columns, self.active_orders)
        self.update_orders(self.completed_columns, self.completed_orders)

    def update_orders(self, columns, numbers):
        """Update orders using pre-existing column structure"""
        # Clear all columns first
        for column_widget, column_layout in columns:
            self.clear_layout(column_layout)
            column_widget.hide()
        
        # Only show first 12 orders maximum (4 per column × 3 columns)
        visible_orders = numbers[:12]
        
        if not visible_orders:
            return
        
        # Determine number of columns based on order count
        order_count = len(visible_orders)
        if order_count <= 4:
            num_columns = 1
        elif order_count <= 8:
            num_columns = 2
        else:
            num_columns = 3
        
        # Show and populate the required columns
        orders_per_column = 4  # Maximum 4 orders per column
        
        for col_idx in range(num_columns):
            column_widget, column_layout = columns[col_idx]
            column_widget.show()
            
            # Add orders to this column
            start_idx = col_idx * orders_per_column
            end_idx = min(start_idx + orders_per_column, len(visible_orders))
            
            for order_idx in range(start_idx, end_idx):
                if order_idx < len(visible_orders):
                    order_widget = self.create_order_widget(visible_orders[order_idx])
                    column_layout.addWidget(order_widget)
            
            # Add stretch to fill remaining space
            column_layout.addStretch(1)

    def create_order_widget(self, order_number):
        order_widget = QFrame()
        order_widget.setStyleSheet("background-color: rgba(255, 255, 255, 200); border-radius: 10px; padding: 2px;")
        order_layout = QVBoxLayout(order_widget)
        order_layout.setContentsMargins(10, 10, 10, 10)
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

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', 5000))  # Listen on all available interfaces
        self.server_socket.listen(1)
        self.server_socket.setblocking(False)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_for_connection)
        self.timer.start(100)

    def check_for_connection(self):
        try:
            client_socket, address = self.server_socket.accept()
            data = client_socket.recv(1024)

            if data == b'ping':
                client_socket.sendall(b'pong')
            else:
                try:
                    orders_data = json.loads(data.decode())
                    self.active_orders = orders_data['active_orders']
                    self.completed_orders = orders_data['completed_orders']
                    self.update_display()
                except json.JSONDecodeError:
                    print(f"Received invalid JSON data: {data}")

            client_socket.close()
        except BlockingIOError:
            pass  # No incoming connection, just continue
        except Exception as e:
            print(f"Error in check_for_connection: {e}")

    def cleanup(self):
        print("Cleaning up...")
        if self.server_socket:
            self.server_socket.close()
        self.close()
        QApplication.quit()


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