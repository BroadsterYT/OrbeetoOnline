import pickle

from PodSixNet.Server import Server
from PodSixNet.Channel import Channel
from cv2 import data

from server_rooms import ServerRoom
import calc
import copy
import constants as cst
import socket

import pygame
from pygame.math import Vector2 as vec


class PlayerChannel(Channel):
    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)
        self.id = None
        self.state = {
            "x": 0,
            "y": 0,
            "vel_x": 0,
            "vel_y": 0,
            "hp": 50,
            "hit_w": 32,
            "hit_h": 32,
            "username": None
        }

    def Network_set_username(self, data):
        self.state["username"] = data["username"]

    def Network_ping(self, data):
        self.Send({"action": "pong"})

    def Network_move(self, data):
        if self.state["hp"] > 0:
            self.state["x"] = data["x"]
            self.state["y"] = data["y"]

    def Network_fire(self, data):
        bullet_id = self._server.spawn_bullet(
            owner=self.id,
            bullet_type=data["bullet_type"],
            x=data["x"],
            y=data["y"],
            vel_x=data["vel_x"],
            vel_y=data["vel_y"],
            hit_w=data["hit_w"],
            hit_h=data["hit_h"],
        )
        return bullet_id

    def Close(self):
        print(f"Player {self.id} disconnected.")
        self._server.remove_player(self)


class OrbeetoServer(Server):
    channelClass = PlayerChannel

    def __init__(self, host="0.0.0.0", port=12345):
        Server.__init__(self, localaddr=(host, port))
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind((host, port))
        self.udp_socket.setblocking(False)

        self.players = {}
        self.bullets = {}
        self.walls = {}
        self.portals = {}

        self.next_player_id = 0
        self.next_bullet_id = 0
        self.next_portal_id = 0

        self.current_room = vec(0, 0)
        self._build_room(0, 0)

    def Connected(self, channel, addr):
        # TODO: Allow player ID's to be remembered and removed
        channel.id = self.next_player_id
        self.players[channel.id] = channel
        self.next_player_id += 1
        channel.Send({"action": "init", "id": channel.id})
        print(f"Player {channel.id} connected.")

    def _build_room(self, room_x, room_y):
        self.walls.clear()

        self.walls = {
            ServerRoom.get_next_wall_id(): ServerRoom.new_wall(0, 0, 16, 16, 4, 41),
            ServerRoom.get_next_wall_id(): ServerRoom.new_wall(256, 256, 16, 16, 16, 16)
        }

    def remove_player(self, channel):
        if channel.id in self.players:
            del self.players[channel.id]

    def spawn_bullet(self, owner, bullet_type: str, x, y, vel_x, vel_y, hit_w: int, hit_h: int):
        bullet_id = self.next_bullet_id
        self.next_bullet_id += 1

        self.bullets[bullet_id] = {
            "owner": owner,
            "bullet_type": bullet_type,
            "x": x,
            "y": y,
            "vel_x": vel_x,
            "vel_y": vel_y,
            "hit_w": hit_w,
            "hit_h": hit_h,
            "alive": True,
        }

    def destroy_bullet(self, bullet_id):
        if bullet_id in self.bullets:
            del self.bullets[bullet_id]

            bullet_destroyed = {
                "action": "destroy_bullet",
                "id": bullet_id,
            }

            for client in self.players.values():
                client.Send(bullet_destroyed)

    def spawn_portal(self, owner, landed_on_data, facing, bullet_x, bullet_y):
        portal_id = self.next_portal_id
        self.next_portal_id += 1

        true_x = bullet_x
        true_y = bullet_y
        hit_width = 54
        hit_height = 20

        if facing == cst.SOUTH:
            true_y = landed_on_data["y"] + landed_on_data["hit_h"] // 2
        elif facing == cst.EAST:
            true_x = landed_on_data["x"] + landed_on_data["hit_w"] // 2
            hit_width = 20
            hit_height = 54
        elif facing == cst.NORTH:
            true_y = landed_on_data["y"] - landed_on_data["hit_h"] // 2
        elif facing == cst.WEST:
            true_x = landed_on_data["x"] - landed_on_data["hit_w"] // 2
            hit_width = 20
            hit_height = 54

        offset_x = true_x - landed_on_data["x"]
        offset_y = true_y - landed_on_data["y"]

        self.portals[portal_id] = {
            "owner": owner,
            "landed_on": landed_on_data,
            "facing": facing,
            "x": true_x,
            "y": true_y,
            "offset_x": offset_x,
            "offset_y": offset_y,
            "hit_w": hit_width,
            "hit_h": hit_height,
            "linked_to": None
        }

        # TODO: Scan list after spawning portal to link portals
        found = []
        for pid, portal in [tup for tup in self.portals.items() if tup[1]["owner"] == owner]:
            found.append(pid)

        if len(found) > 2:
            pid_to_del = min(found)
            del found[found.index(pid_to_del)]
            self.destroy_portal(pid_to_del)

            new_link1 = found[0]
            new_link2 = found[1]
            print(f"New oldest: {new_link1} | Newest: {new_link2}")

            self.portals[new_link1]["linked_to"] = new_link2
            self.portals[new_link2]["linked_to"] = new_link1
            return

        if len(found) == 2:
            new_link1 = found[0]
            new_link2 = found[1]

            self.portals[new_link1]["linked_to"] = new_link2
            self.portals[new_link2]["linked_to"] = new_link1
            return

    def destroy_portal(self, portal_id):
        if portal_id in self.portals:
            del self.portals[portal_id]

    def broadcast(self):
        players_state = {
            "action": "update_players",
            "players": {
                pid: ch.state
                for pid, ch in self.players.items()
            },
        }
        bullets_state = {
            "action": "update_bullets",
            "bullets": {
                bid: bullet
                for bid, bullet in self.bullets.items()
            }
        }
        portals_state = {
            "action": "update_portals",
            "portals": {
                portal_id: portal
                for portal_id, portal in self.portals.items()
            }
        }
        walls_state = {
            "action": "update_walls",
            "walls": {
                wall_id: wall
                for wall_id, wall in self.walls.items()
            }
        }

        for client in self.players.values():
            client.Send(players_state)
            client.Send(bullets_state)
            client.Send(portals_state)
            client.Send(walls_state)

    def tick(self):
        # UDP Sending/Receiving
        try:
            data, addr = self.udp_socket.recvfrom(1024)
            dec_data = pickle.loads(data)

            match dec_data["action"]:
                case "udp_request":
                    print(f"UDP request received from {addr}")

                case "fire":
                    self.spawn_bullet(
                        owner=0,
                        bullet_type=dec_data["bullet_type"],
                        x=dec_data["x"],
                        y=dec_data["y"],
                        vel_x=dec_data["vel_x"],
                        vel_y=dec_data["vel_y"],
                        hit_w=dec_data["hit_w"],
                        hit_h=dec_data["hit_h"],
                    )

                case _:
                    pass

        except BlockingIOError:
            pass

        # TCP Sending/Receiving
        for pid, ch in self.players.items():
            self._handle_player_teleport(pid, ch.state)

        to_destroy = []  # Bullets to destroy after iteration
        for bid, b in self.bullets.items():
            b["x"] += b["vel_x"] * 0.75
            b["y"] += b["vel_y"] * 0.75

            self._handle_bullets_through_portals(b)
            self._handle_player_hit(b, bid, to_destroy)

            wall_coll_result = self._handle_bullet_wall_collision(bid, b, to_destroy)
            if wall_coll_result is not None:
                side_hit, data_hit = wall_coll_result
                # TODO: Spawn bullet shatter on client side

            # TODO: Find way to reference room
            # Destroy bullets OOB
            if b["x"] >= 1280 or b["x"] <= 0 or b["y"] >= 720 or b["y"] <= 0:
                to_destroy.append(bid)

        for bullet in to_destroy:
            self.destroy_bullet(bullet)

        # Updating Portals
        for portal_id, portal in self.portals.items():
            portal["x"] = portal["landed_on"]["x"] + portal["offset_x"]
            portal["y"] = portal["landed_on"]["y"] + portal["offset_y"]

        self.broadcast()

    def _handle_player_teleport(self, player_id, player):
        player_hitbox = pygame.Rect(
            player["x"] - player["hit_w"] // 2,
            player["y"] - player["hit_h"] // 2,
            player["hit_w"],
            player["hit_h"]
        )

        for portal_id, portal in self.portals.items():
            portal_hitbox = pygame.Rect(
                portal["x"] - portal["hit_w"] // 2,
                portal["y"] - portal["hit_h"] // 2,
                portal["hit_w"],
                portal["hit_h"]
            )

            if not player_hitbox.colliderect(portal_hitbox):
                continue

            if portal["linked_to"] is None:
                # print("No connecting portal")
                continue

            client = self.players[player_id]
            client.Send({
                "action": "teleport_player",
                "player_id": player_id,
                "portal_out_id": portal["linked_to"],
            })

    def _handle_player_hit(self, b_data, bid, to_destroy):
        bullet_hitbox = pygame.Rect(
            b_data["x"] - b_data["hit_w"] // 2,
            b_data["y"] - b_data["hit_h"] // 2,
            b_data["hit_w"],
            b_data["hit_h"]
        )

        for pid, ch in self.players.items():
            player = ch.state

            player_hitbox = pygame.Rect(
                player["x"] - player["hit_w"] // 2,
                player["y"] - player["hit_h"] // 2,
                player["hit_w"],
                player["hit_h"]
            )

            if not bullet_hitbox.colliderect(player_hitbox):
                continue

            # Intentional: let players take damage from own bullets
            if b_data["bullet_type"] != "portal_bullet":
                player["hp"] -= 1
                to_destroy.append(bid)

    def _handle_bullets_through_portals(self, b_data):
        bullet_hitbox = pygame.Rect(
            b_data["x"] - b_data["hit_w"] // 2,
            b_data["y"] - b_data["hit_h"] // 2,
            b_data["hit_w"],
            b_data["hit_h"]
        )

        for portal_id, portal in self.portals.items():
            portal_hitbox = pygame.Rect(
                portal["x"] - portal["hit_w"] // 2,
                portal["y"] - portal["hit_h"] // 2,
                portal["hit_w"],
                portal["hit_h"]
            )

            if not bullet_hitbox.colliderect(portal_hitbox):
                continue

            if portal["linked_to"] is None:
                # print("No connecting portal")
                continue

            other_portal = self.portals[portal["linked_to"]]
            dir_in = portal["facing"]
            dir_out = other_portal["facing"]

            dist_offset = copy.copy(b_data["x"]) - copy.copy(portal["x"])
            dir_list = {cst.SOUTH: 180, cst.EAST: 90, cst.NORTH: 0, cst.WEST: 270}

            if dir_in == cst.EAST:
                dir_list.update({cst.EAST: 180, cst.NORTH: 90, cst.WEST: 0, cst.SOUTH: 270})
                dist_offset = copy.copy(b_data["y"]) - copy.copy(portal["y"])
            elif dir_in == cst.NORTH:
                dir_list.update({cst.NORTH: 180, cst.WEST: 90, cst.SOUTH: 0, cst.EAST: 270})
            elif dir_in == cst.WEST:
                dir_list.update({cst.WEST: 180, cst.SOUTH: 90, cst.EAST: 0, cst.NORTH: 270})
                dist_offset = copy.copy(b_data["y"]) - copy.copy(portal["y"])

            # Aligning sprite at other portal
            out_width = (other_portal["hit_w"] + b_data["hit_w"]) // 2
            out_height = (other_portal["hit_h"] + b_data["hit_h"]) // 2

            if dir_out == cst.SOUTH:
                b_data["x"] = other_portal["x"] - dist_offset
                b_data["y"] = other_portal["y"] + out_height
            elif dir_out == cst.EAST:
                b_data["x"] = other_portal["x"] + out_width
                b_data["y"] = other_portal["y"] - dist_offset
            elif dir_out == cst.NORTH:
                b_data["x"] = other_portal["x"] + dist_offset
                b_data["y"] = other_portal["y"] - out_height
            elif dir_out == cst.WEST:
                b_data["x"] = other_portal["x"] - out_width
                b_data["y"] = other_portal["y"] + dist_offset

            current_bullet_vel = vec(b_data["vel_x"], b_data["vel_y"])
            new_bullet_vel = current_bullet_vel.rotate(dir_list[dir_out])
            b_data["vel_x"] = new_bullet_vel.x
            b_data["vel_y"] = new_bullet_vel.y

    def _handle_bullet_wall_collision(self, bid: int, b_data: dict[str, any], destroy_list: list[int]):
        """Handles collisions between bullets and walls.

        :param b_data: Bullet data being evaluated
        :param destroy_list: A list containing all bullet IDs to be deleted after iterating all bullets
        :return: The side the bullet hit a wall and the wall object data
        """
        bullet_hitbox = pygame.Rect(
            b_data["x"] - b_data["hit_w"] // 2,
            b_data["y"] - b_data["hit_h"] // 2,
            b_data["hit_w"],
            b_data["hit_h"]
        )

        for wall_id, wall in self.walls.items():
            wall_width = wall["width"] * wall["block_width"]
            wall_height = wall["height"] * wall["block_height"]
            wall_hitbox = pygame.Rect(
                wall["x"] - wall_width // 2,
                wall["y"] - wall_height // 2,
                wall_width,
                wall_height
            )

            if not bullet_hitbox.colliderect(wall_hitbox):
                continue

            instig_vec = vec(b_data["x"], b_data["y"])
            wall_vec = vec(wall["x"], wall["y"])
            wall_hit = vec(wall_width, wall_height)
            side = calc.triangle_collide(instig_vec, wall_vec, wall_hit)

            if b_data["bullet_type"] == "standard":
                destroy_list.append(bid)
            elif b_data["bullet_type"] == "portal_bullet":
                destroy_list.append(bid)
                self.spawn_portal(b_data["owner"], wall, side, b_data["x"], b_data["y"])

            return side, wall


if __name__ == "__main__":
    import time

    server = OrbeetoServer()
    print(f"Server running on {server.socket.getsockname()}")
    while True:
        server.tick()
        server.Pump()

        time.sleep(0.01)
