// Modal "de onde vem baixa/media/alta": as tres faixas da movimentacao
// (tercis da serie de Zurique, 3.7), com a rampa de transicao e onde caiu o
// movimento observado e o previsto desta decisao. Os numeros vem da base de
// regras da propria decisao (GET /eventos/{id}/explicacao), nao do painel.

import { useEffect } from "react";
import { X } from "lucide-react";
import { pct } from "../api";

const MAX = 0.6; // escala da barra: 0 a 60 % do cheio da rua (acima disso, no fim)
const L = 600;
const pct2 = (v) => `${(v * 100).toFixed(2)}%`;
const x = (v) => (Math.min(Math.max(v, 0), MAX) / MAX) * L;

function Marcador({ v, rotulo, cor, y }) {
  if (v === null || v === undefined) return null;
  const px = x(v);
  return (
    <g>
      <line x1={px} x2={px} y1={34} y2={78} stroke={cor} strokeWidth={2.5} />
      <circle cx={px} cy={78} r={4} fill={cor} />
      <text x={px} y={y} fontSize={13} fill={cor} textAnchor={px > L - 90 ? "end" : px < 90 ? "start" : "middle"}>
        {rotulo} {pct(v)}{v > MAX ? " →" : ""}
      </text>
    </g>
  );
}

export default function FaixasMovimento({ faixas, observada, prevista, reativo, reguas, volumes, fechar }) {
  useEffect(() => {
    const tecla = (e) => e.key === "Escape" && fechar();
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [fechar]);

  const [f1, f2] = faixas.fronteiras;
  const m = faixas.meia_largura_rampa;
  const faixasSvg = [
    { de: 0, ate: f1, nome: "baixa", cor: "#86efac" },
    { de: f1, ate: f2, nome: "média", cor: "#facc15" },
    { de: f2, ate: MAX, nome: "alta", cor: "#f87171" },
  ];
  const marcas = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="titulo-faixas"
      onClick={fechar}
    >
      <div
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-borda bg-carta p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-start justify-between gap-4">
          <h2 id="titulo-faixas" className="text-base font-semibold">
            De onde vêm as faixas baixa, média e alta
          </h2>
          <button type="button" onClick={fechar} aria-label="fechar" className="text-suave hover:text-texto">
            <X size={18} />
          </button>
        </div>

        <svg viewBox={`-10 0 ${L + 20} 128`} className="w-full" role="img"
             aria-label={`faixas: baixa até ${pct2(f1)}, média até ${pct2(f2)}, alta acima`}>
          {faixasSvg.map((s) => (
            <g key={s.nome}>
              <rect x={x(s.de)} y={40} width={x(s.ate) - x(s.de)} height={30} fill={s.cor} opacity={0.55} />
              <text x={(x(s.de) + x(s.ate)) / 2} y={60} fontSize={13} textAnchor="middle" fill="currentColor">
                {s.nome}
              </text>
            </g>
          ))}
          {[f1, f2].map((f) => (
            <rect key={f} x={x(f - m)} y={40} width={x(f + m) - x(f - m)} height={30} fill="url(#rampa)" />
          ))}
          <defs>
            <pattern id="rampa" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <line x1="0" y1="0" x2="0" y2="6" stroke="currentColor" strokeOpacity="0.45" strokeWidth="2" />
            </pattern>
          </defs>
          {marcas.map((v) => (
            <text key={v} x={x(v)} y={98} fontSize={11} textAnchor="middle" fill="currentColor" opacity={0.6}>
              {Math.round(v * 100)}%{v === MAX ? "+" : ""}
            </text>
          ))}
          <Marcador v={observada} rotulo="agora" cor="#2563eb" y={26} />
          {!reativo && <Marcador v={prevista} rotulo="previsto" cor="#9333ea" y={122} />}
        </svg>

        <div className="mt-3 space-y-2 text-sm">
          <p>
            <b>Baixa</b> até {pct2(f1)} · <b>média</b> de {pct2(f1)} a {pct2(f2)} · <b>alta</b> acima de {pct2(f2)} do
            cheio da rua. Nas listras (±{pct2(m)} em volta de cada fronteira), o movimento é um pouco de cada faixa:
            duas regras disparam em parte e o nível pode cair entre duas classes.
          </p>
          <p className="text-suave">
            <b className="text-texto">Como foram tiradas:</b> nas contagens reais de pedestres de Zurique (15 min,
            14 sensores), cada contagem virou fração do pico do próprio sensor; todas foram postas em fila, da menor
            para a maior, e a fila foi cortada em três partes iguais (tercis). A NBR 5101 permite baixar a classe com
            pouco movimento, mas não diz quanto é "pouco": é critério dos autores (seções 3.7 e 5.3 do TCC).
          </p>
          {Object.keys(reguas ?? {}).length > 0 && (
            <div className="text-suave">
              <b className="text-texto">Cheio de cada rua (régua):</b>
              <ul className="mt-1 space-y-0.5 text-xs">
                {Object.entries(reguas).map(([t, r]) => (
                  <li key={t}>
                    trecho {t}: {volumes?.[t] ?? "--"} pessoas agora ÷ {r.pessoas} no cheio
                    {" "}= {volumes?.[t] != null ? pct(volumes[t] / r.pessoas) : "--"}
                    {r.aprendida ? " (p99 dos últimos 28 dias)" : " (valor inicial: ainda sem 7 dias de leituras)"}
                  </li>
                ))}
              </ul>
              <p className="mt-1 text-xs">Vale o maior entre os trechos do poste. A régua mostrada é a de hoje (é
                recalculada uma vez por dia); numa decisão antiga, a conta pode diferir um pouco.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
