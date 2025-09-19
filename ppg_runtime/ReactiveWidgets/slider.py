try:
    from PySide6.QtWidgets import QSlider
    from PySide6.QtCore import Qt
except ImportError:
    try:
        from PySide2.QtWidgets import QSlider
        from PySide2.QtCore import Qt
    except ImportError:
        try:
            from PyQt6.QtWidgets import QSlider
            from PyQt6.QtCore import Qt
        except ImportError:
            try:
                from PyQt5.QtWidgets import QSlider
                from PyQt5.QtCore import Qt
            except ImportError:
                raise ImportError("No Qt bindings found.")


class ReactiveSlider(QSlider):
    def __init__(self, parent, key, orientation=None, onChange=None, minimum=0, maximum=100, **kwargs):

        orientation = orientation or Qt.Horizontal
        super().__init__(orientation, parent, **kwargs)
        self._store_key = key
        self._parent = parent
        self.setRange(minimum, maximum)
        self.setValue(parent.store.get(key, minimum))
        self._updating_from_store = False
        self._onChange = onChange
        self.valueChanged.connect(self._on_value_changed)
        if hasattr(parent, "subscribe_to_store"):
            parent.subscribe_to_store(self)

    def _on_value_changed(self, value):
        if self._updating_from_store: return
        self._parent.update_store({self._store_key: value})
        if callable(self._onChange): self._onChange(value)

    def _update_from_store(self, key):
        if key != self._store_key: return
        value = int(self._parent.store.get(key, self.minimum()))
        if self.value() != value:
            self._updating_from_store = True
            self.setValue(value)
            self._updating_from_store = False

    def on_store_change(self, store):
        self._update_from_store(self._store_key)
