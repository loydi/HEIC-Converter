from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from Ui_form import Ui_MainWindow
import os
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QMutex, QWaitCondition
from PIL import Image
from pillow_heif import register_heif_opener
import webbrowser

register_heif_opener()

class ConverterThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)
    ask_overwrite_signal = pyqtSignal(str, str)

    def __init__(self, files, output_dir, image_type):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.image_type = image_type
        self.overwrite_all = False
        self.skip_all = False
        self.result = None
        self.mutex = QMutex()
        self.condition = QWaitCondition()

    def run(self):
        self.convert_count = 0
        for i, file in enumerate(self.files):
            try:
                img = Image.open(file)
                img = img.convert("RGB")
                output_path = os.path.normpath(os.path.join(self.output_dir, os.path.splitext(os.path.basename(file))[0] + f'.{self.image_type}'))

                if os.path.exists(output_path):
                    if self.skip_all:
                        continue
                    if not self.overwrite_all:
                        self.ask_overwrite_signal.emit(file, output_path)
                        self.mutex.lock()
                        self.condition.wait(self.mutex)
                        self.mutex.unlock()
                        result = self.result
                        if result == "skip":
                            continue
                        elif result == "overwrite_all":
                            self.overwrite_all = True
                        elif result == "skip_all":
                            self.skip_all = True
                            continue
                        elif result == "cancel":
                            self.finished.emit(False)
                            return

                img.save(output_path, self.image_type.upper(), quality=95)
                self.convert_count += 1
                self.progress.emit(int((i + 1) / len(self.files) * 100))
            except Exception as e:
                print(f"Error converting {file}: {e}")
        self.finished.emit(self.convert_count > 0)

class FormMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.anaForm = Ui_MainWindow()
        self.anaForm.setupUi(self)

        self.targetFolder = self.anaForm.targetfolder
        self.imagetype = self.anaForm.imagetype
        self.progressBar = self.anaForm.progressBar
        self.tblliste = self.anaForm.listWidget

        self.anaForm.btn_openfolder.clicked.connect(self.openFolder)
        self.anaForm.btn_AddFiles.clicked.connect(self.add_files)
        self.anaForm.btn_StartConversion.clicked.connect(self.start_convert)
        self.anaForm.btn_ClearFiles.clicked.connect(self.clear_files)
        self.anaForm.actionBuy_me_caffee.triggered.connect(self.buy_me_caffee)
        
        self.anaForm.progressBar.setValue(0)
        self.selected_folder = ""

    def openFolder(self):
        print("openFolder")
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", "", options=options)
        if folder:
            self.targetFolder.setText(folder)
            print(f"Selected folder: {folder}")

    def add_files(self):
        options = QFileDialog.Options()
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", "", options=options)
        if folder:
            self.selected_folder = folder
            self.tblliste.clear()
            heic_files = [f for f in os.listdir(folder) if f.lower().endswith('.heic')]
            for file in heic_files:
                self.tblliste.addItem(file)
            print(f"Selected folder: {folder}")
            print(f"HEIC files: {heic_files}")

    def start_convert(self):
        print("start convert")
        target_folder = self.targetFolder.text()
        if not os.path.exists(target_folder):
            QMessageBox.critical(self, "Error", "Target folder does not exist.")
            return

        image_type = self.imagetype.currentText().lower()
        if image_type not in ["jpeg", "png"]:
            QMessageBox.critical(self, "Error", "Unsupported image type selected.")
            return

        files = [os.path.normpath(os.path.join(self.selected_folder, self.tblliste.item(i).text())) for i in range(self.tblliste.count())]
        if not files:
            QMessageBox.critical(self, "Error", "No files selected for conversion.")
            return

        self.thread = ConverterThread(files, target_folder, image_type)
        self.thread.progress.connect(self.progressBar.setValue)
        self.thread.finished.connect(self.on_conversion_finished)
        self.thread.ask_overwrite_signal.connect(self.ask_overwrite)
        self.thread.start()

    @pyqtSlot(str, str)
    def ask_overwrite(self, file, output_path):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle("File Exists")
        msg_box.setText(f"The file {output_path} already exists. What do you want to do?")
        skip_button = msg_box.addButton("Skip", QMessageBox.ActionRole)
        overwrite_button = msg_box.addButton("Overwrite", QMessageBox.ActionRole)
        overwrite_all_button = msg_box.addButton("Overwrite All", QMessageBox.ActionRole)
        skip_all_button = msg_box.addButton("Skip All", QMessageBox.ActionRole)
        cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)
        msg_box.exec_()

        if msg_box.clickedButton() == skip_button:
            self.thread.result = "skip"
        elif msg_box.clickedButton() == overwrite_button:
            self.thread.result = "overwrite"
        elif msg_box.clickedButton() == overwrite_all_button:
            self.thread.result = "overwrite_all"
        elif msg_box.clickedButton() == skip_all_button:
            self.thread.result = "skip_all"
        elif msg_box.clickedButton() == cancel_button:
            self.thread.result = "cancel"
        self.thread.condition.wakeAll()

    def on_conversion_finished(self, success):
        if success:
            QMessageBox.information(self, "Success", "{0} image converted successfully.".format(self.thread.convert_count))
        else:
            QMessageBox.critical(self, "Error", "No images were converted.")
        self.progressBar.setValue(0)

    def clear_files(self):
        print("clear")
        self.progressBar.setValue(0)
        self.tblliste.clear()
        self.imagetype.clear()
        self.targetFolder.clear()

    def buy_me_caffee(self):
        print("buy me cafee")
        webbrowser.open("https://py.pl/1hAGiN")

