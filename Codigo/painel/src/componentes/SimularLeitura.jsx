// Modal de demonstracao: publica o que a plataforma de monitoramento
// publicaria para um trecho (DIVERGENCIAS 56) - o VOLUME dos ultimos 5 min
// (media de pessoas na area) ou uma OCORRENCIA, na hora. Uma chamada so
// (POST /eventos). O painel continua sem decidir nada: quem decide e o
// servico, e a aba "decisões explicadas" mostra por que.

import { useMemo, useState } from "react";
import { Minus, Plus, Send, X } from "lucide-react";
import { api } from "../api";

// Com a referencia inicial de uma rua local (5 pessoas no "cheio"), estes
// valores caem nas tres faixas: baixa, media e alta.
const RAPIDOS = [
  { rotulo: "vazia (0)", media: 0 },
  { rotulo: "pouco (0,3)", media: 0.3 },
  { rotulo: "médio (1,5)", media: 1.5 },
  { rotulo: "alto (4)", media: 4 },
];

const OCORRENCIAS = [
  { v: "seguranca", rotulo: "segurança" },
  { v: "transito", rotulo: "trânsito" },
  { v: "encerrada", rotulo: "encerrar ocorrência" },
];

function nomeTrecho(t) {
  const faixa =
    t.numero_inicial != null && t.numero_final != null ? ` ${t.numero_inicial}–${t.numero_final}` : "";
  const pontos = t.pontos.length ? ` · ${t.pontos.join(", ")}` : " · sem luminária no sistema";
  return `${[t.tipo_logradouro, t.nome_logradouro].filter(Boolean).join(" ")}${faixa}${pontos}`;
}

const arredonda = (v) => Math.round(v * 10) / 10;

// Montado so quando aberto: cada abertura nasce do trecho do ponto na tela.
export default function SimularLeitura({ fechar, trechos, trechoInicial, aoPublicar }) {
  const [trecho, setTrecho] = useState(trechoInicial ?? trechos[0]?.id ?? "");
  const [tipo, setTipo] = useState("volume");
  const [media, setMedia] = useState(0);
  const [ocorrencia, setOcorrencia] = useState("seguranca");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  const ordenados = useMemo(
    () => [...trechos].sort((a, b) => b.pontos.length - a.pontos.length || a.nome_logradouro.localeCompare(b.nome_logradouro)),
    [trechos],
  );

  async function publicar() {
    setEnviando(true);
    setErro(null);
    const base = { ocorrido_em: new Date().toISOString(), trecho: Number(trecho), origem: "painel-demonstracao" };
    const corpo =
      tipo === "volume"
        ? { ...base, tipo: "volume", pessoas_media: media, periodo_s: 300 }
        : { ...base, tipo: "ocorrencia", ocorrencia };
    try {
      const evento = await api.publicarLeitura(corpo);
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
              Simular publicação da plataforma
            </h2>
            <p className="text-xs text-suave">
              O que o Smart Sampa enviaria: o volume dos últimos 5 min do trecho, ou uma ocorrência na hora.
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

        <div className="mb-4 flex gap-1" role="tablist" aria-label="tipo de publicação">
          {[
            { v: "volume", rotulo: "volume (a cada 5 min)" },
            { v: "ocorrencia", rotulo: "ocorrência (na hora)" },
          ].map((t) => (
            <button key={t.v} type="button" role="tab" aria-selected={tipo === t.v} onClick={() => setTipo(t.v)}
              className={`flex-1 rounded-md border px-2 py-2 text-xs ${tipo === t.v ? "border-luz text-luz" : "border-borda text-suave hover:bg-borda/40"}`}>
              {t.rotulo}
            </button>
          ))}
        </div>

        {tipo === "volume" ? (
          <fieldset className="mb-4">
            <legend className="mb-1 text-xs text-suave">média de pessoas na área nos últimos 5 min</legend>
            <div className="flex items-center gap-2">
              <button type="button" onClick={() => setMedia((n) => Math.max(0, arredonda(n - 0.1)))}
                className="rounded-md border border-borda p-2 hover:bg-borda/40" aria-label="diminuir 0,1">
                <Minus size={14} />
              </button>
              <input
                type="number" min={0} max={10000} step={0.1} value={media}
                onChange={(e) => setMedia(Math.max(0, Math.min(10000, arredonda(Number(e.target.value) || 0))))}
                className="w-20 rounded-md border border-borda bg-fundo px-2 py-2 text-center text-lg tabular-nums text-texto"
                aria-label="média de pessoas"
              />
              <button type="button" onClick={() => setMedia((n) => arredonda(n + 0.1))}
                className="rounded-md border border-borda p-2 hover:bg-borda/40" aria-label="aumentar 0,1">
                <Plus size={14} />
              </button>
              <div className="ml-2 flex flex-wrap gap-1">
                {RAPIDOS.map((r) => (
                  <button key={r.rotulo} type="button" onClick={() => setMedia(r.media)}
                    className={`rounded-md border px-2 py-1 text-xs ${media === r.media ? "border-luz text-luz" : "border-borda text-suave hover:bg-borda/40"}`}>
                    {r.rotulo}
                  </button>
                ))}
              </div>
            </div>
            <p className="mt-2 text-[11px] text-suave">
              Ocupação média, e não soma de passagens. O serviço compara com o movimento normal da rua; o volume vale 15 min.
            </p>
          </fieldset>
        ) : (
          <fieldset className="mb-4">
            <legend className="mb-1 text-xs text-suave">ocorrência no trecho</legend>
            <div className="flex gap-1">
              {OCORRENCIAS.map((o) => (
                <button key={o.v} type="button" onClick={() => setOcorrencia(o.v)}
                  className={`flex-1 rounded-md border px-2 py-2 text-xs ${ocorrencia === o.v ? (o.v === "encerrada" ? "border-luz text-luz" : "border-falha text-falha") : "border-borda text-suave hover:bg-borda/40"}`}>
                  {o.rotulo}
                </button>
              ))}
            </div>
            <p className="mt-2 text-[11px] text-suave">
              Vale até a plataforma publicar o encerramento, ou por 15 min.
            </p>
          </fieldset>
        )}

        {erro && <p className="mb-3 rounded-md bg-falha/10 p-2 text-xs text-falha">não enviado: {erro}</p>}

        <div className="flex justify-end gap-2">
          <button type="button" onClick={fechar} className="rounded-md border border-borda px-3 py-2 text-sm hover:bg-borda/40">
            cancelar
          </button>
          <button type="button" onClick={publicar} disabled={enviando || trecho === ""}
            className="inline-flex items-center gap-2 rounded-md bg-luz px-3 py-2 text-sm font-semibold text-white uppercase tracking-wide transition-colors hover:bg-tinta disabled:opacity-50 disabled:hover:bg-luz">
            <Send size={14} />
            {enviando ? "enviando..." : "publicar"}
          </button>
        </div>
      </div>
    </div>
  );
}
