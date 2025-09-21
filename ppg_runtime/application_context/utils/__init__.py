import sys


def app_is_frozen(): return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')