import sys
from ppg_runtime.application_context.PySide6 import ApplicationContext
from ppg_runtime.application_context import PPGLifeCycle, Pydux, init_lifecycle
from ppg_runtime.application_context.devtools.reloader import hot_reloading
from ppg_runtime.application_context.utils import app_is_frozen
from PySide6.QtWidgets import QMainWindow, QStackedWidget
from views.Home import Home
from views.AuthScreen import AuthScreen

# --------------------------------------------------------------------------------------
# Important! Production Considerations for Hot Reloading
# --------------------------------------------------------------------------------------
# Hot reloading is a development tool that allows you to instantly see UI changes
# when you save a file. It's extremely useful for rapid prototyping and designing
# interfaces.
#
# However, this functionality is not designed for use in production environments.
# For the final version of your application, it is highly recommended to remove
# the code related to hot reloading, such as the `@hot_reloading` decorator
# and the `window._init_hot_reload_system(__file__)` call.
#
# Keeping hot reloading active in production can negatively impact the application's
# performance, stability, and security.
# --------------------------------------------------------------------------------------

@init_lifecycle
@hot_reloading
class Multiscreensdemo(QMainWindow, PPGLifeCycle, Pydux):
    def component_will_mount(self):
        self.subscribe_to_store(self)
        self.set_schema({
            "current_screen_index": int
        })

    def render_(self):
        self.layout = QStackedWidget()

        for screen in (AuthScreen, Home):
            self.layout.addWidget(screen())

        self.setCentralWidget(self.layout)

    def responsive_UI(self):
        self.setMinimumSize(640, 480)

    def on_store_change(self, _):
        self.layout.setCurrentIndex(self.store['current_screen_index'])


if __name__ == '__main__':
    appctxt = ApplicationContext()
    window = Multiscreensdemo()
    if not app_is_frozen():
        window._init_hot_reload_system(__file__)
    window.show()
    exec_func = getattr(appctxt.app, 'exec', appctxt.app.exec_)
    sys.exit(exec_func())