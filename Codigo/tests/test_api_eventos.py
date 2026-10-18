"""RF01 / Quadro 14: interface de dados urbanos.

Roda contra o Postgres do docker-compose; cada teste acontece dentro de uma
transacao desfeita ao final. Sem banco disponivel, os testes sao pulados.
"""

from __future__ import annotations

from datetime import datetime, timezone

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from api_eventos.app import DATABASE_URL, app, conexao

try:
    psycopg.connect(DATABASE_URL, connect_timeout=2).close()
except psycopg.OperationalError:
    pytest.skip("Postgres indisponivel (docker compose up -d db)", allow_module_level=True)

# Volume do trecho (DIVERGENCIAS 56): media de pessoas na area em 5 min.
MOV = {
    "ocorrido_em": "2026-09-21T01:00:00-03:00",
    "tipo": "volume",
    "pessoas_media": 2,
    "origem": "emulador-smart-sampa",
    "trecho": 20159,  # R. Antonio Viana, trecho real do recorte (db/seed_cadastro.sql)
}
OCO = {
    "ocorrido_em": "2026-09-21T01:00:00-03:00",
    "tipo": "ocorrencia",
    "ocorrencia": "seguranca",
    "origem": "emulador-smart-sampa",
    "trecho": 20159,
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
def test_publica_volume(cliente):
    r = cliente.post("/eventos", json=MOV)
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["id"] > 0 and corpo["pessoas_media"] == 2 and corpo["ocorrencia"] is None
    assert corpo["tipo"] == "volume" and corpo["periodo_s"] == 300  # 5 min por padrao
    assert corpo["abrangencia"] == "via"


@pytest.mark.parametrize("ocorrencia", ["seguranca", "transito", "encerrada"])
def test_publica_ocorrencia(cliente, ocorrencia):
    r = cliente.post("/eventos", json={**OCO, "ocorrencia": ocorrencia})
    assert r.status_code == 201
    assert r.json()["ocorrencia"] == ocorrencia and r.json()["pessoas_media"] is None


@pytest.mark.parametrize(
    "alteracao",
    [
        {"placa": "ABC1D23"},  # campo fora do contrato (RNF08)
        {"imagem": "base64..."},
        {"rosto": "..."},
        {"pessoas_media": -1},
        {"pessoas_media": None},  # volume sem media
        {"pessoas": 2},  # contrato antigo (leitura instantanea): nao existe mais
        {"valor": 0.12},  # contrato mais antigo (nivel normalizado)
        {"tipo": "leitura"},
        {"tipo": "meteorologia"},  # fora do contrato (item 49)
        {"ocorrencia": "seguranca"},  # ocorrencia vai em publicacao propria
        {"periodo_s": 0},
        {"periodo_s": 4000},
        {"ocorrido_em": "2026-09-21T01:00:00"},  # sem fuso horario
        {"vigente_ate": "2026-09-21T00:00:00-03:00"},  # vigencia antes do fim do periodo
        {"trecho": None},  # sem trecho: o evento nao diz onde
        {"trecho": 0},
    ],
)
def test_recusa_volume_fora_do_contrato(cliente, alteracao):
    r = cliente.post("/eventos", json={**MOV, **alteracao})
    assert r.status_code == 422, r.json()


@pytest.mark.parametrize(
    "alteracao",
    [{"ocorrencia": "granizo"}, {"ocorrencia": None}, {"pessoas_media": 1}, {"periodo_s": 300}],
)
def test_recusa_ocorrencia_fora_do_contrato(cliente, alteracao):
    assert cliente.post("/eventos", json={**OCO, **alteracao}).status_code == 422


def test_trecho_fora_do_cadastro_e_recusado(cliente):
    r = cliente.post("/eventos", json={**MOV, "trecho": 999999999})
    assert r.status_code == 422 and "nao cadastrado" in r.json()["detail"]


# --------------------------------------------------------------------------
# Pacote por regiao (DIVERGENCIAS 56): so o item errado e recusado
# --------------------------------------------------------------------------
def test_pacote_grava_os_validos_e_recusa_so_os_errados(cliente, conn):
    pacote = [
        MOV,
        {**MOV, "placa": "ABC1D23"},
        {**MOV, "trecho": 999999999},
        {**OCO, "trecho": 22661},
    ]
    r = cliente.post("/eventos", json=pacote)
    assert r.status_code == 200
    corpo = r.json()
    assert [e["trecho"] for e in corpo["aceitos"]] == [20159, 22661]
    assert [x["indice"] for x in corpo["recusados"]] == [1, 2]
    assert "nao cadastrado" in corpo["recusados"][1]["erro"]
    n = conn.execute("SELECT count(*) AS n FROM evento_urbano").fetchone()["n"]
    assert n == 2


@pytest.mark.parametrize("corpo", [[], "texto", 3])
def test_pacote_vazio_ou_corpo_invalido_e_recusado(cliente, corpo):
    assert cliente.post("/eventos", json=corpo).status_code == 422


def test_pacote_acima_do_limite_e_recusado(cliente, monkeypatch):
    from decisao import config
    monkeypatch.setattr(config, "MAX_ITENS_PACOTE", 2)
    assert cliente.post("/eventos", json=[MOV, MOV, MOV]).status_code == 422


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
    assert len(r.json()) == 1 and r.json()[0]["pessoas_media"] == 2


# --------------------------------------------------------------------------
# GET /decisoes e /telemetria
# --------------------------------------------------------------------------
def _decisao_com_telemetria(conn) -> str:
    ev = conn.execute(
        "INSERT INTO evento_urbano (ocorrido_em, tipo, pessoas_media, periodo_s, origem, trecho_id)"
        " VALUES (now(), 'volume', 0, 300, 't', 20159) RETURNING id"
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
# Chave do painel de demonstracao e explicacao da decisao (DIVERGENCIAS 55 e 56)
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

    ev = cliente.post("/eventos", json={**MOV, "pessoas_media": 0,
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
    assert d["entrada"]["observada"] == 0.0
    assert d["entrada"]["niveis_classe"] == [1.0, 0.75, 0.5]
    assert d["regras_ativadas"][0]["id"] == "R5"  # volume baixo, previsao baixa: classe minima
    assert "observada = baixa" in d["regras_ativadas"][0]["texto"]
    assert d["restricao_aplicada"] == "nenhuma" and "sem correcao" in d["motivo_restricao"]
    assert d["nivel_emitido"] == 0.5


def test_explicacao_de_evento_inexistente(cliente):
    assert cliente.get("/eventos/999999999/explicacao").status_code == 404


# --------------------------------------------------------------------------
# POST /bancada (DIVERGENCIAS 65): so a chave secreta grava medicao
# --------------------------------------------------------------------------
SESSAO = {"ponto": "BANCADA-01", "lux_residual": 0.2, "aprovada": True,
          "observacao": "conferencia de teste"}


def test_bancada_recusa_a_chave_publica_do_painel(cliente, com_chave, monkeypatch):
    import api_eventos.app as modulo
    monkeypatch.setattr(modulo, "CHAVE_DEMO", "chave-do-painel")
    r = cliente.post("/bancada/sessoes", json=SESSAO, headers={"X-Chave-Api": "chave-do-painel"})
    assert r.status_code == 401
    assert cliente.post("/bancada/sessoes", json=SESSAO).status_code == 401


def test_conferencia_aprovada_abre_sessao_e_encerra_as_anteriores(cliente, com_chave, conn):
    h = {"X-Chave-Api": "segredo-de-teste"}
    a = cliente.post("/bancada/sessoes", json=SESSAO, headers=h).json()["sessao_id"]
    b = cliente.post("/bancada/sessoes", json=SESSAO, headers=h).json()["sessao_id"]
    abertas = conn.execute(
        "SELECT id FROM sessao_medicao WHERE encerrada_em IS NULL").fetchall()
    assert [x["id"] for x in abertas] == [b] and a != b
    reprovada = cliente.post("/bancada/sessoes", json={**SESSAO, "aprovada": False}, headers=h)
    assert reprovada.status_code == 201
    assert conn.execute("SELECT count(*) AS n FROM sessao_medicao WHERE encerrada_em IS NULL"
                        ).fetchone()["n"] == 1


def test_lux_da_classe_vem_do_banco_e_nao_do_cliente(cliente, com_chave, conn):
    h = {"X-Chave-Api": "segredo-de-teste"}
    assert cliente.post("/bancada/sessoes", json={**SESSAO, "lux_classe": 1}, headers=h
                        ).status_code == 422
    sid = cliente.post("/bancada/sessoes", json=SESSAO, headers=h).json()["sessao_id"]
    assert float(conn.execute("SELECT lux_classe FROM sessao_medicao WHERE id = %s", (sid,)
                              ).fetchone()["lux_classe"]) == 10.0


def test_calibracao_grava_sessao_encerrada_e_linhas(cliente, com_chave, conn):
    h = {"X-Chave-Api": "segredo-de-teste"}
    corpo = {"ponto": "BANCADA-01", "lux_residual": 0.1, "observacao": "teste",
             "linhas": [{"serie": 1, "duty": 0.5, "lux_medido": 9.0},
                        {"serie": 2, "duty": 0.5, "lux_medido": 9.1}]}
    r = cliente.post("/bancada/calibracoes", json=corpo, headers=h)
    assert r.status_code == 201
    sid = r.json()["sessao_id"]
    assert conn.execute("SELECT count(*) AS n FROM calibracao WHERE sessao_id = %s", (sid,)
                        ).fetchone()["n"] == 2
    assert conn.execute("SELECT encerrada_em FROM sessao_medicao WHERE id = %s", (sid,)
                        ).fetchone()["encerrada_em"] is not None


def test_bancada_ponto_desconhecido_e_404(cliente, com_chave):
    r = cliente.post("/bancada/sessoes", json={**SESSAO, "ponto": "NAO-EXISTE"},
                     headers={"X-Chave-Api": "segredo-de-teste"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Logs da API (rastreabilidade operacional)
# ---------------------------------------------------------------------------
@pytest.fixture
def linhas_de_log():
    import logging

    from api_eventos.app import log as log_api

    linhas: list[str] = []

    class Coletor(logging.Handler):
        def emit(self, registro):
            linhas.append(registro.getMessage())

    h = Coletor()
    log_api.addHandler(h)
    yield linhas
    log_api.removeHandler(h)


def test_log_de_chave_invalida_nao_mostra_a_chave(cliente, com_chave, linhas_de_log):
    r = cliente.post("/eventos", json=MOV, headers={"X-Chave-Api": "tentativa-123"})
    assert r.status_code == 401
    assert any("chave ausente ou invalida" in l for l in linhas_de_log)
    assert not any("tentativa-123" in l or "segredo-de-teste" in l for l in linhas_de_log)


def test_log_de_evento_aceito_traz_id_trecho_e_request_id(cliente, linhas_de_log):
    r = cliente.post("/eventos", json=MOV, headers={"X-Request-ID": "abc123"})
    assert r.status_code == 201
    assert r.headers["X-Request-ID"] == "abc123"
    aceito = [l for l in linhas_de_log if "evento=" in l]
    assert aceito and "rid=abc123" in aceito[0] and f"evento={r.json()['id']}" in aceito[0]
    assert "trecho=20159" in aceito[0]


def test_log_de_pacote_registra_recusados(cliente, linhas_de_log):
    r = cliente.post("/eventos", json=[MOV, {**MOV, "pessoas_media": -1}])
    assert r.status_code == 200
    assert any("item=1 recusado" in l for l in linhas_de_log)
    assert any("aceitos=1 recusados=1" in l for l in linhas_de_log)


def test_log_de_validacao_registra_o_motivo(cliente, linhas_de_log):
    r = cliente.post("/eventos", json={**MOV, "pessoas_media": -1})
    assert r.status_code == 422
    assert any("recusado" in l and "pessoas_media" in l for l in linhas_de_log)


def test_consulta_get_bem_sucedida_nao_gera_log(cliente, linhas_de_log):
    assert cliente.get("/trechos").status_code == 200
    assert linhas_de_log == []


# ---------------------------------------------------------------------------
# Visao de bairro (DIVERGENCIAS 76)
# ---------------------------------------------------------------------------
def test_ponto_simulado_nunca_e_o_padrao_e_vem_marcado(cliente, conn):
    conn.execute("INSERT INTO ponto_de_luz (codigo, classe_codigo, simulado, latitude, longitude)"
                 " VALUES ('AAA-SIM', 'P3', true, -23.48, -46.42)")
    pontos = cliente.get("/pontos").json()
    assert pontos[0]["simulado"] is False  # reais primeiro
    sim = next(p for p in pontos if p["codigo"] == "AAA-SIM")
    assert sim["simulado"] is True and sim["latitude"] == -23.48
    assert cliente.get("/energia").json()["ponto"] != "AAA-SIM"


def test_trechos_trazem_estado_para_o_mapa(cliente):
    cliente.post("/eventos", json={**OCO, "ocorrido_em": datetime.now(timezone.utc).isoformat()})
    t = next(x for x in cliente.get("/trechos").json() if x["id"] == 20159)
    assert t["ocorrencia_aberta"] is True and "geometria_wgs84" in t
