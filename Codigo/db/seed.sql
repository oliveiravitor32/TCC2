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
VALUES ('v0-provisoria', 9,
        'Particoes trapezoidais provisorias (tercis 1/3 e 2/3); 9 regras; atenuacao condicionada a ausencia de risco. '
        'Arquivo: decisao/regras/v0-provisoria.toml. Substituida pela v1 apos os tercis de Melbourne.')
ON CONFLICT (rotulo) DO NOTHING;

-- Base vigente: tercis da serie de Melbourne (2026-09-23), calculados por
-- modelo/treinar.py. A v0 fica registrada porque produziu as primeiras decisoes.
INSERT INTO versao_base_regras (rotulo, qtd_regras, resumo)
VALUES ('v1-tercis', 9,
        'Tercis da serie de Melbourne (2026-09-23) normalizada por ponto: '
        'fronteiras em 0.1038 e 0.4053. Arquivo: decisao/regras/v1-tercis.toml.')
ON CONFLICT (rotulo) DO NOTHING;

-- Base vigente desde a retirada da condicao meteorologica (DIVERGENCIAS 49).
-- Os arquivos da v0 e da v1 sairam do repositorio (ficam no historico do
-- git); as linhas acima continuam porque decisoes antigas as referenciam.
INSERT INTO versao_base_regras (rotulo, qtd_regras, resumo)
VALUES ('v2-sem-meteorologia', 8,
        'Tercis da serie de Melbourne (2026-09-23): fronteiras em 0.1038 e 0.4053; '
        '8 regras, sem condicao meteorologica. Arquivo: decisao/regras/v2-sem-meteorologia.toml.')
ON CONFLICT (rotulo) DO NOTHING;

-- Mesma base como tabela em degraus, so para a comparacao do item 51.
INSERT INTO versao_base_regras (rotulo, qtd_regras, resumo)
VALUES ('v2-sem-meteorologia-degraus', 8,
        'Mesma base v2 como tabela em degraus (corte seco nos tercis, faixa horaria no conjunto de maior grau); so para comparacao com a Mamdani.')
ON CONFLICT (rotulo) DO NOTHING;

-- Base por presenca (DIVERGENCIAS 55), substituida pela v4.
INSERT INTO versao_base_regras (rotulo, qtd_regras, resumo)
VALUES ('v3-presenca', 6,
        'Presenca de pedestre na leitura do trecho em vez de volume observado; 6 regras; tercis de Melbourne na previsao. Arquivo: decisao/regras/v3-presenca.toml.'),
       ('v3-presenca-degraus', 6,
        'Mesma base v3 como tabela em degraus; so para comparacao com a Mamdani.')
ON CONFLICT (rotulo) DO NOTHING;

-- Base por volume com saida em degraus de classe (DIVERGENCIAS 56): a vigente.
INSERT INTO versao_base_regras (rotulo, qtd_regras, resumo)
VALUES ('v4-volume', 7,
        'Volume de movimento (media de 5 min por trecho) observado e previsto; 7 regras; saida em degraus de classe lidos de classe_iluminacao. Arquivo: decisao/regras/v4-volume.toml.'),
       ('v4-volume-degraus', 7,
        'Mesma base v4 como tabela em degraus; so para comparacao com a Mamdani.')
ON CONFLICT (rotulo) DO NOTHING;

-- hash_regras e conferido pelo servico de decisao ao iniciar (passo 5).

-- Camadas de previsao (3.6). A persistencia foi a previsao provisoria e
-- segue como referencia de comparacao em 5.1. As metricas do modelo treinado
-- sao preenchidas por  python -m modelo.treinar --registrar.
INSERT INTO versao_modelo_previsao (rotulo, algoritmo)
VALUES ('persistencia', 'persistencia'),
       ('xgboost-v1',   'xgboost'),
       ('media-sazonal', 'media_sazonal')
ON CONFLICT (rotulo) DO NOTHING;

COMMIT;
