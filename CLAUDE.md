# CLAUDE.md

Este arquivo fornece orientações ao Claude Code (claude.ai/code) ao trabalhar com o código deste repositório.

## Comandos

```bash
# Instalar dependências
pip3 install -r requirements.txt

# Iniciar o servidor de desenvolvimento (porta 5001)
python3 app.py
```

Não há testes nem linting configurados.

## GitHub — Push automático

Repositório: https://github.com/rodrigogomes2026/cotacoes

Um hook `post-commit` (`.git/hooks/post-commit`) executa `git push origin main` automaticamente após cada commit — não é necessário fazer push manual.

Para commitar e sincronizar alterações:
```bash
git add <arquivos>
git commit -m "mensagem"
# o push acontece automaticamente via hook
```

Se o hook for perdido (ex.: após clonar o repositório), recriá-lo com:
```bash
printf '#!/bin/sh\ngit push origin main 2>&1\n' > .git/hooks/post-commit
chmod +x .git/hooks/post-commit
```

Ao fazer commits, sempre usar:
```bash
git -c user.email="rgomes1977cpa@gmail.com" -c user.name="rodrigogomes2026" commit -m "mensagem"
```

## Arquitetura

Aplicação Flask em arquivo único (`app.py`) que busca cotações do Yahoo Finance e exibe gráficos interativos com Plotly.js.

### Fluxo de dados

- No carregamento da página, o servidor busca dados via `yfinance`, injeta-os no template Jinja2 como JSON (`HISTORICO_INICIAL`, `COMPARATIVO_INICIAL`) e o Plotly inicializa os gráficos no cliente.
- Troca de período (1M/3M/6M/1A/2A/3A/4A/5A) e o botão Atualizar chamam `/api/dados?periodo=<p>&tickers=<t1,t2,t3>`, que retorna JSON atualizado e re-renderiza via `Plotly.react`.
- A troca de ação nos cards chama `/api/resumo?tickers=` e `/api/dados?tickers=` em paralelo, atualizando preços e gráficos sem recarregar a página.

### Constantes principais em `app.py`

- `ACOES` / `TICKERS_INICIAIS` — as 3 ações exibidas por padrão (B3SA3, PETR4, ITUB4).
- `PALETTE` / `CORES` — cores das linhas dos gráficos: azul (`#2196f3`), laranja (`#f77f00`), verde (`#3fb950`).
- `IBOVESPA_TICKERS` — lista com ~65 tickers do IBOVESPA para o ticker rolante, destaques e seletor dos cards.
- `MOEDAS_TICKERS` — 19 pares de câmbio contra o BRL (USD, EUR, GBP, JPY etc.).
- `CRIPTO_TICKERS` — 20 criptomoedas em USD (BTC, ETH, USDT, BNB, SOL etc.).

### Cache

`_buscar_ibovespa()` e `_buscar_moedas_cripto()` usam cache em memória de 5 minutos para evitar múltiplas chamadas ao Yahoo Finance por página carregada.

### Rotas

| Rota | Descrição |
|---|---|
| `GET /` | Render server-side com dados iniciais embutidos |
| `GET /api/dados?periodo=&tickers=` | Histórico + comparativo para os 3 tickers selecionados |
| `GET /api/resumo?tickers=` | Preço atual + variação diária por ticker |
| `GET /api/ticker` | Cotações do IBOVESPA para a barra rolante |
| `GET /api/destaques` | Top 10 maiores altas e baixas do IBOVESPA |
| `GET /api/moedas-cripto` | Câmbio (forex) e criptomoedas para as barras rolantes |

### Frontend

Todo o JavaScript está embutido em `templates/index.html`. Os pontos-chave:

- `selecionados` — array com os 3 tickers atualmente selecionados nos cards; toda chamada de API usa esse array.
- `renderizarGraficos(historico, comparativo)` — itera `selecionados[i]` para garantir que o gráfico do slot `i` sempre corresponda ao card `i`.
- `SLOT_IDS` — IDs fixos dos divs dos gráficos individuais (`grafico-slot-0/1/2`).
- Barras rolantes: IBOVESPA (azul), CÂMBIO (azul), CRIPTO (azul) — todas com o mesmo estilo de label.

Os estilos em `static/css/style.css` usam variáveis CSS com paleta escura inspirada no GitHub Dark.
