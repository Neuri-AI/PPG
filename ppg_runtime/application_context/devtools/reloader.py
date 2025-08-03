
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
    # PySide6
    from PySide6.QtCore import (
        QObject, Signal, Slot, QTimer, Qt, QRect, QUrl, QSize, QPoint, QSizeF, QPointF
    )
    from PySide6.QtWidgets import (
        QLabel, QPushButton, QWidget, QApplication, QVBoxLayout, QHBoxLayout, QMainWindow,
        QLineEdit, QTextEdit, QPlainTextEdit,  # Added QPlainTextEdit
        QCheckBox, QRadioButton, QComboBox, QSlider, QProgressBar,
        QTabWidget, QGroupBox, QFrame, QScrollArea, QSplitter,
        QMenuBar, QMenu, QStatusBar, QToolBar, QToolButton,  # Added QToolButton
        QTableWidget, QTableWidgetItem, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
        QDialog, QMessageBox, QFileDialog, QFontDialog, QColorDialog,
        QWizard, QWizardPage,  # Added QWizard, QWizardPage
        # Added calendar/date/time, spinbox, dial
        QCalendarWidget, QDial, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit,
        QMdiArea, QMdiSubWindow,  # Added MDI
        QToolBox,  # Added QToolBox
        QGridLayout, QFormLayout, QStackedWidget,
        QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem
    )
    from PySide6.QtGui import (
        QFont, QColor, QPen, QBrush, QIcon, QPixmap, QImage, QPainter,
        # Added Graphics Item Types
    )
    from PySide6.QtWebChannel import QWebChannel
    from PySide6.QtWebEngineWidgets import (
        QWebEngineView
    )

    _QMainWindow = QMainWindow
    _Qt = Qt  # Alias for consistent Qt enum access

except ImportError:
    try:
        # PySide2
        from PySide2.QtCore import (
            QObject, Signal, Slot, QTimer, Qt, QRect, QUrl, QSize, QPoint, QSizeF, QPointF
        )
        from PySide2.QtWidgets import (
            QLabel, QPushButton, QWidget, QApplication, QVBoxLayout, QHBoxLayout, QMainWindow,
            QLineEdit, QTextEdit, QPlainTextEdit,
            QCheckBox, QRadioButton, QComboBox, QSlider, QProgressBar,
            QTabWidget, QGroupBox, QFrame, QScrollArea, QSplitter,
            QMenuBar, QMenu, QStatusBar, QToolBar, QToolButton,
            QTableWidget, QTableWidgetItem, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
            QDialog, QMessageBox, QFileDialog, QFontDialog, QColorDialog,
            QWizard, QWizardPage,
            QCalendarWidget, QDial, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit,
            QMdiArea, QMdiSubWindow,
            QToolBox,
            QGridLayout, QFormLayout, QStackedWidget,
            QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem
        )
        from PySide2.QtGui import (
            QFont, QColor, QPen, QBrush, QIcon, QPixmap, QImage, QPainter
        )
        from PySide2.QtWebChannel import QWebChannel
        from PySide2.QtWebEngineWidgets import (
            QWebEngineView
        )

        _QMainWindow = QMainWindow
        _Qt = Qt

    except ImportError:
        try:
            # PyQt6
            # Note: PyQt6 often moves some classes (like QAction) to QtGui.
            # QGraphicsItem types and QAction are in QtGui for PyQt6.
            from PyQt6.QtCore import (
                QObject, pyqtSignal as Signal, pyqtSlot as Slot, QTimer, Qt, QRect, QUrl, QSize, QPoint, QSizeF, QPointF
            )
            from PyQt6.QtWidgets import (
                QLabel, QPushButton, QWidget, QApplication, QVBoxLayout, QHBoxLayout,
                QMainWindow, QLineEdit, QTextEdit, QPlainTextEdit,
                QCheckBox, QRadioButton, QComboBox, QSlider, QProgressBar,
                QTabWidget, QGroupBox, QFrame, QScrollArea, QSplitter,
                QMenuBar, QMenu, QStatusBar, QToolBar, QToolButton,
                QTableWidget, QTableWidgetItem, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
                QDialog, QMessageBox, QFileDialog, QFontDialog, QColorDialog,
                QWizard, QWizardPage,
                QCalendarWidget, QDial, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit,
                QMdiArea, QMdiSubWindow,
                QToolBox,
                QGridLayout, QFormLayout, QStackedWidget,
                # Basic items might be here
                QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem
            )
            from PyQt6.QtGui import (  # Additional classes commonly found in QtGui for PyQt6
                # QAction here for PyQt6
                QFont, QColor, QPen, QBrush, QIcon, QPixmap, QImage, QPainter,
                # Ensure these are correct for PyQt6

            )
            from PyQt6.QtWebChannel import QWebChannel
            from PyQt6.QtWebEngineWidgets import (
                QWebEngineView
            )

            _QMainWindow = QMainWindow
            _Qt = Qt  # Alias for consistent Qt enum access

        except ImportError:
            try:
                # PyQt5
                from PyQt5.QtCore import (
                    QObject, pyqtSignal as Signal, pyqtSlot as Slot, QTimer, Qt, QRect, QUrl, QSize, QPoint, QSizeF, QPointF
                )
                from PyQt5.QtWidgets import (
                    QLabel, QPushButton, QWidget, QApplication, QVBoxLayout, QHBoxLayout, QMainWindow,
                    QLineEdit, QTextEdit, QPlainTextEdit,
                    QCheckBox, QRadioButton, QComboBox, QSlider, QProgressBar,
                    QTabWidget, QGroupBox, QFrame, QScrollArea, QSplitter,
                    QMenuBar, QMenu,  QStatusBar, QToolBar, QToolButton,
                    QTableWidget, QTableWidgetItem, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
                    QDialog, QMessageBox, QFileDialog, QFontDialog, QColorDialog,
                    QWizard, QWizardPage,
                    QCalendarWidget, QDial, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit,
                    QMdiArea, QMdiSubWindow,
                    QToolBox,
                    QGridLayout, QFormLayout, QStackedWidget,
                    QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsTextItem
                )
                from PyQt5.QtGui import (
                    QFont, QColor, QPen, QBrush, QIcon, QPixmap, QImage, QPainter                )
                from PyQt5.QtWebChannel import QWebChannel
                from PyQt5.QtWebEngineWidgets import (
                    QWebEngineView
                )

                _QMainWindow = QMainWindow
                _Qt = Qt

            except ImportError:
                raise ImportError(
                    "No se encontró PySide6, PySide2, PyQt6 ni PyQt5 instalado."
                    "Por favor, instala uno de estos: pip install PySide6 (o PySide2, PyQt6, PyQt5)"
                )
console = Console()


def clear_console():
    """
    Limpia la pantalla de la consola.
    Funciona tanto en Windows ('cls') como en sistemas Unix/Linux/macOS ('clear').
    """
    os.system('cls' if os.name == 'nt' else 'clear')


class ReloadSignaler(QObject):
    """Señal personalizada para emitir solicitudes de recarga de la UI."""
    reload_requested = Signal()


class ReloadHandler(FileSystemEventHandler):
    """
    Maneja eventos del sistema de archivos y emite una señal de recarga
    cuando el archivo monitoreado es modificado.
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
    Mixin genérico que añade capacidades de hot reload (basado en AST)
    a cualquier clase PySide6/PPG.

    Para usarlo, la clase debe:
    1. Heredar de PPGHotReloadMixin (usando el decorador @hot_reload_app).
    2. Asegurarse de que el método _init_hot_reload_system() se llame una vez
       al inicio de la aplicación.
    3. Definir un método `render_()` que construya la UI.
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
            folder = os.path.dirname(self.__class__.hot_reload_source_file)
            event_handler = ReloadHandler(
                self, self.__class__.hot_reload_source_file)

            self.__class__._hot_reload_observer = Observer()
            self.__class__._hot_reload_observer.schedule(
                event_handler, path=folder, recursive=False)
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
                    f"No se encontró la clase '{class_name}' en el archivo fuente.")

            render_func_node = None
            for item in class_node.body:
                if isinstance(item, ast.FunctionDef) and item.name == 'render_':
                    render_func_node = item
                    break

            if not render_func_node:
                raise RuntimeError(
                    f"No se encontró el método 'render_()' en la clase '{class_name}'.")

            render_code = astor.to_source(render_func_node)

            local_ns = {
                # QtWidgets (Common Widgets & Layouts)
                'QLabel': QLabel,
                'QPushButton': QPushButton,
                'QWidget': QWidget,
                'QApplication': QApplication,
                'QVBoxLayout': QVBoxLayout,
                'QHBoxLayout': QHBoxLayout,
                'QMainWindow': QMainWindow,
                'QLineEdit': QLineEdit,
                'QTextEdit': QTextEdit,
                'QPlainTextEdit': QPlainTextEdit,
                'QCheckBox': QCheckBox,
                'QRadioButton': QRadioButton,
                'QComboBox': QComboBox,
                'QSlider': QSlider,
                'QProgressBar': QProgressBar,
                'QTabWidget': QTabWidget,
                'QGroupBox': QGroupBox,
                'QFrame': QFrame,
                'QScrollArea': QScrollArea,
                'QSplitter': QSplitter,
                'QMenuBar': QMenuBar,
                'QMenu': QMenu,
                'QStatusBar': QStatusBar,
                'QToolBar': QToolBar,
                'QToolButton': QToolButton,
                'QTableWidget': QTableWidget,
                'QTableWidgetItem': QTableWidgetItem,
                'QListWidget': QListWidget,
                'QListWidgetItem': QListWidgetItem,
                'QTreeWidget': QTreeWidget,
                'QTreeWidgetItem': QTreeWidgetItem,
                'QDialog': QDialog,
                'QMessageBox': QMessageBox,
                'QFileDialog': QFileDialog,
                'QFontDialog': QFontDialog,
                'QColorDialog': QColorDialog,
                'QWizard': QWizard,
                'QWizardPage': QWizardPage,
                'QCalendarWidget': QCalendarWidget,
                'QDial': QDial,
                'QSpinBox': QSpinBox,
                'QDoubleSpinBox': QDoubleSpinBox,
                'QDateEdit': QDateEdit,
                'QTimeEdit': QTimeEdit,
                'QDateTimeEdit': QDateTimeEdit,
                'QMdiArea': QMdiArea,
                'QMdiSubWindow': QMdiSubWindow,
                'QToolBox': QToolBox,

                # Layouts
                'QGridLayout': QGridLayout,
                'QFormLayout': QFormLayout,
                'QStackedWidget': QStackedWidget,

                # Graphics View Framework
                'QGraphicsView': QGraphicsView,
                'QGraphicsScene': QGraphicsScene,
                'QGraphicsRectItem': QGraphicsRectItem,
                'QGraphicsEllipseItem': QGraphicsEllipseItem,
                'QGraphicsTextItem': QGraphicsTextItem,

                # QtCore (Basic Data Types & Utilities)
                'QObject': QObject,
                'Signal': Signal,
                'Slot': Slot,
                'QTimer': QTimer,
                'Qt': _Qt,
                'QRect': QRect,
                'QUrl': QUrl,
                'QSize': QSize,
                'QPoint': QPoint,
                'QSizeF': QSizeF,
                'QPointF': QPointF,

                # QtGui (Graphics & Painting)
                'QFont': QFont,
                'QColor': QColor,
                'QPen': QPen,
                'QBrush': QBrush,
                'QIcon': QIcon,
                'QPixmap': QPixmap,
                'QImage': QImage,
                'QPainter': QPainter,

                # QtWebEngineWidgets
                'QWebEngineView': QWebEngineView
            }
            exec(render_code, globals(), local_ns)

            if 'render_' not in local_ns:
                raise RuntimeError(
                    "El código del método 'render_()' no pudo ser compilado o encontrado.")

            new_render_method = types.MethodType(local_ns['render_'], self)
            self.render_ = new_render_method

            self._clear_hot_reloaded_widgets()

            QApplication.processEvents()

            # Llama al nuevo método render_() para recrear los widgets.
            self.render_()

            # --- NUEVO PASO: Asegurar la visibilidad de todos los nuevos widgets hijos ---
            self._ensure_children_visibility()
            # --- FIN NUEVO PASO ---

            self.adjustSize()
            self.update()
            self.repaint()

            if hasattr(self, '_hot_reload_error_label'):
                self._hot_reload_error_label.hide()

            console.print(
                f"✨ [bold green]Hot Reload:[/bold green] Done.", highlight=False)

        except Exception as e:
            console.print(
                f"❌ [bold red]Hot Reload Error: UI can't be reloaded ->[/bold red] {str(e)}", highlight=False)
            import traceback
            traceback.print_exc()
            self._show_hot_reload_error(str(e))

    def _clear_hot_reloaded_widgets(self):
        deleted_count = 0

        widgets_to_delete = []
        for child_obj in self.children():
            if isinstance(child_obj, QWidget):
                if child_obj != self and \
                   (not hasattr(self, '_hot_reload_error_label') or child_obj != self._hot_reload_error_label):
                    widgets_to_delete.append(child_obj)

        for widget in widgets_to_delete:
            try:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
                deleted_count += 1
            except Exception as e:
                console.print(
                    f"[bold yellow]Hot Reload:[/bold yellow] ⚠️ WARNING: Failed to delete widget [bold cyan]{type(widget).__name__}[/bold cyan]: [red]{str(e)}[/red]", highlight=False)

        QApplication.processEvents()

    def _ensure_children_visibility(self):
        """
        Asegura que todos los QWidgets hijos directos de esta ventana
        estén visibles, si no lo están ya. Esto es útil para refrescar
        la UI después de un hot reload sin forzar `show()` en cada widget.
        """

        for child_obj in self.children():
            if isinstance(child_obj, QWidget):
                # Evita llamar show() en la propia ventana o la etiqueta de error si ya está gestionada
                if child_obj != self and \
                   (not hasattr(self, '_hot_reload_error_label') or child_obj != self._hot_reload_error_label):
                    if not child_obj.isVisible():
                        child_obj.show()
                        # Si estás usando posicionamiento absoluto, `raise_()` también puede ayudar
                        # a asegurar que el widget esté en la parte superior del orden de apilamiento.
                        child_obj.raise_()

    def _show_hot_reload_error(self, message):
        if not hasattr(self, '_hot_reload_error_label'):
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
