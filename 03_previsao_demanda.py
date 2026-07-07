"""
03_previsao_demanda.py
Data Foundation v2 — Previsão de Demanda (volume de cotações/mês)

LIMITAÇÃO DECLARADA: o funil principal (notebooks 01-02) tem 12 meses de
histórico (jan-dez/25) — insuficiente para validar sazonalidade com rigor
estatístico (regra prática: 2+ ciclos completos, ou seja, 24+ meses).

Este notebook usa dois datasets:
1. Serie_realista_12m: os 12 meses reais do projeto — usados para inspeção
   visual de tendência, não para forecast validado.
2. Serie_estendida_36m: extensão SINTÉTICA de 36 meses, gerada com a mesma
   lógica de volume médio + variação + leve sazonalidade, exclusivamente
   para demonstrar a metodologia de forecast (baseline + validação
   train/test) de forma estatisticamente defensável.

Isso é uma decisão de honestidade metodológica: melhor declarar a
limitação do dado real do que apresentar uma previsão de 12 pontos como
se fosse confiável.
"""

import numpy as np
import pandas as pd
from datetime import datetime

SEED = 42
rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------------------
# 1. SÉRIE REAL (12 meses) — a partir do funil já gerado
# ---------------------------------------------------------------------------

df_funil = pd.read_parquet("data/silver/funil_silver.parquet")
df_funil["mes"] = pd.to_datetime(df_funil["data_cotacao"]).dt.to_period("M")

serie_12m = df_funil.groupby("mes").size().rename("cotacoes").to_frame()
serie_12m["emissoes"] = df_funil.groupby("mes")["cotou_e_emitiu"].sum()
print("--- Série real (12 meses) ---")
print(serie_12m)

# variação mês a mês (sem sazonalidade clara detectável em 12 pontos)
print(f"\nCV (coeficiente de variação) do volume mensal: {serie_12m['cotacoes'].std() / serie_12m['cotacoes'].mean():.2%}")
print("Nota: 12 pontos não permitem separar tendência de ruído com confiança. Ver série estendida abaixo.")

# ---------------------------------------------------------------------------
# 2. SÉRIE ESTENDIDA SINTÉTICA (36 meses) — só para demonstrar metodologia
# ---------------------------------------------------------------------------

meses_ext = pd.period_range("2023-01", periods=36, freq="M")
VOL_BASE = 45_000
TENDENCIA_MENSAL = 250          # leve crescimento estrutural simulado
AMPLITUDE_SAZONAL = 4_500       # pico em set-nov (renovações fiscais/trabalhistas), baixa em jan/fev
RUIDO_STD = 2_000

serie_ext = []
for i, mes in enumerate(meses_ext):
    tendencia = VOL_BASE + TENDENCIA_MENSAL * i
    mes_num = mes.month
    sazonal = AMPLITUDE_SAZONAL * np.sin(2 * np.pi * (mes_num - 3) / 12)  # pico ~set/out
    ruido = rng.normal(0, RUIDO_STD)
    volume = max(int(tendencia + sazonal + ruido), int(VOL_BASE * 0.5))
    serie_ext.append({"mes": mes, "cotacoes": volume})

df_ext = pd.DataFrame(serie_ext).set_index("mes")
print("\n--- Série estendida sintética (36 meses, uso exclusivo para metodologia de forecast) ---")
print(df_ext.head(6), "...")

# ---------------------------------------------------------------------------
# 3. BASELINE 1 — Média móvel (janela 3 meses)
# ---------------------------------------------------------------------------

TREINO = df_ext.iloc[:24]
TESTE = df_ext.iloc[24:]

media_movel = TREINO["cotacoes"].rolling(3).mean().iloc[-1]
pred_mm = pd.Series([media_movel] * len(TESTE), index=TESTE.index)

# ---------------------------------------------------------------------------
# 4. BASELINE 2 — Regressão linear com dummy sazonal (mês do ano)
# ---------------------------------------------------------------------------

from sklearn.linear_model import LinearRegression

TREINO_reg = TREINO.copy()
TREINO_reg["t"] = range(len(TREINO_reg))
TREINO_reg["mes_num"] = [m.month for m in TREINO_reg.index]
TREINO_reg["mes_sin"] = np.sin(2 * np.pi * TREINO_reg["mes_num"] / 12)
TREINO_reg["mes_cos"] = np.cos(2 * np.pi * TREINO_reg["mes_num"] / 12)

X_treino = TREINO_reg[["t", "mes_sin", "mes_cos"]]
y_treino = TREINO_reg["cotacoes"]

modelo = LinearRegression().fit(X_treino, y_treino)

TESTE_reg = TESTE.copy()
TESTE_reg["t"] = range(len(TREINO_reg), len(TREINO_reg) + len(TESTE_reg))
TESTE_reg["mes_num"] = [m.month for m in TESTE_reg.index]
TESTE_reg["mes_sin"] = np.sin(2 * np.pi * TESTE_reg["mes_num"] / 12)
TESTE_reg["mes_cos"] = np.cos(2 * np.pi * TESTE_reg["mes_num"] / 12)

pred_reg = modelo.predict(TESTE_reg[["t", "mes_sin", "mes_cos"]])

# ---------------------------------------------------------------------------
# 5. AVALIAÇÃO — MAPE dos dois baselines
# ---------------------------------------------------------------------------

def mape(y_real, y_pred):
    return np.mean(np.abs((y_real - y_pred) / y_real)) * 100

mape_mm = mape(TESTE["cotacoes"].values, pred_mm.values)
mape_reg = mape(TESTE["cotacoes"].values, pred_reg)

print(f"\n--- Avaliação (12 meses de teste, out-of-sample) ---")
print(f"MAPE — Média Móvel (3m):        {mape_mm:.2f}%")
print(f"MAPE — Regressão + sazonalidade: {mape_reg:.2f}%")
print(f"\nModelo vencedor: {'Regressão + sazonalidade' if mape_reg < mape_mm else 'Média Móvel'}")

comparativo = pd.DataFrame({
    "real": TESTE["cotacoes"].values,
    "pred_media_movel": pred_mm.values,
    "pred_regressao_sazonal": pred_reg,
}, index=TESTE.index)
print("\n", comparativo)

# ---------------------------------------------------------------------------
# 6. SALVAR RESULTADOS
# ---------------------------------------------------------------------------

serie_12m.to_parquet("data/gold/serie_mensal_real_12m.parquet")
df_ext.to_parquet("data/gold/serie_mensal_sintetica_36m.parquet")
comparativo.to_parquet("data/gold/forecast_comparativo.parquet")

print("\nResultados de previsão de demanda salvos em data/gold/")
