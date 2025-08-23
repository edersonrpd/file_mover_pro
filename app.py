import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QFileDialog, QTextEdit, QProgressBar, QMessageBox,
    QGroupBox, QCheckBox, QGridLayout, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import shutil
import json


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

    def __init__(self, source_dir, target_dir, selected_file_types, operation='move', preview_only=False, custom_extensions=None):
        super().__init__()
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.selected_file_types = selected_file_types
        self.operation = operation  # 'move', 'copy', ou 'delete'
        self.preview_only = preview_only
        self.custom_extensions = custom_extensions or set()

        # Construir conjunto de extensões com base nos tipos selecionados
        self.extensions = set()
        for file_type in selected_file_types:
            if file_type in FILE_TYPES:
                self.extensions.update(FILE_TYPES[file_type]['extensions'])

        # Adicionar extensões personalizadas
        self.extensions.update(self.custom_extensions)

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
            moved_files_info = []  # Para rastrear arquivos movidos para desfazer

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
                                    # Armazenar informações para desfazer
                                    moved_files_info.append({
                                        'original_path': str(source_path),
                                        'moved_path': str(target_path)
                                    })
                                    self.progress.emit(f"Movido: {source_path} -> {target_path}")
                                else:  # copy
                                    shutil.copy2(str(source_path), str(target_path))
                                    self.progress.emit(f"Copiado: {source_path} -> {target_path}")
                                processed_files += 1
                            except Exception as e:
                                self.error.emit(f"Erro ao processar {source_path}: {e}")

            # Salvar informações de arquivos movidos para desfazer (apenas para operação de mover)
            if self.operation == 'move' and moved_files_info:
                undo_file = Path(self.target_dir) / "file_mover_undo.json"
                try:
                    with open(undo_file, 'w') as f:
                        json.dump(moved_files_info, f)
                    self.progress.emit(f"Informações para desfazer salvas em: {undo_file}")
                except Exception as e:
                    self.error.emit(f"Erro ao salvar informações para desfazer: {e}")

            self.finished_signal.emit(processed_files)
        except Exception as e:
            self.error.emit(str(e))


class UndoWorker(QThread):
    progress = pyqtSignal(str)
    finished_signal = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, undo_file_path):
        super().__init__()
        self.undo_file_path = undo_file_path

    def run(self):
        try:
            self.execute_undo()
        except Exception as e:
            self.error.emit(str(e))

    def execute_undo(self):
        """Executa o desfazer da operação de mover"""
        try:
            if not os.path.exists(self.undo_file_path):
                self.error.emit("Arquivo de desfazer não encontrado.")
                return

            # Carregar informações dos arquivos movidos
            with open(self.undo_file_path, 'r') as f:
                moved_files_info = json.load(f)

            undone_count = 0

            # Mover os arquivos de volta para suas posições originais
            for file_info in moved_files_info:
                moved_path = Path(file_info['moved_path'])
                original_path = Path(file_info['original_path'])
                
                # Criar diretório original se não existir
                original_path.parent.mkdir(parents=True, exist_ok=True)
                
                if moved_path.exists():
                    try:
                        shutil.move(str(moved_path), str(original_path))
                        self.progress.emit(f"Desfeito: {moved_path} -> {original_path}")
                        undone_count += 1
                    except Exception as e:
                        self.error.emit(f"Erro ao desfazer movimento de {moved_path}: {e}")
                else:
                    self.error.emit(f"Arquivo não encontrado para desfazer: {moved_path}")

            # Remover o arquivo de desfazer após a operação
            try:
                os.remove(self.undo_file_path)
                self.progress.emit("Arquivo de desfazer removido.")
            except Exception as e:
                self.error.emit(f"Erro ao remover arquivo de desfazer: {e}")

            self.finished_signal.emit(undone_count)
        except Exception as e:
            self.error.emit(f"Erro ao executar desfazer: {str(e)}")


class SpreadsheetMoverApp(QWidget):
    def __init__(self):
        super().__init__()
        self.is_dark_theme = True
        self.worker = None
        self.undo_worker = None
        self.preview_items = None
        self.last_operation_dir = None
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
            QPushButton#undo_btn {
                background-color: #d9534f; color: white;
            }
            QPushButton#undo_btn:hover {
                background-color: #c9302c;
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
            QPushButton#undo_btn {
                background-color: #d9534f; color: white;
            }
            QPushButton#undo_btn:hover {
                background-color: #c9302c;
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
        
        self.undo_btn = QPushButton('↩️ Desfazer')
        self.undo_btn.setObjectName('undo_btn')
        self.undo_btn.clicked.connect(self.undo_operation)
        self.undo_btn.setEnabled(False)
        button_layout.addWidget(self.undo_btn)
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
        file_type_layout = QVBoxLayout()  # Mudando para QVBoxLayout para melhor organização

        # Layout para os checkboxes dos tipos de arquivos predefinidos
        grid_layout = QGridLayout()
        self.file_type_checks = {}
        row, col = 0, 0
        for file_type, info in FILE_TYPES.items():
            checkbox = QCheckBox(info['description'])
            if file_type == 'Spreadsheets':
                checkbox.setChecked(True)
            self.file_type_checks[file_type] = checkbox
            grid_layout.addWidget(checkbox, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        file_type_layout.addLayout(grid_layout)

        # Adicionando campo para extensões personalizadas
        custom_extensions_layout = QHBoxLayout()
        custom_extensions_layout.addWidget(QLabel('Extensões Personalizadas:'))
        self.custom_extensions_edit = QLineEdit()
        self.custom_extensions_edit.setPlaceholderText("Ex: .txt, .log, .dat (separados por vírgula)")
        custom_extensions_layout.addWidget(self.custom_extensions_edit)
        file_type_layout.addLayout(custom_extensions_layout)

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

    def get_custom_extensions(self):
        """Obtém as extensões personalizadas do campo de texto"""
        custom_text = self.custom_extensions_edit.text().strip()
        if not custom_text:
            return set()

        # Dividir por vírgula e limpar espaços
        extensions = set()
        for ext in custom_text.split(','):
            ext = ext.strip().lower()
            if ext:
                # Garantir que a extensão comece com ponto
                if not ext.startswith('.'):
                    ext = '.' + ext
                extensions.add(ext)

        return extensions

    def preview_files(self):
        """Gera e mostra a pré-visualização dos arquivos"""
        source_dir = self.source_edit.text()
        target_dir = self.target_edit.text()
        selected_file_types = self.get_selected_file_types()
        custom_extensions = self.get_custom_extensions()
        operation = self.operation_combo.currentText().lower()

        if not source_dir:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione o diretório de origem.')
            return

        if not os.path.exists(source_dir):
            QMessageBox.warning(self, 'Aviso', 'O diretório de origem não existe.')
            return

        if operation in ['mover', 'copiar'] and not target_dir:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione o diretório de destino.')
            return

        if not selected_file_types and not custom_extensions:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione pelo menos um tipo de arquivo ou insira extensões personalizadas.')
            return

        if operation == 'mover':
            operation_code = 'move'
        elif operation == 'copiar':
            operation_code = 'copy'
        else:  # excluir
            operation_code = 'delete'

        self.preview_btn.setEnabled(False)
        self.move_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.log_output.clear()

        self.worker = MoveWorker(source_dir, target_dir, selected_file_types, operation_code, preview_only=True, custom_extensions=custom_extensions)
        self.worker.progress.connect(self.update_log)
        self.worker.finished_signal.connect(self.preview_finished)
        self.worker.error.connect(self.move_error)
        self.worker.preview_data.connect(self.show_preview_dialog)
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
        custom_extensions = self.get_custom_extensions()
        operation = self.operation_combo.currentText().lower()

        # Mapear texto da operação para código
        operation_map = {'mover': 'move', 'copiar': 'copy', 'excluir': 'delete'}
        operation_code = operation_map.get(operation, 'move')

        if not source_dir:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione o diretório de origem.')
            return

        if not os.path.exists(source_dir):
            QMessageBox.warning(self, 'Aviso', 'O diretório de origem não existe.')
            return

        if operation in ['mover', 'copiar'] and not target_dir:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione o diretório de destino.')
            return

        if not selected_file_types and not custom_extensions:
            QMessageBox.warning(self, 'Aviso', 'Por favor, selecione pelo menos um tipo de arquivo ou insira extensões personalizadas.')
            return

        # Confirmar com o usuário antes de executar
        file_count_msg = ""
        if self.preview_items is not None:
            file_count_msg = f"\n\nSerão afetados {len(self.preview_items)} arquivos."
        elif hasattr(self, '_last_preview_count'):
            file_count_msg = f"\n\nSerão afetados aproximadamente {self._last_preview_count} arquivos."

        reply = QMessageBox.question(
            self,
            'Confirmar Operação',
            f'Tem certeza que deseja {operation} os arquivos selecionados?{file_count_msg}',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        self.move_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        self.undo_btn.setEnabled(False)
        self.move_btn.setText(f"{operation.capitalize()}...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.log_output.clear()

        self.worker = MoveWorker(source_dir, target_dir, selected_file_types, operation_code, custom_extensions=custom_extensions)
        self.worker.progress.connect(self.update_log)
        self.worker.finished_signal.connect(self.operation_finished)
        self.worker.error.connect(self.move_error)
        self.worker.start()

        # Armazenar o diretório da última operação para usar no desfazer
        if operation_code == 'move':
            self.last_operation_dir = target_dir

    def undo_operation(self):
        """Executa a operação de desfazer"""
        if not self.last_operation_dir:
            QMessageBox.warning(self, 'Aviso', 'Não há operação para desfazer.')
            return
            
        undo_file_path = Path(self.last_operation_dir) / "file_mover_undo.json"
        if not undo_file_path.exists():
            QMessageBox.warning(self, 'Aviso', 'Não foi encontrado arquivo de informações para desfazer a operação.')
            return
            
        reply = QMessageBox.question(
            self,
            'Confirmar Desfazer',
            'Tem certeza que deseja desfazer a última operação de mover?\nOs arquivos serão movidos de volta para seus locais originais.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
            
        self.undo_btn.setEnabled(False)
        self.move_btn.setEnabled(False)
        self.preview_btn.setEnabled(False)
        self.undo_btn.setText("Desfazendo...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.log_output.clear()
        
        self.undo_worker = UndoWorker(str(undo_file_path))
        self.undo_worker.progress.connect(self.update_log)
        self.undo_worker.finished_signal.connect(self.undo_finished)
        self.undo_worker.error.connect(self.move_error)
        self.undo_worker.start()

    def undo_finished(self, count):
        """Chamado quando a operação de desfazer é concluída"""
        self.undo_btn.setEnabled(True)
        self.move_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.undo_btn.setText('↩️ Desfazer')
        self.progress_bar.setVisible(False)
        self.log_output.append(f"\n↩️ Total de arquivos desfeitos: {count}")
        QMessageBox.information(self, 'Sucesso', f'Desfeita a operação de mover para {count} arquivos!')
        
        # Limpar dados de pré-visualização e diretório da última operação
        self.preview_items = None
        self.last_operation_dir = None

    def update_log(self, message):
        self.log_output.append(message)

    def operation_finished(self, count):
        operation = self.operation_combo.currentText().lower()
        self.move_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.move_btn.setText('🚀 Executar Operação')
        self.progress_bar.setVisible(False)
        self.log_output.append(f"\n🎉 Total de arquivos {operation}dos: {count}")
        
        # Habilitar botão de desfazer apenas para operações de mover
        if self.operation_combo.currentText().lower() == 'mover' and count > 0:
            self.undo_btn.setEnabled(True)
            QMessageBox.information(self, 'Sucesso', f'{operation.capitalize()} {count} arquivos com sucesso!\nVocê pode usar o botão "Desfazer" para reverter esta operação.')
        else:
            self.undo_btn.setEnabled(False)
            QMessageBox.information(self, 'Sucesso', f'{operation.capitalize()} {count} arquivos com sucesso!')
        
        # Limpar dados de pré-visualização
        self.preview_items = None

    def move_error(self, error_message):
        self.move_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.undo_btn.setEnabled(True)
        self.move_btn.setText('🚀 Executar Operação')
        self.undo_btn.setText('↩️ Desfazer')
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