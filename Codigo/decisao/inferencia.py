"""Inferencia nebulosa Mamdani (TCC 3.7).

Converte o estado da via no nivel PRETENDIDO de iluminacao, fracao do fluxo
pleno no universo 0 a 1. A inferencia nao conhece o piso normativo: o nivel
que ela produz passa obrigatoriamente pela camada de verificacao
(`decisao.verificacao`) antes de virar comando.

Metodo: E = minimo, implicacao = minimo, agregacao = maximo, defuzificacao
pelo centroide, com as funcoes de pertinencia do scikit-fuzzy. A base de
regras e as particoes vem de um arquivo TOML versionado (RNF05); o grau de
ativacao de cada regra e devolvido para a auditoria (rastreabilidade, 2.6).

Variante em DEGRAUS (DIVERGENCIAS 43, item 51): a mesma base, com as
pertinencias reduzidas a 0 ou 1 (movimentacao cortada nos tercis, faixa
horaria no conjunto de maior grau). O resultado e uma tabela: cada combinacao
de termos tem um unico nivel. Serve so para comparar com a Mamdani ("uma
tabela nao bastaria?"); a decisao em operacao usa a Mamdani.

Este modulo e puro: nao le banco, nao faz rede.
"""

from __future__ import annotations

import hashlib
import tomllib
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Final, Mapping

import numpy as np
import skfuzzy as fuzz

__all__ = ["BaseRegras", "Entrada", "Resultado", "carregar", "em_degraus", "inferir", "BASE_VIGENTE"]

# Base vigente. As versoes anteriores (v0-provisoria, v1-tercis) usavam a
# condicao meteorologica, retirada na v2 (DIVERGENCIAS 49); ficam no historico
# do git e registradas em versao_base_regras.
BASE_VIGENTE: Final[Path] = Path(__file__).parent / "regras" / "v2-sem-meteorologia.toml"

PASSO: Final[Decimal] = Decimal("0.001")  # mesma resolucao de NUMERIC(4,3)
PLENO: Final[Decimal] = Decimal("1.000")
RESOLUCAO_SAIDA: Final[int] = 1001  # pontos do universo de saida (passo 0,001)

# Categoricas: a entrada e 0 ou 1; o termo "positivo" tem pertinencia = valor.
_CATEGORICAS: Final[dict[str, tuple[str, str]]] = {
    # variavel: (termo quando 1, termo quando 0)
    "ocorrencia": ("sim", "nao"),
}
_MOVIMENTACAO: Final[tuple[str, ...]] = ("observada", "prevista")
_TERMOS_MOV: Final[tuple[str, ...]] = ("baixa", "media", "alta")


@dataclass(frozen=True)
class Entrada:
    """Estado da via no instante da decisao (Quadro 7).

    `prevista` None = modo reativo (H3): a inferencia recebe a propria
    observada no lugar da previsao, com a mesma base de regras.
    `momento` deve estar no horario local do ponto de luz.
    """

    observada: float
    prevista: float | None
    ocorrencia: bool
    momento: datetime


@dataclass(frozen=True)
class Resultado:
    nivel_pretendido: Decimal
    # Grau de ativacao de cada regra (0 a 1), na ordem da base.
    ativacoes: dict[str, float]
    # True se nenhuma regra ativou: o nivel devolvido e o pleno (lado seguro).
    sem_regra_ativa: bool


@dataclass(frozen=True)
class Regra:
    id: str
    se: Mapping[str, str]
    entao: str
    origem: str

    def texto(self) -> str:
        cond = " E ".join(f"{v} = {t}" for v, t in self.se.items())
        return f"{self.id}: SE {cond} ENTAO nivel = {self.entao}"


@dataclass(frozen=True)
class BaseRegras:
    rotulo: str
    resumo: str
    hash_regras: str
    mov: dict[str, list[float]]
    faixa: dict[str, list[float]]
    saida: dict[str, list[float]]
    regras: tuple[Regra, ...]
    # "mamdani" (vigente) ou "degraus" (comparacao do item 51).
    metodo: str = "mamdani"

    def texto(self) -> str:
        """Base inteira em linguagem natural (RNF05)."""
        return "\n".join(r.texto() for r in self.regras)


# ---------------------------------------------------------------------------
# Carga e validacao
# ---------------------------------------------------------------------------
def _hash(conteudo: bytes) -> str:
    # Normaliza fim de linha: o hash nao pode mudar entre Windows e o
    # conteiner Linux so por causa do checkout do git.
    return hashlib.sha256(conteudo.replace(b"\r\n", b"\n")).hexdigest()


def _trapezio_ok(nome: str, p: list[float], lo: float, hi: float) -> None:
    if len(p) != 4 or not (lo <= p[0] <= p[1] <= p[2] <= p[3] <= hi):
        raise ValueError(f"trapezio invalido em {nome}: {p}")


def _particoes_movimentacao(fronteiras: list[float], meia: float) -> dict[str, list[float]]:
    f1, f2 = fronteiras
    if not (0 < meia and 0 < f1 - meia and f1 + meia < f2 - meia and f2 + meia < 1):
        raise ValueError(f"fronteiras/rampa invalidas: {fronteiras}, {meia}")
    return {
        "baixa": [0.0, 0.0, f1 - meia, f1 + meia],
        "media": [f1 - meia, f1 + meia, f2 - meia, f2 + meia],
        "alta": [f2 - meia, f2 + meia, 1.0, 1.0],
    }


def carregar(caminho: Path = BASE_VIGENTE) -> BaseRegras:
    conteudo = caminho.read_bytes()
    dados = tomllib.loads(conteudo.decode("utf-8"))

    mov = _particoes_movimentacao(
        dados["movimentacao"]["fronteiras"], dados["movimentacao"]["meia_largura_rampa"]
    )
    faixa = dados["faixa_horaria"]["conjuntos"]
    saida = dados["saida"]["conjuntos"]
    for nome, p in faixa.items():
        _trapezio_ok(f"faixa_horaria.{nome}", p, 0.0, 12.0)
    for nome, p in saida.items():
        _trapezio_ok(f"saida.{nome}", p, 0.0, 1.0)

    termos: dict[str, set[str]] = {v: set(t) for v, t in _CATEGORICAS.items()}
    termos.update({v: set(_TERMOS_MOV) for v in _MOVIMENTACAO})
    termos["faixa_horaria"] = set(faixa)

    regras: list[Regra] = []
    for r in dados["regra"]:
        regra = Regra(id=r["id"], se=dict(r["se"]), entao=r["entao"], origem=r["origem"].strip())
        if not regra.origem:
            raise ValueError(f"{regra.id}: regra sem origem declarada")
        if regra.entao not in saida:
            raise ValueError(f"{regra.id}: consequente desconhecido {regra.entao!r}")
        for var, termo in regra.se.items():
            if termo not in termos.get(var, ()):
                raise ValueError(f"{regra.id}: antecedente desconhecido {var} = {termo!r}")
        regras.append(regra)
    if len({r.id for r in regras}) != len(regras):
        raise ValueError("ids de regra repetidos")

    return BaseRegras(
        rotulo=dados["rotulo"],
        resumo=dados["resumo"],
        hash_regras=_hash(conteudo),
        mov=mov,
        faixa=faixa,
        saida=saida,
        regras=tuple(regras),
    )


def em_degraus(base: BaseRegras) -> BaseRegras:
    """A mesma base como tabela em degraus (mesmos tercis, mesmas regras).

    Rotulo proprio, para que a decisao registre qual variante a produziu
    (RNF04); o hash e o do mesmo arquivo de regras.
    """
    return replace(base, rotulo=f"{base.rotulo}-degraus", metodo="degraus")


# ---------------------------------------------------------------------------
# Inferencia
# ---------------------------------------------------------------------------
def horas_desde_18h(momento: datetime) -> float:
    """Faixa horaria em horas desde as 18h, limitada a 0..12."""
    h = (momento.hour + momento.minute / 60 - 18) % 24
    # 06h-18h (dia): leva ao extremo mais proximo da noite.
    if h > 12:
        return 12.0 if h < 18 else 0.0
    return h


def _grau(p: list[float], x: float) -> float:
    return float(fuzz.trapmf(np.array([x]), p)[0])


def _pertinencias(base: BaseRegras, e: Entrada) -> dict[tuple[str, str], float]:
    for nome, v in (("observada", e.observada), ("prevista", e.prevista)):
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError(f"{nome} fora de [0,1]: {v}")

    prevista = e.observada if e.prevista is None else e.prevista
    graus: dict[tuple[str, str], float] = {}
    for var, x in (("observada", e.observada), ("prevista", prevista)):
        if base.metodo == "degraus":
            # Corte seco no tercil (meio da rampa).
            f1 = (base.mov["baixa"][2] + base.mov["baixa"][3]) / 2
            f2 = (base.mov["alta"][0] + base.mov["alta"][1]) / 2
            termo_x = "baixa" if x < f1 else "media" if x < f2 else "alta"
            for termo in base.mov:
                graus[(var, termo)] = 1.0 if termo == termo_x else 0.0
            continue
        for termo, p in base.mov.items():
            graus[(var, termo)] = _grau(p, x)
    for var, valor in (("ocorrencia", e.ocorrencia),):
        pos, neg = _CATEGORICAS[var]
        graus[(var, pos)] = 1.0 if valor else 0.0
        graus[(var, neg)] = 0.0 if valor else 1.0
    h = horas_desde_18h(e.momento)
    for termo, p in base.faixa.items():
        graus[("faixa_horaria", termo)] = _grau(p, h)
    if base.metodo == "degraus":
        # Um unico conjunto: o de maior grau (empate fica com o primeiro).
        chaves = [("faixa_horaria", t) for t in base.faixa]
        vencedor = max(chaves, key=lambda k: graus[k])
        for k in chaves:
            graus[k] = 1.0 if k == vencedor else 0.0
    return graus


def inferir(base: BaseRegras, e: Entrada) -> Resultado:
    graus = _pertinencias(base, e)
    universo = np.linspace(0.0, 1.0, RESOLUCAO_SAIDA)
    agregado = np.zeros_like(universo)
    ativacoes: dict[str, float] = {}

    for r in base.regras:
        forca = min(graus[(v, t)] for v, t in r.se.items())
        ativacoes[r.id] = forca
        if forca > 0:
            consequente = fuzz.trapmf(universo, base.saida[r.entao])
            agregado = np.fmax(agregado, np.fmin(forca, consequente))

    if not agregado.any():
        # Sem evidencia, o lado seguro e o pleno (mesma logica do RNF07).
        return Resultado(nivel_pretendido=PLENO, ativacoes=ativacoes, sem_regra_ativa=True)

    nivel = fuzz.defuzz(universo, agregado, "centroid")
    nivel = min(max(float(nivel), 0.0), 1.0)
    return Resultado(
        nivel_pretendido=Decimal(str(nivel)).quantize(PASSO, rounding=ROUND_HALF_UP),
        ativacoes=ativacoes,
        sem_regra_ativa=False,
    )
