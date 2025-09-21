try:
    from PySide6.QtWidgets import QLineEdit
except ImportError:
    try:
        from PySide2.QtWidgets import QLineEdit
    except ImportError:
        try:
            from PyQt6.QtWidgets import QLineEdit
        except ImportError:
            try:
                from PyQt5.QtWidgets import QLineEdit
            except ImportError:
                raise ImportError(
                    "No Qt bindings found. Install PySide6, PySide2, PyQt6 or PyQt5."
                )
class ReactiveLineEdit(QLineEdit):
    """
    Reactive QLineEdit that connects to Pydux, including support for nested models.

    Args:
        parent: Parent widget that contains the store.
        key: Key in the store (can be nested, e.g. "user.name").
        placeholder: Optional placeholder text.
        onChange: Optional callback when the text changes.

    """
    def __init__(self, parent, key, placeholder: str = "", onChange=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._store_key = key
        self._parent = parent
        self._updating_from_store = False
        self._onChange = onChange

        # Initialize text from the store (supports nested keys)
        self._update_from_store()

        if placeholder:
            self.setPlaceholderText(placeholder)

        # Connect text change signal
        self.textChanged.connect(self._on_text_changed)

        # Subscribe to store changes if the parent allows it
        if hasattr(parent, "subscribe_to_store"):
            parent.subscribe_to_store(self)

    def _on_text_changed(self, text):
        """
        Internal callback when the LineEdit text changes.
        Updates the store (supports nested keys).
        """
        if self._updating_from_store:
            return

        # Check for nested key
        if "." in self._store_key:
            model_key, nested_field = self._store_key.split(".", 1)
            if hasattr(self._parent, "update_nested_model"):
                self._parent.update_nested_model(model_key, {nested_field: text})
        else:
            self._parent.update_store({self._store_key: text})

        if callable(self._onChange):
            self._onChange(text)

    def _update_from_store(self):
        """
            Updates the QLineEdit text from the store.
            Supports nested keys with get_nested().
        """
        value = ""
        if hasattr(self._parent, "get_nested"):
            value = self._parent.get_nested(self._store_key) or ""
        if self.text() != str(value):
            self._updating_from_store = True
            self.setText(str(value))
            self._updating_from_store = False

    def on_store_change(self, store):
        """
            Method that is called automatically when the store changes.
            Here we simply refresh the value from the store.
        """
        self._update_from_store()
