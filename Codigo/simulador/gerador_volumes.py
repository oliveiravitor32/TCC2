"""Gerador de volumes da visao de bairro (DIVERGENCIAS 76).

Publica, a cada 5 min, UM pacote no POST /eventos com o volume de cada trecho
do recorte, como a plataforma faria (Quadro 18). Os numeros sao INVENTADOS,
so para a demonstracao: uma "noite" que comeca movimentada e esvazia aos
poucos, comprimida em --ciclo-min minutos e repetida, com alguns trechos
sempre mais cheios e uma pequena variacao com semente fixa. origem =
"gerador-demo", para ficar claro na auditoria. Nunca e fonte de resultado.

Cada trecho tem uma ESCALA propria (pessoas no horario de pico): ruas quase
vazias e ruas movimentadas. Assim a regua aprendida (3.6) difere de trecho
para trecho, e o mesmo comportamento relativo da noite produz contagens
absolutas diferentes. --historico DIAS grava de uma vez um passado inventado
(um dia tipico por dia, com a mesma escala), direto no banco e sem acordar o
servico de decisao, para que as reguas possam ser aprendidas ja; depois,
recalcula as reguas.

Por padrao NAO publica nos trechos do no real (BANCADA-01), para nao mexer na
demonstracao da bancada; --incluir-bancada desliga essa protecao.

    API_URL=https://... CHAVE_API=... python -m simulador.gerador_volumes [--ciclo-min 60]
    DATABASE_URL=... python -m simulador.gerador_volumes --historico 28
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import time
import urllib.request
from datetime import datetime, timedelta, timezone

from cadastro.recorte import RECORTE

TRECHOS_BANCADA = {20159, 21198, 22661}
# Pessoas na area no horario de pico de cada trecho, distribuidas pelos trechos
# em ordem fixa: de rua quase vazia a rua movimentada.
ESCALAS = [0.5, 1.0, 2.0, 4.0, 8.0, 1.5, 3.0, 6.0]
INICIO_DA_NOITE = 0.6  # fracao do pico no comeco da "noite" ao vivo
# Dia tipico (fracao do pico por hora local), para o historico inventado.
PERFIL_DIA = [0.05, 0.03, 0.02, 0.02, 0.03, 0.08, 0.3, 0.6, 0.7, 0.55, 0.5, 0.55,
              0.6, 0.55, 0.5, 0.55, 0.7, 0.9, 1.0, 0.85, 0.6, 0.4, 0.25, 0.12]
PERIODO_S = 300

# --perfis (demonstracao da previsao): cada trecho segue, pelo RELOGIO REAL, um
# de tres dias tipicos (fracao do pico por hora local, 0 a 23 h), no
# historico e ao vivo. A noite de 18 h a 21 h e calma nos tres; o que muda e
# o que vem depois, e so a previsao sabe disso:
#   dormitorio:    segue vazio -> prevista baixa -> desce a classe minima (R5)
#   comercial:     enche das 21 h a 1 h -> prevista alta -> fica no pleno (R3)
#   intermediario: movimento medio a noite toda -> uma classe abaixo (R4/R6)
PERFIS = {
    "dormitorio":    [0.02, 0.01, 0.01, 0.01, 0.05, 0.3, 0.9, 1.0, 0.7, 0.4, 0.3, 0.3,
                      0.35, 0.3, 0.3, 0.35, 0.5, 0.7, 0.04, 0.03, 0.03, 0.02, 0.02, 0.02],
    "comercial":     [0.8, 0.4, 0.1, 0.03, 0.02, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5,
                      0.6, 0.5, 0.4, 0.4, 0.4, 0.3, 0.04, 0.04, 0.05, 0.9, 1.0, 1.0],
    "intermediario": [0.15, 0.1, 0.05, 0.05, 0.05, 0.1, 0.3, 0.5, 0.5, 0.4, 0.4, 0.4,
                      0.5, 0.4, 0.4, 0.4, 0.5, 0.6, 0.18, 0.18, 0.18, 0.18, 0.18, 0.17],
}
ORDEM_PERFIS = ["dormitorio", "comercial", "intermediario"]

log = logging.getLogger("gerador")


def trechos() -> list[int]:
    rec = json.loads(RECORTE.read_text(encoding="utf-8"))
    return sorted(f["properties"]["cd_identificador"] for f in rec["trechos"]["geojson"]["features"])


def escalas(ids: list[int]) -> dict[int, float]:
    return {t: ESCALAS[i % len(ESCALAS)] for i, t in enumerate(sorted(ids))}


def perfis(ids: list[int]) -> dict[int, str]:
    return {t: ORDEM_PERFIS[i % len(ORDEM_PERFIS)] for i, t in enumerate(sorted(ids))}


def volume_perfil(perfil: str, escala: float, quando: datetime, rnd: random.Random) -> float:
    """Pessoas em media no periodo, pela hora local, interpolando entre as horas."""
    from decisao import config

    local = quando.astimezone(config.FUSO)
    h = local.hour + local.minute / 60
    v = PERFIS[perfil]
    f = v[int(h) % 24] + (v[(int(h) + 1) % 24] - v[int(h) % 24]) * (h - int(h))
    return max(0.0, escala * f * (1 + rnd.gauss(0, 0.1)))


def pacote_perfis(ids, pesos, tipos, rnd, agora) -> list[dict]:
    return [{"ocorrido_em": agora.isoformat(), "tipo": "volume",
             "pessoas_media": round(volume_perfil(tipos[t], pesos[t], agora, rnd), 2),
             "periodo_s": PERIODO_S, "trecho": t, "origem": "gerador-demo"} for t in ids]


def gravar_historico_perfis(ids, pesos, tipos, dias, rnd) -> None:
    """Como gravar_historico, mas pelos perfis e comecando depois do ultimo
    volume ja gravado nesses trechos (nao duplica periodos)."""
    import psycopg

    from decisao import ciclo, config

    agora = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    agora = agora - timedelta(minutes=agora.minute % 5)
    with psycopg.connect(os.environ.get("DATABASE_URL", config.DATABASE_URL)) as conn:
        ultimo = conn.execute("SELECT max(ocorrido_em) FROM evento_urbano WHERE tipo = 'volume'"
                              " AND trecho_id = ANY(%s)", (ids,)).fetchone()[0]
        inicio = agora - timedelta(days=dias)
        if ultimo and ultimo > inicio:
            inicio = ultimo + timedelta(seconds=PERIODO_S)
        conn.execute("ALTER TABLE evento_urbano DISABLE TRIGGER evento_urbano_aviso")
        n = 0
        with conn.cursor().copy(
            "COPY evento_urbano (ocorrido_em, tipo, pessoas_media, periodo_s, origem, trecho_id)"
            " FROM STDIN") as copia:
            t = inicio
            while t < agora:
                for tr in ids:
                    copia.write_row((t, "volume", round(volume_perfil(tipos[tr], pesos[tr], t, rnd), 2),
                                     PERIODO_S, "gerador-demo-historico", tr))
                    n += 1
                t += timedelta(seconds=PERIODO_S)
        conn.execute("ALTER TABLE evento_urbano ENABLE TRIGGER evento_urbano_aviso")
        ciclo.atualizar_referencias(conn, datetime.now(timezone.utc))
        conn.commit()
    log.info("historico por perfis: %s volumes de %s a %s; perfis: %s", n, inicio, agora,
             ", ".join(f"{t}={tipos[t]}" for t in ids))


def pacote(ids: list[int], fracao_da_noite: float, pesos: dict[int, float], rnd: random.Random,
           agora: datetime) -> list[dict]:
    """Volume de cada trecho: perfil que esvazia (1 - f)^2, escala do trecho e ruido de 10 %."""
    base = INICIO_DA_NOITE * (1 - fracao_da_noite) ** 2
    itens = []
    for t in ids:
        media = max(0.0, base * pesos[t] * (1 + rnd.gauss(0, 0.1)))
        itens.append({"ocorrido_em": agora.isoformat(), "tipo": "volume",
                      "pessoas_media": round(media, 2), "periodo_s": PERIODO_S,
                      "trecho": t, "origem": "gerador-demo"})
    return itens


def publicar(url: str, chave: str, itens: list[dict]) -> dict:
    req = urllib.request.Request(url.rstrip("/") + "/eventos", data=json.dumps(itens).encode(),
                                 headers={"Content-Type": "application/json", "X-Chave-Api": chave},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def gravar_historico(ids: list[int], pesos: dict[int, float], dias: int, rnd: random.Random) -> None:
    """Passado inventado de `dias` dias, a cada 5 min, direto no banco. O aviso ao
    servico fica desligado so durante a carga: um evento antigo nao decide nada."""
    import psycopg

    from decisao import ciclo, config

    agora = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    agora = agora - timedelta(minutes=agora.minute % 5)
    inicio = agora - timedelta(days=dias)
    with psycopg.connect(os.environ.get("DATABASE_URL", config.DATABASE_URL)) as conn:
        conn.execute("ALTER TABLE evento_urbano DISABLE TRIGGER evento_urbano_aviso")
        n = 0
        with conn.cursor().copy(
            "COPY evento_urbano (ocorrido_em, tipo, pessoas_media, periodo_s, origem, trecho_id)"
            " FROM STDIN") as copia:
            t = inicio
            while t < agora:
                hora = t.astimezone(config.FUSO).hour
                for tr in ids:
                    media = max(0.0, pesos[tr] * PERFIL_DIA[hora] * (1 + rnd.gauss(0, 0.15)))
                    copia.write_row((t, "volume", round(media, 2), PERIODO_S,
                                     "gerador-demo-historico", tr))
                    n += 1
                t += timedelta(seconds=PERIODO_S)
        conn.execute("ALTER TABLE evento_urbano ENABLE TRIGGER evento_urbano_aviso")
        ciclo.atualizar_referencias(conn, datetime.now(timezone.utc))
        conn.commit()
        reguas = conn.execute(
            "SELECT id, referencia_aprendida FROM trecho_via WHERE id = ANY(%s) ORDER BY id",
            (ids,)).fetchall()
    log.info("historico: %s volumes em %s dias; reguas aprendidas: %s", n, dias,
             ", ".join(f"{t}={r}" for t, r in reguas))


def main() -> None:
    p = argparse.ArgumentParser(description="volumes inventados para a visao de bairro")
    p.add_argument("--ciclo-min", type=float, default=60, help="duracao de uma 'noite' simulada")
    p.add_argument("--intervalo-s", type=float, default=PERIODO_S)
    p.add_argument("--incluir-bancada", action="store_true")
    p.add_argument("--semente", type=int, default=42)
    p.add_argument("--uma-vez", action="store_true")
    p.add_argument("--historico", type=int, default=0, metavar="DIAS",
                   help="grava DIAS de passado inventado no banco e recalcula as reguas")
    p.add_argument("--perfis", action="store_true",
                   help="tres dias tipicos por trecho, pelo relogio real (demonstracao da previsao)")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    url = os.environ.get("API_URL", "http://localhost:8000")
    chave = os.environ.get("CHAVE_API", "")
    ids = [t for t in trechos() if a.incluir_bancada or t not in TRECHOS_BANCADA]
    rnd = random.Random(a.semente)
    pesos = escalas(ids)  # ruas quase vazias e ruas movimentadas
    tipos = perfis(ids)
    if a.historico:
        if a.perfis:
            gravar_historico_perfis(ids, pesos, tipos, a.historico, rnd)
        else:
            gravar_historico(ids, pesos, a.historico, rnd)
        return
    if a.perfis:
        log.info("perfis: %s", ", ".join(f"{t}={tipos[t]}" for t in ids))
        while True:
            try:
                r = publicar(url, chave, pacote_perfis(ids, pesos, tipos, rnd,
                                                       datetime.now(timezone.utc)))
                log.info("perfis: %s aceitos, %s recusados", len(r["aceitos"]), len(r["recusados"]))
            except Exception as erro:
                log.warning("publicacao falhou: %s", erro)
            if a.uma_vez:
                return
            time.sleep(a.intervalo_s)
    inicio = time.monotonic()
    while True:
        f = ((time.monotonic() - inicio) / 60 % a.ciclo_min) / a.ciclo_min
        try:
            r = publicar(url, chave, pacote(ids, f, pesos, rnd, datetime.now(timezone.utc)))
            log.info("noite %.0f%%: %s aceitos, %s recusados", f * 100, len(r["aceitos"]),
                     len(r["recusados"]))
        except Exception as erro:  # demonstracao: segue tentando
            log.warning("publicacao falhou: %s", erro)
        if a.uma_vez:
            return
        time.sleep(a.intervalo_s)


if __name__ == "__main__":
    main()
