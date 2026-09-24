// Painel de acompanhamento (TCC 4.6.1, RF08).
//
// Le o historico pela interface REST e exibe, lado a lado, o dado recebido,
// o nivel pretendido pela inferencia, a correcao imposta pela camada de
// verificacao e a iluminancia medida - a cadeia que 4.6 chama de "a
// interface pela qual a conformidade normativa se torna observavel".
//
// So leitura: o painel nao publica evento nem comanda nada.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CircleDot, Lightbulb, Pause, Play, RefreshCw, WifiOff } from "lucide-react";
import { ESTADOS, api, hora } from "./api";
import { Entregue, EstadoDaVia, Inferencia, Verificacao } from "./componentes/Cartoes";
import { Alertas, Decisoes, Eventos } from "./componentes/Listas";
import Energia from "./componentes/Energia";
import Trajetoria from "./componentes/Trajetoria";

const PERIODO_MS = 2000; // metade do ciclo de decisao (5 s), sem afoga-lo
const JANELA = 240; // decisoes exibidas na trajetoria
const JANELA_ENERGIA_MIN = 30; // minutos integrados no cartao de consumo

export default function App() {
  const [dados, setDados] = useState({
    pontos: [], decisoes: [], telemetria: [], eventos: [], alertas: [], energia: null,
  });
  const [erro, setErro] = useState(null);
  const [rodando, setRodando] = useState(true);
  const [atualizadoEm, setAtualizadoEm] = useState(null);
  const carregando = useRef(false);

  const buscar = useCallback(async () => {
    if (carregando.current) return; // nao empilha requisicao lenta
    carregando.current = true;
    try {
      const [pontos, decisoes, telemetria, eventos, alertas, energia] = await Promise.all([
        api.pontos(),
        api.decisoes({ limite: JANELA }),
        api.telemetria({ limite: JANELA }),
        api.eventos({ limite: 40 }),
        api.alertas({ abertos: true }),
        api.energia({ janela_min: JANELA_ENERGIA_MIN }),
      ]);
      setDados({ pontos, decisoes, telemetria, eventos, alertas, energia });
      setAtualizadoEm(new Date());
      setErro(null);
    } catch (e) {
      setErro(e.message);
    } finally {
      carregando.current = false;
    }
  }, []);

  useEffect(() => {
    buscar();
    if (!rodando) return;
    const id = setInterval(buscar, PERIODO_MS);
    return () => clearInterval(id);
  }, [buscar, rodando]);

  const ponto = dados.pontos[0];
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
    <div className="mx-auto flex min-h-full max-w-7xl flex-col gap-4 p-4 sm:p-6">
      <header className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <h1 className="flex items-center gap-2 text-lg font-semibold">
          <Lightbulb size={20} className="text-luz" aria-hidden="true" />
          Iluminação adaptativa
        </h1>
        <span className="text-xs text-suave">
          {ponto ? `${ponto.codigo} · classe ${ponto.classe_codigo} · pleno ${ponto.lux_pleno} lx` : "sem ponto de luz"}
        </span>
        <span className={`inline-flex items-center gap-1 text-xs ${estado.cor}`}>
          <CircleDot size={12} aria-hidden="true" />
          {estado.texto}
        </span>

        <div className="ml-auto flex items-center gap-3 text-xs text-suave">
          <span>atualizado {hora(atualizadoEm?.toISOString())}</span>
          <button
            type="button"
            onClick={() => setRodando((v) => !v)}
            className="inline-flex items-center gap-1 rounded-md border border-borda px-2 py-1 hover:bg-borda/40"
          >
            {rodando ? <Pause size={12} /> : <Play size={12} />}
            {rodando ? "pausar" : "retomar"}
          </button>
          <button
            type="button"
            onClick={buscar}
            className="inline-flex items-center gap-1 rounded-md border border-borda px-2 py-1 hover:bg-borda/40"
          >
            <RefreshCw size={12} />
            atualizar
          </button>
        </div>
      </header>

      {erro && (
        <p className="flex items-center gap-2 rounded-lg border border-falha/40 bg-falha/10 p-3 text-sm text-falha">
          <WifiOff size={16} aria-hidden="true" />
          sem resposta da interface de dados ({erro}). Os valores abaixo são os últimos
          recebidos e podem estar desatualizados.
        </p>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <EstadoDaVia eventos={dados.eventos} />
        <Inferencia decisao={decisao} />
        <Verificacao decisao={decisao} piso={piso} />
        <Entregue ponto={ponto} latenciaMs={latenciaMs} />
      </div>

      <section className="rounded-xl border border-borda bg-carta p-4">
        <h2 className="mb-1 text-xs font-medium tracking-wide text-suave uppercase">
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

      <footer className="pb-2 text-[11px] text-suave">
        Painel de leitura. A decisão é produzida no serviço municipal e verificada contra
        a ABNT NBR 5101 antes de qualquer comando; nenhum dado pessoal trafega aqui
        (RNF08).
      </footer>
    </div>
  );
}
