from PodSixNet.Connection import connection, ConnectionListener
import constants as cst
import msgpack
import socket
import time

from pygame.math import Vector2 as vec

import screen

PING_INTERVAL = 1
PING_TIMEOUT = 5


class OrbeetoClient:
    def __init__(self, client_player, host="localhost", port=12345):
        self.client_player = client_player

        self.server_address = (host, port)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setblocking(False)

        self.send_connection_request()

        self.players = {}
        self.bullets = {}
        self.portals = {}
        self.walls = {}

        self.last_ping = 0.0
        self.last_pong = time.time()

    def send_connection_request(self) -> None:
        """Sends a request to the server to acknowledge this client's existence

        :return: None
        """
        server_req = {"action": "connection_request"}
        packed = msgpack.packb(server_req, use_bin_type=True)
        self.udp_socket.sendto(packed, self.server_address)
        print(f"Connection request sent to {self.server_address}")

    def send_ping(self) -> None:
        """Sends a ping to the server to determine if the connection is still established

        :return: None
        """
        ping = {"action": "ping"}
        packed = msgpack.packb(ping, use_bin_type=True)
        self.udp_socket.sendto(packed, self.server_address)

    def send_move(self, x: float, y: float, angle: float) -> None:
        """Sends the information about the player's location to the server

        :param x: x-axis position of the player
        :param y: y-axis position of the player
        :param angle: The directional angle the player is facing
        :return: None
        """
        pass

    def send_fire(self, bullet_type: str, x: float, y: float, vel_x: float, vel_y: float, hit_w: int, hit_h: int) -> None:
        """Sends a request to create a bullet on the server with the given data

        :param bullet_type: The type of bullet to create
        :param x: The x-axis position to spawn the bullet
        :param y: The y-axis position to spawn the bullet
        :param vel_x: The x-axis velocity the bullet should have
        :param vel_y: The y-axis velocity the bullet should have
        :param hit_w: The width the bullet's hitbox should have
        :param hit_h: The height the bullet's hitbox should have
        :return: None
        """
        pass

    def loop(self) -> None:
        """Performs the main client loop

        :return:
        """

        unpacked_data = {"action": "null"}
        try:
            data, addr = self.udp_socket.recvfrom(4096)
            unpacked_data = msgpack.unpackb(data, raw=False)
        except BlockingIOError:
            pass
        except Exception as e:
            print(f"Error receiving packet: {e}")
            return

        match unpacked_data["action"]:
            case "server_acknowledgement":
                print(f"Acknowledged by server. Enjoy!")
            case "pong":
                print("Pong received")
            case _:
                pass

    #     self.my_id = None
    #     self.client_player = client_player
    #
    #     self.players = {}
    #     self.bullets = {}
    #     self.portals = {}
    #     self.walls = {}
    #
    #     self.last_ping = 0
    #     self.last_pong = time.time()
    #
    # def Network_init(self, data):
    #     self.my_id = data["id"]
    #     print(f"Connected as Player {self.my_id}")
    #
    # def Network_pong(self, data):
    #     # print("Pong received")
    #     self.last_pong = time.time()
    #
    # def Network_update_players(self, data):
    #     self.players = data["players"]
    #     self.client_player.hp = self.players[self.my_id]["hp"]
    #
    # def Network_update_bullets(self, data):
    #     self.bullets = data["bullets"]
    #
    # def Network_destroy_bullet(self, data):
    #     bullet_id = data["id"]
    #     if bullet_id in self.bullets:
    #         del self.bullets[bullet_id]
    #
    # def Network_update_portals(self, data):
    #     self.portals = data["portals"]
    #
    # def Network_teleport_player(self, data):
    #     print(f"Teleport player {data['player_id']}")
    #     pid = data["player_id"]
    #
    #     portal_out = self.portals[data["portal_out_id"]]
    #     portal_in = self.portals[portal_out["linked_to"]]
    #
    #     dir_out = portal_out["facing"]
    #     dir_in = portal_in["facing"]
    #
    #     self.client_player.room.last_tp_dirs = (dir_in, dir_out)
    #
    #     width = (self.players[pid]["hit_w"] + portal_out["hit_w"]) // 2 + 4
    #     height = (self.players[pid]["hit_h"] + portal_out["hit_h"]) // 2 + 4
    #
    #     print(f"Player vel: {self.client_player.vel.x}, {self.client_player.vel.y}")
    #     print(f"Room vel: {self.client_player.room.vel.x}, {self.client_player.room.vel.y}")
    #
    #     room_vel_before = vec(self.client_player.room.vel.x / (screen.dt * cst.M_FPS), self.client_player.room.vel.y / (screen.dt * cst.M_FPS))
    #
    #     if dir_out == cst.SOUTH:
    #         self.client_player.pos.x = portal_out["x"]
    #         self.client_player.pos.y = portal_out["y"] + height
    #         if dir_in == cst.SOUTH:
    #             self.client_player.vel.y += abs(room_vel_before.y)
    #         elif dir_in == cst.EAST:
    #             self.client_player.vel.x += abs(room_vel_before.y)
    #             self.client_player.vel.y += abs(room_vel_before.x)
    #         elif dir_in == cst.WEST:
    #             self.client_player.vel.x -= abs(room_vel_before.y)
    #             self.client_player.vel.y += abs(room_vel_before.x)
    #
    #     elif dir_out == cst.EAST:
    #         self.client_player.pos.x = portal_out["x"] + width
    #         self.client_player.pos.y = portal_out["y"]
    #         if dir_in == cst.SOUTH:
    #             self.client_player.vel.x += abs(room_vel_before.y)
    #             self.client_player.vel.y += abs(room_vel_before.x)
    #         elif dir_in == cst.EAST:
    #             self.client_player.vel.x += abs(room_vel_before.x)
    #         elif dir_in == cst.NORTH:
    #             self.client_player.vel.x += abs(room_vel_before.y)
    #             self.client_player.vel.y -= abs(room_vel_before.x)
    #
    #     elif dir_out == cst.NORTH:
    #         self.client_player.pos.x = portal_out["x"]
    #         self.client_player.pos.y = portal_out["y"] - height
    #         if dir_in == cst.EAST:
    #             self.client_player.vel.x += abs(room_vel_before.y)
    #             self.client_player.vel.y -= abs(room_vel_before.x)
    #         elif dir_in == cst.NORTH:
    #             self.client_player.vel.y -= abs(room_vel_before.y)
    #         elif dir_in == cst.WEST:
    #             self.client_player.vel.x -= abs(room_vel_before.y)
    #             self.client_player.vel.y -= abs(room_vel_before.x)
    #
    #     elif dir_out == cst.WEST:
    #         self.client_player.pos.x = portal_out["x"] - width
    #         self.client_player.pos.y = portal_out["y"]
    #         if dir_in == cst.SOUTH:
    #             self.client_player.vel.x -= abs(room_vel_before.y)
    #             self.client_player.vel.y += abs(room_vel_before.x)
    #         elif dir_in == cst.NORTH:
    #             self.client_player.vel.x -= abs(room_vel_before.y)
    #             self.client_player.vel.y -= abs(room_vel_before.x)
    #         elif dir_in == cst.WEST:
    #             self.client_player.vel.x -= abs(room_vel_before.x)
    #
    #     self.client_player.pos += self.client_player.room.pos
    #
    #     self.client_player.room.update_binds(dir_in, dir_out)
    #     self.client_player.room.readjust_binds_after_tp(dir_in, dir_out)
    #
    # def Network_destroy_portal(self, data):
    #     portal_id = data["id"]
    #     if portal_id in self.portals:
    #         del self.portals[portal_id]
    #
    # def Network_update_walls(self, data):
    #     self.walls = data["walls"]
    #
    # def Loop(self):
    #     # UDP Send/Receive
    #     try:
    #         data, _ = self.udp_socket.recvfrom(1024)
    #         data_dec = pickle.loads(data)
    #
    #         match data_dec["action"]:
    #             case "udp_request":
    #                 # msg = {
    #                 #     "action": "udp_request"
    #                 # }
    #                 # self.udp_socket.sendto(pickle.dumps(msg), self.server_address)
    #                 pass
    #             case "update_bullets":
    #                 print("got new bullets")
    #                 self.bullets = data_dec["bullets"]
    #
    #             case _:
    #                 pass
    #
    #     except BlockingIOError:
    #         pass
    #
    #     # TCP Send/Receive
    #     connection.Pump()
    #     self.Pump()
    #
    #     now = time.time()
    #     if now - self.last_pong > PING_INTERVAL:
    #         connection.Send({"action": "ping"})
    #         # print("Ping sent.")
    #
    #     if now - self.last_pong > PING_TIMEOUT:
    #         exit(0)
    #
    # def Network(self, data):
    #     # print("Unhandled message: ", data)
    #     pass
    #
    # # ----- Orbeeto Hooks ----- #
    # def send_move(self, x, y, angle):
    #     connection.Send({
    #         "action": "move",
    #         "x": x,
    #         "y": y,
    #         "angle": angle
    #     })
    #
    # def send_fire(self, bullet_type: str, x, y, vel_x, vel_y, hit_w: int, hit_h: int):
    #     fire = {
    #         "action": "fire",
    #         "bullet_type": bullet_type,
    #         "x": x,
    #         "y": y,
    #         "vel_x": vel_x,
    #         "vel_y": vel_y,
    #         "hit_w": hit_w,
    #         "hit_h": hit_h
    #     }
    #     self.udp_socket.sendto(pickle.dumps(fire), self.server_address)
