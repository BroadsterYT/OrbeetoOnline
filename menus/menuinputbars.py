import pygame
import classbases as cb
import constants as cst
import gamestack as gs
import text

arr = []

class InputBox(cb.ActorBase):
    def __init__(self, gamestate: gs.GameState, x, y, width, height, name= "", character_limit= 20, initial_text="", input_type= None):
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
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.hitbox = self.rect.copy()
        self.text = initial_text
        self.font = pygame.font.Font(None, 32)

        self.color_inactive = pygame.Color('black')
        self.color_active = pygame.Color('dodgerblue2')
        self.border_color = self.color_inactive
        self.text_color = pygame.Color('black')
        self.input_type = input_type
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

            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                if (len(self.text) < self.character_limit):
                    self.character_limit_flag = False

            else:
                if len(self.text) < self.character_limit:
                    if self.input_type == "integer":
                        if (event.unicode.isdigit()) and ((self.text + event.unicode) != "0"):
                            self.text += event.unicode
                        else:
                            print("Non integer input!")
                    else:
                        self.text += event.unicode

                else:
                    self.character_limit_flag = True
                    print("Error: limited character amount reached")


    def draw_warning(self):
        text.draw_text("Character Limit!", self.x + self.width + 7, self.y + (self.height/4), 16, "Arial", (255, 0, 0))

    def update(self, event=None):
        if event:
            self.check_click(event)
            self.handle_keyboard(event)

        if self.character_limit_flag:
            self.draw_warning()
        # draw box
        self.image.fill((255, 255, 255))
        pygame.draw.rect(self.image, self.border_color, self.image.get_rect(), 2)

        # draw text
        txt_surface = self.font.render(self.text, True, self.text_color)
        self.image.blit(txt_surface, (5, 5))

    def get_text(self):
        return str(self.text)
