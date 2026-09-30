"""Camada de previsao (TCC 3.6).

Estima o nivel de movimentacao da PROXIMA janela horaria. Duas
implementacoes, ambas registradas em versao_modelo_previsao (RNF04):

  Persistencia     - referencia ingenua: o proximo valor e o corrente.
                     Foi a previsao provisoria ate o treino (Etapa 3) e
                     continua como referencia de comparacao em 5.1.
  PrevisorXGBoost  - modelo treinado por modelo/treinar.py sobre a serie de
                     Melbourne normalizada por ponto.

Os dois recebem o mesmo `Historico`. Sem historico suficiente para os
atrasos, o XGBoost NAO inventa: cai para a persistencia e diz que caiu, o
que fica registrado na decisao pelo valor previsto e no log.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Mapping, Protocol

log = logging.getLogger(__name__)

MODELO = Path(__file__).resolve().parent.parent / "modelo" / "modelo_previsao.json"
METRICAS = MODELO.parent / "resultados" / "metricas.json"


@dataclass(frozen=True)
class Historico:
    """Estado temporal do ponto no instante da decisao.

    `serie` leva o atraso em horas (1 = hora anterior) ao nivel medio
    observado naquela hora. `momento` esta no horario LOCAL do ponto.
    """

    momento: datetime
    observada: float
    serie: Mapping[int, float] = field(default_factory=dict)


class Previsor(Protocol):
    rotulo: str  # deve existir em versao_modelo_previsao

    def prever(self, h: Historico) -> float: ...


class Persistencia:
    rotulo = "persistencia"

    def prever(self, h: Historico) -> float:
        return h.observada


class MediaSazonal:
    """Referencia sazonal dentro do sistema (DIVERGENCIAS 59): o nivel da
    PROXIMA hora e o daquela mesma hora nas semanas anteriores (atrasos
    167, 335, ... ate o historico disponivel). E a media sazonal de 3.6
    calculada so com o historico do proprio ponto, sem treino."""

    rotulo = "media-sazonal"
    SEMANAS = 4

    def horas_necessarias(self) -> int:
        return 168 * self.SEMANAS

    def prever(self, h: Historico) -> float:
        v = [h.serie[k] for k in range(167, 168 * self.SEMANAS, 168) if k in h.serie]
        return sum(v) / len(v) if v else h.observada


# ---------------------------------------------------------------------------
# Calendario brasileiro (o modelo tem o atributo "feriado")
# ---------------------------------------------------------------------------
def _pascoa(ano: int) -> date:
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f, g = (b + 8) // 25, (b - (b + 8) // 25 + 1) // 3
    hh = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - hh - k) % 7
    m = (a + 11 * hh + 22 * l) // 451
    mes = (hh + l - 7 * m + 114) // 31
    dia = ((hh + l - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def feriado_nacional(d: date) -> bool:
    """Feriados nacionais brasileiros (nao inclui os municipais)."""
    p = _pascoa(d.year)
    fixos = {(1, 1), (4, 21), (5, 1), (9, 7), (10, 12), (11, 2), (11, 15), (11, 20), (12, 25)}
    moveis = {p - timedelta(days=48), p - timedelta(days=47),  # carnaval
              p - timedelta(days=2), p, p + timedelta(days=60)}  # sexta santa, pascoa, corpus
    return (d.month, d.day) in fixos or d in moveis


# ---------------------------------------------------------------------------
# Modelo treinado
# ---------------------------------------------------------------------------
class PrevisorXGBoost:
    """Reforco de gradiente treinado em 3.6. Carrega o modelo salvo e a
    ordem de atributos gravada junto com as metricas."""

    def __init__(self, caminho: Path = MODELO, metricas: Path = METRICAS) -> None:
        import xgboost as xgb  # importado aqui: so quem usa o modelo paga

        if not caminho.exists():
            raise FileNotFoundError(f"modelo ausente: {caminho} (rode modelo/treinar.py)")
        dados = json.loads(metricas.read_text(encoding="utf-8"))
        self.rotulo: str = dados["rotulo"]
        self.atributos: list[str] = dados["atributos"]
        self.atrasos = [int(a.removeprefix("atraso_").removesuffix("h"))
                        for a in self.atributos if a.startswith("atraso_")]
        self.modelo = xgb.XGBRegressor()
        self.modelo.load_model(caminho)
        self._avisou_falta = False

    def horas_necessarias(self) -> int:
        return max(self.atrasos)

    def prever(self, h: Historico) -> float:
        import numpy as np
        import pandas as pd

        faltando = [k for k in self.atrasos if k not in h.serie]
        precisa_media = {k for k in range(1, 25) if k not in h.serie}
        if faltando or precisa_media:
            # Sem historico completo o modelo extrapolaria sobre buraco.
            if not self._avisou_falta:
                log.warning("historico incompleto (faltam atrasos %s): usando persistencia",
                            faltando or "para as medias")
                self._avisou_falta = True
            return h.observada

        linha = {f"atraso_{k}h": h.serie[k] for k in self.atrasos}
        linha["media_3h"] = sum(h.serie[k] for k in (1, 2, 3)) / 3
        linha["media_24h"] = sum(h.serie[k] for k in range(1, 25)) / 24
        linha["hora"] = h.momento.hour
        linha["hora_sen"] = np.sin(2 * np.pi * h.momento.hour / 24)
        linha["hora_cos"] = np.cos(2 * np.pi * h.momento.hour / 24)
        linha["dia_semana"] = h.momento.weekday()
        linha["fim_de_semana"] = int(h.momento.weekday() >= 5)
        linha["feriado"] = int(feriado_nacional(h.momento.date()))

        x = pd.DataFrame([[linha[c] for c in self.atributos]], columns=self.atributos)
        return float(np.clip(self.modelo.predict(x)[0], 0.0, 1.0))


def carregar_previsor(rotulo: str | None = None) -> Previsor:
    """'persistencia' ou o modelo treinado; sem argumento, o treinado se
    existir."""
    if rotulo == "persistencia":
        return Persistencia()
    if rotulo in ("media-sazonal", "media_sazonal"):
        return MediaSazonal()
    try:
        return PrevisorXGBoost()
    except FileNotFoundError:
        if rotulo:
            raise
        log.info("modelo treinado ausente; usando persistencia")
        return Persistencia()
