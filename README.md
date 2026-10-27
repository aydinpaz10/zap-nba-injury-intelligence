# Zap NBA Injury Intelligence

**An NBA forecasting and analytics platform combining injury reports, player performance data, and statistical modeling to evaluate how player availability affects game outcomes.**

🌐 **Live Website:** https://zapnba.com

## Overview

Zap NBA Injury Intelligence is a web-based forecasting platform I developed to analyze NBA injuries, player production, and game outcomes.

The platform covers all 30 NBA teams and combines automated data pipelines, player ratings, statistical forecasting models, and historical model validation.

This repository includes a public showcase of the **actual production-derived forecasting algorithms**, along with validation methods, synthetic examples, and tests.

## Key Features

- **Game Predictions:** Win probabilities, predicted scores, and injury-adjusted forecasts.
- **Injury Reports:** Player availability information from official NBA injury reports.
- **Player Ratings:** Estimates of player production above replacement level.
- **Results Tracking:** Comparisons between archived pregame forecasts and actual outcomes.
- **Model Validation:** Historical backtesting and forecasting error analysis.
- **Automated Updates:** Scheduled refreshes of game, player, and injury information.

## Forecasting Models

### 1. Win Probability Model

Baseline and injury-adjusted logistic regression models estimate game win probabilities using features including:

- Prior team strength and recent performance
- Home-court advantage
- Rest and back-to-back schedules
- Estimated missing player production

The injury-adjusted model incorporates player availability to estimate how absences may change predicted outcomes.

**Code:** `models/predictor.mjs`, `models/engine_math.py`

### 2. Player Rating Model

Player ratings estimate box-score production above replacement using Game Score per 36 minutes.

The methodology includes:

- Up to 30 prior appearances within 365 days
- Minimum observed-minute requirements
- Shrinkage to stabilize smaller samples
- Replacement-level benchmarking

These ratings are statistical production proxies, not causal estimates of individual player impact.

**Code:** `models/engine_math.py`

### 3. Score Prediction Model

A constrained ridge regression model predicts team scores using historical offensive and defensive performance, pace, rest, home-court advantage, and player-availability proxies.

**Code:** `models/score-model.mjs`, `models/score_math.py`

## Model Validation

The project includes historical evaluation protocols, chronological feature construction, and uncertainty estimation.

**Important methodological limitations:**

- Historical win-model evaluation used lagged participation proxies rather than confirmed historical injury designations.
- The score-model evaluation was exploratory, not an untouched holdout.
- Historical training data and fitted production coefficients are excluded from this public repository.

See the `validation/` directory for the methodology and evaluation code.

## Repository Structure

| Directory | Contents |
|---|---|
| `models/` | Forecasting algorithms, player calculations, and fitting methods |
| `validation/` | Training, evaluation, uncertainty estimation, and protocols |
| `tests/` | Synthetic model and training tests |
| `examples/` | Runnable fictional NBA forecasting example |
| `prototype/` | Original Python injury-tracking application |

## Run the Models and Tests

The public repository provides a runnable synthetic example without requiring historical NBA data.

**Requirements:** Python 3.12, Node.js 24, and the pinned Python dependencies.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run the synthetic forecasting demonstration:

```bash
node examples/demo.mjs
```

Run the tests:

```bash
node --test tests/*.test.mjs
python -m unittest discover -s tests -p 'test_*.py' -v
```

The synthetic coefficients, teams, and players are fictional. These tests demonstrate model behavior and implementation checks; they do not reproduce the original historical evaluation.

## Technology Stack

- **Python:** Statistical modeling, data processing, and validation
- **JavaScript (Node.js):** Forecasting inference
- **SQL / SQLite:** Historical data storage and feature preparation
- **NumPy, SciPy, scikit-learn:** Numerical methods and model fitting
- **Statistical Methods:** Logistic regression, ridge regression, shrinkage estimation, chronological backtesting, and uncertainty analysis

## Data and Reproducibility

The repository intentionally excludes third-party historical game records, production coefficients, saved forecasts, private databases, and administrative infrastructure.

The historical evaluation and production-model training cannot be reproduced from the public repository alone. They require separately authorized historical data and evaluation artifacts.

See [PUBLICATION_REVIEW.md](PUBLICATION_REVIEW.md) for publication scope and data-rights considerations.

## Live Demo

Explore the deployed application: **https://zapnba.com**

The live website provides the full interactive forecasting experience, while this repository demonstrates selected underlying statistical and engineering methods.

## License

Original project code is available under the [MIT License](LICENSE). Third-party data and dependencies remain subject to their respective terms.

## Author

**Aydin Paz**  
Statistics & Data Science  
University of Texas at Austin
