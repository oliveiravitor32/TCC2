-- Arquitetura de implantacao (DIVERGENCIAS 71): a central decide por evento e
-- so publica quando o alvo muda ou precisa renovar; o controlador faz a rampa
-- e volta ao pleno quando a validade do comando vence. So acrescenta colunas.
BEGIN;

-- Validade do comando, em segundos a partir do recebimento no no.
ALTER TABLE decisao ADD COLUMN IF NOT EXISTS validade_s INTEGER CHECK (validade_s > 0);

-- Nivel que o no estava aplicando ao responder (no meio de uma rampa, ainda
-- nao e o alvo); o diagnostico compara o lux com ele.
ALTER TABLE telemetria ADD COLUMN IF NOT EXISTS nivel_aplicado NUMERIC(4,3)
    CHECK (nivel_aplicado BETWEEN 0 AND 1);

-- Regua do trecho calculada uma vez por dia (percentil 99 de 28 dias), e
-- nao a cada decisao.
ALTER TABLE trecho_via ADD COLUMN IF NOT EXISTS referencia_aprendida NUMERIC(8,2)
    CHECK (referencia_aprendida > 0);
ALTER TABLE trecho_via ADD COLUMN IF NOT EXISTS referencia_calculada_em TIMESTAMPTZ;

CREATE OR REPLACE VIEW auditoria_decisao AS
SELECT d.id                          AS decisao_id,
       d.criado_em,
       d.execucao_id,
       p.codigo                      AS ponto,
       d.classe_codigo,
       c.iluminancia_media_min_lux   AS lux_pleno,
       cm.iluminancia_media_min_lux / c.iluminancia_media_min_lux AS piso_fracao,
       d.nivel_pretendido,
       d.nivel_emitido,
       d.restricao_aplicada,
       t.duty,
       t.lux_medido,
       s.lux_residual,
       (t.lux_medido - COALESCE(s.lux_residual, 0))
           / NULLIF(COALESCE(t.nivel_aplicado, d.nivel_emitido) * c.iluminancia_media_min_lux, 0)
                                     AS razao_entregue,
       t.recebido_em - d.criado_em   AS latencia_decisao,
       t.recebido_em - ev.ultimo_evento_em AS latencia_evento
  FROM decisao d
  JOIN ponto_de_luz p      ON p.id     = d.ponto_de_luz_id
  JOIN classe_iluminacao c ON c.codigo = d.classe_codigo
  LEFT JOIN classe_iluminacao cm ON cm.codigo = c.classe_min_dimerizacao
  LEFT JOIN telemetria t   ON t.decisao_id = d.id
  LEFT JOIN sessao_medicao s ON s.id = t.sessao_id
  LEFT JOIN LATERAL (
        SELECT max(e.recebido_em) AS ultimo_evento_em
          FROM decisao_evento de
          JOIN evento_urbano e ON e.id = de.evento_id
         WHERE de.decisao_id = d.id
           AND NOT EXISTS (
                 SELECT 1
                   FROM decisao_evento de2
                   JOIN decisao d2 ON d2.id = de2.decisao_id
                  WHERE de2.evento_id = de.evento_id
                    AND d2.ponto_de_luz_id = d.ponto_de_luz_id
                    AND d2.criado_em < d.criado_em)
       ) ev ON true;

COMMIT;
