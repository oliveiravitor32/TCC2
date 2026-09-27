// Listas de apoio: cadeia de auditoria (decisoes), eventos recebidos e
// alertas de diagnostico (RF11). Sao elas que tornam a execucao
// inspecionavel decisao a decisao, como o TCC promete em 4.7.1.

import { AlertOctagon, Radio, ScrollText } from "lucide-react";
import { Cartao } from "./Cartoes";
import { RESTRICOES, hora, lux, pct } from "../api";

export function Decisoes({ decisoes, telemetria }) {
  const porDecisao = new Map(telemetria.map((t) => [t.decisao_id, t]));
  return (
    <Cartao icone={ScrollText} titulo="registro de decisões">
      <div className="max-h-72 overflow-y-auto">
        <table className="w-full text-left text-xs tabular-nums">
          <thead className="sticky top-0 bg-carta text-suave">
            <tr>
              <th className="py-1 font-medium">hora</th>
              <th className="py-1 font-medium">pretendido</th>
              <th className="py-1 font-medium">emitido</th>
              <th className="py-1 font-medium">correção</th>
              <th className="py-1 font-medium">lux</th>
            </tr>
          </thead>
          <tbody>
            {decisoes.slice(0, 60).map((d) => {
              const r = RESTRICOES[d.restricao_aplicada];
              const t = porDecisao.get(d.id);
              return (
                <tr key={d.id} className="border-t border-borda/60">
                  <td className="py-1 text-suave">{hora(d.criado_em)}</td>
                  <td className="py-1">{d.nivel_pretendido.toFixed(3)}</td>
                  <td className="py-1 font-medium">{d.nivel_emitido.toFixed(3)}</td>
                  <td className={`py-1 ${r.cor}`}>{r.texto}</td>
                  <td className="py-1 text-suave">
                    {t ? lux(t.lux_medido, 1) : "--"}
                  </td>
                </tr>
              );
            })}
            {decisoes.length === 0 && (
              <tr>
                <td colSpan={5} className="py-3 text-center text-suave">
                  nenhuma decisão no período
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Cartao>
  );
}

export function Eventos({ eventos }) {
  return (
    <Cartao icone={Radio} titulo="eventos urbanos recebidos">
      <ul className="max-h-72 space-y-1 overflow-y-auto text-xs">
        {eventos.slice(0, 40).map((e) => (
          <li key={e.id} className="flex items-baseline gap-2 border-t border-borda/60 py-1">
            <span className="text-suave tabular-nums">{hora(e.ocorrido_em)}</span>
            <span className="font-medium">{e.tipo}</span>
            <span className="text-suave">
              {e.tipo === "movimentacao" ? pct(e.valor) : e.rotulo}
            </span>
            <span className="ml-auto text-suave">trecho {e.trecho} · {e.origem}</span>
          </li>
        ))}
        {eventos.length === 0 && (
          <li className="py-3 text-center text-suave">nenhum evento publicado ainda</li>
        )}
      </ul>
    </Cartao>
  );
}

export function Alertas({ alertas }) {
  const rotulo = {
    falha_total: "falha total: luminária apagada",
    perda_controle: "perda de controle: entrega fora da tolerância",
  };
  return (
    <Cartao icone={AlertOctagon} titulo="diagnóstico do ponto de luz">
      {alertas.length === 0 ? (
        <p className="py-2 text-xs text-ok">nenhum alerta aberto</p>
      ) : (
        <ul className="space-y-2 text-xs">
          {alertas.map((a) => (
            <li key={a.id} className="rounded-md bg-falha/10 p-2 text-falha">
              <p className="font-medium">{rotulo[a.tipo] ?? a.tipo}</p>
              <p className="text-suave">
                {a.ponto} · desde {hora(a.aberto_em)} · razão{" "}
                {a.razao != null ? a.razao.toFixed(3) : "--"} · tolerância{" "}
                {a.tolerancia != null ? pct(a.tolerancia) : "--"} · {a.ciclos} ciclos
              </p>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-[11px] text-suave">
        o alerta registra e marca o ponto; quem protege a via contra falta de comando é
        o failsafe do nó (RNF07)
      </p>
    </Cartao>
  );
}
