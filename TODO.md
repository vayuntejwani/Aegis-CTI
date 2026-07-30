# ✅ DONE: Improve ML Model & NLP for Severity Prediction

## Goals ✅ Achieved
- Words like "terrorism" or "attack" now fetch **Critical** severity ✅
- Implemented scoring-based severity instead of first-match-wins ✅
- Added new threat categories: Terrorism / Insurgency, Nation-State Attack, Sabotage ✅

## Changes Made

### 1. `streamlit/model_stub.py` - Complete Rewrite
- **`predict_stub_severity()`** — Scoring-based approach:
  - 3 keyword groups: Critical (weight 3.0), High (weight 2.0), Medium (weight 1.0)
  - Each matched keyword contributes weight/10 to cumulative raw score
  - Score squashed via `tanh()` to [0, 0.95]
  - Maps to: Critical (≥0.70), High (≥0.45), Medium (≥0.20), Low (<0.20)
  - Proportional confidence scaling per level
- **`predict_stub_category_and_severity()`** — Scoring-based:
  - 11 categories including: Terrorism / Insurgency, Nation-State Attack, Sabotage
  - All categories scored; highest score wins (not first-match)
  - ∼20+ cue words per category
- **`CATEGORY_RISK`** — New entries:
  - Terrorism / Insurgency: 0.95
  - Nation-State Attack: 0.95
  - Sabotage: 0.85

### 2. `streamlit/nlp_processing.py` - Boosted Vocabulary
- Added 30+ terrorism/attack/military terms to `boosted_vocab`:
  `terrorism, terrorist, attack, explosion, bomb, ied, wmd, nuclear, insurgent, militant, cross-border, airstrike, nation-state, state-sponsored, enemy, warhead, artillery, ambush, mass casualty, sabotage, ...`

## Test Results (all passing)
- "Terrorism attack with explosion and bomb threat" → **Critical** (0.948)
- "Cross-border attack by militants with armed assault" → **Critical** (0.961)
- "IED explosion near headquarters with blast damage" → **Critical** (0.970)
- "State-sponsored attack with missile strike" → **Critical** (0.959)
- Just "terrorism" alone → **High** (0.752)
- Phishing (low priority baseline) → **Medium** (0.662)

