# Module: main

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog, QProgressBar, QLabel
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PIL import Image
from pillow_heif import register_heif_opener
import os

# Register HEIC format with Pillow
register_heif_opener()

class ConverterThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(int, str)

    def __init__(self, files, output_dir):
        super().__init__()
        self.files = files
        self.output_dir = output_dir

    def run(self):
        converted_count = 0
        for i, file in enumerate(self.files):
            try:
                img = Image.open(file)
                img = img.convert("RGB")
                output_path = os.path.join(self.output_dir, os.path.splitext(os.path.basename(file))[0] + '.jpg')
                img.save(output_path, "JPEG")
                converted_count += 1
                self.progress.emit(int((i + 1) / len(self.files) * 100))
                print(f"Progress: {int((i + 1) / len(self.files) * 100)}%")
            except Exception as e:
                print(f"Error converting {file}: {e}")
        self.finished.emit(converted_count, self.output_dir)
        print("Conversion finished")

class HEICConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('HEIC Converter')

        layout = QVBoxLayout()

        self.selectButton = QPushButton('Select HEIC Files')
        self.selectButton.clicked.connect(self.selectFiles)
        layout.addWidget(self.selectButton)

        self.convertButton = QPushButton('Convert to JPEG')
        self.convertButton.clicked.connect(self.convertFiles)
        self.convertButton.setEnabled(False)
        layout.addWidget(self.convertButton)

        self.progressBar = QProgressBar()
        layout.addWidget(self.progressBar)

        self.statusLabel = QLabel('')
        layout.addWidget(self.statusLabel)

        self.setLayout(layout)

    def selectFiles(self):
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(self, "Select HEIC Files", "", "HEIC Files (*.heic);;All Files (*)", options=options)
        if files:
            self.files = files
            self.convertButton.setEnabled(True)
            print(f"Selected files: {self.files}")

    def convertFiles(self):
        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if output_dir:
            self.thread = ConverterThread(self.files, output_dir)
            self.thread.progress.connect(self.progressBar.setValue)
            self.thread.finished.connect(self.onConversionFinished)
            self.thread.start()
            print(f"Started conversion thread with output directory: {output_dir}")

    def onConversionFinished(self, converted_count, output_dir):
        self.convertButton.setEnabled(False)
        self.progressBar.setValue(0)
        self.files = []
        self.statusLabel.setText(f"Conversion process finished. {converted_count} files converted to {output_dir}")
        print(f"Conversion process finished. {converted_count} files converted to {output_dir}")

if __name__ == '__main__':
    app = QApplication([])
    window = HEICConverter()
    window.show()
    app.exec_()