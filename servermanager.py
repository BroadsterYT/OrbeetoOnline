import subprocess, sys, atexit

class ServerManager:
    def __init__(self):
        self.proc = None
        atexit.register(self.stop)

    def start(self):
        if not self.proc:
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


servermanager = ServerManager()

"""
# Example usage:
if __name__ == "__main__":
    manager = ServerManager()
    manager.start()
"""