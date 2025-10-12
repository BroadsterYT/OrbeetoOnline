from server_rooms import ServerRoom
import calc
import copy
import constants as cst
import msgpack
import socket

import pygame
from pygame.math import Vector2 as vec


class OrbeetoServer:
    def __init__(self, host="0.0.0.0", port=12345):
        # Server IP MUST BE 0.0.0.0! localhost and 127.0.0.1 are not sufficient
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((host, port))
        self.udp_socket.setblocking(False)

        self.players: dict[tuple[str, int]: float] = {}

        self.bullets = {}
        self.bullet_deltas = {}

        self.portals = {}
        self.walls = {}

        self.player_pings = {}

        self.next_bullet_id = 0
        self.next_portal_id = 0

        self.current_room = vec(0, 0)
        self._build_room(0, 0)

    # ========== Basic Server UDP Behavior ========== #
    def _send_data_to_client(self, data: dict, addr: tuple[str, int]) -> None:
        """Send data (a dictionary) to a client at a specified address

        :param data: The data to send to the client
        :param addr: The address of the client (IP address, port)
        :return: None
        """
        packed_data = msgpack.packb(data, use_bin_type=True)
        self.udp_socket.sendto(packed_data, addr)

    def _acknowledge_client(self, addr: tuple[str, int]) -> None:
        """Acknowledges a client's connection to the server and marks them as able to receive server updates. This
        creates a player object representation on the server

        :param addr: The IP address/port to acknowledge
        :return: None
        """
        ip, port = addr

        old_clients = [a for a in self.players if a[0] == ip and a != addr]
        for old_addr in old_clients:
            self.players.pop(old_addr, None)
            self.player_pings.pop(old_addr, None)

        self.players.update({addr: {
            "x": 0,
            "y": 0,
            "hit_w": 32,
            "hit_h": 32,
            "angle": 0,
            "hp": 50
        }
        })
        self.player_pings.update({addr: time.time()})
        print(f"Acknowledge client using {addr}")

    def _send_client_connection_acknowledgement(self, addr: tuple[str, int]) -> None:
        """Sends a message to a client stating that it has been acknowledged on the server

        :param addr: The client IP address/port that was acknowledged
        :return: None
        """
        ack = {"action": "server_acknowledgement"}
        self._send_data_to_client(ack, addr)
        print(f"Server acknowledgement sent to {addr}")

    def _check_client_pings(self) -> None:
        """Checks if a client has not pinged and is removed if the timeout is exceeded

        :return: None
        """
        to_disconnect = []
        for addr, player in self.players.items():
            if time.time() - self.player_pings[addr] > 5:
                to_disconnect.append(addr)

        # print(to_disconnect)
        for addr in to_disconnect:
            self.players.pop(addr)
            self.player_pings.pop(addr)
            print(f"Client using {addr} has not pinged and has been removed.")

    def _send_client_pong(self, addr: tuple[str, int]) -> None:
        """Sends a client a ping response

        :param addr: The client address to send the response to
        :return: None
        """
        response = {
            "action": "server_pong"
        }
        self._send_data_to_client(response, addr)

    # ========== Game Messages for Clients ========== #
    def _send_bullet_updates(self):
        updates = {
            "action": "update_bullets",
            "deltas": {
                str(bid): {"x": b["x"], "y": b["y"]}
                for bid, b in self.bullet_deltas.items()
            }
        }
        for addr in self.players:
            self._send_data_to_client(updates, addr)

    def tick(self) -> None:
        """Performs an iteration of the server's main loop

        :return: None
        """
        self._check_client_pings()

        try:
            while True:
                self._handle_incoming_data()
        except BlockingIOError:
            pass
        except ConnectionResetError:
            return

        self._update_bullets()
        self._send_bullet_updates()

        for addr, player in self.players.items():
            self._handle_player_teleport(addr)

            walls = {
                "action": "update_walls",
                "walls": {
                    str(wall_id): wall
                    for wall_id, wall in self.walls.items()
                }
            }
            self._send_data_to_client(walls, addr)

            portals = {
                "action": "update_portals",
                "portals": {
                    str(portal_id): portal
                    for portal_id, portal in self.portals.items()
                }
            }
            self._send_data_to_client(portals, addr)

    def _handle_incoming_data(self) -> None:
        """Performs actions given incoming client messages

        :return: None
        """
        raw_data, addr = self.udp_socket.recvfrom(4096)
        data = msgpack.unpackb(raw_data, raw=False)

        match data["action"]:
            case "connection_request":
                self._acknowledge_client(addr)
                self._send_client_connection_acknowledgement(addr)
            case "player_ping":
                self.player_pings[addr] = time.time()
                self._send_client_pong(addr)

            case "player_move":
                self.players[addr]["x"] = data["x"]
                self.players[addr]["y"] = data["y"]
                self.players[addr]["angle"] = data["angle"]
            case "player_fire":
                print(f"Player {addr} fired")
                self._spawn_bullet(
                    addr,
                    data["bullet_type"],
                    data["x"],
                    data["y"],
                    data["vel_x"],
                    data["vel_y"],
                    data["hit_w"],
                    data["hit_h"],
                )
            case _:
                pass

    # ========== Server-Side Game Operation ========= #
    def _build_room(self, room_x: int, room_y: int) -> None:
        """Creates all the walls of the room

        :param room_x: The x-axis coordinate of the room in the plane of all rooms
        :param room_y: The y-axis coordinate of the room in the plane of all rooms
        :return:
        """
        self.walls.clear()
        self.walls = {
            ServerRoom.get_next_wall_id(): ServerRoom.new_wall(0, 0, 16, 16, 4, 41),
            ServerRoom.get_next_wall_id(): ServerRoom.new_wall(256, 256, 16, 16, 16, 16)
        }

    def _update_bullets(self) -> None:
        """Updates all bullets on server-side

        :return: None
        """
        to_destroy = []  # Bullets to destroy after iteration
        for bid, b in self.bullets.items():
            b["x"] += b["vel_x"] * 0.75
            b["y"] += b["vel_y"] * 0.75
            self.bullet_deltas[bid] = {"x": b["x"], "y": b["y"]}

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
            self._destroy_bullet(bullet)

    def _spawn_bullet(self, owner: tuple[str, int], bullet_type: str, x, y, vel_x, vel_y, hit_w: int, hit_h: int):
        """Spawns a bullet on the server

        :param owner: The address of the client that shot the bullet (IP address, port)
        :param bullet_type: The type of bullet to spawn
        :param x: The x-axis position to spawn the bullet
        :param y: The y-axis position to spawn the bullet
        :param vel_x: The x-axis velocity the bullet should have
        :param vel_y: The y-axis velocity the bullet should have
        :param hit_w: The width the bullet's hitbox should have
        :param hit_h: The height the bullet's hitbox should have
        :return: None
        """
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
        }
        self.bullet_deltas[bullet_id] = (0, 0)

        for addr in self.players:
            bullet_spawn = {
                "action": "bullet_spawn",
                "id": bullet_id,
                "bullet": self.bullets[bullet_id]
            }
            self._send_data_to_client(bullet_spawn, addr)

    def _destroy_bullet(self, bullet_id):
        if bullet_id in self.bullets:
            del self.bullets[bullet_id]

            bullet_destroyed = {
                "action": "destroy_bullet",
                "id": bullet_id,
            }
            for addr in self.players:
                self._send_data_to_client(bullet_destroyed, addr)
        if bullet_id in self.bullet_deltas:
            del self.bullet_deltas[bullet_id]

    def _spawn_portal(self, owner: tuple[str, int], landed_on_data, facing: str, bullet_x: float, bullet_y: float):
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
            self._destroy_portal(pid_to_del)

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

    def _destroy_portal(self, portal_id):
        if portal_id in self.portals:
            del self.portals[portal_id]

    #
    # def broadcast(self):
    #     players_state = {
    #         "action": "update_players",
    #         "players": {
    #             pid: ch.state
    #             for pid, ch in self.players.items()
    #         },
    #     }
    #     bullets_state = {
    #         "action": "update_bullets",
    #         "bullets": {
    #             bid: bullet
    #             for bid, bullet in self.bullets.items()
    #         }
    #     }
    #     portals_state = {
    #         "action": "update_portals",
    #         "portals": {
    #             portal_id: portal
    #             for portal_id, portal in self.portals.items()
    #         }
    #     }
    #     walls_state = {
    #         "action": "update_walls",
    #         "walls": {
    #             wall_id: wall
    #             for wall_id, wall in self.walls.items()
    #         }
    #     }
    #
    #     for client in self.players.values():
    #         client.Send(players_state)
    #         client.Send(bullets_state)
    #         client.Send(portals_state)
    #         client.Send(walls_state)
    #
    # def tick(self):
    #     # UDP Sending/Receiving
    #     try:
    #         data, addr = self.udp_socket.recvfrom(1024)
    #         dec_data = pickle.loads(data)
    #
    #         match dec_data["action"]:
    #             case "udp_request":
    #                 print(f"UDP request received from {addr}")
    #
    #             case "fire":
    #                 self.spawn_bullet(
    #                     owner=0,
    #                     bullet_type=dec_data["bullet_type"],
    #                     x=dec_data["x"],
    #                     y=dec_data["y"],
    #                     vel_x=dec_data["vel_x"],
    #                     vel_y=dec_data["vel_y"],
    #                     hit_w=dec_data["hit_w"],
    #                     hit_h=dec_data["hit_h"],
    #                 )
    #
    #             case _:
    #                 pass
    #
    #     except BlockingIOError:
    #         pass
    #
    #     # TCP Sending/Receiving
    #     for pid, ch in self.players.items():
    #         self._handle_player_teleport(pid, ch.state)
    #
    #
    #     # Updating Portals
    #     for portal_id, portal in self.portals.items():
    #         portal["x"] = portal["landed_on"]["x"] + portal["offset_x"]
    #         portal["y"] = portal["landed_on"]["y"] + portal["offset_y"]
    #
    #     self.broadcast()
    #
    def _handle_player_teleport(self, addr):
        player = self.players[addr]
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

            tp_data = {
                "action": "teleport_player",
                "portal_out_id": portal["linked_to"]
            }
            self._send_data_to_client(tp_data, addr)

    def _handle_player_hit(self, b_data, bid, to_destroy):
        bullet_hitbox = pygame.Rect(
            b_data["x"] - b_data["hit_w"] // 2,
            b_data["y"] - b_data["hit_h"] // 2,
            b_data["hit_w"],
            b_data["hit_h"]
        )

        for addr, player in self.players.items():
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
                self._spawn_portal(b_data["owner"], wall, side, b_data["x"], b_data["y"])

            return side, wall


if __name__ == "__main__":
    import time

    server = OrbeetoServer()

    while True:
        start = time.time()
        server.tick()
        elapsed = time.time() - start
        time.sleep(max(1 / 60, elapsed))
