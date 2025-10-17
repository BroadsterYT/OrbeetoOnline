"""
Module containing all classes and functions related to the pause menu
"""
import sys

import menus

import classbases as cb
import constants as cst
import gamestack as gs
from gamestack import s_action, s_startup
from servermanager import ServerManager


class PauseMenu(cb.AbstractBase):
    def __init__(self):
        """The pause menu"""
        super().__init__()
        self.is_open = False
        self.servermanager = ServerManager()

        # ---------- Settings ---------- #
        self.b_settings = menus.MenuButton(gs.s_pause, cst.WINWIDTH // 2, 500, 256, 32, 'Settings',
                                           gs.gamestack.replace, gs.s_pause, gs.s_settings)
        self.b_settings_close = menus.MenuButton(gs.s_settings, cst.WINWIDTH // 2, cst.WINHEIGHT // (5/4), 256, 32, 'Back',
                                                 gs.gamestack.replace, gs.s_settings, gs.s_pause)

        self.close_button = menus.MenuButton(gs.s_pause, cst.WINWIDTH // 2, cst.WINHEIGHT // (5/4), 126, 32, 'Quit', self.leave)

        # noinspection PyTypeChecker
        self.add(
            self.b_settings,
            self.close_button,
        )

        # TODO: Add settings menu page
    def leave(self):
        """either leave current game or the application"""
        if gs.gamestack.stack[1] == gs.s_pause:
            self.leavegame()
        else:
            self.exitapplication()

    def leavegame(self):
        """leave current game"""
        gs.gamestack.pop()
        gs.gamestack.push(s_startup)
        self.servermanager.stop()

    def exitapplication(self):
        """exit application"""
        sys.exit()

    def update(self):
        pass
