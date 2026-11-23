// Trajetoria do nivel ao longo do tempo (RF08).
//
// O no so responde a cada comando (uma telemetria por decisao, 3.13.2) e
// executa a rampa sozinho entre um comando e outro (DIVERGENCIAS 71). Por
// isso a linha azul e o nivel ESPERADO no no, refeito aqui com a mesma regra
// do controlador (decisao/rampa.py, firmware/no/no.ino): sobe na hora, desce
// em passos de 5 s no maximo a taxa da classe, nunca abaixo do piso, e volta
// ao pleno quando a validade vence sem renovacao.
//
// Os pontos sao MEDICAO, para conferir a conta:
//   - cheio: iluminancia "antes do comando" - onde o no estava de fato quando
//     o comando seguinte chegou, ou seja, o fim de cada trecho da linha;
//   - vazado: a primeira leitura depois do comando (mostra a subida imediata).
//
// SVG a mao, sem biblioteca de grafico.

import { useEffect, useRef, useState } from "react";

import { CaixaDica, hora, useDica } from "./Dica";
import { RESTRICOES, api } from "../api";

const M = { esq: 38, dir: 12, topo: 12, base: 22 };
const L = 720;
const A = 240;
const PASSO_S = 5;
// Janelas de visualizacao (h). 1 h e 6 h usam as decisoes que o painel ja
// busca a cada 2 s; 24 h e 7 d buscam por TEMPO (desde agora - janela), a
// cada 30 s: com a frota decidindo a cada 5 min, 7 d sao ~2.000 decisoes,
// pesado demais para buscar a cada 2 s, e nessa escala 2 s nao muda nada.
const JANELAS = [[1, "1 h"], [6, "6 h"], [24, "24 h"], [168, "7 d"]];
const JANELA_PROPRIA_H = 24; // a partir daqui a trajetoria busca os proprios dados
const PERIODO_LONGO_MS = 30000;
// Margem antes da janela: a ultima decisao anterior a ela define de onde o
// nivel parte (a validade do comando vai ate 15 min).
const MARGEM_MS = 20 * 60e3;
const LIMITE_API = 5000;
// Espacamento padrao: uma largura de tela mostra no maximo 12 h, e cada
// MUDANCA de nivel ganha pelo menos ESPACO_COMANDO unidades (de L = 720). Quando nao
// cabe, o grafico fica mais largo que a caixa e rola para os lados (arrastar
// com o mouse ou a barra de rolagem). Vale para todos os filtros: 7 d fica
// com 14 telas; uma hora com muitas mudancas tambem alarga.
const HORAS_POR_TELA = 12;
const ESPACO_COMANDO = 14;
const MAX_ZOOM = 60;
// Intervalo das marcas de tempo: o menor que deixe ~4 marcas por tela.
const PASSOS_MARCA_MIN = [5, 10, 15, 30, 60, 120, 180, 360];
const dataCurta = (ms) =>
  new Date(ms).toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "2-digit" });

// Busca decisoes e telemetria do ponto por tempo, para as janelas longas.
function useHistorico(ponto, horas) {
  const [dados, setDados] = useState(null);
  useEffect(() => {
    setDados(null);
    if (!ponto || horas < JANELA_PROPRIA_H) return undefined;
    let vivo = true;
    const buscar = async () => {
      const inicio = new Date(Date.now() - horas * 3600e3 - MARGEM_MS).toISOString();
      try {
        const [decisoes, telemetria] = await Promise.all([
          api.decisoes({ ponto, inicio, limite: LIMITE_API }),
          api.telemetria({ ponto, inicio, limite: LIMITE_API }),
        ]);
        if (vivo) setDados({ decisoes, telemetria });
      } catch {
        // mantem o ultimo historico; o painel ja mostra o erro da API
      }
    };
    buscar();
    const id = setInterval(buscar, PERIODO_LONGO_MS);
    return () => { vivo = false; clearInterval(id); };
  }, [ponto, horas]);
  return dados;
}

function caminho(pontos) {
  return pontos.length ? "M" + pontos.map((p) => `${p.x},${p.y}`).join(" L") : "";
}

const tresCasas = (v) => Math.round(v * 1000) / 1000;

// Nivel esperado no no de `ini` a `fim` (ms), a partir dos comandos
// publicados em ordem crescente. Devolve os vertices da linha (degraus da
// rampa incluidos) e uma funcao que da o nivel num instante.
function simular(comandos, ini, fim, nivelInicial) {
  const pts = [];
  let nivel = nivelInicial;
  let t = ini;
  let cmd = null;
  let recebido = 0;
  let proximoPasso = Infinity;
  const marcar = (tt) => pts.push({ t: tt, v: nivel });
  marcar(t);

  const avancar = (ate) => {
    while (t < ate) {
      const vence = cmd ? recebido + cmd.validade_s * 1000 : Infinity;
      const prox = Math.min(ate, proximoPasso, vence);
      t = prox;
      if (cmd && t >= vence) {
        // Failsafe (RNF07): comando vencido, volta ao pleno.
        marcar(t);
        nivel = 1;
        marcar(t);
        cmd = null;
        proximoPasso = Infinity;
      } else if (t === proximoPasso) {
        const alvo = Math.max(cmd.nivel_emitido, cmd.piso ?? 0);
        if (nivel > alvo) {
          const queda = Math.floor(((cmd.taxa_min ?? 0.1) * PASSO_S) / 60 * 1000 + 1e-3) / 1000;
          marcar(t);
          nivel = tresCasas(Math.max(alvo, nivel - queda));
          marcar(t);
        }
        proximoPasso += PASSO_S * 1000;
      }
    }
  };

  const esperadoEm = new Map();
  for (const c of comandos) {
    const tc = new Date(c.publicado_em).getTime();
    if (tc > fim) break;
    if (tc >= ini) avancar(tc);
    esperadoEm.set(c.id, nivel); // onde o no deveria estar ao receber
    cmd = c;
    recebido = Math.max(tc, ini);
    proximoPasso = recebido + PASSO_S * 1000;
    if (c.entrada?.teste_imediato) {
      // Modo de teste do painel: vai direto ao alvo (sem rampa), acima do piso.
      marcar(recebido);
      nivel = Math.max(c.nivel_emitido, c.piso ?? 0);
      marcar(recebido);
    } else if (c.nivel_emitido >= nivel) {
      // Subir e livre e imediato.
      marcar(recebido);
      nivel = c.nivel_emitido;
      marcar(recebido);
    }
  }
  avancar(fim);
  marcar(fim);
  return { pts, esperadoEm };
}

export default function Trajetoria({ ponto, decisoes: decisoesPainel, telemetria: telemetriaPainel,
                                     piso, luxPleno }) {
  // As consultas vem em ordem decrescente; aqui o tempo corre para a direita.
  const [janela, setJanela] = useState(1);
  const historico = useHistorico(ponto, janela);
  const longa = janela >= JANELA_PROPRIA_H;
  const decisoes = longa ? historico?.decisoes ?? [] : decisoesPainel;
  const telemetria = longa ? historico?.telemetria ?? [] : telemetriaPainel;
  const corte = Date.now() - janela * 3600e3;
  // So as MUDANCAS de nivel pedem espaco: renovacao do mesmo nivel e linha reta.
  const nMudancas = decisoes.filter((d) => d.publicado_em && new Date(d.publicado_em).getTime() >= corte
    && d.nivel_anterior != null && Math.abs(d.nivel_emitido - d.nivel_anterior) > 1e-6).length;
  const zoom = Math.min(MAX_ZOOM, Math.max(1, janela / HORAS_POR_TELA, (nMudancas * ESPACO_COMANDO) / L));
  const passoMarca = PASSOS_MARCA_MIN.find((m) => m >= (janela * 60) / zoom / 4) ?? 360;
  const LV = L * zoom; // largura logica do grafico

  // Arrastar para os lados (so no grafico largo).
  const rolagem = useRef(null);
  const arrasto = useRef(null);
  const [arrastando, setArrastando] = useState(false);
  const aoApertar = (ev) => {
    if (zoom === 1 || !rolagem.current) return;
    arrasto.current = { x: ev.clientX, inicio: rolagem.current.scrollLeft };
    setArrastando(true);
  };
  const aoMover = (ev) => {
    if (!arrasto.current || !rolagem.current) return;
    rolagem.current.scrollLeft = arrasto.current.inicio - (ev.clientX - arrasto.current.x);
  };
  const aoSoltar = () => { arrasto.current = null; setArrastando(false); };
  // Ao trocar o filtro (ou chegar o historico, ou o grafico passar a rolar),
  // comeca no fim: o agora.
  const carregou = Boolean(historico);
  const rola = zoom > 1;
  useEffect(() => {
    if (rola && rolagem.current) rolagem.current.scrollLeft = rolagem.current.scrollWidth;
  }, [janela, carregou, rola]);
  // Posicao da rolagem (fracao da largura), para saber que dia esta na borda esquerda.
  const [rolado, setRolado] = useState(1);
  const aoRolar = (ev) => {
    const el = ev.currentTarget;
    setRolado(el.scrollWidth ? el.scrollLeft / el.scrollWidth : 0);
  };
  // Series visiveis; clicar na legenda esconde ou mostra cada uma.
  const [ocultas, setOcultas] = useState(() => new Set());
  const ver = (k) => !ocultas.has(k);
  const alternar = (k) => setOcultas((o) => {
    const n = new Set(o);
    if (n.has(k)) n.delete(k); else n.add(k);
    return n;
  });
  const serie = [...decisoes].reverse();
  const todos = serie.filter((d) => d.publicado_em && d.validade_s);
  const tIni = serie.length ? new Date(serie[0].criado_em).getTime() : 0;
  const t1 = Math.max(serie.length ? new Date(serie[serie.length - 1].criado_em).getTime() : 0,
                      Date.now());
  const t0 = Math.max(tIni, t1 - janela * 3600e3);
  const naJanela = (iso) => new Date(iso).getTime() >= t0;
  const comandos = todos.filter((d) => naJanela(d.publicado_em));
  const span = Math.max(t1 - t0, 1000);
  const xt = (ms) => M.esq + ((ms - t0) / span) * (LV - M.esq - M.dir);
  const x = (iso) => xt(new Date(iso).getTime());
  // Instante na borda esquerda da parte visivel (sem rolagem: o inicio).
  // O eixo y fica parado por cima dos primeiros M.esq: a borda visivel do
  // grafico comeca logo depois dele, nao no inicio da rolagem.
  const xBorda = rola ? rolado * LV + M.esq : 0;
  const diaNaBorda = t0 + Math.max(0, (xBorda - M.esq) / (LV - M.esq - M.dir)) * span;
  const dica = useDica(comandos.map((d) => x(d.publicado_em)), LV);

  const botoes = (
    <div className="mb-1 flex justify-end gap-1 text-xs">
        {JANELAS.map(([h, rotulo]) => (
          <button key={rotulo} type="button" onClick={() => setJanela(h)}
                  className={`px-2 py-0.5 ${janela === h ? "bg-luz text-white" : "text-suave hover:text-texto"}`}>
            {rotulo}
          </button>
        ))}
    </div>
  );

  if (serie.length < 2) {
    return (
      <div>
        {botoes}
        <div className="flex h-60 items-center justify-center text-sm text-suave">
          {longa && !historico ? "carregando o histórico..." : "aguardando decisões para desenhar a trajetória..."}
        </div>
      </div>
    );
  }

  const y = (v) => M.topo + (1 - Math.min(Math.max(v, 0), 1)) * (A - M.topo - M.base);
  const porDecisao = new Map(telemetria.map((t) => [t.decisao_id, t]));

  // Ponto de partida: o "antes" medido no primeiro comando da janela, ou o
  // nivel anterior registrado na decisao; sem nada, o pleno (o no liga no pleno).
  const primeiro = todos[0];
  const inicial = primeiro
    ? porDecisao.get(primeiro.id)?.nivel_antes ?? primeiro.nivel_anterior ?? 1
    : serie[0].nivel_emitido;
  // Simula desde a primeira decisao carregada e mostra so a janela escolhida.
  const { pts, esperadoEm } = simular(todos, tIni, t1, inicial);
  const esperado = pts.filter((p, i) => p.t >= t0 || pts[i + 1]?.t >= t0)
    .map((p) => ({ x: xt(Math.max(p.t, t0)), y: y(p.v) }));
  const pretendido = serie.filter((d) => naJanela(d.criado_em))
    .map((d) => ({ x: x(d.criado_em), y: y(d.nivel_pretendido) }));

  const antes = [];
  const depois = [];
  for (const d of comandos) {
    const t = porDecisao.get(d.id);
    if (!t) continue;
    if (t.lux_antes != null) antes.push({ x: x(d.publicado_em), y: y(t.lux_antes / luxPleno) });
    if (t.lux_medido != null) depois.push({ x: x(t.medido_em), y: y(t.lux_medido / luxPleno) });
  }

  const sel = dica.i != null ? comandos[dica.i] : null;
  const tSel = sel ? porDecisao.get(sel.id) : null;
  const espSel = sel ? esperadoEm.get(sel.id) : null;
  const lx = (v) => (v != null ? `${v.toFixed(2)} lx` : "--");
  const dif = (med, esp) =>
    med != null && esp ? `${(((med - esp) / esp) * 100).toFixed(1)}%` : "--";

  return (
    <figure className="relative w-full">
      {botoes}
      <div className="mb-1 flex items-baseline justify-between gap-3">
        {/* Dia dos registros na borda esquerda; muda ao passar pela meia-noite. */}
        <p className="text-sm font-bold text-texto">{dataCurta(diaNaBorda)}</p>
        {zoom > 1 && (
          <p className="text-right text-[11px] text-suave">
            arraste o gráfico para os lados (ou use a barra de rolagem) para ver o resto do período
          </p>
        )}
      </div>
      <div className="relative">
      <div ref={rolagem} className={zoom > 1 ? "overflow-x-auto" : ""} onScroll={aoRolar}
           onMouseDown={aoApertar} onMouseMove={aoMover} onMouseUp={aoSoltar} onMouseLeave={aoSoltar}>
      <div className="relative select-none" style={{ width: `${zoom * 100}%` }}>
      {sel && (
        <CaixaDica
          x={x(sel.publicado_em)} L={LV}
          titulo={`comando às ${hora(sel.publicado_em)}`}
          linhas={[
            ["antes: esperado", espSel != null ? lx(espSel * luxPleno) : "--", "var(--color-luz)"],
            ["antes: medido", tSel ? lx(tSel.lux_antes) : "sem resposta", "var(--color-ok)"],
            ["diferença", tSel ? dif(tSel.lux_antes, espSel * luxPleno) : "--"],
            ["novo alvo", sel.nivel_emitido.toFixed(3)],
            ["pretendido", sel.nivel_pretendido.toFixed(3), "var(--color-suave)"],
            ["verificação", RESTRICOES[sel.restricao_aplicada]?.texto ?? sel.restricao_aplicada],
            ["após o comando", tSel ? lx(tSel.lux_medido) : "--"],
            ["validade", `${sel.validade_s} s`],
          ]}
        />
      )}
      <svg viewBox={`0 0 ${LV} ${A}`}
           className={`block w-full ${zoom > 1 ? (arrastando ? "cursor-grabbing" : "cursor-grab") : "cursor-crosshair"}`}
           role="img"
           aria-label="Trajetória do nível de iluminação" {...dica.eventos}>
        {[0, 0.25, 0.5, 0.75, 1].map((v) => (
          <g key={v}>
            <line x1={M.esq} x2={LV - M.dir} y1={y(v)} y2={y(v)}
                  stroke="var(--color-borda)" strokeWidth="1" />
            {zoom === 1 && <text x={M.esq - 6} y={y(v) + 4} textAnchor="end" fontSize="10"
                  fill="var(--color-suave)">
              {v.toFixed(2)}
            </text>}
          </g>
        ))}

        {/* Marcas de tempo; a meia-noite (troca de dia) em negrito, com a data. */}
        {marcas(t0, t1, passoMarca).map((ms) => {
          const d = new Date(ms);
          const meiaNoite = d.getHours() === 0 && d.getMinutes() === 0;
          return (
            <g key={ms}>
              <line x1={xt(ms)} x2={xt(ms)} y1={M.topo} y2={A - M.base}
                    stroke={meiaNoite ? "var(--color-texto)" : "var(--color-borda)"}
                    strokeWidth={meiaNoite ? 1.5 : 0.5} />
              <text x={xt(ms)} y={A - 6} fontSize="10"
                    textAnchor={xt(ms) > LV - 60 ? "end" : xt(ms) < M.esq + 60 ? "start" : "middle"}
                    fontWeight={meiaNoite ? "bold" : "normal"}
                    fill={meiaNoite ? "var(--color-texto)" : "var(--color-suave)"}>
                {meiaNoite
                  ? dataCurta(ms)
                  : d.getMinutes()
                    ? d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
                    : `${String(d.getHours()).padStart(2, "0")}h`}
              </text>
            </g>
          );
        })}

        {/* Piso da classe: o limite que a verificacao nao deixa cruzar. */}
        {ver("piso") && (
          <>
            <line x1={M.esq} x2={LV - M.dir} y1={y(piso)} y2={y(piso)}
                  stroke="var(--color-piso)" strokeWidth="1.5" strokeDasharray="6 4" />
            <text x={LV - M.dir} y={y(piso) - 5} textAnchor="end" fontSize="10"
                  fill="var(--color-piso)">
              piso P5
            </text>
          </>
        )}

        {ver("pretendido") && (
          <path d={caminho(pretendido)} fill="none" stroke="var(--color-suave)"
                strokeWidth="1.5" strokeDasharray="4 4" />
        )}
        {ver("esperado") && (
          <path d={caminho(esperado)} fill="none" stroke="var(--color-luz)" strokeWidth="2.5" />
        )}
        {ver("depois") && depois.map((p, i) => (
          <circle key={`d${i}`} cx={p.x} cy={p.y} r="2.5" fill="var(--color-carta)"
                  stroke="var(--color-ok)" strokeWidth="1.2" />
        ))}
        {ver("antes") && antes.map((p, i) => (
          <circle key={`a${i}`} cx={p.x} cy={p.y} r="3" fill="var(--color-ok)" />
        ))}
        {sel && (
          <g pointerEvents="none">
            <line x1={x(sel.publicado_em)} x2={x(sel.publicado_em)} y1={M.topo} y2={A - M.base}
                  stroke="var(--color-suave)" strokeWidth="1" strokeDasharray="3 3" />
            {espSel != null && (
              <circle cx={x(sel.publicado_em)} cy={y(espSel)} r="4" fill="none"
                      stroke="var(--color-luz)" strokeWidth="2" />
            )}
          </g>
        )}
        {/* area transparente para o mouse funcionar em todo o grafico */}
        <rect x="0" y="0" width={LV} height={A} fill="transparent" />
      </svg>
      </div>
      </div>
      {/* Grafico largo: o eixo y fica parado na esquerda enquanto o resto rola. */}
      {zoom > 1 && (
        <svg viewBox={`0 0 ${M.esq} ${A}`} className="pointer-events-none absolute left-0 top-0 bg-carta"
             style={{ width: `${(M.esq / L) * 100}%` }} aria-hidden="true">
          {[0, 0.25, 0.5, 0.75, 1].map((v) => (
            <text key={v} x={M.esq - 6} y={y(v) + 4} textAnchor="end" fontSize="10"
                  fill="var(--color-suave)">
              {v.toFixed(2)}
            </text>
          ))}
        </svg>
      )}
      </div>

      <figcaption className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-suave">
        {[
          ["pretendido", { cor: "var(--color-suave)", tracejado: true }, "nível pretendido (inferência)"],
          ["esperado", { cor: "var(--color-luz)" }, "nível esperado no nó (calculado pela rampa)"],
          ["antes", { cor: "var(--color-ok)", ponto: true }, `medido antes do comando / ${luxPleno} lx`],
          ["depois", { cor: "var(--color-ok)", ponto: true, vazado: true }, "medido logo após o comando"],
          ["piso", { cor: "var(--color-piso)", tracejado: true }, "piso da classe"],
        ].map(([k, estilo, texto]) => (
          <Legenda key={k} {...estilo} ativa={ver(k)} aoClicar={() => alternar(k)}>
            {texto}
          </Legenda>
        ))}
      </figcaption>
    </figure>
  );
}

// Instantes redondos a cada `passoMin` minutos (no fuso do navegador) entre t0 e t1.
function marcas(t0, t1, passoMin) {
  const d = new Date(t0);
  d.setHours(0, 0, 0, 0);
  const out = [];
  for (let ms = d.getTime(); ms <= t1; ms += passoMin * 60e3) if (ms >= t0) out.push(ms);
  return out;
}

function Legenda({ cor, tracejado, ponto, vazado, ativa, aoClicar, children }) {
  return (
    <button type="button" onClick={aoClicar} aria-pressed={ativa}
            title={ativa ? "clique para esconder" : "clique para mostrar"}
            className={`inline-flex items-center gap-2 hover:text-texto ${ativa ? "" : "line-through opacity-40"}`}>
      <svg width="22" height="8" aria-hidden="true">
        {ponto ? (
          <circle cx="11" cy="4" r="2.5" fill={vazado ? "none" : cor} stroke={cor} />
        ) : (
          <line x1="0" y1="4" x2="22" y2="4" stroke={cor} strokeWidth="2"
                strokeDasharray={tracejado ? "4 3" : undefined} />
        )}
      </svg>
      {children}
    </button>
  );
}
