try:
    from PySide6.QtWidgets import QCheckBox
except ImportError:
    try:
        from PySide2.QtWidgets import QCheckBox
    except ImportError:
        try:
            from PyQt6.QtWidgets import QCheckBox
        except ImportError:
            try:
                from PyQt5.QtWidgets import QCheckBox
            except ImportError:
                raise ImportError("No Qt bindings found.")

from typing import Callable, Optional

class ReactiveCheckBox(QCheckBox):
    """
    Reactive QCheckBox connected to Pydux, including support for nested models.

    Args:
        parent: Parent widget that contains the store.
        key: Key in the store (can be nested, e.g., "user.active").
        text: Optional text for the checkbox label.
        onChange: Optional callback when the checkbox state changes.
    """
    def __init__(self, parent, key: str, text: str = "", onChange: Optional[Callable[[bool], None]] = None, **kwargs):
        super().__init__(text, parent, **kwargs)
        self._store_key = key
        self._parent = parent
        self._updating_from_store = False
        self._onChange = onChange

        # Initialize checkbox state from store
        value = self._parent.get_nested(self._store_key) or False
        self.setChecked(bool(value))

        # Connect state change signal
        self.stateChanged.connect(self._on_state_changed)

        # Subscribe to store changes if parent supports it
        if hasattr(parent, "subscribe_to_store"):
            parent.subscribe_to_store(self)

    def _on_state_changed(self, state):
        """
        Internal callback when checkbox state changes.
        Updates the store (supports nested keys).
        """
        if self._updating_from_store:
            return

        if "." in self._store_key:
            model_key, nested_field = self._store_key.split(".", 1)
            if hasattr(self._parent, "update_nested_model"):
                self._parent.update_nested_model(model_key, {nested_field: bool(state)})
        else:
            self._parent.update_store({self._store_key: bool(state)})

        if callable(self._onChange):
            self._onChange(state)

    def _update_from_store(self):
        """
        Updates the checkbox state from the store.
        Supports nested keys using get_nested().
        """
        value = self._parent.get_nested(self._store_key) or False
        if self.isChecked() != bool(value):
            self._updating_from_store = True
            self.setChecked(bool(value))
            self._updating_from_store = False

    def on_store_change(self, store):
        """
        Method automatically called when the store changes.
        Refreshes the checkbox state from the store.
        """
        self._update_from_store()
