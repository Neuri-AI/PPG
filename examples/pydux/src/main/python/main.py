import sys
from ppg_runtime.application_context.PySide6 import ApplicationContext
from ppg_runtime.application_context import PPGLifeCycle, Pydux, init_lifecycle
from ppg_runtime.application_context.devtools.reloader import hot_reloading
from ppg_runtime.application_context.utils import app_is_frozen
from PySide6.QtWidgets import QMainWindow, QTextEdit, QLabel


@init_lifecycle
@hot_reloading
class Pydux(QMainWindow, PPGLifeCycle, Pydux):
    def component_will_mount(self):
        self.subscribe_to_store(self)
        self.set_schema({
            "greeting": str
        })

    def render_(self):
        self.label = QLabel('Hello World!', self)
        self.line = QTextEdit(self, placeholderText='Type something...', textChanged=lambda: self.on_text_changed(self.line.toPlainText()))

    def on_text_changed(self, text):
        self.update_store({"greeting": text})

    def responsive_UI(self):
        self.setMinimumSize(640, 480)
        self.label.move(20, 20)
        self.line.setGeometry(20, 120, 600, 300)

    def on_store_change(self, _):
        self.label.setText(self.store.get("greeting", ""))
        self.label.adjustSize()


if __name__ == '__main__':
    appctxt = ApplicationContext()
    window = Pydux()
    if not app_is_frozen():
        window._init_hot_reload_system(__file__)
    window.show()
    exec_func = getattr(appctxt.app, 'exec', appctxt.app.exec_)
    sys.exit(exec_func())