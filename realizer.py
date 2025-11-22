import classbases as cb
import calc
import os
import constants as cst
import tiles

import text

from pygame.math import Vector2 as vec


class ServerRealizer:
    def __init__(self, client):
        self.room = cb.get_room()
        self.net = client

        self.local_players = {}
        self.local_bullets = {}
        self.local_portals = {}
        self.local_walls = {}

        self.walls = {}

        self.portal_room_offsets = {}

    @staticmethod
    def _create_vessel(
            sprite_path: str,
            sprites_per_row: int,
            num_sprites: int,
            img_offset: int,
            rect_width: int,
            rect_height: int,
            hit_width: int,
            hit_height: int
    ) -> cb.ActorBase:
        """Creates an empty vessel to display on client-side

        :param sprite_path:
        :param sprites_per_row:
        :param num_sprites:
        :param rect_width:
        :param rect_height:
        :param hit_width:
        :param hit_height:
        :return: The created actor
        """
        vessel = cb.ActorBase()

        vessel.add_to_gamestate()
        vessel.set_images(os.path.join(os.getcwd(), sprite_path), rect_width, rect_height, sprites_per_row, num_sprites, img_offset)
        vessel.set_rects(0, 0, rect_width, rect_height, hit_width, hit_height)

        return vessel

    def realize_players(self):
        for pid, player in self.net.players.items():
            if pid not in self.local_players:
                if pid != self.net.my_id:
                    self.local_players[pid] = self._create_vessel(
                        "sprites/orbeeto/orbeeto.png",
                        5,
                        5,
                        0,
                        64,
                        64,
                        32,
                        32
                    )
                    self.local_players[pid].pos = vec(player["x"] + self.room.pos.x, player["y"] + self.room.pos.y)
            else:
                self.local_players[pid].pos = vec(player["x"] + self.room.pos.x, player["y"] + self.room.pos.y)
                self.local_players[pid].render_images()
                self.local_players[pid].center_rects()
            #draws a username label over everyone's character
            if pid != self.net.my_id:
                text.draw_text("Player1", player["x"] + self.room.pos.x - 24, player["y"]  + self.room.pos.y - 60, 18)


        for p_tup in [tup for tup in self.local_players.items() if tup[0] not in self.net.players.keys()]:
            p_tup[1].in_gamestate = False

    def realize_bullets(self):
        for bid, bullet in self.net.bullets.items():
            if bullet["bullet_type"] == "standard":
                if bid not in self.local_bullets:
                    self.local_bullets[bid] = self._create_vessel(
                        "sprites/bullets/bullets.png",
                        8,
                        1,
                        0,
                        32,
                        32,
                        8,
                        8
                    )
                    self.local_bullets[bid].pos = vec(bullet["x"] + self.room.pos.x, bullet["y"] + self.room.pos.y)
                    self.local_bullets[bid].rotate_image(calc.get_vec_angle(bullet["vel_x"], bullet["vel_y"]))
                else:
                    self.local_bullets[bid].pos = vec(bullet["x"] + self.room.pos.x, bullet["y"] + self.room.pos.y)
                    self.local_bullets[bid].rotate_image(calc.get_vec_angle(bullet["vel_x"], bullet["vel_y"]))
                    self.local_bullets[bid].center_rects()

            elif bullet["bullet_type"] == "portal_bullet":
                if bid not in self.local_bullets:
                    self.local_bullets[bid] = self._create_vessel(
                        'sprites/bullets/bullets.png',
                        8,
                        5,
                        8,
                        32,
                        32,
                        8,
                        8
                    )
                    self.local_bullets[bid].pos = vec(bullet["x"] + self.room.pos.x, bullet["y"] + self.room.pos.y)
                    self.local_bullets[bid].rotate_image(calc.get_vec_angle(bullet["vel_x"], bullet["vel_y"]))
                else:
                    self.local_bullets[bid].pos = vec(bullet["x"] + self.room.pos.x, bullet["y"] + self.room.pos.y)
                    self.local_bullets[bid].rotate_image(calc.get_vec_angle(bullet["vel_x"], bullet["vel_y"]))
                    self.local_bullets[bid].center_rects()

        # Destroy realization when server says bullet is dead
        for b_tup in [tup for tup in self.local_bullets.items() if tup[0] not in self.net.bullets.keys()]:
            b_tup[1].remove_from_gamestate()

    def realize_portals(self):
        for pid, portal in self.net.portals.items():
            if pid not in self.local_portals:
                self.local_portals[pid] = self._create_vessel(
                    "sprites/portals/portals.png",
                    8,
                    16,
                    0,
                    64,
                    64,
                    64,
                    64,
                )

                self.local_portals[pid].pos = vec(portal["x"] + self.room.pos.x, portal["y"] + self.room.pos.y)

                if portal["facing"] == cst.EAST or portal["facing"] == cst.WEST:
                    self.local_portals[pid].rotate_image(90)
            else:
                self.local_portals[pid].pos = vec(portal["x"] + self.room.pos.x, portal["y"] + self.room.pos.y)
                self.local_portals[pid].center_rects()

        for p_tup in [tup for tup in self.local_portals.items() if tup[0] not in self.net.portals.keys()]:
            p_tup[1].in_gamestate = False

    def realize_walls(self):
        for wall_id, wall in self.net.walls.items():
            if wall_id not in self.local_walls:
                self.local_walls[wall_id] = tiles.Wall(
                    wall["x"] - wall["hit_w"] // 2,
                    wall["y"] - wall["hit_h"] // 2,
                    wall["hit_w"] // wall["block_width"],
                    wall["hit_h"] // wall["block_height"]
                )

                self.local_walls[wall_id].pos = vec(wall["x"] + self.room.pos.x, wall["y"] + self.room.pos.y)
            else:
                self.local_walls[wall_id].pos = vec(wall["x"] + self.room.pos.x, wall["y"] + self.room.pos.y)
                self.local_walls[wall_id].center_rects()
