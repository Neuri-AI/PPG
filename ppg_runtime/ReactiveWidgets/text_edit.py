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
    def __init__(self, parent, key, placeholder: str = "", onChange=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._store_key = key
        self._parent = parent
        self._updating_from_store = False
        self._onChange = onChange
        self.setText(str(parent.store.get(key, "")))
        if placeholder:
            self.setPlaceholderText(placeholder)
        self.textChanged.connect(self._on_text_changed)
        if hasattr(parent, "subscribe_to_store"):
            parent.subscribe_to_store(self)

    def _on_text_changed(self):
        if self._updating_from_store: return
        text = self.toPlainText()
        self._parent.update_store({self._store_key: text})
        if callable(self._onChange): self._onChange(text)

    def _update_from_store(self, key):
        if key != self._store_key: return
        value = str(self._parent.store.get(key, ""))
        if self.toPlainText() != value:
            self._updating_from_store = True
            self.setPlainText(value)
            self._updating_from_store = False

    def on_store_change(self, store):
        self._update_from_store(self._store_key)
