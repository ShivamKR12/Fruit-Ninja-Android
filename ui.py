# ui.py

import pygame
import random
from settings import WHITE, GOLD, COMBO_COLORS


class Button:
    """A 3D elevated button with warm wood/golden colors & touch-sink animations."""
    def __init__(self, text, size, center_x, center_y, width, height, font_file,
                 bg_color=(211, 84, 0),       # Vibrant Orange / Wood Top
                 bottom_color=(135, 54, 0),   # Dark Wood 3D Side/Shadow
                 hover_color=(243, 156, 18),  # Bright Golden-Yellow Touch Highlight
                 elevation=6):
        self.original_y_pos = center_y - height // 2
        self.elevation = elevation
        self.dynamic_elevation = elevation
        self.pressed = False

        self.top_rect = pygame.Rect(center_x - width // 2, self.original_y_pos, width, height)
        self.bottom_rect = pygame.Rect(center_x - width // 2, self.original_y_pos, width, elevation)

        self.original_top_color = pygame.Color(bg_color)
        self.top_color = self.original_top_color
        self.bottom_color = pygame.Color(bottom_color)
        self.hover_color = pygame.Color(hover_color)

        self.font = pygame.font.Font(font_file, size)
        self.update_text(text, WHITE)

    def update_text(self, text, text_color):
        self.text_surface = self.font.render(text, True, text_color)
        self.text_rect = self.text_surface.get_rect(center=self.top_rect.center)

    def reset_state(self):
        self.top_color = self.original_top_color
        self.dynamic_elevation = self.elevation
        self.pressed = False

    def _update_elevation_and_hover(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        if self.top_rect.collidepoint(mouse_pos):
            if mouse_pressed:
                self.top_color = self.hover_color
                self.dynamic_elevation = 0
                self.pressed = True
            else:
                self.reset_state()
        else:
            self.reset_state()

    def draw(self, surface):
        self._update_elevation_and_hover()

        self.top_rect.y = self.original_y_pos - self.dynamic_elevation
        self.text_rect.center = self.top_rect.center

        self.bottom_rect.midtop = self.top_rect.midtop
        self.bottom_rect.height = self.top_rect.height + self.dynamic_elevation

        pygame.draw.rect(surface, self.bottom_color, self.bottom_rect, border_radius=12)
        pygame.draw.rect(surface, self.top_color, self.top_rect, border_radius=12)
        pygame.draw.rect(surface, WHITE, self.top_rect, width=3, border_radius=12)
        surface.blit(self.text_surface, self.text_rect)

    def is_clicked(self, touch_x=None, touch_y=None):
        if touch_x is not None and touch_y is not None:
            if self.top_rect.collidepoint(touch_x, touch_y):
                self.reset_state()
                return True
            return False

        mouse_pos = pygame.mouse.get_pos()
        if self.top_rect.collidepoint(mouse_pos):
            if self.pressed and not pygame.mouse.get_pressed()[0]:
                self.reset_state()
                return True
        return False


class Slider:
    """A 3D elevated slider bar & coin-style knob matching the wood/golden theme."""
    def __init__(self, x, y, width, initial_val=0.7):
        self.track_height = 24
        self.track_elevation = 4
        self.bar_rect = pygame.Rect(x, y, width, self.track_height)
        self.bottom_bar_rect = pygame.Rect(x, y, width, self.track_height + self.track_elevation)
        
        self.val = initial_val
        self.handle_radius = 26
        self.handle_elevation = 6
        self.handle_x = int(self.bar_rect.x + (self.bar_rect.width * self.val))
        self.handle_y = self.bar_rect.centery
        self.is_dragging = False

        self.track_top_color = (135, 54, 0)
        self.track_bottom_color = (60, 25, 0)
        self.knob_top_color = (211, 84, 0)
        self.knob_bottom_color = (135, 54, 0)
        self.knob_active_color = (243, 156, 18)

    def draw(self, surface, font_obj):
        pygame.draw.rect(surface, self.track_bottom_color, self.bottom_bar_rect, border_radius=12)
        pygame.draw.rect(surface, self.track_top_color, self.bar_rect, border_radius=12)
        pygame.draw.rect(surface, WHITE, self.bar_rect, width=3, border_radius=12)
        
        fill_width = max(0, self.handle_x - self.bar_rect.x)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.bar_rect.x, self.bar_rect.y, fill_width, self.bar_rect.height)
            pygame.draw.rect(surface, GOLD, fill_rect, border_radius=12)
            pygame.draw.rect(surface, WHITE, fill_rect, width=2, border_radius=12)
        
        current_elevation = 0 if self.is_dragging else self.handle_elevation
        knob_y = self.handle_y - current_elevation
        knob_color = self.knob_active_color if self.is_dragging else self.knob_top_color

        pygame.draw.circle(surface, self.knob_bottom_color, (self.handle_x, self.handle_y), self.handle_radius)
        pygame.draw.circle(surface, knob_color, (self.handle_x, knob_y), self.handle_radius)
        pygame.draw.circle(surface, WHITE, (self.handle_x, knob_y), self.handle_radius, width=3)
        
        value_percentage = f"VOLUME: {int(self.val * 100)}%"
        label = font_obj.render(value_percentage, True, WHITE)
        surface.blit(label, (self.bar_rect.x + 70, self.bar_rect.y - 95))

    def update_touch(self, touch_x, touch_y, state_down):
        knob_dist_sq = (touch_x - self.handle_x)**2 + (touch_y - self.handle_y)**2
        if state_down and knob_dist_sq <= (self.handle_radius + 25)**2:
            self.is_dragging = True
            
        if not state_down:
            self.is_dragging = False
            
        if self.is_dragging:
            self.handle_x = max(self.bar_rect.x, min(touch_x, self.bar_rect.x + self.bar_rect.width))
            self.val = (self.handle_x - self.bar_rect.x) / float(self.bar_rect.width)
            return True
        return False


class ComboText:
    """Floating text that flashes on screen when a combo is achieved."""
    def __init__(self, x, y, count, font_file):
        self.x = x
        self.y = y
        self.count = count
        self.font = pygame.font.Font(font_file, 75)
        
        # Pick a random vibrant color
        chosen_color = random.choice(COMBO_COLORS)
        
        self.text_str = f"COMBO x{count}! (+{count})"
        self.surface = self.font.render(self. text_str, True, chosen_color)
        self.life = 30
        self.max_life = 30

    def update(self):
        self.y -= 1.5
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            alpha = int((self.life / self.max_life) * 255)
            text_surf = self.surface.copy()
            alpha_surf = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
            alpha_surf.fill((255, 255, 255, alpha))
            text_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            # Draw a subtle drop shadow 3 pixels down and right
            shadow_surf = self.font.render(f"COMBO x{self.count}! (+{self.count})", True, (0, 0, 0))
            shadow_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(shadow_surf, (int(self.x) + 3, int(self.y) + 3))
            
            # Draw main gold text on top
            surface.blit(text_surf, (int(self.x), int(self.y)))
