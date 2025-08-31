from PodSixNet.Connection import connection, ConnectionListener


class NetClient(ConnectionListener):
    def __init__(self, host="localhost", port=12345):
        self.Connect((host, port))
        print(f"Hooked to Player on {host} with port {port}")
        self.my_id = None
        self.players = {}

    def Network_init(self, data):
        self.my_id = data["id"]
        print(f"Connected as Player {self.my_id}")

    def Network_update_state(self, data):
        self.players = data["players"]

    def Network(self, data):
        print("Unhandled message: ", data)

    # ----- Orbeeto Hooks ----- #
    def send_move(self, x, y):
        connection.Send({"action": "move", "x": x, "y": y})

    def pump(self):
        connection.Pump()
        self.Pump()
