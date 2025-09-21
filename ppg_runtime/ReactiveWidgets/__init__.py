from .check_box import ReactiveCheckBox
from .combo_box import ReactiveComboBox
from .label import ReactiveLabel
from .line_edit import ReactiveLineEdit
from .slider import ReactiveSlider
from .spin_box import ReactiveSpinBox
from .text_edit import ReactiveTextEdit

__all__ = [
    "ReactiveCheckBox",
    "ReactiveComboBox",
    "ReactiveLabel",
    "ReactiveLineEdit",
    "ReactiveSlider",
    "ReactiveSpinBox",
    "ReactiveTextEdit",
]

# alias for backward compatibility
CheckBox = ReactiveCheckBox
QCheckBox = ReactiveCheckBox
ComboBox = ReactiveComboBox
QComboBox = ReactiveComboBox
Label = ReactiveLabel
QLabel = ReactiveLabel
LineEdit = ReactiveLineEdit
QLineEdit = ReactiveLineEdit
Slider = ReactiveSlider
QSlider = ReactiveSlider
SpinBox = ReactiveSpinBox
QSpinBox = ReactiveSpinBox
TextEdit = ReactiveTextEdit
QTextEdit = ReactiveTextEdit