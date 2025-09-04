"""

"""


class ServerRoom:
    next_wall_id = -1

    def __init__(self):
        pass

    @staticmethod
    def new_wall(pos_x: float, pos_y: float, block_width: int, block_height: int, width: int, height: int) -> dict[str, float | int]:
        """Creates a wall object for the server to interpret

        :param pos_x:
        :param pos_y:
        :param block_width:
        :param block_height:
        :param width:
        :param height:
        :return:
        """
        true_x = pos_x + (width * block_width) // 2
        true_y = pos_y + (height * block_height) // 2

        wall = {
            "x": true_x,
            "y": true_y,
            "block_width": block_width,
            "block_height": block_height,
            "width": width,
            "height": height
        }
        return wall

    @staticmethod
    def get_next_wall_id():
        ServerRoom.next_wall_id += 1
        return ServerRoom.next_wall_id
