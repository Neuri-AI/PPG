import warnings
import json
import traceback
from collections import namedtuple
from ppg_runtime import _state, _frozen, _source
from ppg_runtime._resources import ResourceLocator
from ppg_runtime._signal import SignalWakeupHandler
from ppg_runtime.excepthook import _Excepthook, StderrExceptionHandler
from ppg_runtime.platform import is_windows, is_mac
from ppg_runtime.application_context.utils import app_is_frozen as is_frozen
from functools import lru_cache
from pydantic import BaseModel, create_model, ValidationError, Field
from typing import Dict, Type, Any, Optional, Union, get_origin, get_args
from rich.console import Console

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

console = Console()

try:
    # PySide6
    from PySide6.QtCore import QObject, Signal, Slot, QTimer, Qt, QRect, QUrl, QTimer
    from PySide6.QtWidgets import QLabel, QPushButton, QWidget, QApplication, QVBoxLayout, QHBoxLayout, QMainWindow
    from PySide6.QtWebChannel import QWebChannel
    from PySide6.QtWebEngineWidgets import QWebEngineView

    # Alias para QMainWindow si tu código la usa directamente desde QtWidgets
    _QMainWindow = QMainWindow
    # Para PySide6, los enums suelen ser de acceso directo (sin ámbito)
    # No es necesario un alias especial para Qt a menos que lo quieras
    _Qt = Qt

except ImportError:
    try:

        from PySide2.QtCore import QObject, Signal, Slot, Qt, QTimer
        from PySide2.QtWidgets import QMainWindow, QApplication, QWidget
        from PySide2.QtWebChannel import QWebChannel

        _QMainWindow = QMainWindow
        _Qt = Qt

    except ImportError:
        try:

            from PyQt6.QtCore import QObject, pyqtSignal as Signal, pyqtSlot as Slot, Qt, QTimer

            from PyQt6.QtWidgets import QMainWindow, QApplication, QWidget
            from PyQt6.QtWebChannel import QWebChannel

            _QMainWindow = QMainWindow
            _Qt = Qt

        except ImportError:
            try:

                from PyQt5.QtCore import QObject, pyqtSignal as Signal, pyqtSlot as Slot, Qt, QTimer
                from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget
                from PyQt5.QtWebChannel import QWebChannel

                _QMainWindow = QMainWindow
                _Qt = Qt

            except ImportError:
                raise ImportError(
                    "No PySide6, PySide2, PyQt6, or PyQt5 installation found."
                    "Please install one of these: pip install PySide6 (or PySide2, PyQt6, PyQt5)"
                )


def init_lifecycle(cls):
    def __init__(self, *args, **kwargs):
        super(cls, self).__init__(*args, **kwargs)
        self.component_will_mount()
        self.allow_bg()
        self.render_()
        self.component_did_mount()
        self.set_CSS()
        self.responsive_UI()

    cls.__init__ = __init__
    return cls


def cached_property(getter):
    """
    A cached Python @property. You use it in conjunction with ApplicationContext
    below to instantiate the components that comprise your application. For more
    information, please consult the Manual:
        https://build-system.fman.io/manual/#cached_property
    """
    return property(lru_cache()(getter))


class WebEngineBridge(QObject):
    bridge = Signal(str)

    def __init__(self):
        super().__init__()
        self.handlers = {}

    def register_handler(self, event_name, func):
        self.handlers[event_name] = func

    @Slot(str, result=str)
    def send(self, message_json):
        try:
            message = json.loads(message_json)
            event = message.get("event")
            payload = message.get("payload")
            if event in self.handlers:
                result = self.handlers[event](payload)
                response = {"success": True, "data": result}
            else:
                response = {"success": False,
                            "error": f"Handler for event '{event}' not found."}
        except Exception:
            response = {
                "success": False,
                "error": traceback.format_exc()
            }
        return json.dumps(response)

    def emit_to_ui(self, event, payload):
        """Emit an event to the UI with the given payload.

        Args:
            event (str): event name to emit
            payload (Any): event payload
        """
        message = json.dumps({"event": event, "payload": payload})
        self.bridge.emit(message)


class BridgeManager:
    _instances = []

    def __init__(self, webview, channel_name="bridge"):
        self.webview = webview
        self.bridge = WebEngineBridge()

        self.channel = QWebChannel()
        self.channel.registerObject(channel_name, self.bridge)
        self.webview.page().setWebChannel(self.channel)

        BridgeManager._instances.append(self)

    def register(self, event, func):
        self.bridge.register_handler(event, func)

    def unregister(self, event):
        """Unregisters an event handler."""
        if event in self.bridge.handlers:
            del self.bridge.handlers[event]

    def emit(self, event, payload):
        """Sends an event only to current instance's UI."""
        self.bridge.emit_to_ui(event, payload)

    @classmethod
    def emit_all(cls, event, payload):
        """Sends an event to all instances of BridgeManager."""
        for instance in cls._instances:
            instance.bridge.emit_to_ui(event, payload)

    def close(self):
        """Closes the bridge and removes it from the instances list."""
        self.webview.page().setWebChannel(None)
        BridgeManager._instances.remove(self)


class ReactiveStoreDict(dict):
    """
    A reactive dictionary that automatically notifies dependent widgets of changes.

    This class extends Python's built-in `dict` to add reactivity. It keeps track of which
    widgets or components are 'listening' to specific keys. When a value is updated,
    it only notifies the widgets that depend on that particular key,
    optimizing the update process.

    Attributes:
        _deps (dict): A dictionary where keys are the store's keys and values are
                      sets of widgets dependent on those keys.
        _component (Any): A reference to the parent component that contains this store.
        _tracking_widget (Any): The widget currently accessing a key; used to register
                                dependencies.
        _base_model (BaseModel): The underlying Pydantic model for data validation.
    """

    def __init__(self, base_model, parent_component):
        """
        Initializes the ReactiveStoreDict.

        Args:
            base_model: The base Pydantic model used for data validation.
            parent_component: The component containing this store, used for context.
        """
        super().__init__(base_model.model_dump())
        self._deps = {}
        self._component = parent_component
        self._tracking_widget = None
        self._base_model = base_model

    def __getitem__(self, key):
        """
        Retrieves an item from the dictionary.

        If a widget is currently being tracked (i.e., it's in the process of being rendered
        and needs to track its dependencies), this method registers it as a dependent
        of the accessed key.
        """
        if self._tracking_widget:
            self._deps.setdefault(key, set()).add(self._tracking_widget)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        """
        Sets a new value for a key in the dictionary.

        This method updates both the internal dictionary and the underlying Pydantic model.
        After the update, it calls `notify_key` to trigger updates for all dependent widgets.
        """
        super().__setitem__(key, value)
        self._base_model = self._base_model.model_copy(update={key: value})
        self.notify_key(key)

    def track(self, widget):
        """
        Sets the current tracking widget.

        This method is called by a component's rendering logic to indicate that the
        given widget is about to access store keys and should be registered as a
        dependent of any keys it reads.

        Args:
            widget: The widget to be tracked for dependencies.
        """
        self._tracking_widget = widget
        return self

    def notify_key(self, key):
        """
        Notifies all widgets dependent on a specific key about a change.

        This method iterates through the set of widgets registered for the given key
        and triggers their update method (`_update_from_store`), ensuring that only
        the relevant parts of the UI are refreshed.

        Args:
            key: The key that has been updated.
        """
        if key not in self._deps:
            return
        for widget in self._deps[key]:
            if hasattr(widget, "_update_from_store"):
                widget._update_from_store(key)


class Pydux:
    _instance = None
    _store = None
    _observers = []
    _schema = None

    def __new__(cls, *args, **kwargs):
        """
        Create a new instance of the class. If the class is Pydux, it will create a singleton instance.
        If the class is a subclass of Pydux, it will create a normal instance but use the shared store.

        Args:
            cls: The class to create an instance of.
            *args: Positional arguments to pass to the class constructor.
        """
        if cls is Pydux:
            if not cls._instance:
                cls._instance = super(Pydux, cls).__new__(cls, *args, **kwargs)
            return cls._instance
        else:
            # For subclasses, create a new instance but share the store
            return super(Pydux, cls).__new__(cls, *args, **kwargs)

    def _default_for_type(self, typ):
        """
            Gets a default value for a given type.
            For BaseModel, it returns the class itself to use as a factory.
        """
        if typ == int:
            return 0
        if typ == str:
            return ""
        if typ == bool:
            return True
        if typ == dict or get_origin(typ) == dict:
            return {}
        if typ == list or get_origin(typ) == list:
            return []
        if typ == float:
            return 0.0
        if typ == Any:
            return None
        if get_origin(typ) == Optional:
            inner_type = get_args(typ)[0]
            return self._default_for_type(inner_type)
        if get_origin(typ) == Union:
            first_type = get_args(typ)[0]
            return self._default_for_type(first_type)
        if isinstance(typ, type) and issubclass(typ, BaseModel):
            # Return the class itself to use as default_factory
            return typ
        return None

    def set_schema(self, schema_dict: Dict[str, Type]) -> None:
        """
        Receives a dictionary {"field": type} and creates a dynamic Pydantic model.

        Args:
            schema_dict (Dict[str, Type]): Dictionary with field names and their types.
        """
        if Pydux._schema is not None:
            console.print(
                f"\n\n⚠️ [bold yellow]WARNING[/bold yellow]: Schema already set. This will reset the store.\n\n", highlight=False)

        fields = {}
        for key, typ in schema_dict.items():
            # For BaseModel, use default_factory. For others, use the default value.
            if isinstance(typ, type) and issubclass(typ, BaseModel):
                fields[key] = (Optional[typ], Field(default_factory=typ))
            else:
                default = self._default_for_type(typ)
                fields[key] = (Optional[typ], default)

        Pydux._schema = create_model('DynamicStoreModel', **fields)
        Pydux._store = ReactiveStoreDict(Pydux._schema(), self)

    def update_store(self, obj: Dict[str, Any]) -> None:
        """
        Updates the store with new values.

        Args:
            obj (Dict[str, Any]): Dictionary with changes.
        """
        if Pydux._schema is None:
            # Without schema, update simple dict
            if Pydux._store is None:
                Pydux._store = {}
            if isinstance(Pydux._store, dict):
                Pydux._store.update(obj)
            else:
                Pydux._store = obj
        else:
            try:
                # Use model_dump() from the base model to get nested data
                # No need for the check if we always use ReactiveStoreDict
                current_data = Pydux._store._base_model.model_dump()
                combined = {**current_data, **obj}
                validated = Pydux._schema(**combined)

                # If already ReactiveStoreDict, just update keys
                for k, v in combined.items():
                    Pydux._store[k] = v

            except ValidationError as e:
                raise TypeError(f"Validation error: {e}")

        # Notify reactive widgets
        if isinstance(Pydux._store, ReactiveStoreDict):
            for key in obj:
                Pydux._store.notify_key(key)

        self._notify_observers()

    def update_nested_model(self, model_key: str, partial_data: Dict[str, Any]) -> None:
        """
        Performs a partial update on a nested Pydantic model within the store.

        This is useful for updating specific fields of a complex object without
        having to replace the entire object. It retrieves the current nested model,
        merges the new data, and then updates the main store.

        Args:
            model_key: The key of the nested model in the store.
            partial_data: A dictionary with the fields to update in the nested model.
        """
        if Pydux._schema is None:
            raise ValueError(
                "Schema must be set before using update_nested_model")
        if not Pydux._store:
            raise ValueError("Store is empty")

        current_model_data = getattr(Pydux._store._base_model, model_key)

        # Si el valor es una instancia de Pydantic, usa model_copy
        if isinstance(current_model_data, BaseModel):
            updated_model_instance = current_model_data.model_copy(
                update=partial_data)
            self.update_store({model_key: updated_model_instance})

        else:
            if not isinstance(current_model_data, dict):
                # Si no es un diccionario, lo convertimos
                current_model_data = current_model_data

            updated_model_data = {**current_model_data, **partial_data}
            self.update_store({model_key: updated_model_data})

    def _notify_observers(self) -> None:
        """
        Calls the `on_store_change` method of all subscribed observers.
        Also invokes `_reconcile_widgets_state` if defined (PPGLifeCycle).
        """
        for observer in Pydux._observers:
            if hasattr(observer, '_reconcile_widgets_state') and callable(observer._reconcile_widgets_state):
                QTimer.singleShot(0, observer._reconcile_widgets_state)

            if Pydux._schema is None:
                observer.on_store_change(
                    Pydux._store if isinstance(Pydux._store, dict) else {})
            else:
                # CORRECTION: Pass the Pydantic instance directly
                observer.on_store_change(Pydux._store._base_model)

    def subscribe_to_store(self, observer: Any) -> None:
        """
        Subscribes an observer to the store to receive updates.

        Args:
            observer: Any object that has an `on_store_change(store)` method.
        """
        if hasattr(observer, 'on_store_change') and callable(observer.on_store_change):
            if observer not in Pydux._observers:
                Pydux._observers.append(observer)
        else:
            raise ValueError("Observer must have an 'on_store_change' method")

    def unsubscribe_from_store(self, observer: Any) -> None:
        """Removes an observer from the store."""
        if observer in Pydux._observers:
            Pydux._observers.remove(observer)
        else:
            raise ValueError("Observer not found in store")

    def get_nested(self, path: str) -> Any:
        """
        Get a nested value from the store using a dot-notated path.
        Example: get_nested("user.name") returns the name of the user.

        Args:
            path (str): The dot-notated path to the value in the store.
        """
        if not Pydux._store:
            return None

        keys = path.split('.')
        # No need for the check if we always use ReactiveStoreDict
        current = Pydux._store._base_model.model_dump()

        try:
            for key in keys:
                if isinstance(current, dict):
                    current = current[key]
                else:
                    current = getattr(current, key)
            return current
        except (KeyError, AttributeError):
            return None

    @property
    def store(self) -> Dict[str, Any]:
        """Getter for the store, always returns a dict."""
        if Pydux._schema is None:
            return Pydux._store if isinstance(Pydux._store, dict) else {}
        # No need for the check if we always use ReactiveStoreDict
        return Pydux._store._base_model.model_dump()

    @store.setter
    def store(self, value: Dict[str, Any]) -> None:
        """Setter for the store."""
        self.update_store(value)

    def clear_store(self) -> None:
        """Clear the store and reset it to an empty state."""
        if Pydux._schema:
            # CORRECTION: Always initialize the store as a ReactiveStoreDict
            Pydux._store = ReactiveStoreDict(Pydux._schema(), self)
        else:
            Pydux._store = {}
        self._notify_observers()

    def has_key(self, key: str) -> bool:
        """
        Check if a key exists in the store.

        Args:
            key (str): The key to check in the store.
        """
        store_dict = self.store
        return key in store_dict and store_dict[key] is not None

    def remove_from_store(self, key: str) -> None:
        """
        Remove a key from the store, setting it to None if schema is used.

        Args:
            key (str): The key to remove.
        """
        if Pydux._schema is None:
            if isinstance(Pydux._store, dict) and key in Pydux._store:
                del Pydux._store[key]
                self._notify_observers()
            else:
                raise KeyError(f"Key '{key}' not found in store")
        else:
            # No need for the check if we always use ReactiveStoreDict
            current_data = Pydux._store._base_model.model_dump()
            if key in current_data:
                updated = {**current_data, key: None}
                validated = Pydux._schema(**updated)
                Pydux._store = ReactiveStoreDict(validated, self)
                self._notify_observers()
            else:
                raise KeyError(f"Key '{key}' not found in store")

    def on_store_change(self, store: Dict[str, Any]) -> None:
        """
        Placeholder method to override by subclasses.
        Executes each time the store changes.

        Args:
            store (Dict[str, Any]): The new state of the store.
        """
        pass


class PPGStore:
    _instance = None
    _store = {}
    _observers = []

    def __new__(cls, *args, **kwargs):
        import warnings
        warnings.warn(
            "PPGStore is deprecated and will be removed in a future release. Use Pydux instead.",
            DeprecationWarning
        )
        if not cls._instance:
            cls._instance = super(PPGStore, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def add_to_store(self, obj: dict):
        if obj and isinstance(obj, dict):
            self._store.update(obj)
        else:
            raise ValueError(
                "Provide either a key and value or a dictionary object")

        self._notify_observers()

    def remove_from_store(self, key):
        if key in self._store:
            del self._store[key]
            self._notify_observers()
        else:
            raise KeyError(f"Key '{key}' not found in store")

    def _notify_observers(self) -> None:
        """
        Calls the `on_store_change` method of all subscribed observers.
        Also invokes `_reconcile_widgets_state` if defined (PPGLifeCycle).
        """
        for observer in Pydux._observers:
            if hasattr(observer, '_reconcile_widgets_state') and callable(observer._reconcile_widgets_state):
                QTimer.singleShot(0, observer._reconcile_widgets_state)

            if Pydux._schema is None:
                observer.on_store_change(
                    Pydux._store if isinstance(Pydux._store, dict) else {})
            else:
                observer.on_store_change(Pydux._store._base_model)

    def subscribe_to_store(self, observer):
        if hasattr(observer, 'update_store') and callable(observer.update_store):
            self._observers.append(observer)
        else:
            raise ValueError("Observer must have an 'update_store' method")

    def unsubscribe_from_store(self, observer):
        """
        Unsubscribe an observer from the store.
        Raises ValueError if the observer is not found.
        """
        if observer in self._observers:
            self._observers.remove(observer)
        else:
            raise ValueError("Observer not found in store")

    def update_store(self, store):
        pass

    def remove_observer(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)
        else:
            raise ValueError("Observer not found")

    @property
    def store(self):
        return self._store

    @store.setter
    def store(self, value):
        if isinstance(value, dict):
            self._store.update(value)
            self._notify_observers()
        else:
            raise ValueError("store must be a dictionary")


class PPGLifeCycle:
    def component_will_mount(self): pass

    def allow_bg(self):
        try:
            from PySide2.QtCore import Qt
            self.setAttribute(Qt.WA_StyledBackground, True)
        except ImportError:
            try:
                from PySide6.QtCore import Qt
                self.setAttribute(Qt.WA_StyledBackground, True)
            except ImportError:
                try:
                    from PyQt5.QtCore import Qt
                    self.setAttribute(Qt.WA_StyledBackground, True)
                except ImportError:
                    try:
                        from PyQt6.QtCore import Qt
                        self.setAttribute(Qt.WA_StyledBackground, True)
                    except ImportError:
                        pass

    def render_(self): pass

    def resizeEvent(self, e=None):
        self.responsive_UI()

    def component_did_mount(self): pass
    def set_CSS(self, path=None): pass
    def responsive_UI(self): pass

    def destroyComponent(self):
        self.setParent(None)
        self.deleteLater()

    def find(self, type, name):
        return self.findChild(type, name)

    @cached_property
    def _resource_locator(self):
        if is_frozen():
            resource_dirs = _frozen.get_resource_dirs()
        else:
            resource_dirs = _source.get_resource_dirs(self._project_dir)
        return ResourceLocator(resource_dirs)

    @cached_property
    def build_settings(self):
        """
        This dictionary contains the values of the settings listed in setting
        "public_settings". Eg. `self.build_settings['version']`.
        """
        if is_frozen():
            return _frozen.load_build_settings()
        return _source.load_build_settings(self._project_dir)

    @cached_property
    def _project_dir(self):
        assert not is_frozen(), 'Only available when running from source'
        return _source.get_project_dir()

    def get_resource(self, *rel_path):
        """
        Return the absolute path to the data file with the given name or
        (relative) path. When running from source, searches src/main/resources.
        Otherwise, searches your app's installation directory. If no file with
        the given name or path exists, a FileNotFoundError is raised.
        """
        return self._resource_locator.locate(*rel_path)

    def _clear_widgets(self):
        """
            Clear all child widgets except for the main widget.
        """
        try:
            for child_obj in self.findChildren(QWidget):
                if child_obj != self:
                    child_obj.deleteLater()
            QApplication.processEvents()
        except RuntimeError:
            pass

    def _ensure_children_visibility(self):
        """
        Ensure all child widgets are visible.

        Raises:
            RuntimeError: If a widget was already deleted.
            e: If any other error occurs.
        """
        try:
            for child_obj in self.findChildren(QWidget):
                child_obj.show()
            self.adjustSize()
            self.update()
            self.repaint()
        except RuntimeError as e:
            if 'already deleted' in str(e):
                raise RuntimeError("A widget was already deleted.")
            else:
                raise e

    def _trigger_render(self):
        """
        Trigger a re-render of the component (for Pydux instances)
        """
        try:
            # Todo el ciclo de vida se envuelve en el try
            self._clear_widgets()
            self.allow_bg()
            self.render_()
            self.responsive_UI()
            self.component_did_mount()
            self.set_CSS()

            self._ensure_children_visibility()
        except RuntimeError:
            pass
        finally:
            self.setUpdatesEnabled(True)

    def _reconcile_widgets_state(self):
        pass

    @staticmethod
    def calc(a, b): return int((a * b) / 100.0)


class _ApplicationContext:
    """
    The main point of contact between your application and ppg. For information
    on how to use it, please see the Manual:
        https://build-system.fman.io/manual/#your-python-code
    """

    def __init__(self):
        if self.excepthook:
            self.excepthook.install()
        # Many Qt classes require a QApplication to have been instantiated.
        # Do this here, before everything else, to achieve this:
        self.app
        # We don't build as a console app on Windows, so no point in installing
        # the SIGINT handler:
        if not is_windows():
            self._signal_wakeup_handler = \
                SignalWakeupHandler(self.app, self._qt_binding.QAbstractSocket)
            self._signal_wakeup_handler.install()
        if self.app_icon:
            self.app.setWindowIcon(self.app_icon)

    def run(self):
        """
        You should overwrite this method with the steps for starting your app.
        See eg. fbs's tutorial.
        """
        raise NotImplementedError()

    @cached_property
    def app(self):
        """
        The global Qt QApplication object for your app. Feel free to overwrite
        this property, eg. if you wish to use your own subclass of QApplication.
        An example of this is given in the Manual.
        """
        result = self._qt_binding.QApplication([])
        result.setApplicationName(self.build_settings['app_name'])
        result.setApplicationVersion(self.build_settings['version'])
        return result

    @cached_property
    def build_settings(self):
        """
        This dictionary contains the values of the settings listed in setting
        "public_settings". Eg. `self.build_settings['version']`.
        """
        if is_frozen():
            return _frozen.load_build_settings()
        return _source.load_build_settings(self._project_dir)

    def get_resource(self, *rel_path):
        """
        Return the absolute path to the data file with the given name or
        (relative) path. When running from source, searches src/main/resources.
        Otherwise, searches your app's installation directory. If no file with
        the given name or path exists, a FileNotFoundError is raised.
        """
        return self._resource_locator.locate(*rel_path)

    @cached_property
    def exception_handlers(self):
        """
        Return a list of exception handlers that should be invoked when an error
        occurs. See the documentation of module `fbs_runtime.excepthook` for
        more information.
        """
        return [StderrExceptionHandler()]

    @cached_property
    def licensing(self):
        """
        This field helps you implement a license key functionality for your
        application. For more information, see:
            https://build-system.fman.io/manual#license-keys
        """

        # fbs's licensing implementation incurs a dependency on Python library
        # `rsa`. We don't want to force all users to install this library.
        # So we import fbs_runtime.licensing here, instead of at the top of this
        # file. This lets people who don't use licensing avoid the dependency.
        from ppg_runtime.licensing import _Licensing

        return _Licensing(self.build_settings['licensing_pubkey'])

    @cached_property
    def app_icon(self):
        """
        The app icon. Not available on Mac because app icons are handled by the
        OS there.
        """
        if not is_mac():
            return self._qt_binding.QIcon(self.get_resource('Icon.ico'))

    @cached_property
    def excepthook(self):
        """
        Overwrite this method to use a custom excepthook. It should be an object
        with a .install() method, or `None` if you want to completely disable
        fbs's excepthook implementation.
        """
        return _Excepthook(self.exception_handlers)

    @cached_property
    def _qt_binding(self):
        # Implemented in subclasses.
        raise NotImplementedError()

    @cached_property
    def _resource_locator(self):
        if is_frozen():
            resource_dirs = _frozen.get_resource_dirs()
        else:
            resource_dirs = _source.get_resource_dirs(self._project_dir)
        return ResourceLocator(resource_dirs)

    @cached_property
    def _project_dir(self):
        assert not is_frozen(), 'Only available when running from source'
        return _source.get_project_dir()


_QtBinding = \
    namedtuple('_QtBinding', ('QApplication', 'QIcon', 'QAbstractSocket'))


def get_application_context(DevelopmentAppCtxtCls, FrozenAppCtxtCls=None):
    if FrozenAppCtxtCls is None:
        FrozenAppCtxtCls = DevelopmentAppCtxtCls
    if _state.APPLICATION_CONTEXT is None:
        _state.APPLICATION_CONTEXT = \
            FrozenAppCtxtCls() if is_frozen() else DevelopmentAppCtxtCls()
    return _state.APPLICATION_CONTEXT
