"""
=============================================================
DATA FOUNDATION — Funções Utilitárias
=============================================================
Autor  : Léo Touguinha | Especialista em Dados | Mercado Financeiro
Repo   : github.com/leotouguinha/data-foundation
=============================================================
"""

import random
import uuid
import os
from datetime import datetime, timedelta


# ─── Reprodutibilidade ────────────────────────────────────────
SEED = 42
random.seed(SEED)


# ─── Geradores de dados sintéticos ───────────────────────────

def gerar_cpf_fake() -> str:
    """
    Gera CPF no formato XXX.XXX.XXX-XX sem validação de dígitos.
    Proposital: simula dados sujos que existem em bases reais.
    """
    nums = [random.randint(0, 9) for _ in range(9)]
    return (
        f"{''.join(map(str, nums[:3]))}."
        f"{''.join(map(str, nums[3:6]))}."
        f"{''.join(map(str, nums[6:9]))}-"
        f"{random.randint(10, 99)}"
    )


def gerar_id_transacao() -> str:
    """Gera ID único de transação no formato TXN + 10 hex chars."""
    return f"TXN{uuid.uuid4().hex[:10].upper()}"


def gerar_id_funil() -> str:
    """Gera ID único de funil no formato FUN + 8 hex chars."""
    return f"FUN{uuid.uuid4().hex[:8].upper()}"


def data_aleatoria(inicio: str = "2023-01-01", fim: str = "2024-12-31") -> str:
    """
    Retorna data aleatória no intervalo [inicio, fim].
    Formato: YYYY-MM-DD
    """
    fmt = "%Y-%m-%d"
    d1 = datetime.strptime(inicio, fmt)
    d2 = datetime.strptime(fim, fmt)
    delta = (d2 - d1).days
    return (d1 + timedelta(days=random.randint(0, delta))).strftime(fmt)


# ─── Helpers de exibição ─────────────────────────────────────

def separador(titulo: str = "", largura: int = 55):
    """Imprime separador formatado para relatórios no notebook."""
    if titulo:
        print(f"\n{'='*largura}")
        print(f"  {titulo}")
        print(f"{'='*largura}")
    else:
        print(f"{'─'*largura}")


def semaforo_dq(score: float) -> str:
    """Retorna emoji + status para Data Quality Score."""
    if score >= 95:
        return "🟢 EXCELENTE"
    if score >= 85:
        return "🟡 ACEITÁVEL"
    if score >= 70:
        return "🟠 ATENÇÃO"
    return "🔴 CRÍTICO"


def formatar_reais(valor: float) -> str:
    """Formata valor monetário em padrão brasileiro."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ─── Constantes de negócio ───────────────────────────────────

NOMES_BRASILEIROS = [
    "Ana Lima", "Bruno Souza", "Carla Mendes", "Diego Ferreira",
    "Elisa Costa", "Felipe Rocha", "Gabriela Nunes", "Henrique Alves",
    "Isabela Martins", "João Pedro Silva", "Karina Oliveira", "Lucas Pereira",
    "Mariana Santos", "Nicolas Gomes", "Olivia Ribeiro", "Paulo Andrade",
    "Queila Barbosa", "Rafael Cardoso", "Sabrina Teixeira", "Thiago Moreira",
    "Ursula Nascimento", "Vinícius Araujo", "Wanessa Freitas", "Xavier Lopes",
    "Yasmin Cavalcanti", "Zeca Figueiredo", "Amanda Ramos", "Bernardo Castro",
    "Camila Dias", "Daniel Monteiro", "Fernanda Queiroz", "Gustavo Pinto",
    "Helena Vasconcelos", "Igor Azevedo", "Juliana Corrêa", "Kleber Melo",
]

CANAIS_FINANCEIROS = [
    "pix", "app_mobile", "internet_banking", "agencia", "totem"
]

# Pesos de canal — reflete adoção digital real em fintechs brasileiras
CANAIS_PESOS = (
    ["pix"]              * 40 +
    ["app_mobile"]       * 30 +
    ["internet_banking"] * 20 +
    ["agencia"]          *  7 +
    ["totem"]            *  3
)

SEGURADORAS = [
    {"nome": "Tokio Marine",  "comissao_min": 0.0060, "comissao_max": 0.0110},
    {"nome": "Porto Seguro",  "comissao_min": 0.0050, "comissao_max": 0.0095},
    {"nome": "Swiss Re",      "comissao_min": 0.0040, "comissao_max": 0.0080},
    {"nome": "Junto Seguros", "comissao_min": 0.0010, "comissao_max": 0.0070},
    {"nome": "SulAmérica",    "comissao_min": 0.0055, "comissao_max": 0.0100},
]

MODALIDADES_GARANTIA = {
    "fiscal"  : {"is_min": 500_000,  "is_max": 50_000_000, "comissao_media": 300},
    "recursal": {"is_min": 1_000,    "is_max": 10_000,     "comissao_media": 300},
    "outras"  : {"is_min": 50_000,   "is_max": 2_000_000,  "comissao_media": 180},
}

MIX_MODALIDADE = {
    "fiscal"  : 0.10,
    "recursal": 0.70,
    "outras"  : 0.20,
}
