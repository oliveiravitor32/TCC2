// Leitura ao passar o mouse nos graficos (SVG a mao): acha a amostra mais
// proxima do cursor no eixo do tempo, marca com uma linha vertical e mostra
// os valores numa caixa ao lado.

import { useState } from "react";

// xs: posicao horizontal de cada amostra, no sistema do viewBox (largura L).
export function useDica(xs, L) {
  const [i, setI] = useState(null);
  const mover = (ev) => {
    const r = ev.currentTarget.getBoundingClientRect();
    const xv = ((ev.clientX - r.left) / r.width) * L;
    let melhor = null;
    let dist = Infinity;
    xs.forEach((x, k) => {
      const dd = Math.abs(x - xv);
      if (dd < dist) {
        dist = dd;
        melhor = k;
      }
    });
    setI(melhor);
  };
  return { i, eventos: { onMouseMove: mover, onMouseLeave: () => setI(null) } };
}

// Caixa posicionada em % da largura; vira para a esquerda na metade direita.
export function CaixaDica({ x, L, titulo, linhas }) {
  const f = x / L;
  return (
    <div
      className="pointer-events-none absolute top-2 z-10 min-w-44 border border-borda bg-carta px-3 py-2 text-xs shadow-md"
      style={f > 0.5 ? { right: `${(1 - f) * 100 + 1}%` } : { left: `${f * 100 + 1}%` }}
    >
      <p className="mb-1 font-semibold text-texto">{titulo}</p>
      {linhas.map(([rotulo, valor, cor]) => (
        <div key={rotulo} className="flex justify-between gap-4 text-suave">
          <span className="inline-flex items-center gap-1">
            {cor && <span className="inline-block size-2 rounded-full" style={{ background: cor }} />}
            {rotulo}
          </span>
          <span className="tabular-nums text-texto">{valor}</span>
        </div>
      ))}
    </div>
  );
}

export const hora = (iso) =>
  new Date(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
