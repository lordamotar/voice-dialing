import sys
import os

# Set current working directory to the directory of the executable when frozen
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--settings":
        import settings_gui
        settings_gui.main()
    else:
        from voice_typing.main import main as app_main
        app_main()

