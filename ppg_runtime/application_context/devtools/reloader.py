import os
import time
import ast
import inspect
import types
import astor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console

try:
    from PySide6.QtCore import (
        QObject, Signal, QTimer, Qt
    )
    from PySide6.QtWidgets import (
        QLabel, QWidget, QApplication, QPushButton
    )
except ImportError:
    try:
        from PySide2.QtCore import (
            QObject, Signal, QTimer, Qt
        )
        from PySide2.QtWidgets import (
            QLabel, QWidget, QApplication, QPushButton
        )
    except ImportError:
        try:
            from PyQt6.QtCore import (
                QObject, pyqtSignal as Signal, QTimer, Qt
            )
            from PyQt6.QtWidgets import (
                QLabel, QWidget, QApplication, QPushButton
            )
        except ImportError:
            try:
                from PyQt5.QtCore import (
                    QObject, pyqtSignal as Signal, QTimer, Qt
                )
                from PyQt5.QtWidgets import (
                    QLabel, QWidget, QApplication, QPushButton
                )
            except ImportError:
                raise ImportError(
                    "PySide6, PySide2, PyQt6, or PyQt5 not found."
                    "Please install one of them: pip install PySide6 (or PySide2, PyQt6, PyQt5)"
                )

console = Console()


def clear_console():
    """
    Clears the console screen.
    Works on both Windows ('cls') and Unix/Linux/macOS ('clear') systems.
    """
    os.system('cls' if os.name == 'nt' else 'clear')


class ReloadSignaler(QObject):
    reload_requested = Signal()


class ReloadHandler(FileSystemEventHandler):
    """
    Handles file system events and emits a reload signal
    when the monitored file is modified.
    """

    def __init__(self, app_class_instance, target_file):
        self.app_class_instance = app_class_instance
        self.target_file = target_file
        self.last_modified = {}
        console.print(
            f"🔥 [bold green]Hot Reload:[/bold green] Listening for changes in [bold cyan]{os.path.basename(target_file)}[/bold cyan]")

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".py"):
            return

        try:
            if not os.path.samefile(event.src_path, self.target_file):
                return
        except (OSError, FileNotFoundError):
            return

        current_time = time.time()
        last_time = self.last_modified.get(event.src_path, 0)
        if current_time - last_time < 0.5:
            return
        self.last_modified[event.src_path] = current_time

        console.print(
            f"\n🔄 [bold green]Hot Reload:[/bold green] Detected change in '[bold cyan]{os.path.basename(event.src_path)}[/]'")

        if hasattr(self.app_class_instance.__class__, '_hot_reload_signaler') and \
           self.app_class_instance.__class__._hot_reload_signaler:
            self.app_class_instance.__class__._hot_reload_signaler.reload_requested.emit()
        else:
            console.print(
                "❌ [bold red]Hot Reload ERROR:[/bold red] No hot reload signaler available in application class.")


class PPGHotReloadMixin:
    """
    Generic mixin that adds hot reload capabilities (based on AST)
    to any PySide6/PPG class.

    To use it, the class must:
    1. Inherit from PPGHotReloadMixin (using the @hot_reload_app decorator).
    2. Ensure the _init_hot_reload_system() method is called once at the start of the application.
    3. Define a `render_()` method that builds the UI.
    """

    _hot_reload_signaler = None
    _hot_reload_observer = None
    _hot_reload_timer = None
    _hot_reload_count = 0
    hot_reload_source_file = None

    def _init_hot_reload_system(self, source_file: str = None):
        if self.__class__.hot_reload_source_file is not None:
            console.print(
                "⚠️ [bold yellow]Hot Reload:[/bold yellow] Hot reloading is already running. Skipping initialization.", highlight=False)
            return

        if source_file is None:
            frame = inspect.currentframe()
            try:
                caller_frame = frame.f_back
                while caller_frame:
                    filename = caller_frame.f_code.co_filename
                    if not any(f.endswith(os.path.basename(filename)) for f in
                               [__file__, 'ppg_runtime', 'watchdog', 'application_context']):
                        if os.path.exists(filename) and filename.endswith('.py'):
                            source_file = filename
                            break
                    caller_frame = caller_frame.f_back
            finally:
                del frame

        if not source_file or not os.path.exists(source_file):
            console.print(
                "❌ [bold red]Hot Reload ERROR:[/bold red] Could not determine source file. Hot reload disabled.", highlight=False)
            console.print(
                f"    [dim]Attempted detection path: '{source_file}'[/dim]", highlight=False)
            return

        self.__class__.hot_reload_source_file = os.path.abspath(source_file)
        self._setup_hot_reload_signals()
        self._setup_hot_reload_file_watcher()

    def _setup_hot_reload_signals(self):
        if not self.__class__._hot_reload_signaler:
            self.__class__._hot_reload_signaler = ReloadSignaler()
            self.__class__._hot_reload_signaler.reload_requested.connect(
                self._handle_hot_reload_request)

        if not self.__class__._hot_reload_timer:
            self.__class__._hot_reload_timer = QTimer()
            self.__class__._hot_reload_timer.setSingleShot(True)
            self.__class__._hot_reload_timer.timeout.connect(
                self._perform_hot_reload)

    def _setup_hot_reload_file_watcher(self):
        if self.__class__._hot_reload_observer:
            return
        try:
            # Get the directory of the source file
            source_dir = os.path.dirname(self.__class__.hot_reload_source_file)

            event_handler = ReloadHandler(
                self, self.__class__.hot_reload_source_file)

            self.__class__._hot_reload_observer = Observer()

            # Monitor the root folder and all its subfolders.
            self.__class__._hot_reload_observer.schedule(
                event_handler, path=source_dir, recursive=True)

            self.__class__._hot_reload_observer.start()

        except Exception as e:
            console.print(
                f"❌ [bold red]Error setting up file observer for hot reload:[/bold red] {e}")

    def _handle_hot_reload_request(self):
        self.__class__._hot_reload_count += 1
        if self.__class__._hot_reload_timer:
            self.__class__._hot_reload_timer.start(500)

    def _perform_hot_reload(self):
        clear_console()
        console.print(
            f"\n🔄 [bold green]Hot Reload:[/bold green] Detected change in '[bold cyan]{self.__class__.hot_reload_source_file}[/bold cyan]'.")
        console.print(
            f"⚡️ [bold green]Hot Reload:[/bold green] Processing changes... [bold cyan](Reload #{self.__class__._hot_reload_count})[/bold cyan]")

        try:
            with open(self.__class__.hot_reload_source_file, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)
            class_name = self.__class__.__name__
            class_node = None
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    class_node = node
                    break

            if not class_node:
                raise RuntimeError(
                    f"Class '{class_name}' not found in '{self.__class__.hot_reload_source_file}'.")

            original_module = inspect.getmodule(self)
            local_ns = dict(original_module.__dict__)
            local_ns.update(globals())
            local_ns['self'] = self

            # Re-execute all import statements from the source file
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_code = astor.to_source(node)
                    exec(import_code, local_ns, local_ns)

            # Rebuild class and replace all methods
            for item in class_node.body:
                if isinstance(item, ast.FunctionDef):
                    method_code = astor.to_source(item)
                    exec(method_code, local_ns, local_ns)

                    if item.name in local_ns:
                        new_method = types.MethodType(
                            local_ns[item.name], self)
                        setattr(self, item.name, new_method)

            if not hasattr(self, 'render_'):
                raise RuntimeError(
                    f"render_() method not found in class '{class_name}'.")

            self._clear_hot_reloaded_widgets()

            # We use QTimer.singleShot to schedule the rendering in the next cycle of the event loop.
            # This prevents the "Internal C++ object already deleted" error.
            QTimer.singleShot(0, self._process_post_render_updates)

            console.print(
                f"✨ [bold green]Hot Reload:[/bold green] Done. UI will update shortly.", highlight=False)

        except Exception as e:
            console.print(
                f"❌ [bold red]Hot Reload Error: UI can't be reloaded ->[/bold red] {str(e)}", highlight=False)
            import traceback
            traceback.print_exc()
            self._show_hot_reload_error(str(e))

    def _process_post_render_updates(self):
        """
            Contains the rendering and UI update actions,
            scheduled to run after the initial hot reload
            has cleared the old widgets.
        """
        try:
            #self.component_will_mount() # Removed: should only be called during initial mount
            self._trigger_render()
            self._ensure_children_visibility()
            self.adjustSize()
            self.update()
            self.repaint()

            # Security check before attempting to hide the label
            if hasattr(self, '_hot_reload_error_label'):
                try:
                    if self._hot_reload_error_label.parent() is not None:
                        self._hot_reload_error_label.hide()
                except RuntimeError:
                    # C++ Object already deleted, ignore it
                    pass
        except Exception as e:
            console.print(
                f"❌ [bold red]Hot Reload Error: UI can't be reloaded ->[/bold red] {str(e)}", highlight=False)
            import traceback
            traceback.print_exc()
            self._show_hot_reload_error(str(e))


    def _clear_hot_reloaded_widgets(self):
        widgets_to_delete = []
        for child_obj in self.children():
            if isinstance(child_obj, QWidget):
                is_error_label = hasattr(self, '_hot_reload_error_label') and child_obj is self._hot_reload_error_label
                if child_obj is not self and not is_error_label:
                    widgets_to_delete.append(child_obj)

        for widget in widgets_to_delete:
            try:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
            except Exception as e:
                console.print(
                    f"[bold yellow]Hot Reload:[/bold yellow] ⚠️ WARNING: Failed to delete widget [bold cyan]{type(widget).__name__}[/bold cyan]: [red]{str(e)}[/red]", highlight=False)
        QApplication.processEvents()

    def _ensure_children_visibility(self):
        """
        Ensures that all direct child QWidgets of this window
        are visible, if they are not already. This is useful
        for refreshing the UI after a hot reload without forcing
        `show()` on each widget.
        """

        for child_obj in self.children():
            if isinstance(child_obj, QWidget):
                # Avoid calling show() on the window itself or the error label if it's already managed
                if child_obj != self and \
                   (not hasattr(self, '_hot_reload_error_label') or child_obj != self._hot_reload_error_label):
                    if not child_obj.isVisible():
                        child_obj.show()
                        # If using absolute positioning, `raise_()` can also help
                        # ensure the widget is at the top of the stacking order.
                        child_obj.raise_()

    def _show_hot_reload_error(self, message):
        # This is the most important part. If the label object has already been deleted,
        # create it again to avoid the RuntimeError.
        is_deleted = False
        if hasattr(self, '_hot_reload_error_label'):
            try:
                # Check if the widget still has a valid parent, if not, it's deleted
                if self._hot_reload_error_label.parent() is None:
                    is_deleted = True
            except RuntimeError:
                is_deleted = True

        if not hasattr(self, '_hot_reload_error_label') or is_deleted:
            self._hot_reload_error_label = QLabel(self)
            self._hot_reload_error_label.setGeometry(
                50, self.height() - 120, self.width() - 100, 100)
            self._hot_reload_error_label.setStyleSheet(
                "color: tomato; font-weight: bold; background-color: #fff; padding: 10px; border: 2px solid tomato; border-radius: 5px;")
            self._hot_reload_error_label.setWordWrap(True)
            self._hot_reload_error_label.setAttribute(
                Qt.WA_DeleteOnClose, False)

        self._hot_reload_error_label.raise_()
        self._hot_reload_error_label.setText(
            f"❌ Hot Reload Error:\n{message}")
        self._hot_reload_error_label.show()


    def cleanup_hot_reload_resources(self):
        try:
            if self.__class__._hot_reload_observer:
                self.__class__._hot_reload_observer.stop()
                self.__class__._hot_reload_observer.join(timeout=1)
                self.__class__._hot_reload_observer = None

        except Exception as e:
            console.print(
                f"⚠️ [bold yellow]Hot Reload:[/bold yellow] Warning stopping file observer: {e}", highlight=False)

        try:
            if self.__class__._hot_reload_timer and self.__class__._hot_reload_timer.isActive():
                self.__class__._hot_reload_timer.stop()
                console.print(
                    "🕒 [bold yellow]Hot Reload:[/bold yellow] Debounce timer stopped.", highlight=False)
        except Exception as e:
            console.print(
                f"⚠️ [bold yellow]Hot Reload:[/bold yellow] Warning stopping debounce timer: {e}", highlight=False)

    def closeEvent(self, event):
        self.cleanup_hot_reload_resources()
        super().closeEvent(event)
        event.accept()


def hot_reloading(cls):
    if PPGHotReloadMixin not in cls.__bases__:
        cls.__bases__ = (PPGHotReloadMixin,) + cls.__bases__

    setattr(cls, '_hot_reload_signaler', None)
    setattr(cls, '_hot_reload_observer', None)
    setattr(cls, '_hot_reload_timer', None)
    setattr(cls, '_hot_reload_count', 0)
    setattr(cls, 'hot_reload_source_file', None)

    return cls
