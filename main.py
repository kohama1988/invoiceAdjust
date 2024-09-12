import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, 
                             QLabel, QLineEdit, QMessageBox, QProgressBar, QSpacerItem, QSizePolicy, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QFont
from PIL import Image
import cv2
import numpy as np

# 导入之前的函数
from process_receipt import detectAndCorrectReceipt
from resize import resize_image
from layout_images import layout_images, create_pages

class WorkerThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = True

    def run(self):
        self.is_running = True
        self.function(*self.args, **self.kwargs, progress_callback=self.progress.emit, stop_check=self.stop_check)
        self.finished.emit()

    def stop_check(self):
        return not self.is_running

    def quit(self):
        self.is_running = False
        super().quit()

class ReceiptProcessorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.threads = []
        self.input_folder = ''
        self.progress_label = QLabel('', self)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Receipt Processor')
        self.setGeometry(100, 100, 600, 400)

        main_layout = QVBoxLayout()

        # STEP 1: 选择图片文件夹
        step1_layout = self.create_step_layout("STEP 1", "select folder")
        self.add_button = step1_layout.itemAt(2).widget()
        self.add_button.clicked.connect(self.add_images)
        self.image_count_label = QLabel('', self)
        step1_layout.addWidget(self.image_count_label)
        main_layout.addLayout(step1_layout)

        # 显示选择的文件夹路径
        self.folder_label = QLabel('Not select folder yet', self)
        main_layout.addWidget(self.folder_label)

        main_layout.addWidget(self.create_separator())

        # STEP 2: 提取发票
        step2_layout = self.create_step_layout("STEP 2", "Extract Receipts")
        self.extract_button = step2_layout.itemAt(2).widget()
        self.extract_button.clicked.connect(self.extract_receipts)
        self.extract_progress = QProgressBar(self)
        step2_layout.addWidget(self.extract_progress)
        step2_layout.addWidget(self.progress_label)
        main_layout.addLayout(step2_layout)

        main_layout.addWidget(self.create_separator())

        # STEP 3: Resize
        step3_layout = self.create_step_layout("STEP 3", "Resize")
        resize_input_layout = QHBoxLayout()
        resize_input_layout.addWidget(QLabel('Scale factor (0-1):'))
        self.resize_input = QLineEdit('0.3', self)
        resize_input_layout.addWidget(self.resize_input)
        self.resize_button = step3_layout.itemAt(2).widget()
        self.resize_button.clicked.connect(self.resize_images)
        step3_layout.addLayout(resize_input_layout)
        main_layout.addLayout(step3_layout)

        main_layout.addWidget(self.create_separator())

        # STEP 4: 开始排列
        step4_layout = self.create_step_layout("STEP 4", "Arrange")
        self.start_button = step4_layout.itemAt(2).widget()
        self.start_button.clicked.connect(self.start_processing)
        self.arrange_progress = QProgressBar(self)
        step4_layout.addWidget(self.arrange_progress)
        main_layout.addLayout(step4_layout)

        main_layout.addStretch(1)

        # 添加logo、开发者信息和版本号
        bottom_layout = QHBoxLayout()

        logo_label = QLabel(self)
        pixmap = QPixmap('logo.jpg')
        scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        bottom_layout.addWidget(logo_label)

        bottom_layout.addStretch(1)

        dev_version_layout = QVBoxLayout()
        developer_label = QLabel('Developer: yang.yu@vibracoustic.com', self)
        developer_label.setAlignment(Qt.AlignRight)
        dev_version_layout.addWidget(developer_label)

        version_label = QLabel('ver 1.0', self)
        version_label.setAlignment(Qt.AlignRight)
        dev_version_layout.addWidget(version_label)

        bottom_layout.addLayout(dev_version_layout)

        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

    def create_step_layout(self, step_text, button_text):
        layout = QHBoxLayout()
        step_label = QLabel(step_text, self)
        step_label.setFont(QFont('Arial', 12, QFont.Bold))
        layout.addWidget(step_label)
        layout.addSpacing(20)
        button = QPushButton(button_text, self)
        button.setFixedWidth(120)
        layout.addWidget(button)
        layout.addStretch(1)
        return layout

    def create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def disable_all_except(self, exception):
        for layout in [self.layout().itemAt(i).layout() for i in range(self.layout().count()) if isinstance(self.layout().itemAt(i), QHBoxLayout)]:
            for i in range(layout.count()):
                item = layout.itemAt(i).widget()
                if isinstance(item, QPushButton) and item != exception:
                    item.setEnabled(False)

    def enable_all(self):
        for layout in [self.layout().itemAt(i).layout() for i in range(self.layout().count()) if isinstance(self.layout().itemAt(i), QHBoxLayout)]:
            for i in range(layout.count()):
                item = layout.itemAt(i).widget()
                if isinstance(item, QPushButton):
                    item.setEnabled(True)

    def add_images(self):
        self.disable_all_except(self.add_button)
        self.input_folder = QFileDialog.getExistingDirectory(self, "Select Folder...")
        if self.input_folder:
            self.folder_label.setText(f'Selected folder: {self.input_folder}')
            image_count = len([f for f in os.listdir(self.input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
            self.image_count_label.setText(f'{image_count} images found')
        self.enable_all()

    def extract_receipts(self):
        if not self.input_folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first!")
            return

        receipts_folder = os.path.join(self.input_folder, 'receipts')
        if not os.path.exists(receipts_folder):
            os.makedirs(receipts_folder)

        try:
            self.disable_all_except(self.extract_button)
            self.extract_progress.setValue(0)

            # 创建一个 QThread 对象
            self.thread = QThread()
            self.threads.append(self.thread)  # Add to thread list
            # 创建一个 worker 对象
            self.worker = Worker(detectAndCorrectReceipt, self.input_folder)
            # 将 worker 移动到线程
            self.worker.moveToThread(self.thread)
            # 连接信号和槽
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.update_extract_progress)
            # 启动线程
            self.thread.start()

            # 最后，线程结束时恢复按钮状态并显示完成消息
            self.thread.finished.connect(
                lambda: self.enable_all()
            )
            self.thread.finished.connect(
                lambda: QMessageBox.information(self, "Completed", "Receipts extracted and saved in receipts folder.")
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error occurred while processing images: {str(e)}")
            self.enable_all()

    def update_extract_progress(self, value, current, total):
        self.extract_progress.setValue(value)
        self.progress_label.setText(f'({current}/{total})')

    def resize_images(self):
        if not self.input_folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first!")
            return
        try:
            scale_factor = float(self.resize_input.text())
            if not 0 < scale_factor <= 1:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Warning", "Please enter a valid scale factor (between 0 and 1)!")
            return

        receipts_folder = os.path.join(self.input_folder, 'receipts')
        resize_folder = os.path.join(self.input_folder, 'resize')
        if not os.path.exists(resize_folder):
            os.makedirs(resize_folder)

        for filename in os.listdir(receipts_folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                input_path = os.path.join(receipts_folder, filename)
                output_path = os.path.join(resize_folder, filename)
                resize_image(input_path, output_path, scale_factor)

        QMessageBox.information(self, "Completed", "Images resized and saved in resize folder.")

    def start_processing(self):
        if not self.input_folder:
            QMessageBox.warning(self, "Warning", "Please select a folder first!")
            return

        resize_folder = os.path.join(self.input_folder, 'resize')
        output_folder = os.path.join(self.input_folder, 'output')

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        try:
            self.disable_all_except(self.start_button)
            self.worker = WorkerThread(self.process_images, resize_folder, output_folder)
            self.threads.append(self.worker)  # Add to thread list
            self.worker.progress.connect(self.update_arrange_progress)
            self.worker.finished.connect(self.on_arrange_finished)
            self.worker.start()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error occurred while processing images: {str(e)}")
            self.enable_all()

    def process_images(self, resize_folder, output_folder, progress_callback, stop_check):
        try:
            image_sizes = [(f, Image.open(os.path.join(resize_folder, f)).size) 
                           for f in os.listdir(resize_folder) 
                           if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            pages = layout_images(image_sizes)
            total_pages = len(pages)
            
            create_pages(pages, resize_folder, output_folder)
            
            for i in range(total_pages):
                if stop_check():
                    break
                progress_callback(int((i + 1) / total_pages * 100))
            
        except Exception as e:
            print(f"Error occurred while processing images: {str(e)}")
            raise

    def update_arrange_progress(self, value):
        self.arrange_progress.setValue(value)

    def on_arrange_finished(self):
        self.enable_all()
        QMessageBox.information(self, "Completed", "Images arranged and saved in output folder.")

    def closeEvent(self, event):
        # Stop all threads
        for thread in self.threads:
            thread.quit()
            thread.wait()
        super().closeEvent(event)

# 添加一个新的 Worker 类来处理后台任务
class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int, int, int)

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.function(*self.args, **self.kwargs, progress_callback=self.progress.emit)
        self.finished.emit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ReceiptProcessorApp()
    ex.show()
    app.exec_()
    # Ensure all threads have stopped
    for thread in ex.threads:
        thread.quit()
        thread.wait()