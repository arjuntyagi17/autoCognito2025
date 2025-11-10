from typing import Optional

try:
    import pygame 
except Exception: 
    pygame = None 


class Grid:
    def get_grid(self, tetris_game):
        grid_copy = [row[:] for row in tetris_game.grid]
        current_block = None
        next_block = None
        if tetris_game.fig:
            current_block = {
                "type": tetris_game.fig.type,
                "x": tetris_game.fig.x,
                "y": tetris_game.fig.y,
                "rotation": tetris_game.fig.rotation,
                "color": tetris_game.fig.color,
                "cells": [],
            }
            for i in range(4):
                for j in range(4):
                    if (i * 4 + j) in tetris_game.fig.img():
                        r = tetris_game.fig.y + i
                        c = tetris_game.fig.x + j
                        current_block["cells"].append((r, c))
                        if 0 <= r < tetris_game.rows and 0 <= c < tetris_game.cols:
                            grid_copy[r][c] = tetris_game.fig.color

        if tetris_game.next:
            next_block = {
                "type": tetris_game.next.type,
                "rotation": tetris_game.next.rotation,
                "color": tetris_game.next.color,
                "cells": [], 
            }

        return grid_copy, current_block, next_block, tetris_game.lvl


def _install_bot_key_injector():
    if pygame is None:
        return 

    if getattr(_install_bot_key_injector, "_installed", False):
        return

    try:
        from .bot import Bot
    except Exception:
        _install_bot_key_injector._installed = True
        return

    try:
        original_get_pressed = pygame.key.get_pressed
    except Exception:
        _install_bot_key_injector._installed = True
        return

    KEYMAP = {
        "w": getattr(pygame, "K_UP", 273),
        "a": getattr(pygame, "K_LEFT", 276),
        "s": getattr(pygame, "K_DOWN", 274),
        "d": getattr(pygame, "K_RIGHT", 275),
        " ": getattr(pygame, "K_SPACE", 32),
    }
    try:
        bot = Bot()
    except Exception:
        _install_bot_key_injector._installed = True
        return
    import os
    interval_env = os.getenv("BOT_INTERVAL_MS")
    try:
        interval_ms = int(interval_env) if interval_env else 120
    except Exception:
        interval_ms = 120

    state = {
        "active_key": None,     
        "pulse_frames": 0,        
        "last_decide_ms": 0,     
        "interval_ms": interval_ms,
        "game_instance": None,
    }

    def _update_action() -> None:
        try:
            now = pygame.time.get_ticks() if pygame.get_init() else 0
        except Exception:
            now = 0
        if now - state["last_decide_ms"] < state["interval_ms"]:
            return
        state["last_decide_ms"] = now
        
        obs = None
        if state["game_instance"] is not None:
            try:
                grid_helper = Grid()
                grid, current, next_piece, level = grid_helper.get_grid(state["game_instance"])
                obs = {
                    "grid": grid,
                    "current_piece": current,
                    "next_piece": next_piece,
                    "level": level
                }
            except:
                pass
        
        try:
            action = bot.decide(obs) 
        except Exception:
            action = None

        keycode = KEYMAP.get(action) if isinstance(action, str) else None
        if keycode is None:
            state["active_key"] = None
            state["pulse_frames"] = 0
            return

        state["active_key"] = keycode
        if action == " ":
            state["pulse_frames"] = 3
        elif action in ("w", "a", "d", "s"):
            state["pulse_frames"] = 5
        else:
            state["pulse_frames"] = 3

    class _KeyStateProxy:
        def __init__(self, base):
            self._base = base

        def __getitem__(self, idx):
            try:
                base_val = self._base[idx]
            except Exception:
                base_val = 0
            if state["active_key"] is not None and idx == state["active_key"]:
                return 1
            return base_val

        def __len__(self):
            try:
                return len(self._base)
            except Exception:
                return 0

        def __iter__(self):
            for i in range(len(self)):
                yield self[i]

    def injected_get_pressed():
        try:
            base = original_get_pressed()
        except Exception:
            return original_get_pressed()
        _update_action()
        if state["active_key"] is not None:
            if state["pulse_frames"] > 0:
                state["pulse_frames"] -= 1
            if state["pulse_frames"] == 0:
                state["active_key"] = None
        return _KeyStateProxy(base)

    # Swap in our injector
    try:
        pygame.key.get_pressed = injected_get_pressed
    except Exception:
        pass

    _install_bot_key_injector._installed = True
    
    def set_game_instance(game):
        state["game_instance"] = game
    
    return set_game_instance

_set_game_fn = None
try:
    _set_game_fn = _install_bot_key_injector()
except Exception:
    pass

def update_game_state(game):
    if _set_game_fn is not None:
        _set_game_fn(game)


