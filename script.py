import sys
import socket
import time
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QGroupBox, QComboBox, QSpinBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QFrame
)
from Crypto.Hash import SHA256

# --- Logic Functions ---
def get_unique_5_digit_code():
    """Generates a unique 5-digit code using SHA-256 of the current timestamp."""
    timestamp_str = str(time.time()).encode('utf-8')
    hash_obj = SHA256.new(data=timestamp_str)
    hash_hex = hash_obj.hexdigest()
    unique_int = int(hash_hex, 16)
    return str(unique_int)[-5:]


# --- Background Worker for Networking ---
class PrintWorker(QThread):
    finished = Signal(bool, str, int, str)  # success, details, total_labels, unique_code

    def __init__(self, ip, port, mode, total_labels, manual_code):
        super().__init__()
        self.ip = ip
        self.port = port
        self.mode = mode
        self.total_labels = total_labels
        self.manual_code = manual_code

    def run(self):
        unique_code = ""
        if self.mode == "Sequencial":
            unique_code = get_unique_5_digit_code()

        # Build configuration header
        all_labels_zpl = (
            "~CT~~CD,~CC^~CT~\n"
            "^XA\n~TA000\n~JSN\n^LT0\n^MNW\n^MTT\n^PON\n^PMN\n^LH0,0\n^JMA\n^PR6,6\n~SD15\n^JUS\n^LRN\n^CI27\n^PA0,1,1,0\n^XZ\n"
        )

        # Assemble the string sequence loop
        for counter in range(1, self.total_labels + 1):
            if self.mode == "Sequencial":
                counter_str = f"{counter:03d}"
                barcode_payload = f"REC{unique_code}{counter_str}ARQ"
            else:
                barcode_payload = f"REC{self.manual_code}ARQ"

            label_zpl = (
                f"^XA\n"
                f"^MMT\n"
                f"^PW783\n"
                f"^LL384\n"
                f"^LS0\n"
                f"^FO2,7^GB771,369,4^FS\n"
                f"^FT300,145^A0N,102,101^FH\\^CI28^FDLPN^FS^CI27\n"
                f"^FO105,170^BY3^BCN,100,N,N,N^FD{barcode_payload}^FS\n" 
                f"^FT220,320^A0N,48,46^FD{barcode_payload}^FS\n"
                f"^FO659,333^GFA,373,512,16,:Z64:eJxlkD1qxDAQhZ9xDIYUZgvXOUIOsIVcKL0L6z6CbQx7Cd8g7bJFHMhFVPoIZgWezJMES8jDI0v+9Dw/gAc08gq8WAtYard/6w4mylJHiQ+gPvTcOzc2TgVUE7nI8S6qb3TkRD2XAU3ia9GC7pb9WSOaUx+YryK7n9cd3Y4kMvQjnySJAXjdYUI+9+Rq7lljyxK2lskT149MMWhyR26WVMK9/sLqn9xVDo4/WwNbEPGHF3JX+MAb9Aeco/Yf4uWB4h9PJ/KpcLOhlSA/B7KfeZV/ZL5AW9eX+bxlf5V56kLBdpUwzxLeZEeZ38Ao/CxRvMbSxYAyP15Ck9pL8wfr7yQU//SHc/JmvaNO7f/TLySEld0=:7C7C\n"
                f"^PQ1,0,1,Y\n"
                f"^XZ\n"
            )
            all_labels_zpl += label_zpl

        # Stream to the Zebra device
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((self.ip, self.port))
                s.sendall(all_labels_zpl.encode('utf-8'))
            self.finished.emit(True, "Sucesso", self.total_labels, unique_code)
        except Exception as e:
            self.finished.emit(False, str(e), self.total_labels, unique_code)


# --- Main Application Window ---
class LabelPrinterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Impressão de etiquetas REC 🏷️")
        self.setMinimumWidth(500)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        title_label = QLabel("Impressão de etiquetas REC")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        subtitle_label = QLabel("Imprima etiquetas LPN no formulário abaixo.")
        
        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # --- Toggle Button for Configurations ---
        self.toggle_config_button = QPushButton("⚙️ Mostrar Configurações da Impressora")
        self.toggle_config_button.setStyleSheet(
            "font-weight: bold; padding: 6px;"
        )
        self.toggle_config_button.setCheckable(True)
        self.toggle_config_button.clicked.connect(self.toggle_config_visibility)
        main_layout.addWidget(self.toggle_config_button)

        # --- Group Box: Printer Configurations ---
        self.config_group = QGroupBox("⚙️ Configurações da Impressora")
        config_layout = QFormLayout()
        
        self.ip_input = QLineEdit("10.55.22.240")
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(9100)
        
        config_layout.addRow("IP da Impressora:", self.ip_input)
        config_layout.addRow("Porta:", self.port_input)
        self.config_group.setLayout(config_layout)
        main_layout.addWidget(self.config_group)
        
        # Hide the settings panel initially
        self.config_group.hide()

        # Separator between settings and runtime workflow
        self.workflow_line = QFrame()
        self.workflow_line.setFrameShape(QFrame.HLine)
        self.workflow_line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(self.workflow_line)

        # --- Print Mode Selection ---
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Selecione o modo de impressão:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Sequencial", "Reimpressão Manual"])
        self.mode_combo.currentTextChanged.connect(self.toggle_mode_widgets)
        mode_layout.addWidget(self.mode_combo)
        main_layout.addLayout(mode_layout)

        self.seq_container = QWidget()
        seq_layout = QHBoxLayout(self.seq_container)
        seq_layout.setContentsMargins(0, 0, 0, 0)
        seq_layout.addWidget(QLabel("Quantas etiquetas serão impressas?"))
        self.total_labels_input = QSpinBox()
        self.total_labels_input.setRange(1, 999)
        self.total_labels_input.setValue(1)
        self.total_labels_input.setToolTip("Escolha um número entre 1 e 999")
        seq_layout.addWidget(self.total_labels_input)
        main_layout.addWidget(self.seq_container)

        self.manual_container = QWidget()
        manual_outer_layout = QVBoxLayout(self.manual_container)
        manual_outer_layout.setContentsMargins(0, 0, 0, 0)
        manual_outer_layout.addWidget(QLabel("Insira o código numérico da LPN:"))
        
        manual_input_layout = QHBoxLayout()
        self.prefix_input = QLineEdit("REC")
        self.prefix_input.setEnabled(False)
        self.prefix_input.setMaximumWidth(50)
        self.prefix_input.setAlignment(Qt.AlignCenter)
        
        self.manual_code_input = QLineEdit()
        self.manual_code_input.setMaxLength(8)
        self.manual_code_input.setPlaceholderText("12345001")
        self.manual_code_input.setToolTip("Insira apenas os 8 números centrais.")
        
        self.suffix_input = QLineEdit("ARQ")
        self.suffix_input.setEnabled(False)
        self.suffix_input.setMaximumWidth(50)
        self.suffix_input.setAlignment(Qt.AlignCenter)
        
        manual_input_layout.addWidget(self.prefix_input)
        manual_input_layout.addWidget(self.manual_code_input)
        manual_input_layout.addWidget(self.suffix_input)
        manual_outer_layout.addLayout(manual_input_layout)
        main_layout.addWidget(self.manual_container)
        
        self.manual_container.hide()

        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: blue; font-weight: bold;")
        self.info_label.setWordWrap(True)
        main_layout.addWidget(self.info_label)

        self.print_button = QPushButton("Iniciar Impressão")
        self.print_button.setStyleSheet(
            "font-weight: bold; font-size: 14px; padding: 8px;"
        )
        self.print_button.clicked.connect(self.handle_print)
        main_layout.addWidget(self.print_button)

        main_layout.addStretch()

    @Slot(bool)
    def toggle_config_visibility(self, checked):
        if checked:
            self.config_group.show()
            self.toggle_config_button.setText("⚙️ Ocultar Configurações da Impressora")
        else:
            self.config_group.hide()
            self.toggle_config_button.setText("⚙️ Mostrar Configurações da Impressora")

    @Slot(str)
    def toggle_mode_widgets(self, mode):
        if mode == "Sequencial":
            self.seq_container.show()
            self.manual_container.hide()
        else:
            self.seq_container.hide()
            self.manual_container.show()
        self.info_label.clear()

    def handle_print(self):
        mode = self.mode_combo.currentText()
        ip = self.ip_input.text().strip()
        port = self.port_input.value()
        
        if not ip:
            QMessageBox.warning(self, "Aviso", "Por favor, insira o endereço IP da impressora.")
            return

        manual_code = ""
        total_labels = 1

        if mode == "Reimpressão Manual":
            manual_code = self.manual_code_input.text().strip()
            if not manual_code or not manual_code.isdigit() or len(manual_code) != 8:
                QMessageBox.critical(
                    self, "Erro de Validação", 
                    "❌ O código inserido deve conter exatamente 8 dígitos numéricos."
                )
                return
        else:
            total_labels = self.total_labels_input.value()

        self.print_button.setEnabled(False)
        self.print_button.setText("Enviando dados de impressão...")
        self.info_label.setText(f"Conectando à impressora em {ip}:{port}...")

        self.worker = PrintWorker(ip, port, mode, total_labels, manual_code)
        self.worker.finished.connect(self.on_print_finished)
        self.worker.start()

    @Slot(bool, str, int, str)
    def on_print_finished(self, success, details, total_labels, unique_code):
        self.print_button.setEnabled(True)
        self.print_button.setText("Iniciar Impressão")
        
        if success:
            if unique_code:
                self.info_label.setText(f"✅ Sequência única deste lote: {unique_code}")
            else:
                self.info_label.clear()

            QMessageBox.information(
                self, "Sucesso", 
                f"🖨️ Impressão de {total_labels} etiqueta(s) enviada(s) com sucesso!"
            )
        else:
            self.info_label.clear()
            QMessageBox.critical(
                self, "Erro de Conexão", 
                f"❌ Erro ao tentar se conectar à impressora.\n\nDetalhes técnicos: {details}"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LabelPrinterApp()
    window.show()
    sys.exit(app.exec())