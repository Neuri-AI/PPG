try:
    from PySide6.QtWidgets import QSpinBox
except ImportError:
    try:
        from PySide2.QtWidgets import QSpinBox
    except ImportError:
        try:
            from PyQt6.QtWidgets import QSpinBox
        except ImportError:
            try:
                from PyQt5.QtWidgets import QSpinBox
            except ImportError:
                raise ImportError("No Qt bindings found.")


class ReactiveSpinBox(QSpinBox):
    """
    Reactive QSpinBox connected to Pydux, including support for nested models.

    Args:
        parent: Parent widget that contains the store.
        key: Key in the store (can be nested, e.g., "settings.count").
        onChange: Optional callback when value changes.
        minimum: Minimum value (default 0).
        maximum: Maximum value (default 100).
    """
    def __init__(self, parent, key, onChange=None, minimum=0, maximum=100, **kwargs):
        super().__init__(parent, **kwargs)
        self._store_key = key
        self._parent = parent
        self._updating_from_store = False
        self._onChange = onChange

        self.setRange(minimum, maximum)

        # Initialize value from store (supports nested)
        if hasattr(parent, "get_nested"):
            value = parent.get_nested(key) or minimum
        else:
            value = parent.store.get(key, minimum)
        self.setValue(int(value))

        # Connect signals
        self.valueChanged.connect(self._on_value_changed)

        # Subscribe to store changes
        if hasattr(parent, "subscribe_to_store"):
            parent.subscribe_to_store(self)

    def _on_value_changed(self, value):
        """
        Internal callback when the spinbox value changes.
        Updates the store (supports nested).
        """
        if self._updating_from_store:
            return

        if "." in self._store_key and hasattr(self._parent, "update_nested_model"):
            model_key, nested_field = self._store_key.split(".", 1)
            self._parent.update_nested_model(model_key, {nested_field: value})
        else:
            self._parent.update_store({self._store_key: value})

        if callable(self._onChange):
            self._onChange(value)

    def _update_from_store(self):
        """
        Syncs the spinbox value with the store.
        Supports nested keys using get_nested().
        """
        if hasattr(self._parent, "get_nested"):
            value = self._parent.get_nested(self._store_key) or self.minimum()
        else:
            value = self._parent.store.get(self._store_key, self.minimum())

        value = int(value)
        if self.value() != value:
            self._updating_from_store = True
            self.setValue(value)
            self._updating_from_store = False

    def on_store_change(self, store):
        """
        Method automatically called when the store changes.
        Simply refreshes the spinbox value from the store.
        """
        self._update_from_store()
