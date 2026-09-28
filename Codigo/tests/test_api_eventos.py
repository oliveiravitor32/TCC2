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

# Leitura do trecho (DIVERGENCIAS 55): pessoas na area + ocorrencia.
MOV = {
    "ocorrido_em": "2026-09-21T01:00:00-03:00",
    "pessoas": 2,
    "origem": "emulador-smart-sampa",
    "trecho": 20159,  # R. Antonio Viana, trecho real do recorte (db/seed_cadastro.sql)
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
def test_publica_leitura(cliente):
    r = cliente.post("/eventos", json=MOV)
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["id"] > 0 and corpo["pessoas"] == 2 and corpo["ocorrencia"] is None
    assert corpo["tipo"] == "leitura" and corpo["abrangencia"] == "via"


@pytest.mark.parametrize("ocorrencia", ["seguranca", "transito"])
def test_publica_leitura_com_ocorrencia(cliente, ocorrencia):
    r = cliente.post("/eventos", json={**MOV, "pessoas": 0, "ocorrencia": ocorrencia})
    assert r.status_code == 201 and r.json()["ocorrencia"] == ocorrencia


@pytest.mark.parametrize(
    "alteracao",
    [
        {"placa": "ABC1D23"},  # campo fora do contrato (RNF08)
        {"imagem": "base64..."},
        {"rosto": "..."},
        {"pessoas": -1},
        {"pessoas": 1.5},
        {"pessoas": None},
        {"valor": 0.12},  # contrato antigo (nivel normalizado): nao existe mais
        {"tipo": "movimentacao"},
        {"tipo": "meteorologia"},  # fora do contrato (item 49)
        {"ocorrencia": "granizo"},  # fora do vocabulario
        {"ocorrencia": "encerrada"},  # ausencia de ocorrencia = campo ausente
        {"ocorrido_em": "2026-09-21T01:00:00"},  # sem fuso horario
        {"vigente_ate": "2026-09-21T00:00:00-03:00"},  # vigencia antes da ocorrencia
        {"trecho": None},  # sem trecho: o evento nao diz onde
        {"trecho": 0},
    ],
)
def test_recusa_evento_fora_do_contrato(cliente, alteracao):
    r = cliente.post("/eventos", json={**MOV, **alteracao})
    assert r.status_code == 422, r.json()


def test_leitura_sem_pessoas_e_recusada(cliente):
    corpo = {k: v for k, v in MOV.items() if k != "pessoas"}
    assert cliente.post("/eventos", json=corpo).status_code == 422


def test_nenhum_evento_invalido_chega_ao_banco(cliente, conn):
    antes = conn.execute("SELECT count(*) AS n FROM evento_urbano").fetchone()["n"]
    cliente.post("/eventos", json={**MOV, "placa": "ABC1D23"})
    depois = conn.execute("SELECT count(*) AS n FROM evento_urbano").fetchone()["n"]
    assert depois == antes


# --------------------------------------------------------------------------
# GET /eventos
# --------------------------------------------------------------------------
def test_consulta_filtra_por_intervalo(cliente):
    cliente.post("/eventos", json=MOV)
    cliente.post("/eventos", json={**MOV, "ocorrido_em": "2026-09-21T03:00:00-03:00"})
    r = cliente.get(
        "/eventos",
        params={"inicio": "2026-09-21T00:30:00-03:00", "fim": "2026-09-21T02:00:00-03:00"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1 and r.json()[0]["pessoas"] == 2


# --------------------------------------------------------------------------
# GET /decisoes e /telemetria
# --------------------------------------------------------------------------
def _decisao_com_telemetria(conn) -> str:
    ev = conn.execute(
        "INSERT INTO evento_urbano (ocorrido_em, pessoas, origem, trecho_id)"
        " VALUES (now(), 0, 't', 20159) RETURNING id"
    ).fetchone()["id"]
    d = conn.execute(
        """
        INSERT INTO decisao (ponto_de_luz_id, versao_base_regras_id, versao_modelo_id,
                             classe_codigo, nivel_pretendido, nivel_emitido, restricao_aplicada)
        SELECT p.id, r.id, m.id, 'P3', 0.171, 0.500, 'piso'
          FROM ponto_de_luz p, versao_base_regras r, versao_modelo_previsao m
         WHERE p.codigo = 'BANCADA-01' AND r.rotulo = 'v3-presenca' AND m.rotulo = 'persistencia'
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
    assert linha["versao_base_regras"] == "v3-presenca"
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


# --------------------------------------------------------------------------
# GET /energia (RF12, 3.11): consumo estimado para a luminaria de referencia
# --------------------------------------------------------------------------
def _telemetria_em(conn, quando, nivel, lux, residual_sessao=None):
    """Uma decisao com telemetria num instante dado, para a serie de energia."""
    sessao = None
    if residual_sessao is not None:
        sessao = conn.execute(
            "INSERT INTO sessao_medicao (ponto_de_luz_id, lux_residual, lux_classe)"
            " SELECT id, %s, 10 FROM ponto_de_luz WHERE codigo = 'BANCADA-01' RETURNING id",
            (residual_sessao,),
        ).fetchone()["id"]
    d = conn.execute(
        """
        INSERT INTO decisao (criado_em, ponto_de_luz_id, versao_base_regras_id,
                             versao_modelo_id, classe_codigo, nivel_pretendido,
                             nivel_emitido, restricao_aplicada)
        SELECT %s, p.id, r.id, m.id, 'P3', %s, %s, 'nenhuma'
          FROM ponto_de_luz p, versao_base_regras r, versao_modelo_previsao m
         WHERE p.codigo = 'BANCADA-01' AND r.rotulo = 'v3-presenca'
           AND m.rotulo = 'persistencia'
        RETURNING id
        """,
        (quando, nivel, nivel),
    ).fetchone()["id"]
    conn.execute(
        "INSERT INTO telemetria (decisao_id, ponto_de_luz_id, sessao_id, medido_em,"
        " recebido_em, duty, lux_medido)"
        " SELECT %s, id, %s, %s, %s, %s, %s FROM ponto_de_luz WHERE codigo = 'BANCADA-01'",
        (d, sessao, quando, quando, nivel / 2, lux),
    )
    return d


def test_energia_sem_telemetria(cliente):
    r = cliente.get("/energia", params={"janela_min": 10}).json()
    assert r["luminaria"] == "REF-40W" and r["potencia_nominal_w"] == 40.0
    assert r["amostras"] == [] and r["potencia_agora_w"] is None
    assert r["energia_pela_luz_wh"] == 0
    assert r["energia_pleno_wh"] == pytest.approx(40 * 10 / 60, abs=0.01)


def test_energia_integra_a_serie_da_luz_medida(cliente, conn):
    import datetime as dt

    agora = dt.datetime.now(dt.timezone.utc)
    # Meia hora inteira no piso (5 lx de 10 lx = metade do fluxo pleno).
    for k in range(30, 0, -1):
        _telemetria_em(conn, agora - dt.timedelta(minutes=k), 0.5, 5.0)
    r = cliente.get("/energia", params={"janela_min": 30}).json()
    # 29 ou 30: a amostra mais antiga cai na borda da janela, e o "agora" do
    # servidor e alguns milissegundos posterior ao do teste.
    assert len(r["amostras"]) >= 29
    assert r["amostras"][-1]["fracao_medida"] == pytest.approx(0.5, abs=0.01)
    assert r["potencia_agora_w"] == pytest.approx(20.0, abs=0.5)
    # Metade da potencia por meia hora: cerca de 10 Wh, contra 20 Wh do pleno.
    assert r["energia_pela_luz_wh"] == pytest.approx(10.0, rel=0.06)
    assert r["energia_pleno_wh"] == pytest.approx(20.0, abs=0.01)
    assert r["razao_pleno"] == pytest.approx(0.5, rel=0.05)


def test_energia_desconta_a_residual_da_sessao(cliente, conn):
    import datetime as dt

    agora = dt.datetime.now(dt.timezone.utc)
    # 5,4 lx medidos com 0,4 de residual = 5,0 liquidos = metade do pleno.
    _telemetria_em(conn, agora - dt.timedelta(minutes=2), 0.5, 5.4, residual_sessao=0.4)
    _telemetria_em(conn, agora - dt.timedelta(minutes=1), 0.5, 5.4, residual_sessao=None)
    r = cliente.get("/energia", params={"janela_min": 10}).json()
    assert r["amostras"][0]["fracao_medida"] == pytest.approx(0.5, abs=0.01)
    # Sem sessao aberta, a residual nao e descontada e a fracao sai maior.
    assert r["amostras"][1]["fracao_medida"] > r["amostras"][0]["fracao_medida"]


def test_energia_nos_dois_extremos_da_faixa_contratual(cliente, conn):
    import datetime as dt

    agora = dt.datetime.now(dt.timezone.utc)
    for k in range(10, 0, -1):
        _telemetria_em(conn, agora - dt.timedelta(minutes=k), 0.5, 5.0)
    p40 = cliente.get("/energia", params={"janela_min": 10}).json()
    p440 = cliente.get("/energia", params={"janela_min": 10, "luminaria": "REF-440W"}).json()
    assert p440["energia_pela_luz_wh"] == pytest.approx(11 * p40["energia_pela_luz_wh"], rel=1e-3)
    # 3.11: a razao entre regimes nao depende da potencia nominal.
    assert p440["razao_pleno"] == pytest.approx(p40["razao_pleno"], rel=1e-3)


def test_energia_com_luminaria_desconhecida(cliente):
    assert cliente.get("/energia", params={"luminaria": "REF-1W"}).status_code == 404


# ---------------------------------------------------------------------------
# Chave de acesso no POST (DIVERGENCIAS 22)
# ---------------------------------------------------------------------------
@pytest.fixture
def com_chave(monkeypatch):
    import api_eventos.app as modulo
    monkeypatch.setattr(modulo, "CHAVE_API", "segredo-de-teste")


def test_post_sem_chave_e_recusado(cliente, com_chave, conn):
    antes = conn.execute("SELECT count(*) AS n FROM evento_urbano").fetchone()["n"]
    assert cliente.post("/eventos", json=MOV).status_code == 401
    assert cliente.post("/eventos", json=MOV, headers={"X-Chave-Api": "errada"}).status_code == 401
    assert conn.execute("SELECT count(*) AS n FROM evento_urbano").fetchone()["n"] == antes


def test_post_com_chave_e_aceito(cliente, com_chave):
    r = cliente.post("/eventos", json=MOV, headers={"X-Chave-Api": "segredo-de-teste"})
    assert r.status_code == 201


def test_consultas_nao_exigem_chave(cliente, com_chave):
    assert cliente.get("/eventos").status_code == 200
    assert cliente.get("/pontos").status_code == 200


# ---------------------------------------------------------------------------
# Trecho de via (DIVERGENCIAS 54)
# ---------------------------------------------------------------------------
def test_evento_sem_trecho_e_recusado(cliente):
    corpo = {k: v for k, v in MOV.items() if k != "trecho"}
    assert cliente.post("/eventos", json=corpo).status_code == 422


def test_trecho_fora_do_cadastro_e_recusado(cliente, conn):
    antes = conn.execute("SELECT count(*) AS n FROM evento_urbano").fetchone()["n"]
    r = cliente.post("/eventos", json={**MOV, "trecho": 999999999})
    assert r.status_code == 422 and "nao cadastrado" in r.json()["detail"]
    assert conn.execute("SELECT count(*) AS n FROM evento_urbano").fetchone()["n"] == antes


def test_evento_devolve_e_filtra_por_trecho(cliente):
    assert cliente.post("/eventos", json=MOV).json()["trecho"] == 20159
    cliente.post("/eventos", json={**MOV, "trecho": 19400})
    assert {e["trecho"] for e in cliente.get("/eventos", params={"trecho": 19400}).json()} == {19400}


def test_trechos_lista_as_luminarias_associadas(cliente):
    trechos = {t["id"]: t for t in cliente.get("/trechos").json()}
    assert trechos[20159]["nome_logradouro"] == "ANTONIO VIANA"
    assert trechos[20159]["pontos"] == ["BANCADA-01"]
    assert trechos[19400]["pontos"] == ["SIMULADO-02"]
    assert trechos[18570]["pontos"] == []  # R. Vinhais: nenhum poste com no


def test_pontos_trazem_placa_e_trechos(cliente):
    linha = next(p for p in cliente.get("/pontos").json() if p["codigo"] == "BANCADA-01")
    assert linha["placa"] == "IP0412418"
    assert linha["trechos"][0] == 20159  # o mais proximo primeiro


# ---------------------------------------------------------------------------
# Chave do painel de demonstracao e explicacao da decisao (DIVERGENCIAS 55)
# ---------------------------------------------------------------------------
def test_chave_demo_tambem_publica(cliente, com_chave, monkeypatch):
    import api_eventos.app as modulo
    monkeypatch.setattr(modulo, "CHAVE_DEMO", "chave-do-painel")
    assert cliente.post("/eventos", json=MOV, headers={"X-Chave-Api": "chave-do-painel"}).status_code == 201
    monkeypatch.setattr(modulo, "CHAVE_DEMO", "")  # desligada
    assert cliente.post("/eventos", json=MOV, headers={"X-Chave-Api": "chave-do-painel"}).status_code == 401


def test_explicacao_mostra_regras_e_correcao(cliente, conn):
    from decisao import ciclo
    from decisao.inferencia import carregar
    from decisao.previsao import Persistencia

    ev = cliente.post("/eventos", json={**MOV, "pessoas": 0,
                                        "ocorrido_em": "2031-03-10T01:00:00-03:00"}).json()
    from datetime import datetime, timezone

    from psycopg.rows import tuple_row

    base = carregar()
    conn.row_factory = tuple_row  # o ciclo trabalha com tuplas; a API, com dicionarios
    ponto = next(p for p in ciclo.pontos(conn) if p.codigo == "BANCADA-01")
    ciclo.decidir(conn, base=base, previsor=Persistencia(), ponto=ponto,
                  agora=datetime(2031, 3, 10, 4, 0, 5, tzinfo=timezone.utc),
                  versao_regras_id=ciclo.registrar_versao_regras(conn, base),
                  versao_modelo_id=ciclo.id_modelo(conn, "persistencia"))
    conn.row_factory = dict_row
    r = cliente.get(f"/eventos/{ev['id']}/explicacao")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["trecho_nome"] == "R ANTONIO VIANA"
    d = corpo["decisoes"][0]
    assert d["ponto"] == "BANCADA-01" and d["decidida"]
    assert d["entrada"]["presenca"] is False
    assert d["regras_ativadas"][0]["id"] == "R4"  # via vazia, previsao baixa: reduzido
    assert "presenca = nao" in d["regras_ativadas"][0]["texto"]
    assert d["restricao_aplicada"] == "piso" and "piso" in d["motivo_restricao"]
    assert d["nivel_emitido"] == 0.5


def test_explicacao_de_evento_inexistente(cliente):
    assert cliente.get("/eventos/999999999/explicacao").status_code == 404
