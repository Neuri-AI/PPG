
from ppg_runtime.application_context import Pydux, PPGLifeCycle, init_lifecycle
from PySide6.QtWidgets import QWidget, QLabel

@init_lifecycle
class Home(QWidget, PPGLifeCycle, Pydux):

	def component_will_mount(self):
		self.subscribe_to_store(self)

	def render_(self):
		QLabel('Welcome Home!', self)

