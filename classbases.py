"""
Module containing ActorBase and AbstractBase.
"""
import functools
import time

import pygame
from pygame.math import Vector2 as vec

import screen

import calc
import constants as cst
import gamestack as gs
import groups
import spritesheet


def get_room():
    """Returns the room object being used

    Returns:
        Room: The central room object
    """
    return groups.all_rooms[0]


def check_update_state(method):
    """Only runs the given method if the sprite's can_update field is True

    :param method: The method to execute if the update check is successfully passed
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.get_update_state():
            method(self, *args, **kwargs)
    return wrapper


class ActorBase(pygame.sprite.Sprite):
    """The base class for all actors in the game."""
    def __init__(self, layer: int = 1, gamestate: gs.GameState = gs.s_action):
        """The base class for all actors in the game

        :param layer: The layer the sprite should be drawn on
        :param gamestate: The gamestate the sprite should be a part of. Defaults to 'gs.s_action'
        """
        super().__init__()
        self._layer = layer
        self.gamestate = gamestate
        self.in_gamestate = False
        self.visible = True
        self._can_update = True

        self.last_frame = time.time()  # For animation frames

        self.pos = vec(0, 0)
        self.pos_copy = self.pos.copy()  # For adjusting sprites within the scrolling rooms
        self.room_pos = vec(0, 0)  # For maintaining position within a moving room
        
        self.vel = vec(0, 0)
        self.vel_const = vec(0, 0)  # Used for objects moving at a constant velocity
        self.accel = vec(0, 0)
        self.accel_const = 0.58

        self.spritesheet = None
        self.orig_images = []
        self.orig_image = None
        self.images = []
        self.image = None
        self.index = 0

        self.rect = pygame.Rect(0, 0, 64, 64)
        self.hitbox = pygame.Rect(0, 0, 64, 64)

        self.is_grappled = False
        self.grappled_by = None

    # ----------------- Setting properties ----------------- #
    @property
    def layer(self):
        """The layer the sprite should be drawn in. Higher values are drawn on top of lower values."""
        return self._layer

    @layer.setter
    def layer(self, value: int):
        if value > 0:
            self._layer = value
        else:
            raise ValueError(f"ERROR: Assigning layer of value {value} has no effect.")

    @property
    def can_update(self):
        """When true, allows the sprite's update function to be called."""
        return self._can_update

    @can_update.setter
    def can_update(self, value: bool):
        self._can_update = value

    # -------------------------------- Visibility -------------------------------- #
    def add_to_gamestate(self) -> None:
        """Adds the object instance to its game state

        :return: None
        """
        self.gamestate.all_sprites.add(self, layer=self.layer)
        self.in_gamestate = True

    def remove_from_gamestate(self) -> None:
        """Removes the object from its game state

        :return: None
        """
        self.gamestate.all_sprites.remove(self)
        self.in_gamestate = False

    def get_update_state(self) -> bool:
        """Returns the update state of the sprite.

        Returns:
            bool: Whether the sprite can update
        """
        state = True
        if not self.can_update:
            state = False
        return state

    # ----------------------------- Images and Rects ----------------------------- #
    def set_images(self, image_file: str, frame_width: int, frame_height: int, sprites_per_row: int,
                   image_count: int, image_offset: int = 0, index: int = 0) -> None:
        """Initializes the sprite's spritesheet, images, and animations

        :param image_file: The path of the spritesheet image
        :param frame_width: The width of each individual frame
        :param frame_height: The height of each individual frame
        :param sprites_per_row: The number of sprites within each row of the sprite sheet
        :param image_count: The number of images in the sprite's animation
        :param image_offset: The index of the frame to begin the snip from (0 = no offset, use first image)
        :param index: The index of the sprite's animation to start from
        :return: None
        """
        self.spritesheet = spritesheet.Spritesheet(image_file, sprites_per_row)
        self.orig_images = self.spritesheet.get_images(frame_width, frame_height, image_count, image_offset)
        self.images = self.spritesheet.get_images(frame_width, frame_height, image_count, image_offset)
        self.index = index

        self.render_images()

    def render_images(self) -> None:
        """Sets the proper image for the sprite to display.

        Returns:
            None
        """
        self.image = self.images[self.index]
        self.orig_image = self.orig_images[self.index]

    def set_rects(self, rect_pos_x: float, rect_pos_y: float, rect_width: int | float, rect_height: int | float,
                  hitbox_width: int | float, hitbox_height: int | float, set_pos: bool = True) -> None:
        """Initializes the rect and hitbox of a sprite.

        :param rect_pos_x: The x-axis position to spawn the rect and hitbox
        :param rect_pos_y: The y-axis position to spawn the rect and hitbox
        :param rect_width: The width of the rect
        :param rect_height: The height of the rect
        :param hitbox_width: The width of the hitbox
        :param hitbox_height: The height of the hitbox
        :param set_pos: Should the rect and hitbox be snapped to the position of the sprite? Is True by default.
        :return: None
        """
        self.rect = pygame.Rect(rect_pos_x, rect_pos_y, rect_width, rect_height)
        self.hitbox = pygame.Rect(rect_pos_x, rect_pos_y, hitbox_width, hitbox_height)

        if set_pos:
            self.center_rects()

    def rotate_image(self, angle: float) -> None:
        """Rotates the sprite's image by a specific angle

        :param angle: The angle to rotate the sprite's image by
        :return: None
        """
        self.orig_image = self.orig_images[self.index]
        self.image = pygame.transform.rotate(self.orig_image, int(angle))
        self.rect = self.image.get_rect(center=self.rect.center)
    
    # ---------------------------------- Physics --------------------------------- # 
    def center_rects(self) -> None:
        """Sets the ``rect`` and ``hitbox`` of the sprite to its position."""
        self.rect.center = self.pos
        self.hitbox.center = self.pos

    def set_room_pos(self) -> None:
        """Calculates the position of the sprite within its current room and assigns that value to self.room_pos
        """
        room = get_room()
        self.room_pos = vec((self.pos.x - room.pos.x, self.pos.y - room.pos.y))

    def accel_movement(self) -> None:
        """Makes a sprite move according to its acceleration (self.accel and self.accel_const).
        """
        if self.vel.magnitude() > 25:
            self.vel = self.vel.normalize() * 25
        self.accel.x += self.vel.x * cst.FRIC
        self.accel.y += self.vel.y * cst.FRIC
        self.vel += self.accel * (screen.dt * cst.M_FPS)
        self.pos += self.vel * (screen.dt * cst.M_FPS) + self.accel_const * self.accel

        self.center_rects()

    def get_accel(self) -> pygame.math.Vector2:
        """Returns the acceleration the sprite should have. Should be overridden if the sprite requires more
        acceleration than moving within a room.
        """
        room = get_room()
        final_accel = vec(0, 0)
        final_accel += room.get_accel()
        return final_accel

    def collide_check(self, *contact_lists: list) -> None:
        """Check if the sprite comes into contact with another sprite from a specific group.
        If the sprites do collide, then they will perform a hitbox collision.

        :param contact_lists: The sprite group(s) to check for a collision with
        :return: None
        """
        for group in contact_lists:
            for sprite in group:
                if sprite.in_gamestate:
                    self._block_from_side(sprite)

    def _block_from_side(self, sprite) -> None:
        if self.hitbox.colliderect(sprite.hitbox):
            width = (self.hitbox.width + sprite.hitbox.width) // 2
            height = (self.hitbox.height + sprite.hitbox.height) // 2

            # If hitting the right side
            if calc.triangle_collide(self, sprite) == cst.EAST:
                self.vel.x = 0
                self.pos.x = sprite.pos.x + width

            # Hitting bottom side
            if calc.triangle_collide(self, sprite) == cst.SOUTH:
                self.vel.y = 0
                self.pos.y = sprite.pos.y + height

            # Hitting left side
            if calc.triangle_collide(self, sprite) == cst.WEST:
                self.vel.x = 0
                self.pos.x = sprite.pos.x - width

            # Hitting top side
            if calc.triangle_collide(self, sprite) == cst.NORTH:
                self.vel.y = 0
                self.pos.y = sprite.pos.y - height

    def _align_sprite(self, portal_out, offset: float, direction: str) -> None:
        width = (portal_out.hitbox.width + self.hitbox.width) // 2
        height = (portal_out.hitbox.height + self.hitbox.height) // 2

        # Makes sure that sprites don't repeatedly get thrown back into the portals b/c of room velocity
        room = get_room()
        vel_adjust = room.vel.copy()

        if direction == cst.SOUTH:
            self.pos.x = portal_out.pos.x - offset
            self.pos.y = portal_out.pos.y + height + abs(vel_adjust.y)

        elif direction == cst.EAST:
            self.pos.x = portal_out.pos.x + width + abs(vel_adjust.x)
            self.pos.y = portal_out.pos.y - offset

        elif direction == cst.NORTH:
            self.pos.x = portal_out.pos.x + offset
            self.pos.y = portal_out.pos.y - height - abs(vel_adjust.y)

        elif direction == cst.WEST:
            self.pos.x = portal_out.pos.x - width - abs(vel_adjust.x)
            self.pos.y = portal_out.pos.y + offset


class AbstractBase(pygame.sprite.AbstractGroup):
    """The base class for all standard abstract groups. Contains methods to help manipulate the abstract group."""
    def __init__(self, gamestate=gs.s_action):
        super().__init__()
        self.can_update = True
        self.gamestate = gamestate

    def add_to_gamestate(self):
        """Adds the group to its gamestate. NOTE: This method is only intended for associated objects within different
        game states. """
        self.gamestate.groups.append(self)

    def get_update_state(self) -> bool:
        """Returns the update state of the abstract group.

        Returns:
            bool: Whether the abstract group can update
        """
        state = True
        if not self.can_update:
            state = False
        return state


if __name__ == '__main__':
    test = vec(1, 1)
    test += 1
    print(test)
