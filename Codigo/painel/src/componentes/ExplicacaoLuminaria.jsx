// Decisoes explicadas, filtradas por luminaria: as ultimas decisoes do poste,
// cada uma com os trechos que ela olhou e o trecho que definiu o nivel com o
// fundo escuro. Cada decisao e do poste (ou do grupo dele), nao do trecho: o
// servico le a publicacao vigente de cada trecho e usa a ocorrencia (se
// houver em qualquer um) ou o MAIOR movimento pela regua (3.5.2).

import { useEffect, useState } from "react";
import { ArrowDown, ArrowRight, ArrowUp, ChevronDown, ChevronRight, Equal } from "lucide-react";
import { Decisao } from "./Explicacoes";
import { OCORRENCIAS, api, descreverDegrau, descreverEvento, hora, pct } from "../api";

const num = (v) => Number(v).toLocaleString("pt-BR", { maximumFractionDigits: 2 });

function nomeTrecho(t) {
  if (!t) return null;
  const rua = [t.tipo_logradouro, t.nome_logradouro].filter(Boolean).join(" ") || "sem nome";
  return `${rua} ${t.numero_inicial ?? ""}–${t.numero_final ?? ""}`;
}

// Linhas de trecho de UMA decisao: os trechos do poste, com o que a decisao
// viu em cada um, e qual definiu o nivel.
function trechosDaDecisao(d, ponto, trechos, eventosPorId) {
  const e = d.entrada ?? {};
  const volumes = e.pessoas_media_por_trecho ?? {};
  const ocorrencias = new Map();
  for (const id of d.evento_ids ?? []) {
    const ev = eventosPorId.get(id);
    if (ev?.tipo === "ocorrencia" && ev.ocorrencia !== "encerrada") ocorrencias.set(String(ev.trecho), ev);
  }
  const ids = [...new Set([...(ponto?.trechos ?? []).map(String), ...Object.keys(volumes)])];
  const linhas = ids.map((id) => {
    const t = trechos.find((x) => String(x.id) === id);
    const n = volumes[id];
    const r = t?.regua ?? null;
    return {
      id, nome: nomeTrecho(t) ?? `trecho ${id}`,
      pessoas: n ?? null, regua: r, fracao: n != null && r ? Math.min(n / r, 1) : null,
      ocorrencia: ocorrencias.get(id) ?? null,
    };
  });
  // Quem definiu: ocorrencia vence; senao, o maior movimento.
  if (e.ocorrencia) {
    for (const l of linhas) l.definiu = Boolean(l.ocorrencia);
    if (!linhas.some((l) => l.definiu)) linhas.forEach((l) => (l.definiu = false));
  } else {
    const max = Math.max(...linhas.map((l) => l.fracao ?? -1));
    for (const l of linhas) l.definiu = l.fracao !== null && l.fracao === max;
  }
  linhas.sort((a, b) => (b.definiu - a.definiu) || ((b.fracao ?? -1) - (a.fracao ?? -1)));
  return linhas;
}

function Mudanca({ de, para }) {
  const dif = de == null ? 0 : para - de;
  const [Icone, cor, texto] =
    de == null ? [ArrowRight, "text-suave", "primeira decisão"]
      : dif > 0.001 ? [ArrowUp, "text-ok", "subiu"]
        : dif < -0.001 ? [ArrowDown, "text-piso", "desceu"]
          : [Equal, "text-suave", "manteve"];
  return (
    <span className="inline-flex items-center gap-1.5 tabular-nums">
      <b>{de == null ? "--" : pct(de)}</b>
      <ArrowRight size={14} className="text-suave" aria-hidden="true" />
      <b>{pct(para)}</b>
      <span className={`inline-flex items-center gap-0.5 text-xs font-semibold ${cor}`}>
        <Icone size={13} aria-hidden="true" /> {texto}
      </span>
    </span>
  );
}

function resumo(d, linhas) {
  const e = d.entrada ?? {};
  if (e.sem_dado) return "Nenhum trecho com publicação valendo: pleno por segurança.";
  const def = linhas.find((l) => l.definiu);
  if (e.ocorrencia) {
    return `Ocorrência${def?.ocorrencia ? ` de ${OCORRENCIAS[def.ocorrencia.ocorrencia]}` : ""} em ${def?.nome ?? "um trecho"}: volta à classe da via.`;
  }
  const deg = descreverDegrau(e.degrau);
  return `Maior movimento em ${def?.nome ?? "--"} (${pct(def?.fracao)} do cheio da rua) → ${deg}.`;
}

// Monta o item da cadeia para ESTA decisao quando a API no ar nao aceita o
// parametro `decisao` (devolve a primeira decisao que usou o evento): usa o
// item dela como molde (faixas, reguas) e troca tudo o que e da decisao pelos
// valores gravados nela. Textos das regras vem do que a API ja mostrou.
function montar(d, molde, textos) {
  const regras = Object.entries(d.ativacoes ?? {})
    .filter(([, g]) => Number(g) > 0)
    .map(([id, g]) => ({ id, grau: Number(g), ...(textos.get(id) ?? { texto: `${id} (texto indisponível)`, origem: "" }) }))
    .sort((a, b) => b.grau - a.grau);
  return {
    ...molde, decisao_id: d.id, criado_em: d.criado_em, entrada: d.entrada,
    versao_base_regras: d.versao_base_regras, regras_ativadas: regras,
    nivel_pretendido: Number(d.nivel_pretendido), nivel_emitido: Number(d.nivel_emitido),
    nivel_anterior: d.nivel_anterior, restricao_aplicada: d.restricao_aplicada,
    motivo_restricao: d.restricao_aplicada === molde.restricao_aplicada ? molde.motivo_restricao : "",
    lux_medido: null, lux_esperado: null, duty: null,
  };
}

// Para cada trecho do poste: a publicacao dele que esta decisao usou e o
// quadro completo da decisao (os mesmos cartoes da visao por publicacao).
function useCadeias(d, codigo) {
  const [porTrecho, setPorTrecho] = useState(null);
  useEffect(() => {
    let vivo = true;
    (async () => {
      const respostas = [];
      for (const ev of d.evento_ids ?? []) {
        try { respostas.push(await api.explicacao(ev, d.id)); } catch { /* evento sem explicacao */ }
      }
      const textos = new Map();
      for (const x of respostas)
        for (const i of x.decisoes)
          for (const r of i.regras_ativadas ?? []) textos.set(r.id, { texto: r.texto, origem: r.origem });
      const mapa = {};
      for (const x of respostas) {
        const t = String(x.evento.trecho);
        if (mapa[t] && new Date(mapa[t].evento.ocorrido_em) >= new Date(x.evento.ocorrido_em)) continue;
        const doPonto = x.decisoes.find((i) => i.ponto === codigo && i.decidida);
        const item = !doPonto ? null : doPonto.decisao_id === d.id ? doPonto : montar(d, doPonto, textos);
        mapa[t] = { evento: x.evento, item };
      }
      if (vivo) setPorTrecho(mapa);
    })();
    return () => { vivo = false; };
    // So pela id: a lista de decisoes e rebuscada a cada 2 s (objeto novo).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [d.id, codigo]);
  return porTrecho;
}

function QuadrosPorTrecho({ d, linhas, codigo, trechos }) {
  const porTrecho = useCadeias(d, codigo);
  if (!porTrecho) return <p className="text-xs text-suave">carregando os quadros…</p>;
  return (
    <ul className="space-y-3">
      {linhas.map((l) => {
        const c = porTrecho[l.id];
        const escuro = l.definiu;
        return (
          <li key={l.id} className={`rounded-xl p-3 ${escuro ? "bg-[#3d4350] text-white" : "bg-fundo"}`}>
            <div className="flex flex-wrap items-baseline justify-between gap-x-3">
              <span className="text-base font-semibold">
                {c ? descreverEvento(c.evento) : "sem publicação valendo"}
                <span className={`ml-2 text-sm font-normal ${escuro ? "text-white/80" : "text-suave"}`}>{l.nome}</span>
              </span>
              {escuro && (
                <span className="rounded bg-luz px-1.5 py-0.5 text-[11px] font-bold tracking-wide text-white uppercase">
                  definiu o nível
                </span>
              )}
            </div>
            <p className={`text-xs ${escuro ? "text-white/75" : "text-suave"}`}>
              trecho {l.id}
              {c && <> · recebida às {hora(c.evento.recebido_em)} · origem {c.evento.origem}</>}
              {l.fracao != null && <> · {num(l.pessoas)} de {num(l.regua)} pessoas = <b>{pct(l.fracao)}</b> do cheio da rua</>}
            </p>
            {l.fracao != null && (
              <span className={`mt-1 block h-1.5 overflow-hidden rounded ${escuro ? "bg-white/20" : "bg-borda"}`}>
                <span className={`block h-full ${escuro ? "bg-luz" : "bg-suave/60"}`} style={{ width: `${l.fracao * 100}%` }} />
              </span>
            )}
            {!escuro && l.ocorrencia == null && l.fracao != null && (
              <p className="mt-1 text-xs text-suave">
                lida nesta decisão, mas não definiu o nível
                {d.entrada?.ocorrencia ? " (ocorrência em outro trecho vence qualquer volume)" : " (percentual menor que o do trecho escuro)"}
              </p>
            )}
            {escuro && c?.item && (
              <div className="mt-3 rounded-xl bg-carta text-texto">
                <Decisao d={c.item} trechos={trechos} />
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}

function CartaoDecisao({ d, anterior, ponto, trechos, eventosPorId, aberta, alternar, nova }) {
  const linhas = trechosDaDecisao(d, ponto, trechos, eventosPorId);
  const def = linhas.find((l) => l.definiu);
  const de = d.nivel_anterior ?? anterior ?? null;
  return (
    <li className={`rounded-xl border ${aberta ? "border-luz/50" : "border-borda"} bg-carta`}>
      <button type="button" onClick={alternar}
              className="flex w-full flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3 text-left hover:bg-fundo/60">
        {aberta ? <ChevronDown size={16} className="text-luz" /> : <ChevronRight size={16} className="text-suave" />}
        <span className="tabular-nums text-sm text-suave">{hora(d.criado_em)}</span>
        <Mudanca de={de} para={d.nivel_emitido} />
        {nova && <span className="rounded bg-ok px-1.5 py-0.5 text-[11px] font-bold text-white uppercase">nova</span>}
        {!aberta && (
          <span className="ml-auto truncate text-xs text-suave">
            definiu: <b className="text-texto">{d.entrada?.sem_dado ? "nenhum (sem dado)" : def?.nome ?? "--"}</b>
            {def?.ocorrencia ? " (ocorrência)" : def?.fracao != null ? ` (${pct(def.fracao)})` : ""}
          </span>
        )}
      </button>
      {aberta && (
        <div className="space-y-3 border-t border-borda px-4 pt-3 pb-4">
          <p className="text-sm">{resumo(d, linhas)}</p>
          <QuadrosPorTrecho d={d} linhas={linhas} codigo={ponto.codigo} trechos={trechos} />
        </div>
      )}
    </li>
  );
}

export default function ExplicacaoLuminaria({ codigo, pontos, trechos, eventos }) {
  const [decisoes, setDecisoes] = useState([]);
  const [erro, setErro] = useState(null);
  const [aberta, setAberta] = useState(null); // id aberto; null = a mais recente
  const [vistas, setVistas] = useState(null); // ids ja vistos, para o selo "nova"
  const ponto = pontos.find((p) => p.codigo === codigo);

  useEffect(() => {
    setDecisoes([]); setAberta(null); setVistas(null);
    if (!codigo) return;
    let vivo = true;
    const buscar = () =>
      api.decisoes({ ponto: codigo, limite: 15 })
        .then((x) => { if (vivo) { setDecisoes(x); setErro(null); } })
        .catch((e) => vivo && setErro(e.message));
    buscar();
    const id = setInterval(buscar, 2000);
    return () => { vivo = false; clearInterval(id); };
  }, [codigo]);

  useEffect(() => {
    if (vistas === null && decisoes.length) setVistas(new Set(decisoes.map((d) => d.id)));
  }, [decisoes, vistas]);

  const eventosPorId = new Map(eventos.map((e) => [e.id, e]));
  const idAberto = aberta ?? decisoes[0]?.id;

  if (!ponto) return <p className="text-sm text-suave">escolha uma luminária à esquerda</p>;
  return (
    <div className="space-y-3">
      <div>
        <h2 className="text-lg font-semibold">
          {ponto.codigo} <span className="text-sm font-normal text-suave">poste {ponto.placa ?? "--"} · classe {ponto.classe_codigo}</span>
        </h2>
        <p className="text-xs text-suave">
          olha {ponto.trechos?.length ?? 0} trecho(s) de rua · decide de novo a cada publicação de qualquer um deles
          {decisoes[0] && <> · nível agora: <b className="text-texto">{pct(decisoes[0].nivel_emitido)}</b></>}
        </p>
      </div>
      {erro && <p className="text-xs text-falha">{erro}</p>}
      {!erro && decisoes.length === 0 && <p className="text-sm text-suave">nenhuma decisão desta luminária ainda</p>}
      <ul className="space-y-2">
        {decisoes.map((d, i) => (
          <CartaoDecisao key={d.id} d={d} anterior={decisoes[i + 1]?.nivel_emitido}
                         ponto={ponto} trechos={trechos} eventosPorId={eventosPorId}
                         aberta={d.id === idAberto}
                         alternar={() => setAberta(d.id === idAberto ? "nenhuma" : d.id)}
                         nova={vistas !== null && !vistas.has(d.id)} />
        ))}
      </ul>
      <p className="text-[11px] text-suave">
        A régua (o "cheio" da rua) mostrada é a de hoje; numa decisão antiga, o percentual pode diferir um pouco.
      </p>
    </div>
  );
}
