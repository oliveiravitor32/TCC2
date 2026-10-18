// Visao de bairro (DIVERGENCIAS 76): os postes do recorte do Jardim Helena no
// mapa, coloridos pelo nivel decidido e pela saude, e os trechos de via pelo
// volume vigente ou pela ocorrencia aberta.
//
// So o BANCADA-01 e um no real; os demais sao SIMULADOS (lux sintetico), so
// para a demonstracao. Os botoes de ocorrencia publicam eventos no POST
// /eventos, como a plataforma faria: nenhum comando sai daqui, e toda decisao
// continua passando pela verificacao normativa do servico.

import { useMemo, useState } from "react";
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { AlertTriangle, ShieldAlert, ShieldCheck } from "lucide-react";
import { RESTRICOES, TERCIS, api, hora, lux } from "../api";

// Nivel decidido -> classe (P3 pleno, P4 uma abaixo, P5 minima) -> tom de azul.
const NIVEIS = [
  { min: 0.95, rotulo: "pleno (P3)", cor: "#1e3a8a" },
  { min: 0.7, rotulo: "uma abaixo (P4)", cor: "#4f78dc" },
  { min: 0, rotulo: "mínima (P5)", cor: "#a9c0f0" },
];
const SEM_DECISAO = "#c4c7d0";
const corNivel = (n) => (n === null || n === undefined ? SEM_DECISAO : NIVEIS.find((x) => n >= x.min).cor);

// Saude do ponto -> borda.
function saude(p) {
  if (p.estado_operacional === "sem_comunicacao") return { cor: "#6b7280", texto: "sem comunicação", tracejado: "3 3" };
  if (p.estado_operacional === "manutencao") return { cor: "#0a0a0a", texto: "em manutenção" };
  if (p.estado_operacional === "falha" || p.alertas_abertos > 0) return { cor: "#c62828", texto: "alerta de diagnóstico" };
  return { cor: "#ffffff", texto: "ok" };
}

// Volume vigente do trecho (normalizado pela regua) -> faixa dos tercis (3.7).
function corTrecho(t) {
  if (t.ocorrencia_aberta) return { cor: "#c62828", texto: "ocorrência aberta" };
  const v = t.nivel_observado;
  if (v === null || v === undefined) return { cor: "#9ca3af", texto: "sem volume vigente" };
  if (v < TERCIS[0]) return { cor: "#86efac", texto: "movimento baixo" };
  if (v < TERCIS[1]) return { cor: "#facc15", texto: "movimento médio" };
  return { cor: "#f97316", texto: "movimento alto" };
}

const latlng = (geo) => (geo?.coordinates ?? []).map(([lon, lat]) => [lat, lon]);

export default function Mapa({ pontos, trechos, aoAbrirPonto, aoPublicar }) {
  const [selecao, setSelecao] = useState(new Set());
  const [grupoEmFoco, setGrupoEmFoco] = useState(null);
  const [enviando, setEnviando] = useState(false);
  const [mensagem, setMensagem] = useState(null);

  const comPosicao = pontos.filter((p) => p.latitude !== null && p.longitude !== null);
  const centro = useMemo(() => {
    if (!comPosicao.length) return [-23.4858, -46.4236];
    const lat = comPosicao.reduce((s, p) => s + p.latitude, 0) / comPosicao.length;
    const lon = comPosicao.reduce((s, p) => s + p.longitude, 0) / comPosicao.length;
    return [lat, lon];
  }, [comPosicao.length]); // eslint-disable-line react-hooks/exhaustive-deps

  const tamanhoGrupo = useMemo(() => {
    const m = new Map();
    for (const p of pontos) if (p.grupo_id !== null) m.set(p.grupo_id, (m.get(p.grupo_id) ?? 0) + 1);
    return m;
  }, [pontos]);

  const resumo = useMemo(() => {
    const r = { pleno: 0, p4: 0, p5: 0, semDecisao: 0, alertas: 0, simulados: 0 };
    for (const p of pontos) {
      if (p.simulado) r.simulados += 1;
      if (p.alertas_abertos > 0 || p.estado_operacional === "falha") r.alertas += 1;
      const n = p.nivel_emitido;
      if (n === null || n === undefined) r.semDecisao += 1;
      else if (n >= 0.95) r.pleno += 1;
      else if (n >= 0.7) r.p4 += 1;
      else r.p5 += 1;
    }
    return r;
  }, [pontos]);

  const alternar = (id) =>
    setSelecao((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  async function publicarOcorrencia(tipo) {
    if (!selecao.size) return;
    setEnviando(true);
    setMensagem(null);
    const agora = new Date().toISOString();
    const pacote = [...selecao].map((trecho) => ({
      ocorrido_em: agora, tipo: "ocorrencia", ocorrencia: tipo, trecho, origem: "painel-mapa",
    }));
    try {
      const r = await api.publicarLeitura(pacote);
      setMensagem(`${r.aceitos.length} trecho(s) publicados${r.recusados.length ? `, ${r.recusados.length} recusado(s)` : ""}. A decisão sai do serviço, verificada contra a norma.`);
      aoPublicar?.();
    } catch (e) {
      setMensagem(`não publicado: ${e.message}`);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_20rem]">
      <section className="self-start border border-borda bg-carta">
        <div className="h-[60vh] min-h-[22rem] w-full">
          <MapContainer center={centro} zoom={18} scrollWheelZoom className="h-full w-full">
            <TileLayer
              url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              maxZoom={19}
            />
            {trechos.filter((t) => t.geometria_wgs84).map((t) => {
              const c = corTrecho(t);
              const sel = selecao.has(t.id);
              return (
                <Polyline
                  key={`${t.id}-${sel}-${c.cor}`}
                  positions={latlng(t.geometria_wgs84)}
                  pathOptions={{ color: c.cor, weight: sel ? 11 : 7, opacity: 0.9, dashArray: sel ? "2 8" : null }}
                  eventHandlers={{ click: () => alternar(t.id) }}
                >
                  <Tooltip sticky>
                    {t.tipo_logradouro ?? ""} {t.nome_logradouro} ({t.numero_inicial}–{t.numero_final}) · {c.texto}
                    {sel ? " · selecionado" : " · clique para selecionar"}
                  </Tooltip>
                </Polyline>
              );
            })}
            {comPosicao.map((p) => {
              const s = saude(p);
              const real = !p.simulado;
              const foco = grupoEmFoco !== null && p.grupo_id === grupoEmFoco;
              return (
                <CircleMarker
                  key={`${p.codigo}-${p.nivel_emitido}-${s.cor}-${foco}`}
                  center={[p.latitude, p.longitude]}
                  radius={real ? 11 : foco ? 9 : 7}
                  pathOptions={{
                    fillColor: corNivel(p.nivel_emitido), fillOpacity: 1,
                    color: foco ? "#0a0a0a" : s.cor, weight: real || foco ? 4 : 3, dashArray: s.tracejado,
                  }}
                  eventHandlers={{
                    click: () => aoAbrirPonto?.(p.codigo),
                    mouseover: () => setGrupoEmFoco(p.grupo_id),
                    mouseout: () => setGrupoEmFoco(null),
                  }}
                >
                  <Tooltip direction="top" offset={[0, -8]}>
                    <strong>{p.codigo}</strong> {p.codigo === "BANCADA-01" ? "· nó real" : "· simulado"}
                    <br />poste {p.placa ?? "--"} · grupo {p.grupo_id ?? "--"} ({tamanhoGrupo.get(p.grupo_id) ?? 1} poste(s))
                    <br />nível {p.nivel_emitido ?? "--"} · {RESTRICOES[p.restricao_aplicada]?.texto ?? "sem decisão"}
                    <br />luz {lux(p.lux_medido)} · {s.texto} · {hora(p.decidido_em)}
                    <br />clique para abrir o monitoramento
                  </Tooltip>
                </CircleMarker>
              );
            })}
          </MapContainer>
        </div>
        <p className="border-t border-borda px-3 py-2 text-xs text-suave">
          Marcadores maiores: os pontos do trabalho (<strong>BANCADA-01</strong>, o nó real, e SIMULADO-02). Os
          outros {resumo.simulados} postes do recorte são <strong>simulados</strong>, com luz sintética, só para
          mostrar o bairro: não compõem nenhum resultado. Passe o mouse num poste para ver o seu grupo de controle.
        </p>
      </section>

      <aside className="flex flex-col gap-4">
        <section className="border border-borda bg-carta p-4">
          <h2 className="mb-2 border-l-4 border-luz pl-2 text-xs font-bold tracking-wide text-luz uppercase">recorte</h2>
          <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-sm">
            <dt className="text-suave">postes</dt><dd className="text-right font-semibold">{pontos.length}</dd>
            <dt className="text-suave">no pleno (P3)</dt><dd className="text-right font-semibold">{resumo.pleno}</dd>
            <dt className="text-suave">uma abaixo (P4)</dt><dd className="text-right font-semibold">{resumo.p4}</dd>
            <dt className="text-suave">na mínima (P5)</dt><dd className="text-right font-semibold">{resumo.p5}</dd>
            <dt className="text-suave">sem decisão</dt><dd className="text-right font-semibold">{resumo.semDecisao}</dd>
            <dt className="text-suave">grupos de controle</dt><dd className="text-right font-semibold">{tamanhoGrupo.size}</dd>
            <dt className="text-suave">com alerta</dt>
            <dd className={`text-right font-semibold ${resumo.alertas ? "text-falha" : ""}`}>{resumo.alertas}</dd>
          </dl>
        </section>

        <section className="border border-borda bg-carta p-4">
          <h2 className="mb-2 border-l-4 border-luz pl-2 text-xs font-bold tracking-wide text-luz uppercase">ocorrência em área</h2>
          <p className="mb-3 text-xs text-suave">
            Clique nos trechos de rua para selecionar ({selecao.size} selecionado(s)). Os botões publicam a ocorrência
            como a plataforma faria; o serviço decide e verifica.
          </p>
          <div className="flex flex-wrap gap-2">
            <button type="button" disabled={!selecao.size || enviando || !api.podePublicar}
              onClick={() => publicarOcorrencia("seguranca")}
              className="inline-flex items-center gap-1 bg-falha px-3 py-1.5 text-xs font-semibold text-white uppercase tracking-wide disabled:opacity-40">
              <ShieldAlert size={14} /> abrir ocorrência
            </button>
            <button type="button" disabled={!selecao.size || enviando || !api.podePublicar}
              onClick={() => publicarOcorrencia("encerrada")}
              className="inline-flex items-center gap-1 border border-borda px-3 py-1.5 text-xs font-semibold uppercase tracking-wide hover:border-luz disabled:opacity-40">
              <ShieldCheck size={14} /> encerrar
            </button>
            {selecao.size > 0 && (
              <button type="button" onClick={() => setSelecao(new Set())} className="px-2 text-xs text-suave underline">
                limpar seleção
              </button>
            )}
          </div>
          {!api.podePublicar && (
            <p className="mt-2 flex items-center gap-1 text-xs text-falha"><AlertTriangle size={12} /> painel sem chave de publicação</p>
          )}
          {mensagem && <p className="mt-2 text-xs">{mensagem}</p>}
        </section>

        <section className="border border-borda bg-carta p-4 text-xs">
          <h2 className="mb-2 border-l-4 border-luz pl-2 font-bold tracking-wide text-luz uppercase">legenda</h2>
          <p className="mb-1 font-semibold">postes: preenchimento = nível decidido</p>
          <ul className="mb-2 space-y-1">
            {NIVEIS.map((n) => (
              <li key={n.rotulo} className="flex items-center gap-2"><span className="inline-block h-3 w-3" style={{ background: n.cor }} />{n.rotulo}</li>
            ))}
            <li className="flex items-center gap-2"><span className="inline-block h-3 w-3" style={{ background: SEM_DECISAO }} />sem decisão</li>
          </ul>
          <p className="mb-1 font-semibold">postes: borda = saúde</p>
          <ul className="mb-2 space-y-1">
            <li className="flex items-center gap-2"><span className="inline-block h-3 w-3 border-2" style={{ borderColor: "#c62828" }} />alerta de diagnóstico</li>
            <li className="flex items-center gap-2"><span className="inline-block h-3 w-3 border-2 border-dashed" style={{ borderColor: "#6b7280" }} />sem comunicação</li>
          </ul>
          <p className="mb-1 font-semibold">ruas: volume vigente</p>
          <ul className="space-y-1">
            {[["#86efac", "baixo"], ["#facc15", "médio"], ["#f97316", "alto"], ["#c62828", "ocorrência aberta"], ["#9ca3af", "sem volume (pleno)"]].map(([c, t]) => (
              <li key={t} className="flex items-center gap-2"><span className="inline-block h-1.5 w-5" style={{ background: c }} />{t}</li>
            ))}
          </ul>
        </section>
      </aside>
    </div>
  );
}
