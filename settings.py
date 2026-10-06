# settings.py

import os
import sys
import pygame


FPS = 45

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
RED = (240, 50, 50)
GOLD = (255, 215, 0)

FRUIT_COLORS = {
    'melon': (46, 204, 113),
    'orange': (230, 126, 34),
    'pomegranate': (192, 57, 43),
    'guava': (241, 196, 15),
    'bomb': (243, 156, 18)
}

FRUIT_NAMES = ['melon', 'orange', 'pomegranate', 'guava', 'bomb']

COMBO_COLORS = [
    (255, 215, 0),    # Gold / Bright Yellow
    (0, 210, 255),    # Sky Blue / Cyan
    (255, 60, 60),    # Bright Red
    (50, 230, 90),    # Neon Lime Green
    (255, 80, 200),   # Arcade Magenta / Pink
    (255, 140, 0),    # Punchy Orange
    (180, 100, 255),  # Electric Purple
]


def resource_path(relative_path):
    """Get the absolute path to a resource file, supporting PyInstaller, Buildozer and Android."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "assets", relative_path)
