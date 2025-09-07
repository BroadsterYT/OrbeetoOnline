from PodSixNet.Connection import connection, ConnectionListener
import time

PING_INTERVAL = 2
PING_TIMEOUT = 5


class NetClient(ConnectionListener):
    def __init__(self, host="localhost", port=12345):
        self.Connect((host, port))
        print(f"Hooked to Player on {host} with port {port}")
        self.my_id = None
        self.players = {}
        self.bullets = {}
        self.portals = {}

        self.last_ping = 0
        self.last_pong = time.time()

    def Network_init(self, data):
        self.my_id = data["id"]
        print(f"Connected as Player {self.my_id}")

    def Network_pong(self, data):
        print("Pong received")
        self.last_pong = time.time()

    def Network_update_state(self, data):
        self.players = data["players"]

    def Network_update_bullets(self, data):
        self.bullets = data["bullets"]

    def Network_destroy_bullet(self, data):
        bullet_id = data["id"]
        if bullet_id in self.bullets:
            del self.bullets[bullet_id]

    def Network_update_portals(self, data):
        self.portals = data["portals"]

    def Network_destroy_portal(self, data):
        portal_id = data["id"]
        if portal_id in self.portals:
            del self.portals[portal_id]

    def Loop(self):
        connection.Pump()
        self.Pump()

        now = time.time()
        if now - self.last_pong > PING_INTERVAL:
            connection.Send({"action": "ping"})
            print("Ping sent.")

        if now - self.last_pong > PING_TIMEOUT:
            exit(0)

    def Network(self, data):
        # print("Unhandled message: ", data)
        pass

    # ----- Orbeeto Hooks ----- #
    def send_move(self, x, y):
        connection.Send({"action": "move", "x": x, "y": y})

    def send_fire(self, bullet_type: str, x, y, vel_x, vel_y, hit_w: int, hit_h: int):
        connection.Send({
            "action": "fire",
            "bullet_type": bullet_type,
            "x": x,
            "y": y,
            "vel_x": vel_x,
            "vel_y": vel_y,
            "hit_w": hit_w,
            "hit_h": hit_h
        })
