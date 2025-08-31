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

    def Close(self):
        self._server.remove_player()


class OrbeetoServer(Server):
    channelClass = PlayerChannel

    def __init__(self, host="localhost", port=12345):
        Server.__init__(self, localaddr=(host, port))
        self.players = {}
        self.next_id = 1

    def Connected(self, channel, addr):
        channel.id = self.next_id
        self.players[channel.id] = channel
        self.next_id += 1
        channel.Send({"action": "init", "id": channel.id})
        print(f"Player {channel.id} connected.")

    def remove_player(self, channel):
        if channel.id in self.players:
            del self.players[channel.id]
            print(f"Player {channel.id} disconnected.")

    def broadcast(self):
        state = {
            "action": "update_state",
            "players": {
                pid: ch.state
                for pid, ch in self.players.items()
            },
        }
        for ch in self.players.values():
            ch.Send(state)

    def tick(self):
        self.broadcast()
        for pid, ch in self.players.items():
            state = ch.state
            print(f"Player={pid} | x={state['x']} | y={state['y']}")


if __name__ == "__main__":
    server = OrbeetoServer()
    print("Server running on localhost:12345")
    while True:
        server.Pump()
        server.tick()
        time.sleep(0.02)
