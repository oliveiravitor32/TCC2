"""Interface de dados urbanos (TCC 3.2, 4.6.1, Quadro 14).

Emula a interface de programacao que a plataforma municipal precisaria
publicar. Recebe e disponibiliza eventos (RF01) e expoe o historico de
decisoes e de telemetria para o painel (RF08).

Execucao local:  uvicorn api_eventos.app:app --reload
Banco: variavel DATABASE_URL (padrao: Postgres do docker-compose).
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import asynccontextmanager
from datetime import datetime

import psycopg
from fastapi import Depends, FastAPI, Query, status
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .esquemas import Decisao, Evento, EventoEntrada, Telemetria, Tipo

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://iluminacao:iluminacao@localhost:5432/iluminacao"
)
LIMITE_MAX = 5000

_pool: ConnectionPool | None = None


@asynccontextmanager
async def _ciclo_de_vida(_: FastAPI):
    global _pool
    _pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=5, open=True)
    try:
        yield
    finally:
        _pool.close()


app = FastAPI(
    title="Interface de dados urbanos",
    description="Emulacao da interface da plataforma municipal (TCC 4.6.2, Quadro 14).",
    version="0.1.0",
    lifespan=_ciclo_de_vida,
)


def conexao() -> Iterator[psycopg.Connection]:
    """Uma transacao por requisicao: confirma no sucesso, desfaz no erro."""
    assert _pool is not None, "pool nao inicializado"
    with _pool.connection() as conn:
        conn.row_factory = dict_row
        yield conn


Conn = Depends(conexao)


# ---------------------------------------------------------------------------
# Eventos
# ---------------------------------------------------------------------------
@app.post("/eventos", response_model=Evento, status_code=status.HTTP_201_CREATED)
def publicar_evento(evento: EventoEntrada, conn: psycopg.Connection = Conn) -> dict:
    return conn.execute(
        """
        INSERT INTO evento_urbano
            (ocorrido_em, tipo, valor, rotulo, abrangencia, origem, vigente_ate)
        VALUES (%(ocorrido_em)s, %(tipo)s, %(valor)s, %(rotulo)s,
                %(abrangencia)s, %(origem)s, %(vigente_ate)s)
        RETURNING *
        """,
        evento.model_dump(),
    ).fetchone()


@app.get("/eventos", response_model=list[Evento])
def consultar_eventos(
    inicio: datetime | None = None,
    fim: datetime | None = None,
    tipo: Tipo | None = None,
    limite: int = Query(500, ge=1, le=LIMITE_MAX),
    conn: psycopg.Connection = Conn,
) -> list[dict]:
    return conn.execute(
        """
        SELECT * FROM evento_urbano
         WHERE (%(inicio)s::timestamptz IS NULL OR ocorrido_em >= %(inicio)s)
           AND (%(fim)s::timestamptz    IS NULL OR ocorrido_em <  %(fim)s)
           AND (%(tipo)s::text          IS NULL OR tipo = %(tipo)s)
         ORDER BY ocorrido_em DESC, id DESC
         LIMIT %(limite)s
        """,
        {"inicio": inicio, "fim": fim, "tipo": tipo, "limite": limite},
    ).fetchall()


# ---------------------------------------------------------------------------
# Decisoes e telemetria (leitura, para o painel)
# ---------------------------------------------------------------------------
@app.get("/decisoes", response_model=list[Decisao])
def consultar_decisoes(
    ponto: str | None = None,
    inicio: datetime | None = None,
    fim: datetime | None = None,
    execucao_id: int | None = None,
    limite: int = Query(500, ge=1, le=LIMITE_MAX),
    conn: psycopg.Connection = Conn,
) -> list[dict]:
    return conn.execute(
        """
        SELECT d.id, d.criado_em, p.codigo AS ponto, d.classe_codigo,
               d.nivel_pretendido, d.nivel_emitido, d.restricao_aplicada,
               d.nivel_anterior, d.previsao_movimentacao,
               r.rotulo AS versao_base_regras, m.rotulo AS versao_modelo,
               d.execucao_id,
               COALESCE(array_agg(de.evento_id ORDER BY de.evento_id)
                        FILTER (WHERE de.evento_id IS NOT NULL), '{}') AS evento_ids
          FROM decisao d
          JOIN ponto_de_luz p            ON p.id = d.ponto_de_luz_id
          JOIN versao_base_regras r      ON r.id = d.versao_base_regras_id
          JOIN versao_modelo_previsao m  ON m.id = d.versao_modelo_id
          LEFT JOIN decisao_evento de    ON de.decisao_id = d.id
         WHERE (%(ponto)s::text           IS NULL OR p.codigo = %(ponto)s)
           AND (%(inicio)s::timestamptz   IS NULL OR d.criado_em >= %(inicio)s)
           AND (%(fim)s::timestamptz      IS NULL OR d.criado_em <  %(fim)s)
           AND (%(execucao_id)s::bigint   IS NULL OR d.execucao_id = %(execucao_id)s)
         GROUP BY d.id, p.codigo, r.rotulo, m.rotulo
         ORDER BY d.criado_em DESC
         LIMIT %(limite)s
        """,
        {"ponto": ponto, "inicio": inicio, "fim": fim, "execucao_id": execucao_id, "limite": limite},
    ).fetchall()


@app.get("/telemetria", response_model=list[Telemetria])
def consultar_telemetria(
    ponto: str | None = None,
    inicio: datetime | None = None,
    fim: datetime | None = None,
    limite: int = Query(500, ge=1, le=LIMITE_MAX),
    conn: psycopg.Connection = Conn,
) -> list[dict]:
    return conn.execute(
        """
        SELECT t.decisao_id, p.codigo AS ponto, t.medido_em, t.recebido_em,
               t.duty, t.lux_medido
          FROM telemetria t
          JOIN ponto_de_luz p ON p.id = t.ponto_de_luz_id
         WHERE (%(ponto)s::text         IS NULL OR p.codigo = %(ponto)s)
           AND (%(inicio)s::timestamptz IS NULL OR t.medido_em >= %(inicio)s)
           AND (%(fim)s::timestamptz    IS NULL OR t.medido_em <  %(fim)s)
         ORDER BY t.medido_em DESC
         LIMIT %(limite)s
        """,
        {"ponto": ponto, "inicio": inicio, "fim": fim, "limite": limite},
    ).fetchall()
