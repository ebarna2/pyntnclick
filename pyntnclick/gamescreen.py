# gamescreen.py
# Copyright Boomslang team, 2010 (see COPYING File)
# Main menu for the game

import pygame.draw
from pygame import Rect, Surface
from pygame.color import Color
from pygame.locals import MOUSEBUTTONDOWN, MOUSEMOTION, KEYDOWN, K_ESCAPE

from pyntnclick.cursor import CursorScreen
from pyntnclick.engine import Screen
from pyntnclick.state import handle_result
from pyntnclick.widgets.base import Container, ModalStackContainer
from pyntnclick.widgets.text import TextButton, ModalWrappedTextLabel
from pyntnclick.widgets.imagebutton import ImageButtonWidget

# XXX: Need a way to get at the constants.
from pyntnclick.constants import GameConstants
constants = GameConstants()
SCREEN = constants.screen
LEAVE = constants.leave


class InventorySlot(ImageButtonWidget):
    SELECTED_COLOR = Color("yellow")
    SELECTED_WIDTH = 2

    def __init__(self, rect, gd):
        self.item = None
        super(InventorySlot, self).__init__(rect, gd, None)
        self.add_callback(MOUSEBUTTONDOWN, self.mouse_down)

    def set_item(self, item):
        self.item = item

    def draw(self, surface):
        if self.item:
            surface.blit(self.item.get_inventory_image(), self.rect)
            if self.selected:
                pygame.draw.rect(surface, self.SELECTED_COLOR,
                                 self.rect, self.SELECTED_WIDTH)

    @property
    def selected(self):
        return self.parent.game.tool is self.item

    def mouse_down(self, event, widget):
        if event.button != 1 or not self.item:
            return
        if self.selected:
            self.parent.select(None)
        elif self.item.is_interactive(self.parent.game.tool):
            result = self.item.interact(self.parent.game.tool)
            handle_result(result, self.parent.state_widget)
        else:
            self.parent.select(self.item)


class UpDownButton(TextButton):
    # TextButton for now.
    def __init__(self, rect, gd):
        super(UpDownButton, self).__init__(rect, gd, self.TEXT, padding=3)


class UpButton(UpDownButton):
    TEXT = 'UP'


class DownButton(UpDownButton):
    TEXT = 'DN'


class InventoryView(Container):
    MIN_UPDOWN_WIDTH = 16

    def __init__(self, rect, gd, screen):
        self.bsize = gd.constants.button_size
        super(InventoryView, self).__init__(rect, gd)
        self.screen = screen
        self.game = screen.game
        self.state_widget = screen.state_widget

        slots = (self.rect.width - self.MIN_UPDOWN_WIDTH) / self.bsize
        self.slots = [self.add(self.make_slot(i)) for i in range(slots)]
        self.inv_offset = 0

        self.updown_width = self.rect.width - slots * self.bsize
        ud_left = self.rect.right - self.updown_width
        self.up_button = self.add(UpButton(Rect(
                    (ud_left, self.rect.top),
                    (self.updown_width, self.rect.height / 2)), gd))
        self.up_button.add_callback(MOUSEBUTTONDOWN, self.up_callback)
        self.down_button = self.add(DownButton(Rect(
                    (ud_left, self.rect.top + self.rect.height / 2),
                    (self.updown_width, self.rect.height / 2)), gd))
        self.down_button.add_callback(MOUSEBUTTONDOWN, self.down_callback)

        self.add_callback(MOUSEBUTTONDOWN, self.mouse_down)
        self.update_slots()

    def make_slot(self, slot):
        rect = Rect((self.rect.left + slot * self.bsize, self.rect.top),
                    (self.bsize, self.rect.height))
        return InventorySlot(rect, self.gd)

    def up_callback(self, event, widget):
        self.inv_offset = max(self.inv_offset - len(self.slots), 0)
        self.update_slots()

    def down_callback(self, event, widget):
        self.inv_offset += len(self.slots)
        self.update_slots()

    def update_slots(self):
        items = (self.slot_items + [None] * len(self.slots))[:len(self.slots)]
        for item, slot in zip(items, self.slots):
            slot.set_item(item)

        if self.inv_offset <= 0:
            self.up_button.disable()
        else:
            self.up_button.enable()

        max_slot = (self.inv_offset + len(self.slots))
        if max_slot >= len(self.game.inventory):
            self.down_button.disable()
        else:
            self.down_button.enable()

    def draw(self, surface):
        super(InventoryView, self).draw(surface)

    @property
    def slot_items(self):
        return self.game.inventory[self.inv_offset:][:len(self.slots)]

    def mouse_down(self, event, widget):
        if event.button != 1:
            self.game.cancel_doodah(self.screen)

    def select(self, tool):
        self.game.set_tool(tool)


class StateWidget(Container):

    def __init__(self, rect, gd, screen):
        super(StateWidget, self).__init__(rect, gd)
        self.screen = screen
        self.game = screen.game
        self.detail = DetailWindow(rect, gd, screen)
        self.add_callback(MOUSEBUTTONDOWN, self.mouse_down)
        self.add_callback(MOUSEMOTION, self.mouse_move)
        self._message_queue = []

    def draw(self, surface):
        self.game.current_scene.draw(surface, self)
        # Pass to container to draw children
        super(StateWidget, self).draw(surface)
        #self.animate()
        # XXX: Work out if we still need this
        # if self.game.previous_scene and self.game.do_check == LEAVE:
        #    # We still need to handle leave events, so still display the scene
        #    self.game.previous_scene.draw(surface, self)
        #else:
        #    self.game.current_scene.draw(surface, self)
        # We draw descriptions here, so we do the right thing
        # with detail views
        if self.game.current_detail:
            self.game.current_detail.draw_description(surface)
        else:
            self.game.current_scene.draw_description(surface)

    def queue_widget(self, widget):
        self._message_queue.append(widget)

    def mouse_down(self, event, widget):
        if self.game.current_detail:
            return self.detail.mouse_down(event, widget)
        self.mouse_move(event, widget)
        if event.button != 1:  # We have a right/middle click
            self.game.cancel_doodah(self.screen)
        else:
            result = self.game.interact(event.pos)
            handle_result(result, self)

    def animate(self):
        # XXX: if self.game.animate():
            # queue a redraw
        #    self.invalidate()
        # We do this here so we can get enter and leave events regardless
        # of what happens
        result = self.game.check_enter_leave(self.screen)
        handle_result(result, self)
        if self._message_queue:
            # Only add a message if we're at the top
            if self.screen.modal_magic.is_top(self.screen.inner_container):
                widget = self._message_queue.pop(0)
                self.screen.modal_magic.add(widget)
        if self.game.current_detail:
            self.game.current_detail.animate()
        else:
            self.game.current_scene.animate()

    def mouse_move(self, event, widget):
        if self.game.current_detail:
            return self.detail.mouse_move(event, widget)
        self.game.highlight_override = False
        self.game.current_scene.mouse_move(event.pos)
        self.game.old_pos = event.pos

    def show_message(self, message):
        # Display the message as a modal dialog
        # XXX: MessageDialog(self.screen, message, 60, style=style).present()
        # queue a redraw to show updated state
        # XXX: self.invalidate()
        # The cursor could have gone anywhere
        # XXX: if self.subwidgets:
        #    self.subwidgets[0]._mouse_move(mouse.get_pos())
        # else:
        #    self._mouse_move(mouse.get_pos())
        rect = Rect((0, 0), (1, 1))
        widget = ModalWrappedTextLabel(rect, self.gd, message,
                max_width=self.gd.constants.screen[0] - 100)
        widget.rect.center = self.rect.center
        # We abuse animate so we can queue multiple results
        # according
        self.queue_widget(widget)

    def show_detail(self, detail):
        self.clear_detail()
        detail_obj = self.game.set_current_detail(detail)
        self.add(self.detail)
        detail_rect = Rect((0, 0), detail_obj.get_detail_size())
        # Centre the widget
        detail_rect.center = self.rect.center
        self.detail.set_image_rect(detail_rect)
        self.game.do_enter_detail()

    def clear_detail(self):
        """Hide the detail view"""
        if self.game.current_detail is not None:
            self.remove(self.detail)
            self.game.do_leave_detail()
            self.game.set_current_detail(None)
            #self._mouse_move(mouse.get_pos())

    def end_game(self):
        self.screen.change_screen('end')


class DetailWindow(Container):
    def __init__(self, rect, gd, screen):
        super(DetailWindow, self).__init__(rect, gd)
        self.image_rect = None
        self.screen = screen
        self.game = screen.game
        self.border_width = 5
        self.border_color = (0, 0, 0)
        # parent only gets set when we get added to the scene
        self.close = TextButton(Rect(0, 0, 0, 0), self.gd,
                text='Close')
        self.close.add_callback('clicked', self.close_but)
        self.add(self.close)

    def close_but(self, ev, widget):
        self.parent.clear_detail()

    def end_game(self):
        self.parent.end_game()

    def set_image_rect(self, rect):
        bw = self.border_width
        self.image_rect = rect
        self.rect = rect.inflate(bw * 2, bw * 2)
        self.close.rect.midbottom = rect.midbottom

    def draw(self, surface):
        # scene_surface = self.get_root().surface.subsurface(self.parent.rect)
        # overlay = scene_surface.convert_alpha()
        # overlay.fill(Color(0, 0, 0, 191))
        # scene_surface.blit(overlay, (0, 0))
        self.game.current_detail.draw(
            surface.subsurface(self.image_rect), self)
        super(DetailWindow, self).draw(surface)

    def mouse_down(self, event, widget):
        self.mouse_move(event, widget)
        if event.button != 1:  # We have a right/middle click
            self.game.cancel_doodah(self.screen)
        else:
            result = self.game.interact_detail(
                self.global_to_local(event.pos))
            handle_result(result, self)

    def mouse_move(self, event, widget):
        self._mouse_move(event.pos)

    def _mouse_move(self, pos):
        self.game.highlight_override = False
        self.game.current_detail.mouse_move(self.global_to_local(pos))

    def show_message(self, message):
        self.parent.show_message(message)
        # self.invalidate()


class ToolBar(Container):
    def __init__(self, rect, gd, screen):
        self.screen = screen
        button_size = gd.constants.button_size

        if not isinstance(rect, Rect):
            rect = Rect(rect, (gd.constants.scene_size[0], button_size))
        super(ToolBar, self).__init__(rect, gd)

        self.bg_color = (31, 31, 31)
        self.left = self.rect.left

        self.menu_button = self.add_tool(
            0, TextButton, gd, "Menu", fontname=gd.constants.bold_font,
            color="red", padding=1, border=0, bg_color="black")
        self.menu_button.add_callback(MOUSEBUTTONDOWN, self.menu_callback)

        hand_image = gd.resource.get_image('items', 'hand.png')
        self.hand_button = self.add_tool(
            None, ImageButtonWidget, gd, hand_image)
        self.hand_button.add_callback(MOUSEBUTTONDOWN, self.hand_callback)

        self.inventory = self.add_tool(
            self.rect.width - self.left, InventoryView, gd, screen)

    def add_tool(self, width, cls, *args, **kw):
        rect = (self.left, self.rect.top)
        if width is not None:
            rect = Rect(rect, (width, self.rect.height))
        tool = cls(rect, *args, **kw)
        self.add(tool)
        self.left += tool.rect.width
        return tool

    def draw(self, surface):
        bg = Surface(self.rect.size)
        bg.fill(self.bg_color)
        surface.blit(bg, self.rect)
        super(ToolBar, self).draw(surface)

    def hand_callback(self, event, widget):
        self.inventory.select(None)

    def menu_callback(self, event, widget):
        self.screen.change_screen('menu')


class GameScreen(CursorScreen):

    def setup(self):
        super(GameScreen, self).setup()
        self.gd.running = False
        self.create_initial_state = self.gd.initial_state
        self.container.add_callback(KEYDOWN, self.key_pressed)
        self.state_widget = None

    def _clear_all(self):
        for widget in self.container.children[:]:
            self.container.remove(widget)

    def process_event(self, event_name, data):
        if event_name == 'restart':
            self.start_game()
        elif event_name == 'inventory':
            self.inventory.update_slots()

    def start_game(self):
        self._clear_all()
        self.modal_magic = self.container.add(
            ModalStackContainer(self.container.rect.copy(), self.gd))
        self.inner_container = self.modal_magic.add(
            Container(self.container.rect.copy(), self.gd))
        toolbar_height = self.gd.constants.button_size
        rect = Rect(0, 0, self.surface_size[0],
                    self.surface_size[1] - toolbar_height)
        self.game = self.create_initial_state()
        self.state_widget = StateWidget(rect, self.gd, self)
        self.inner_container.add(self.state_widget)

        self.toolbar = ToolBar((0, rect.height), self.gd, self)
        self.inventory = self.toolbar.inventory
        self.inner_container.add(self.toolbar)

        self.gd.running = True

    def animate(self):
        """Animate the state widget"""
        if self.state_widget:
            self.state_widget.animate()

    def key_pressed(self, event, widget):
        if event.key == K_ESCAPE:
            self.change_screen('menu')


class DefEndScreen(Screen):
    """A placeholder 'Game Over' screen so people can get started easily"""

    def setup(self):
        self.background = self.resource.get_image('pyntnclick/end.png')

    def draw(self, surface):
        surface.blit(self.background, (0, 0))


class DefMenuScreen(Screen):
    """A placeholder Start screen so people can get started easily"""

    def setup(self):
        self.background = self.resource.get_image('pyntnclick/start.png')

    def draw(self, surface):
        surface.blit(self.background, (0, 0))
