"""Inferencia nebulosa Mamdani (TCC 3.7).

Converte o estado da via no nivel PRETENDIDO de iluminacao, fracao do fluxo
pleno no universo 0 a 1. A inferencia nao conhece o piso normativo: o nivel
que ela produz passa obrigatoriamente pela camada de verificacao
(`decisao.verificacao`) antes de virar comando.

Saida em DEGRAUS DE CLASSE (base v4, DIVERGENCIAS 56): o universo de saida e
o degrau - 0 = classe da via, 1 = uma classe abaixo, 2 = classe minima
admitida. O degrau defuzificado vira fracao do pleno pela interpolacao entre
os `niveis` da classe do ponto, que quem chama le de classe_iluminacao (RF09):
nenhum valor normativo mora aqui.

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
from decimal import ROUND_CEILING, Decimal
from pathlib import Path
from typing import Final, Mapping

import numpy as np
import skfuzzy as fuzz

__all__ = ["BaseRegras", "Entrada", "Resultado", "carregar", "em_degraus", "fracao_do_degrau",
           "inferir", "BASE_VIGENTE"]

# Base vigente: v4, por volume de movimento com saida em degraus de classe
# (DIVERGENCIAS 56). A v2 e a v3 continuam no repositorio e em
# versao_base_regras, para o texto das regras de decisoes antigas (RNF04); a
# inferencia so executa bases com saida em degraus de classe.
BASE_VIGENTE: Final[Path] = Path(__file__).parent / "regras" / "v5-zurique.toml"
SAIDA_DEGRAU: Final[str] = "degrau_de_classe"

PASSO: Final[Decimal] = Decimal("0.001")  # mesma resolucao de NUMERIC(4,3)
PLENO: Final[Decimal] = Decimal("1.000")
RESOLUCAO_SAIDA: Final[int] = 1001  # pontos do universo de saida (passo 0,001)

# Categoricas: a entrada e 0 ou 1; o termo "positivo" tem pertinencia = valor.
_CATEGORICAS: Final[dict[str, tuple[str, str]]] = {
    # variavel: (termo quando 1, termo quando 0)
    "ocorrencia": ("sim", "nao"),
    "presenca": ("sim", "nao"),  # so para ler a v3 (historico)
}
_MOVIMENTACAO: Final[tuple[str, ...]] = ("observada", "prevista")
_TERMOS_MOV: Final[tuple[str, ...]] = ("baixa", "media", "alta")


@dataclass(frozen=True)
class Entrada:
    """Estado da via no instante da decisao (Quadro 7).

    `observada`: media de pessoas do ultimo periodo publicado (5 min),
    normalizada pela referencia do trecho - a maior entre os trechos do
    ponto. `prevista`: nivel previsto para a proxima hora, na mesma escala
    (3.6). `prevista` None = modo reativo (H3): a observada ocupa o lugar
    dela, com a mesma base de regras. Sem observada, nenhuma regra de
    movimentacao dispara (falta de informacao nunca produz atenuacao).
    `momento` deve estar no horario local do ponto de luz.
    """

    observada: float | None
    prevista: float | None
    ocorrencia: bool
    momento: datetime


@dataclass(frozen=True)
class Resultado:
    nivel_pretendido: Decimal
    # Degrau de classe defuzificado: 0 = classe da via, 2 = classe minima.
    degrau: float
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
    # "degrau_de_classe" (v4) ou "fracao" (v2/v3: so leitura do historico).
    saida_tipo: str = "fracao"
    universo: tuple[float, float] = (0.0, 1.0)

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
    saida_tipo = dados["saida"].get("tipo", "fracao")
    universo = tuple(dados["saida"].get("universo", [0.0, 1.0]))
    for nome, p in faixa.items():
        _trapezio_ok(f"faixa_horaria.{nome}", p, 0.0, 12.0)
    for nome, p in saida.items():
        _trapezio_ok(f"saida.{nome}", p, *universo)

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
        saida_tipo=saida_tipo,
        universo=universo,
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

    # Modo reativo (H3): sem previsao, a observada ocupa o lugar dela.
    prevista = e.observada if e.prevista is None else e.prevista
    graus: dict[tuple[str, str], float] = {}
    for var, x in (("observada", e.observada), ("prevista", prevista)):
        if x is None:
            # Sem dado de movimentacao: nenhum conjunto ativa, e as regras
            # que dependem dele ficam em zero.
            for termo in base.mov:
                graus[(var, termo)] = 0.0
            continue
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
    pos, neg = _CATEGORICAS["ocorrencia"]
    graus[("ocorrencia", pos)] = 1.0 if e.ocorrencia else 0.0
    graus[("ocorrencia", neg)] = 0.0 if e.ocorrencia else 1.0
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


def fracao_do_degrau(degrau: float, niveis: tuple[Decimal, Decimal, Decimal]) -> Decimal:
    """Degrau 0..2 -> fracao do pleno, linear entre os niveis da classe.

    `niveis` = (classe da via, uma abaixo, minima), como fracao do pleno; em
    classe com menos degraus os valores se repetem (nao dimerizavel = 1, 1,
    1). Arredonda para cima: o lado seguro.
    """
    d = min(max(degrau, 0.0), 2.0)
    i = min(int(d), 1)
    a, b = float(niveis[i]), float(niveis[i + 1])
    valor = a + (b - a) * (d - i)
    return Decimal(str(round(valor, 9))).quantize(PASSO, rounding=ROUND_CEILING)


def inferir(base: BaseRegras, e: Entrada, niveis: tuple[Decimal, Decimal, Decimal]) -> Resultado:
    if base.saida_tipo != SAIDA_DEGRAU:
        raise ValueError(f"{base.rotulo}: so bases com saida em degraus de classe executam")
    if not (PLENO >= niveis[0] >= niveis[1] >= niveis[2] > 0):
        raise ValueError(f"niveis de classe incoerentes: {niveis}")
    graus = _pertinencias(base, e)
    universo = np.linspace(base.universo[0], base.universo[1], RESOLUCAO_SAIDA)
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
        return Resultado(nivel_pretendido=niveis[0], degrau=0.0, ativacoes=ativacoes,
                         sem_regra_ativa=True)

    degrau = round(min(max(float(fuzz.defuzz(universo, agregado, "centroid")), 0.0), 2.0), 4)
    return Resultado(
        nivel_pretendido=fracao_do_degrau(degrau, niveis),
        degrau=degrau,
        ativacoes=ativacoes,
        sem_regra_ativa=False,
    )
