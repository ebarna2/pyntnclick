import pygame

from pyntnclick.widgets.base import Button


class ImageButtonWidget(Button):
    """An image that is also a button. Whatever next?"""

    def __init__(self, rect, gd, image):
        if not isinstance(rect, pygame.Rect):
            rect = pygame.Rect(rect, image.get_size())
        super(ImageButtonWidget, self).__init__(rect, gd)
        self.image = image
        self.visible = True

    def draw(self, surface):
        self.disabled = not self.visible
        if self.visible:
            surface.blit(self.image, self.rect)
