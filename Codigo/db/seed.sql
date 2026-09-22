-- Carga inicial: classes P3-P6 (Quadro 8, adaptado da ABNT NBR 5101:2024),
-- ponto de luz da bancada, luminarias de referencia (Quadro 9) e versoes
-- iniciais da base de regras e do modelo de previsao.

BEGIN;

-- P6 primeiro: as demais referenciam classes inferiores.
INSERT INTO classe_iluminacao
    (codigo, descricao, iluminancia_media_min_lux, iluminancia_min_lux,
     iluminancia_vert_min_lux, classe_min_dimerizacao, taxa_max_decrescimo_min)
VALUES
    ('P6', 'Nao dimerizavel',      3.0, 0.6, 1.0, NULL, 0.100),
    ('P5', 'Piso admissivel',      5.0, 1.0, 1.5, NULL, 0.100),
    ('P4', 'Nivel intermediario',  7.5, 1.5, 2.5, 'P6', 0.100),
    ('P3', 'Fluxo pleno',         10.0, 2.0, 3.0, 'P5', 0.100)
ON CONFLICT (codigo) DO NOTHING;

-- Cenario adotado (3.8): calcada de via urbana local -> classe P3.
-- Dimerizacao admitida ate P5 => piso = 5,0 / 10,0 = 0,5 do fluxo pleno.
-- Taxa: decrescimo maximo de 0,1 do pleno por minuto (elevacao e livre).

INSERT INTO ponto_de_luz
    (codigo, logradouro, latitude, longitude, classe_codigo, potencia_plena_w)
VALUES
    ('BANCADA-01', 'No de bancada (TCC)', NULL, NULL, 'P3', NULL)
ON CONFLICT (codigo) DO NOTHING;
-- potencia_plena_w fica NULL ate a medicao do segmento de fita em bancada (3.4.2).

-- Quadro 9: extremos da faixa contratual de 40 W a 440 W, 90 lm/W.
INSERT INTO luminaria_referencia
    (codigo, potencia_nominal_w, eficacia_lm_w, interface_dimerizacao, origem)
VALUES
    ('REF-40W',   40.0, 90.0, '0-10 V', 'Caderno de Encargos (SAO PAULO, 2015): limite inferior da faixa contratual'),
    ('REF-440W', 440.0, 90.0, '0-10 V', 'Caderno de Encargos (SAO PAULO, 2015): limite superior da faixa contratual')
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO versao_base_regras (rotulo, qtd_regras, resumo)
VALUES ('v0-provisoria', 1, 'Particoes trapezoidais provisorias; sera substituida apos a definicao dos tercis.')
ON CONFLICT (rotulo) DO NOTHING;

-- Previsao provisoria (passo 5): persistencia, ate o treino do XGBoost (Etapa 3).
INSERT INTO versao_modelo_previsao (rotulo, algoritmo)
VALUES ('persistencia', 'persistencia')
ON CONFLICT (rotulo) DO NOTHING;

COMMIT;
