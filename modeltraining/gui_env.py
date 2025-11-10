from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import random
import pygame

from tetris.tetris import tetris as GameClass
from tetris.tetris import rows as GUI_ROWS, cols as GUI_COLS
from modeltraining.agent_heuristic import SHAPES, W, H, reachable_move_first

@dataclass
class StepResult:
    lines_cleared: int
    score: int
    done: bool
    piece_index: int

class GuiTetrisEnv:
    def __init__(self, seed: int = 0):
        self.reset(seed)

    def reset(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.game = GameClass(GUI_ROWS, GUI_COLS)
        self.done = self.game.end
        self.piece_index = 0
        return self._obs()

    def _obs(self):
        board01 = [[1 if v > 0 else 0 for v in row] for row in self.game.grid]
        cur = self.game.fig
        piece = cur.type if cur is not None else None
        return {
            "board": board01,
            "piece": piece,
            "current": None if cur is None else {
                "type": cur.type,
                "x": cur.x,
                "y": cur.y,
                "rotation": cur.rotation,
            },
            "level": self.game.lvl,
        }

    def _apply_action(self, action: Optional[str]):
        if action is None:
            return
        if action == "a":
            self.game.left()
        elif action == "d":
            self.game.right()
        elif action == "w":
            self.game.rotate()
        elif action == "s":
            self.game.fast_drop()
        elif action == " ":
            self.game.freefall()

    def _gravity(self):
        self.game.move()

    def step_place(self, target_rot: int, target_x: int) -> StepResult:
        if self.game.end:
            self.done = True
            return StepResult(0, self.game.score, True, self.piece_index)

        obs = self._obs()
        piece = obs["piece"]
        if piece is None:
            self.done = True
            return StepResult(0, self.game.score, True, self.piece_index)

        can_reach = reachable_move_first(obs["board"], piece, target_rot, target_x)

        score_before = self.game.score
        filled_before = sum(v > 0 for row in self.game.grid for v in row)

        guard = H + 32
        while not self.game.end and guard > 0:
            guard -= 1

            try:
                pygame.event.pump()
            except Exception:
                pass

            act = None
            cur = self.game.fig
            if can_reach and cur is not None:
                if cur.x < target_x:
                    act = "d"
                elif cur.x > target_x:
                    act = "a"
                else:
                    if (cur.rotation % len(SHAPES[piece])) != (target_rot % len(SHAPES[piece])):
                        act = "w"
                    else:
                        act = " "

            self._apply_action(act)
            self._gravity()

            if self.game.end:
                break

            filled_now = sum(v > 0 for row in self.game.grid for v in row)
            if filled_now != filled_before:
                self.piece_index += 1
                break

        lines = self.game.score - score_before
        self.done = self.game.end
        return StepResult(lines, self.game.score, self.done, self.piece_index)
