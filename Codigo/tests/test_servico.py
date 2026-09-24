"""Servico de decisao: a decisao precisa estar CONFIRMADA antes da
publicacao, senao a telemetria do no (outra conexao) nao a encontra.

Regressao do teste ponta a ponta do passo 5, em que o `transaction()` do
psycopg, numa conexao sem autocommit, virou savepoint e nada foi gravado.
"""

from __future__ import annotations

import psycopg
import pytest

from decisao import config

try:
    psycopg.connect(config.DATABASE_URL, connect_timeout=2).close()
except psycopg.OperationalError:
    pytest.skip("Postgres indisponivel (docker compose up -d db)", allow_module_level=True)

from decisao.servico import Servico  # noqa: E402


def test_decisao_do_passo_fica_visivel_para_outra_conexao():
    s = Servico()
    outra = psycopg.connect(config.DATABASE_URL, autocommit=True)
    try:
        # Pelo relogio REAL: a suite de cenarios grava decisoes com carimbos
        # no futuro virtual, e um max(criado_em) global nunca seria superado.
        s.passo()  # broker desconectado: publica falha, mas a decisao e gravada
        novas = outra.execute(
            "SELECT id FROM decisao WHERE execucao_id IS NULL"
            "   AND criado_em > now() - interval '2 minutes'"
        ).fetchall()
        assert len(novas) >= 1
    finally:
        ids = [r[0] for r in novas] if "novas" in locals() else []
        if ids:
            outra.execute("DELETE FROM decisao_evento WHERE decisao_id = ANY(%s)", (ids,))
            outra.execute("DELETE FROM decisao WHERE id = ANY(%s)", (ids,))
        outra.close()
        s.db_ciclo.close()
        s.db_retorno.close()
