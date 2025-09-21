try:
    from PySide6.QtWidgets import QComboBox
except ImportError:
    try:
        from PySide2.QtWidgets import QComboBox
    except ImportError:
        try:
            from PyQt6.QtWidgets import QComboBox
        except ImportError:
            try:
                from PyQt5.QtWidgets import QComboBox
            except ImportError:
                raise ImportError("No Qt bindings found.")


class ReactiveComboBox(QComboBox):
    """
    Reactive QComboBox connected to Pydux, including support for nested models.

    Args:
        parent: Parent widget that contains the store.
        key: Key in the store for the selection (can be nested, e.g., "user.country").
        items: Fixed list of options (optional).
        dynamic_items: Key in the store that provides a dynamic list of options (optional).
        onChange: Optional callback when selection changes.
    """
    def __init__(self, parent, key, items=None, dynamic_items=None, onChange=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._parent = parent
        self._store_key = key
        self._items_key = dynamic_items
        self._onChange = onChange
        self._updating_from_store = False

        # Load initial items
        self._static_items = items or []
        self._update_items()

        # Set initial selection from store
        value = self._parent.get_nested(key) or ""
        if value in self._get_items():
            self.setCurrentText(str(value))

        # Connect signal for selection change
        self.currentTextChanged.connect(self._on_text_changed)

        # Subscribe to store changes if parent supports it
        if hasattr(parent, "subscribe_to_store"):
            parent.subscribe_to_store(self)

    def _get_items(self):
        """Returns current list of items (dynamic from store if items_key is defined)."""
        if self._items_key:
            dynamic_list = self._parent.get_nested(self._items_key)
            if isinstance(dynamic_list, list):
                return dynamic_list
        return self._static_items

    def _update_items(self):
        """Updates ComboBox items from store or fixed list."""
        current = self.currentText()
        self.blockSignals(True)
        self.clear()
        self.addItems([str(i) for i in self._get_items()])
        # Restore selection if still exists
        if current in self._get_items():
            self.setCurrentText(current)
        self.blockSignals(False)

    def _on_text_changed(self, text):
        """
        Internal callback when ComboBox selection changes.
        Updates the store (supports nested keys).
        """
        if self._updating_from_store:
            return

        if "." in self._store_key:
            model_key, nested_field = self._store_key.split(".", 1)
            if hasattr(self._parent, "update_nested_model"):
                self._parent.update_nested_model(model_key, {nested_field: text})
        else:
            self._parent.update_store({self._store_key: text})

        if callable(self._onChange):
            self._onChange(text)

    def _update_from_store(self):
        """Synchronizes ComboBox selection and items with the store."""
        # Update items if dynamic items key is defined
        if self._items_key:
            self._update_items()
        # Update selection
        value = str(self._parent.get_nested(self._store_key) or "")
        if self.currentText() != value:
            self._updating_from_store = True
            self.setCurrentText(value)
            self._updating_from_store = False

    def on_store_change(self, store):
        """Method automatically called when the store changes."""
        self._update_from_store()
