"""Gravacao das sessoes de medicao da bancada (3.4.3, 3.4.4).

Usado por dois caminhos com o mesmo SQL: os scripts da bancada falando com o
banco local (bancada/conferir.py, bancada/calibrar.py) e a API da VM
(POST /bancada/sessoes e POST /bancada/calibracoes), quando o no esta ligado
a VM e a sessao precisa ficar no banco que recebe a telemetria.

A iluminancia da classe e lida do banco, nunca recebida do cliente: o valor
congelado na sessao e o da tabela classe_iluminacao (RF09).
"""

from __future__ import annotations

import psycopg

__all__ = ["PontoNaoCadastrado", "registrar_conferencia", "registrar_calibracao"]


class PontoNaoCadastrado(LookupError):
    pass


def _ponto(conn: psycopg.Connection, codigo: str) -> tuple[int, float]:
    linha = conn.execute(
        "SELECT p.id, c.iluminancia_media_min_lux FROM ponto_de_luz p"
        " JOIN classe_iluminacao c ON c.codigo = p.classe_codigo WHERE p.codigo = %s",
        (codigo,),
    ).fetchone()
    if linha is None:
        raise PontoNaoCadastrado(codigo)
    if isinstance(linha, dict):
        return linha["id"], float(linha["iluminancia_media_min_lux"])
    return linha[0], float(linha[1])


def _primeiro(linha) -> object:
    return next(iter(linha.values())) if isinstance(linha, dict) else linha[0]


def registrar_conferencia(conn: psycopg.Connection, ponto: str, lux_residual: float,
                          aprovada: bool, observacao: str) -> tuple[int, bool]:
    """Sessao da conferencia; devolve (id, descartada).

    Aprovada: fica ABERTA e as anteriores do ponto sao encerradas, de modo que
    a telemetria seguinte e descontada desta residual (ciclo.registrar_telemetria).
    Reprovada: e encerrada na hora, so como registro.
    """
    pid, lux_classe = _ponto(conn, ponto)
    with conn.transaction():
        if aprovada:
            conn.execute(
                "UPDATE sessao_medicao SET encerrada_em = now()"
                " WHERE ponto_de_luz_id = %s AND encerrada_em IS NULL",
                (pid,),
            )
        linha = conn.execute(
            "INSERT INTO sessao_medicao (ponto_de_luz_id, lux_residual, lux_classe, observacao,"
            " encerrada_em) VALUES (%s, %s, %s, %s, CASE WHEN %s THEN NULL ELSE now() END)"
            " RETURNING id, descartada",
            (pid, round(lux_residual, 2), lux_classe, observacao, aprovada),
        ).fetchone()
    if isinstance(linha, dict):
        return linha["id"], linha["descartada"]
    return linha[0], linha[1]


def registrar_calibracao(conn: psycopg.Connection, ponto: str, lux_residual: float,
                         linhas: list[tuple[int, float, float]], observacao: str,
                         potencia_plena_w: float | None = None) -> int:
    """Sessao de calibracao encerrada, com as linhas (serie, duty 0-1, lux medido).

    Repeticoes no mesmo duty e serie de uma varredura sao ignoradas (a chave
    da tabela calibracao), como na gravacao original do calibrar.py.
    """
    pid, lux_classe = _ponto(conn, ponto)
    with conn.transaction():
        sid = _primeiro(conn.execute(
            "INSERT INTO sessao_medicao (ponto_de_luz_id, lux_residual, lux_classe, observacao)"
            " VALUES (%s, %s, %s, %s) RETURNING id",
            (pid, round(lux_residual, 2), lux_classe, observacao),
        ).fetchone())
        for serie, duty, lux in linhas:
            conn.execute(
                "INSERT INTO calibracao (sessao_id, serie, duty, lux_medido)"
                " VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (sid, serie, duty, lux),
            )
        if potencia_plena_w:
            conn.execute("UPDATE ponto_de_luz SET potencia_plena_w = %s WHERE id = %s",
                         (potencia_plena_w, pid))
        conn.execute("UPDATE sessao_medicao SET encerrada_em = now() WHERE id = %s", (sid,))
    return sid
