import json
from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

ACOES = {
    "B3": "B3SA3.SA",
    "Petrobras": "PETR4.SA",
    "Itaú": "ITUB4.SA",
}

PERIODOS_VALIDOS = {"1mo", "3mo", "6mo", "1y"}
CORES = {"B3": "#00b4d8", "Petrobras": "#48cae4", "Itaú": "#f77f00"}

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


def buscar_historico(periodo="1mo"):
    tickers = list(ACOES.values())
    df = yf.download(tickers, period=periodo, auto_adjust=True, progress=False)["Close"]
    df = df.dropna(how="all")
    result = {}
    for nome, ticker in ACOES.items():
        serie = df[ticker].dropna()
        result[nome] = {
            "datas": serie.index.strftime("%Y-%m-%d").tolist(),
            "precos": [round(float(v), 2) for v in serie.values],
        }
    return result


def buscar_resumo():
    resumo = {}
    for nome, ticker in ACOES.items():
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

    comparativo = {}
    for nome, dados in historico.items():
        comparativo[nome] = {
            "datas": dados["datas"],
            "perc": normalizar_serie(dados["precos"]),
            "cor": CORES[nome],
        }

    for nome in historico:
        historico[nome]["cor"] = CORES[nome]

    return render_template(
        "index.html",
        resumo=resumo,
        historico=json.dumps(historico),
        comparativo=json.dumps(comparativo),
        cores=CORES,
    )


@app.route("/api/dados")
def api_dados():
    periodo = request.args.get("periodo", "1mo")
    if periodo not in PERIODOS_VALIDOS:
        return jsonify({"erro": "Período inválido"}), 400

    historico = buscar_historico(periodo)
    comparativo = {}
    for nome, dados in historico.items():
        comparativo[nome] = {
            "datas": dados["datas"],
            "perc": normalizar_serie(dados["precos"]),
            "cor": CORES[nome],
        }
        historico[nome]["cor"] = CORES[nome]

    return jsonify({"historico": historico, "comparativo": comparativo})


@app.route("/api/resumo")
def api_resumo():
    return jsonify(buscar_resumo())


@app.route("/api/ticker")
def api_ticker():
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
    return jsonify(resultado)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
