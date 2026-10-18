"""Grupo de controle (3.12.6.4, DIVERGENCIAS 76): uma avaliacao por grupo,
resultado identico ao de decidir ponto a ponto, sem cascata entre grupos."""

from __future__ import annotations

from datetime import timedelta

import psycopg
import pytest

from decisao import ciclo, config, grupos
from decisao.previsao import Persistencia

from tests.test_ciclo import ANTONIO_VIANA, ASCENSO_FERNANDES, BASE, T0, ocorrencia, volume

try:
    psycopg.connect(config.DATABASE_URL, connect_timeout=2).close()
except psycopg.OperationalError:
    pytest.skip("Postgres indisponivel (docker compose up -d db)", allow_module_level=True)


@pytest.fixture
def conn():
    c = psycopg.connect(config.DATABASE_URL)
    for t in ("alerta_diagnostico", "telemetria", "decisao_evento", "decisao",
              "calibracao", "sessao_medicao", "evento_urbano"):
        c.execute(f"DELETE FROM {t}")
    try:
        yield c
    finally:
        c.rollback()
        c.close()


def _novo_ponto(conn, codigo: str, trechos: list[int]) -> None:
    pid = conn.execute(
        "INSERT INTO ponto_de_luz (codigo, classe_codigo, simulado) VALUES (%s, 'P3', true) RETURNING id",
        (codigo,),
    ).fetchone()[0]
    for t in trechos:
        conn.execute("INSERT INTO trecho_ponto (trecho_id, ponto_de_luz_id, distancia_m, criterio)"
                     " VALUES (%s, %s, 1, 'teste')", (t, pid))


@pytest.fixture
def cadastro(conn):
    """BANCADA-01 + dois pontos com os MESMOS trechos dela + um so com Antonio Viana."""
    trechos_bancada = [r[0] for r in conn.execute(
        "SELECT tp.trecho_id FROM trecho_ponto tp JOIN ponto_de_luz p ON p.id = tp.ponto_de_luz_id"
        " WHERE p.codigo = 'BANCADA-01'").fetchall()]
    _novo_ponto(conn, "GRP-A", trechos_bancada)
    _novo_ponto(conn, "GRP-B", trechos_bancada)
    _novo_ponto(conn, "GRP-C", [ANTONIO_VIANA])
    grupos.recalcular(conn)
    return {p.codigo: p for p in ciclo.pontos(conn)}


def _args(conn):
    return dict(base=BASE, previsor=Persistencia(),
                versao_regras_id=ciclo.registrar_versao_regras(conn, BASE),
                versao_modelo_id=ciclo.id_modelo(conn, "persistencia"))


def test_cada_ponto_em_um_unico_grupo_e_recalculo_estavel(conn, cadastro):
    p = cadastro
    assert p["BANCADA-01"].grupo_id == p["GRP-A"].grupo_id == p["GRP-B"].grupo_id
    assert p["GRP-C"].grupo_id not in (p["BANCADA-01"].grupo_id, p["SIMULADO-02"].grupo_id)
    assert all(x.grupo_id is not None for x in p.values())
    antes = {c: x.grupo_id for c, x in p.items()}
    grupos.recalcular(conn)
    assert {x.codigo: x.grupo_id for x in ciclo.pontos(conn)} == antes


@pytest.mark.parametrize("cenario", ["vazio", "medio", "ocorrencia", "sem_volume"])
def test_decisao_por_grupo_igual_a_ponto_a_ponto(conn, cadastro, cenario):
    membros = [cadastro[c] for c in ("BANCADA-01", "GRP-A", "GRP-B")]
    agora = T0 + timedelta(minutes=10)
    if cenario != "sem_volume":
        volume(conn, em=agora - timedelta(minutes=1), media=0 if cenario == "vazio" else 2.5)
        volume(conn, em=agora - timedelta(minutes=1), media=0, trecho=ASCENSO_FERNANDES)
    if cenario == "ocorrencia":
        ocorrencia(conn, em=agora - timedelta(minutes=1), rotulo="seguranca")
    a = _args(conn)
    with conn.transaction(force_rollback=True):
        sozinhos = [ciclo.decidir(conn, ponto=m, agora=agora, **a) for m in membros]
    em_grupo = ciclo.decidir_grupo(conn, membros, agora=agora, **a)
    for s, g in zip(sozinhos, em_grupo):
        assert (s.nivel_pretendido, s.nivel_emitido, s.restricao_aplicada, s.validade_s) == \
               (g.nivel_pretendido, g.nivel_emitido, g.restricao_aplicada, g.validade_s)
        assert s.observada == g.observada and s.degrau == g.degrau
    gids = conn.execute("SELECT DISTINCT grupo_id FROM decisao").fetchall()
    assert gids == [(membros[0].grupo_id,)]


def test_sem_cascata_entre_grupos(conn, cadastro):
    """Ocorrencia num trecho que GRP-C nao enxerga nao muda a decisao de GRP-C."""
    agora = T0 + timedelta(minutes=10)
    volume(conn, em=agora - timedelta(minutes=1), media=0)
    volume(conn, em=agora - timedelta(minutes=1), media=0, trecho=ASCENSO_FERNANDES)
    ocorrencia(conn, em=agora - timedelta(minutes=1), rotulo="seguranca", trecho=ASCENSO_FERNANDES)
    a = _args(conn)
    bancada = ciclo.decidir_grupo(conn, [cadastro["BANCADA-01"]], agora=agora, **a)[0]
    c = ciclo.decidir_grupo(conn, [cadastro["GRP-C"]], agora=agora, **a)[0]
    assert bancada.nivel_emitido == 1 and c.nivel_emitido < 1


def test_grupo_com_classes_diferentes_e_recusado(conn, cadastro):
    from dataclasses import replace

    p = cadastro["GRP-A"]
    with pytest.raises(ValueError):
        ciclo.decidir_grupo(conn, [p, replace(p, classe_codigo="P4")], agora=T0, **_args(conn))
