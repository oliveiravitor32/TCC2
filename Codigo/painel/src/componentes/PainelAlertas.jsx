// Aba de alertas: tudo o que esta acontecendo agora, um cartao por situacao.
// Junta os alertas de diagnostico abertos (RF11) com o estado do no
// (sem comunicacao, falha, manutencao). Cores iguais as do mapa.

import { AlertTriangle, Wrench, WifiOff, ExternalLink, CheckCircle2 } from "lucide-react";
import { hora } from "./Dica";

const TIPOS = {
  falha_total: {
    titulo: "falha total", cor: "#facc15", icone: AlertTriangle,
    texto: "comando acima de zero e luz perto da residual: luminária apagada",
  },
  perda_controle: {
    titulo: "perda de controle", cor: "#facc15", icone: AlertTriangle,
    texto: "luz entregue fora da tolerância por ciclos seguidos",
  },
  falha: {
    titulo: "ponto em falha", cor: "#facc15", icone: AlertTriangle,
    texto: "marcado como em falha no cadastro",
  },
  sem_comunicacao: {
    titulo: "sem comunicação", cor: "#c62828", icone: WifiOff,
    texto: "o nó caiu do broker; sem comando, ele volta ao pleno sozinho (failsafe)",
  },
  manutencao: {
    titulo: "em manutenção", cor: "#6b7280", icone: Wrench,
    texto: "conferência ou calibração pela serial; o serviço não comanda este ponto",
  },
};
const ORDEM = ["sem_comunicacao", "falha_total", "perda_controle", "falha", "manutencao"];

export function listarAlertas(pontos, alertas) {
  const porCodigo = new Map(pontos.map((p) => [p.codigo, p]));
  const itens = alertas.map((a) => ({
    chave: `a${a.id}`, tipo: a.tipo, ponto: porCodigo.get(a.ponto) ?? { codigo: a.ponto }, desde: a.aberto_em,
    detalhe: `razão ${a.razao != null ? a.razao.toFixed(3) : "--"} · tolerância ${a.tolerancia ?? "--"} · ${a.ciclos ?? "--"} ciclos`,
  }));
  // 'falha' vinda de um alerta de falha total ja tem o cartao do alerta.
  const comAlerta = new Set(alertas.map((a) => a.ponto));
  for (const p of pontos) {
    if (p.estado_operacional === "falha" && comAlerta.has(p.codigo)) continue;
    if (["sem_comunicacao", "falha", "manutencao"].includes(p.estado_operacional)) {
      itens.push({ chave: `e${p.codigo}`, tipo: p.estado_operacional, ponto: p, desde: null, detalhe: null });
    }
  }
  return itens.sort((x, y) => ORDEM.indexOf(x.tipo) - ORDEM.indexOf(y.tipo) || x.ponto.codigo.localeCompare(y.ponto.codigo));
}

export default function PainelAlertas({ pontos, alertas, aoAbrirPonto }) {
  const itens = listarAlertas(pontos, alertas);
  if (!itens.length) {
    return (
      <section className="flex items-center gap-2 border border-borda bg-carta p-6 text-sm text-ok">
        <CheckCircle2 size={18} /> nenhum alerta no momento: todos os pontos comunicando e sem diagnóstico aberto
      </section>
    );
  }
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {itens.map((it) => {
        const t = TIPOS[it.tipo] ?? { titulo: it.tipo, cor: "#c62828", icone: AlertTriangle, texto: "" };
        const Icone = t.icone;
        const p = it.ponto;
        return (
          <article key={it.chave} className="flex flex-col border border-borda border-l-8 bg-carta p-4" style={{ borderLeftColor: t.cor }}>
            <div className="mb-1 flex items-center gap-2">
              <Icone size={16} style={{ color: t.cor === "#facc15" ? "#a16207" : t.cor }} />
              <h3 className="text-xs font-bold tracking-wide uppercase">{t.titulo}</h3>
            </div>
            <p className="text-sm font-semibold">{p.codigo}</p>
            <p className="mb-2 text-xs text-suave">
              {p.simulado === false ? "nó real" : p.simulado ? "simulado" : ""}
              {p.placa ? ` · poste ${p.placa}` : ""}
              {p.grupo_id != null ? ` · grupo ${p.grupo_id}` : ""}
            </p>
            <p className="text-xs">{t.texto}</p>
            {it.detalhe && <p className="mt-1 text-xs text-suave">{it.detalhe}</p>}
            {it.desde && <p className="mt-1 text-xs text-suave">desde {hora(it.desde)}</p>}
            <button type="button" onClick={() => aoAbrirPonto?.(p.codigo)}
              className="mt-auto inline-flex items-center gap-1 self-start pt-3 text-xs font-semibold uppercase tracking-wide text-luz hover:underline">
              <ExternalLink size={12} /> ver no monitoramento
            </button>
          </article>
        );
      })}
    </div>
  );
}
