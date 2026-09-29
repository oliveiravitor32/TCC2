// Aba "decisões explicadas": para cada publicacao recebida, o que o sistema
// fez e por que (DIVERGENCIAS 55 e 56). A cadeia inteira, na ordem em que
// acontece: publicacao -> luminarias do trecho -> entradas da inferencia -> regras que
// dispararam -> nivel pretendido -> correcao da verificacao -> nivel emitido
// -> luz medida. Tudo vem do registro de auditoria (GET /eventos/{id}/explicacao).

import { useEffect, useState } from "react";
import { ArrowRight, Brain, Lightbulb, ShieldCheck } from "lucide-react";
import { RESTRICOES, api, descreverDegrau, descreverEvento, faixaHoraria, faixaMov, hora, lux, pct } from "../api";

function Etapa({ icone: Icone, titulo, children }) {
  return (
    <div className="rounded-lg border border-borda bg-fundo/40 p-3">
      <h4 className="mb-2 flex items-center gap-1 text-[11px] font-medium tracking-wide text-suave uppercase">
        <Icone size={12} aria-hidden="true" />
        {titulo}
      </h4>
      {children}
    </div>
  );
}

function Decisao({ d }) {
  if (!d.decidida) {
    return (
      <p className="rounded-lg border border-borda p-3 text-xs text-suave">
        {d.ponto} ({d.placa ?? "sem placa"}): nenhuma decisão usou esta publicação
        {" "}(ainda não decidiu, ou é o encerramento de uma ocorrência).
      </p>
    );
  }
  const e = d.entrada ?? {};
  const restr = RESTRICOES[d.restricao_aplicada] ?? RESTRICOES.nenhuma;
  const volumes = Object.entries(e.pessoas_media_por_trecho ?? {});
  const prev = e.modo === "reativo" ? e.observada : e.prevista;
  const niveis = e.niveis_classe ?? [];

  return (
    <div className="space-y-2 rounded-xl border border-borda p-3">
      <p className="text-sm font-medium">
        {d.ponto}{" "}
        <span className="text-xs font-normal text-suave">
          poste {d.placa ?? "--"} · a {d.distancia_m.toFixed(1)} m do trecho · decidido às {hora(d.criado_em)}
        </span>
      </p>
      <div className="grid gap-2 md:grid-cols-[1fr_auto_1.4fr_auto_1fr]">
        <Etapa icone={ArrowRight} titulo="entradas da IA">
          <ul className="space-y-1 text-xs">
            <li>
              movimento agora: <b>{faixaMov(e.observada)}</b>{" "}
              <span className="text-suave">({pct(e.observada)} do cheio da rua)</span>
              {volumes.length > 0 && (
                <span className="block text-suave">
                  média de pessoas em 5 min: {volumes.map(([t, n]) => `trecho ${t}: ${n}`).join("; ")}
                </span>
              )}
            </li>
            <li>
              ocorrência: <b className={e.ocorrencia ? "text-falha" : ""}>{e.ocorrencia ? "sim" : "não"}</b>
            </li>
            <li>
              {e.modo === "reativo" ? "sem previsão (modo reativo): usa o movimento agora" : "movimento previsto"}:{" "}
              <b>{faixaMov(prev)}</b> <span className="text-suave">({pct(prev)})</span>
            </li>
            <li>
              horário: <b>{faixaHoraria(e.horas_desde_18h)}</b>
            </li>
            {niveis.length === 3 && (
              <li className="text-suave">
                classes da via: {niveis.map((n) => n.toFixed(3)).join(" → ")} do pleno
              </li>
            )}
            {e.sem_dado && <li className="text-falha">sem volume vigente: pleno por segurança</li>}
          </ul>
        </Etapa>
        <ArrowRight className="hidden self-center text-suave md:block" size={16} aria-hidden="true" />
        <Etapa icone={Brain} titulo={`regras que dispararam · ${d.versao_base_regras}`}>
          {d.regras_ativadas.length === 0 ? (
            <p className="text-xs text-suave">nenhuma regra: sem evidência, o lado seguro é o pleno</p>
          ) : (
            <ul className="space-y-2 text-xs">
              {d.regras_ativadas.map((r) => (
                <li key={r.id}>
                  <div className="flex items-center gap-2">
                    <span className="w-10 shrink-0 tabular-nums text-suave">{Math.round(r.grau * 100)}%</span>
                    <span className="h-1.5 flex-1 rounded bg-borda">
                      <span className="block h-1.5 rounded bg-luz" style={{ width: `${r.grau * 100}%` }} />
                    </span>
                  </div>
                  <p className="mt-0.5 font-medium">{r.texto}</p>
                  <p className="text-[11px] text-suave">{r.origem}</p>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-2 border-t border-borda pt-2 text-xs">
            degrau: <b>{descreverDegrau(e.degrau)}</b>
            {e.degrau != null && <span className="text-suave"> ({e.degrau.toFixed(2)})</span>}
            <br />
            nível pretendido: <b className="tabular-nums">{d.nivel_pretendido.toFixed(3)}</b>
          </p>
        </Etapa>
        <ArrowRight className="hidden self-center text-suave md:block" size={16} aria-hidden="true" />
        <div className="space-y-2">
          <Etapa icone={ShieldCheck} titulo="verificação normativa">
            <span className={`inline-block rounded-md px-2 py-0.5 text-xs ${restr.cor} ${restr.fundo}`}>{restr.texto}</span>
            <p className="mt-1 text-xs text-suave">{d.motivo_restricao}</p>
            <p className="mt-1 text-xs">
              nível emitido: <b className="tabular-nums">{d.nivel_emitido.toFixed(3)}</b>
            </p>
          </Etapa>
          <Etapa icone={Lightbulb} titulo="luz entregue">
            <p className="text-xs">
              medido <b>{lux(d.lux_medido)}</b> · esperado {lux(d.lux_esperado)}
            </p>
          </Etapa>
        </div>
      </div>
    </div>
  );
}

export default function Explicacoes({ eventos, selecionado, setSelecionado }) {
  const [explicacao, setExplicacao] = useState(null);
  const [erro, setErro] = useState(null);

  const atual = selecionado ?? eventos[0]?.id ?? null;

  useEffect(() => {
    if (atual == null) return;
    let vivo = true;
    const buscar = () =>
      api.explicacao(atual)
        .then((x) => vivo && (setExplicacao(x), setErro(null)))
        .catch((e) => vivo && setErro(e.message));
    buscar();
    // A decisao chega logo depois da publicacao: tenta de novo ate aparecer.
    const id = setInterval(buscar, 2000);
    return () => {
      vivo = false;
      clearInterval(id);
    };
  }, [atual]);

  return (
    <div className="grid gap-4 lg:grid-cols-[18rem_1fr]">
      <section className="rounded-xl border border-borda bg-carta p-3">
        <h2 className="mb-2 text-xs font-medium tracking-wide text-suave uppercase">publicações recebidas</h2>
        <ul className="max-h-[32rem] space-y-1 overflow-y-auto text-xs">
          {eventos.map((e) => (
            <li key={e.id}>
              <button
                type="button"
                onClick={() => setSelecionado(e.id)}
                className={`flex w-full items-baseline gap-2 rounded-md px-2 py-1 text-left ${e.id === atual ? "bg-luz/15 text-luz" : "hover:bg-borda/40"}`}
              >
                <span className="tabular-nums text-suave">{hora(e.ocorrido_em)}</span>
                <span className={`font-medium ${e.tipo === "ocorrencia" && e.ocorrencia !== "encerrada" ? "text-falha" : ""}`}>
                  {descreverEvento(e)}
                </span>
                <span className="ml-auto text-suave">trecho {e.trecho}</span>
              </button>
            </li>
          ))}
          {eventos.length === 0 && <li className="py-3 text-center text-suave">nenhuma publicação ainda</li>}
        </ul>
      </section>

      <section className="space-y-3 rounded-xl border border-borda bg-carta p-4">
        {erro && <p className="text-xs text-falha">{erro}</p>}
        {!explicacao && !erro && <p className="text-sm text-suave">escolha uma publicação à esquerda</p>}
        {explicacao && (
          <>
            <div>
              <h2 className="text-base font-semibold">{descreverEvento(explicacao.evento)}</h2>
              <p className="text-xs text-suave">
                {explicacao.trecho_nome ?? "trecho"} (trecho {explicacao.evento.trecho}) · recebida às{" "}
                {hora(explicacao.evento.recebido_em)} · origem {explicacao.evento.origem}
              </p>
            </div>
            {explicacao.decisoes.length === 0 ? (
              <p className="text-sm text-suave">
                Nenhuma luminária do sistema neste trecho: a publicação fica registrada, mas não gera decisão.
              </p>
            ) : (
              explicacao.decisoes.map((d) => <Decisao key={d.ponto} d={d} />)
            )}
          </>
        )}
      </section>
    </div>
  );
}
