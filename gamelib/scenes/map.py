"""Neurally implanted schematic for moving around on the ship.

   It is illegal for prisoners in transit to activate such an
   implant. Failure to comply carries a minimum sentence of
   six months.

   Many parts of the ship are derelict and inaccessible.
   """

from pyntnclick.i18n import _
from pyntnclick.state import Scene, Thing, Result
from pyntnclick.scenewidgets import InteractRectUnion

from gamelib.scenes.game_constants import PLAYER_ID
from gamelib.scenes.game_widgets import make_jim_dialog


class Map(Scene):

    FOLDER = "map"
    BACKGROUND = 'map.png'

    INITIAL_DATA = {
        'implant': True,
    }

    def setup(self):
        self.add_thing(ToCryo())
        self.add_thing(ToBridge())
        self.add_thing(ToMess())
        self.add_thing(ToEngine())
        self.add_thing(ToMachine())
        self.add_thing(ToCrew())
        self.add_thing(InaccessibleArea())
        self.add_thing(HydroponicsArea())

    def enter(self):
        if self.get_data('implant'):
            self.set_data('implant', False)
            ai1 = make_jim_dialog(
                _("Under the terms of the emergency conscription "
                  "act, I have downloaded the ship's schematics to your "
                  "neural implant to help you navigate around the ship."),
                self.game)
            if ai1:
                return ai1, make_jim_dialog(_("Prisoner %s, you are a "
                "class 1 felon. Obtaining access to the ship's schematics "
                "constitutes a level 2 offence and carries a minimal penalty "
                "of an additional 3 years on your sentence.") % PLAYER_ID,
                self.game)


class DoorThing(Thing):

    # name of destination
    DEST = None

    def interact(self, _item):
        """Go to destination."""
        if self.DEST in self.game.scenes:
            self.game.change_scene(self.DEST)


class ToCryo(DoorThing):
    "Way to cryo room."

    NAME = "map.tocryo"
    DEST = "cryo"

    INTERACTS = {
        'door': InteractRectUnion((
            (515, 158, 56, 68),
            (361, 519, 245, 29),
        ))
    }

    INITIAL = 'door'


class ToBridge(DoorThing):
    "Way to bridge room."

    NAME = "map.tobridge"
    DEST = "bridge"

    INTERACTS = {
        'door': InteractRectUnion((
            (36, 260, 60, 83),
            (26, 177, 71, 21),
        ))
    }

    INITIAL = 'door'


class ToMess(DoorThing):
    "Way to cryo room."

    NAME = "map.tomess"
    DEST = "mess"

    INTERACTS = {
        'door': InteractRectUnion((
            (395, 262, 64, 80),
            (341, 434, 110, 27),
        ))
    }

    INITIAL = 'door'


class ToEngine(DoorThing):
    "Way to engine room."

    NAME = "map.toengine"
    DEST = "engine"

    INTERACTS = {
        'door': InteractRectUnion((
            (691, 279, 76, 54),
            (662, 500, 128, 23),
        ))
    }

    INITIAL = 'door'

    def interact(self, item):
        if not self.game.is_in_inventory('helmet:'):
            return Result(_('The airlock refuses to open. The automated'
                    ' voice says: "Hull breach beyond this door. Personnel'
                    ' must be equipped for vacuum before entry."'))
        else:
            return super(ToEngine, self).interact(item)


class ToMachine(DoorThing):
    "Way to machine room."

    NAME = "map.tomachine"
    DEST = "machine"

    INTERACTS = {
        'door': InteractRectUnion((
            (608, 156, 57, 72),
            (578, 91, 140, 23),
        ))
    }

    INITIAL = 'door'


class ToCrew(DoorThing):
    "Way to crew quarters."

    NAME = "map.tocrew_quarters"
    DEST = "crew_quarters"

    INTERACTS = {
        'door': InteractRectUnion((
            (210, 321, 37, 64),
            (69, 469, 148, 26),
        ))
    }

    INITIAL = 'door'


class InaccessibleArea(Thing):
    NAME = 'map.inaccessible'

    INTERACTS = {
        'areas': InteractRectUnion((
            (207, 227, 39, 63),
            (256, 225, 35, 64),
            (259, 322, 34, 64),
            (514, 380, 58, 66),
            (607, 377, 60, 70),
        ))
    }

    INITIAL = 'areas'

    def interact(self, _item):
        return Result(_("You look in the door, but just see empty space: "
                        "that room appears to have been obliterated by "
                        "meteors."))


class HydroponicsArea(Thing):
    NAME = 'map.hydroponics'

    INTERACTS = {
        'areas': InteractRectUnion((
            (314, 263, 73, 81),
            (313, 138, 125, 22),
        ))
    }

    INITIAL = 'areas'

    def interact(self, _item):
        return Result(_("Peering in through the window, you see that the "
                        "entire chamber is overgrown with giant broccoli. "
                        "It would take you years to cut a path through that."))


SCENES = [Map]
