"""Associacao espacial entre trechos de via e pontos de luz.

Liga os dois cadastros que o municipio ja mantem (DIVERGENCIAS 54):

- trecho de via = segmento de logradouro do GeoSampa (camada
  `geoportal:segmento_logradouro`), identificado pelo `cd_identificador` do
  segmento e pelo `codlog` do logradouro. E a unidade em que a plataforma de
  monitoramento publica o estado da via: qual camera cobre qual trecho e
  assunto interno dela;
- ponto de luz = ponto de iluminacao publica do GeoSampa (camada
  `geoportal:iluminacao_publica`), identificado pela placa do poste
  (`cd_placa`), o codigo cadastral que o Cadastro Tecnico da concessao exige.

Um ponto pertence a todo trecho cuja linha passa a ate RAIO_M dele. Um poste
de esquina fica em mais de um trecho, e responde a eventos de todos eles.

Coordenadas em SIRGAS 2000 / UTM 23S (EPSG:31983): distancias em metros, sem
projecao. Modulo puro: nao le banco nem rede.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final, Iterable, Sequence

RAIO_M: Final[float] = 25.0
CRITERIO: Final[str] = f"distancia a linha do trecho <= {RAIO_M:g} m (EPSG:31983)"

Coordenada = tuple[float, float]


@dataclass(frozen=True)
class Trecho:
    id: int  # cd_identificador do segmento no GeoSampa
    codlog: str | None
    tipo: str | None
    nome: str
    numero_inicial: int | None
    numero_final: int | None
    linha: tuple[Coordenada, ...]


@dataclass(frozen=True)
class Poste:
    placa: str  # cd_placa no GeoSampa
    endereco: str | None
    x: float
    y: float


@dataclass(frozen=True)
class Associacao:
    trecho_id: int
    placa: str
    distancia_m: float


def distancia_segmento(p: Coordenada, a: Coordenada, b: Coordenada) -> float:
    """Distancia do ponto p ao segmento de reta ab."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    comprimento2 = dx * dx + dy * dy
    if comprimento2 == 0:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / comprimento2
    t = max(0.0, min(1.0, t))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def distancia_linha(p: Coordenada, linha: Sequence[Coordenada]) -> float:
    """Distancia do ponto p a uma linha poligonal (menor entre os segmentos)."""
    if len(linha) < 2:
        raise ValueError("linha com menos de dois vertices")
    return min(distancia_segmento(p, linha[i], linha[i + 1]) for i in range(len(linha) - 1))


def associar(postes: Iterable[Poste], trechos: Iterable[Trecho], raio_m: float = RAIO_M) -> list[Associacao]:
    """Todos os pares (trecho, poste) a ate raio_m, ordenados por placa e distancia."""
    trechos = list(trechos)
    pares = [
        Associacao(t.id, p.placa, round(d, 2))
        for p in postes
        for t in trechos
        if (d := distancia_linha((p.x, p.y), t.linha)) <= raio_m
    ]
    return sorted(pares, key=lambda a: (a.placa, a.distancia_m))


# ---------------------------------------------------------------------------
# Leitura das camadas do GeoSampa (GeoJSON devolvido pelo WFS)
# ---------------------------------------------------------------------------
def trechos_do_geojson(fc: dict) -> list[Trecho]:
    out = []
    for f in fc["features"]:
        q = f["properties"]
        tipo = (q.get("cd_tipo_logradouro") or "").strip() or None
        nome = (q.get("nm_logradouro") or "").strip() or "SEM DENOMINACAO"
        pares = [q.get("cd_numero_inicial_par"), q.get("cd_numero_inicial_impar")]
        finais = [q.get("cd_numero_final_par"), q.get("cd_numero_final_impar")]
        out.append(Trecho(
            id=int(q["cd_identificador"]),
            codlog=q.get("codlog"),
            tipo=tipo,
            nome=nome,
            numero_inicial=min((n for n in pares if n is not None), default=None),
            numero_final=max((n for n in finais if n is not None), default=None),
            linha=tuple((float(c[0]), float(c[1])) for c in f["geometry"]["coordinates"]),
        ))
    return out


def postes_do_geojson(fc: dict) -> list[Poste]:
    """Postes com placa; placas repetidas no cadastro entram uma vez so."""
    vistos: dict[str, Poste] = {}
    for f in fc["features"]:
        q = f["properties"]
        placa = (q.get("cd_placa") or "").strip()
        if not placa or placa in vistos:
            continue
        x, y = f["geometry"]["coordinates"][:2]
        vistos[placa] = Poste(placa, (q.get("tx_endereco") or "").strip() or None, float(x), float(y))
    return list(vistos.values())
