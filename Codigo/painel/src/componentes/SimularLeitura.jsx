// Modal de demonstracao: publica o que a plataforma de monitoramento
// publicaria para um trecho (DIVERGENCIAS 56) - o VOLUME dos ultimos 5 min
// (media de pessoas na area) ou uma OCORRENCIA, na hora. Uma chamada so
// (POST /eventos). O painel continua sem decidir nada: quem decide e o
// servico, e a aba "decisões explicadas" mostra por que.

import { useMemo, useState } from "react";
import { Minus, Plus, Send, X } from "lucide-react";
import { TERCIS, agoraServidor, api, faixaMov } from "../api";

// Atalhos de volume calculados pela REGUA do trecho escolhido (3.6): cada
// rua tem o seu "cheio" tipico, e o servico compara o volume com ele. O nivel
// normalizado (pessoas / regua) cai nas faixas dos tercis (3.7); os alvos
// abaixo ficam no meio de cada faixa.
const ALVOS = [
  { rotulo: "vazia", nivel: 0 },
  { rotulo: "pouco", nivel: TERCIS[0] / 2 },
  { rotulo: "médio", nivel: (TERCIS[0] + TERCIS[1]) / 2 },
  { rotulo: "alto", nivel: Math.min(1, TERCIS[1] * 2) },
];

const OCORRENCIAS = [
  { v: "seguranca", rotulo: "segurança" },
  { v: "transito", rotulo: "trânsito" },
  { v: "encerrada", rotulo: "encerrar ocorrência" },
];

function nomeTrecho(t) {
  const faixa =
    t.numero_inicial != null && t.numero_final != null ? ` ${t.numero_inicial}–${t.numero_final}` : "";
  // So os pontos do trabalho pelo nome; os simulados da visao de bairro
  // (prefixo JH-) entram so como contagem, para a opcao caber na tela.
  const reais = t.pontos.filter((c) => !c.startsWith("JH-"));
  const simulados = t.pontos.length - reais.length;
  const partes = [...reais, ...(simulados ? [`${simulados} simulado${simulados > 1 ? "s" : ""}`] : [])];
  const pontos = partes.length ? ` · ${partes.join(", ")}` : " · sem luminária no sistema";
  return `${[t.tipo_logradouro, t.nome_logradouro].filter(Boolean).join(" ")}${faixa}${pontos}`;
}

const arredonda = (v) => Math.round(v * 10) / 10;
const num = (v) => Number(v).toLocaleString("pt-BR", { maximumFractionDigits: 2 });
const rua = (t) =>
  `${[t.tipo_logradouro, t.nome_logradouro].filter(Boolean).join(" ")}` +
  (t.numero_inicial != null && t.numero_final != null ? ` ${t.numero_inicial}–${t.numero_final}` : "");

// Montado so quando aberto. Abre com TODOS os trechos que o poste na tela
// enxerga (o "movimento agora" do poste e o maior deles), ou com os trechos
// selecionados no mapa. Varios trechos saem num PACOTE so: a API grava todos
// numa transacao e o servico decide depois, ja vendo todos.
export default function SimularLeitura({ fechar, trechos, trechosIniciais = [], pontoAtual, aoPublicar }) {
  const existe = (id) => trechos.some((t) => t.id === id);
  const [selecionados, setSelecionados] = useState(() => {
    const ini = trechosIniciais.filter(existe);
    return ini.length ? ini : trechos[0] ? [trechos[0].id] : [];
  });
  const [tipo, setTipo] = useState("volume");
  // "normal" = como a plataforma publicaria; "teste" = forcar evento imediato
  // (POST /teste/eventos): o comando vai ao no sem a rampa de descida.
  const [modo, setModo] = useState("normal");
  // Volume pela FAIXA (cada trecho recebe as pessoas pela propria regua) ou
  // pelo NUMERO de pessoas (o mesmo em todos; alvo = null).
  const [alvo, setAlvo] = useState(ALVOS[0]);
  const [media, setMedia] = useState(0);
  const [ocorrencia, setOcorrencia] = useState("seguranca");
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState(null);

  const escolhidos = selecionados.map((id) => trechos.find((t) => t.id === id)).filter(Boolean);
  const pessoasDe = (t) => (alvo ? Math.round(alvo.nivel * (t.regua ?? 5) * 100) / 100 : media);
  const disponiveis = useMemo(
    () => [...trechos].filter((t) => !selecionados.includes(t.id))
      .sort((a, b) => b.pontos.length - a.pontos.length || a.nome_logradouro.localeCompare(b.nome_logradouro)),
    [trechos, selecionados],
  );
  const doPoste = (pontoAtual?.trechos ?? []).filter((id) => existe(id) && !selecionados.includes(id));

  const tirar = (id) => setSelecionados((s) => s.filter((x) => x !== id));
  const por = (ids) => setSelecionados((s) => [...s, ...ids.filter((id) => !s.includes(id))]);

  async function publicar() {
    setEnviando(true);
    setErro(null);
    const agora = agoraServidor();
    const itens = escolhidos.map((t) => {
      const base = { ocorrido_em: agora, trecho: t.id, origem: "painel-demonstracao" };
      return tipo === "volume"
        ? { ...base, tipo: "volume", pessoas_media: pessoasDe(t), periodo_s: 300 }
        : { ...base, tipo: "ocorrencia", ocorrencia };
    });
    const corpo = itens.length === 1 ? itens[0] : itens;
    try {
      const r = modo === "teste" ? await api.publicarTeste(corpo) : await api.publicarLeitura(corpo);
      if (r.aceitos) {
        if (r.recusados.length) {
          setErro(`${r.recusados.length} de ${itens.length} recusado(s): ${r.recusados.map((x) => x.erro).join("; ")}`);
          if (!r.aceitos.length) return;
        }
        aoPublicar(r.aceitos[0]);
      } else {
        aoPublicar(r);
      }
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
        className="max-h-[92vh] w-full max-w-xl overflow-y-auto rounded-xl border border-borda bg-carta p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 id="titulo-simular" className="text-base font-semibold">
              Simular publicação da plataforma
            </h2>
            <p className="text-xs text-suave">
              O que o sistema de monitoramento enviaria: o volume dos últimos 5 min de cada trecho, ou uma ocorrência na hora.
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

        <div className="mb-4 flex gap-1 border-b border-borda" role="tablist" aria-label="modo">
          {[
            { v: "normal", rotulo: "publicação normal" },
            { v: "teste", rotulo: "forçar evento imediato (teste)" },
          ].map((m) => (
            <button key={m.v} type="button" role="tab" aria-selected={modo === m.v} onClick={() => setModo(m.v)}
              className={`-mb-px border-b-2 px-3 py-2 text-xs ${modo === m.v ? (m.v === "teste" ? "border-taxa text-taxa" : "border-luz text-luz") : "border-transparent text-suave hover:text-texto"}`}>
              {m.rotulo}
            </button>
          ))}
        </div>

        {modo === "teste" && (
          <p className="mb-4 rounded-md bg-taxa/10 p-2 text-xs text-taxa">
            Só para teste e demonstração: o serviço decide normalmente (regras e piso), mas o nó vai
            direto ao nível, <strong>sem a rampa de descida</strong> que a norma exige. Não usar em resultados.
          </p>
        )}

        <div className="mb-4">
          <p className="mb-1 text-xs text-suave">
            trechos de via ({escolhidos.length}){escolhidos.length > 1 && " · enviados juntos, num pacote só"}
          </p>
          <div className="flex flex-wrap gap-1">
            {escolhidos.map((t) => (
              <span key={t.id} className="inline-flex items-center gap-1 rounded-full border border-luz/50 bg-luz/10 py-0.5 pr-1 pl-2 text-xs text-luz">
                {rua(t)}
                <button type="button" onClick={() => tirar(t.id)} aria-label={`tirar ${rua(t)}`}
                  className="rounded-full p-0.5 hover:bg-luz/20"><X size={11} /></button>
              </span>
            ))}
            {!escolhidos.length && <span className="text-xs text-falha">nenhum trecho escolhido</span>}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {doPoste.length > 0 && (
              <button type="button" onClick={() => por(doPoste)}
                className="rounded-md border border-borda px-2 py-1 text-xs text-luz hover:border-luz">
                + todos os trechos do {pontoAtual.codigo} ({doPoste.length})
              </button>
            )}
            <select value="" onChange={(e) => e.target.value && por([Number(e.target.value)])}
              aria-label="acrescentar trecho"
              className="min-w-0 flex-1 rounded-md border border-borda bg-fundo px-2 py-1 text-xs text-texto">
              <option value="">+ acrescentar outro trecho…</option>
              {disponiveis.map((t) => <option key={t.id} value={t.id}>{nomeTrecho(t)}</option>)}
            </select>
          </div>
        </div>

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
            <div className="flex flex-wrap items-center gap-1">
              <span className="mr-1 text-[11px] text-suave">pela faixa:</span>
              {ALVOS.map((a) => (
                <button key={a.rotulo} type="button" onClick={() => setAlvo(a)}
                  className={`rounded-md border px-2 py-1 text-xs ${alvo === a ? "border-luz text-luz" : "border-borda text-suave hover:bg-borda/40"}`}>
                  {a.rotulo} ({(a.nivel * 100).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%)
                </button>
              ))}
            </div>
            <div className="mt-2 flex items-center gap-2">
              <span className="text-[11px] text-suave">ou pessoas (igual em todos):</span>
              <button type="button" onClick={() => { setMedia((n) => Math.max(0, arredonda((alvo ? 0 : n) - 0.1))); setAlvo(null); }}
                className="rounded-md border border-borda p-1.5 hover:bg-borda/40" aria-label="diminuir 0,1">
                <Minus size={12} />
              </button>
              <input
                type="number" min={0} max={10000} step={0.1} value={alvo ? "" : media} placeholder="--"
                onChange={(e) => { setAlvo(null); setMedia(Math.max(0, Math.min(10000, arredonda(Number(e.target.value) || 0)))); }}
                className={`w-20 rounded-md border bg-fundo px-2 py-1 text-center tabular-nums text-texto ${alvo ? "border-borda" : "border-luz"}`}
                aria-label="média de pessoas"
              />
              <button type="button" onClick={() => { setMedia((n) => arredonda((alvo ? 0 : n) + 0.1)); setAlvo(null); }}
                className="rounded-md border border-borda p-1.5 hover:bg-borda/40" aria-label="aumentar 0,1">
                <Plus size={12} />
              </button>
            </div>
            {escolhidos.length > 0 && (
              <ul className="mt-3 space-y-1 rounded-md border border-borda p-2 text-[11px]">
                <li className="text-suave">o que vai ser enviado (pessoas ÷ régua do trecho = faixa):</li>
                {escolhidos.map((t) => {
                  const n = pessoasDe(t);
                  const nivel = t.regua ? n / t.regua : null;
                  return (
                    <li key={t.id} className="flex justify-between gap-2">
                      <span className="truncate">{rua(t)}</span>
                      <span className="whitespace-nowrap tabular-nums">
                        {num(n)} de {t.regua != null ? num(t.regua) : "--"}
                        {t.regua_aprendida ? "" : "*"} = <b>{nivel != null ? `${num(nivel * 100)}%` : "--"}</b>
                        {nivel != null && <> · {faixaMov(nivel)}</>}
                      </span>
                    </li>
                  );
                })}
              </ul>
            )}
            <p className="mt-2 text-[11px] text-suave">
              Ocupação média, e não soma de passagens; o volume vale 15 min. Vale o maior trecho de cada poste.
              {escolhidos.some((t) => !t.regua_aprendida) && " * régua inicial (sem 7 dias de histórico)."}
            </p>
          </fieldset>
        ) : (
          <fieldset className="mb-4">
            <legend className="mb-1 text-xs text-suave">ocorrência {escolhidos.length > 1 ? "nos trechos" : "no trecho"}</legend>
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
          <button type="button" onClick={publicar} disabled={enviando || !escolhidos.length}
            className="inline-flex items-center gap-2 rounded-md bg-luz px-3 py-2 text-sm font-semibold text-white uppercase tracking-wide transition-colors hover:bg-tinta disabled:opacity-50 disabled:hover:bg-luz">
            <Send size={14} />
            {enviando ? "enviando..." : modo === "teste" ? "forçar agora" : "publicar"}
            {escolhidos.length > 1 && ` (${escolhidos.length})`}
          </button>
        </div>
      </div>
    </div>
  );
}
