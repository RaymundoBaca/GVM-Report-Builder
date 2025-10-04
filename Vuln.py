import sys
import threading
import traceback
from pathlib import Path
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

# -----------------------
# Custom Exception for Cancellation
# -----------------------
class CancelledException(Exception):
    """Raised when user cancels the execution."""
    pass

# -----------------------
# PyInstaller path adjustment
# -----------------------
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

RESULTS_DIR = BASE_DIR / "Results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------
# Import internal scripts
# -----------------------
try:
    from sc import rAI1_0, rAI1_1, rAI1_2, rAI1_3, rAI1_4
    from sc import rAI2_1, rAI2_2, rAI2_3, rAI2_5
    from sc import rAI3, rAI4, rAI5
except Exception:
    traceback.print_exc()
    input("Error importing scripts. Press Enter to exit...")
    sys.exit(1)

# -----------------------
# Main application class
# -----------------------
class MainApp(QtWidgets.QMainWindow):
    # Safe signals to update GUI
    log_signal = QtCore.Signal(str, str)        # message, type
    progress_signal = QtCore.Signal(int)        # value
    finished_signal = QtCore.Signal(bool, str)  # success, message

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vulnerability Analysis")
        self.setFixedSize(900, 720)
        self.cancelled = False

        # Window icon
        try:
            self.setWindowIcon(QtGui.QIcon(str(BASE_DIR / "favicon.ico")))
        except Exception:
            pass
        
        # Dictionary to store original button colors for hover effect
        self.button_colors = {}

        # -----------------------
        # Main layout
        # -----------------------
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QGridLayout()
        central_widget.setLayout(layout)

        layout.setContentsMargins(16, 12, 16, 12)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(10)
        layout.setColumnStretch(0, 6)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(2, 2)

        label_style = "color: white; font-size: 13px;"
        entry_style = "background-color: #2e2e2e; color: white;"

        # Detail label
        label_detail = QtWidgets.QLabel("Select the detail level for the report:")
        label_detail.setStyleSheet(label_style)
        layout.addWidget(label_detail, 0, 0)

        # Detail combo box
        self.combo_detail = QtWidgets.QComboBox()
        self.combo_detail.addItems(["1 - Precise", "2 - Super Precise", "3 - No Details"])
        self.combo_detail.setStyleSheet(entry_style)
        layout.addWidget(self.combo_detail, 1, 0, 1, 3)

        # PDF selection
        lbl_pdf = QtWidgets.QLabel("Select your PDF report:")
        lbl_pdf.setStyleSheet(label_style)
        layout.addWidget(lbl_pdf, 2, 0)
        self.line_pdf = QtWidgets.QLineEdit()
        self.line_pdf.setStyleSheet(entry_style)
        self.line_pdf.setReadOnly(True)  # Read-only to force button usage
        layout.addWidget(self.line_pdf, 3, 0)
        btn_pdf = QtWidgets.QPushButton("Browse PDF")
        btn_pdf.setStyleSheet("""
            background-color: #4169E1;
            border: 1px solid white;
            border-radius: 5px;
            padding: 4px 8px;
            color: white;
        """)
        btn_pdf.clicked.connect(self.select_pdf)
        self.button_colors[btn_pdf] = ("#4169E1", "#2E4C9E")  # normal, hover
        btn_pdf.installEventFilter(self)
        layout.addWidget(btn_pdf, 3, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        # TXT selection
        lbl_txt = QtWidgets.QLabel("Select your TXT report:")
        lbl_txt.setStyleSheet(label_style)
        layout.addWidget(lbl_txt, 4, 0)
        self.line_txt = QtWidgets.QLineEdit()
        self.line_txt.setStyleSheet(entry_style)
        self.line_txt.setReadOnly(True)  # Read-only to force button usage
        layout.addWidget(self.line_txt, 5, 0)
        btn_txt = QtWidgets.QPushButton("Browse TXT")
        btn_txt.setStyleSheet("""
            background-color: #4169E1;
            border: 1px solid white;
            border-radius: 5px;
            padding: 4px 8px;
            color: white;
        """)
        btn_txt.clicked.connect(self.select_txt)
        self.button_colors[btn_txt] = ("#4169E1", "#2E4C9E")  # normal, hover
        btn_txt.installEventFilter(self)
        layout.addWidget(btn_txt, 5, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        # Output folder
        lbl_folder = QtWidgets.QLabel("Select the output folder:")
        lbl_folder.setStyleSheet(label_style)
        layout.addWidget(lbl_folder, 6, 0)
        self.line_folder = QtWidgets.QLineEdit()
        self.line_folder.setStyleSheet(entry_style)
        self.line_folder.setReadOnly(True)  # Read-only to force button usage
        layout.addWidget(self.line_folder, 7, 0)
        btn_folder = QtWidgets.QPushButton("Select")
        btn_folder.setStyleSheet("""
            background-color: #4169E1;
            border: 1px solid white;
            border-radius: 5px;
            padding: 4px 8px;
            color: white;
        """)
        btn_folder.clicked.connect(self.select_folder)
        self.button_colors[btn_folder] = ("#4169E1", "#2E4C9E")  # normal, hover
        btn_folder.installEventFilter(self)
        layout.addWidget(btn_folder, 7, 1, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)

        # Hackjolote image
        try:
            hack = QtGui.QPixmap(str(BASE_DIR / "Hackalotl.png")).scaled(
                200, 200, QtCore.Qt.AspectRatioMode.KeepAspectRatio
            )
            label_hack = QtWidgets.QLabel()
            label_hack.setPixmap(hack)
            layout.addWidget(label_hack, 2, 2, 6, 1, alignment=QtCore.Qt.AlignmentFlag.AlignTop)
        except Exception:
            pass

        # Console
        self.text_console = QtWidgets.QTextEdit()
        self.text_console.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.text_console.setStyleSheet("background-color: #2e2e2e; color: white;")
        layout.addWidget(self.text_console, 8, 0, 1, 3)

        # Progress bar
        self.progress = QtWidgets.QProgressBar()
        layout.addWidget(self.progress, 9, 0, 1, 3)

        # Buttons (below progress bar)
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_cancel.setStyleSheet("""
            background-color: #B80000;
            border: 1px solid white;
            border-radius: 5px;
            padding: 5px 10px;
            color: white;
        """)
        btn_cancel.clicked.connect(self.cancel)
        self.button_colors[btn_cancel] = ("#B80000", "#8B0000")  # normal, hover
        btn_cancel.installEventFilter(self)

        self.btn_run = QtWidgets.QPushButton("Run")
        self.btn_run.setStyleSheet("""
            background-color: #008507;
            border: 1px solid white;
            border-radius: 5px;
            padding: 5px 10px;
            color: white;
        """)
        self.btn_run.clicked.connect(self.start_thread)
        self.button_colors[self.btn_run] = ("#008507", "#006405")  # normal, hover
        self.btn_run.installEventFilter(self)

        # Credit label (centered)
        lbl_credit = QtWidgets.QLabel()
        lbl_credit.setText('<span style="color:#00BFFF;">Created by:</span> <span style="color:white;">José Raymundo Baca Hernández</span>')
        lbl_credit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Horizontal layout for bottom row
        btn_hbox = QtWidgets.QHBoxLayout()
        btn_hbox.addWidget(btn_cancel)    # Cancel button left
        btn_hbox.addStretch()             # Space
        btn_hbox.addWidget(lbl_credit)    # Credit label center
        btn_hbox.addStretch()             # Space
        btn_hbox.addWidget(self.btn_run)  # Run button right
        layout.addLayout(btn_hbox, 10, 0, 1, 3)  # Add to grid

        # Set dark background globally
        self.setStyleSheet("background-color: #1e1e1e;")

        # Connect signals
        self.log_signal.connect(self.log)
        self.progress_signal.connect(self.progress.setValue)
        self.finished_signal.connect(self.on_finished)


    # -------------------------------
    # GUI functions
    # -------------------------------
    def eventFilter(self, obj, event):
        """Event filter to handle button hover effects."""
        if obj in self.button_colors:
            # Skip hover effect if button is disabled (like Run button during execution)
            if not obj.isEnabled():
                return super().eventFilter(obj, event)
            
            normal_color, hover_color = self.button_colors[obj]
            
            if event.type() == QtCore.QEvent.Enter:
                # Mouse entered button - apply hover color
                obj.setStyleSheet(f"""
                    background-color: {hover_color};
                    border: 1px solid white;
                    border-radius: 5px;
                    padding: {'5px 10px' if obj in [self.btn_run] or 'Cancel' in obj.text() else '4px 8px'};
                    color: white;
                """)
            elif event.type() == QtCore.QEvent.Leave:
                # Mouse left button - restore normal color
                obj.setStyleSheet(f"""
                    background-color: {normal_color};
                    border: 1px solid white;
                    border-radius: 5px;
                    padding: {'5px 10px' if obj in [self.btn_run] or 'Cancel' in obj.text() else '4px 8px'};
                    color: white;
                """)
        
        return super().eventFilter(obj, event)
    
    def select_pdf(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if path:
            self.line_pdf.setText(path)

    def select_txt(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select TXT", "", "TXT Files (*.txt)")
        if path:
            self.line_txt.setText(path)

    def select_folder(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select output folder")
        if path:
            self.line_folder.setText(path)

    def log(self, message, type_="info"):
        color = {"info": "white", "warning": "orange", "error": "red", "success": "green"}.get(type_, "white")
        cursor = self.text_console.textCursor()
        fmt = QtGui.QTextCharFormat()
        fmt.setForeground(QtGui.QBrush(QtGui.QColor(color)))
        cursor.setCharFormat(fmt)
        cursor.insertText(message + "\n")
        self.text_console.verticalScrollBar().setValue(self.text_console.verticalScrollBar().maximum())
        QApplication.processEvents()

    def start_thread(self):
        # Disable Run button and update text
        self.btn_run.setEnabled(False)
        self.btn_run.setText("Running...")
        # Apply darker color when disabled to show it's not clickable
        self.btn_run.setStyleSheet("""
            background-color: #006405;
            border: 1px solid white;
            border-radius: 5px;
            padding: 5px 10px;
            color: white;
        """)

        # Clear console before running
        self.text_console.clear()
        self.progress_signal.emit(0)
        self.cancelled = False
        threading.Thread(target=self.run_scripts, daemon=True).start()
        self.log_signal.emit("✅ Execution started by user.", "success")

    def cancel(self):
        self.cancelled = True
        self.progress_signal.emit(0)
        self.log_signal.emit("⚠️ Cancelling execution...", "warning")
        QApplication.processEvents()

    # -------------------------------
    # Script execution (background thread)
    # -------------------------------
    def run_scripts(self):
        if not self.line_pdf.text() or not self.line_txt.text():
            self.finished_signal.emit(False, "You must select both PDF and TXT.")
            return

        detail = self.combo_detail.currentText()[0]
        pdf_path = Path(self.line_pdf.text())
        txt_path = Path(self.line_txt.text())
        output_dir = Path(self.line_folder.text()) if self.line_folder.text() else RESULTS_DIR

        # Progress tracking
        total_scripts = 9  # 5 rAI1 + 1 rAI2 + 1 rAI2_5 + 3 others
        current_script_idx = 0
        
        def log_wrapper(message, type_="info"):
            """Wrapper to emit log signal and force GUI update from thread."""
            if self.cancelled:
                raise CancelledException("Execution cancelled by user")
            self.log_signal.emit(message, type_)
            QApplication.processEvents()
        
        def update_progress(script_progress):
            """Update progress considering both script index and internal progress.
            script_progress: 0.0 to 1.0 representing progress within current script
            """
            if self.cancelled:
                raise CancelledException("Execution cancelled by user")
            base_progress = (current_script_idx / total_scripts) * 100
            script_weight = (1 / total_scripts) * 100
            total_progress = base_progress + (script_progress * script_weight)
            self.progress_signal.emit(int(total_progress))
            # Force GUI update
            QApplication.processEvents()

        try:
            self.progress_signal.emit(0)

            # rAI1.x
            scripts_rAI1 = [rAI1_0, rAI1_1, rAI1_2, rAI1_3, rAI1_4]
            for idx, script in enumerate(scripts_rAI1):
                current_script_idx = idx
                script.main(pdf_path, txt_path, log_wrapper, output_dir=output_dir, progress_callback=update_progress)
                current_script_idx = idx + 1
                update_progress(0.0)

            # rAI2.x
            current_script_idx = 5
            if detail == "1":
                rAI2_1.main(pdf_path, txt_path, log_wrapper, output_dir=output_dir, progress_callback=update_progress)
            elif detail == "2":
                rAI2_2.main(pdf_path, txt_path, log_wrapper, output_dir=output_dir, progress_callback=update_progress)
            else:
                rAI2_3.main(pdf_path, txt_path, log_wrapper, output_dir=output_dir, progress_callback=update_progress)
            current_script_idx = 6
            update_progress(0.0)

            current_script_idx = 6
            rAI2_5.main(pdf_path, txt_path, log_wrapper, output_dir=output_dir, progress_callback=update_progress)
            current_script_idx = 7
            update_progress(0.0)

            # rAI3-5
            others = [rAI3, rAI4, rAI5]
            for idx, script in enumerate(others):
                current_script_idx = 7 + idx
                script.main(pdf_path, txt_path, log_wrapper, output_dir=output_dir, progress_callback=update_progress)
                current_script_idx = 7 + idx + 1
                update_progress(0.0)

            self.progress_signal.emit(100)
            self.finished_signal.emit(True, "All scripts completed successfully.")

        except CancelledException:
            self.log_signal.emit("⚠️ Execution cancelled by user.", "warning")
            self.finished_signal.emit(False, "Execution cancelled by user.")
        except Exception as e:
            self.log_signal.emit(f"[ERROR] {e}", "error")
            traceback.print_exc()
            self.finished_signal.emit(False, str(e))

    # -------------------------------
    # Finish handler (executed in GUI)
    # -------------------------------
    def on_finished(self, success: bool, msg: str):
        self.btn_run.setEnabled(True)
        self.btn_run.setText("Run")
        # Restore normal color when re-enabled
        self.btn_run.setStyleSheet("""
            background-color: #008507;
            border: 1px solid white;
            border-radius: 5px;
            padding: 5px 10px;
            color: white;
        """)

        if success:
            QtWidgets.QMessageBox.information(self, "Success", msg)
        else:
            QtWidgets.QMessageBox.critical(self, "Error", msg)

# -----------------------
# FIX: Unique taskbar ID (Windows)
# -----------------------
try:
    import ctypes
    myappid = u"GVM.Reports.By.Raymundo.v1"  # Unique identifier
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# -----------------------
# PyInstaller path adjustment
# -----------------------
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

RESULTS_DIR = BASE_DIR / "Results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # -----------------------
    # Uniform style for all Windows
    # -----------------------
    QtWidgets.QApplication.setStyle("Fusion")  # estilo cross-Windows

    # Global CSS
    app.setStyleSheet(f"""
    QWidget {{
        background-color: #1e1e1e;
        color: white;
        font-family: Arial;
        font-size: 12px;
    }}

    QLabel {{
        color: white;
        font-size: 13px;
    }}

    QProgressBar {{
        border: 1px solid #555;
        border-radius: 5px;
        background-color: #2e2e2e;
        text-align: center;
        color: white;
    }}

    QProgressBar::chunk {{
        background-color: #4C94D8;
    }}

    QComboBox, QLineEdit {{
        background-color: #2e2e2e;
        color: white;
        border: 1px solid #555;
        padding: 3px;
    }}

    QTextEdit {{
        background-color: #2e2e2e;
        color: white;
    }}
    """)

    # -----------------------
    # Set global icon
    # -----------------------
    icon_path = BASE_DIR / "Axolotl.ico"
    app.setWindowIcon(QtGui.QIcon(str(icon_path)))

    # -----------------------
    # Launch window
    # -----------------------
    window = MainApp()
    window.show()
    sys.exit(app.exec())
