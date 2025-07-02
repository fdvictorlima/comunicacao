import sys
import json
import os
import base64
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QComboBox, QTextEdit, QPushButton, QTabWidget, QMessageBox,
    QListWidget, QDateEdit, QHBoxLayout, QSplitter, QShortcut,
    QScrollArea, QFrame, QSizePolicy, QToolButton
)
from PyQt5.QtCore import QDate, Qt, QBuffer, QIODevice
from PyQt5.QtGui import QFont, QKeySequence, QTextCursor, QTextListFormat, QTextCharFormat, QPixmap

JSON_FILE = "dados.json"
ARIAL_FONT = QFont("Arial", 10)


class RegistroTab(QWidget):
    def __init__(self):
        super().__init__()
        self.imagens_base64 = []
        self.imagem_widgets = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Data e Nome lado a lado
        data_nome_layout = QHBoxLayout()
        self.data_edit = QDateEdit(calendarPopup=True)
        self.data_edit.setDisplayFormat("dd/MM/yyyy")
        self.data_edit.setDate(QDate.currentDate())
        self.data_edit.setFont(ARIAL_FONT)
        data_nome_layout.addWidget(QLabel("Data do registro:", font=ARIAL_FONT))
        data_nome_layout.addWidget(self.data_edit)

        self.nome_box = QComboBox()
        self.nome_box.setFont(ARIAL_FONT)
        self.nome_box.addItems(["Victor", "Clara"])
        data_nome_layout.addWidget(QLabel("Nome:", font=ARIAL_FONT))
        data_nome_layout.addWidget(self.nome_box)

        main_layout.addLayout(data_nome_layout)

        # Texto e botões
        main_layout.addWidget(QLabel("Texto do registro:", font=ARIAL_FONT))

        button_bar = QHBoxLayout()
        self.buttons = {}

        buttons_info = [
            ("Negrito", "Ctrl+B", self.toggle_negrito),
            ("Itálico", "Ctrl+I", self.toggle_italico),
            ("Sublinhado", "Ctrl+U", self.toggle_sublinhado),
            ("Marca-texto", "Ctrl+M", self.toggle_marcatexto),
            ("Título", "Ctrl+T", self.toggle_titulo),
            ("Enumeração", "Ctrl+E", self.aplicar_enum),
            ("Tópicos", "Ctrl+L", self.aplicar_topicos),
            ("Colar Imagem (Ctrl+V)", "Ctrl+V", self.colar_imagem_area_transferencia)
        ]

        for label, shortcut, callback in buttons_info:
            btn = QPushButton(label)
            btn.setFont(ARIAL_FONT)
            btn.setFixedHeight(28)
            btn.setCheckable(label not in ["Enumeração", "Tópicos", "Colar Imagem (Ctrl+V)"])
            btn.clicked.connect(callback)
            QShortcut(QKeySequence(shortcut), self).activated.connect(callback)
            button_bar.addWidget(btn)
            self.buttons[label] = btn

        main_layout.addLayout(button_bar)

        self.textbox = QTextEdit()
        self.textbox.setFont(ARIAL_FONT)
        main_layout.addWidget(self.textbox)

        # Área de rolagem para miniaturas com botões de remover
        self.scroll_area = QScrollArea()
        self.scroll_area.setFixedHeight(120)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QHBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setSpacing(10)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(QLabel("Imagens coladas:", font=ARIAL_FONT))
        main_layout.addWidget(self.scroll_area)

        self.save_button = QPushButton("Salvar Registro")
        self.save_button.setFont(ARIAL_FONT)
        self.save_button.clicked.connect(self.salvar_registro)
        main_layout.addWidget(self.save_button)

        self.setLayout(main_layout)

        self.textbox.cursorPositionChanged.connect(self.atualizar_botoes)

    def atualizar_botoes(self):
        fmt = self.textbox.currentCharFormat()
        self.buttons["Negrito"].setChecked(fmt.fontWeight() == QFont.Bold)
        self.buttons["Itálico"].setChecked(fmt.fontItalic())
        self.buttons["Sublinhado"].setChecked(fmt.fontUnderline())
        self.buttons["Marca-texto"].setChecked(fmt.background().color() == Qt.yellow)
        is_titulo = (fmt.fontPointSize() >= 16 and fmt.fontWeight() == QFont.Bold)
        self.buttons["Título"].setChecked(is_titulo)

    def toggle_negrito(self):
        cursor = self.textbox.textCursor()
        fmt = QTextCharFormat()
        current_weight = self.textbox.fontWeight()
        fmt.setFontWeight(QFont.Normal if current_weight == QFont.Bold else QFont.Bold)
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            self.textbox.setCurrentCharFormat(fmt)
        self.atualizar_botoes()

    def toggle_italico(self):
        cursor = self.textbox.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.textbox.fontItalic())
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            self.textbox.setCurrentCharFormat(fmt)
        self.atualizar_botoes()

    def toggle_sublinhado(self):
        cursor = self.textbox.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.textbox.fontUnderline())
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            self.textbox.setCurrentCharFormat(fmt)
        self.atualizar_botoes()

    def toggle_marcatexto(self):
        cursor = self.textbox.textCursor()
        fmt = QTextCharFormat()
        current_bg = self.textbox.textBackgroundColor()
        fmt.setBackground(Qt.transparent if current_bg == Qt.yellow else Qt.yellow)
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            self.textbox.setCurrentCharFormat(fmt)
        self.atualizar_botoes()

    def toggle_titulo(self):
        cursor = self.textbox.textCursor()
        fmt = QTextCharFormat()
        current_fmt = self.textbox.currentCharFormat()
        is_current_text_title = (current_fmt.fontPointSize() >= 16 and current_fmt.fontWeight() == QFont.Bold)

        if is_current_text_title:
            fmt.setFontPointSize(10)
            fmt.setFontWeight(QFont.Normal)
        else:
            fmt.setFontPointSize(16)
            fmt.setFontWeight(QFont.Bold)
            fmt.setFontUnderline(False)
            fmt.setFontItalic(False)

        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            self.textbox.setCurrentCharFormat(fmt)
        self.atualizar_botoes()

    def aplicar_enum(self):
        cursor = self.textbox.textCursor()
        cursor.beginEditBlock()
        fmt = QTextListFormat()
        fmt.setStyle(QTextListFormat.ListDecimal)
        cursor.createList(fmt)
        cursor.endEditBlock()

    def aplicar_topicos(self):
        cursor = self.textbox.textCursor()
        cursor.beginEditBlock()
        fmt = QTextListFormat()
        fmt.setStyle(QTextListFormat.ListDisc)
        cursor.createList(fmt)
        cursor.endEditBlock()

    def colar_imagem_area_transferencia(self):
        clipboard = QApplication.clipboard()
        image = clipboard.image()
        if image.isNull():
            QMessageBox.information(self, "Imagem", "Não há imagem na área de transferência.")
            return

        buffer = QBuffer()
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, "PNG")
        img_bytes = buffer.data()
        buffer.close()

        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        self.imagens_base64.append(img_base64)

        pixmap = QPixmap()
        pixmap.loadFromData(img_bytes)

        # Widget container para miniatura + botão remover
        container = QWidget()
        container.setFixedSize(110, 110)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(2)

        thumb = QLabel()
        thumb.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        thumb.setFrameShape(QFrame.Box)
        thumb.setLineWidth(1)
        thumb.setFixedSize(100, 100)
        thumb.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        btn_remove = QToolButton()
        btn_remove.setText("X")
        btn_remove.setFixedSize(20, 20)
        btn_remove.setToolTip("Remover imagem")
        btn_remove.clicked.connect(lambda _, w=container, b64=img_base64: self.remover_imagem(w, b64))

        container_layout.addWidget(thumb)
        container_layout.addWidget(btn_remove, alignment=Qt.AlignCenter)

        self.scroll_layout.addWidget(container)
        self.imagem_widgets.append(container)

        QMessageBox.information(self, "Imagem", "Imagem da área de transferência capturada e adicionada.")

    def remover_imagem(self, widget, img_base64):
        if img_base64 in self.imagens_base64:
            self.imagens_base64.remove(img_base64)
        self.scroll_layout.removeWidget(widget)
        widget.deleteLater()
        self.imagem_widgets.remove(widget)

    def salvar_registro(self):
        nome = self.nome_box.currentText()
        texto = self.textbox.toHtml().strip()
        texto = texto.replace("\n", "").replace("<br>", "")

        data_registro = self.data_edit.date().toString("dd/MM/yyyy")
        hora_registro = datetime.now().strftime("%H:%M")

        if not texto or texto == "<br>":
            QMessageBox.warning(self, "Erro", "O campo de texto está vazio.")
            return

        registro = {
            "data": data_registro,
            "hora": hora_registro,
            "nome": nome,
            "texto": texto,
            "imagens_base64": self.imagens_base64
        }

        dados = []
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                try:
                    dados = json.load(f)
                except json.JSONDecodeError:
                    pass

        dados.append(registro)

        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

        QMessageBox.information(self, "Salvo", "Registro salvo com sucesso!")
        self.textbox.clear()

        # Limpa miniaturas e lista de imagens
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.imagens_base64.clear()
        self.imagem_widgets.clear()
        self.atualizar_botoes()


class VisualizarTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        splitter = QSplitter(Qt.Horizontal)

        self.lista = QListWidget()
        self.lista.setFont(ARIAL_FONT)
        self.lista.itemClicked.connect(self.mostrar_detalhes)
        splitter.addWidget(self.lista)

        self.texto_view = QTextEdit()
        self.texto_view.setReadOnly(True)
        self.texto_view.setFont(ARIAL_FONT)
        splitter.addWidget(self.texto_view)

        splitter.setSizes([300, 600])
        layout.addWidget(splitter)

        self.setLayout(layout)
        self.carregar_dados()

    def carregar_dados(self):
        self.lista.clear()
        self.texto_view.clear()

        if not os.path.exists(JSON_FILE):
            self.lista.addItem("Nenhum registro encontrado.")
            return

        with open(JSON_FILE, "r", encoding="utf-8") as f:
            try:
                self.dados = json.load(f)
            except json.JSONDecodeError:
                self.lista.addItem("Erro ao carregar JSON.")
                return

        def sort_key(x):
            data_str = x.get('data', '01/01/1900')
            hora_str = x.get('hora', '00:00')
            try:
                return datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M")
            except ValueError:
                return datetime.min

        self.dados.sort(key=sort_key, reverse=True)

        for item in self.dados:
            data_display = item.get('data', '')
            hora_display = item.get('hora', '')
            resumo = item.get("texto", "").replace("\n", " ").strip()[:40]
            linha = f"{data_display} {hora_display} - {item.get('nome', '')}: {resumo}..."
            self.lista.addItem(linha)

    def mostrar_detalhes(self, item):
        index = self.lista.row(item)
        if 0 <= index < len(self.dados):
            registro = self.dados[index]
            texto_html = registro.get("texto", "").replace("\n", "<br>")
            html = f"<div style='font-family: Arial; font-size: 11pt; line-height: 1.4'>{texto_html}</div>"

            imagens_base64 = registro.get("imagens_base64", [])
            from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

            # Remove container antigo se existir
            if hasattr(self, 'container_widget'):
                self.layout().removeWidget(self.container_widget)
                self.container_widget.deleteLater()
                del self.container_widget

            if imagens_base64:
                container = QWidget()
                vlayout = QVBoxLayout(container)

                label_texto = QTextEdit()
                label_texto.setReadOnly(True)
                label_texto.setFont(ARIAL_FONT)
                label_texto.setHtml(html)
                vlayout.addWidget(label_texto)

                for img_b64 in imagens_base64:
                    img_bytes = base64.b64decode(img_b64)
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_bytes)
                    label_imagem = QLabel()
                    label_imagem.setPixmap(pixmap.scaledToWidth(400, Qt.SmoothTransformation))
                    vlayout.addWidget(label_imagem)

                self.texto_view.hide()
                self.layout().addWidget(container)
                self.container_widget = container
            else:
                self.texto_view.show()
                self.texto_view.setHtml(html)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro de Informações")
        self.setGeometry(100, 100, 900, 500)

        self.tabs = QTabWidget()
        self.tabs.setFont(ARIAL_FONT)

        self.registro_tab = RegistroTab()
        self.visualizar_tab = VisualizarTab()

        self.tabs.addTab(self.registro_tab, "Registrar")
        self.tabs.addTab(self.visualizar_tab, "Visualizar")

        self.setCentralWidget(self.tabs)

        self.tabs.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        if index == 1:
            self.visualizar_tab.carregar_dados()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(ARIAL_FONT)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
