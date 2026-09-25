"""Diagnostico do ponto de luz (TCC 3.4.5, RF11).

Primeiro a classificacao pura; depois a integracao com o banco, com a falha
induzida deliberadamente - como 3.4.5 exige, "para que a deteccao seja
verificada e nao apenas afirmada".
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from decisao import ciclo, config
from decisao.diagnostico import Leitura, Limiares, Monitor, classificar, tolerancia_do_ponto
from decisao.inferencia import carregar
from decisao.previsao import Persistencia

LIM = Limiares(tolerancia=0.15, ciclos_falha=3, ciclos_perda=12)


# --------------------------------------------------------------------------
# Classificacao (pura)
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "liquido,esperado_diag",
    [
        (5.0, "normal"),        # exatamente o esperado
        (5.7, "normal"),        # 14 % acima: dentro da tolerancia
        (4.3, "normal"),        # 14 % abaixo
        (6.0, "divergente"),    # 20 % acima
        (4.0, "divergente"),    # 20 % abaixo
        (0.4, "falha_total"),   # praticamente so a residual
        (0.0, "falha_total"),
    ],
)
def test_classificacao(liquido, esperado_diag):
    assert classificar(Leitura(0.5, 5.0, liquido), LIM) == esperado_diag


def test_sem_comando_nao_ha_o_que_verificar():
    assert classificar(Leitura(0.0, 0.0, 0.0), LIM) == "normal"


def test_erro_de_escala_do_sensor_cancela_na_razao():
    # Sensor lendo 20 % a mais em TUDO: a razao continua 1 se a escala da
    # classe for a mesma do instrumento (3.4.4).
    assert classificar(Leitura(0.5, 6.0, 6.0), LIM) == "normal"


# --------------------------------------------------------------------------
# Integracao com o banco
# --------------------------------------------------------------------------
try:
    psycopg.connect(config.DATABASE_URL, connect_timeout=2).close()
except psycopg.OperationalError:
    pytest.skip("Postgres indisponivel (docker compose up -d db)", allow_module_level=True)

BASE = carregar()
T0 = datetime(2031, 5, 5, 4, 0, tzinfo=timezone.utc)


@pytest.fixture
def conn():
    c = psycopg.connect(config.DATABASE_URL)
    for t in ("alerta_diagnostico", "telemetria", "decisao_evento", "decisao",
              "calibracao", "sessao_medicao", "evento_urbano"):
        c.execute(f"DELETE FROM {t}")
    c.execute("UPDATE ponto_de_luz SET estado_operacional = 'operante'")
    try:
        yield c
    finally:
        c.rollback()
        c.close()


@pytest.fixture
def ponto(conn):
    return next(p for p in ciclo.pontos(conn) if p.codigo == "BANCADA-01")


def decidir(conn, ponto, agora):
    return ciclo.decidir(
        conn, base=BASE, previsor=Persistencia(), ponto=ponto, agora=agora,
        versao_regras_id=ciclo.registrar_versao_regras(conn, BASE),
        versao_modelo_id=ciclo.id_modelo(conn, "persistencia"),
    )


def ciclo_com_lux(conn, ponto, agora, lux: float, sessao_id=None):
    """Uma decisao (pleno, por falta de dado) e a telemetria correspondente."""
    d = decidir(conn, ponto, agora)
    conn.execute(
        "INSERT INTO telemetria (decisao_id, ponto_de_luz_id, sessao_id, medido_em, duty, lux_medido)"
        " VALUES (%s, %s, %s, %s, 0.5, %s)",
        (d.id, ponto.id, sessao_id, agora, lux),
    )
    return d


def test_tolerancia_provisoria_sem_ensaio(conn, ponto):
    assert tolerancia_do_ponto(conn, ponto.id) == config.TOLERANCIA_PROVISORIA


def _sessao(conn, ponto, pontos: dict[float, list[float]], residual=0.0, quando=None) -> int:
    """Sessao de calibracao com {duty: [lux da serie 1, 2, 3...]}."""
    sid = conn.execute(
        "INSERT INTO sessao_medicao (ponto_de_luz_id, lux_residual, lux_classe, iniciada_em)"
        " VALUES (%s, %s, 10, COALESCE(%s, now())) RETURNING id", (ponto.id, residual, quando)
    ).fetchone()[0]
    for duty, valores in pontos.items():
        for serie, lux in enumerate(valores, start=1):
            conn.execute(
                "INSERT INTO calibracao (sessao_id, serie, duty, lux_medido) VALUES (%s, %s, %s, %s)",
                (sid, serie, duty, lux),
            )
    return sid


PISO_RESOLUCAO = config.DEGRAUS_TOLERANCIA * config.RESOLUCAO_SENSOR_LUX / 5.0  # ~3,4 %


def test_tolerancia_vem_da_dispersao_quando_ela_supera_a_resolucao(conn, ponto):
    # 3 % de dispersao no pleno: 3 sigma = 9 %, acima do piso de resolucao.
    _sessao(conn, ponto, {0.6: [9.7, 10.0, 10.3]})
    t = tolerancia_do_ponto(conn, ponto.id)
    assert t == pytest.approx(config.K_SIGMA * 0.03, rel=0.05)
    assert t > PISO_RESOLUCAO


def test_bancada_perfeita_nao_zera_a_tolerancia(conn, ponto):
    # Achado da sessao 72: repeticoes identicas davam dispersao 0 %. A
    # tolerancia nao pode cair abaixo do que o sensor distingue.
    _sessao(conn, ponto, {0.57: [9.96, 9.96, 9.96], 0.30: [4.98, 4.98, 4.98]})
    assert tolerancia_do_ponto(conn, ponto.id) == pytest.approx(PISO_RESOLUCAO)


def test_pontos_abaixo_do_piso_nao_inflam_a_tolerancia(conn, ponto):
    # A 0,3 lx um degrau do sensor vale ~38 %: fora da faixa de operacao,
    # esse ponto nao pode definir a tolerancia (daria mais de 100 %).
    _sessao(conn, ponto, {0.03: [0.30, 0.30, 0.41], 0.57: [9.96, 9.96, 9.96]})
    assert tolerancia_do_ponto(conn, ponto.id) == pytest.approx(PISO_RESOLUCAO)


def test_so_a_sessao_mais_recente_conta(conn, ponto):
    from datetime import datetime, timedelta, timezone

    ontem = datetime.now(timezone.utc) - timedelta(days=1)
    _sessao(conn, ponto, {0.6: [8.0, 10.0, 12.0]}, quando=ontem)  # sessao antiga e ruim
    _sessao(conn, ponto, {0.6: [9.96, 9.96, 9.96]})               # recalibracao boa
    assert tolerancia_do_ponto(conn, ponto.id) == pytest.approx(PISO_RESOLUCAO)


def test_falha_total_induzida_abre_alerta_apos_tres_ciclos(conn, ponto):
    m = Monitor()
    agora = T0
    for i in range(1, 4):
        # Decisao pede 1,0 (10 lux); o no entrega a residual: ramo interrompido.
        d = ciclo_com_lux(conn, ponto, agora, lux=0.3)
        assert m.avaliar(conn, d.id) == "falha_total"
        n = conn.execute("SELECT count(*) FROM alerta_diagnostico").fetchone()[0]
        assert n == (1 if i == 3 else 0), f"ciclo {i}"
        agora += timedelta(seconds=5)
    estado = conn.execute(
        "SELECT estado_operacional FROM ponto_de_luz WHERE id = %s", (ponto.id,)
    ).fetchone()[0]
    assert estado == "falha"


def test_ponto_normalizado_encerra_o_alerta(conn, ponto):
    m = Monitor()
    agora = T0
    for _ in range(3):
        m.avaliar(conn, ciclo_com_lux(conn, ponto, agora, lux=0.0).id)
        agora += timedelta(seconds=5)
    # Volta a entregar o esperado (10 lux para nivel 1,0).
    assert m.avaliar(conn, ciclo_com_lux(conn, ponto, agora, lux=10.0).id) == "normal"
    aberto, estado = conn.execute(
        "SELECT (SELECT count(*) FROM alerta_diagnostico WHERE encerrado_em IS NULL),"
        "       (SELECT estado_operacional FROM ponto_de_luz WHERE id = %s)", (ponto.id,)
    ).fetchone()
    assert aberto == 0 and estado == "operante"


def test_perda_de_controle_exige_doze_ciclos(conn, ponto):
    m = Monitor()
    m.limiares[ponto.id] = LIM
    agora = T0
    for i in range(1, 13):
        d = ciclo_com_lux(conn, ponto, agora, lux=7.0)  # 30 % abaixo de 10
        assert m.avaliar(conn, d.id) == "divergente"
        n = conn.execute("SELECT count(*) FROM alerta_diagnostico").fetchone()[0]
        assert n == (1 if i == 12 else 0), f"ciclo {i}"
        agora += timedelta(seconds=5)
    tipo = conn.execute("SELECT tipo FROM alerta_diagnostico").fetchone()[0]
    assert tipo == "perda_controle"


def test_leitura_isolada_fora_da_tolerancia_nao_alerta(conn, ponto):
    m = Monitor()
    m.limiares[ponto.id] = LIM
    agora = T0
    for lux in (10.0, 7.0, 10.0, 7.0, 10.0):
        m.avaliar(conn, ciclo_com_lux(conn, ponto, agora, lux=lux).id)
        agora += timedelta(seconds=5)
    assert conn.execute("SELECT count(*) FROM alerta_diagnostico").fetchone()[0] == 0


def test_residual_da_sessao_e_descontada(conn, ponto):
    sid = conn.execute(
        "INSERT INTO sessao_medicao (ponto_de_luz_id, lux_residual, lux_classe)"
        " VALUES (%s, 0.4, 10) RETURNING id", (ponto.id,)
    ).fetchone()[0]
    m = Monitor()
    m.limiares[ponto.id] = LIM
    # 10,4 lx medidos - 0,4 de residual = 10,0 liquidos: exatamente o esperado.
    d = ciclo_com_lux(conn, ponto, T0, lux=10.4, sessao_id=sid)
    assert m.avaliar(conn, d.id) == "normal"


def test_sem_telemetria_nao_ha_diagnostico(conn, ponto):
    d = decidir(conn, ponto, T0)
    assert Monitor().avaliar(conn, d.id) is None
