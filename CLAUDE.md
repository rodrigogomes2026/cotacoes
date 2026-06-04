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

## GitHub — Auto-push

Repository: https://github.com/rodrigogomes2026/cotacoes

A `post-commit` hook (`.git/hooks/post-commit`) runs `git push origin main` automatically after every commit — no manual push needed.

To commit and sync changes:
```bash
git add <files>
git commit -m "mensagem"
# push happens automatically via the hook
```

If the hook is ever lost (e.g. after cloning), recreate it:
```bash
printf '#!/bin/sh\ngit push origin main 2>&1\n' > .git/hooks/post-commit
chmod +x .git/hooks/post-commit
```

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
