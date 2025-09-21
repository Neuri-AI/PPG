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
    """

    def __init__(self, parent, key: str = "", placeholder: str = "", text: str = "", onChange=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._store_key = key
        self._parent = parent
        self._placeholder = placeholder
        self._template_text = text
        self._onChange = onChange

        # Subscribe to store changes if parent supports it
        if hasattr(parent, "subscribe_to_store"):
            parent.subscribe_to_store(self)

        # Initialize label text
        self._update_from_store()

    def _update_from_store(self):
        """
        Updates the QLabel text from the store.
        """
        if self._template_text:
            # Get the entire store to use for formatting
            if hasattr(self._parent, "store"):
                store_data = self._parent.store
            else:
                # Fallback if no store is found
                store_data = {}

            try:
                # Format the text with all values from the store
                current_value = self._template_text.format(**store_data)
            except KeyError:
                # If a key in the template doesn't exist in the store
                # This prevents the app from crashing.
                current_value = self._template_text
        else:
            # Original logic for non-templated text
            if hasattr(self._parent, "get_nested"):
                current_value = self._parent.get_nested(self._store_key) or ""
            else:
                current_value = str(
                    self._parent.store.get(self._store_key, ""))

        # Use placeholder if value is empty
        if not current_value and self._placeholder:
            current_value = self._placeholder

        # Update text if it's different
        if self.text() != str(current_value):
            self.setText(str(current_value))
            self.adjustSize()
            if callable(self._onChange):
                self._onChange(current_value)

    def on_store_change(self, store):
        """
        Method automatically called when the store changes.
        """
        self._update_from_store()
