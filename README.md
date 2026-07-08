# Data Foundation v2

### Pipeline de Dados End-to-End — Funil de Originação B2B (Seguro Garantia)

> **Cenário 100% fictício.** Dados sintéticos, clientes e seguradoras fictícios. Metodologia e raciocínio de negócio são reais — replicáveis em qualquer operação de originação B2B.

---

## O que este projeto demonstra

| Fase | Entrega | Achado-chave |
|---|---|---|
| **1 — Geração de bases** | 220 clientes CNPJ, 32 seguradoras, 12 meses, ~514k cotações simuladas | Erros de qualidade e comportamento de churn injetados deliberadamente, por design |
| **2 — Qualidade + Funil** | PySpark real (não decorativo), 4 dimensões de qualidade | DQ Score 99,84/100. **Fiscal concentra ~R$50,9M em comissão não capturada** — 5x mais que as outras 4 modalidades somadas (~R$10,6M). Canal automático (API) converte 46% melhor que manual |
| **3 — Previsão de demanda** | Regressão sazonal vs baseline, validado out-of-sample | MAPE 2,56% (regressão) vs 10,6% (média móvel) — limitação de histórico real (12 meses) declarada explicitamente |
| **4 — RFM + Churn** | Segmentação de clientes por risco, ponderada por valor | RFM é a entrega defensável; modelo supervisionado teve AUC 1,0 — **documentado como vazamento de dados identificado, não como sucesso** |

---

## Stack

`Python` · `PySpark` · `Pandas` · `scikit-learn` · `Parquet` · Arquitetura Medallion (Bronze → Silver → Gold)

---

## Arquitetura

```
Bronze (bruto, com erros injetados)
  clientes · seguradoras · cotacoes_bronze · propostas · emissoes · funil_completo
        │
        ▼  [Fase 2 — PySpark: 4 dimensões de qualidade, dedup, integridade]
Silver (limpo, com linhagem)
  funil_silver
        │
        ▼  [Fases 2-4 — agregações, forecast, RFM/churn]
Gold (analítico)
  resumo_modalidade · resumo_canal · resumo_seguradora_manual
  serie_mensal_real_12m · serie_mensal_sintetica_36m · forecast_comparativo
  rfm_churn_clientes
```

---

## Documentação por fase

Cada fase tem README próprio com metodologia, limitações declaradas e seção de governança (ownership, classificação, linhagem):

1. [README — Fase 1: Geração de Bases](./README_01_geracao_bases.md)
2. [README — Fase 2: Qualidade de Dados + Funil de Originação](./README_02_qualidade_funil.md)
3. [README — Fase 3: Previsão de Demanda](./README_03_previsao_demanda.md)
4. [README — Fase 4: RFM + Análise de Churn](./README_04_analise_churn.md)

Catálogo consolidado (inventário de tabelas, dicionário de dados completo, linhagem ponta a ponta):

- [CATALOGO_DADOS.md](./CATALOGO_DADOS.md)

---

## Estrutura do repositório

> Cada fase tem dois arquivos de código equivalentes, por decisão deliberada: `.py` para execução em produção/agendamento (ex: Airflow, cron), `.ipynb` para exploração interativa e leitura direto no GitHub (outputs já embutidos — tabelas e prints visíveis sem precisar rodar nada).

```
data-foundation/
├── README.md                          ← este arquivo
├── CATALOGO_DADOS.md
│
├── 01_geracao_bases.py                 ┐
├── 01_geracao_bases.ipynb              ┤ + README_01_geracao_bases.md
├── 02_qualidade_e_funil.py             ┐
├── 02_qualidade_e_funil.ipynb          ┤ + README_02_qualidade_funil.md
├── 03_previsao_demanda.py              ┐
├── 03_previsao_demanda.ipynb           ┤ + README_03_previsao_demanda.md
├── 04_analise_churn.py                 ┐
├── 04_analise_churn.ipynb              ┤ + README_04_analise_churn.md
│
└── data/
    ├── clientes.parquet
    ├── seguradoras.parquet
    ├── cotacoes_bronze.parquet
    ├── propostas.parquet
    ├── emissoes.parquet
    ├── funil_completo.parquet
    ├── silver/
    │   └── funil_silver.parquet
    └── gold/
        ├── resumo_modalidade.parquet
        ├── resumo_canal.parquet
        ├── resumo_seguradora_manual.parquet
        ├── serie_mensal_real_12m.parquet
        ├── serie_mensal_sintetica_36m.parquet
        ├── forecast_comparativo.parquet
        └── rfm_churn_clientes.parquet
```

## Como executar

```bash
pip install pyspark pandas pyarrow scikit-learn --break-system-packages

python 01_geracao_bases.py        # gera bases sintéticas (Bronze)
python 02_qualidade_e_funil.py    # qualidade + funil (Silver/Gold, PySpark)
python 03_previsao_demanda.py     # previsão de demanda (Gold)
python 04_analise_churn.py        # RFM + churn (Gold)
```

> Execute na ordem — cada fase depende do output da anterior.

---

## Princípios que guiaram este projeto

- **Honestidade metodológica acima de números bonitos.** Onde o dado real não sustentava uma conclusão (12 meses para forecast, densidade de cotação incompatível com a definição de churn), isso foi declarado, não escondido — inclusive quando o resultado (AUC 1,0) parecia "bom demais".
- **PySpark onde há motivo real, não como decoração de currículo.** Processamento roda em Spark de verdade; a escrita final via Pandas é decisão documentada de portabilidade Windows, não de volume de dado.
- **Governança correta para o tipo de dado.** Dataset B2B (CNPJ) não é caso de LGPD como pilar central — é sigilo comercial e regulação setorial (SUSEP). Aplicar LGPD genericamente só porque há CNPJ seria um erro de enquadramento.

---

## Autor

**Leonardo Touguinha** | Especialista em Dados | Mercado Financeiro
[LinkedIn](https://linkedin.com/in/lmtdata/) · [GitHub](https://github.com/LeoTouguinha)
