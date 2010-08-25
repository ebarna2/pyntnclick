"""Mess where crew eat. Fun stuff."""

from gamelib.state import Scene, Item, Thing, InteractImage, InteractNoImage, Result
from gamelib.cursor import CursorSprite


class Mess(Scene):

    FOLDER = "mess"
    BACKGROUND = "mess_hall.png"

    INITIAL_DATA = {
        'accessible': True,
        }

    def __init__(self, state):
        super(Mess, self).__init__(state)
        self.add_item(EmptyCan("empty_can"))
        self.add_item(FullCan("full_can"))
        self.add_item(TubeFragments("tube_fragments"))
        self.add_item(ReplacementTubes("replacement_tubes"))
        self.add_thing(CansOnShelf())
        self.add_thing(Tubes())
        self.add_thing(ToMap())


class EmptyCan(Item):
    "After emptying the full can."

    INVENTORY_IMAGE = "empty_can.png"
    CURSOR = CursorSprite('empty_can_cursor.png', 20, 30)

class FullCan(Item):
    "Found on the shelf."

    INVENTORY_IMAGE = "full_can.png"
    CURSOR = CursorSprite('full_can_cursor.png', 20, 30)

    def interact_with_titanium_leg(self, tool, state):
        state.replace_inventory_item(self, DentedCan("dented_can"))
        return Result("You club the can with the femur. The can gets dented, but doesn't open.")


class DentedCan(FullCan):
    "A can banged on with the femur"

    def interact_with_titanium_leg(self, tool, inventory):
        return Result("You club the can with the femur. The dents shift around, but it still doesn't open.")


class TubeFragments(Item):
    "Old tubes that need repair."

    INVENTORY_IMAGE = "tube_fragments.png"
    CURSOR = CursorSprite('tube_fragments_cursor.png', 3, 60)


class ReplacementTubes(Item):
    "Repaired tubes."

    INVENTORY_IMAGE = "replacement_tubes.png"
    CURSOR = CursorSprite('replacement_tubes.png', 53, 46)


class CansOnShelf(Thing):

    NAME = "mess.cans"

    INTERACTS = {
        "cans": InteractImage(165, 209, "cans_on_shelf.png"),
        "nocans": InteractNoImage(165, 209, 50, 50),
    }

    INITIAL = "cans"

    INITIAL_DATA = {
        "cans": True,
    }

    def interact_without(self):
        if self.data['cans']:
            self.state.add_inventory_item('full_can')
            self.set_data("cans", False)
            self.set_interact("nocans")
            return Result("Best before along time in the past. Better not eat these.")

    def get_description(self):
        if self.data["cans"]:
            return "The contents of these cans looks synthetic."
        else:
            return "You've pillaged these shelves already."


class Tubes(Thing):

    NAME = "mess.tubes"

    INTERACTS = {
        "blocked": InteractImage(250, 130, "blocking_broccoli.png"),
        "broken": InteractImage(250, 183, "broken_tubes.png"),
        "fixed": InteractImage(252, 183, "fixed_tubes.png"),
        }

    INITIAL = "blocked"


class ToMap(Thing):
    "Way to map."

    NAME = "mess.tomap"
    DEST = "map"

    INTERACTS = {
        "door": InteractNoImage(20, 390, 85, 150),
        }

    INITIAL = "door"

    def interact_without(self):
        """Go to map."""
        self.state.set_current_scene("map")


SCENES = [Mess]
