import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QFileDialog, QTextEdit, QProgressBar, QMessageBox,
    QGroupBox, QCheckBox, QScrollArea, QGridLayout, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QDialog
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
    preview_data = pyqtSignal(list)  # Sinal para enviar dados de pré-visualização

    def __init__(self, source_dir, target_dir, selected_file_types, operation='move', preview_only=False):
        super().__init__()
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.selected_file_types = selected_file_types
        self.operation = operation  # 'move', 'copy', ou 'delete'
        self.preview_only = preview_only
        
        # Construir conjunto de extensões com base nos tipos selecionados
        self.extensions = set()
        for file_type in selected_file_types:
            if file_type in FILE_TYPES:
                self.extensions.update(FILE_TYPES[file_type]['extensions'])

    def is_selected_file(self, filename):
        return Path(filename).suffix.lower() in self.extensions

    def get_file_size_formatted(self, filepath):
        """Retorna o tamanho do arquivo formatado"""
        try:
            size = os.path.getsize(filepath)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "Desconhecido"

    def run(self):
        try:
            if self.preview_only:
                self.generate_preview()
            else:
                self.execute_operation()
        except Exception as e:
            self.error.emit(str(e))

    def generate_preview(self):
        """Gera dados de pré-visualização dos arquivos que serão afetados"""
        try:
            preview_items = []
            
            # Walk through all directories and subdirectories
            for root, _, files in os.walk(self.source_dir):
                for file in files:
                    if self.is_selected_file(file):
                        source_path = Path(root) / file
                        file_size = self.get_file_size_formatted(str(source_path))
                        
                        item = {
                            'filename': file,
                            'source_path': str(source_path),
                            'size': file_size,
                            'operation': self.operation
                        }
                        
                        if self.operation in ['move', 'copy']:
                            # Calcular caminho de destino
                            target_path = Path(self.target_dir) / file
                            counter = 1
                            original_target_path = target_path
                            while target_path.exists():
                                stem = original_target_path.stem
                                suffix = original_target_path.suffix
                                target_path = Path(self.target_dir) / f"{stem}_{counter}{suffix}"
                                counter += 1
                            item['target_path'] = str(target_path)
                        else:  # delete
                            item['target_path'] = 'Será excluído'
                            
                        preview_items.append(item)
            
            self.preview_data.emit(preview_items)
            self.finished_signal.emit(len(preview_items))
        except Exception as e:
            self.error.emit(str(e))

    def execute_operation(self):
        """Executa a operação selecionada (mover, copiar ou deletar)"""
        try:
            if self.operation in ['move', 'copy']:
                # Create target directory if it doesn't exist
                Path(self.target_dir).mkdir(parents=True, exist_ok=True)

            processed_files = 0

            # Walk through all directories and subdirectories
            for root, _, files in os.walk(self.source_dir):
                for file in files:
                    if self.is_selected_file(file):
                        source_path = Path(root) / file
                        
                        if self.operation == 'delete':
                            try:
                                os.remove(str(source_path))
                                self.progress.emit(f"Excluído: {source_path}")
                                processed_files += 1
                            except Exception as e:
                                self.error.emit(f"Erro ao excluir {source_path}: {e}")
                        else:  # move or copy
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
                                if self.operation == 'move':
                                    shutil.move(str(source_path), str(target_path))
                                    self.progress.emit(f"Movido: {source_path} -> {target_path}")
                                else:  # copy
                                    shutil.copy2(str(source_path), str(target_path))
                                    self.progress.emit(f"Copiado: {source_path} -> {target_path}")
                                processed_files += 1
                            except Exception as e:
                                self.error.emit(f"Erro ao processar {source_path}: {e}")

            self.finished_signal.emit(processed_files)
        except Exception as e:
            self.error.emit(str(e))


class SpreadsheetMoverApp(QWidget):
    def __init__(self):
        super().__init__()
        self.is_dark_theme = True
        self.worker = None
        self.preview_items = None
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
        self.setWindowTitle('File Mover Pro v2')
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
        
        # Para operação de exclusão, o diretório de destino não é necessário
        dir_layout.addWidget(QLabel('Diretório de Destino:'), 1, 0)
        self.target_edit = QLineEdit()
        self.target_edit.setPlaceholderText("Selecione a pasta para mover arquivos para...")
        dir_layout.addWidget(self.target_edit, 1, 1)
        target_btn = QPushButton('📂 Procurar')
        target_btn.clicked.connect(self.browse_target)
        dir_layout.addWidget(target_btn, 1, 2)
        main_layout.addLayout(dir_layout)

        # Seleção de operação
        operation_layout = QHBoxLayout()
        operation_layout.addWidget(QLabel('Operação:'))
        self.operation_combo = QComboBox()
        self.operation_combo.addItems(['Mover', 'Copiar', 'Excluir'])
        self.operation_combo.currentTextChanged.connect(self.on_operation_changed)
        operation_layout.addWidget(self.operation_combo)
        operation_layout.addStretch()
        main_layout.addLayout(operation_layout)

        self.create_file_type_selection(main_layout)

        # Botões
        button_layout = QHBoxLayout()
        self.preview_btn = QPushButton('👁️ Pré-visualizar')
        self.preview_btn.clicked.connect(self.preview_files)
        button_layout.addWidget(self.preview_btn)
        
        self.move_btn = QPushButton('🚀 Executar Operação')
        self.move_btn.clicked.connect(self.execute_operation)
        button_layout.addWidget(self.move_btn)
        main_layout.addLayout(button_layout)

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

    def on_operation_changed(self, text):
        """Habilita/desabilita o campo de diretório de destino conforme a operação"""
        if text == 'Excluir':
            self.target_edit.setEnabled(False)
            self.target_edit.setPlaceholderText("Não necessário para exclusão")
        else:
            self.target_edit.setEnabled(True)
            self.target_edit.setPlaceholderText("Selecione a pasta para mover arquivos para...")

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

    def preview_files(self):
        """Gera e mostra a pré-visualização dos arquivos"""
        source_dir = self.source_edit.text()
        target_dir = self.target_edit.text()
        selected_file_types = self.get_selected_file_types()
        operation = self.operation_combo.currentText().lower()
        
        if operation == 'mover':
            operation_code = 'move'
        elif operation == 'copiar':
            operation_code = 'copy'
        else:  # excluir
            operation_code = 'delete'
        
        if not source_dir:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione o diretório de origem.')
            return
            
        if not selected_file_types:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione pelo menos um tipo de arquivo.')
            return
            
        if not os.path.exists(source_dir):
            QMessageBox.critical(self, 'Erro', 'O diretório de origem não existe.')
            return
            
        if operation_code in ['move', 'copy'] and not target_dir:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione o diretório de destino.')
            return

        self.preview_btn.setEnabled(False)
        self.preview_btn.setText("Gerando pré-visualização...")
        self.log_output.clear()
        
        # Criar worker para pré-visualização
        self.worker = MoveWorker(source_dir, target_dir, selected_file_types, operation_code, preview_only=True)
        self.worker.preview_data.connect(self.show_preview_dialog)
        self.worker.finished_signal.connect(self.preview_finished)
        self.worker.error.connect(self.move_error)
        self.worker.start()

    def show_preview_dialog(self, preview_items):
        """Mostra o diálogo de pré-visualização"""
        if not preview_items:
            QMessageBox.information(self, 'Pré-visualização', 'Nenhum arquivo encontrado para a operação selecionada.')
            return
            
        # Criar diálogo de pré-visualização
        dialog = QDialog(self)
        dialog.setWindowTitle('Pré-visualização de Arquivos')
        dialog.setGeometry(100, 100, 800, 500)
        
        layout = QVBoxLayout()
        
        # Tabela de pré-visualização
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(['Arquivo', 'Tamanho', 'Origem', 'Destino/Operação'])
        table.setRowCount(len(preview_items))
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        
        for row, item in enumerate(preview_items):
            table.setItem(row, 0, QTableWidgetItem(item['filename']))
            table.setItem(row, 1, QTableWidgetItem(item['size']))
            table.setItem(row, 2, QTableWidgetItem(item['source_path']))
            table.setItem(row, 3, QTableWidgetItem(item['target_path']))
            
            # Centralizar o tamanho
            table.item(row, 1).setTextAlignment(Qt.AlignCenter)
        
        layout.addWidget(table)
        
        # Informações adicionais
        operation = self.operation_combo.currentText()
        info_label = QLabel(f"Total de arquivos a serem {operation.lower()}s: {len(preview_items)}")
        layout.addWidget(info_label)
        
        # Botões
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton('Cancelar')
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton(f'Confirmar {operation}')
        confirm_btn.clicked.connect(dialog.accept)
        confirm_btn.setDefault(True)
        button_layout.addWidget(confirm_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        # Armazenar o resultado da pré-visualização
        self.preview_items = preview_items
        
        # Executar diálogo
        if dialog.exec_() == QDialog.Accepted:
            # Se confirmado, executar a operação
            self.execute_operation()
        else:
            self.preview_btn.setEnabled(True)
            self.preview_btn.setText('👁️ Pré-visualizar')

    def preview_finished(self, count):
        """Chamado quando a pré-visualização é concluída"""
        if count == 0:
            self.preview_btn.setEnabled(True)
            self.preview_btn.setText('👁️ Pré-visualizar')
            QMessageBox.information(self, 'Pré-visualização', 'Nenhum arquivo encontrado para a operação selecionada.')

    def execute_operation(self):
        """Executa a operação selecionada"""
        source_dir = self.source_edit.text()
        target_dir = self.target_edit.text()
        selected_file_types = self.get_selected_file_types()
        operation = self.operation_combo.currentText().lower()
        
        if operation == 'mover':
            operation_code = 'move'
        elif operation == 'copiar':
            operation_code = 'copy'
        else:  # excluir
            operation_code = 'delete'
        
        if not source_dir:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione o diretório de origem.')
            return
            
        if not selected_file_types:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione pelo menos um tipo de arquivo.')
            return
            
        if not os.path.exists(source_dir):
            QMessageBox.critical(self, 'Erro', 'O diretório de origem não existe.')
            return
            
        if operation_code in ['move', 'copy'] and not target_dir:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione o diretório de destino.')
            return

        # Confirmar operação de exclusão
        if operation_code == 'delete':
            reply = QMessageBox.question(
                self, 
                'Confirmar Exclusão', 
                f'Tem certeza que deseja excluir {len(self.preview_items) if self.preview_items else "os arquivos"}?\nEsta ação não pode ser desfeita.',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        self.move_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        self.move_btn.setText(f"{operation.capitalize()}...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.log_output.clear()
        
        self.worker = MoveWorker(source_dir, target_dir, selected_file_types, operation_code)
        self.worker.progress.connect(self.update_log)
        self.worker.finished_signal.connect(self.operation_finished)
        self.worker.error.connect(self.move_error)
        self.worker.start()

    def update_log(self, message):
        self.log_output.append(message)

    def operation_finished(self, count):
        operation = self.operation_combo.currentText().lower()
        self.move_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.move_btn.setText('🚀 Executar Operação')
        self.progress_bar.setVisible(False)
        self.log_output.append(f"\n🎉 Total de arquivos {operation}dos: {count}")
        QMessageBox.information(self, 'Sucesso', f'{operation.capitalize()} {count} arquivos com sucesso!')
        
        # Limpar dados de pré-visualização
        self.preview_items = None

    def move_error(self, error_message):
        self.move_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.move_btn.setText('🚀 Executar Operação')
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