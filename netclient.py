from PodSixNet.Connection import connection, ConnectionListener
import constants as cst
import time

from pygame.math import Vector2 as vec

PING_INTERVAL = 2
PING_TIMEOUT = 5


class NetClient(ConnectionListener):
    def __init__(self, client_player, host="localhost", port=12345):
        self.Connect((host, port))
        print(f"Hooked to Player on {host} with port {port}")
        self.my_id = None

        self.client_player = client_player

        self.players = {}
        self.bullets = {}
        self.portals = {}
        self.walls = {}

        self.last_ping = 0
        self.last_pong = time.time()

    def Network_init(self, data):
        self.my_id = data["id"]
        print(f"Connected as Player {self.my_id}")

    def Network_pong(self, data):
        # print("Pong received")
        self.last_pong = time.time()

    def Network_update_players(self, data):
        self.players = data["players"]

    def Network_update_bullets(self, data):
        self.bullets = data["bullets"]

    def Network_destroy_bullet(self, data):
        bullet_id = data["id"]
        if bullet_id in self.bullets:
            del self.bullets[bullet_id]

    def Network_update_portals(self, data):
        self.portals = data["portals"]

    def Network_teleport_player(self, data):
        print("Teleport player!")
        pid = data["player_id"]
        if pid != self.my_id:
            return

        portal_out = self.portals[data["portal_out_id"]]
        portal_in = self.portals[portal_out["linked_to"]]

        dir_out = portal_out["facing"]
        dir_in = portal_in["facing"]

        self.client_player.room.last_tp_dirs = (dir_in, dir_out)

        width = (self.players[pid]["hit_w"] + portal_out["hit_w"]) // 2 + 32
        height = (self.players[pid]["hit_h"] + portal_out["hit_h"]) // 2 + 32

        if dir_out == cst.SOUTH:
            self.client_player.pos.x = portal_out["x"]
            self.client_player.pos.y = portal_out["y"] + height
        elif dir_out == cst.EAST:
            self.client_player.pos.x = portal_out["x"] + width
            self.client_player.pos.y = portal_out["y"]
        elif dir_out == cst.NORTH:
            self.client_player.pos.x = portal_out["x"]
            self.client_player.pos.y = portal_out["y"] - height
        elif dir_out == cst.WEST:
            self.client_player.pos.x = portal_out["x"] - width
            self.client_player.pos.y = portal_out["y"]
            # self.client_player.vel.x += 1000

        self.client_player.pos += self.client_player.room.pos

        self.client_player.room.update_binds(dir_in, dir_out)
        self.client_player.room.readjust_binds_after_tp(dir_in, dir_out)

        # dir_angles = {cst.SOUTH: 180, cst.EAST: 90, cst.NORTH: 0, cst.WEST: 270}
        #
        # if dir_in == cst.EAST:
        #     dir_angles.update({cst.EAST: 180, cst.NORTH: 90, cst.WEST: 0, cst.SOUTH: 270})
        # elif dir_in == cst.NORTH:
        #     dir_angles.update({cst.NORTH: 180, cst.WEST: 90, cst.SOUTH: 0, cst.EAST: 270})
        # elif dir_in == cst.WEST:
        #     dir_angles.update({cst.WEST: 180, cst.SOUTH: 90, cst.EAST: 0, cst.NORTH: 270})

        print(f"Before rotation - Room vel: {self.client_player.room.vel}")
        print(f"Before rotation - Player vel: {self.client_player.vel}")
        # self.client_player.room.sprites_rotate_trajectory(dir_angles[dir_out])
        # self.client_player.vel += self.client_player.room.vel
        self.client_player.room.vel = vec(data["room_vel_x"], data["room_vel_y"])
        print(f"After rotation - Room vel: {self.client_player.room.vel}")
        print(f"After rotation - Player vel: {self.client_player.vel}")

    def Network_destroy_portal(self, data):
        portal_id = data["id"]
        if portal_id in self.portals:
            del self.portals[portal_id]

    def Network_update_walls(self, data):
        self.walls = data["walls"]

    def Loop(self):
        connection.Pump()
        self.Pump()

        now = time.time()
        if now - self.last_pong > PING_INTERVAL:
            connection.Send({"action": "ping"})
            # print("Ping sent.")

        if now - self.last_pong > PING_TIMEOUT:
            exit(0)

    def Network(self, data):
        # print("Unhandled message: ", data)
        pass

    # ----- Orbeeto Hooks ----- #
    def send_move(self, x, y):
        connection.Send({
            "action": "move",
            "x": x,
            "y": y,
        })

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
