"""O que se perde ao retirar o sistema de regras (DIVERGENCIAS 58).

    python -m cenarios.avaliacao_ia.deficit

Retirar as regras = voltar a programacao agendada (horario fixo, linha de base
2 de 3.11), que atenua das 0h as 5h locais sem saber o que ocorre na via.
Para cada ciclo, o nivel que a situacao pede:
  - classe da via (1,0 na P3) com ocorrencia aberta ou volume observado alto;
  - uma classe abaixo (0,75) com volume medio;
  - sem exigencia acima do piso com volume baixo ou sem dado.
O mapeamento volume -> classe e o criterio declarado dos autores (tercis por
trecho, 3.7); a norma nao da numeros (6.3). Conta-se, para o horario fixo e
para o sistema adaptativo, os minutos abaixo do nivel pedido (margem 0,02) e o
deficit medio nesses minutos, em fracao do pleno e em lux da P3.

Le os relatorios gerados com --serie (que trazem 'inicio' e a serie por ciclo).
"""

from __future__ import annotations

import json
from datetime import datetime, time, timedelta
from pathlib import Path

import psycopg

from cenarios.executar import HORA_FIM_ATENUACAO, HORA_INICIO_ATENUACAO
from decisao import ciclo, config
from decisao.energia import trajetoria_horario_fixo
from decisao.inferencia import carregar

RES = Path(__file__).resolve().parent.parent / "resultados"
MARGEM = 0.02
ARQUIVOS = {"suite": "suite_antecipado.json", "noites": "avaliacao_ia_zurique_antecipado.json"}  # item 69


def main() -> None:
    base = carregar(config.REGRAS)
    f1 = (base.mov["baixa"][2] + base.mov["baixa"][3]) / 2
    f2 = (base.mov["alta"][0] + base.mov["alta"][1]) / 2
    with psycopg.connect(config.DATABASE_URL, connect_timeout=5) as conn:
        piso = float(ciclo.criterio(conn, "P3").piso)
        lux = float(conn.execute(
            "SELECT iluminancia_media_min_lux FROM classe_iluminacao WHERE codigo = 'P3'").fetchone()[0])
    saida = {}
    for grupo, arq in ARQUIVOS.items():
        d = json.loads((RES / arq).read_text(encoding="utf-8"))
        tot = {"fixo": {"min": 0.0, "soma": 0.0}, "adaptativo": {"min": 0.0, "soma": 0.0},
               "min_com_exigencia": 0.0, "min_ocorrencia_fixo": 0.0}
        por = {}
        for r in d["relatorios"]:
            if "serie" not in r:
                raise SystemExit(f"{arq} sem serie: rode o executor com --serie")
            serie = r["serie"]
            inicio = datetime.fromisoformat(r["inicio"])
            fixo = trajetoria_horario_fixo(
                inicio, inicio + timedelta(seconds=config.PERIODO_S * len(serie)), piso,
                hora_inicio_atenuacao=HORA_INICIO_ATENUACAO, hora_fim_atenuacao=HORA_FIM_ATENUACAO,
                passo_s=config.PERIODO_S, fuso=config.FUSO,
            )
            c = {"fixo": [0, 0.0], "adaptativo": [0, 0.0], "exig": 0, "oco_fixo": 0}
            for x, (_, _, nf) in zip(serie, fixo):
                obs = x["observada"]
                if x["ocorrencia"] or (obs is not None and obs >= f2):
                    pede = 1.0
                elif obs is not None and obs >= f1:
                    pede = 0.75
                else:
                    continue
                c["exig"] += 1
                for nome, nivel in (("fixo", nf), ("adaptativo", x["emitido"])):
                    if nivel < pede - MARGEM:
                        c[nome][0] += 1
                        c[nome][1] += pede - nivel
                        if nome == "fixo" and x["ocorrencia"]:
                            c["oco_fixo"] += 1
            passo_min = config.PERIODO_S / 60
            por[r["cenario"]] = {
                "min_com_exigencia": round(c["exig"] * passo_min, 1),
                "fixo_min_abaixo": round(c["fixo"][0] * passo_min, 1),
                "adaptativo_min_abaixo": round(c["adaptativo"][0] * passo_min, 1),
                "fixo_min_abaixo_com_ocorrencia": round(c["oco_fixo"] * passo_min, 1),
            }
            for nome in ("fixo", "adaptativo"):
                tot[nome]["min"] += c[nome][0] * passo_min
                tot[nome]["soma"] += c[nome][1]
            tot["min_com_exigencia"] += c["exig"] * passo_min
            tot["min_ocorrencia_fixo"] += c["oco_fixo"] * passo_min
        resumo = {"min_com_exigencia": round(tot["min_com_exigencia"], 1),
                  "fixo_min_abaixo_com_ocorrencia": round(tot["min_ocorrencia_fixo"], 1)}
        for nome in ("fixo", "adaptativo"):
            n = tot[nome]["min"] / (config.PERIODO_S / 60)
            resumo[f"{nome}_min_abaixo"] = round(tot[nome]["min"], 1)
            resumo[f"{nome}_deficit_medio_fracao"] = round(tot[nome]["soma"] / n, 3) if n else 0.0
            resumo[f"{nome}_deficit_medio_lux"] = round(tot[nome]["soma"] / n * lux, 2) if n else 0.0
        saida[grupo] = {"resumo": resumo, "por_cenario": por}
    (RES / "avaliacao_ia_deficit.json").write_text(json.dumps(saida, indent=2, ensure_ascii=False) + "\n",
                                                   encoding="utf-8")
    print(json.dumps(saida, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
