"""
04_analise_churn.py
Data Foundation v2 — Análise de Churn de Clientes (CNPJ)

Definição operacional de churn: cliente sem nenhuma cotação nos últimos
3 meses do período observado (out/nov/dez-25 vazios de atividade).

LIMITAÇÃO DECLARADA: com 12 meses de histórico e definição de "3 meses sem
cotar", a janela real de observação para um cliente "ter chance de dar
churn e ainda sermos capazes de confirmar" é curta — poucos clientes têm
tempo suficiente de histórico para um evento de churn ser observado com
segurança antes do fim do período. Isso significa que:
  1. A abordagem primária aqui é RFM (Recência, Frequência, Valor) — uma
     regra de negócio documentada, não um modelo preditivo supervisionado.
  2. Um modelo supervisionado (regressão logística) é tentado como
     complemento, mas o resultado deve ser lido com ceticismo dado o
     volume pequeno de eventos de churn confirmados em 12 meses.
Isso é intencionalmente honesto: prometer "modelo preditivo de churn"
maduro com 12 meses de dado e 220 clientes seria uma alegação que não
resiste a uma pergunta técnica de entrevista.
"""

import pandas as pd
import numpy as np
from datetime import datetime

df_funil = pd.read_parquet("data/silver/funil_silver.parquet")
df_clientes = pd.read_parquet("data/clientes.parquet")

df_funil["data_cotacao"] = pd.to_datetime(df_funil["data_cotacao"])
DATA_REF = df_funil["data_cotacao"].max()  # 2025-12-31 aprox.

# ---------------------------------------------------------------------------
# 1. RFM por cliente
# ---------------------------------------------------------------------------

rfm = (
    df_funil.groupby("id_cliente")
    .agg(
        ultima_cotacao=("data_cotacao", "max"),
        primeira_cotacao=("data_cotacao", "min"),
        frequencia=("id_cotacao", "count"),
        valor_total_corretagem=("valor_corretagem", "sum"),
    )
    .reset_index()
)

rfm["recencia_dias"] = (DATA_REF - rfm["ultima_cotacao"]).dt.days
rfm["recencia_meses"] = (rfm["recencia_dias"] / 30).round(1)
rfm["tempo_relacionamento_dias"] = (rfm["ultima_cotacao"] - rfm["primeira_cotacao"]).dt.days

# Definição operacional de churn: sem cotação nos últimos 90 dias
rfm["churn"] = (rfm["recencia_dias"] >= 90).astype(int)

print(f"Total de clientes: {len(rfm)}")
print(f"Clientes classificados como churn (>=90 dias sem cotar): {rfm['churn'].sum()} ({rfm['churn'].mean():.1%})")
print(f"\nDistribuição de recência (meses desde última cotação):")
print(rfm["recencia_meses"].describe())

# ---------------------------------------------------------------------------
# 2. SEGMENTAÇÃO RFM (regra de negócio, não modelo)
# ---------------------------------------------------------------------------

rfm["score_recencia"] = pd.qcut(rfm["recencia_dias"].rank(method="first"), 4, labels=[4, 3, 2, 1]).astype(int)
rfm["score_frequencia"] = pd.qcut(rfm["frequencia"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
rfm["score_valor"] = pd.qcut(rfm["valor_total_corretagem"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
rfm["rfm_score"] = rfm["score_recencia"] + rfm["score_frequencia"] + rfm["score_valor"]

def segmentar(row):
    if row["churn"] == 1:
        return "Em risco / Churn"
    if row["rfm_score"] >= 10:
        return "Cliente-chave (alto valor, ativo)"
    if row["rfm_score"] >= 7:
        return "Ativo regular"
    return "Baixo engajamento (monitorar)"

rfm["segmento"] = rfm.apply(segmentar, axis=1)
print("\n--- Segmentação RFM ---")
print(rfm["segmento"].value_counts())

print("\n--- Top 10 clientes de maior risco de churn, ponderado por valor histórico ---")
em_risco = rfm[rfm["churn"] == 1].sort_values("valor_total_corretagem", ascending=False)
print(em_risco[["id_cliente", "recencia_meses", "frequencia", "valor_total_corretagem", "segmento"]].head(10))

# ---------------------------------------------------------------------------
# 3. TENTATIVA DE MODELO SUPERVISIONADO (logística) — com ceticismo declarado
# ---------------------------------------------------------------------------

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report

n_eventos_churn = rfm["churn"].sum()
print(f"\n--- Tentativa de modelo supervisionado ---")
print(f"Eventos de churn disponíveis para treino: {n_eventos_churn} (de {len(rfm)} clientes)")

if n_eventos_churn < 30:
    print("AVISO: menos de 30 eventos positivos. Qualquer modelo supervisionado aqui é ilustrativo, não confiável para produção.")

features = ["frequencia", "valor_total_corretagem", "tempo_relacionamento_dias"]
X = rfm[features].fillna(0)
y = rfm["churn"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y if y.sum() > 5 else None)

modelo_churn = LogisticRegression(class_weight="balanced", max_iter=1000)
modelo_churn.fit(X_train, y_train)

y_pred_proba = modelo_churn.predict_proba(X_test)[:, 1]
try:
    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"AUC (conjunto de teste, N={len(y_test)}): {auc:.3f} — leia com ceticismo dado o volume de eventos.")
    if auc > 0.97:
        print(
            "\nALERTA DE VAZAMENTO DE DADOS: AUC próximo de 1.0 não indica um bom modelo aqui.\n"
            "Churn foi definido por regra determinística (cliente para de cotar), e clientes\n"
            "que 'saíram' têm, por construção, menor frequência total no período — a feature\n"
            "'frequencia' carrega quase toda a informação do rótulo. Isso é vazamento de dados,\n"
            "não sinal preditivo real. Em um cenário real, o modelo precisaria prever ANTES do\n"
            "cliente parar de cotar (ex: usando janela de 6 meses para prever churn nos 3\n"
            "meses seguintes), não usar o período inteiro que já contém o próprio evento."
        )
except ValueError as e:
    print(f"Não foi possível calcular AUC: {e}")

# ---------------------------------------------------------------------------
# 4. SALVAR RESULTADOS
# ---------------------------------------------------------------------------

rfm.to_parquet("data/gold/rfm_churn_clientes.parquet", index=False)
print("\nResultados de RFM/churn salvos em data/gold/rfm_churn_clientes.parquet")
