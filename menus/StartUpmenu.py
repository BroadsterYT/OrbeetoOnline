import pygame

class Header(pygame.sprite.Sprite):
    def __init__(self, text, pos=(0,0), font_size=77):
        super().__init__()
        self.in_gamestate = True
        self.font = pygame.font.SysFont(None, font_size)
        self.text = text
        self.image = self.font.render(self.text, True, (255, 255, 255))
        self.rect = self.image.get_rect(topleft=pos)
