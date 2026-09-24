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

export const api = {
  base: BASE,
  pontos: () => pegar("/pontos"),
  decisoes: (params) => pegar("/decisoes", params),
  telemetria: (params) => pegar("/telemetria", params),
  eventos: (params) => pegar("/eventos", params),
  alertas: (params) => pegar("/alertas", params),
};

// Rotulos das correcoes da camada de verificacao (3.7).
export const RESTRICOES = {
  nenhuma: { texto: "sem correção", cor: "text-suave", fundo: "bg-borda/40" },
  piso: { texto: "piso da classe", cor: "text-piso", fundo: "bg-piso/15" },
  taxa: { texto: "taxa de descida", cor: "text-taxa", fundo: "bg-taxa/15" },
  meteorologia: { texto: "meteorologia", cor: "text-meteo", fundo: "bg-meteo/15" },
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
