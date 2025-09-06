from PodSixNet.Connection import connection, ConnectionListener
import time
import sys

class NetClient(ConnectionListener):
    def __init__(self, host="localhost", port=12345, handshake_timeout=5):
        self.Connect((host, port))
        print(f"Hooked to Player on {host} with port {port}")
        self.my_id = None
        self.players = {}
        self.bullets = {}
        self.name = "PlayerX"
        self.connected_ok = False
        self.handshake_timeout = handshake_timeout
        self.start_time = time.time()
        self.last_print_time = 0

        self.send_init()

    def send_init(self):
        """Sends initialization request to the server"""
        connection.Send({"action": "init", "name": self.name})

    def Network_ack(self, data):
        """If server receives initialization request, server sends acknowledgement message back to client"""
        print(f"Server says: {data['message']}, your ID is {data['id']}")
        self.my_id = data['id']
        self.connected_ok = True


    def wait_for_handshake(self):
        """checks if acknowledgement is received from the server"""
        self.pump()
        current_time = time.time()

        if not self.connected_ok and time.time() - self.start_time > self.handshake_timeout:
            print("Error: Server did not acknowledge handshake!")
            sys.exit()
        elif not self.connected_ok and current_time - self.last_print_time > 1:
            print("Waiting on Server...")
            self.last_print_time = current_time
            return False
        elif self.connected_ok:
            return True
        return False

    '''
    def Network_init(self, data):
        self.my_id = data["id"]
        print(f"Connected as Player {self.my_id}")
    '''
    def Network_update_state(self, data):
        self.players = data["players"]
        # print("Players updated")

    def Network_update_bullets(self, data):
        self.bullets = data["bullets"]
        # print("Bullets updated")

    def Network_destroy_bullet(self, data):
        bullet_id = data["id"]
        if bullet_id in self.bullets:
            del self.bullets[bullet_id]

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

    def pump(self):
        connection.Pump()
        self.Pump()