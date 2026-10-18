"""Grupos de controle (3.12.6.4, DIVERGENCIAS 76).

Um grupo reune os pontos de luz associados EXATAMENTE aos mesmos trechos e da
mesma classe. Como cada ponto ja decide pelo maior volume e por qualquer
ocorrencia dos seus trechos, pontos do mesmo grupo sempre recebem a mesma
decisao: agrupar so evita calcular a mesma coisa varias vezes, sem mudar
nenhum nivel. Cada ponto fica em um unico grupo, e a decisao de um grupo le
so os seus trechos, nunca o nivel de outro grupo (sem cascata).

Recalcular quando o cadastro mudar (ponto novo, nova associacao):
    python -m decisao.grupos
"""

from __future__ import annotations

import psycopg

from . import config


def chave(classe: str, trechos: list[int]) -> str:
    return classe + ":" + ",".join(str(t) for t in sorted(trechos))


def recalcular(conn: psycopg.Connection) -> int:
    """Refaz a associacao ponto -> grupo a partir de trecho_ponto. Idempotente:
    recalcular de novo da os mesmos grupos. Devolve quantos grupos ha em uso."""
    linhas = conn.execute(
        """
        SELECT p.id, p.classe_codigo,
               COALESCE(array_agg(tp.trecho_id ORDER BY tp.trecho_id)
                        FILTER (WHERE tp.trecho_id IS NOT NULL), '{}') AS trechos
        FROM ponto_de_luz p LEFT JOIN trecho_ponto tp ON tp.ponto_de_luz_id = p.id
        GROUP BY p.id, p.classe_codigo
        """
    ).fetchall()
    usados: set[int] = set()
    for pid, classe, trechos in linhas:
        k = chave(classe, list(trechos))
        gid = conn.execute(
            """
            INSERT INTO grupo_controle (chave, classe_codigo, trechos) VALUES (%s, %s, %s)
            ON CONFLICT (chave) DO UPDATE SET chave = EXCLUDED.chave
            RETURNING id
            """,
            (k, classe, sorted(trechos)),
        ).fetchone()[0]
        conn.execute("UPDATE ponto_de_luz SET grupo_id = %s WHERE id = %s", (gid, pid))
        usados.add(gid)
    return len(usados)


def main() -> None:
    with psycopg.connect(config.DATABASE_URL) as conn:
        n = recalcular(conn)
        conn.commit()
    print(f"{n} grupos de controle em uso")


if __name__ == "__main__":
    main()
