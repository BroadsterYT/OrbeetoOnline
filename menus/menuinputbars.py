import pygame
import classbases as cb
import constants as cst
import gamestack as gs

arr = []

class InputBox(cb.ActorBase):
    def __init__(self, gamestate: gs.GameState, x, y, width, height, name= "", character_limit= 20, initial_text=""):
        """
        when creating an object of this class you need to make sure you call its update method on the event handler and
        pass the event with it (look at other implementations).
        In order to get access to the text of an input you can traverse through the global array that this file shares
        and look for the specific input box you want by looking for it's name that is defined at its creation.

        :param gamestate:
        :param x:
        :param y:
        :param width:
        :param height:
        :param name:
        :param initial_text:
        """
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
        self.character_limit = character_limit
        self.character_limit_flag = False

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
                if self.character_limit_flag == True:
                    self.text = self.text[9:]
                    self.character_limit_flag = False
                else:
                    self.text = self.text[:-1]
            else:
                if len(self.text) < self.character_limit:
                    self.text += event.unicode
                else:
                    if not self.character_limit_flag:
                        print("Error: limited character amount reached")
                        self.text = "Char num!" + self.text
                    self.character_limit_flag = True


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