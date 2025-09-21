import sys
from ppg_runtime.application_context.PySide6 import ApplicationContext
from ppg_runtime.application_context import PPGLifeCycle, Pydux, init_lifecycle, BridgeManager
from ppg_runtime.application_context.devtools.reloader import hot_reloading
from ppg_runtime.application_context.utils import app_is_frozen
from PySide6.QtWidgets import QMainWindow, QPushButton
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage

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
class Pwa(QMainWindow, PPGLifeCycle, Pydux):
    def component_will_mount(self):
        self.subscribe_to_store(self)

    def render_(self):

        # loads the embedded browser engine (WebEngineView) where the PWA will be displayed (index.html)
        self.engine = QWebEngineView(self)
        self.engine.load(QUrl.fromLocalFile(self.get_resource("index.html")))


        # Create a bridge for Python ↔ JavaScript communication using QWebChannel
        # You can create multiple bridges if needed by instantiating BridgeManager with different names
        self.bridge = BridgeManager(self.engine, "bridge")

        # Register an event called "callback"
        # When triggered from JS, it will call handle_callback() in Python
        self.bridge.register("callback", self.handle_callback)


        # Add buttons to demonstrate functionality (e.g., opening DevTools, emitting events to JS)
        self.button = QPushButton("Open DevTools", self, clicked=self.open_dev_tools)
        self.button2 = QPushButton("test emit", self, clicked=lambda: self.bridge.emit("callback", {"data": "Hello from Python!"}))

        self.setCentralWidget(self.engine)

    def handle_callback(self, payload):
        """This is a callback function that handles messages from JavaScript via the bridge.

        Args:
            payload (dict): The payload data sent from JavaScript.

        Returns:
            str: A response message indicating the result of the callback handling.
        """

        print("Received message from JS:", payload)

        # You can send back a response to JavaScript if needed by returning a value
        return f"USER: {payload['username']} logged in successfully! (handled by Python)"

    def open_dev_tools(self):
        """Opens the DevTools window for the embedded web engine."""

        self.dev_tools = QWebEngineView(self)
        if not self.engine.page().devToolsPage():
            self.engine.page().setDevToolsPage(QWebEnginePage(self.engine.page().profile(), self.dev_tools))
        self.dev_tools.setPage(self.engine.page().devToolsPage())
        self.dev_tools.setWindowTitle("DevTools")
        self.dev_tools.show()
        self.dev_tools.resize(500, self.height())
        self.dev_tools.move(self.width() - 500, 0)


        # Emit an event to JavaScript indicating that DevTools has been opened (for demonstration purposes)
        self.bridge.emit("devtools_opened", {"message": "DevTools opened"})

    def responsive_UI(self):
        self.setMinimumSize(640, 480)
        self.button2.move(100, 0)


if __name__ == '__main__':
    appctxt = ApplicationContext()
    window = Pwa()
    if not app_is_frozen():
        window._init_hot_reload_system(__file__)
    window.show()
    exec_func = getattr(appctxt.app, 'exec', appctxt.app.exec_)
    sys.exit(exec_func())