
from ppg_runtime.application_context import Pydux, PPGLifeCycle, init_lifecycle
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel

@init_lifecycle
class AuthScreen(QWidget, PPGLifeCycle, Pydux):

	def component_will_mount(self):
		self.subscribe_to_store(self)

	def render_(self):
		layout = QVBoxLayout()
		layout.addWidget(QLabel('Auth Screen', self))
		layout.addWidget(QLineEdit(self, placeholderText='Username'))
		layout.addWidget(QLineEdit(self, placeholderText='Password', echoMode=QLineEdit.EchoMode.Password))
		layout.addWidget(QPushButton('Login', self, clicked=self.handle_login))
		self.setLayout(layout)

	def handle_login(self):
		self.update_store({'current_screen_index': 1})


