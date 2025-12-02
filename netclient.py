from PodSixNet.Connection import connection, ConnectionListener
import constants as cst
import pickle
import socket
import time
import ipaddress

from pygame.math import Vector2 as vec

from menus.menuinputbars import arr

import gamestack as gs
from servermanager import servermanager
import gamestack

import screen

PING_INTERVAL = 2
PING_TIMEOUT = 6


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
        self.last_pong = None

        self.connection_lost_header = None

        print(f"Hooked to Player on {host} with port {port}")

    def validate_IPAddress(self, ip):
        if ip == "localhost":
            return True
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            print("Invalid IP address!")
            return False

    def establish_connection(self):
        host, port = self.server_address
        if not self.validate_IPAddress(host):
            return
        # resetting player conditions
        self.client_player.hp = 50
        self.client_player.health_bar.add_to_gamestate()
        self.client_player.gun_heat = 0
        self.client_player.realizer.clear()

        room_pos = self.client_player.room.pos
        self.client_player.pos.x = room_pos.x + 640
        self.client_player.pos.y = room_pos.y + 360

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setblocking(False)
        server_req = {
            "action": "udp_request"
        }
        server_req_bin = pickle.dumps(server_req)
        try:
            self.udp_socket.sendto(server_req_bin, self.server_address)
        except Exception as e:
            print(e)
            return
        print(f"host: {self.server_address[0]}, port: {self.server_address[1]}")
        self.Connect((self.server_address[0], self.server_address[1]))
        self.send_username()

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            if host == "localhost" or host == s.getsockname()[0]:
                self.send_server_settings()
        finally:
            s.close()

        self.last_pong = time.time()

    def send_username(self):
        username = "Player"
        for box in arr:
            if box.name == "UsernameInput":
                username = box.get_text()
        if username == "":
            username = "anonymous"
        print("username: ", username)

        connection.Send({
            "action": "set_username",
            "id": self.my_id,
            "username": username
        })

    def send_server_settings(self):
        setting = "1"
        for box in arr:
            if box.name == "Server-Settings-2":
                setting = box.get_text()

        connection.Send({
            "action": "set_server_settings",
            "id": self.my_id,
            "setting": setting
        })

    def Network_init(self, data):
        self.my_id = data["id"]
        print(f"Connected as Player {self.my_id}")

        room_pos = self.client_player.room.pos

        # Preserving position in room between servers
        old_rel_x = data["old_room_rel_pos_x"]
        old_rel_y = data["old_room_rel_pos_y"]
        if old_rel_x is not None:
            self.client_player.pos.x = room_pos.x + old_rel_x
        if old_rel_y is not None:
            self.client_player.pos.y = room_pos.y + old_rel_y

        self.connected = True

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

    def Network_game_end(self, data):
        servermanager.stop()
        self.handle_timeout()
        gs.gamestack.push(gs.s_game_win)

    def Pre_game_pump(self):
        try:
            connection.Pump()
            self.Pump()
            #print("pre pump worked")
        except Exception as e:
            #print("Pre pump error! error msg: " + str(e))
            pass

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
        except ConnectionResetError:
            print("The server closed the connection or is unreachable!")
            self.handle_timeout()

        # TCP Send/Receive
        connection.Pump()
        self.Pump()

        if (time.time() - self.last_pong) > PING_INTERVAL:
            connection.Send({"action": "ping"})

        if (time.time() - self.last_pong) > PING_TIMEOUT:
            print("Ping timeout")
            self.handle_timeout()

    def handle_timeout(self):
        servermanager.stop()
        self.connected = False

        gs.gamestack.push(gs.s_startup)
        gs.s_startup.all_sprites.add(self.connection_lost_header)

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

    def cleanup(self):
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