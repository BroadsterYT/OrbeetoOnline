import subprocess, sys, atexit
from menus.menuinputbars import arr

class ServerManager:
    def __init__(self):
        self.proc = None
        atexit.register(self.stop)

    def start(self):
        if not self.proc:
            self.print_settings()
            pythonw = sys.executable.replace("python.exe", "pythonw.exe")
            self.proc = subprocess.Popen([pythonw, "server.py"], creationflags=subprocess.CREATE_NO_WINDOW)
            print("Server started")

    def stop(self):
        if self.proc:
            print("Shutting down server...")
            self.proc.terminate()
            self.proc.wait()
            if self.proc.poll() is None:
                print("Process is still running")
            else:
                print("Process has terminated")
                self.proc = None
            print("Server stopped")

    def print_settings(self):
        print("\n---Server Settings---")
        for input_box in arr:
            if input_box.name == 'Server-Settings-1':
                print("Game duration: " + input_box.get_text())
            elif input_box.name == 'Server-Settings-2':
                print("Player limit: " + input_box.get_text())
            elif input_box.name == 'Server-Settings-3':
                print("Setting 3: " + input_box.get_text())
        print("")

servermanager = ServerManager()

"""
# Example usage:
if __name__ == "__main__":
    manager = ServerManager()
    manager.start()
"""