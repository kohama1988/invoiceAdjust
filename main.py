import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, 
                             QLabel, QLineEdit, QMessageBox, QProgressBar, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap
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

    def run(self):
        self.function(*self.args, **self.kwargs, progress_callback=self.progress.emit)
        self.finished.emit()

class ReceiptProcessorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.input_folder = ''
        self.progress_label = QLabel('', self)  # 在这里初始化 progress_label
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Receipt Processor')
        self.setGeometry(100, 100, 500, 300)

        main_layout = QVBoxLayout()

        # 添加图片按钮和图片数量显示
        folder_layout = QHBoxLayout()
        self.add_button = QPushButton('选择图片文件夹', self)
        self.add_button.clicked.connect(self.add_images)
        folder_layout.addWidget(self.add_button)
        self.image_count_label = QLabel('', self)
        folder_layout.addWidget(self.image_count_label)
        main_layout.addLayout(folder_layout)

        # 显示选择的文件夹路径
        self.folder_label = QLabel('未选择文件夹', self)
        main_layout.addWidget(self.folder_label)

        # 提取发票按钮和进度条
        extract_layout = QHBoxLayout()
        self.extract_button = QPushButton('提取发票', self)
        self.extract_button.clicked.connect(self.extract_receipts)
        self.extract_button.setFixedWidth(100)
        extract_layout.addWidget(self.extract_button)
        self.extract_progress = QProgressBar(self)
        extract_layout.addWidget(self.extract_progress)
        extract_layout.addWidget(self.progress_label)
        main_layout.addLayout(extract_layout)

        # 缩小倍数输入框和resize按钮
        resize_layout = QHBoxLayout()
        resize_layout.addWidget(QLabel('缩小倍数 (0-1):'))
        self.resize_input = QLineEdit('0.3', self)
        resize_layout.addWidget(self.resize_input)
        self.resize_button = QPushButton('Resize', self)
        self.resize_button.clicked.connect(self.resize_images)
        resize_layout.addWidget(self.resize_button)
        main_layout.addLayout(resize_layout)

        # 开始排列按钮和进度条
        arrange_layout = QHBoxLayout()
        self.start_button = QPushButton('开始排列', self)
        self.start_button.clicked.connect(self.start_processing)
        self.start_button.setFixedWidth(100)
        arrange_layout.addWidget(self.start_button)
        self.arrange_progress = QProgressBar(self)
        arrange_layout.addWidget(self.arrange_progress)
        main_layout.addLayout(arrange_layout)

        # 添加伸缩空间
        main_layout.addStretch(1)

        # 添加logo、开发者信息和版本号
        bottom_layout = QHBoxLayout()

        logo_dev_layout = QVBoxLayout()
        logo_label = QLabel(self)
        pixmap = QPixmap('logo.jpg')
        scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        logo_dev_layout.addWidget(logo_label)

        bottom_layout.addLayout(logo_dev_layout)
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

    def add_images(self):
        self.input_folder = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if self.input_folder:
            self.folder_label.setText(f'已选择文件夹: {self.input_folder}')
            image_count = len([f for f in os.listdir(self.input_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
            self.image_count_label.setText(f'有{image_count}张图片需要整理')

    def extract_receipts(self):
        if not self.input_folder:
            QMessageBox.warning(self, "警告", "请先选择图片文件夹！")
            return

        receipts_folder = os.path.join(self.input_folder, 'receipts')
        if not os.path.exists(receipts_folder):
            os.makedirs(receipts_folder)

        try:
            self.extract_button.setEnabled(False)
            self.extract_progress.setValue(0)

            # 创建一个 QThread 对象
            self.thread = QThread()
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
                lambda: self.extract_button.setEnabled(True)
            )
            self.thread.finished.connect(
                lambda: QMessageBox.information(self, "完成", "发票提取完成！结果保存在 receipts 文件夹中。")
            )

        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理图片时发生错误：{str(e)}")
            self.extract_button.setEnabled(True)

    def update_extract_progress(self, value, current, total):
        self.extract_progress.setValue(value)
        self.progress_label.setText(f'({current}/{total})')

    def resize_images(self):
        if not self.input_folder:
            QMessageBox.warning(self, "警告", "请先选择图片文件夹！")
            return
        try:
            scale_factor = float(self.resize_input.text())
            if not 0 < scale_factor <= 1:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "警告", "请输入有效的缩小倍数（0-1之间的小数）！")
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

        QMessageBox.information(self, "完成", "图片缩放完成！结果保存在 resize 文件夹中。")

    def start_processing(self):
        if not self.input_folder:
            QMessageBox.warning(self, "警告", "请先选择图片文件夹！")
            return

        resize_folder = os.path.join(self.input_folder, 'resize')
        output_folder = os.path.join(self.input_folder, 'output')

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        try:
            self.worker = WorkerThread(self.process_images, resize_folder, output_folder)
            self.worker.progress.connect(self.update_arrange_progress)
            self.worker.finished.connect(self.on_arrange_finished)
            self.worker.start()
            self.start_button.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理图片时发生错误：{str(e)}")
            self.start_button.setEnabled(True)

    def process_images(self, resize_folder, output_folder, progress_callback):
        try:
            image_sizes = [(f, Image.open(os.path.join(resize_folder, f)).size) 
                           for f in os.listdir(resize_folder) 
                           if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            pages = layout_images(image_sizes)
            total_pages = len(pages)
            
            create_pages(pages, resize_folder, output_folder)
            
            for i in range(total_pages):
                progress_callback(int((i + 1) / total_pages * 100))
            
        except Exception as e:
            print(f"处理图片时发生错误��{str(e)}")
            raise

    def update_arrange_progress(self, value):
        self.arrange_progress.setValue(value)

    def on_arrange_finished(self):
        self.start_button.setEnabled(True)
        QMessageBox.information(self, "完成", "图片排列完成！输出已保存到 output 文件夹。")

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
    sys.exit(app.exec_())