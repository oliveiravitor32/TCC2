// Cliente da interface de dados urbanos (TCC 4.6.2, Quadro 14).
//
// A base vem de VITE_API_URL: em desenvolvimento, o uvicorn local; na
// Vercel, a URL publica da VM. Sem ela, o painel nao inventa dado - mostra
// o erro, porque um painel que mostra numero velho como se fosse atual e
// pior do que um painel vazio.

const BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

async function pegar(caminho, params = {}) {
  if (!BASE) throw new Error("VITE_API_URL nao configurada");
  const url = new URL(BASE + caminho);
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null) url.searchParams.set(k, v);
  }
  const r = await fetch(url, { headers: { Accept: "application/json" } });
  if (!r.ok) throw new Error(`${caminho}: ${r.status} ${r.statusText}`);
  return r.json();
}

// Chave do painel de demonstracao (DIVERGENCIAS 55). Embutida no build por
// decisao do autor: fica legivel no site, e por isso e uma chave separada da
// principal, que a VM pode desligar sem afetar o evento.sh.
const CHAVE_DEMO = import.meta.env.VITE_CHAVE_DEMO || "";

async function enviar(caminho, corpo) {
  if (!BASE) throw new Error("VITE_API_URL nao configurada");
  const r = await fetch(BASE + caminho, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json", "X-Chave-Api": CHAVE_DEMO },
    body: JSON.stringify(corpo),
  });
  const dados = await r.json().catch(() => ({}));
  if (!r.ok) {
    const detalhe = Array.isArray(dados.detail)
      ? dados.detail.map((d) => d.msg).join("; ")
      : dados.detail || r.statusText;
    throw new Error(`${r.status}: ${detalhe}`);
  }
  return dados;
}

export const api = {
  base: BASE,
  podePublicar: Boolean(CHAVE_DEMO),
  pontos: () => pegar("/pontos"),
  trechos: () => pegar("/trechos"),
  explicacao: (eventoId) => pegar(`/eventos/${eventoId}/explicacao`),
  publicarLeitura: (corpo) => enviar("/eventos", corpo),
  decisoes: (params) => pegar("/decisoes", params),
  telemetria: (params) => pegar("/telemetria", params),
  eventos: (params) => pegar("/eventos", params),
  alertas: (params) => pegar("/alertas", params),
  energia: (params) => pegar("/energia", params),
};

// Rotulos das correcoes da camada de verificacao (3.7).
export const RESTRICOES = {
  nenhuma: { texto: "sem correção", cor: "text-suave", fundo: "bg-borda/40" },
  piso: { texto: "piso da classe", cor: "text-piso", fundo: "bg-piso/15" },
  taxa: { texto: "taxa de descida", cor: "text-taxa", fundo: "bg-taxa/15" },
};

export const ESTADOS = {
  operante: { texto: "operante", cor: "text-ok" },
  falha: { texto: "em falha", cor: "text-falha" },
  manutencao: { texto: "em manutenção", cor: "text-suave" },
  sem_comunicacao: { texto: "sem comunicação", cor: "text-falha" },
};

export const hora = (iso) =>
  iso ? new Date(iso).toLocaleTimeString("pt-BR", { hour12: false }) : "--:--:--";

export const pct = (v) => (v === null || v === undefined ? "--" : `${(v * 100).toFixed(1)}%`);

export const lux = (v, casas = 2) =>
  v === null || v === undefined ? "--" : `${Number(v).toFixed(casas)} lx`;

// Fronteiras da movimentacao prevista: os tercis da serie adotada (3.7).
export const TERCIS = [0.1038, 0.4053];
export const faixaMov = (v) =>
  v === null || v === undefined ? "sem previsão" : v < TERCIS[0] ? "baixa" : v < TERCIS[1] ? "média" : "alta";

// Faixa horaria em horas desde as 18h (0 a 12), com as mesmas fronteiras
// dos conjuntos da base de regras: inicio da noite ate 3 h (pleno) e saindo
// ate 5 h; madrugada de 4 a 10 h; pre-amanhecer a partir de 9 h. Nas
// sobreposicoes, a inferencia enxerga os dois conjuntos ao mesmo tempo.
export const faixaHoraria = (h) => {
  if (h === null || h === undefined) return "--";
  // Fora da noite (18h-06h) a inferencia usa o extremo mais proximo; a hora
  // real da decisao aparece no cabecalho de cada decisao.
  const faixa =
    h < 4 ? "início da noite"
      : h < 5 ? "início da noite → madrugada"
        : h < 9 ? "madrugada"
          : h < 10 ? "madrugada → pré-amanhecer"
            : "pré-amanhecer";
  return faixa;
};

export const OCORRENCIAS = { seguranca: "segurança", transito: "trânsito" };
