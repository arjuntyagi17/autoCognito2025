"""
================================================================================
TETRIS BOT - ML CHALLENGE
================================================================================

OBJECTIVE:
----------
Build an ML/AI bot that plays Tetris by implementing the `decide()` method below.
Your bot will receive game state information and must return the action to take.

HOW IT WORKS:
-------------
1. The game calls `bot.decide(obs)` approximately every 120ms (8-9 times per second)
2. Your bot receives a dictionary (`obs`) containing complete game state
3. You analyze the state and return one action string
4. The game executes your action and continues

IMPORTS YOU MIGHT NEED:
-----------------------
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any

# Add your imports here (numpy, tensorflow, pytorch, etc.)
# import numpy as np
# import torch
# from your_model import YourModel


"""
================================================================================
IMPLEMENT YOUR BOT HERE
================================================================================
"""


class Bot:
    def __init__(self) -> None:
        pass


    def decide(self, obs: Optional[dict]) -> Optional[str]:
        if not hasattr(self, "_weights"):
            import json
            from pathlib import Path
            wpath = Path(__file__).with_name("weights.json")
            with open(wpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._weights = [float(x) for x in data]

        LINES_BONUS = 0.760666

        if obs is None:
            return None
        grid = obs.get("grid")
        cur = obs.get("current_piece")
        level = int(obs.get("level", 1) or 1)
        if grid is None or cur is None:
            return None

        H = len(grid)
        W = len(grid[0]) if H else 0
        SPEEDY = (level >= 10)

        SHAPES = {
            "I": [[1, 5, 9, 13], [4, 5, 6, 7]],
            "Z": [[4, 5, 9, 10], [2, 6, 5, 9]],
            "S": [[6, 7, 9, 10], [1, 5, 6, 10]],
            "L": [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 9, 8], [4, 5, 6, 10]],
            "J": [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]],
            "T": [[1, 4, 5, 6], [1, 4, 5, 9], [4, 5, 6, 9], [1, 5, 6, 9]],
            "O": [[1, 2, 5, 6]],
        }


        def clone(b):
            return [row[:] for row in b]


        def remove_current(b, cells):
            out = clone(b)
            if cells:
                for (r, c) in cells:
                    if 0 <= r < H and 0 <= c < W:
                        out[r][c] = 0
            return out


        def collision(board, mask, x, y):
            for idx in mask:
                i, j = divmod(idx, 4)
                rr, cc = y + i, x + j
                if rr < 0 or rr >= H or cc < 0 or cc >= W:
                    return True
                if board[rr][cc] > 0:
                    return True
            return False


        def drop_y(board, mask, x):
            y = 0
            while not collision(board, mask, x, y + 1):
                y += 1
                if y >= H:
                    break
            if collision(board, mask, x, y):
                return None
            return y


        def place_and_clear(board, mask, x, y):
            b = clone(board)
            for idx in mask:
                i, j = divmod(idx, 4)
                rr, cc = y + i, x + j
                if 0 <= rr < H and 0 <= cc < W:
                    b[rr][cc] = 1
            cleared = 0
            write = H - 1
            for r in range(H - 1, -1, -1):
                if all(b[r][c] > 0 for c in range(W)):
                    cleared += 1
                else:
                    if write != r:
                        b[write] = b[r][:]
                    write -= 1
            for r in range(write, -1, -1):
                b[r] = [0] * W
            return cleared, b


        def col_heights(board):
            heights = [0] * W
            for c in range(W):
                h = 0
                for r in range(H):
                    if board[r][c] > 0:
                        h = H - r
                        break
                heights[c] = h
            return heights


        def count_holes(board, heights):
            holes = 0
            for c in range(W):
                top = H - heights[c]
                for r in range(top + 1, H):
                    if board[r][c] == 0:
                        holes += 1
            return holes


        def row_transitions(board):
            trans = 0
            for r in range(H):
                prev = 1
                for c in range(W):
                    curv = 1 if board[r][c] > 0 else 0
                    if curv != prev:
                        trans += 1
                    prev = curv
                if prev == 0:
                    trans += 1
            return trans


        def col_transitions(board):
            trans = 0
            for c in range(W):
                prev = 1
                for r in range(H):
                    curv = 1 if board[r][c] > 0 else 0
                    if curv != prev:
                        trans += 1
                    prev = curv
                if prev == 0:
                    trans += 1
            return trans


        def features(board):
            heights = col_heights(board)
            agg_h = sum(heights)
            holes = count_holes(board, heights)
            bump = sum(abs(heights[i] - heights[i + 1]) for i in range(W - 1))
            max_h = max(heights) if heights else 0
            rtr = row_transitions(board)
            ctr = col_transitions(board)
            return (agg_h, holes, bump, max_h, rtr, ctr)


        def score_board(board, lines_cleared):
            f = features(board)
            return sum(w * v for w, v in zip(self._weights, f)) + LINES_BONUS * lines_cleared


        def x_bounds(mask):
            js = [idx % 4 for idx in mask]
            return -min(js), (W - 1 - max(js))


        base_board = remove_current(grid, cur.get("cells"))
        ptype = cur.get("type")
        if ptype not in SHAPES:
            return None

        best = None
        for r_idx, mask in enumerate(SHAPES[ptype]):
            xmin, xmax = x_bounds(mask)
            for x in range(xmin, xmax + 1):
                y = drop_y(base_board, mask, x)
                if y is None:
                    continue
                cleared, after = place_and_clear(base_board, mask, x, y)
                s = score_board(after, cleared)
                if (best is None) or (s > best[0]):
                    best = (s, r_idx, x, y)
        if best is None:
            return " "

        target_rot, target_x = best[1], best[2]

        cur_x = int(cur.get("x", 0))
        cur_y = int(cur.get("y", 0))
        cur_rot = int(cur.get("rotation", 0))
        mask_now = SHAPES[ptype][cur_rot % len(SHAPES[ptype])]
        mask_rot = SHAPES[ptype][target_rot % len(SHAPES[ptype])]

        if SPEEDY:
            dist = abs(target_x - cur_x)
            rem = 0
            while not collision(base_board, mask_now, cur_x, cur_y + 1 + rem) and (cur_y + rem) < H:
                rem += 1
            if dist > rem + 1:
                if target_x > cur_x:
                    target_x = cur_x + min(dist, max(1, rem // 2))
                else:
                    target_x = cur_x - min(dist, max(1, rem // 2))

        if (cur_rot % len(SHAPES[ptype])) != (target_rot % len(SHAPES[ptype])):
            if not collision(base_board, mask_rot, cur_x, cur_y):
                return "w"
            dir_right = 1 if target_x > cur_x else -1
            nx = cur_x + dir_right
            if 0 <= nx < W and not collision(base_board, mask_now, nx, cur_y):
                return "d" if dir_right == 1 else "a"
            nx = cur_x - dir_right
            if 0 <= nx < W and not collision(base_board, mask_now, nx, cur_y):
                return "a" if dir_right == 1 else "d"
            if not SPEEDY and not collision(base_board, mask_now, cur_x, cur_y + 1):
                return "s"
            return None

        if cur_x < target_x:
            nx = cur_x + 1
            if not collision(base_board, mask_now, nx, cur_y):
                return "d"
            if not SPEEDY and not collision(base_board, mask_now, cur_x, cur_y + 1):
                return "s"
            return None
        elif cur_x > target_x:
            nx = cur_x - 1
            if not collision(base_board, mask_now, nx, cur_y):
                return "a"
            if not SPEEDY and not collision(base_board, mask_now, cur_x, cur_y + 1):
                return "s"
            return None

        return " "