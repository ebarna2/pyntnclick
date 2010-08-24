# gamescreen.py
# Copyright Boomslang team, 2010 (see COPYING File)
# Main menu for the game

from albow.controls import Button, Widget
from albow.layout import Row
from albow.palette_view import PaletteView
from albow.screen import Screen
from pygame import Rect, mouse
from pygame.color import Color
from pygame.locals import BLEND_ADD

from constants import SCREEN, BUTTON_SIZE, SCENE_SIZE
from cursor import CursorWidget
from hand import HandButton
from popupmenu import PopupMenu, PopupMenuButton
from state import initial_state, Item
from widgets import MessageDialog

class InventoryView(PaletteView):

    sel_color = Color("yellow")
    sel_width = 2

    def __init__(self, state, handbutton):
        PaletteView.__init__(self, (BUTTON_SIZE, BUTTON_SIZE), 1, 6, scrolling=True)
        self.state = state
        self.handbutton = handbutton

    def num_items(self):
        return len(self.state.inventory)

    def draw_item(self, surface, item_no, rect):
        item_image = self.state.inventory[item_no].get_inventory_image()
        surface.blit(item_image, rect, None, BLEND_ADD)

    def click_item(self, item_no, event):
        self.state.set_tool(self.state.inventory[item_no])
        self.handbutton.unselect()

    def item_is_selected(self, item_no):
        return self.state.tool is self.state.inventory[item_no]

    def unselect(self):
        self.state.set_tool(None)


class StateWidget(Widget):

    def __init__(self, state):
        Widget.__init__(self, Rect(0, 0, SCENE_SIZE[0], SCENE_SIZE[1]))
        self.state = state
        self.detail = DetailWindow(state)

    def draw(self, surface):
        self.state.draw(surface)

    def mouse_down(self, event):
        if self.subwidgets:
            self.remove(self.detail)
            self.state.set_current_detail(None)
        else:
            result = self.state.interact(event.pos)
            if result:
                result.process(self)

    def animate(self):
        if self.state.animate():
            # queue a redraw
            self.invalidate()
        # We do this here so we can get enter and leave events regardless
        # of what happens
        result = self.state.check_enter_leave()
        if result:
            result.process(self)

    def mouse_move(self, event):
        if not self.subwidgets:
            self.state.mouse_move(event.pos)

    def show_message(self, message):
        self.parent.cursor_highlight(False)
        # Display the message as a modal dialog
        MessageDialog(message, 60).present()
        # queue a redraw to show updated state
        self.invalidate()
        # The cursor could have gone anywhere
        self.state.current_scene.mouse_move(self.state.tool, mouse.get_pos())

    def show_detail(self, detail):
        w, h = self.state.set_current_detail(detail)
        self.detail.set_image_rect(Rect(0, 0, w, h))
        self.add_centered(self.detail)
        self.parent.cursor_highlight(False)


class DetailWindow(Widget):
    def __init__(self, state):
        Widget.__init__(self)
        self.state = state
        self.border_width = 5
        self.border_color = (0, 0, 0)

    def set_image_rect(self, rect):
        bw = self.border_width
        self.image_rect = rect
        self.image_rect.topleft = (bw, bw)
        self.set_rect(rect.inflate(bw*2, bw*2))

    def draw(self, surface):
        self.state.draw_detail(surface.subsurface(self.image_rect))

    def mouse_down(self, event):
        result = self.state.interact_detail(self.global_to_local(event.pos))
        if result:
            result.process(self)

    def mouse_move(self, event):
        self.state.mouse_move_detail(self.global_to_local(event.pos))

    def show_message(self, message):
        self.parent.show_message(message)
        self.invalidate()


class ToolBar(Row):
    def __init__(self, items):
        for item in items:
            item.height = BUTTON_SIZE
        Row.__init__(self, items, spacing=0, width=SCREEN[0])


class GameScreen(Screen, CursorWidget):
    def __init__(self, shell):
        CursorWidget.__init__(self)
        Screen.__init__(self, shell)
        self.running = False

    def _clear_all(self):
        for widget in self.subwidgets[:]:
            self.remove(widget)

    def start_game(self):
        self._clear_all()
        # TODO: Randomly plonk the state here for now
        self.state = initial_state(self)
        self.state_widget = StateWidget(self.state)
        self.add(self.state_widget)

        self.popup_menu = PopupMenu(self.shell)
        self.menubutton = PopupMenuButton('Menu',
                action=self.popup_menu.show_menu)

        self.handbutton = HandButton(action=self.hand_pressed)

        self.inventory = InventoryView(self.state, self.handbutton)

        self.testbutton = Button('Test', lambda: self.state_widget.show_detail('cryo_detail'))

        self.toolbar = ToolBar([
                self.menubutton,
                self.handbutton,
                self.inventory,
                self.testbutton,
                ])
        self.toolbar.bottomleft = self.bottomleft
        self.add(self.toolbar)

        self.running = True

    # Albow uses magic method names (command + '_cmd'). Yay.
    # Albow's search order means they need to be defined here, not in
    # PopMenu, which is annoying.
    def hide_cmd(self):
        # This option does nothing, but the method needs to exist for albow
        return

    def enter_screen(self):
        CursorWidget.enter_screen(self)

    def leave_screen(self):
        CursorWidget.leave_screen(self)

    def main_menu_cmd(self):
        self.shell.show_screen(self.shell.menu_screen)

    def quit_cmd(self):
        self.shell.quit()

    def hand_pressed(self):
        self.handbutton.toggle_selected()
        self.inventory.unselect()

    def begin_frame(self):
        if self.running:
            self.state_widget.animate()

    def mouse_delta(self, event):
        CursorWidget.mouse_delta(self, event)
        if not self.state_widget.rect.collidepoint(event.pos):
            self.cursor_highlight(False)
