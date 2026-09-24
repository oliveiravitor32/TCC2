// Cartoes do topo: a cadeia de uma decisao, da esquerda para a direita
// (RF08). E a leitura que o TCC pede em 4.6: o dado que entrou, o nivel que
// a inferencia pretendeu, a correcao que a verificacao impos e a luz que o
// no entregou.

import {
  Activity,
  AlertTriangle,
  Brain,
  CloudRain,
  Lightbulb,
  ShieldCheck,
  Sun,
} from "lucide-react";
import { RESTRICOES, lux, pct } from "../api";

export function Cartao({ icone: Icone, titulo, children, destaque }) {
  return (
    <section
      className={`rounded-xl border bg-carta p-4 ${
        destaque ? "border-luz/40" : "border-borda"
      }`}
    >
      <h2 className="mb-2 flex items-center gap-2 text-xs font-medium tracking-wide text-suave uppercase">
        <Icone size={14} aria-hidden="true" />
        {titulo}
      </h2>
      {children}
    </section>
  );
}

export function EstadoDaVia({ eventos }) {
  const ultimo = (tipo) => eventos.find((e) => e.tipo === tipo);
  const mov = ultimo("movimentacao");
  const met = ultimo("meteorologia");
  const oco = ultimo("ocorrencia");
  const adversa = met && ["chuva", "neblina", "nevoeiro"].includes(met.rotulo);
  const emOcorrencia = oco && oco.rotulo !== "encerrada";

  return (
    <Cartao icone={Activity} titulo="dado recebido da via">
      <p className="text-3xl font-semibold tabular-nums">
        {mov ? pct(mov.valor) : "--"}
      </p>
      <p className="text-xs text-suave">movimentação normalizada no ponto</p>
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        <span
          className={`inline-flex items-center gap-1 rounded-md px-2 py-1 ${
            adversa ? "bg-meteo/15 text-meteo" : "bg-borda/40 text-suave"
          }`}
        >
          {adversa ? <CloudRain size={12} /> : <Sun size={12} />}
          {met ? met.rotulo : "sem dado"}
        </span>
        <span
          className={`inline-flex items-center gap-1 rounded-md px-2 py-1 ${
            emOcorrencia ? "bg-falha/15 text-falha" : "bg-borda/40 text-suave"
          }`}
        >
          <AlertTriangle size={12} />
          {emOcorrencia ? `ocorrência: ${oco.rotulo}` : "sem ocorrência"}
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

export function Entregue({ ponto, latenciaMs }) {
  const razao =
    ponto?.lux_medido != null && ponto?.nivel_emitido
      ? ponto.lux_medido / (ponto.nivel_emitido * ponto.lux_pleno)
      : null;
  return (
    <Cartao icone={Lightbulb} titulo="luz entregue">
      <p className="text-3xl font-semibold tabular-nums text-luz">
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
      </dl>
    </Cartao>
  );
}
