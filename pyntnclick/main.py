'''Game main module.

Contains the entry point used by the run_game.py script.

'''

# Albow looks for stuff in os.path[0], which isn't always where it expects.
# The following horribleness fixes this.
import sys
import os.path
right_path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, right_path)
from optparse import OptionParser

import pygame
from pygame.locals import SWSURFACE
from albow.shell import Shell

from pyntnclick.menu import MenuScreen
from pyntnclick.gamescreen import GameScreen
from pyntnclick.endscreen import EndScreen
from pyntnclick.constants import GameConstants
from pyntnclick.resources import Resources
from pyntnclick.sound import Sound
from pyntnclick import state


class MainShell(Shell):
    def __init__(self, display, game_description):
        Shell.__init__(self, display)
        self.menu_screen = MenuScreen(self, game_description)
        self.game_screen = GameScreen(self, game_description)
        self.end_screen = EndScreen(self, game_description)
        self.set_timer(game_description.constants.frame_rate)
        self.show_screen(self.menu_screen)


class GameDescriptionError(Exception):
    """Raised when an GameDescription is invalid."""


class GameDescription(object):

    # initial scene for start of game (unless overridden by debug)
    INITIAL_SCENE = None

    # list of game scenes
    SCENE_LIST = None

    # resource module
    RESOURCE_MODULE = "Resources"

    def __init__(self):
        if self.INITIAL_SCENE is None:
            raise GameDescriptionError("A game must have an initial scene.")
        if not self.SCENE_LIST:
            raise GameDescriptionError("A game must have a non-empty list"
                                       " of scenes.")
        self._initial_scene = self.INITIAL_SCENE
        self._scene_list = self.SCENE_LIST
        self._resource_module = self.RESOURCE_MODULE
        self._debug_rects = False
        self.resource = Resources(self._resource_module)
        self.sound = Sound(self.resource)
        self.constants = self.game_constants()

    def initial_state(self):
        """Create a copy of the initial game state."""
        initial_state = state.GameState(self)
        initial_state.set_debug_rects(self._debug_rects)
        for scene in self._scene_list:
            initial_state.load_scenes(scene)
        initial_state.set_current_scene(self._initial_scene)
        initial_state.set_do_enter_leave()
        return initial_state

    def game_constants(self):
        return GameConstants()

    def option_parser(self):
        parser = OptionParser()
        parser.add_option("--no-sound", action="store_false", default=True,
                dest="sound", help="disable sound")
        if self.constants.debug:
            parser.add_option("--scene", type="str", default=None,
                dest="scene", help="initial scene")
            parser.add_option("--no-rects", action="store_false", default=True,
                dest="rects", help="disable debugging rects")
        return parser

    def main(self):
        parser = self.option_parser()
        opts, _ = parser.parse_args(sys.argv)
        pygame.display.init()
        pygame.font.init()
        if opts.sound:
            self.sound.enable_sound(self.constants)
        else:
            self.sound.disable_sound()
        if self.constants.debug:
            if opts.scene is not None:
                # debug the specified scene
                self._initial_scene = opts.scene
            self._debug_rects = opts.rects
        display = pygame.display.set_mode(self.constants.screen,
                                          SWSURFACE)
        pygame.display.set_icon(self.resource.load_image(
                'suspended_sentence24x24.png', basedir='icons'))
        pygame.display.set_caption("Suspended Sentence")
        shell = MainShell(display, self)
        try:
            shell.run()
        except KeyboardInterrupt:
            pass
