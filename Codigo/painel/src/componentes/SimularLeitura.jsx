// Modal de demonstracao: publica a LEITURA de um trecho como a plataforma de
// monitoramento publicaria (DIVERGENCIAS 55) - quantas pessoas ha na area,
// se ha ocorrencia e onde. Uma chamada so (POST /eventos). O painel continua
// sem decidir nada: quem decide e o servico, e a aba "decisões explicadas"
// mostra por que.

import { useMemo, useState } from "react";
import { Minus, Plus, Send, X } from "lucide-react";
import { api } from "../api";

const RAPIDOS = [
  { rotulo: "via vazia", pessoas: 0 },
  { rotulo: "1 pessoa", pessoas: 1 },
  { rotulo: "2 pessoas", pessoas: 2 },
  { rotulo: "grupo (8)", pessoas: 8 },
];

const VIGENCIAS = [
  { rotulo: "1 min (como a plataforma, que republica a cada poucos segundos)", min: 1 },
  { rotulo: "10 min", min: 10 },
  { rotulo: "30 min", min: 30 },
];

function nomeTrecho(t) {
  const faixa =
    t.numero_inicial != null && t.numero_final != null ? ` ${t.numero_inicial}–${t.numero_final}` : "";
  const pontos = t.pontos.length ? ` · ${t.pontos.join(", ")}` : " · sem luminária no sistema";
  return `${[t.tipo_logradouro, t.nome_logradouro].filter(Boolean).join(" ")}${faixa}${pontos}`;
}

// Montado so quando aberto: cada abertura nasce do trecho do ponto na tela.
export default function SimularLeitura({ fechar, trechos, trechoInicial, aoPublicar }) {
  const [trecho, setTrecho] = useState(trechoInicial ?? trechos[0]?.id ?? "");
  const [pessoas, setPessoas] = useState(0);
  const [ocorrencia, setOcorrencia] = useState(null);
  const [vigencia, setVigencia] = useState(10);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  const ordenados = useMemo(
    () => [...trechos].sort((a, b) => b.pontos.length - a.pontos.length || a.nome_logradouro.localeCompare(b.nome_logradouro)),
    [trechos],
  );

  async function publicar() {
    setEnviando(true);
    setErro(null);
    const agora = new Date();
    try {
      const evento = await api.publicarLeitura({
        ocorrido_em: agora.toISOString(),
        pessoas,
        ocorrencia,
        trecho: Number(trecho),
        origem: "painel-demonstracao",
        vigente_ate: new Date(agora.getTime() + vigencia * 60_000).toISOString(),
      });
      aoPublicar(evento);
      fechar();
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="titulo-simular"
      onClick={fechar}
    >
      <div
        className="w-full max-w-lg rounded-xl border border-borda bg-carta p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 id="titulo-simular" className="text-base font-semibold">
              Simular leitura da plataforma
            </h2>
            <p className="text-xs text-suave">
              O que o Smart Sampa enviaria: pessoas na área do trecho, ocorrência e local.
            </p>
          </div>
          <button type="button" onClick={fechar} className="rounded-md p-1 text-suave hover:bg-borda/40" aria-label="fechar">
            <X size={16} />
          </button>
        </div>

        {!api.podePublicar && (
          <p className="mb-3 rounded-md bg-falha/10 p-2 text-xs text-falha">
            Este painel foi publicado sem VITE_CHAVE_DEMO: a API vai recusar o envio.
          </p>
        )}

        <label className="mb-4 block text-xs text-suave">
          local (trecho de via)
          <select
            value={trecho}
            onChange={(e) => setTrecho(e.target.value)}
            className="mt-1 w-full rounded-md border border-borda bg-fundo px-2 py-2 text-sm text-texto"
          >
            {ordenados.map((t) => (
              <option key={t.id} value={t.id}>
                {nomeTrecho(t)}
              </option>
            ))}
          </select>
        </label>

        <fieldset className="mb-4">
          <legend className="mb-1 text-xs text-suave">pessoas na área agora</legend>
          <div className="flex items-center gap-2">
            <button type="button" onClick={() => setPessoas((n) => Math.max(0, n - 1))}
              className="rounded-md border border-borda p-2 hover:bg-borda/40" aria-label="menos uma pessoa">
              <Minus size={14} />
            </button>
            <input
              type="number" min={0} max={10000} value={pessoas}
              onChange={(e) => setPessoas(Math.max(0, Math.min(10000, Number(e.target.value) || 0)))}
              className="w-20 rounded-md border border-borda bg-fundo px-2 py-2 text-center text-lg tabular-nums text-texto"
              aria-label="pessoas"
            />
            <button type="button" onClick={() => setPessoas((n) => n + 1)}
              className="rounded-md border border-borda p-2 hover:bg-borda/40" aria-label="mais uma pessoa">
              <Plus size={14} />
            </button>
            <div className="ml-2 flex flex-wrap gap-1">
              {RAPIDOS.map((r) => (
                <button key={r.rotulo} type="button" onClick={() => setPessoas(r.pessoas)}
                  className={`rounded-md border px-2 py-1 text-xs ${pessoas === r.pessoas ? "border-luz text-luz" : "border-borda text-suave hover:bg-borda/40"}`}>
                  {r.rotulo}
                </button>
              ))}
            </div>
          </div>
        </fieldset>

        <fieldset className="mb-4">
          <legend className="mb-1 text-xs text-suave">ocorrência no trecho</legend>
          <div className="flex gap-1">
            {[
              { v: null, rotulo: "nenhuma" },
              { v: "seguranca", rotulo: "segurança" },
              { v: "transito", rotulo: "trânsito" },
            ].map((o) => (
              <button key={o.rotulo} type="button" onClick={() => setOcorrencia(o.v)}
                className={`flex-1 rounded-md border px-2 py-2 text-xs ${ocorrencia === o.v ? (o.v ? "border-falha text-falha" : "border-luz text-luz") : "border-borda text-suave hover:bg-borda/40"}`}>
                {o.rotulo}
              </button>
            ))}
          </div>
        </fieldset>

        <label className="mb-4 block text-xs text-suave">
          a leitura vale por
          <select value={vigencia} onChange={(e) => setVigencia(Number(e.target.value))}
            className="mt-1 w-full rounded-md border border-borda bg-fundo px-2 py-2 text-sm text-texto">
            {VIGENCIAS.map((v) => (
              <option key={v.min} value={v.min}>{v.rotulo}</option>
            ))}
          </select>
        </label>

        {erro && <p className="mb-3 rounded-md bg-falha/10 p-2 text-xs text-falha">não enviado: {erro}</p>}

        <div className="flex justify-end gap-2">
          <button type="button" onClick={fechar} className="rounded-md border border-borda px-3 py-2 text-sm hover:bg-borda/40">
            cancelar
          </button>
          <button type="button" onClick={publicar} disabled={enviando || trecho === ""}
            className="inline-flex items-center gap-2 rounded-md bg-luz px-3 py-2 text-sm font-medium text-fundo disabled:opacity-50">
            <Send size={14} />
            {enviando ? "enviando..." : "enviar leitura"}
          </button>
        </div>
      </div>
    </div>
  );
}
