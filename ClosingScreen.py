import time
class closingScreeen:
    def __init__(self):
        self.close_time = None

    def changeCloseFlag(self):
        self.close_time = time.time() + 3

close_screen = closingScreeen()
