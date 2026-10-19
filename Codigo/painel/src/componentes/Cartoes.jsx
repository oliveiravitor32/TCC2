// Cartoes do topo: a cadeia de uma decisao, da esquerda para a direita
// (RF08). E a leitura que o TCC pede em 4.6: o dado que entrou, o nivel que
// a inferencia pretendeu, a correcao que a verificacao impos e a luz que o
// no entregou.

import {
  Activity,
  AlertTriangle,
  Brain,
  Lightbulb,
  ShieldCheck,
} from "lucide-react";
import { OCORRENCIAS, RESTRICOES, lux, pct } from "../api";

export function Cartao({ icone: Icone, titulo, children, destaque }) {
  return (
    <section
      className={`border bg-carta p-4 ${
        destaque ? "border-luz" : "border-borda"
      }`}
    >
      <h2 className="mb-2 flex items-center gap-2 border-l-4 border-luz pl-2 text-xs font-bold tracking-wide text-luz uppercase">
        <Icone size={14} aria-hidden="true" />
        {titulo}
      </h2>
      {children}
    </section>
  );
}

export function EstadoDaVia({ eventos }) {
  // Publicacao mais recente de cada trecho do ponto, por tipo (DIVERGENCIAS
  // 54 e 56): o volume de 5 min e a ocorrencia ('encerrada' fecha).
  const volumes = new Map();
  const ocorrencias = new Map();
  for (const e of eventos) {
    const alvo = e.tipo === "ocorrencia" ? ocorrencias : volumes;
    if (!alvo.has(e.trecho)) alvo.set(e.trecho, e);
  }
  const vols = [...volumes.values()];
  const maior = vols.reduce((m, e) => Math.max(m, Number(e.pessoas_media)), 0);
  const oco = [...ocorrencias.values()].find((e) => e.ocorrencia !== "encerrada");

  return (
    <Cartao icone={Activity} titulo="volume recebido da via">
      <p className="text-3xl font-semibold tabular-nums">
        {vols.length ? maior.toLocaleString("pt-BR", { maximumFractionDigits: 1 }) : "--"}
      </p>
      <p className="text-xs text-suave">
        {vols.length
          ? `pessoas em média (5 min) · maior de ${vols.length} trecho${vols.length > 1 ? "s" : ""}`
          : "nenhum volume ainda"}
      </p>
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        <span
          className={`inline-flex items-center gap-1 rounded-md px-2 py-1 ${
            oco ? "bg-falha/15 text-falha" : "bg-borda/40 text-suave"
          }`}
        >
          <AlertTriangle size={12} />
          {oco ? `ocorrência: ${OCORRENCIAS[oco.ocorrencia]}` : "sem ocorrência"}
        </span>
      </div>
    </Cartao>
  );
}

export function Inferencia({ decisao }) {
  return (
    <Cartao icone={Brain} titulo="nível pretendido">
      <p className="text-3xl font-semibold tabular-nums">
        {decisao ? decisao.nivel_pretendido.toFixed(3) : "--"}
      </p>
      <p className="text-xs text-suave">inferência nebulosa, fração do fluxo pleno</p>
      <dl className="mt-3 space-y-1 text-xs text-suave">
        <div className="flex justify-between gap-2">
          <dt>previsão da próxima janela</dt>
          <dd className="tabular-nums text-texto">
            {decisao?.previsao_movimentacao != null
              ? pct(decisao.previsao_movimentacao)
              : "reativo"}
          </dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt>base de regras</dt>
          <dd className="text-texto">{decisao?.versao_base_regras ?? "--"}</dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt>modelo</dt>
          <dd className="text-texto">{decisao?.versao_modelo ?? "--"}</dd>
        </div>
      </dl>
    </Cartao>
  );
}

export function Verificacao({ decisao, piso }) {
  const r = RESTRICOES[decisao?.restricao_aplicada ?? "nenhuma"];
  const corrigiu = decisao && decisao.restricao_aplicada !== "nenhuma";
  return (
    <Cartao icone={ShieldCheck} titulo="verificação normativa" destaque={corrigiu}>
      <p className="text-3xl font-semibold tabular-nums">
        {decisao ? decisao.nivel_emitido.toFixed(3) : "--"}
      </p>
      <p className="text-xs text-suave">nível emitido ao nó</p>
      <div className={`mt-3 inline-flex rounded-md px-2 py-1 text-xs ${r.fundo} ${r.cor}`}>
        {corrigiu ? `corrigido: ${r.texto}` : r.texto}
      </div>
      {corrigiu && (
        <p className="mt-2 text-xs text-suave">
          a inferência pediu {decisao.nivel_pretendido.toFixed(3)}; a norma não admitiu
        </p>
      )}
      {!corrigiu && piso != null && (
        <p className="mt-2 text-xs text-suave">piso da classe: {piso.toFixed(3)}</p>
      )}
    </Cartao>
  );
}

// Hora local (com segundos) e ha quanto tempo: mostra se o no esta conversando.
function quando(iso) {
  if (!iso) return "--";
  const t = new Date(iso);
  const s = Math.max(0, Math.round((Date.now() - t) / 1000));
  const ha = s < 60 ? `${s} s` : s < 3600 ? `${Math.round(s / 60)} min`
    : s < 86400 ? `${Math.round(s / 3600)} h` : `${Math.round(s / 86400)} d`;
  const dia = s >= 86400 ? `${t.toLocaleDateString("pt-BR")} ` : "";
  return `${dia}${t.toLocaleTimeString("pt-BR")} · há ${ha}`;
}

export function Entregue({ ponto, latenciaMs, ultimoComando, ultimaResposta }) {
  const razao =
    ponto?.lux_medido != null && ponto?.nivel_emitido
      ? ponto.lux_medido / (ponto.nivel_emitido * ponto.lux_pleno)
      : null;
  return (
    <Cartao icone={Lightbulb} titulo="luz entregue">
      <p className="text-3xl font-extrabold tabular-nums text-luz">
        {lux(ponto?.lux_medido)}
      </p>
      <p className="text-xs text-suave">
        medida pelo sensor; esperado{" "}
        {ponto?.nivel_emitido != null
          ? lux(ponto.nivel_emitido * ponto.lux_pleno)
          : "--"}
      </p>
      <dl className="mt-3 space-y-1 text-xs text-suave">
        <div className="flex justify-between gap-2">
          <dt>ciclo de trabalho</dt>
          <dd className="tabular-nums text-texto">
            {ponto?.duty != null ? pct(ponto.duty) : "--"}
          </dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt>antes do comando</dt>
          <dd className="tabular-nums text-texto">
            {ponto?.nivel_antes != null
              ? `${ponto.nivel_antes.toFixed(3)} · ${lux(ponto.lux_antes)}`
              : "--"}
          </dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt>entregue / esperado</dt>
          <dd className="tabular-nums text-texto">
            {razao ? razao.toFixed(3) : "--"}
          </dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt>decisão até medição</dt>
          <dd className="tabular-nums text-texto">
            {latenciaMs != null ? `${latenciaMs} ms` : "--"}
          </dd>
        </div>
        <div className="flex justify-between gap-2 border-t border-borda pt-1">
          <dt>último comando enviado</dt>
          <dd className="tabular-nums text-texto">{quando(ultimoComando)}</dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt>última resposta do nó</dt>
          <dd className="tabular-nums text-texto">{quando(ultimaResposta)}</dd>
        </div>
      </dl>
    </Cartao>
  );
}
