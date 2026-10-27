# Zap NBA Injury Intelligence

**An NBA forecasting and analytics platform that combines injury reports, player performance data, and predictive modeling to evaluate how player availability affects game outcomes.**

🌐 **Live Website:** https://zapnba.com

## Overview

Zap NBA Injury Intelligence is a web-based platform I developed to make NBA injury information more accessible and quantify its potential impact on game predictions.

The platform tracks all 30 NBA teams, combines player statistics with injury information, and generates game forecasts using statistical models built with Python and SQL.

## Key Features

- **Game Predictions:** Predicted scores, win probabilities, and injury-adjusted forecasts.
- **Injury Reports:** Player availability information sourced from official NBA injury reports.
- **Player Ratings:** Statistical ratings estimating player production above replacement level.
- **Results Tracking:** Compares archived pregame predictions against actual game outcomes.
- **Model Validation:** Evaluates forecasting accuracy using historical NBA game data.
- **Automated Updates:** Scheduled data refreshes to maintain current information.

## Technology

- **Python:** Data processing, statistical modeling, and forecasting
- **SQL (SQLite):** Structured data storage and analysis
- **Statistical Modeling:** Player evaluation, game prediction, and model validation
- **Automated Data Pipelines:** Injury-report ingestion and data updates

## Model Development & Validation

I evaluated the forecasting models on 1,230 held-out NBA games.

| Metric | Result |
|---|---|
| Baseline win-model log loss | 0.6003 |
| Injury-adjusted win-model log loss | 0.5986 |
| Predicted team score MAE | 9.65 points |
| Baseline team score MAE | 9.77 points |

The injury-adjusted model showed a small improvement in log loss, although the improvement was not statistically conclusive.

These results illustrate both the potential value and limitations of incorporating player availability into NBA forecasting.

## Project Goals

1. Make NBA injury information easier to understand.
2. Quantify how player absences may influence team performance.
3. Evaluate predictions against actual outcomes.
4. Develop transparent, reproducible statistical forecasting methods.
5. Present complex analytical information through an accessible website.

## Live Demo

Explore the platform at **https://zapnba.com**.

## Author

**Aydin Paz**  
Statistics & Data Science — University of Texas at Austin  
[LinkedIn](https://linkedin.com/in/aydinpaz)
