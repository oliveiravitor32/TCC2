// Trajetoria do nivel ao longo do tempo (RF08).
//
// Tres series sobre o mesmo eixo, que e o que torna a camada de verificacao
// observavel (4.6): o que a inferencia PRETENDEU, o que o sistema EMITIU
// depois da verificacao, e o que o no ENTREGOU em lux (normalizado pelo
// valor da classe, para caber na mesma escala).
//
// SVG a mao, sem biblioteca de grafico: sao tres linhas e duas referencias.

const M = { esq: 38, dir: 12, topo: 12, base: 22 };
const L = 720;
const A = 240;

function caminho(pontos) {
  return pontos.length ? "M" + pontos.map((p) => `${p.x},${p.y}`).join(" L") : "";
}

export default function Trajetoria({ decisoes, telemetria, piso, luxPleno }) {
  // As consultas vem em ordem decrescente; aqui o tempo corre para a direita.
  const serie = [...decisoes].reverse();
  if (serie.length < 2) {
    return (
      <div className="flex h-60 items-center justify-center text-sm text-suave">
        aguardando decisões para desenhar a trajetória...
      </div>
    );
  }

  const t0 = new Date(serie[0].criado_em).getTime();
  const t1 = new Date(serie[serie.length - 1].criado_em).getTime();
  const span = Math.max(t1 - t0, 1000);
  const x = (iso) => M.esq + ((new Date(iso).getTime() - t0) / span) * (L - M.esq - M.dir);
  const y = (v) => M.topo + (1 - Math.min(Math.max(v, 0), 1)) * (A - M.topo - M.base);

  const emitido = serie.map((d) => ({ x: x(d.criado_em), y: y(d.nivel_emitido) }));
  const pretendido = serie.map((d) => ({ x: x(d.criado_em), y: y(d.nivel_pretendido) }));

  const porDecisao = new Map(telemetria.map((t) => [t.decisao_id, t]));
  const medido = serie
    .filter((d) => porDecisao.has(d.id))
    .map((d) => ({
      x: x(d.criado_em),
      y: y(porDecisao.get(d.id).lux_medido / luxPleno),
    }));

  const corrigidas = serie
    .filter((d) => d.restricao_aplicada !== "nenhuma")
    .map((d) => ({ x: x(d.criado_em), y: y(d.nivel_emitido), r: d.restricao_aplicada }));

  const corRestricao = {
    piso: "var(--color-piso)",
    taxa: "var(--color-taxa)",
  };

  return (
    <figure className="w-full">
      <svg viewBox={`0 0 ${L} ${A}`} className="w-full" role="img"
           aria-label="Trajetória do nível de iluminação">
        {[0, 0.25, 0.5, 0.75, 1].map((v) => (
          <g key={v}>
            <line x1={M.esq} x2={L - M.dir} y1={y(v)} y2={y(v)}
                  stroke="var(--color-borda)" strokeWidth="1" />
            <text x={M.esq - 6} y={y(v) + 4} textAnchor="end" fontSize="10"
                  fill="var(--color-suave)">
              {v.toFixed(2)}
            </text>
          </g>
        ))}

        {/* Piso da classe: o limite que a verificacao nao deixa cruzar. */}
        <line x1={M.esq} x2={L - M.dir} y1={y(piso)} y2={y(piso)}
              stroke="var(--color-piso)" strokeWidth="1.5" strokeDasharray="6 4" />
        <text x={L - M.dir} y={y(piso) - 5} textAnchor="end" fontSize="10"
              fill="var(--color-piso)">
          piso P5
        </text>

        <path d={caminho(pretendido)} fill="none" stroke="var(--color-suave)"
              strokeWidth="1.5" strokeDasharray="4 4" />
        <path d={caminho(emitido)} fill="none" stroke="var(--color-luz)" strokeWidth="2.5" />
        {medido.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r="2" fill="var(--color-ok)" opacity="0.85" />
        ))}
        {corrigidas.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r="3.5" fill="none"
                  stroke={corRestricao[p.r]} strokeWidth="1.5" />
        ))}
      </svg>

      <figcaption className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-suave">
        <Legenda cor="var(--color-suave)" tracejado>nível pretendido (inferência)</Legenda>
        <Legenda cor="var(--color-luz)">nível emitido (após verificação)</Legenda>
        <Legenda cor="var(--color-ok)" ponto>iluminância medida / {luxPleno} lx</Legenda>
        <Legenda cor="var(--color-piso)" tracejado>piso da classe</Legenda>
      </figcaption>
    </figure>
  );
}

function Legenda({ cor, tracejado, ponto, children }) {
  return (
    <span className="inline-flex items-center gap-2">
      <svg width="22" height="8" aria-hidden="true">
        {ponto ? (
          <circle cx="11" cy="4" r="2.5" fill={cor} />
        ) : (
          <line x1="0" y1="4" x2="22" y2="4" stroke={cor} strokeWidth="2"
                strokeDasharray={tracejado ? "4 3" : undefined} />
        )}
      </svg>
      {children}
    </span>
  );
}
