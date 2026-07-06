# Fase 1 — Geração de Bases Sintéticas

## Cenário (100% fictício)

Simulação de funil de originação de seguro garantia B2B: 220 clientes CNPJ fictícios cotam com 32 seguradoras fictícias, em 5 modalidades (Fiscal, Trabalhista, Cível, Recursal, Outras), via canal automático (API) ou manual.

**Nenhum nome de cliente ou seguradora é real.** Nomes têm "sabor" setorial (bebidas, farmacêutico, bancário, automotivo etc.) apenas para dar realismo analítico, sem replicar marca de terceiro.

## Parâmetros do cenário

| Parâmetro | Valor |
|---|---|
| Clientes (CNPJ) | 220 |
| Seguradoras no mercado simulado | 32 (23 com relacionamento comercial, 11 com API) |
| Volume médio de cotações/mês | ~45.000 |
| Emissões médias/mês | ~10.000 |
| Canal automático (API) / manual | 70% / 30% |
| Concentração de emissão em 5 seguradoras-âncora | ~65-68% |
| Período simulado | 12 meses (jan-dez/2025) |
| Mix de modalidade | Recursal 45% · Cível 16% · Trabalhista 15% · Outras 14% · Fiscal 10% |

## Erros de qualidade injetados deliberadamente

Para que a Fase 2 (qualidade de dados) tenha algo real para detectar, ~1,5% da base Bronze contém erros propositais: nulos em campos críticos, duplicatas, orphan records (cliente/seguradora inexistente), violação de regra de negócio (IS < prêmio) e taxa de corretagem fora da faixa válida.

## Comportamento de churn injetado deliberadamente

~15% dos clientes (33 de 220) param de cotar a partir de um mês aleatório entre junho e outubro/2025, simulando migração de volume para outra corretora — necessário porque, com ~204 cotações/cliente/mês em média, nenhum cliente ficaria 3 meses sem cotar por acaso.

## Governança

### Enquadramento regulatório — por que este projeto NÃO é primariamente um caso de LGPD

Diferente de um dataset com CPF de pessoa física, este cenário é **B2B (CNPJ)**. Sob a LGPD (Lei 13.709/2018, Art. 5º, I), dado pessoal é informação relacionada a **pessoa natural identificada ou identificável** — CNPJ de empresa, isoladamente, não se enquadra. O enquadramento correto aqui é:

- **Sigilo comercial/contratual** — dados de cotação, prêmio e comissão são informação competitivamente sensível entre corretora e seguradora, não dado pessoal.
- **Regulação setorial (SUSEP)** — regras de conduta e guarda de registros de operação de seguro garantia, independente de LGPD.
- **LGPD se aplicaria** apenas se o dataset incluísse pessoa física identificável associada ao CNPJ (ex: nome do representante legal, contato individual) — o que este schema **não contém por design**.

### Ownership

| Domínio | Data Owner (papel) | Data Steward (papel) |
|---|---|---|
| Cadastro de clientes (CNPJ) | Diretoria Comercial | Especialista em Dados |
| Cotações / Funil | Diretoria Comercial | Especialista em Dados |
| Seguradoras / Parcerias | Diretoria de Produtos/Parcerias | Especialista em Dados |
| Comissão e taxa | Diretoria Financeira | Especialista em Dados |

### Classificação

| Nível | Campos | Justificativa |
|---|---|---|
| Confidencial (sigilo comercial) | `taxa_corretagem`, `valor_corretagem`, `premio_seguro` | Informação competitiva entre corretora/seguradora |
| Interno | `id_cliente`, `cnpj`, `modalidade`, `canal` | Uso interno de análise, sem exposição pública |
| Público / sem restrição | Nomes fictícios de clientes e seguradoras | Dados sintéticos, sem correspondência real |

### Linhagem

Colunas `_origem` e `_dt_processamento` presentes a partir da camada Silver (Fase 2), rastreando origem e timestamp de processamento de cada registro.
