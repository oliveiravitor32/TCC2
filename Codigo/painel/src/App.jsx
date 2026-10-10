// Painel de acompanhamento (TCC 4.6.1, RF08).
//
// Le o historico pela interface REST e exibe, lado a lado, o dado recebido,
// o nivel pretendido pela inferencia, a correcao imposta pela camada de
// verificacao e a iluminancia medida - a cadeia que 4.6 chama de "a
// interface pela qual a conformidade normativa se torna observavel".
//
// O painel nao comanda nada nem decide nada. A unica escrita e a do modal de
// demonstracao, que publica o volume ou a ocorrencia de um trecho como a
// plataforma de monitoramento publicaria (DIVERGENCIAS 55 e 56); a decisao
// continua no servico.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CircleDot, FlaskConical, Lightbulb, Pause, Play, RefreshCw, WifiOff } from "lucide-react";
import { ESTADOS, api, hora } from "./api";
import { Entregue, EstadoDaVia, Inferencia, Verificacao } from "./componentes/Cartoes";
import { Alertas, Decisoes, Eventos } from "./componentes/Listas";
import Energia from "./componentes/Energia";
import Trajetoria from "./componentes/Trajetoria";
import SimularLeitura from "./componentes/SimularLeitura";
import Explicacoes from "./componentes/Explicacoes";

const PERIODO_MS = 2000; // metade do ciclo de decisao (5 s), sem afoga-lo
const JANELA = 240; // decisoes exibidas na trajetoria
const JANELA_ENERGIA_MIN = 30; // minutos integrados no cartao de consumo

export default function App() {
  const [dados, setDados] = useState({
    pontos: [], decisoes: [], telemetria: [], eventos: [], todosEventos: [], alertas: [], energia: null,
  });
  const [trechos, setTrechos] = useState([]);
  const [aba, setAba] = useState("monitoramento");
  const [modalAberto, setModalAberto] = useState(false);
  const [eventoExplicado, setEventoExplicado] = useState(null);
  const [erro, setErro] = useState(null);
  const [rodando, setRodando] = useState(true);
  const [atualizadoEm, setAtualizadoEm] = useState(null);
  // Ponto de luz exibido. Cada ponto tem os proprios trechos de via
  // (DIVERGENCIAS 54): decisoes, telemetria e eventos sao filtrados por ele.
  const [selecionado, setSelecionado] = useState(null);
  const carregando = useRef(false);

  const buscar = useCallback(async () => {
    if (carregando.current) return; // nao empilha requisicao lenta
    carregando.current = true;
    try {
      const pontos = await api.pontos();
      const atual = pontos.find((p) => p.codigo === selecionado) ?? pontos[0];
      const ponto = atual?.codigo;
      const [decisoes, telemetria, todosEventos, todosAlertas, energia] = await Promise.all([
        api.decisoes({ ponto, limite: JANELA }),
        api.telemetria({ ponto, limite: JANELA }),
        api.eventos({ limite: 200 }),
        api.alertas({ abertos: true }),
        api.energia({ ponto, janela_min: JANELA_ENERGIA_MIN }),
      ]);
      // So os eventos dos trechos deste ponto: sao os que a decisao dele viu.
      const trechos = new Set(atual?.trechos ?? []);
      const eventos = todosEventos.filter((e) => trechos.has(e.trecho));
      const alertas = todosAlertas.filter((a) => a.ponto === ponto);
      setDados({ pontos, decisoes, telemetria, eventos, todosEventos, alertas, energia });
      setAtualizadoEm(new Date());
      setErro(null);
    } catch (e) {
      setErro(e.message);
    } finally {
      carregando.current = false;
    }
  }, [selecionado]);

  // Trechos de via: mudam so com o cadastro, basta buscar uma vez.
  useEffect(() => {
    api.trechos().then(setTrechos).catch(() => setTrechos([]));
  }, []);

  useEffect(() => {
    buscar();
    if (!rodando) return;
    const id = setInterval(buscar, PERIODO_MS);
    return () => clearInterval(id);
  }, [buscar, rodando]);

  const ponto = dados.pontos.find((p) => p.codigo === selecionado) ?? dados.pontos[0];
  const decisao = dados.decisoes[0];
  const piso = ponto?.piso_fracao ?? null;

  const latenciaMs = useMemo(() => {
    const t = dados.telemetria.find((x) => x.decisao_id === decisao?.id);
    if (!t || !decisao) return null;
    return Math.max(
      0,
      Math.round(new Date(t.recebido_em) - new Date(decisao.criado_em)),
    );
  }, [dados.telemetria, decisao]);

  const estado = ESTADOS[ponto?.estado_operacional] ?? ESTADOS.sem_comunicacao;

  return (
    <div className="flex min-h-full flex-col">
      <header className="w-full bg-tinta text-white">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-x-5 gap-y-3 px-4 py-4 text-center sm:px-6">
        <h1 className="flex items-center gap-2 text-lg font-bold tracking-tight">
          <Lightbulb size={20} className="text-luz" aria-hidden="true" />
          Iluminação adaptativa
        </h1>
        <span className="text-xs text-white/70">
          {ponto
            ? `${ponto.codigo}${ponto.placa ? ` (poste ${ponto.placa})` : ""} · classe ${ponto.classe_codigo} · pleno ${ponto.lux_pleno} lx`
            : "sem ponto de luz"}
        </span>
        {dados.pontos.length > 1 && (
          <label className="inline-flex items-center gap-1 text-xs text-white/70">
            ponto
            <select
              value={ponto?.codigo ?? ""}
              onChange={(e) => setSelecionado(e.target.value)}
              className="border border-white/30 bg-tinta px-2 py-1 text-white hover:border-luz"
            >
              {dados.pontos.map((p) => (
                <option key={p.codigo} value={p.codigo}>
                  {p.codigo} · {p.logradouro ?? "sem endereço"}
                </option>
              ))}
            </select>
          </label>
        )}
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold text-white uppercase tracking-wide ${estado.cor.replace("text-", "bg-")}`}>
          <CircleDot size={12} aria-hidden="true" />
          {estado.texto}
        </span>

        <div className="flex flex-wrap items-center justify-center gap-3 text-xs text-white/70">
          <button
            type="button"
            onClick={() => setModalAberto(true)}
            className="inline-flex items-center gap-1 bg-luz px-3 py-1.5 font-semibold text-white uppercase tracking-wide transition-colors hover:bg-white hover:text-tinta"
          >
            <FlaskConical size={14} />
            simular publicação
          </button>
          <span>atualizado {hora(atualizadoEm?.toISOString())}</span>
          <button
            type="button"
            onClick={() => setRodando((v) => !v)}
            className="inline-flex items-center gap-1 border border-white/30 px-2 py-1 text-white transition-colors hover:border-luz hover:bg-luz"
          >
            {rodando ? <Pause size={12} /> : <Play size={12} />}
            {rodando ? "pausar" : "retomar"}
          </button>
          <button
            type="button"
            onClick={buscar}
            className="inline-flex items-center gap-1 border border-white/30 px-2 py-1 text-white transition-colors hover:border-luz hover:bg-luz"
          >
            <RefreshCw size={12} />
            atualizar
          </button>
        </div>
      </div>
      </header>

      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-4 p-4 sm:p-6">

      {erro && (
        <p className="flex items-center gap-2 border-l-4 border-falha bg-falha/10 p-3 text-sm text-falha">
          <WifiOff size={16} aria-hidden="true" />
          sem resposta da interface de dados ({erro}). Os valores abaixo são os últimos
          recebidos e podem estar desatualizados.
        </p>
      )}

      <nav className="flex gap-1 border-b border-borda text-sm" aria-label="visões do painel">
        {[
          { id: "monitoramento", rotulo: "monitoramento" },
          { id: "explicacoes", rotulo: "decisões explicadas" },
        ].map((a) => (
          <button
            key={a.id}
            type="button"
            onClick={() => setAba(a.id)}
            className={`-mb-px border-b-[3px] px-3 py-2 font-semibold tracking-wide uppercase transition-colors ${aba === a.id ? "border-luz text-luz" : "border-transparent text-suave hover:border-luz/40 hover:text-texto"}`}
          >
            {a.rotulo}
          </button>
        ))}
      </nav>

      {modalAberto && (
      <SimularLeitura
        fechar={() => setModalAberto(false)}
        trechos={trechos}
        trechoInicial={ponto?.trechos?.[0]}
        aoPublicar={(evento) => {
          setEventoExplicado(evento.id);
          setAba("explicacoes");
          buscar();
        }}
      />
      )}

      {aba === "explicacoes" ? (
        <Explicacoes
          eventos={dados.todosEventos}
          selecionado={eventoExplicado}
          setSelecionado={setEventoExplicado}
        />
      ) : (
      <>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <EstadoDaVia eventos={dados.eventos} />
        <Inferencia decisao={decisao} />
        <Verificacao decisao={decisao} piso={piso} />
        <Entregue ponto={ponto} latenciaMs={latenciaMs} />
      </div>

      <section className="border border-borda bg-carta p-4">
        <h2 className="mb-1 border-l-4 border-luz pl-2 text-xs font-bold tracking-wide text-luz uppercase">
          trajetória do nível
        </h2>
        <Trajetoria
          decisoes={dados.decisoes}
          telemetria={dados.telemetria}
          piso={piso ?? 0.5}
          luxPleno={ponto?.lux_pleno ?? 10}
        />
      </section>

      <Energia energia={dados.energia} />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Decisoes decisoes={dados.decisoes} telemetria={dados.telemetria} />
        </div>
        <div className="flex flex-col gap-4">
          <Alertas alertas={dados.alertas} />
          <Eventos eventos={dados.eventos} />
        </div>
      </div>
      </>
      )}

      </main>

      <footer className="w-full bg-tinta text-[11px] leading-relaxed text-white/70">
        <div className="mx-auto max-w-7xl px-4 py-5 text-center sm:px-6">
        O painel não decide: o botão de simulação só publica o volume ou a ocorrência de um trecho, como a plataforma
        de monitoramento faria. A decisão é produzida no serviço municipal e verificada contra
        a ABNT NBR 5101 antes de qualquer comando; nenhum dado pessoal trafega aqui
        (RNF08).
        </div>
      </footer>
    </div>
  );
}
