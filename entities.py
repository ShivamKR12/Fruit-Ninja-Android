# entities.py

import random
import pygame
from settings import resource_path


class Fruit:
    """Represents an individual sliceable entity (fruit or bomb) in the game."""
    def __init__(self, name, screen_width, screen_height):
        self.name = name
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.size = 120
        self.reset()
        
    def reset(self, score=0):
        self.x = random.randint(100, max(120, self.screen_width - 100))
        self.y = self.screen_height + 100
        
        difficulty_multiplier = min(2.0, 1.0 + (score / 50.0))
        self.speed_x = random.randint(-4, 4) * random.uniform(1.0, difficulty_multiplier)
        
        base_speed_y = random.randint(int(-self.screen_height * 0.04), int(-self.screen_height * 0.03))
        self.speed_y = int(base_speed_y * difficulty_multiplier)
        
        self.t = 0
        self.hit = False
        
        throw_gate = max(0.45, 0.70 - (score / 200.0))
        self.throw = random.random() >= throw_gate
        self.gravity_modifier = 0.35 * difficulty_multiplier
        
        raw_image = pygame.image.load(resource_path(f"{self.name}.png"))
        self.image = pygame.transform.scale(raw_image, (self.size, self.size))

    def update(self, score=0):
        if self.throw:
            self.x += self.speed_x
            self.y += self.speed_y
            self.speed_y += (self.gravity_modifier * self.t)
            self.t += 1

            if self.y > self.screen_height + 250:
                self.reset(score)
        else:
            self.reset(score)

    def check_collision(self, touch_x, touch_y):
        if not self.hit and self.throw:
            if (self.x < touch_x < self.x + self.size) and (self.y < touch_y < self.y + self.size):
                self.hit = True
                self.speed_x += 4
                
                half_fruit_path = "explosion.png" if self.name == 'bomb' else f"half_{self.name}.png"
                raw_sliced = pygame.image.load(resource_path(half_fruit_path))
                self.image = pygame.transform.scale(raw_sliced, (self.size, self.size))
                return True
        return False

    def draw(self, surface):
        if self.throw and self.y <= self.screen_height + 200:
            surface.blit(self.image, (self.x, self.y))


class Particle:
    """A small colored particle that sprays outward when a fruit is cut."""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.speed_x = random.uniform(-12, 12)
        self.speed_y = random.uniform(-18, -6)
        self.max_life = random.randint(20, 35)
        self.life = self.max_life
        self.size = random.randint(6, 12)

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += 0.5
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            alpha = int((self.life / self.max_life) * 255)
            p_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            p_surf.fill((*self.color, alpha))
            surface.blit(p_surf, (int(self.x), int(self.y)))
