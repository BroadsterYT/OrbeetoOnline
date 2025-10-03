import pygame
import classbases as cb
import constants as cst
import gamestack as gs

arr = []

class InputBox(cb.ActorBase):
    def __init__(self, gamestate: gs.GameState, x, y, width, height, name= "", initial_text=""):
        super().__init__(cst.LAYER['ui_2'], gamestate)
        self.add_to_gamestate()

        self.rect = pygame.Rect(x, y, width, height)
        self.hitbox = self.rect.copy()
        self.text = initial_text
        self.font = pygame.font.Font(None, 32)

        self.color_inactive = pygame.Color('black')
        self.color_active = pygame.Color('dodgerblue2')
        self.border_color = self.color_inactive
        self.text_color = pygame.Color('black')
        self.active = False

        # start with a white box
        self.image = pygame.Surface((width, height))
        self.image.fill((255, 255, 255))

        self.name = name
        arr.append(self)

    def check_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hitbox.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
            self.border_color = self.color_active if self.active else self.color_inactive

    def handle_keyboard(self, event):
        if not self.active:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                print(f"Input confirmed: {self.text}")
                self.text = ""
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

    def update(self, event=None):
        if event:
            self.check_click(event)
            self.handle_keyboard(event)

        # draw box
        self.image.fill((255, 255, 255))
        pygame.draw.rect(self.image, self.border_color, self.image.get_rect(), 2)

        # draw text
        txt_surface = self.font.render(self.text, True, self.text_color)
        self.image.blit(txt_surface, (5, 5))

    def get_text(self):
        return self.text