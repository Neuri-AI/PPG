try:
    from PySide6.QtWidgets import QLabel
except ImportError:
    try:
        from PySide2.QtWidgets import QLabel
    except ImportError:
        try:
            from PyQt6.QtWidgets import QLabel
        except ImportError:
            try:
                from PyQt5.QtWidgets import QLabel
            except ImportError:
                raise ImportError(
                    "No Qt bindings found. Install PySide6, PySide2, PyQt6 or PyQt5."
                )
class ReactiveLabel(QLabel):
    """
    Reactive QLabel connected to Pydux, including support for nested models.

    Args:
        parent: Parent widget that contains the store.
        key: Key in the store (can be nested, e.g., "user.name").
        placeholder: Optional placeholder text when value is empty.
        onChange: Optional callback when the text changes.
    """
    def __init__(self, parent, key: str, placeholder: str = "", onChange=None):
        super().__init__(parent)
        self._store_key = key
        self._parent = parent
        self._placeholder = placeholder
        self._onChange = onChange

        # Subscribe to store changes if parent supports it
        if hasattr(parent, "subscribe_to_store"):
            parent.subscribe_to_store(self)

        # Initialize label text
        self._update_from_store()

    def _update_from_store(self):
        """
        Updates the QLabel text from the store.
        Supports nested keys using get_nested().
        """
        if hasattr(self._parent, "get_nested"):
            value = self._parent.get_nested(self._store_key) or ""
        else:
            value = str(self._parent.store.get(self._store_key, ""))

        # Use placeholder if value is empty
        if not value and self._placeholder:
            value = self._placeholder

        if self.text() != str(value):
            self.setText(str(value))
            self.adjustSize()
            if callable(self._onChange):
                self._onChange(value)

    def on_store_change(self, store):
        """
        Method automatically called when the store changes.
        Simply refreshes the label text from the store.
        """
        self._update_from_store()
