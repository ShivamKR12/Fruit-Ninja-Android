# main.py

"""
IMPROVEMENTS TO BE MADE: 

1. [FIXED] No way to quit an ongoing match. 
2. Seperate highscores for different modes ?
3. Stop playing sounds such as explosion, etc after the game is over ?
4. A way to clear/reset the highscore ?
5. A proper settings menu/screen to move/have these functionalities, alongside already existing ones such as the volume slider, etc.
"""

import os
import sys
import random
import pygame
from settings import (
    FPS, WHITE, RED, GOLD, FRUIT_COLORS, FRUIT_NAMES, resource_path
)
from ui import Button, Slider, ComboText
from entities import Fruit, Particle


class Game:
    """Orchestrates the application window, state machine, loops, and inputs."""
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self.display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.screen_width, self.screen_height = self.display.get_size()
        
        self.clock = pygame.time.Clock()
        
        raw_bg = pygame.image.load(resource_path('background.jpg'))
        self.background = pygame.transform.scale(
            raw_bg, (self.screen_width, self.screen_height)
        )
        
        self.raw_logo = pygame.image.load(resource_path('FruitNinja.png'))
        self.logo_rect = self.raw_logo.get_rect(
            center=(self.screen_width / 2, self.screen_height / 4)
        )

        self.font_file = resource_path('comic.ttf')
        if not os.path.exists(self.font_file):
            self.font_file = None 
            
        self.font = pygame.font.Font(self.font_file, 42)
        self.score_font = pygame.font.Font(self.font_file, 64)
        
        self.snd_start = pygame.mixer.Sound(resource_path("Sounds/Game-start.wav"))
        self.snd_over = pygame.mixer.Sound(resource_path("Sounds/Game-over.wav"))
        self.snd_click = pygame.mixer.Sound(resource_path("Sounds/ui-button-push.wav"))
        self.snd_explode = pygame.mixer.Sound(resource_path("Sounds/Bomb-explode.wav"))
        self.snd_combo = pygame.mixer.Sound(resource_path("Sounds/combo-1.wav"))
        self.snd_highscore = pygame.mixer.Sound(resource_path("Sounds/New-best-score.wav"))
        self.snd_swipe = pygame.mixer.Sound(resource_path("Sounds/Sword-swipe-1.wav"))
        self.swipe_cooldown = 0
        
        self.slice_sounds = {
            'melon': pygame.mixer.Sound(resource_path("Sounds/Impact-Watermelon.wav")),
            'orange': pygame.mixer.Sound(resource_path("Sounds/Impact-Orange.wav")),
            'pomegranate': pygame.mixer.Sound(resource_path("Sounds/Clean-Slice-1.wav")),
            'guava': pygame.mixer.Sound(resource_path("Sounds/Visceral-impact-1.wav"))
        }
        
        self.active_touches = {}
        self.player_lives = 3
        self.score = 0
        self.highscore = self.load_highscore()
        self.is_new_highscore = False
        
        self.game_mode = 'classic'
        self.time_left = 0
        self.blade_theme = 'default'
        
        self.game_over = False
        self.in_menu = True
        self.in_mode_select = False
        self.running = True
        
        self.blade_paths = {}
        self.particles = []
        self.combo_texts = []
        self.touch_combo_counts = {}
        
        self.fruit_names = list(FRUIT_NAMES)
        self.fruits = [
            Fruit(name, self.screen_width, self.screen_height) 
            for name in self.fruit_names
        ]

        # Main Menu Buttons
        self.play_btn = Button(
            "PLAY", 60, self.screen_width / 2, self.screen_height * 0.52,
            340, 100, self.font_file
        )
        self.quit_btn = Button(
            "QUIT", 60, self.screen_width / 2, self.screen_height * 0.82,
            340, 100, self.font_file
        )
        
        # Volume slider placed directly between PLAY and QUIT
        self.volume_slider = Slider(
            int(self.screen_width / 2 - 230), int(self.screen_height * 0.67),
            460, initial_val=0.7
        )
        self.sync_volume()

        # Mode Selection Sub-Menu Buttons
        self.classic_btn = Button(
            "CLASSIC", 60, self.screen_width / 2, self.screen_height * 0.50,
            340, 100, self.font_file
        )
        self.arcade_btn = Button(
            "ARCADE", 60, self.screen_width / 2, self.screen_height * 0.65,
            340, 100, self.font_file
        )
        self.zen_btn = Button(
            "ZEN", 60, self.screen_width / 2, self.screen_height * 0.80,
            340, 100, self.font_file
        )
        self.back_btn = Button(
            "BACK", 40, self.screen_width / 2, self.screen_height * 0.94,
            240, 70, self.font_file
        )

        # Game Over Screen Button
        self.continue_btn = Button(
            "CONTINUE", 60, self.screen_width / 2, self.screen_height * 0.75,
            380, 100, self.font_file
        )

        # In-Game Quit Button
        self.quit_match_btn = Button(
            "QUIT", 40, 100, self.screen_height - 60,
            150, 70, self.font_file
        )
        
        self.white_life_img = pygame.image.load(resource_path('white_lives.png'))
        self.red_life_img = pygame.image.load(resource_path('red_lives.png'))
        
        self.shake_duration = 0
        self.shake_intensity = 0

    def load_highscore(self):
        try:
            with open("highscore.txt", "r") as f:
                return int(f.read().strip())
        except Exception:
            return 0

    def save_highscore(self):
        try:
            with open("highscore.txt", "w") as f:
                f.write(str(self.highscore))
        except Exception:
            pass

    def sync_volume(self):
        v = self.volume_slider.val
        self.snd_start.set_volume(v)
        self.snd_over.set_volume(v)
        self.snd_click.set_volume(v)
        self.snd_explode.set_volume(v)
        self.snd_combo.set_volume(v)
        self.snd_highscore.set_volume(v)
        self.snd_swipe.set_volume(v)
        
        for snd in self.slice_sounds.values():
            snd.set_volume(v)

    def draw_text(self, text, size, x, y, color=WHITE):
        font = pygame.font.Font(self.font_file, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.display.blit(text_surface, text_rect)

    def draw_lives(self):
        start_x = self.screen_width - 160
        y_pos = 40
        
        for i in range(self.player_lives):
            self.display.blit(self.white_life_img, (start_x + 45 * i, y_pos))
            
        for i in range(3 - self.player_lives):
            x_pos = (start_x + 90) - (45 * i)
            self.display.blit(self.red_life_img, (x_pos, y_pos))

    def start_game(self, mode):
        self.snd_click.play()
        self.snd_start.play()
        self.game_mode = mode
        self.in_menu = False
        self.reset_game()

    def show_menu_screen(self):
        waiting = True
        self.in_mode_select = False
        
        while waiting and self.running:
            self.clock.tick(FPS)
            
            self.display.blit(self.background, (0, 0))
            self.display.blit(self.raw_logo, self.logo_rect)
            
            # Original text scales restored
            self.draw_text(
                f"Best Score: {self.highscore}", 75,
                self.screen_width / 2, self.screen_height * 0.40, color=GOLD
            )
            
            if not self.in_mode_select:
                # Base Menu
                self.volume_slider.draw(self.display, self.font)
                self.play_btn.draw(self.display)
                self.quit_btn.draw(self.display)
            else:
                # Sub-menu overlay
                self.classic_btn.draw(self.display)
                self.arcade_btn.draw(self.display)
                self.zen_btn.draw(self.display)
                self.back_btn.draw(self.display)
                
            pygame.display.flip()
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_AC_BACK
                ):
                    if self.in_mode_select:
                        self.in_mode_select = False
                    else:
                        self.running = False
                        waiting = False
                
                elif event.type == pygame.FINGERDOWN:
                    px = int(event.x * self.screen_width)
                    py = int(event.y * self.screen_height)
                    
                    if not self.in_mode_select:
                        self.volume_slider.update_touch(px, py, True)
                        
                        if self.play_btn.is_clicked(px, py):
                            self.snd_click.play()
                            self.in_mode_select = True
                        elif self.quit_btn.is_clicked(px, py):
                            self.snd_click.play()
                            self.running = False
                            waiting = False
                    else:
                        if self.classic_btn.is_clicked(px, py):
                            self.start_game('classic')
                            waiting = False
                        elif self.arcade_btn.is_clicked(px, py):
                            self.start_game('arcade')
                            waiting = False
                        elif self.zen_btn.is_clicked(px, py):
                            self.start_game('zen')
                            waiting = False
                        elif self.back_btn.is_clicked(px, py):
                            self.snd_click.play()
                            self.in_mode_select = False
                        
                elif event.type == pygame.FINGERMOTION:
                    if not self.in_mode_select:
                        px = int(event.x * self.screen_width)
                        py = int(event.y * self.screen_height)
                        if self.volume_slider.update_touch(px, py, True):
                            self.sync_volume()
                        
                elif event.type == pygame.FINGERUP:
                    if not self.in_mode_select:
                        self.volume_slider.update_touch(0, 0, False)

    def show_results_screen(self):
        if self.score > self.highscore:
            self.highscore = self.score
            self.is_new_highscore = True
            self.save_highscore()
            self.snd_highscore.play()
        else:
            self.is_new_highscore = False
            self.snd_over.play()

        waiting = True
        while waiting and self.running:
            self.clock.tick(FPS)
            
            self.display.blit(self.background, (0, 0))
            self.draw_text(
                "GAME OVER", 115, self.screen_width / 2,
                self.screen_height * 0.20, color=RED
            )
            
            if self.is_new_highscore:
                self.draw_text(
                    "NEW HIGH SCORE!", 68, self.screen_width / 2,
                    self.screen_height * 0.40, color=GOLD
                )
                self.draw_text(
                    f"Score : {self.score}", 60, self.screen_width / 2,
                    self.screen_height * 0.52, color=WHITE
                )
            else:
                self.draw_text(
                    f"Your Score : {self.score}", 70, self.screen_width / 2,
                    self.screen_height * 0.42, color=WHITE
                )
                self.draw_text(
                    f"Best Score : {self.highscore}", 60,
                    self.screen_width / 2, self.screen_height * 0.55, color=GOLD
                )
                
            self.continue_btn.draw(self.display)
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_AC_BACK
                ):
                    self.running = False
                    waiting = False
                    
                if event.type == pygame.FINGERUP:
                    px = int(event.x * self.screen_width)
                    py = int(event.y * self.screen_height)
                    
                    if self.continue_btn.is_clicked(px, py):
                        self.snd_click.play()
                        waiting = False
                        self.in_menu = True

    def reset_game(self):
        self.game_over = False
        self.score = 0
        self.active_touches.clear()
        self.particles.clear()
        self.blade_paths.clear()
        self.combo_texts.clear()
        self.touch_combo_counts.clear()
        self.shake_duration = 0
        self.shake_intensity = 0
        
        if self.game_mode == 'classic':
            self.player_lives = 3
            self.time_left = 0
            self.fruit_names = list(FRUIT_NAMES)
        elif self.game_mode == 'arcade':
            self.player_lives = 3 
            self.time_left = 60 * FPS 
            self.fruit_names = list(FRUIT_NAMES)
        elif self.game_mode == 'zen':
            self.player_lives = 3
            self.time_left = 90 * FPS 
            self.fruit_names = [name for name in FRUIT_NAMES if name != 'bomb']

        if self.highscore >= 300:
            self.blade_theme = 'poison'
        elif self.highscore >= 100:
            self.blade_theme = 'water'
        else:
            self.blade_theme = 'default'

        self.fruits = [
            Fruit(name, self.screen_width, self.screen_height)
            for name in self.fruit_names
        ]
        for fruit in self.fruits:
            fruit.reset(self.score)

    def process_slice_input(self, pixel_x, pixel_y, finger_id):
        if finger_id not in self.touch_combo_counts:
            self.touch_combo_counts[finger_id] = 0

        bomb_hit = False
        for fruit in self.fruits:
            if fruit.check_collision(pixel_x, pixel_y):
                color = FRUIT_COLORS.get(fruit.name, WHITE)
                for _ in range(50):
                    p_x = fruit.x + (fruit.size // 2)
                    p_y = fruit.y + (fruit.size // 2)
                    self.particles.append(Particle(p_x, p_y, color))
                    
                if fruit.name == 'bomb':
                    bomb_hit = True
                    self.shake_duration = 15
                    self.shake_intensity = 20
                    self.snd_explode.play()
                    
                    if self.game_mode == 'arcade':
                        self.score = max(0, self.score - 10)
                    elif self.game_mode == 'classic':
                        self.player_lives -= 1
                        if self.player_lives <= 0:
                            self.game_over = True
                else:
                    self.touch_combo_counts[finger_id] += 1
                    self.score += 1
                    if fruit.name in self.slice_sounds:
                        self.slice_sounds[fruit.name].play()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_AC_BACK
            ):
                self.in_menu = True
                self.snd_click.play()
                
            elif event.type == pygame.FINGERDOWN:
                px = int(event.x * self.screen_width)
                py = int(event.y * self.screen_height)
                
                if self.quit_match_btn.is_clicked(px, py):
                    self.snd_click.play()
                    self.in_menu = True
                    return

                self.active_touches[event.finger_id] = (px, py)
                self.touch_combo_counts[event.finger_id] = 0
                self.process_slice_input(px, py, event.finger_id)
                self.blade_paths[event.finger_id] = [[px, py, 10]]
                
                if self.swipe_cooldown == 0:
                    self.snd_swipe.play()
                    self.swipe_cooldown = 8
                
            elif event.type == pygame.FINGERMOTION:
                px = int(event.x * self.screen_width)
                py = int(event.y * self.screen_height)
                self.active_touches[event.finger_id] = (px, py)
                self.process_slice_input(px, py, event.finger_id)
                if event.finger_id in self.blade_paths:
                    self.blade_paths[event.finger_id].append([px, py, 10])
                
            elif event.type == pygame.FINGERUP:
                if event.finger_id in self.touch_combo_counts:
                    final_combo_count = self.touch_combo_counts[event.finger_id]
                    if final_combo_count >= 3:
                        fx, fy = self.active_touches.get(
                            event.finger_id,
                            (self.screen_width / 2, self.screen_height / 2)
                        )
                        self.score += final_combo_count
                        self.combo_texts.append(
                            ComboText(fx - 140, fy - 60, final_combo_count, self.font_file)
                        )
                        self.snd_combo.play()
                    del self.touch_combo_counts[event.finger_id]

                if event.finger_id in self.active_touches:
                    del self.active_touches[event.finger_id]

    def update(self):
        if self.game_mode in ['arcade', 'zen']:
            self.time_left -= 1
            if self.time_left <= 0:
                self.game_over = True
                
        target_fruit_count = min(15, 5 + (self.score // 10))
        while len(self.fruits) < target_fruit_count:
            new_name = random.choice(self.fruit_names)
            new_fruit = Fruit(new_name, self.screen_width, self.screen_height)
            new_fruit.reset(self.score)
            self.fruits.append(new_fruit)
        
        for fruit in self.fruits:
            fruit.update(self.score)
            
        if self.shake_duration > 0:
            self.shake_duration -= 1
        
        if self.swipe_cooldown > 0:
            self.swipe_cooldown -= 1
        
        for finger_id in list(self.blade_paths.keys()):
            path = self.blade_paths[finger_id]
            for i in range(len(path)):
                path[i][2] -= 1
            self.blade_paths[finger_id] = [pt for pt in path if pt[2] > 0]
            if finger_id not in self.active_touches and not self.blade_paths[finger_id]:
                del self.blade_paths[finger_id]
                    
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)
        
        for ct in self.combo_texts[:]:
            ct.update()
            if ct.life <= 0:
                self.combo_texts.remove(ct)

    def render(self):
        offset_x = 0
        offset_y = 0
        if self.shake_duration > 0:
            offset_x = random.randint(-self.shake_intensity, self.shake_intensity)
            offset_y = random.randint(-self.shake_intensity, self.shake_intensity)
            
        self.display.blit(self.background, (offset_x, offset_y))
        
        score_surface = self.score_font.render(f'Score : {self.score}', True, WHITE)
        self.display.blit(score_surface, (40, 30))
        
        if self.game_mode == 'classic':
            self.draw_lives()
        elif self.game_mode in ['arcade', 'zen']:
            time_sec = max(0, self.time_left // FPS)
            time_surface = self.score_font.render(f'Time: {time_sec}s', True, GOLD)
            self.display.blit(time_surface, (self.screen_width - 300, 30))
            
        self.quit_match_btn.draw(self.display)
        
        for fruit in self.fruits:
            fruit.draw(self.display)
        
        for p in self.particles:
            p.draw(self.display)
            
        for ct in self.combo_texts:
            ct.draw(self.display)

        trail_surf = pygame.Surface(
            (self.screen_width, self.screen_height), pygame.SRCALPHA
        )
        has_trails = False
        
        for path in self.blade_paths.values():
            num_points = len(path)
            if num_points >= 2:
                has_trails = True
                for i in range(num_points - 1):
                    p1 = (path[i][0], path[i][1])
                    p2 = (path[i + 1][0], path[i + 1][1])
                    progress = (i + 1) / (num_points - 1)
                    thickness = int(3 + (27 * progress))
                    
                    alpha = int(30 + (225 * progress))
                    
                    if self.blade_theme == 'water':
                        r = int(30 * (1.0 - progress))
                        g = int(150 + (100 * progress))
                        b = 255
                    elif self.blade_theme == 'poison':
                        r = int(50 + (100 * progress))
                        g = 255
                        b = int(50 * (1.0 - progress))
                    else: 
                        r = int(255)
                        g = int(50 + (180 * progress))
                        b = int(30 * (1.0 - progress))
                        
                    color = (r, g, b, alpha)
                    
                    pygame.draw.line(trail_surf, color, p1, p2, thickness)
                    pygame.draw.circle(trail_surf, color, p2, thickness // 2)
                    
        if has_trails:
            self.display.blit(trail_surf, (offset_x, offset_y))
        
        pygame.display.update()
        
    def run(self):
        while self.running:
            if self.in_menu:
                self.show_menu_screen()
            elif self.game_over:
                self.show_results_screen()
            else:
                self.handle_events()
                self.update()
                self.render()
                self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
