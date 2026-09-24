// Consumo estimado, projetado para a luminaria de referencia (TCC 3.11, RF12).
//
// A area amarela e a potencia derivada da LUZ MEDIDA pelo sensor; o retangulo
// cinza atras dela e o que a mesma luminaria consumiria em fluxo pleno
// constante, que e o regime praticamente invariante de hoje (2.3). A distancia
// entre as duas e a economia.
//
// A conta vem pronta do servidor (endpoint /energia), que usa o mesmo modulo
// que produz os resultados do Capitulo 5: assim nao existe uma segunda
// implementacao do RF12 aqui que pudesse divergir daquela.

import { Gauge, TrendingDown } from "lucide-react";
import { Cartao } from "./Cartoes";

const M = { esq: 44, dir: 12, topo: 14, base: 22 };
const L = 720;
const A = 200;

export default function Energia({ energia }) {
  if (!energia) {
    return (
      <Cartao icone={Gauge} titulo="consumo estimado">
        <p className="py-6 text-center text-sm text-suave">carregando...</p>
      </Cartao>
    );
  }

  const {
    amostras, potencia_nominal_w: pico, potencia_agora_w: agora,
    energia_pela_luz_wh: wh, energia_pleno_wh: whPleno,
    energia_horario_fixo_wh: whFixo, razao_pleno: razao,
    divergencia_entre_estimativas: divergencia, luminaria, janela_min: janela,
  } = energia;

  const economia = razao != null ? 1 - razao : null;

  return (
    <Cartao icone={Gauge} titulo={`consumo estimado · ${luminaria} · ${janela} min`}>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto]">
        <Grafico amostras={amostras} pico={pico} />

        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 self-start lg:w-56 lg:grid-cols-1">
          <Numero rotulo="potência agora" valor={agora != null ? `${agora.toFixed(1)} W` : "--"}
                  detalhe={`pleno: ${pico.toFixed(0)} W`} destaque />
          <Numero rotulo="energia na janela" valor={`${wh.toFixed(2)} Wh`}
                  detalhe={`pleno: ${whPleno.toFixed(2)} Wh · horário fixo: ${whFixo.toFixed(2)} Wh`} />
          <Numero
            rotulo="ante o fluxo pleno"
            valor={economia != null ? `−${(economia * 100).toFixed(1)}%` : "--"}
            detalhe={razao != null ? `consome ${(razao * 100).toFixed(1)}% do pleno` : ""}
            icone={economia > 0 ? TrendingDown : null}
          />
        </dl>
      </div>

      <p className="mt-3 text-[11px] leading-relaxed text-suave">
        Estimativa derivada da iluminância medida, e não medição elétrica: supõe potência
        proporcional ao nível e despreza o consumo fixo do driver e do controlador, o que
        a torna um limite superior otimista (3.11).
        {divergencia != null && (
          <> Divergência para a estimativa pelo comando: {(divergencia * 100).toFixed(1)}%.</>
        )}
      </p>
    </Cartao>
  );
}

function Numero({ rotulo, valor, detalhe, destaque, icone: Icone }) {
  return (
    <div>
      <dt className="text-xs text-suave">{rotulo}</dt>
      <dd
        className={`flex items-center gap-1 text-2xl font-semibold tabular-nums ${
          destaque ? "text-luz" : ""
        }`}
      >
        {Icone && <Icone size={16} className="text-ok" aria-hidden="true" />}
        {valor}
      </dd>
      {detalhe && <dd className="text-[11px] text-suave">{detalhe}</dd>}
    </div>
  );
}

function Grafico({ amostras, pico }) {
  if (amostras.length < 2) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-suave">
        aguardando telemetria para desenhar o consumo...
      </div>
    );
  }

  const t0 = new Date(amostras[0].medido_em).getTime();
  const t1 = new Date(amostras[amostras.length - 1].medido_em).getTime();
  const span = Math.max(t1 - t0, 1000);
  const x = (iso) => M.esq + ((new Date(iso).getTime() - t0) / span) * (L - M.esq - M.dir);
  const y = (w) => M.topo + (1 - Math.min(w / pico, 1)) * (A - M.topo - M.base);

  const pts = amostras.map((a) => ({ x: x(a.medido_em), y: y(a.potencia_medida_w) }));
  const linha = "M" + pts.map((p) => `${p.x},${p.y}`).join(" L");
  const area = `${linha} L${pts[pts.length - 1].x},${y(0)} L${pts[0].x},${y(0)} Z`;
  const minutos = Math.round(span / 60000);

  return (
    <figure>
      <svg viewBox={`0 0 ${L} ${A}`} className="w-full" role="img"
           aria-label="Potência estimada ao longo do tempo">
        {/* Fluxo pleno constante: o teto e a linha de base de comparação. */}
        <rect x={M.esq} y={y(pico)} width={L - M.esq - M.dir} height={y(0) - y(pico)}
              fill="var(--color-borda)" opacity="0.35" />
        <line x1={M.esq} x2={L - M.dir} y1={y(pico)} y2={y(pico)}
              stroke="var(--color-suave)" strokeWidth="1.5" strokeDasharray="6 4" />
        <text x={M.esq + 6} y={y(pico) + 13} fontSize="10" fill="var(--color-suave)">
          fluxo pleno constante ({pico.toFixed(0)} W)
        </text>

        {[0, 0.5, 1].map((f) => (
          <text key={f} x={M.esq - 6} y={y(pico * f) + 4} textAnchor="end" fontSize="10"
                fill="var(--color-suave)">
            {(pico * f).toFixed(0)} W
          </text>
        ))}

        <path d={area} fill="var(--color-luz)" opacity="0.18" />
        <path d={linha} fill="none" stroke="var(--color-luz)" strokeWidth="2.5" />
        <circle cx={pts[pts.length - 1].x} cy={pts[pts.length - 1].y} r="3.5"
                fill="var(--color-luz)" />

        <line x1={M.esq} x2={L - M.dir} y1={y(0)} y2={y(0)}
              stroke="var(--color-borda)" strokeWidth="1" />
        <text x={M.esq} y={A - 6} fontSize="10" fill="var(--color-suave)">
          −{minutos} min
        </text>
        <text x={L - M.dir} y={A - 6} textAnchor="end" fontSize="10" fill="var(--color-suave)">
          agora
        </text>
      </svg>
      <figcaption className="mt-1 text-xs text-suave">
        potência estimada pela iluminância medida, contra o consumo em fluxo pleno
      </figcaption>
    </figure>
  );
}
