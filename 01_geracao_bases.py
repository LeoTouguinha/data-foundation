"""
01_geracao_bases.py
Data Foundation v2 — Funil de Originação de Seguro Garantia (cenário 100% fictício)

Gera as bases brutas (Bronze) que simulam o ambiente de dados de uma corretora
de seguro garantia, incluindo cotações via API (automáticas) e manuais, com
concentração de emissão em seguradoras-âncora e mix de modalidades definido.

TODOS os dados — clientes, seguradoras, valores — são fictícios.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ---------------------------------------------------------------------------
# 1. CLIENTES FICTÍCIOS (220 CNPJs) — nomes com "sabor" setorial, sem marca real
# ---------------------------------------------------------------------------

SETORES = {
    "Bebidas": ["Sabor Cerrado", "Fonte Azul", "Bebidas Horizonte", "Refrescos Nortemar", "Cervejaria Vale Dourado"],
    "Varejo Farmacêutico": ["FarmaVida", "Rede Bem-Estar", "Drogaria Popular Sul", "Saúde Prime", "FarmaCenter"],
    "Bancos/Fintech": ["Banco Confiança", "Crédito Horizonte", "Fintech Avanza", "Banco Solar", "Meridiano Financeira"],
    "Adquirente/Meios de Pagamento": ["PagaFácil", "Adquire Brasil", "TransactPay", "MeioCerto Pagamentos"],
    "Automotivo/Montadora": ["MotorVale", "Rodante Veículos", "TransAuto do Brasil", "Metalcar Indústria"],
    "Construção/Infraestrutura": ["ConstruMax", "Infra Nacional", "Edifica Brasil", "TerraForte Engenharia"],
    "Indústria Geral": ["Indústrias Cerrado", "MetalForte", "GrupoNova Manufatura", "Industrial Vale Sul"],
    "Varejo Geral": ["MegaVarejo", "Comercial Estrela", "Rede Distribui", "Lojas Horizonte"],
}

SUFIXOS = ["S.A.", "Ltda.", "Participações S.A.", "Indústria e Comércio Ltda.", "Holding S.A."]

def gerar_cnpj():
    n = [random.randint(0, 9) for _ in range(12)]
    def dv(nums, pesos):
        s = sum(n * p for n, p in zip(nums, pesos))
        r = s % 11
        return 0 if r < 2 else 11 - r
    p1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    d1 = dv(n, p1)
    p2 = [6,5,4,3,2,9,8,7,6,5,4,3,2]
    d2 = dv(n + [d1], p2)
    n_full = n + [d1, d2]
    s = "".join(str(x) for x in n_full)
    return f"{s[0:2]}.{s[2:5]}.{s[5:8]}/{s[8:12]}-{s[12:14]}"

clientes = []
setores_list = list(SETORES.keys())
pesos_setor = [0.14, 0.13, 0.16, 0.10, 0.12, 0.12, 0.13, 0.10]  # distribuição plausível entre setores

for i in range(1, 221):
    setor = np.random.choice(setores_list, p=pesos_setor)
    base_nome = random.choice(SETORES[setor])
    sufixo = random.choice(SUFIXOS)
    nome_cliente = f"{base_nome} {sufixo}"
    data_cadastro = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1800))
    clientes.append({
        "id_cliente": i,
        "cnpj": gerar_cnpj(),
        "nome_cliente": nome_cliente,
        "setor": setor,
        "data_cadastro_cliente": data_cadastro.strftime("%Y-%m-%d"),
    })

df_clientes = pd.DataFrame(clientes)

# ---------------------------------------------------------------------------
# 2. SEGURADORAS FICTÍCIAS (32 no mercado, 23 com relacionamento, 11 com API)
# ---------------------------------------------------------------------------

nomes_seguradoras_base = [
    "Seguradora Atlântico", "Confiança Seguros", "Prisma Garantias", "Seguradora Horizonte",
    "Vitalis Seguros", "Garantia Nacional", "Seguradora Meridiano", "Portoseg Garantias",
    "Aliança Sul Seguros", "Seguradora Cerrado", "TotalGarante Seguros", "Seguradora Bravo",
    "Fortaleza Garantias", "Seguradora Zenith", "Global Garante Seguros", "Seguradora Ipê",
    "Âncora Seguros", "Base Sólida Garantias", "Seguradora Vetor", "Confia Mais Seguros",
    "Seguradora Delta Sul", "Garante Brasil Seguros", "Seguradora Tucano", "Pontual Garantias",
    "Seguradora Vega", "Segura Norte Garantias", "Seguradora Íris", "Máxima Garantias",
    "Seguradora Continental", "Boreal Seguros", "Seguradora Alfa Garante", "Rota Segura Seguros",
]
assert len(nomes_seguradoras_base) == 32

seguradoras = []
for i, nome in enumerate(nomes_seguradoras_base, start=1):
    seguradoras.append({"id_seguradora": i, "nome_seguradora": nome})
df_seguradoras = pd.DataFrame(seguradoras)

# 23 com relacionamento comercial ativo (as primeiras 23 da lista, ordem arbitrária)
ids_com_relacionamento = list(range(1, 24))
# 11 dessas 23 têm API de cotação automática
ids_com_api = ids_com_relacionamento[:11]
# 5 seguradoras-âncora concentram 65% das emissões (as 5 primeiras com API, decrescente)
seguradoras_ancora = ids_com_api[:5]
pesos_ancora = [0.22, 0.16, 0.12, 0.09, 0.06]  # soma 0.65
seguradoras_nao_ancora_com_relacionamento = [i for i in ids_com_relacionamento if i not in seguradoras_ancora]
peso_restante = 0.35 / len(seguradoras_nao_ancora_com_relacionamento)

df_seguradoras["tem_relacionamento"] = df_seguradoras["id_seguradora"].isin(ids_com_relacionamento)
df_seguradoras["tem_api_cotacao"] = df_seguradoras["id_seguradora"].isin(ids_com_api)

# ---------------------------------------------------------------------------
# 3. MODALIDADES — mix, faixas de prêmio (IS) e taxa de corretagem
# ---------------------------------------------------------------------------

MODALIDADES = {
    "Fiscal":      {"peso": 0.10, "is_min": 500_000,  "is_max": 5_000_000, "taxa_min": 0.010, "taxa_max": 0.015},
    "Trabalhista": {"peso": 0.15, "is_min": 10_000,    "is_max": 60_000,    "taxa_min": 0.010, "taxa_max": 0.030},
    "Cível":       {"peso": 0.16, "is_min": 30_000,    "is_max": 80_000,    "taxa_min": 0.010, "taxa_max": 0.030},
    "Recursal":    {"peso": 0.45, "is_min": 1_500,     "is_max": 7_500,     "taxa_min": 0.030, "taxa_max": 0.050},
    "Outras":      {"peso": 0.14, "is_min": 50_000,    "is_max": 200_000,   "taxa_min": 0.010, "taxa_max": 0.030},
}
assert abs(sum(m["peso"] for m in MODALIDADES.values()) - 1.0) < 1e-9

# ---------------------------------------------------------------------------
# 4. COTAÇÕES — 12 meses (jan-dez/25), ~45k/mês, variação mensal, 70% API / 30% manual
# ---------------------------------------------------------------------------

MESES = pd.date_range("2025-01-01", "2025-12-01", freq="MS")
VOL_MEDIO_MES = 45_000
VARIACAO_MENSAL = 0.12  # +-12% de variação em torno da média

modalidades_nomes = list(MODALIDADES.keys())
modalidades_pesos = [MODALIDADES[m]["peso"] for m in modalidades_nomes]

cotacoes = []
cotacao_seq = 1

for mes in MESES:
    vol_mes = int(np.random.normal(VOL_MEDIO_MES, VOL_MEDIO_MES * VARIACAO_MENSAL / 2))
    vol_mes = max(vol_mes, int(VOL_MEDIO_MES * 0.7))
    dias_no_mes = pd.Period(mes, freq="M").days_in_month

    for _ in range(vol_mes):
        id_cliente = random.randint(1, 220)
        modalidade = np.random.choice(modalidades_nomes, p=modalidades_pesos)
        params = MODALIDADES[modalidade]

        # canal: 70% automático (API) / 30% manual
        canal = np.random.choice(["Automatico", "Manual"], p=[0.70, 0.30])

        if canal == "Automatico":
            # cotação automática só pode ir para seguradora com API
            id_seguradora = int(np.random.choice(ids_com_api))
        else:
            id_seguradora = int(np.random.choice(ids_com_relacionamento))

        dia = random.randint(1, dias_no_mes)
        data_cotacao = mes + timedelta(days=dia - 1)

        importancia_segurada = round(np.random.uniform(params["is_min"], params["is_max"]), 2)
        taxa_corretagem = round(np.random.uniform(params["taxa_min"], params["taxa_max"]), 4)

        # premio proporcional à IS com um fator de mercado (~2-6% da IS, varia por modalidade)
        fator_premio = np.random.uniform(0.02, 0.06)
        premio_seguro = round(importancia_segurada * fator_premio, 2)
        valor_corretagem = round(premio_seguro * taxa_corretagem, 2)

        # erro no retorno da cotação (mais comum em manual e em seguradoras sem API)
        prob_erro = 0.03 if canal == "Automatico" else 0.09
        erro_retorno = np.random.random() < prob_erro
        sucesso_cotacao = not erro_retorno

        # bids: quantas seguradoras foram consultadas nessa cotação (1 a 5)
        bids_realizados = random.randint(1, 5)

        cotacoes.append({
            "id_cotacao": cotacao_seq,
            "numero_cotacao": f"COT-{data_cotacao.strftime('%Y%m')}-{cotacao_seq:06d}",
            "id_cliente": id_cliente,
            "id_seguradora": id_seguradora,
            "modalidade": modalidade,
            "data_cotacao": data_cotacao.strftime("%Y-%m-%d"),
            "canal": canal,
            "bids_realizados": bids_realizados,
            "importancia_segurada": importancia_segurada,
            "premio_seguro": premio_seguro,
            "taxa_corretagem": taxa_corretagem,
            "valor_corretagem": valor_corretagem,
            "sucesso_cotacao": sucesso_cotacao,
            "erro_retorno_cotacao": erro_retorno,
        })
        cotacao_seq += 1

df_cotacoes = pd.DataFrame(cotacoes)

# ---------------------------------------------------------------------------
# 4b. INJEÇÃO DELIBERADA DE COMPORTAMENTO DE CHURN
#     Com ~204 cotações/cliente/mês em média, nenhum cliente ficaria 3 meses
#     sem cotar por acaso. Sem isso, a análise de churn (fase 4) não tem
#     nenhum evento positivo para detectar. Selecionamos ~15% dos clientes
#     para "sumir" do funil a partir de um mês aleatório entre jun e out/25,
#     simulando migração de volume para outra corretora (churn real).
# ---------------------------------------------------------------------------

n_clientes_churn = int(220 * 0.15)  # ~33 clientes
clientes_churn = rng_churn = np.random.default_rng(SEED + 1)
ids_clientes_churn = clientes_churn.choice(range(1, 221), size=n_clientes_churn, replace=False)
mes_churn_por_cliente = {
    cid: clientes_churn.integers(6, 11)  # para de cotar a partir do mês 6 a 10 (jun-out)
    for cid in ids_clientes_churn
}

def cliente_ainda_ativo(row):
    cid = row["id_cliente"]
    if cid not in mes_churn_por_cliente:
        return True
    mes_cotacao = int(row["data_cotacao"][5:7])
    return mes_cotacao < mes_churn_por_cliente[cid]

mask_ativo = df_cotacoes.apply(cliente_ainda_ativo, axis=1)
n_removidas = (~mask_ativo).sum()
df_cotacoes = df_cotacoes[mask_ativo].reset_index(drop=True)
print(f"\nChurn injetado: {n_clientes_churn} clientes ({n_clientes_churn/220:.0%}) pararam de cotar entre jun-out/25.")
print(f"Cotações removidas por churn simulado: {n_removidas:,}")
print(f"Total de cotações geradas: {len(df_cotacoes):,}")
print(df_cotacoes.groupby(df_cotacoes["data_cotacao"].str[:7]).size())

# ---------------------------------------------------------------------------
# 5. FUNIL: definir quais cotações viram PROPOSTA e quais viram EMISSÃO
#    Meta: média de 10k emissões/mês sobre ~45k cotações/mês (~22% conversão)
#    65% das emissões concentradas nas 5 seguradoras-âncora
# ---------------------------------------------------------------------------

df_validas = df_cotacoes[df_cotacoes["sucesso_cotacao"]].copy()

# probabilidade base de virar proposta, depois emissão — calibrada para bater a meta mensal
PROB_PROPOSTA_BASE = 0.475
PROB_EMISSAO_DADO_PROPOSTA_BASE = 0.42  # calibrado para ~22% de conversão cotação->emissão

propostas = []
emissoes = []

for mes in MESES:
    mes_str = mes.strftime("%Y-%m")
    cotacoes_mes = df_validas[df_validas["data_cotacao"].str.startswith(mes_str)]

    # sorteia propostas
    mask_proposta = np.random.random(len(cotacoes_mes)) < PROB_PROPOSTA_BASE
    props_mes = cotacoes_mes[mask_proposta].copy()

    # entre as propostas, sorteia emissão — seguradoras-âncora têm boost de conversão
    prob_emissao = np.where(
        props_mes["id_seguradora"].isin(seguradoras_ancora),
        PROB_EMISSAO_DADO_PROPOSTA_BASE * 2.05,
        PROB_EMISSAO_DADO_PROPOSTA_BASE * 0.62,
    )
    prob_emissao = np.clip(prob_emissao, 0, 0.97)
    mask_emissao = np.random.random(len(props_mes)) < prob_emissao
    emiss_mes = props_mes[mask_emissao].copy()

    propostas.append(props_mes)
    emissoes.append(emiss_mes)

df_propostas = pd.concat(propostas, ignore_index=True)
df_emissoes = pd.concat(emissoes, ignore_index=True)

print(f"\nPropostas: {len(df_propostas):,} | Emissões: {len(df_emissoes):,}")
print(f"Conversão cotação->emissão: {len(df_emissoes) / len(df_cotacoes):.1%}")
print(f"Média de emissões/mês: {len(df_emissoes) / 12:,.0f}")
conc = df_emissoes["id_seguradora"].isin(seguradoras_ancora).mean()
print(f"Concentração de emissão nas 5 seguradoras-âncora: {conc:.1%}")

# adiciona datas de proposta/emissão/vigência
def add_datas_funil(df_prop, df_emis):
    df_prop = df_prop.copy()
    df_prop["data_proposta"] = pd.to_datetime(df_prop["data_cotacao"]) + pd.to_timedelta(
        np.random.randint(1, 10, len(df_prop)), unit="D")

    df_emis = df_emis.copy()
    dp = pd.to_datetime(df_prop.set_index("id_cotacao")["data_proposta"])
    df_emis["data_proposta"] = df_emis["id_cotacao"].map(dp)
    df_emis["data_emissao"] = df_emis["data_proposta"] + pd.to_timedelta(
        np.random.randint(2, 20, len(df_emis)), unit="D")
    df_emis["data_inicio_vigencia"] = df_emis["data_emissao"] + pd.to_timedelta(1, unit="D")
    df_emis["data_final_vigencia"] = df_emis["data_inicio_vigencia"] + pd.to_timedelta(365, unit="D")
    df_emis["emissao_automatica_ou_manual"] = df_emis["canal"]
    return df_prop, df_emis

df_propostas, df_emissoes = add_datas_funil(df_propostas, df_emissoes)

# ---------------------------------------------------------------------------
# 6. TABELA FATO CONSOLIDADA — status do funil por cotação
# ---------------------------------------------------------------------------

df_funil = df_cotacoes.copy()
df_funil["sucesso_emissao"] = df_funil["id_cotacao"].isin(df_emissoes["id_cotacao"])
df_funil["gerou_proposta"] = df_funil["id_cotacao"].isin(df_propostas["id_cotacao"])
df_funil["cotou_e_emitiu"] = df_funil["sucesso_cotacao"] & df_funil["sucesso_emissao"]
df_funil["cotou_e_nao_emitiu"] = df_funil["sucesso_cotacao"] & ~df_funil["sucesso_emissao"]

# ---------------------------------------------------------------------------
# 6b. INJEÇÃO DELIBERADA DE ERROS DE QUALIDADE (Bronze "suja", ~1.5% da base)
#     Objetivo: dar ao notebook de qualidade (Silver) algo real para detectar
#     e corrigir — sem isso, DQ Score sai 100/100 e o notebook fica decorativo.
# ---------------------------------------------------------------------------

n_total = len(df_funil)
rng = np.random.default_rng(SEED)

# (a) Nulos em campos críticos — ~0.4% dos registros, campo sorteado
idx_nulos = rng.choice(n_total, size=int(n_total * 0.004), replace=False)
campos_nulaveis = ["id_seguradora", "modalidade", "premio_seguro", "importancia_segurada"]
for idx in idx_nulos:
    campo = rng.choice(campos_nulaveis)
    df_funil.loc[df_funil.index[idx], campo] = None

# (b) Duplicatas — ~0.3% dos registros duplicados (numero_cotacao repetido)
idx_duplicar = rng.choice(n_total, size=int(n_total * 0.003), replace=False)
linhas_duplicadas = df_funil.iloc[idx_duplicar].copy()
df_funil = pd.concat([df_funil, linhas_duplicadas], ignore_index=True)

# (c) Orphan records — id_cliente ou id_seguradora inexistente (~0.3%)
n_total_pos = len(df_funil)
idx_orphan_cliente = rng.choice(n_total_pos, size=int(n_total_pos * 0.0015), replace=False)
df_funil.loc[df_funil.index[idx_orphan_cliente], "id_cliente"] = rng.integers(900, 999, size=len(idx_orphan_cliente))

idx_orphan_seg = rng.choice(n_total_pos, size=int(n_total_pos * 0.0015), replace=False)
df_funil.loc[df_funil.index[idx_orphan_seg], "id_seguradora"] = rng.integers(900, 999, size=len(idx_orphan_seg))

# (d) Violação de regra de negócio — importancia_segurada < premio_seguro (~0.3%)
idx_violacao = rng.choice(n_total_pos, size=int(n_total_pos * 0.003), replace=False)
df_funil.loc[df_funil.index[idx_violacao], "importancia_segurada"] = (
    df_funil.loc[df_funil.index[idx_violacao], "premio_seguro"] * 0.5
)

# (e) Taxa de corretagem fora da faixa válida 0-10% — erro de digitação simulado (~0.2%)
idx_taxa = rng.choice(n_total_pos, size=int(n_total_pos * 0.002), replace=False)
df_funil.loc[df_funil.index[idx_taxa], "taxa_corretagem"] = rng.uniform(0.15, 0.40, size=len(idx_taxa))

print(f"\nErros de qualidade injetados na Bronze:")
print(f"  Nulos em campos críticos: {len(idx_nulos)}")
print(f"  Duplicatas (numero_cotacao repetido): {len(idx_duplicar)}")
print(f"  Orphan records (cliente): {len(idx_orphan_cliente)}")
print(f"  Orphan records (seguradora): {len(idx_orphan_seg)}")
print(f"  Violação IS < Prêmio: {len(idx_violacao)}")
print(f"  Taxa de corretagem fora da faixa: {len(idx_taxa)}")
print(f"  Total de registros Bronze após injeção: {len(df_funil):,}")

# ---------------------------------------------------------------------------
# 7. SALVAR BASES (Bronze)
# ---------------------------------------------------------------------------

df_clientes.to_parquet("data/clientes.parquet", index=False, compression="snappy")
df_seguradoras.to_parquet("data/seguradoras.parquet", index=False, compression="snappy")
df_cotacoes.to_parquet("data/cotacoes_bronze.parquet", index=False, compression="snappy")
df_propostas.to_parquet("data/propostas.parquet", index=False, compression="snappy")
df_emissoes.to_parquet("data/emissoes.parquet", index=False, compression="snappy")
df_funil.to_parquet("data/funil_completo.parquet", index=False, compression="snappy")

print("\nBases salvas em data/ (formato Parquet, compressão snappy)")
print(f"  clientes.parquet          {len(df_clientes):>7,} registros")
print(f"  seguradoras.parquet       {len(df_seguradoras):>7,} registros")
print(f"  cotacoes_bronze.parquet   {len(df_cotacoes):>7,} registros")
print(f"  propostas.parquet         {len(df_propostas):>7,} registros")
print(f"  emissoes.parquet          {len(df_emissoes):>7,} registros")
print(f"  funil_completo.parquet    {len(df_funil):>7,} registros")
