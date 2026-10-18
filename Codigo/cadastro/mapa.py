"""Visao de bairro para a demonstracao (DIVERGENCIAS 76).

Cadastra como NOS SIMULADOS todos os postes do recorte do Jardim Helena que
ainda nao tem no, com o mesmo criterio de associacao de 25 m, e preenche as
coordenadas em WGS84 (pontos e trechos) para o mapa do painel. Gera tambem as
linhas da ACL do broker para a frota simulada (um usuario, FROTA-SIM, que so
enxerga os topicos desses postes).

    python -m cadastro.mapa        # -> db/seed_mapa.sql e bloco da frota em deploy/broker/acl

O seed NAO entra na carga inicial do banco local (docker-compose.yml): os
testes e a suite de cenarios continuam com os dois pontos de sempre. Aplicar
so onde se quer a visao de bairro, e depois recalcular os grupos:
    psql ... < db/seed_mapa.sql && python -m decisao.grupos
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from .associar import CRITERIO, associar, postes_do_geojson, trechos_do_geojson
from .recorte import PONTOS, RECORTE

RAIZ = Path(__file__).resolve().parent.parent
SEED = RAIZ / "db" / "seed_mapa.sql"
ACL = RAIZ / "deploy" / "broker" / "acl"
USUARIO_FROTA = "FROTA-SIM"
PREFIXO = "JH-"
MARCA_INI = "# --- frota simulada (gerado por python -m cadastro.mapa; nao editar) ---"
MARCA_FIM = "# --- fim da frota simulada ---"


def utm23s_para_wgs84(e: float, n: float) -> tuple[float, float]:
    """SIRGAS 2000 / UTM 23S (EPSG:31983) -> latitude, longitude em graus.

    Inversa de Transverse Mercator (Snyder, 1987) no elipsoide GRS80; SIRGAS
    2000 e WGS84 coincidem no nivel de centimetros, o que basta para o mapa."""
    a, f = 6378137.0, 1 / 298.257222101
    k0, e0, n0, lon0 = 0.9996, 500000.0, 10000000.0, math.radians(-45.0)
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    m = (n - n0) / k0
    mu = m / (a * (1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    fi1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu)
           + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
           + (151 * e1 ** 3 / 96) * math.sin(6 * mu)
           + (1097 * e1 ** 4 / 512) * math.sin(8 * mu))
    c1 = ep2 * math.cos(fi1) ** 2
    t1 = math.tan(fi1) ** 2
    n1 = a / math.sqrt(1 - e2 * math.sin(fi1) ** 2)
    r1 = a * (1 - e2) / (1 - e2 * math.sin(fi1) ** 2) ** 1.5
    d = (e - e0) / (n1 * k0)
    lat = fi1 - (n1 * math.tan(fi1) / r1) * (
        d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 ** 2 - 9 * ep2) * d ** 4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1 ** 2 - 252 * ep2 - 3 * c1 ** 2) * d ** 6 / 720)
    lon = lon0 + (d - (1 + 2 * t1 + c1) * d ** 3 / 6
                  + (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2) * d ** 5 / 120
                  ) / math.cos(fi1)
    return math.degrees(lat), math.degrees(lon)


def _txt(v) -> str:
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


def codigos_simulados() -> dict[str, object]:
    """codigo do no simulado -> poste do recorte (placas unicas, sem os que ja tem no)."""
    rec = json.loads(RECORTE.read_text(encoding="utf-8"))
    com_no = set(PONTOS.values())
    postes = {}
    for p in postes_do_geojson(rec["postes"]["geojson"]):
        if p.placa and p.placa not in com_no:
            postes.setdefault(PREFIXO + p.placa, p)  # placa duplicada: fica a primeira
    return postes


def gerar_sql() -> str:
    rec = json.loads(RECORTE.read_text(encoding="utf-8"))
    trechos = trechos_do_geojson(rec["trechos"]["geojson"])
    todos = {p.placa: p for p in postes_do_geojson(rec["postes"]["geojson"])}
    simulados = codigos_simulados()
    linhas = [
        "-- Visao de bairro (DIVERGENCIAS 76). GERADO por `python -m cadastro.mapa`; nao editar a mao.",
        "-- Nos SIMULADOS (lux sintetico, simulado = true): so para a demonstracao, nunca resultado.",
        "-- Depois de aplicar: python -m decisao.grupos",
        "BEGIN;",
        "",
        "-- Coordenadas WGS84 dos trechos, so para o mapa do painel.",
    ]
    for t in sorted(trechos, key=lambda t: t.id):
        coords = [[round(lon, 7), round(lat, 7)] for lat, lon in (utm23s_para_wgs84(x, y) for x, y in t.linha)]
        geo = json.dumps({"type": "LineString", "coordinates": coords})
        linhas.append(f"UPDATE trecho_via SET geometria_wgs84 = {_txt(geo)}::jsonb WHERE id = {t.id};")
    linhas.append("")
    linhas.append("-- Pontos que ja tem no (BANCADA-01, SIMULADO-02): so as coordenadas.")
    for codigo, placa in PONTOS.items():
        lat, lon = utm23s_para_wgs84(todos[placa].x, todos[placa].y)
        linhas.append(f"UPDATE ponto_de_luz SET latitude = {lat:.6f}, longitude = {lon:.6f}"
                      f" WHERE codigo = {_txt(codigo)};")
    linhas.append("")
    linhas.append(f"-- {len(simulados)} postes reais do recorte como nos simulados.")
    for codigo, p in sorted(simulados.items()):
        lat, lon = utm23s_para_wgs84(p.x, p.y)
        linhas.append(
            "INSERT INTO ponto_de_luz (codigo, logradouro, classe_codigo, placa, utm_e, utm_n,"
            " latitude, longitude, simulado)\n"
            f"VALUES ({_txt(codigo)}, {_txt(p.endereco)}, 'P3', {_txt(p.placa)}, {p.x:.2f}, {p.y:.2f},"
            f" {lat:.6f}, {lon:.6f}, true)\n"
            "ON CONFLICT (codigo) DO UPDATE SET latitude = EXCLUDED.latitude,"
            " longitude = EXCLUDED.longitude, simulado = true;"
        )
    linhas.append("")
    linhas.append(f"-- Associacao trecho x ponto dos simulados: {CRITERIO}.")
    for a in associar(list(simulados.values()), trechos):
        codigo = PREFIXO + a.placa
        linhas.append(
            "INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)\n"
            f"SELECT {a.trecho_id}, id, {a.distancia_m}, {_txt(CRITERIO)} FROM ponto_de_luz"
            f" WHERE codigo = {_txt(codigo)}\nON CONFLICT DO NOTHING;"
        )
    linhas.append("\nCOMMIT;")
    return "\n".join(linhas) + "\n"


def bloco_acl() -> str:
    """So os topicos dos postes simulados: a frota nao alcanca BANCADA-01 nem SIMULADO-02."""
    linhas = [MARCA_INI, f"user {USUARIO_FROTA}"]
    for codigo in sorted(codigos_simulados()):
        linhas += [f"topic read iluminacao/{codigo}/comando",
                   f"topic write iluminacao/{codigo}/telemetria",
                   f"topic write iluminacao/{codigo}/estado"]
    linhas.append(MARCA_FIM)
    return "\n".join(linhas) + "\n"


def atualizar_acl() -> None:
    atual = ACL.read_text(encoding="utf-8")
    if MARCA_INI in atual:
        atual = atual[: atual.index(MARCA_INI)].rstrip("\n") + "\n"
    ACL.write_text(atual + "\n" + bloco_acl(), encoding="utf-8")


def main() -> None:
    SEED.write_text(gerar_sql(), encoding="utf-8")
    atualizar_acl()
    print(f"{SEED.name}: {len(codigos_simulados())} nos simulados; ACL da {USUARIO_FROTA} atualizada")


if __name__ == "__main__":
    main()
