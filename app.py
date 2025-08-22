import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QFileDialog, QTextEdit, QProgressBar, QMessageBox,
    QGroupBox, QCheckBox, QScrollArea, QGridLayout,
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import shutil


# Definições de tipos de arquivos
FILE_TYPES = {
    'Spreadsheets': {
        'extensions': {'.xlsx', '.xls', '.csv', '.ods', '.tsv', '.xlsm', '.xlsb',
                      '.xltx', '.xltm', '.xlt', '.xlam', '.xla'},
        'description': 'Planilhas (Excel, CSV, ODS, etc.)'
    },

    'PDF': {
        'extensions': {'.pdf'},
        'description': 'Documentos (PDF)'
    },
    'Documents': {
        'extensions': {'.doc', '.docx', '.txt', '.rtf', '.odt', '.md'},
        'description': 'Documentos (Word, Texto, etc.)'
    },
    'Images': {
        'extensions': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp'},
        'description': 'Imagens (JPG, PNG, GIF, etc.)'
    },
    'Videos': {
        'extensions': {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'},
        'description': 'Vídeos (MP4, AVI, MKV, etc.)'
    },
    'Audio': {
        'extensions': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'},
        'description': 'Áudios (MP3, WAV, FLAC, etc.)'
    },
    'Archives': {
        'extensions': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'},
        'description': 'Arquivos compactados (ZIP, RAR, 7Z, etc.)'
    },
    'Scripts': {
        'extensions': {'.py', '.js', '.sh', '.bat', '.pl', '.rb'},
        'description': 'Scripts (Python, JavaScript, Shell, etc.)'
    },
    'SQL': {
        'extensions': {'.sql'},
        'description': 'Scripts SQL'
    },
    'Executaveis': {
        'extensions': {'.exe', '.msi', '.app', '.bat'},
        'description': 'Executáveis (EXE, MSI, APP, etc.)'
    }
}


class MoveWorker(QThread):
    progress = pyqtSignal(str)
    finished_signal = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, source_dir, target_dir, selected_file_types):
        super().__init__()
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.selected_file_types = selected_file_types

        # Construir conjunto de extensões com base nos tipos selecionados
        self.extensions = set()
        for file_type in selected_file_types:
            if file_type in FILE_TYPES:
                self.extensions.update(FILE_TYPES[file_type]['extensions'])

    def is_selected_file(self, filename):
        return Path(filename).suffix.lower() in self.extensions

    def run(self):
        try:
            # Create target directory if it doesn't exist
            Path(self.target_dir).mkdir(parents=True, exist_ok=True)

            moved_files = 0

            # Walk through all directories and subdirectories
            for root, _, files in os.walk(self.source_dir):
                for file in files:
                    if self.is_selected_file(file):
                        source_path = Path(root) / file
                        target_path = Path(self.target_dir) / file

                        # Handle filename conflicts by adding a counter
                        counter = 1
                        original_target_path = target_path
                        while target_path.exists():
                            stem = original_target_path.stem
                            suffix = original_target_path.suffix
                            target_path = Path(self.target_dir) / f"{stem}_{counter}{suffix}"
                            counter += 1

                        try:
                            shutil.move(str(source_path), str(target_path))
                            self.progress.emit(f"Movido: {source_path} -> {target_path}")
                            moved_files += 1
                        except Exception as e:
                            self.error.emit(f"Erro ao mover {source_path}: {e}")

            self.finished_signal.emit(moved_files)
        except Exception as e:
            self.error.emit(str(e))


class SpreadsheetMoverApp(QWidget):
    def __init__(self):
        super().__init__()
        self.is_dark_theme = True
        self.worker = None
        self.init_styles()
        self.initUI()
        self.apply_theme()

    def init_styles(self):
        self.dark_theme_qss = '''
            QWidget {
                background-color: #2b2b2b; color: #f0f0f0;
                font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif; font-size: 10pt;
            }
            QGroupBox {
                border: 1px solid #444; border-radius: 6px; margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; subcontrol-position: top center;
                padding: 0 5px;
            }
            QLineEdit, QTextEdit {
                background-color: #3c3c3c; border: 1px solid #555;
                padding: 6px; border-radius: 4px;
            }
            QPushButton {
                background-color: #0078d7; color: white;
                border: none; padding: 8px 12px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #005a9e; }
            QPushButton:pressed { background-color: #004c87; }
            QPushButton#theme_btn {
                background-color: #444;
            }
            QPushButton#theme_btn:hover {
                background-color: #555;
            }
            QProgressBar {
                border: 1px solid #555; border-radius: 4px; text-align: center;
                background-color: #3c3c3c;
            }
            QProgressBar::chunk {
                background-color: #0078d7; border-radius: 3px;
            }
            QScrollArea { border: none; }
            QCheckBox { spacing: 5px; }
            QCheckBox::indicator { width: 16px; height: 16px; }
        '''
        self.light_theme_qss = '''
            QWidget {
                background-color: #f0f0f0; color: #2b2b2b;
                font-family: "Segoe UI", "Helvetica Neue", "Arial", sans-serif; font-size: 10pt;
            }
            QGroupBox {
                border: 1px solid #ccc; border-radius: 6px; margin-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; subcontrol-position: top center;
                padding: 0 5px;
            }
            QLineEdit, QTextEdit {
                background-color: #fff; border: 1px solid #ccc;
                padding: 6px; border-radius: 4px;
            }
            QPushButton {
                background-color: #0078d7; color: white;
                border: none; padding: 8px 12px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #005a9e; }
            QPushButton:pressed { background-color: #004c87; }
            QPushButton#theme_btn {
                background-color: #e0e0e0; color: #2b2b2b;
            }
            QPushButton#theme_btn:hover {
                background-color: #d0d0d0;
            }
            QProgressBar {
                border: 1px solid #ccc; border-radius: 4px; text-align: center;
                background-color: #e8e8e8; color: #2b2b2b;
            }
            QProgressBar::chunk {
                background-color: #0078d7; border-radius: 3px;
            }
            QScrollArea { border: none; }
            QCheckBox { spacing: 5px; }
            QCheckBox::indicator { width: 16px; height: 16px; }
        '''

    def initUI(self):
        self.setWindowTitle('File Mover Pro v1')
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        top_layout = QHBoxLayout()
        self.theme_btn = QPushButton('☀️')
        self.theme_btn.setObjectName('theme_btn')
        self.theme_btn.setFixedWidth(40)
        self.theme_btn.setToolTip("Toggle Light/Dark Theme")
        self.theme_btn.clicked.connect(self.toggle_theme)
        top_layout.addStretch()
        top_layout.addWidget(self.theme_btn)
        main_layout.addLayout(top_layout)

        dir_layout = QGridLayout()
        dir_layout.setSpacing(10)
        dir_layout.addWidget(QLabel('Diretório de Origem:'), 0, 0)
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Selecione a pasta para mover arquivos de...")
        dir_layout.addWidget(self.source_edit, 0, 1)
        source_btn = QPushButton('📂 Procurar')
        source_btn.clicked.connect(self.browse_source)
        dir_layout.addWidget(source_btn, 0, 2)
        dir_layout.addWidget(QLabel('Diretório de Destino:'), 1, 0)
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("Selecione a pasta para mover arquivos para...")
        dir_layout.addWidget(self.target_edit, 1, 1)
        target_btn = QPushButton('📂 Procurar')
        target_btn.clicked.connect(self.browse_target)
        dir_layout.addWidget(target_btn, 1, 2)
        main_layout.addLayout(dir_layout)

        self.create_file_type_selection(main_layout)

        self.move_btn = QPushButton('🚀 Mover Arquivos Selecionados')
        self.move_btn.clicked.connect(self.move_files)
        main_layout.addWidget(self.move_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)

        self.setLayout(main_layout)

    def create_file_type_selection(self, layout):
        file_type_group = QGroupBox("Selecionar Tipos de Arquivos para Mover")
        file_type_layout = QGridLayout()
        file_type_layout.setSpacing(10)
        self.file_type_checks = {}
        row, col = 0, 0
        for file_type, info in FILE_TYPES.items():
            checkbox = QCheckBox(info['description'])
            if file_type == 'Spreadsheets':
                checkbox.setChecked(True)
            self.file_type_checks[file_type] = checkbox
            file_type_layout.addWidget(checkbox, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
        file_type_group.setLayout(file_type_layout)
        layout.addWidget(file_type_group)

    def browse_source(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecione Diretório Origem")
        if directory:
            self.source_edit.setText(directory)

    def browse_target(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecione Diretório Destino")
        if directory:
            self.target_edit.setText(directory)

    def get_selected_file_types(self):
        selected = []
        for file_type, checkbox in self.file_type_checks.items():
            if checkbox.isChecked():
                selected.append(file_type)
        return selected

    def move_files(self):
        source_dir = self.source_edit.text()
        target_dir = self.target_edit.text()
        selected_file_types = self.get_selected_file_types()
        if not source_dir or not target_dir:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione os diretórios de origem e destino.')
            return
        if not selected_file_types:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione pelo menos um tipo de arquivo para mover.')
            return
        if not os.path.exists(source_dir):
            QMessageBox.critical(self, 'Erro', 'O diretório de origem não existe.')
            return
        self.move_btn.setEnabled(False)
        self.move_btn.setText("Movendo...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.log_output.clear()
        self.worker = MoveWorker(source_dir, target_dir, selected_file_types)
        self.worker.progress.connect(self.update_log)
        self.worker.finished_signal.connect(self.move_finished)
        self.worker.error.connect(self.move_error)
        self.worker.start()

    def update_log(self, message):
        self.log_output.append(message)

    def move_finished(self, count):
        self.move_btn.setEnabled(True)
        self.move_btn.setText('🚀 Mover Arquivos Selecionados')
        self.progress_bar.setVisible(False)
        self.log_output.append(f"\n🎉 Total de arquivos movidos: {count}")
        QMessageBox.information(self, 'Sucesso', f'Movido {count} arquivos com sucesso!')

    def move_error(self, error_message):
        self.move_btn.setEnabled(True)
        self.move_btn.setText('🚀 Mover Arquivos Selecionados')
        self.progress_bar.setVisible(False)
        self.log_output.append(f"\n❌ Erro: {error_message}")
        QMessageBox.critical(self, 'Erro', f'Ocorreu um erro: {error_message}')

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()

    def apply_theme(self):
        if self.is_dark_theme:
            self.setStyleSheet(self.dark_theme_qss)
            self.theme_btn.setText('☀️')
            self.theme_btn.setToolTip("Alternar para o Tema Claro")
        else:
            self.setStyleSheet(self.light_theme_qss)
            self.theme_btn.setText('🌙')
            self.theme_btn.setToolTip("Alternar para o Tema Escuro")

def main():
    app = QApplication(sys.argv)
    window = SpreadsheetMoverApp()
    icon = QIcon("imagem.ico")
    app.setWindowIcon(icon)
    window.setWindowIcon(icon)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
