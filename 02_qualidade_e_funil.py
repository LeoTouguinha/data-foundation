"""
02_qualidade_e_funil.py
Data Foundation v2 — Camada Silver (Qualidade de Dados) + Funil de Originação
Processamento: PySpark (Spark real, não decorativo)
Escrita: Pandas (workaround documentado — ver nota de arquitetura abaixo)

NOTA DE ARQUITETURA — por que a escrita é via Pandas, não .write.parquet():
Em ambiente Windows local (Anaconda/Jupyter), a escrita distribuída nativa do
Spark (.write.csv() / .write.parquet()) depende do winutils.exe/Hadoop, que
historicamente falha nesse SO. O workaround: todo o PROCESSAMENTO (joins,
agregações, regras de qualidade) roda em Spark de verdade — só a ESCRITA final
usa .toPandas().to_parquet() para sair do contexto distribuído e gravar em
disco local sem depender do Hadoop client.
Neste ambiente de execução (Linux, container), essa limitação não existe —
a escrita nativa do Spark funcionaria sem problema. Mantemos o padrão pandas
na escrita mesmo assim porque este notebook é para rodar no ambiente Windows
do autor — é uma decisão de portabilidade, não de necessidade técnica local.
Em produção real (Linux/cloud — AWS EMR, Databricks), a escrita seria
.write.parquet() nativo, distribuído, sem essa camada intermediária.
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
import pandas as pd
import os

spark = (
    SparkSession.builder
    .appName("DataFoundation_QualidadeFunil")
    .config("spark.sql.shuffle.partitions", "8")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("ERROR")

DATA_DIR = "data"

# ---------------------------------------------------------------------------
# 1. LEITURA (Spark lê Parquet nativamente — sem necessidade de pandas aqui)
# ---------------------------------------------------------------------------

df_clientes = spark.read.parquet(f"{DATA_DIR}/clientes.parquet")
df_seguradoras = spark.read.parquet(f"{DATA_DIR}/seguradoras.parquet")
df_funil_raw = spark.read.parquet(f"{DATA_DIR}/funil_completo.parquet")

print(f"Registros lidos — funil: {df_funil_raw.count():,} | clientes: {df_clientes.count()} | seguradoras: {df_seguradoras.count()}")

# ---------------------------------------------------------------------------
# 2. QUALIDADE DE DADOS (Silver) — 4 dimensões, com quantificação de impacto
# ---------------------------------------------------------------------------

total = df_funil_raw.count()

# 2.1 Completude — nulos em campos críticos
campos_criticos = ["id_cliente", "id_seguradora", "modalidade", "premio_seguro", "importancia_segurada"]
completude = {}
for c in campos_criticos:
    nulos = df_funil_raw.filter(F.col(c).isNull()).count()
    completude[c] = round(100 * (1 - nulos / total), 2)

# 2.2 Unicidade — duplicatas por número de cotação
duplicatas = (
    df_funil_raw.groupBy("numero_cotacao").count()
    .filter(F.col("count") > 1).count()
)

# 2.3 Integridade — cotações referenciando cliente/seguradora inexistente (orphan records)
ids_clientes_validos = set(r["id_cliente"] for r in df_clientes.select("id_cliente").collect())
ids_seguradoras_validas = set(r["id_seguradora"] for r in df_seguradoras.select("id_seguradora").collect())

orphan_clientes = df_funil_raw.filter(~F.col("id_cliente").isin(ids_clientes_validos)).count()
orphan_seguradoras = df_funil_raw.filter(~F.col("id_seguradora").isin(ids_seguradoras_validas)).count()

# 2.4 Validade — regras de negócio
premio_negativo = df_funil_raw.filter(F.col("premio_seguro") < 0).count()
is_menor_que_premio = df_funil_raw.filter(F.col("importancia_segurada") < F.col("premio_seguro")).count()
taxa_fora_faixa = df_funil_raw.filter((F.col("taxa_corretagem") < 0) | (F.col("taxa_corretagem") > 0.10)).count()

print("\n--- Relatório de Qualidade (Bronze) ---")
print(f"Completude por campo: {completude}")
print(f"Duplicatas (numero_cotacao repetido): {duplicatas}")
print(f"Orphan records (cliente inexistente): {orphan_clientes}")
print(f"Orphan records (seguradora inexistente): {orphan_seguradoras}")
print(f"Prêmio negativo: {premio_negativo}")
print(f"IS < Prêmio (regra de negócio violada): {is_menor_que_premio}")
print(f"Taxa de corretagem fora da faixa 0-10%: {taxa_fora_faixa}")

# DQ Score ponderado (0-100)
peso_completude, peso_unicidade, peso_integridade, peso_validade = 0.30, 0.20, 0.25, 0.25
score_completude = sum(completude.values()) / len(completude)
score_unicidade = 100 * (1 - duplicatas / total)
score_integridade = 100 * (1 - (orphan_clientes + orphan_seguradoras) / (2 * total))
score_validade = 100 * (1 - (premio_negativo + is_menor_que_premio + taxa_fora_faixa) / (3 * total))

dq_score = (
    score_completude * peso_completude +
    score_unicidade * peso_unicidade +
    score_integridade * peso_integridade +
    score_validade * peso_validade
)
print(f"\nDQ Score ponderado: {dq_score:.2f} / 100")

# 2.5 Camada Silver — remove registros que violam completude, integridade ou validade crítica
df_silver = (
    df_funil_raw
    .filter(F.col("id_cliente").isNotNull())
    .filter(F.col("id_seguradora").isNotNull())
    .filter(F.col("modalidade").isNotNull())
    .filter(F.col("premio_seguro").isNotNull())
    .filter(F.col("importancia_segurada").isNotNull())
    .filter(F.col("id_cliente").isin(ids_clientes_validos))
    .filter(F.col("id_seguradora").isin(ids_seguradoras_validas))
    .filter(F.col("premio_seguro") >= 0)
    .filter(F.col("importancia_segurada") >= F.col("premio_seguro"))
    .filter((F.col("taxa_corretagem") >= 0) & (F.col("taxa_corretagem") <= 0.10))
    .dropDuplicates(["numero_cotacao"])
    .withColumn("_origem", F.lit("funil_completo.parquet (Bronze)"))
    .withColumn("_dt_processamento", F.current_timestamp())
)

registros_removidos = total - df_silver.count()
print(f"Registros removidos na promoção Bronze->Silver: {registros_removidos} ({100*registros_removidos/total:.2f}%)")

# ---------------------------------------------------------------------------
# 3. ANÁLISE DE FUNIL — cotou e não emitiu, receita não capturada por modalidade
# ---------------------------------------------------------------------------

df_nao_emitiu = df_silver.filter(F.col("cotou_e_nao_emitiu") == True)

resumo_modalidade = (
    df_silver.groupBy("modalidade")
    .agg(
        F.count("*").alias("total_cotacoes"),
        F.sum(F.col("cotou_e_emitiu").cast("int")).alias("total_emissoes"),
        F.sum(F.col("cotou_e_nao_emitiu").cast("int")).alias("total_nao_emitiu"),
        F.sum(F.when(F.col("cotou_e_nao_emitiu"), F.col("valor_corretagem")).otherwise(0)).alias("comissao_em_risco"),
        F.avg("valor_corretagem").alias("comissao_media"),
    )
    .withColumn("taxa_conversao", F.round(F.col("total_emissoes") / F.col("total_cotacoes") * 100, 2))
    .orderBy(F.desc("comissao_em_risco"))
)

print("\n--- Comissão em risco por modalidade (cotou e não emitiu) ---")
resumo_modalidade.show(truncate=False)

# Análise por canal (automático vs manual) — o problema de negócio central
resumo_canal = (
    df_silver.groupBy("canal")
    .agg(
        F.count("*").alias("total_cotacoes"),
        F.sum(F.col("cotou_e_emitiu").cast("int")).alias("total_emissoes"),
    )
    .withColumn("taxa_conversao", F.round(F.col("total_emissoes") / F.col("total_cotacoes") * 100, 2))
)
print("\n--- Conversão por canal (API vs Manual) ---")
resumo_canal.show(truncate=False)

# Seguradoras sem API mas com volume relevante de cotação manual — candidatas a incentivo de API
resumo_seguradora = (
    df_silver.filter(F.col("canal") == "Manual")
    .groupBy("id_seguradora")
    .agg(
        F.count("*").alias("cotacoes_manuais"),
        F.sum(F.col("cotou_e_emitiu").cast("int")).alias("emissoes"),
        F.sum(F.col("valor_corretagem")).alias("comissao_gerada"),
    )
    .orderBy(F.desc("cotacoes_manuais"))
)
print("\n--- Top seguradoras por volume de cotação manual (candidatas a incentivo de API) ---")
resumo_seguradora.show(10, truncate=False)

# ---------------------------------------------------------------------------
# 4. ESCRITA — Pandas (workaround Windows, ver nota de arquitetura no topo)
# ---------------------------------------------------------------------------

os.makedirs(f"{DATA_DIR}/silver", exist_ok=True)
os.makedirs(f"{DATA_DIR}/gold", exist_ok=True)

df_silver.toPandas().to_parquet(f"{DATA_DIR}/silver/funil_silver.parquet", index=False, compression="snappy")
resumo_modalidade.toPandas().to_parquet(f"{DATA_DIR}/gold/resumo_modalidade.parquet", index=False)
resumo_canal.toPandas().to_parquet(f"{DATA_DIR}/gold/resumo_canal.parquet", index=False)
resumo_seguradora.toPandas().to_parquet(f"{DATA_DIR}/gold/resumo_seguradora_manual.parquet", index=False)

print("\nCamada Silver e agregados Gold salvos.")

spark.stop()
