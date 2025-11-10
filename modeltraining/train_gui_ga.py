from __future__ import annotations
import statistics, random, sys, json
from typing import List, Tuple
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from gui_env import GuiTetrisEnv
from agent_heuristic import HeuristicAgent, BASE_W

POP = 12
ELITE = 3
MUT_RATE = 0.6
MUT_STD = 0.15
GAMES_PER_EVAL = 3
MAX_PIECES_PER_GAME = 800
GENERATIONS = 10

from types import SimpleNamespace

def play_game(agent: HeuristicAgent, seed: int) -> Tuple[int, int]:
    env = GuiTetrisEnv(seed=seed)
    pieces = 0
    total_lines = 0
    while not env.done and pieces < MAX_PIECES_PER_GAME:
        obs = env._obs()
        p = obs["piece"]
        if p is None:
            break
        shim = SimpleNamespace(board=obs["board"], piece=p)
        r, x = agent.choose_action(shim)
        res = env.step_place(r, x)
        total_lines += res.lines_cleared
        pieces += 1
    return total_lines, pieces


def eval_genome(weights: List[float], base_seed: int, idx: int, total: int) -> Tuple[float, float]:
    agent = HeuristicAgent(weights)
    scores, lpps = [], []
    for k in range(GAMES_PER_EVAL):
        lines, pieces = play_game(agent, base_seed + 7919 * k)
        scores.append(lines)
        lpps.append(lines / max(1, pieces))
    s = statistics.mean(scores)
    lpp = statistics.mean(lpps)
    print(f"  eval {idx+1:02d}/{total:02d}: lines={s:.1f}  LPP≈{lpp:.3f}", flush=True)
    return s, lpp

def mutate(weights: List[float], rng: random.Random) -> List[float]:
    w = list(weights)
    for i in range(len(w)):
        if rng.random() < MUT_RATE:
            w[i] += rng.gauss(0.0, MUT_STD)
    return w

def crossover(a: List[float], b: List[float], rng: random.Random) -> List[float]:
    cut = rng.randrange(1, len(a))
    return a[:cut] + b[cut:]

def smoke_test():
    print("Smoke test (GUI-backed): baseline one game...", flush=True)
    agent = HeuristicAgent(BASE_W)
    lines, pieces = play_game(agent, seed=0)
    print(f"  baseline -> lines={lines}, pieces={pieces}, LPP≈{lines/max(1,pieces):.3f}\n", flush=True)

def eval_many(weights, seeds=20):
    agent = HeuristicAgent(weights)
    totals, lpps = [], []
    for k in range(seeds):
        lines, pieces = play_game(agent, seed=100000 + k)
        totals.append(lines)
        lpps.append(lines / max(1, pieces))
    print(
        f"Final check over {seeds} seeds: "
        f"avg lines={statistics.mean(totals):.1f} ± {statistics.pstdev(totals):.1f}, "
        f"avg LPP={statistics.mean(lpps):.3f}",
        flush=True,
    )

def train(seed: int = 0, generations: int = GENERATIONS):
    rng = random.Random(seed)
    pop = [[w + rng.gauss(0, 0.05) for w in BASE_W] for _ in range(POP)]
    best_w = pop[0]
    best_score = -1e9

    for gen in range(1, generations + 1):
        print(f"[gen {gen:02d}] evaluating population of {POP}...", flush=True)
        evals, gen_lpps = [], []
        for i, w in enumerate(pop):
            s, lpp = eval_genome(w, base_seed=seed + 101 * i + 3571 * gen, idx=i, total=len(pop))
            evals.append((s, w))
            gen_lpps.append(lpp)
        evals.sort(reverse=True, key=lambda t: t[0])
        scores = [s for s, _ in evals]
        mean_s = statistics.mean(scores)
        med_s = statistics.median(scores)
        best_s = scores[0]
        p90 = scores[max(0, int(0.1 * len(scores)) - 1)]
        print(
            f"[gen {gen:02d}] mean={mean_s:.2f}  med={med_s:.2f}  best={best_s:.2f}  p90={p90:.2f}  "
            f"LPP≈{statistics.mean(gen_lpps):.3f}",
            flush=True,
        )
        print(f"           best_w = {[round(x, 4) for x in evals[0][1]]}\n", flush=True)

        if best_s > best_score:
            best_score = best_s
            best_w = evals[0][1][:]

        elites = [w for _, w in evals[:ELITE]]
        next_pop = elites[:]
        while len(next_pop) < POP:
            p1, p2 = rng.sample(elites, 2)
            child = crossover(p1, p2, rng)
            child = mutate(child, rng)
            next_pop.append(child)
        pop = next_pop

    with open("best_weights.json", "w") as f:
        json.dump(best_w, f)
    print("\n=== Training done (GUI-backed) ===", flush=True)
    print("Best weights saved to best_weights.json", flush=True)
    print("Best weights:", [round(x, 6) for x in best_w], flush=True)
    eval_many(best_w, seeds=20)
    return best_w

if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    smoke_test()
    train(seed=0)
