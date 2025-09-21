try:
    from PySide6.QtWidgets import QTextEdit
except ImportError:
    try:
        from PySide2.QtWidgets import QTextEdit
    except ImportError:
        try:
            from PyQt6.QtWidgets import QTextEdit
        except ImportError:
            try:
                from PyQt5.QtWidgets import QTextEdit
            except ImportError:
                raise ImportError("No Qt bindings found.")


class ReactiveTextEdit(QTextEdit):
    """
    Reactive QTextEdit connected to Pydux, including support for nested models.

    Args:
        parent: Parent widget that contains the store.
        key: Key in the store (can be nested, e.g., "user.description").
        placeholder: Optional placeholder text when value is empty.
        onChange: Optional callback when the text changes.
    """
    def __init__(self, parent, key, placeholder: str = "", onChange=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._store_key = key
        self._parent = parent
        self._updating_from_store = False
        self._onChange = onChange

        # Initialize text from store (supports nested)
        self._update_from_store()

        if placeholder:
            self.setPlaceholderText(placeholder)

        # Connect text changed signal
        self.textChanged.connect(self._on_text_changed)

        # Subscribe to store changes
        if hasattr(parent, "subscribe_to_store"):
            parent.subscribe_to_store(self)

    def _on_text_changed(self):
        """
        Internal callback when the text changes.
        Updates the store (supports nested keys).
        """
        if self._updating_from_store:
            return

        text = self.toPlainText()
        if "." in self._store_key and hasattr(self._parent, "update_nested_model"):
            model_key, nested_field = self._store_key.split(".", 1)
            self._parent.update_nested_model(model_key, {nested_field: text})
        else:
            self._parent.update_store({self._store_key: text})

        if callable(self._onChange):
            self._onChange(text)

    def _update_from_store(self):
        """
        Syncs the QTextEdit content with the store.
        Supports nested keys using get_nested().
        """
        if hasattr(self._parent, "get_nested"):
            value = self._parent.get_nested(self._store_key) or ""
        else:
            value = str(self._parent.store.get(self._store_key, ""))

        if self.toPlainText() != str(value):
            self._updating_from_store = True
            self.setPlainText(str(value))
            self._updating_from_store = False

    def on_store_change(self, store):
        """
        Method automatically called when the store changes.
        Simply refreshes the QTextEdit content from the store.
        """
        self._update_from_store()
