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
from PyQt5.QtGui import QFont, QKeySequence, QTextCursor, QTextListFormat, QTextCharFormat

JSON_FILE = "dados.json"
ARIAL_FONT = QFont("Arial", 10)

class RegistroTab(QWidget):
    def __init__(self):
        super().__init__()
        self.titulo_ativo = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.data_edit = QDateEdit(calendarPopup=True)
        self.data_edit.setDisplayFormat("dd/MM/yyyy") # Formato de exibição da data
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

        buttons_info = [
            ("Negrito", "Ctrl+B", self.toggle_negrito),
            ("Itálico", "Ctrl+I", self.toggle_italico),
            ("Sublinhado", "Ctrl+U", self.toggle_sublinhado),
            ("Marca-texto", "Ctrl+M", self.toggle_marcatexto),
            ("Título", "Ctrl+T", self.toggle_titulo),
            ("Enumeração", "Ctrl+E", self.aplicar_enum),
            ("Tópicos", "Ctrl+L", self.aplicar_topicos)
        ]

        for label, shortcut, callback in buttons_info:
            btn = QPushButton(f"{label} ({shortcut})")
            btn.setFont(ARIAL_FONT)
            btn.setFixedHeight(28)
            btn.setCheckable(label not in ["Enumeração", "Tópicos"])
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

        self.textbox.cursorPositionChanged.connect(self.atualizar_botoes)

    def atualizar_botoes(self):
        fmt = self.textbox.currentCharFormat()
        # cursor = self.textbox.textCursor() # Não utilizado diretamente aqui

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
        # Ao invés de usar self.titulo_ativo, verificamos o formato atual do texto
        # para determinar se estamos no modo título ou normal.
        current_fmt = self.textbox.currentCharFormat()
        is_current_text_title = (current_fmt.fontPointSize() >= 16 and current_fmt.fontWeight() == QFont.Bold)

        if is_current_text_title:
            fmt.setFontPointSize(10) # Tamanho normal
            fmt.setFontWeight(QFont.Normal)
        else:
            fmt.setFontPointSize(16) # Tamanho de título
            fmt.setFontWeight(QFont.Bold)
            fmt.setFontUnderline(False) # Garante que não está sublinhado
            fmt.setFontItalic(False) # Garante que não está itálico

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

    def salvar_registro(self):
        nome = self.nome_box.currentText()
        texto = self.textbox.toHtml().strip()
        # Remove quebras de linha desnecessárias, mas preserva a formatação HTML
        texto = texto.replace("\n", "").replace("<br>", "")

        # Formata data e hora separadamente
        data_registro = self.data_edit.date().toString("dd/MM/yyyy")
        hora_registro = datetime.now().strftime("%H:%M") # Hora no formato HH:mm

        if not texto or texto == "<br>":
            QMessageBox.warning(self, "Erro", "O campo de texto está vazio.")
            return

        registro = {
            "data": data_registro, # Campo 'data'
            "hora": hora_registro, # Campo 'hora'
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

        # Ajusta a chave de ordenação para considerar 'data' e 'hora' separadamente
        # Tenta data + hora, senão só data, senão vazio para evitar erro em dados antigos
        def sort_key(x):
            data_str = x.get('data', '01/01/1900')
            hora_str = x.get('hora', '00:00')
            try:
                # Tenta analisar no novo formato dd/MM/yyyy HH:mm
                return datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M")
            except ValueError:
                try:
                    # Se falhar, tenta o formato antigo dd-MM-yyyy HH:MM:SS
                    # (precisa ser compatível com o formato que o script de correção usaria)
                    return datetime.strptime(f"{x.get('data', '01-01-1900')} {x.get('hora', '00:00:00')}", "%d-%m-%Y %H:%M:%S")
                except ValueError:
                    return datetime.min # Valor mínimo para ordenar no final em caso de erro

        self.dados.sort(key=sort_key, reverse=True)


        for item in self.dados:
            # Pega data e hora dos campos separados. Se não existirem (dados antigos),
            # usa o campo 'data_hora' se houver, ou string vazia.
            data_display = item.get('data', '')
            hora_display = item.get('hora', '')
            if not data_display and 'data_hora' in item: # Compatibilidade com formato anterior
                data_display = item['data_hora'].split(' ')[0]
                hora_display = item['data_hora'].split(' ')[1]

            resumo = item["texto"].replace("\n", " ").strip()[:40]
            linha = f"{data_display} {hora_display} - {item['nome']}: {resumo}..."
            self.lista.addItem(linha)

    def mostrar_detalhes(self, item):
        index = self.lista.row(item)
        if 0 <= index < len(self.dados):
            texto_html = self.dados[index].get("texto", "").replace("\n", "<br>")
            self.texto_view.setHtml(f"<div style='font-family: Arial; font-size: 11pt; line-height: 1.4'>{texto_html}</div>")

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
