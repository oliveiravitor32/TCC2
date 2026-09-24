"""RF01 / Quadro 14: interface de dados urbanos.

Roda contra o Postgres do docker-compose; cada teste acontece dentro de uma
transacao desfeita ao final. Sem banco disponivel, os testes sao pulados.
"""

from __future__ import annotations

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from api_eventos.app import DATABASE_URL, app, conexao

try:
    psycopg.connect(DATABASE_URL, connect_timeout=2).close()
except psycopg.OperationalError:
    pytest.skip("Postgres indisponivel (docker compose up -d db)", allow_module_level=True)

MOV = {
    "ocorrido_em": "2026-09-21T01:00:00-03:00",
    "tipo": "movimentacao",
    "valor": 0.12,
    "origem": "emulador-smart-sampa",
}


@pytest.fixture
def conn():
    c = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    # A suite de cenarios deixa milhares de eventos e decisoes no banco, com
    # carimbos no relogio virtual. Limpar aqui (e desfazer no rollback) e o
    # que torna estes testes independentes da ordem de execucao.
    for tabela in ("alerta_diagnostico", "telemetria", "decisao_evento", "decisao",
                   "calibracao", "sessao_medicao", "evento_urbano", "execucao_cenario"):
        c.execute(f"DELETE FROM {tabela}")
    try:
        yield c
    finally:
        c.rollback()
        c.close()


@pytest.fixture
def cliente(conn):
    app.dependency_overrides[conexao] = lambda: conn
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --------------------------------------------------------------------------
# POST /eventos
# --------------------------------------------------------------------------
def test_publica_movimentacao(cliente):
    r = cliente.post("/eventos", json=MOV)
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["id"] > 0 and corpo["valor"] == 0.12 and corpo["abrangencia"] == "via"


@pytest.mark.parametrize(
    "tipo,rotulo", [("meteorologia", "chuva"), ("meteorologia", "limpo"), ("ocorrencia", "seguranca")]
)
def test_publica_categoricos(cliente, tipo, rotulo):
    ev = {"ocorrido_em": MOV["ocorrido_em"], "tipo": tipo, "rotulo": rotulo, "origem": "teste"}
    assert cliente.post("/eventos", json=ev).status_code == 201


@pytest.mark.parametrize(
    "alteracao",
    [
        {"placa": "ABC1D23"},  # campo fora do contrato (RNF08)
        {"imagem": "base64..."},
        {"valor": 1.5},  # fora do universo normalizado
        {"valor": None},  # movimentacao sem valor
        {"rotulo": "chuva"},  # movimentacao com rotulo
        {"tipo": "meteorologia", "valor": None, "rotulo": "granizo"},  # fora do vocabulario
        {"tipo": "ocorrencia", "rotulo": "seguranca"},  # categorico com valor
        {"ocorrido_em": "2026-09-21T01:00:00"},  # sem fuso horario
        {"vigente_ate": "2026-09-21T00:00:00-03:00"},  # vigencia antes da ocorrencia
        {"tipo": "bairro"},
    ],
)
def test_recusa_evento_fora_do_contrato(cliente, alteracao):
    r = cliente.post("/eventos", json={**MOV, **alteracao})
    assert r.status_code == 422, r.json()


def test_nenhum_evento_invalido_chega_ao_banco(cliente, conn):
    antes = conn.execute("SELECT count(*) AS n FROM evento_urbano").fetchone()["n"]
    cliente.post("/eventos", json={**MOV, "placa": "ABC1D23"})
    depois = conn.execute("SELECT count(*) AS n FROM evento_urbano").fetchone()["n"]
    assert depois == antes


# --------------------------------------------------------------------------
# GET /eventos
# --------------------------------------------------------------------------
def test_consulta_filtra_por_intervalo_e_tipo(cliente):
    cliente.post("/eventos", json=MOV)
    cliente.post("/eventos", json={**MOV, "ocorrido_em": "2026-09-21T03:00:00-03:00"})
    cliente.post(
        "/eventos",
        json={"ocorrido_em": MOV["ocorrido_em"], "tipo": "meteorologia", "rotulo": "chuva", "origem": "t"},
    )
    r = cliente.get(
        "/eventos",
        params={"inicio": "2026-09-21T00:30:00-03:00", "fim": "2026-09-21T02:00:00-03:00",
                "tipo": "movimentacao"},
    )
    assert r.status_code == 200
    assert [e["tipo"] for e in r.json()] == ["movimentacao"]


# --------------------------------------------------------------------------
# GET /decisoes e /telemetria
# --------------------------------------------------------------------------
def _decisao_com_telemetria(conn) -> str:
    ev = conn.execute(
        "INSERT INTO evento_urbano (ocorrido_em, tipo, valor, origem)"
        " VALUES (now(), 'movimentacao', 0.1, 't') RETURNING id"
    ).fetchone()["id"]
    d = conn.execute(
        """
        INSERT INTO decisao (ponto_de_luz_id, versao_base_regras_id, versao_modelo_id,
                             classe_codigo, nivel_pretendido, nivel_emitido, restricao_aplicada)
        SELECT p.id, r.id, m.id, 'P3', 0.171, 0.500, 'piso'
          FROM ponto_de_luz p, versao_base_regras r, versao_modelo_previsao m
         WHERE p.codigo = 'BANCADA-01' AND r.rotulo = 'v0-provisoria' AND m.rotulo = 'persistencia'
        RETURNING id
        """
    ).fetchone()["id"]
    conn.execute("INSERT INTO decisao_evento VALUES (%s, %s)", (d, ev))
    conn.execute(
        "INSERT INTO telemetria (decisao_id, ponto_de_luz_id, medido_em, duty, lux_medido)"
        " SELECT %s, id, now(), 0.25, 5.1 FROM ponto_de_luz WHERE codigo = 'BANCADA-01'",
        (d,),
    )
    return str(d), ev


def test_decisoes_trazem_a_cadeia_de_auditoria(cliente, conn):
    d, ev = _decisao_com_telemetria(conn)
    r = cliente.get("/decisoes", params={"ponto": "BANCADA-01"})
    assert r.status_code == 200
    linha = next(x for x in r.json() if x["id"] == d)
    assert linha["nivel_pretendido"] == 0.171
    assert linha["nivel_emitido"] == 0.5
    assert linha["restricao_aplicada"] == "piso"
    assert linha["versao_base_regras"] == "v0-provisoria"
    assert linha["versao_modelo"] == "persistencia"
    assert linha["evento_ids"] == [ev]


def test_telemetria_liga_a_decisao(cliente, conn):
    d, _ = _decisao_com_telemetria(conn)
    r = cliente.get("/telemetria", params={"ponto": "BANCADA-01"})
    linha = next(x for x in r.json() if x["decisao_id"] == d)
    assert linha["duty"] == 0.25 and linha["lux_medido"] == 5.1


# --------------------------------------------------------------------------
# GET /pontos e /alertas (fora do Quadro 14; o painel depende deles)
# --------------------------------------------------------------------------
def test_pontos_traz_estado_e_ultima_decisao(cliente, conn):
    d, _ = _decisao_com_telemetria(conn)
    linha = next(p for p in cliente.get("/pontos").json() if p["codigo"] == "BANCADA-01")
    assert linha["classe_codigo"] == "P3"
    assert linha["lux_pleno"] == 10.0
    assert linha["piso_fracao"] == 0.5
    assert linha["estado_operacional"] == "operante"
    assert linha["nivel_emitido"] == 0.5 and linha["restricao_aplicada"] == "piso"
    assert linha["lux_medido"] == 5.1 and linha["duty"] == 0.25


def test_pontos_sem_decisao_nao_quebra(cliente, conn):
    linha = cliente.get("/pontos").json()[0]
    assert linha["nivel_emitido"] is None and linha["lux_medido"] is None


def test_alertas_lista_apenas_os_abertos_por_padrao(cliente, conn):
    d, _ = _decisao_com_telemetria(conn)
    conn.execute(
        "INSERT INTO alerta_diagnostico (ponto_de_luz_id, decisao_id, tipo, razao,"
        " tolerancia, ciclos, encerrado_em)"
        " SELECT id, %s, 'falha_total', 0.02, 0.15, 3, NULL FROM ponto_de_luz"
        " WHERE codigo = 'BANCADA-01'", (d,),
    )
    conn.execute(
        "INSERT INTO alerta_diagnostico (ponto_de_luz_id, tipo, razao, tolerancia,"
        " ciclos, encerrado_em)"
        " SELECT id, 'perda_controle', 0.7, 0.15, 12, now() FROM ponto_de_luz"
        " WHERE codigo = 'BANCADA-01'",
    )
    abertos = cliente.get("/alertas").json()
    assert [a["tipo"] for a in abertos] == ["falha_total"]
    assert abertos[0]["ponto"] == "BANCADA-01" and abertos[0]["ciclos"] == 3
    assert len(cliente.get("/alertas", params={"abertos": False}).json()) == 2


def test_cors_liberado_para_o_painel(cliente):
    r = cliente.get("/pontos", headers={"Origin": "https://painel.vercel.app"})
    assert r.headers.get("access-control-allow-origin") is not None
