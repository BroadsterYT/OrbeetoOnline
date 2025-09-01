from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

import time


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
            x=data["x"],
            y=data["y"],
            vel_x=data["vel_x"],
            vel_y=data["vel_y"],
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
        self.next_player_id = 0
        self.next_bullet_id = 0

    def Connected(self, channel, addr):
        # TODO: Allow player ID's to be remembered and removed
        channel.id = self.next_player_id
        self.players[channel.id] = channel
        self.next_player_id += 1
        channel.Send({"action": "init", "id": channel.id})
        print(f"Player {channel.id} connected.")

    def remove_player(self, channel):
        if channel.id in self.players:
            del self.players[channel.id]

    def spawn_bullet(self, owner, x, y, vel_x, vel_y):
        bullet_id = self.next_bullet_id
        self.next_bullet_id += 1

        self.bullets[bullet_id] = {
            "owner": owner,
            "x": x,
            "y": y,
            "vel_x": vel_x,
            "vel_y": vel_y,
            "alive": True,
        }

    def destroy_bullet(self, bullet_id):
        if bullet_id in self.bullets:
            del self.bullets[bullet_id]

            bullet_destroyed = {
                "action": "destroy_bullet",
                "id": bullet_id
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
        for pid, ch in self.players.items():
            state = ch.state
            print(f"Player={pid} | x={state['x']} | y={state['y']}")

        to_destroy = []  # Bullets to destroy after iteration
        for bid, b in self.bullets.items():
            b["x"] += b["vel_x"] * 0.75
            b["y"] += b["vel_y"] * 0.75

        # TODO: Find way to reference room
        # Destroy bullets OOB
            if b["x"] >= 1280 or b["x"] <= 0 or b["y"] >= 720 or b["y"] <= 0:
                to_destroy.append(bid)

        for bullet in to_destroy:
            self.destroy_bullet(bullet)

        for bid, bullet in self.bullets.items():
            print(f"Bullet={bid} | x={bullet['x']} | y={bullet['y']} | vel_x={bullet['vel_x']} | vel_y={bullet['vel_y']}")

        self.broadcast()


if __name__ == "__main__":
    server = OrbeetoServer()
    print(f"Server running on {server.socket.getsockname()}")
    while True:
        server.Pump()
        server.tick()

        time.sleep(0.01)
