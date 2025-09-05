from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

from server_rooms import ServerRoom
import calc
import constants as cst

import pygame
from pygame.math import Vector2 as vec


class PlayerChannel(Channel):
    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)
        self.id = None
        self.state = {"x": 0, "y": 0, "hp": 50}

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
        self.players = {}
        self.bullets = {}
        self.walls = {}
        self.next_player_id = 0
        self.next_bullet_id = 0

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
            ServerRoom.get_next_wall_id(): ServerRoom.new_wall(0, 0, 16, 16, 4, 41)
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

    def broadcast(self):
        players_state = {
            "action": "update_state",
            "players": {
                pid: ch.state
                for pid, ch in self.players.items()
            },
        }
        for ch in self.players.values():
            ch.Send(players_state)

        bullets_state = {
            "action": "update_bullets",
            "bullets": {
                bid: bullet
                for bid, bullet in self.bullets.items()
            }
        }

        for client in self.players.values():
            client.Send(bullets_state)

    def tick(self):
        to_destroy = []  # Bullets to destroy after iteration
        for bid, b in self.bullets.items():
            b["x"] += b["vel_x"] * 0.75
            b["y"] += b["vel_y"] * 0.75

            result = self._handle_bullet_wall_collision(bid, b, to_destroy)
            if result is not None:
                side_hit, data_hit = result
                print(f"Side Hit: {side_hit} | Object Hit: {data_hit}")

            # TODO: Find way to reference room
            # Destroy bullets OOB
            if b["x"] >= 1280 or b["x"] <= 0 or b["y"] >= 720 or b["y"] <= 0:
                to_destroy.append(bid)

        for bullet in to_destroy:
            self.destroy_bullet(bullet)

        self.broadcast()

    def _handle_bullet_wall_collision(self, bid: int, b_data: dict[str, any], destroy_list: list[int]):
        """

        :param b_data: Bullet data being evaluated
        :param destroy_list: A list containing all bullet IDs to be deleted after iterating all bullets
        :return:
        """
        if b_data["bullet_type"] == "portal_bullet":
            return

        for wall_id, wall in self.walls.items():
            bullet_hitbox = pygame.Rect(
                b_data["x"] - b_data["hit_w"] // 2,
                b_data["y"] - b_data["hit_h"] // 2,
                b_data["hit_w"],
                b_data["hit_h"]
            )

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

            destroy_list.append(bid)
            return side, wall




if __name__ == "__main__":
    import time

    server = OrbeetoServer()
    print(f"Server running on {server.socket.getsockname()}")
    while True:
        server.Pump()
        server.tick()

        time.sleep(0.01)
