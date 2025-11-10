# 🧠 Auto-cognito — Tetris AI Bot  

A high-performance **AI Tetris agent** that plays the game entirely autonomously.  
It evaluates all possible placements of each falling piece using a **linear heuristic model**, with weights trained via a **Genetic Algorithm (GA)**.

---

## 🎮 Overview

The bot runs inside the competition Tetris engine.  
Each frame, it receives the full board state (`grid`, `current_piece`, `level`) and returns a keypress (`a/d/w/s/space`).

---

## 🧩 Gameplay

At every frame, the bot:
1. **Simulates every possible placement** of the current piece (across all rotations and x-positions).
2. **Clears full lines** in the simulated board and computes six features:
   - Aggregate column height  
   - Number of holes  
   - Surface bumpiness  
   - Maximum column height  
   - Row transitions  
   - Column transitions
3. **Scores** each resulting board using the learned weight vector:  
   $\text{score}=\sum_{i=1}^{6} w_i f_i + 0.760666 \cdot \text{(lines cleared)}$

4. Picks the **highest-scoring placement**, then issues keypresses to reach it:
   - Rotates (`w`) to the correct orientation  
   - Moves horizontally (`a`/`d`) toward target  
   - Hard-drops (`space`) when aligned

If gravity is fast (level ≥ 10), the bot estimates how far a piece can physically move before falling and only aims for reachable columns.

---

## 🧬 Machine Learning

The 6 feature weights in `weights.json` were found using a **Genetic Algorithm**:
- Each genome is a 6-number vector of weights.  
- A population of candidate agents plays multiple Tetris games.  
- *Fitness* = average lines cleared per game.  
- The top performers are kept (elitism), then crossover and random Gaussian mutation generate the next generation.  
- After ~10 generations, the best-performing vector becomes the final weight set.


---

## 📁 Structure

```
.
├─ player/
│  ├─ bot.py           # The live competition bot (uses weights.json)
│  └─ weights.json     # Learned 6-feature weight vector
└─ modeltraining/
   ├─ agent_heuristic.py   # Feature extraction and move scoring
   └─ train_gui_ga.py      # Genetic Algorithm trainer
```

---

## 🚀 Usage

1. Ensure `weights.json` is in `player/`.
2. Run the game:

   ```
   python main.py
   ```
3. The bot automatically takes control and plays.
To retrain:
    ```
    cd modeltraining
    python train_gui_ga.py
    ```

---
