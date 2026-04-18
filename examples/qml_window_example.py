import sys
from PySide6.QtWidgets import QApplication

from .example_windows.example_window import ExampleWindow

def main():
    app = QApplication(sys.argv)
    
    window = ExampleWindow()
    window.show()
    
    sys.exit(app.exec())


main()