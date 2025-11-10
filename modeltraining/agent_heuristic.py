from __future__ import annotations
from typing import List, Tuple

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tetris.tetris import rows as H, cols as W

SHAPES = {
    "I": [[1, 5, 9, 13], [4, 5, 6, 7]],
    "Z": [[4, 5, 9, 10], [2, 6, 5, 9]],
    "S": [[6, 7, 9, 10], [1, 5, 6, 10]],
    "L": [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 9, 8], [4, 5, 6, 10]],
    "J": [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]],
    "T": [[1, 4, 5, 6], [1, 4, 5, 9], [4, 5, 6, 9], [1, 5, 6, 9]],
    "O": [[1, 2, 5, 6]],
}

BASE_W = (-0.510066, -0.35663, -0.184483, -0.18, -0.15, -0.30)
LINES_BONUS = 0.760666

def _coll(board: List[List[int]], mask: List[int], x: int, y: int) -> bool:
    for idx in mask:
        i, j = divmod(idx, 4)
        rr, cc = y + i, x + j
        if rr < 0 or rr >= H or cc < 0 or cc >= W:
            return True
        if board[rr][cc]:
            return True
    return False

def features(board: List[List[int]]) -> Tuple[float, ...]:
    heights = []
    holes = 0
    for c in range(W):
        h = 0
        seen = False
        for r in range(H):
            if board[r][c]:
                if not seen:
                    h = H - r
                    seen = True
            elif seen:
                holes += 1
        heights.append(h)
    agg_h = sum(heights)
    bump = sum(abs(heights[i] - heights[i + 1]) for i in range(W - 1))
    max_h = max(heights) if heights else 0

    row_tr = 0
    for r in range(H):
        prev = 1
        for c in range(W):
            cur = 1 if board[r][c] else 0
            if cur != prev:
                row_tr += 1
            prev = cur
        if prev == 0:
            row_tr += 1

    col_tr = 0
    for c in range(W):
        prev = 1
        for r in range(H):
            cur = 1 if board[r][c] else 0
            if cur != prev:
                col_tr += 1
            prev = cur
        if prev == 0:
            col_tr += 1

    return (agg_h, holes, bump, max_h, row_tr, col_tr)

MAX_TICKS = H + 16
def reachable_move_first(board: List[List[int]], piece: str, target_rot: int, target_x: int) -> bool:
    rotations = SHAPES[piece]
    x, y, rot = 5, 0, 0
    if _coll(board, rotations[rot], x, y):
        return False
    ticks = 0
    while ticks < MAX_TICKS:
        ticks += 1
        mask_now = rotations[rot]
        mask_goal = rotations[target_rot]

        acted = False
        if x < target_x:
            nx = x + 1
            if not _coll(board, mask_now, nx, y):
                x = nx
                acted = True
        elif x > target_x:
            nx = x - 1
            if not _coll(board, mask_now, nx, y):
                x = nx
                acted = True
        else:
            if rot != target_rot and not _coll(board, mask_goal, x, y):
                rot = target_rot
                acted = True

        if not acted and x != target_x and rot != target_rot:
            if not _coll(board, mask_goal, x, y):
                rot = target_rot
                acted = True

        mask_now = rotations[rot]
        if _coll(board, mask_now, x, y + 1):
            return (rot == target_rot) and (x == target_x)
        y += 1
    return False

class HeuristicAgent:
    def __init__(self, weights=None):
        self.w = list(weights) if weights is not None else list(BASE_W)

    def _score_board(self, board: List[List[int]], lines_cleared: int) -> float:
        f = features(board)
        return sum(wi * fi for wi, fi in zip(self.w, f)) + LINES_BONUS * lines_cleared

    def choose_action(self, env_like) -> Tuple[int, int]:
        board = env_like.board
        piece = env_like.piece
        best = None
        for r_idx, mask in enumerate(SHAPES[piece]):
            js = [m % 4 for m in mask]
            xmin, xmax = -min(js), (W - 1 - max(js))
            for x in range(xmin, xmax + 1):
                y = 0
                while not _coll(board, mask, x, y + 1):
                    y += 1
                    if y >= H:
                        break
                if _coll(board, mask, x, y):
                    continue

                if not reachable_move_first(board, piece, r_idx, x):
                    continue

                tmp = [row[:] for row in board]
                for m in mask:
                    i, j = divmod(m, 4)
                    rr, cc = y + i, x + j
                    tmp[rr][cc] = 1

                cleared = 0
                write = H - 1
                for r in range(H - 1, -1, -1):
                    if all(tmp[r][c] for c in range(W)):
                        cleared += 1
                    else:
                        if write != r:
                            tmp[write] = tmp[r][:]
                        write -= 1
                for r in range(write, -1, -1):
                    tmp[r] = [0] * W

                s = self._score_board(tmp, cleared)
                if best is None or s > best[0]:
                    best = (s, r_idx, x)

        if best is None:
            return (0, max(0, min(W - 4, W // 2 - 2)))
        return best[1], best[2]
