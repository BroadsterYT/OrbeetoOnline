"""Main program. Contains the game loop."""
import asyncio
import os
import sys
import time

import pygame
from pygame.locals import QUIT

import controls as ctrl
import menus
import screen
import text

import constants as cst
import gamestack as gs
import rooms
import visuals
from gamestack import s_server_settings

from menus.StartUpmenu import Header
from servermanager import servermanager
from menus.menuinputbars import arr

pygame.init()
pygame.display.set_caption('Orbeeto')
pygame.display.set_icon(pygame.image.load(os.path.join(os.getcwd(), 'other/orbeeto.png')))

screen.buffer_screen = pygame.Surface((cst.WINWIDTH, cst.WINHEIGHT))
screen.viewport = pygame.display.set_mode((cst.WINWIDTH, cst.WINHEIGHT),
                                           pygame.HWSURFACE | pygame.SCALED | pygame.DOUBLEBUF)


def redraw_game_window() -> None:
    """Draws all sprites onto the screen

    Returns:
        None
    """
    gs.gamestack.update()
    screen.viewport.blit(screen.buffer_screen, visuals.screen_shake_queue.run())
    pygame.display.flip()

    screen.buffer_screen.fill((0, 255, 255))


main_room = rooms.Room(0, 0)
gs.s_action.groups.append(main_room)


def join_game_window() -> None:
    global join_count
    global main_room

    main_room.player1.net.server_address = (main_room.player1.get_ip_input(), 12345)
    print(f"IP input: {main_room.player1.get_ip_input()}")
    main_room.player1.net.establish_connection()

    join_count = True
    gs.gamestack.pop()
    gs.gamestack.pop()
    gs.gamestack.pop()


# Start up menu
header = Header("Welcome to Orbeeto!", pos=(cst.WINWIDTH // 2 - 260, 180), color=(0, 130, 0))
message = Header("press 'Esc' for settings", pos=(cst.WINWIDTH // 2 - 120, 250), font_size=30, color=(250, 0, 0))
PlayGame_button = menus.MenuButton(gs.s_startup, cst.WINWIDTH // 2, 475, 286, 32, 'Play Game',
                                   lambda: gs.gamestack.push(gs.s_join_game))
end_game_button = menus.MenuButton(gs.s_startup, cst.WINWIDTH // 2, 550, 322, 32, 'Leave Game',
                                            sys.exit)
gs.s_startup.all_sprites.add(header, message)

# join local or create game menu
join_local_Game_button = menus.MenuButton(gs.s_join_game, cst.WINWIDTH // 2, 475, 500, 32, 'Join Local Game',
                                          lambda: gs.gamestack.push(gs.s_join_local_game))
create_local_Game_button = menus.MenuButton(gs.s_join_game, cst.WINWIDTH // 2, 400, 550, 32, 'Create Local Game',
                                            gs.gamestack.push, s_server_settings)
Join_game_back_button = menus.MenuButton(gs.s_join_game, cst.WINWIDTH // 2, 550, 130, 32, 'Back',
                                         gs.gamestack.pop)


#join local game
join_game_header = Header("Join locally hosted Game", pos=(cst.WINWIDTH // 2 - 230, 200), font_size=55, color=(250, 0, 0))
IPAddress_header = Header("Host IP Address:", pos=(cst.WINWIDTH // 2 - 150, 300), font_size=30, color=(0, 0, 100))
input_box_IP = menus.InputBox(gs.s_join_local_game, cst.WINWIDTH // 2 - 150, 320, 300, 35, 'IPAddressInput')
Username_header = Header("Username:", pos=(cst.WINWIDTH // 2 - 150, 380), font_size=30, color=(0, 0, 100))
input_box_username = menus.InputBox(gs.s_join_local_game, cst.WINWIDTH // 2 - 150, 400, 300, 35, 'UsernameInput')
join_game_button = menus.MenuButton(gs.s_join_local_game, cst.WINWIDTH // 2, 500, 130, 32, 'Join',
                                                join_game_window)
join_local_game_back_button = menus.MenuButton(gs.s_join_local_game, cst.WINWIDTH // 2, 550, 130, 32, 'Back',
                                         gs.gamestack.pop)

gs.s_join_local_game.all_sprites.add(join_game_header, IPAddress_header, Username_header)


#leaving the game confirmation window
quit_return_button = menus.MenuButton(gs.s_confirm_quit, cst.WINWIDTH // 2, cst.WINHEIGHT // (11/8), 190, 32, 'Return',
                                                 gs.gamestack.replace, gs.s_confirm_quit, gs.s_pause)

confirm_quit_button = menus.MenuButton(gs.s_confirm_quit, cst.WINWIDTH // 2, cst.WINHEIGHT // (5/4), 126, 32, 'Quit', sys.exit)
quit_game_header = Header("Are you sure you want to leave?", pos=(cst.WINWIDTH // 2 - 310, 250), font_size=60, color=(250, 0, 0))

gs.s_confirm_quit.all_sprites.add(quit_game_header)

# server settings submenue
def start_server():
    servermanager.start()
    gs.gamestack.pop()

server_settings_header = Header("Server settings", pos=(cst.WINWIDTH // 2 - 145, 150), font_size=55, color=(250, 0, 0))

server_settings_1_header = Header("Game duration (in min):", pos=(cst.WINWIDTH // 2 - 165, 280), font_size=30, color=(0, 0, 100))
server_settings_1_input_box = menus.InputBox(gs.s_server_settings, cst.WINWIDTH // 2 - 150, 300, 300, 35, 'Server-Settings-1', 2)

server_settings_2_header = Header("Max num of players:", pos=(cst.WINWIDTH // 2 - 165, 360), font_size=30, color=(0, 0, 100))
server_settings_2_input_box = menus.InputBox(gs.s_server_settings, cst.WINWIDTH // 2 - 150, 380, 300, 35, 'Server-Settings-2', 1)

server_settings_3_header = Header("Something:", pos=(cst.WINWIDTH // 2 - 165, 440), font_size=30, color=(0, 0, 100))
server_settings_3_input_box = menus.InputBox(gs.s_server_settings, cst.WINWIDTH // 2 - 150, 460, 300, 35, 'Server-Settings-3')

start_server = menus.MenuButton(gs.s_server_settings, cst.WINWIDTH // 2, 575, 380, 32, 'Start Server',
                                            start_server)
server_settings_return_button = menus.MenuButton(gs.s_server_settings, cst.WINWIDTH // 2, 630, 200, 32, 'Return',
                                            gs.gamestack.pop)
gs.s_server_settings.all_sprites.add(server_settings_header, server_settings_1_header, server_settings_2_header, server_settings_3_header)
# Pause menu
pause_menu = menus.PauseMenu()
pause_menu.net_ref = main_room.player1.net
pause_release = 0


prev_time = time.time()  # Used for delta time


async def main(max_frame_rate) -> None:
    """The main loop of the program.

    :param max_frame_rate: The maximum framerate the game should run at
    :return: None
    """
    loop = asyncio.get_event_loop()
    next_frame_target = 0.0
    sec_per_frame = 1 / max_frame_rate

    running = True
    while running:
        # print(ctrl.is_input_held[4], ctrl.is_input_held[5])

        if sec_per_frame:
            # Framerate limiter
            delay = next_frame_target - time.time()
            if delay > 0:
                await asyncio.sleep(delay)
            next_frame_target = time.time() + sec_per_frame

        # Delta time
        global prev_time
        now = time.time()
        screen.dt = now - prev_time
        prev_time = now

        # ----- Opening and closing pause menu ----- #
        global pause_release
        if pause_release == ctrl.key_released[ctrl.K_PAUSE] - 1 and not pause_menu.is_open:
            gs.gamestack.push(gs.s_pause)
            pause_release = ctrl.key_released[ctrl.K_PAUSE]
            pause_menu.is_open = True

        elif pause_release == ctrl.key_released[ctrl.K_PAUSE] - 1 and pause_menu.is_open and gs.s_pause in gs.gamestack.stack:
            gs.gamestack.pop()
            pause_release = ctrl.key_released[ctrl.K_PAUSE]
            pause_menu.is_open = False

        elif pause_menu.is_open and gs.s_pause not in gs.gamestack.stack:
            pause_release = ctrl.key_released[ctrl.K_PAUSE]
            pause_menu.is_open = False
        pause_menu.update()

        # Draw framerate on screen
        try:
            text.draw_text(f'{pow(screen.dt, -1)}', 0, 0)
        except ZeroDivisionError:
            pass

        #player name label
        """
        if gs.gamestack.stack[-1] == gs.s_action:
            for box in arr:
                if box.name == 'UsernameInput':
                    username = box.get_text()
                    #text.draw_text(username, player.pos.x, player.pos.y - 65, 18)
                    #text.draw_text(username, cst.WINWIDTH // 2 - 24, cst.WINHEIGHT //2 - 65, 18)
        """

        # ---------- Mouse Inputs ---------- #
        if ctrl.is_input_held[1] and ctrl.release_check:
            ctrl.last_click_pos = [pygame.mouse.get_pos(), gs.gamestack.stack[-1]]
            ctrl.release_check = False

        if ctrl.last_release_count < ctrl.key_released[1]:
            ctrl.last_release_pos = [pygame.mouse.get_pos(), gs.gamestack.stack[-1]]
            ctrl.last_release_count = ctrl.key_released[1]
            ctrl.release_check = True

        # ------------------------------- Redraw Window ------------------------------ #
        redraw_game_window()

        events_to_handle = list(pygame.event.get())
        events_handled = loop.create_task(handle_events(events_to_handle))
        await loop.run_in_executor(None, pygame.display.flip)  # noqa
        await events_handled


def check_mouse_scroll(event) -> None:
    """Checks if the mouse wheel is being scrolled up or down and updates ctrl.is_input_held accordingly

    :param event: The Pygame event currently being evaluated
    :return: None
    """
    if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
        ctrl.is_input_held[event.button] = True

    if event.type == pygame.MOUSEBUTTONUP and event.button in (4, 5):
        ctrl.is_input_held[event.button] = False


def check_key_release(event, is_mouse) -> None:
    """Checks if any input(s) has been released. If one has, then its count in key_released will be updated to match.

    :param event: The Pygame event currently being evaluated
    :param is_mouse: Are the inputs mouse buttons? True if yes, false if no.
    :return: None
    """
    if not is_mouse:
        for input_key in ctrl.key_released.keys():
            if event.type == pygame.KEYUP and event.key == input_key:
                ctrl.key_released[input_key] += 1
    else:
        for button in ctrl.key_released.keys():
            if event.type == pygame.MOUSEBUTTONUP and event.button == button:
                ctrl.key_released[button] += 1


async def handle_events(events_to_handle) -> None:
    """Handles the list of pygame events given

    :param events_to_handle: The list of pygame events to handle
    :return: None
    """

    for event in events_to_handle:
        key_pressed = pygame.key.get_pressed()

        if event.type == QUIT:
            sys.exit()

        if gs.gamestack.stack[-1] == gs.s_join_local_game:
            input_box_IP.update(event)
            input_box_username.update(event)

        if gs.gamestack.stack[-1] == gs.s_server_settings:
            server_settings_1_input_box.update(event)
            server_settings_2_input_box.update(event)
            server_settings_3_input_box.update(event)

        check_mouse_scroll(event)

        # Key input updating
        for key in ctrl.is_input_held.keys():
            if key in [1, 2, 3]:
                ctrl.is_input_held[key] = pygame.mouse.get_pressed(5)[key - 1]
            else:
                ctrl.is_input_held[key] = key_pressed[key]

        # Key release updating
        check_key_release(event, False)
        check_key_release(event, True)

if __name__ == '__main__':
    asyncio.run(main(cst.FPS))
