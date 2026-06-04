# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the development server (port 5001)
python app.py
```

There are no tests or linting configured.

## Architecture

Single-file Flask app (`app.py`) that fetches Brazilian stock quotes from Yahoo Finance and renders them as interactive Plotly.js charts.

**Data flow:**
- On page load, the server fetches data via `yfinance`, renders it into the Jinja2 template as JSON blobs (`HISTORICO_INICIAL`, `COMPARATIVO_INICIAL`), and Plotly initializes charts client-side.
- Period changes (1M/3M/6M/1A) and the refresh button call `/api/dados?periodo=<p>`, which returns fresh JSON and re-renders charts via `Plotly.react`.

**Three stocks are hardcoded** in `ACOES` and `CORES` dicts in `app.py` — adding a new ticker requires updating both dicts and the `DIV_IDS` map in `index.html`.

**`normalizar_serie`** converts raw prices to cumulative % change from the first data point, used exclusively in the comparative chart.

**Routes:**
- `GET /` — server-side render with initial data baked in
- `GET /api/dados?periodo=` — returns `{historico, comparativo}` JSON for client-side updates
- `GET /api/resumo` — returns current price + daily % change per ticker (fetches last 2 trading days)

**Frontend** lives entirely in `templates/index.html` (inline `<script>`); styles in `static/css/style.css` use CSS custom properties with a GitHub-dark color palette.
