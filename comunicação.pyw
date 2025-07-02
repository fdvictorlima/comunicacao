import sys
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QComboBox, QTextEdit, QPushButton, QTabWidget, QMessageBox,
    QListWidget, QDateEdit, QHBoxLayout, QSplitter, QShortcut
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont, QKeySequence, QTextCursor, QTextListFormat

JSON_FILE = "dados.json"
ARIAL_FONT = QFont("Arial", 10)


class RegistroTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.data_edit = QDateEdit(calendarPopup=True)
        self.data_edit.setDisplayFormat("dd-MM-yyyy")
        self.data_edit.setDate(QDate.currentDate())
        self.data_edit.setFont(ARIAL_FONT)
        layout.addWidget(QLabel("Data do registro:", font=ARIAL_FONT))
        layout.addWidget(self.data_edit)

        self.nome_box = QComboBox()
        self.nome_box.setFont(ARIAL_FONT)
        self.nome_box.addItems(["Victor", "Clara"])
        layout.addWidget(QLabel("Selecione o nome:", font=ARIAL_FONT))
        layout.addWidget(self.nome_box)

        layout.addWidget(QLabel("Texto do registro:", font=ARIAL_FONT))

        button_bar = QHBoxLayout()
        self.buttons = {}
        for label, shortcut, callback in [
            ("Negrito", "Ctrl+B", self.toggle_negrito),
            ("Itálico", "Ctrl+I", self.toggle_italico),
            ("Sublinhado", "Ctrl+U", self.toggle_sublinhado),
            ("Marca-texto", "Ctrl+M", self.toggle_marcatexto),
            ("Título", "Ctrl+T", self.toggle_titulo),
            ("Enumeração", "Ctrl+E", self.aplicar_enum),
            ("Tópicos", "Ctrl+L", self.aplicar_topicos)
        ]:
            btn = QPushButton(f"{label} ({shortcut})")
            btn.setFont(ARIAL_FONT)
            btn.setFixedHeight(28)
            btn.clicked.connect(callback)
            QShortcut(QKeySequence(shortcut), self).activated.connect(callback)
            button_bar.addWidget(btn)
            self.buttons[label] = btn

        layout.addLayout(button_bar)

        self.textbox = QTextEdit()
        self.textbox.setFont(ARIAL_FONT)
        layout.addWidget(self.textbox)

        self.save_button = QPushButton("Salvar Registro")
        self.save_button.setFont(ARIAL_FONT)
        self.save_button.clicked.connect(self.salvar_registro)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def toggle_format(self, attr, toggle_value):
        cursor = self.textbox.textCursor()
        fmt = cursor.charFormat()
        current = getattr(fmt, attr)()
        getattr(fmt, f"set{attr.capitalize()}")(not current if toggle_value is None else toggle_value)
        cursor.mergeCharFormat(fmt)

    def toggle_negrito(self):
        self.toggle_format("FontWeight", None)

    def toggle_italico(self):
        self.toggle_format("FontItalic", None)

    def toggle_sublinhado(self):
        self.toggle_format("FontUnderline", None)

    def toggle_marcatexto(self):
        cursor = self.textbox.textCursor()
        fmt = cursor.charFormat()
        current_color = fmt.background().color().name()
        fmt.setBackground(Qt.transparent if current_color == "#ffff00" else Qt.yellow)
        cursor.mergeCharFormat(fmt)

    def toggle_titulo(self):
        cursor = self.textbox.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            if selected.startswith("\u2029"):
                selected = selected[1:]
            html = f"<h3>{selected}</h3>" if "<h3>" not in selected else selected.replace("<h3>", "").replace("</h3>", "")
            cursor.insertHtml(html)

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

    def salvar_registro(self):
        nome = self.nome_box.currentText()
        texto = self.textbox.toHtml().strip()
        data = self.data_edit.date().toString("dd-MM-yyyy")
        hora = datetime.now().strftime("%H:%M:%S")

        if not texto or texto == "<br>":
            QMessageBox.warning(self, "Erro", "O campo de texto está vazio.")
            return

        registro = {
            "data": data,
            "hora": hora,
            "nome": nome,
            "texto": texto
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

        self.dados.sort(key=lambda x: datetime.strptime(f"{x['data']} {x.get('hora', '00:00:00')}", "%d-%m-%Y %H:%M:%S"), reverse=True)

        for item in self.dados:
            resumo = item["texto"].replace("\n", " ").strip()[:40]
            linha = f"{item['data']} {item.get('hora', '')} - {item['nome']}: {resumo}..."
            self.lista.addItem(linha)

    def mostrar_detalhes(self, item):
        index = self.lista.row(item)
        if 0 <= index < len(self.dados):
            texto_html = self.dados[index].get("texto", "").replace("\n", "<br>")
            self.texto_view.setHtml(f"<div style='font-family: Arial; font-size: 11pt'>{texto_html}</div>")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro de Informações")
        self.setGeometry(100, 100, 900, 500)

        tabs = QTabWidget()
        tabs.setFont(ARIAL_FONT)
        tabs.addTab(RegistroTab(), "Registrar")
        tabs.addTab(VisualizarTab(), "Visualizar")

        self.setCentralWidget(tabs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(ARIAL_FONT)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())