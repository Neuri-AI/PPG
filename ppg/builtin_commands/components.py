component_template = f"""
from ppg_runtime.application_context import Pydux, PPGLifeCycle, init_lifecycle
from $Binding.QtWidgets import $Widget

@init_lifecycle
class $Name($Widget, PPGLifeCycle, Pydux):

	def component_will_mount(self):
		self.subscribe_to_store(self)

	def render_(self):
		# Render the UI here
		pass

"""
