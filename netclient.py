from PodSixNet.Connection import connection, ConnectionListener
import constants as cst
import pickle
import socket
import time



from pygame.math import Vector2 as vec

import screen



PING_INTERVAL = 0.5
#changed this from 1 to 3
PING_TIMEOUT = 3


class NetClient(ConnectionListener):
    def __init__(self, client_player, host="localhost", port=12345):
        self.server_address = (host, port)
        self.udp_socket = None
        self.connected = False

        self.my_id = None
        self.client_player = client_player

        self.players = {}
        self.bullets = {}
        self.portals = {}
        self.walls = {}

        self.last_ping = 0
        self.last_pong = time.time()

        # self.Connect((host, port))
        print(f"Hooked to Player on {host} with port {port}")

    def establish_connection(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setblocking(False)

        server_req = {
            "action": "udp_request"
        }
        server_req_bin = pickle.dumps(server_req)
        self.udp_socket.sendto(server_req_bin, self.server_address)
        print(f"host: {self.server_address[0]}, port: {self.server_address[1]}")
        self.Connect((self.server_address[0], self.server_address[1]))
        self.connected = True

    def Network_init(self, data):
        self.my_id = data["id"]
        print(f"Connected as Player {self.my_id}")

    def Network_pong(self, data):
        # print("Pong received")
        self.last_pong = time.time()

    def Network_update_players(self, data):
        if self.my_id is not None:
            self.players = data["players"]
            self.client_player.hp = self.players[self.my_id]["hp"]

    def Network_update_bullets(self, data):
        self.bullets = data["bullets"]

    def Network_destroy_bullet(self, data):
        bullet_id = data["id"]
        if bullet_id in self.bullets:
            del self.bullets[bullet_id]

    def Network_update_portals(self, data):
        self.portals = data["portals"]

    def Network_teleport_player(self, data):
        print(f"Teleport player {data['player_id']}")
        pid = data["player_id"]

        portal_out = self.portals[data["portal_out_id"]]
        portal_in = self.portals[portal_out["linked_to"]]

        dir_out = portal_out["facing"]
        dir_in = portal_in["facing"]

        self.client_player.room.last_tp_dirs = (dir_in, dir_out)

        width = (self.players[pid]["hit_w"] + portal_out["hit_w"]) // 2 + 4
        height = (self.players[pid]["hit_h"] + portal_out["hit_h"]) // 2 + 4

        print(f"Player vel: {self.client_player.vel.x}, {self.client_player.vel.y}")
        print(f"Room vel: {self.client_player.room.vel.x}, {self.client_player.room.vel.y}")

        room_vel_before = vec(self.client_player.room.vel.x / (screen.dt * cst.M_FPS), self.client_player.room.vel.y / (screen.dt * cst.M_FPS))

        if dir_out == cst.SOUTH:
            self.client_player.pos.x = portal_out["x"]
            self.client_player.pos.y = portal_out["y"] + height
            if dir_in == cst.SOUTH:
                self.client_player.vel.y += abs(room_vel_before.y)
            elif dir_in == cst.EAST:
                self.client_player.vel.x += abs(room_vel_before.y)
                self.client_player.vel.y += abs(room_vel_before.x)
            elif dir_in == cst.WEST:
                self.client_player.vel.x -= abs(room_vel_before.y)
                self.client_player.vel.y += abs(room_vel_before.x)

        elif dir_out == cst.EAST:
            self.client_player.pos.x = portal_out["x"] + width
            self.client_player.pos.y = portal_out["y"]
            if dir_in == cst.SOUTH:
                self.client_player.vel.x += abs(room_vel_before.y)
                self.client_player.vel.y += abs(room_vel_before.x)
            elif dir_in == cst.EAST:
                self.client_player.vel.x += abs(room_vel_before.x)
            elif dir_in == cst.NORTH:
                self.client_player.vel.x += abs(room_vel_before.y)
                self.client_player.vel.y -= abs(room_vel_before.x)

        elif dir_out == cst.NORTH:
            self.client_player.pos.x = portal_out["x"]
            self.client_player.pos.y = portal_out["y"] - height
            if dir_in == cst.EAST:
                self.client_player.vel.x += abs(room_vel_before.y)
                self.client_player.vel.y -= abs(room_vel_before.x)
            elif dir_in == cst.NORTH:
                self.client_player.vel.y -= abs(room_vel_before.y)
            elif dir_in == cst.WEST:
                self.client_player.vel.x -= abs(room_vel_before.y)
                self.client_player.vel.y -= abs(room_vel_before.x)

        elif dir_out == cst.WEST:
            self.client_player.pos.x = portal_out["x"] - width
            self.client_player.pos.y = portal_out["y"]
            if dir_in == cst.SOUTH:
                self.client_player.vel.x -= abs(room_vel_before.y)
                self.client_player.vel.y += abs(room_vel_before.x)
            elif dir_in == cst.NORTH:
                self.client_player.vel.x -= abs(room_vel_before.y)
                self.client_player.vel.y -= abs(room_vel_before.x)
            elif dir_in == cst.WEST:
                self.client_player.vel.x -= abs(room_vel_before.x)

        self.client_player.pos += self.client_player.room.pos

        self.client_player.room.update_binds(dir_in, dir_out)
        self.client_player.room.readjust_binds_after_tp(dir_in, dir_out)

    def Network_destroy_portal(self, data):
        portal_id = data["id"]
        if portal_id in self.portals:
            del self.portals[portal_id]

    def Network_update_walls(self, data):
        self.walls = data["walls"]

    def handle_timeout(self):

        self.connected = False
        self.cleanup()

        try:
            import gamestack

            # Only pop if there is more than 1 item in the stack
            if len(gamestack.gamestack.stack) > 1:
                gamestack.gamestack.pop()
            else:
                gamestack.gamestack.stack = [
                    gamestack.s_action,
                    gamestack.s_startup
                ]
        except Exception as e:
            print("Failed to pop game state:", e)

    def Loop(self):
        if not self.connected:
            return

        # UDP Send/Receive
        try:
            data, _ = self.udp_socket.recvfrom(1024)
            data_dec = pickle.loads(data)

            if data_dec["action"] == "udp_request":
                msg = {
                    "action": "udp_request"
                }
                self.udp_socket.sendto(pickle.dumps(msg), self.server_address)
        except BlockingIOError:
            pass

        # TCP Send/Receive
        connection.Pump()
        self.Pump()

        now = time.time()
        if now - self.last_pong > PING_INTERVAL:
            connection.Send({"action": "ping"})
            # print("Ping sent.")

        if now - self.last_pong > PING_TIMEOUT:
            print("Ping timeout")
            self.handle_timeout()
            #exit(0)



    def Network(self, data):
        # print("Unhandled message: ", data)
        pass

    # ----- Orbeeto Hooks ----- #
    def request_disconnect(self):
        connection.Close()

    def send_move(self, x, y):
        if not self.connected:
            return

        connection.Send({
            "action": "move",
            "x": x,
            "y": y,
        })

    def send_fire(self, bullet_type: str, x, y, vel_x, vel_y, hit_w: int, hit_h: int):
        if not self.connected:
            return

        fire = {
            "action": "fire",
            "bullet_type": bullet_type,
            "x": x,
            "y": y,
            "vel_x": vel_x,
            "vel_y": vel_y,
            "hit_w": hit_w,
            "hit_h": hit_h
        }
        self.udp_socket.sendto(pickle.dumps(fire), self.server_address)

    def cleanup (self):
        try:
            self.udp_socket.close()
        except Exception:
            print(Exception)
            pass
        try:
            connection.Close()
        except Exception:
            print(Exception)
            pass
        print("Network client cleaned up.")