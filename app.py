import json
import time
from datetime import date, timedelta
from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

ACOES = {
    "B3": "B3SA3.SA",
    "Petrobras": "PETR4.SA",
    "Itaú": "ITUB4.SA",
}
TICKERS_INICIAIS = ["B3SA3", "PETR4", "ITUB4"]
PALETTE = ["#2196f3", "#f77f00", "#3fb950"]
CORES = {"B3": "#2196f3", "Petrobras": "#f77f00", "Itaú": "#3fb950"}

PERIODOS_VALIDOS = {"1mo", "3mo", "6mo", "1y", "2y", "3y", "4y", "5y"}
_PERIODO_YF_NATIVO = {"1mo", "3mo", "6mo", "1y", "2y", "5y"}

MOEDAS_TICKERS = {
    "USD": ("USDBRL=X", "R$"),
    "EUR": ("EURBRL=X", "R$"),
    "GBP": ("GBPBRL=X", "R$"),
    "JPY": ("JPYBRL=X", "R$"),
    "CAD": ("CADBRL=X", "R$"),
    "AUD": ("AUDBRL=X", "R$"),
    "CHF": ("CHFBRL=X", "R$"),
    "CNY": ("CNYBRL=X", "R$"),
    "HKD": ("HKDBRL=X", "R$"),
    "NZD": ("NZDBRL=X", "R$"),
    "SGD": ("SGDBRL=X", "R$"),
    "SEK": ("SEKBRL=X", "R$"),
    "KRW": ("KRWBRL=X", "R$"),
    "NOK": ("NOKBRL=X", "R$"),
    "MXN": ("MXNBRL=X", "R$"),
    "INR": ("INRBRL=X", "R$"),
    "RUB": ("RUBBRL=X", "R$"),
    "ZAR": ("ZARBRL=X", "R$"),
    "TRY": ("TRYBRL=X", "R$"),
}

CRIPTO_TICKERS = {
    "BTC":  ("BTC-USD",  "US$"),
    "ETH":  ("ETH-USD",  "US$"),
    "USDT": ("USDT-USD", "US$"),
    "BNB":  ("BNB-USD",  "US$"),
    "SOL":  ("SOL-USD",  "US$"),
    "USDC": ("USDC-USD", "US$"),
    "XRP":  ("XRP-USD",  "US$"),
    "DOGE": ("DOGE-USD", "US$"),
    "ADA":  ("ADA-USD",  "US$"),
    "TON":  ("TON-USD",  "US$"),
    "AVAX": ("AVAX-USD", "US$"),
    "SHIB": ("SHIB-USD", "US$"),
    "TRX":  ("TRX-USD",  "US$"),
    "LINK": ("LINK-USD", "US$"),
    "BCH":  ("BCH-USD",  "US$"),
    "DOT":  ("DOT-USD",  "US$"),
    "XLM":  ("XLM-USD",  "US$"),
    "PEPE": ("PEPE-USD", "US$"),
    "UNI":  ("UNI-USD",  "US$"),
    "NEAR": ("NEAR-USD", "US$"),
}

IBOVESPA_TICKERS = [
    "ABEV3", "ASAI3", "AZUL4", "B3SA3", "BBAS3", "BBDC3", "BBDC4",
    "BPAC11", "BRAP4", "BRFS3", "BRKM5", "CCRO3", "CMIG4", "COGN3",
    "CPFE3", "CSAN3", "CYRE3", "DXCO3", "EGIE3", "ELET3", "ELET6",
    "EMBR3", "ENEV3", "ENGI11", "EQTL3", "FLRY3", "GGBR4", "GOAU4",
    "GOLL4", "HAPV3", "HYPE3", "IGTI11", "IRBR3", "ITSA4", "ITUB4",
    "JBSS3", "KLBN11", "LREN3", "MGLU3", "MRFG3", "MRVE3", "MULT3",
    "NTCO3", "PETR3", "PETR4", "PETZ3", "PRIO3", "QUAL3", "RADL3",
    "RAIL3", "RDOR3", "RENT3", "SANB11", "SBSP3", "SLCE3", "SUZB3",
    "TAEE11", "TIMS3", "TOTS3", "UGPA3", "USIM5", "VALE3", "VBBR3",
    "VIVT3", "WEGE3", "YDUQ3",
]


def buscar_historico(periodo="1mo", acoes=None):
    if acoes is None:
        acoes = ACOES
    tickers = list(acoes.values())
    if periodo in _PERIODO_YF_NATIVO:
        df = yf.download(tickers, period=periodo, auto_adjust=True, progress=False)["Close"]
    else:
        anos = int(periodo[0])
        start = (date.today() - timedelta(days=365 * anos)).isoformat()
        df = yf.download(tickers, start=start, auto_adjust=True, progress=False)["Close"]
    if isinstance(df, pd.Series):
        df = df.to_frame(name=tickers[0])
    df = df.dropna(how="all")
    result = {}
    for nome, ticker in acoes.items():
        try:
            serie = df[ticker].dropna()
        except KeyError:
            continue
        result[nome] = {
            "datas": serie.index.strftime("%Y-%m-%d").tolist(),
            "precos": [round(float(v), 2) for v in serie.values],
        }
    return result


def buscar_resumo(acoes=None):
    if acoes is None:
        acoes = ACOES
    resumo = {}
    for nome, ticker in acoes.items():
        ativo = yf.Ticker(ticker)
        hist = ativo.history(period="2d")
        if len(hist) >= 2:
            preco_atual = float(hist["Close"].iloc[-1])
            preco_anterior = float(hist["Close"].iloc[-2])
            variacao = ((preco_atual - preco_anterior) / preco_anterior) * 100
        elif len(hist) == 1:
            preco_atual = float(hist["Close"].iloc[-1])
            variacao = 0.0
        else:
            preco_atual = 0.0
            variacao = 0.0
        resumo[nome] = {
            "preco": round(preco_atual, 2),
            "variacao": round(variacao, 2),
        }
    return resumo


def normalizar_serie(precos):
    if not precos or precos[0] == 0:
        return precos
    base = precos[0]
    return [round((p / base - 1) * 100, 2) for p in precos]


@app.route("/")
def index():
    historico = buscar_historico("1mo")
    resumo = buscar_resumo()

    # Use ticker codes as keys so frontend selecionados[] aligns with chart slots
    historico_coded = {}
    comparativo_coded = {}
    resumo_ext = []
    for nome, ticker_sa in ACOES.items():
        codigo = ticker_sa.replace(".SA", "")
        cor = CORES[nome]
        if nome not in historico:
            continue
        historico_coded[codigo] = {**historico[nome], "cor": cor}
        comparativo_coded[codigo] = {
            "datas": historico[nome]["datas"],
            "perc": normalizar_serie(historico[nome]["precos"]),
            "cor": cor,
        }
        resumo_ext.append({
            "ticker": codigo,
            "preco": resumo[nome]["preco"],
            "variacao": resumo[nome]["variacao"],
        })

    return render_template(
        "index.html",
        resumo_ext=resumo_ext,
        historico=json.dumps(historico_coded),
        comparativo=json.dumps(comparativo_coded),
        tickers_iniciais=TICKERS_INICIAIS,
        ibovespa_tickers=IBOVESPA_TICKERS,
    )


def _acoes_e_cores_from_param(tickers_param):
    codigos = [t.strip().upper() for t in tickers_param.split(",")][:3]
    acoes = {c: c + ".SA" for c in codigos}
    cores = {c: PALETTE[i] for i, c in enumerate(codigos)}
    return acoes, cores


@app.route("/api/dados")
def api_dados():
    periodo = request.args.get("periodo", "1mo")
    if periodo not in PERIODOS_VALIDOS:
        return jsonify({"erro": "Período inválido"}), 400

    tickers_param = request.args.get("tickers")
    if tickers_param:
        acoes_uso, cores_uso = _acoes_e_cores_from_param(tickers_param)
    else:
        acoes_uso, cores_uso = ACOES, CORES

    historico = buscar_historico(periodo, acoes=acoes_uso)
    comparativo = {}
    for nome, dados in historico.items():
        cor = cores_uso.get(nome, PALETTE[0])
        comparativo[nome] = {
            "datas": dados["datas"],
            "perc": normalizar_serie(dados["precos"]),
            "cor": cor,
        }
        historico[nome]["cor"] = cor

    return jsonify({"historico": historico, "comparativo": comparativo})


@app.route("/api/resumo")
def api_resumo():
    tickers_param = request.args.get("tickers")
    if tickers_param:
        acoes_uso, _ = _acoes_e_cores_from_param(tickers_param)
    else:
        acoes_uso = ACOES
    return jsonify(buscar_resumo(acoes_uso))


_ibovespa_cache: dict = {"data": None, "ts": 0.0}


def _buscar_ibovespa():
    now = time.time()
    if _ibovespa_cache["data"] and now - _ibovespa_cache["ts"] < 300:
        return _ibovespa_cache["data"]
    tickers_sa = [t + ".SA" for t in IBOVESPA_TICKERS]
    df = yf.download(tickers_sa, period="2d", auto_adjust=True, progress=False)["Close"]
    resultado = []
    for codigo, ticker in zip(IBOVESPA_TICKERS, tickers_sa):
        try:
            serie = df[ticker].dropna()
            if len(serie) >= 2:
                preco = round(float(serie.iloc[-1]), 2)
                variacao = round(
                    ((float(serie.iloc[-1]) - float(serie.iloc[-2])) / float(serie.iloc[-2])) * 100, 2
                )
            elif len(serie) == 1:
                preco = round(float(serie.iloc[-1]), 2)
                variacao = 0.0
            else:
                continue
            resultado.append({"ticker": codigo, "preco": preco, "variacao": variacao})
        except Exception:
            continue
    _ibovespa_cache["data"] = resultado
    _ibovespa_cache["ts"] = now
    return resultado


@app.route("/api/ticker")
def api_ticker():
    return jsonify(_buscar_ibovespa())


_moedas_cache: dict = {"data": None, "ts": 0.0}


def _buscar_moedas_cripto():
    now = time.time()
    if _moedas_cache["data"] and now - _moedas_cache["ts"] < 300:
        return _moedas_cache["data"]

    todos = {**{c: t for c, (t, _) in MOEDAS_TICKERS.items()},
             **{c: t for c, (t, _) in CRIPTO_TICKERS.items()}}
    simbolos = list(todos.values())
    df = yf.download(simbolos, period="2d", auto_adjust=True, progress=False)["Close"]
    if isinstance(df, pd.Series):
        df = df.to_frame(name=simbolos[0])

    resultado = []
    for grupo, mapa in (("forex", MOEDAS_TICKERS), ("cripto", CRIPTO_TICKERS)):
        for codigo, (ticker, moeda) in mapa.items():
            try:
                serie = df[ticker].dropna()
                v = float(serie.iloc[-1])
                if grupo == "forex":
                    decimais = 4 if v < 1 else 2
                else:
                    decimais = 8 if v < 0.0001 else (6 if v < 0.01 else (4 if v < 1 else 2))
                if len(serie) >= 2:
                    preco = round(v, decimais)
                    variacao = round(
                        ((v - float(serie.iloc[-2])) / float(serie.iloc[-2])) * 100, 2
                    )
                elif len(serie) == 1:
                    preco = round(v, decimais)
                    variacao = 0.0
                else:
                    continue
                resultado.append({"codigo": codigo, "preco": preco, "variacao": variacao,
                                   "moeda": moeda, "tipo": grupo})
            except Exception:
                continue

    _moedas_cache["data"] = resultado
    _moedas_cache["ts"] = now
    return resultado


@app.route("/api/moedas-cripto")
def api_moedas_cripto():
    return jsonify(_buscar_moedas_cripto())


@app.route("/api/destaques")
def api_destaques():
    dados = _buscar_ibovespa()
    ordenado = sorted(dados, key=lambda x: x["variacao"], reverse=True)
    return jsonify({
        "altas":  ordenado[:10],
        "baixas": ordenado[-10:][::-1],
    })


if __name__ == "__main__":
    app.run(debug=True, port=5001)
