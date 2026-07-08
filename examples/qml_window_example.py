import os
import sys

# Ensure src/ is on the path for unity_animation_player imports
_src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if _src_path not in sys.path:
    sys.path.insert(0, os.path.abspath(_src_path))

# Ensure examples/ is on the path when running directly
_examples_dir = os.path.dirname(os.path.abspath(__file__))
if _examples_dir not in sys.path:
    sys.path.insert(0, _examples_dir)

from PySide6.QtWidgets import QApplication
from qml_window_example_windows.ball_window import ExampleWindow


def main():
    app = QApplication(sys.argv)
    
    window = ExampleWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()