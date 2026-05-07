"""Entry point for the RPG game.
This file now delegates to the modular implementation in ui.py.
"""

from ui import MainApp

if __name__ == '__main__':
    app = MainApp()
    app.mainloop()
