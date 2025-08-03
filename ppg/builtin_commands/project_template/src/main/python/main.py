import sys
from ppg_runtime.application_context.${python_bindings} import ApplicationContext
from ppg_runtime.application_context import Pydux, PPGLifeCycle, init_lifecycle
from ${python_bindings}.QtWidgets import QMainWindow, QLabel

@init_lifecycle
class ${app_name}(QMainWindow, PPGLifeCycle, Pydux):
    def component_will_mount(self):
        self.subscribe_to_store(self)

    def render_(self):
       QLabel('Hello World!', parent=self)

    def responsive_UI(self):
        self.setMinimumSize(640, 480)


if __name__ == '__main__':
    appctxt = ApplicationContext()
    window = ${app_name}()
    window.show()
    # This fixes the issue with PySide2 that the exec function is not found
    exec_func = getattr(appctxt.app, 'exec', appctxt.app.exec_)
    sys.exit(exec_func())