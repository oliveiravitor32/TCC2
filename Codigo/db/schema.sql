-- Iluminacao Adaptativa - esquema do banco (TCC 4.7.1, Quadro 15, 4.7.2)
-- PostgreSQL 16+
-- Nenhuma entidade guarda imagem, audio ou identificador individual (RNF08).

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid()

-- ---------------------------------------------------------------------------
-- Referencia normativa (RF09): os limites da ABNT NBR 5101 ficam em tabela,
-- nunca no codigo. A camada de verificacao le seu criterio daqui.
-- ---------------------------------------------------------------------------
CREATE TABLE classe_iluminacao (
    codigo                     TEXT PRIMARY KEY,
    descricao                  TEXT NOT NULL,
    iluminancia_media_min_lux  NUMERIC(6,2) NOT NULL CHECK (iluminancia_media_min_lux > 0),
    iluminancia_min_lux        NUMERIC(6,2) NOT NULL CHECK (iluminancia_min_lux > 0),
    iluminancia_vert_min_lux   NUMERIC(6,2) NOT NULL CHECK (iluminancia_vert_min_lux > 0),
    -- Classe mais baixa ate a qual a dimerizacao e admitida (NBR 5101, 6.10:
    -- no maximo duas classes imediatamente inferiores). NULL = nao dimerizavel.
    classe_min_dimerizacao     TEXT REFERENCES classe_iluminacao (codigo),
    -- Fracao do fluxo pleno por minuto; limita apenas o DECRESCIMO.
    taxa_max_decrescimo_min    NUMERIC(4,3) NOT NULL
                               CHECK (taxa_max_decrescimo_min > 0 AND taxa_max_decrescimo_min <= 1),
    fonte_normativa            TEXT NOT NULL DEFAULT 'ABNT NBR 5101:2024',
    criado_em                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE classe_iluminacao IS
    'Criterio normativo externo consultado pela camada de verificacao (RF09).';
COMMENT ON COLUMN classe_iluminacao.classe_min_dimerizacao IS
    'Piso admissivel: a fracao de fluxo pleno e a razao entre as iluminancias medias.';

-- ---------------------------------------------------------------------------
-- Trecho de via: segmento de logradouro do GeoSampa (DIVERGENCIAS 54). E a
-- unidade espacial em que a plataforma de monitoramento publica o estado da
-- via; qual camera cobre qual trecho e assunto interno dela.
-- ---------------------------------------------------------------------------
CREATE TABLE trecho_via (
    -- cd_identificador do segmento no GeoSampa: o mesmo codigo nas duas pontas.
    id               BIGINT PRIMARY KEY,
    codlog           TEXT,            -- codigo oficial do logradouro
    tipo_logradouro  TEXT,
    nome_logradouro  TEXT NOT NULL,
    numero_inicial   INTEGER,
    numero_final     INTEGER,
    -- LineString em SIRGAS 2000 / UTM 23S (EPSG:31983), como no GeoSampa.
    geometria        JSONB NOT NULL,
    fonte            TEXT NOT NULL,
    extraido_em      DATE NOT NULL,
    -- "Cheio" tipico do trecho (pessoas na area, media horaria), usado so para
    -- normalizar a serie da previsao como no treino (3.6). O servico aprende o
    -- percentil 99 das leituras apos 7 dias; ate la vale este valor inicial,
    -- declarado para rua local (DIVERGENCIAS 55).
    referencia_pessoas NUMERIC(8,2) NOT NULL DEFAULT 5 CHECK (referencia_pessoas > 0)
);

-- ---------------------------------------------------------------------------
-- Ponto de luz. Cada registro e uma luminaria comandada pelo sistema; na
-- bancada, ela "representa" um poste real do cadastro (placa).
-- ---------------------------------------------------------------------------
CREATE TABLE ponto_de_luz (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo              TEXT NOT NULL UNIQUE,
    logradouro          TEXT,
    latitude            NUMERIC(9,6),
    longitude           NUMERIC(9,6),
    classe_codigo       TEXT NOT NULL REFERENCES classe_iluminacao (codigo),
    estado_operacional  TEXT NOT NULL DEFAULT 'operante'
                        CHECK (estado_operacional IN ('operante','falha','manutencao','sem_comunicacao')),
    -- Potencia do segmento de fita a ciclo pleno: 14,4 W/m x comprimento
    -- fixado por medicao (3.4.2). Base da estimativa de energia de bancada
    -- (RF12, 3.11); nao e medicao eletrica.
    potencia_plena_w    NUMERIC(7,2) CHECK (potencia_plena_w > 0),
    -- Placa do poste (cd_placa do GeoSampa): o codigo cadastral pelo qual a
    -- telegestao enderaca o ativo (Caderno de Encargos, 13 e 13.3).
    placa               TEXT UNIQUE,
    -- Posicao oficial em EPSG:31983 (metros), base da associacao espacial.
    utm_e               NUMERIC(11,2),
    utm_n               NUMERIC(11,2),
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Associacao trecho x ponto de luz (N:N), calculada a partir dos dois
-- cadastros por cadastro/associar.py. Um poste de esquina fica em mais de um
-- trecho. Novo ponto = novas linhas aqui, sem alterar o servico (RNF09).
-- ---------------------------------------------------------------------------
CREATE TABLE trecho_ponto (
    trecho_id        BIGINT NOT NULL REFERENCES trecho_via (id),
    ponto_de_luz_id  BIGINT NOT NULL REFERENCES ponto_de_luz (id),
    distancia_m      NUMERIC(6,2) NOT NULL CHECK (distancia_m >= 0),
    criterio         TEXT NOT NULL,   -- regra que produziu a associacao
    associado_em     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (trecho_id, ponto_de_luz_id)
);
CREATE INDEX trecho_ponto_ponto_idx ON trecho_ponto (ponto_de_luz_id);

-- ---------------------------------------------------------------------------
-- Luminaria de referencia (Quadro 9, 3.11): derivada do Caderno de Encargos,
-- nao e modelo comercial. Projeta a energia do registro de decisoes.
-- ---------------------------------------------------------------------------
CREATE TABLE luminaria_referencia (
    codigo                  TEXT PRIMARY KEY,
    potencia_nominal_w      NUMERIC(7,2) NOT NULL CHECK (potencia_nominal_w > 0),
    eficacia_lm_w           NUMERIC(6,2) NOT NULL CHECK (eficacia_lm_w > 0),
    interface_dimerizacao   TEXT NOT NULL,
    -- Hipotese do Quadro 9: potencia proporcional ao nivel comandado,
    -- consumo fixo do driver e do controlador desprezado (limite otimista).
    origem                  TEXT NOT NULL
);

-- ---------------------------------------------------------------------------
-- Leituras recebidas da interface de dados urbanos (REST). Cada evento e a
-- leitura de um trecho num instante: quantas pessoas ha na area e se ha
-- ocorrencia (DIVERGENCIAS 55). A plataforma publica a cada poucos segundos.
-- ---------------------------------------------------------------------------
CREATE TABLE evento_urbano (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ocorrido_em  TIMESTAMPTZ NOT NULL,
    recebido_em  TIMESTAMPTZ NOT NULL DEFAULT now(),
    tipo         TEXT NOT NULL DEFAULT 'leitura' CHECK (tipo IN ('leitura')),
    -- Contagem instantanea de pessoas na area do trecho (analitico da camera).
    pessoas      INTEGER NOT NULL CHECK (pessoas >= 0),
    -- Ocorrencia em curso no trecho; NULL = nenhuma.
    ocorrencia   TEXT CHECK (ocorrencia IN ('seguranca','transito')),
    abrangencia  TEXT NOT NULL DEFAULT 'via'
                 CHECK (abrangencia IN ('via','quadra','bairro','municipio')),
    origem       TEXT NOT NULL,
    -- Onde: o trecho de via a que o evento se refere (um por evento).
    trecho_id    BIGINT NOT NULL REFERENCES trecho_via (id),
    -- Ate quando o evento permanece vigente para o ciclo de decisao.
    vigente_ate  TIMESTAMPTZ,
    CHECK (vigente_ate IS NULL OR vigente_ate >= ocorrido_em)
);

CREATE INDEX evento_urbano_ocorrido_idx ON evento_urbano (ocorrido_em DESC);
CREATE INDEX evento_urbano_trecho_idx   ON evento_urbano (trecho_id, ocorrido_em DESC);

-- Evento novo acorda o servico de decisao na hora (LISTEN evento_urbano):
-- esperar o proximo ciclo de 5 s estouraria o RNF03 (< 2 s).
CREATE FUNCTION avisar_evento_urbano() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    PERFORM pg_notify('evento_urbano', NEW.id::text);
    RETURN NEW;
END $$;

CREATE TRIGGER evento_urbano_aviso
    AFTER INSERT ON evento_urbano
    FOR EACH ROW EXECUTE FUNCTION avisar_evento_urbano();

-- ---------------------------------------------------------------------------
-- Versao da base de regras Mamdani: condicao para reproduzir resultados.
-- ---------------------------------------------------------------------------
CREATE TABLE versao_base_regras (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rotulo         TEXT NOT NULL UNIQUE,
    vigente_desde  TIMESTAMPTZ NOT NULL DEFAULT now(),
    qtd_regras     INTEGER NOT NULL CHECK (qtd_regras > 0),
    resumo         TEXT NOT NULL,
    -- Hash do arquivo de regras, para detectar edicao sem nova versao.
    hash_regras    TEXT
);

-- ---------------------------------------------------------------------------
-- Versao do modelo de previsao (3.6). Sem ela, uma decisao so seria
-- reconstituivel pelo valor previsto gravado, e nao pelo modelo (RNF04).
-- A referencia de persistencia tambem e registrada como "modelo".
-- ---------------------------------------------------------------------------
CREATE TABLE versao_modelo_previsao (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rotulo           TEXT NOT NULL UNIQUE,
    algoritmo        TEXT NOT NULL
                     CHECK (algoritmo IN ('persistencia','media_sazonal','xgboost')),
    -- Serie de Melbourne em janela movel: a data de extracao fixa o recorte.
    serie_extraida_em DATE,
    treinado_em      TIMESTAMPTZ,
    mae              NUMERIC(10,4),
    rmse             NUMERIC(10,4),
    -- Hash do arquivo do modelo salvo.
    hash_modelo      TEXT
);

-- ---------------------------------------------------------------------------
-- Execucao de cenario (RF10, 3.9). Separa as rodadas no banco para comparar
-- regimes (3.11) e o acionamento antecipado x reativo (H3). Decisoes fora de
-- qualquer cenario (operacao livre, demonstracao) ficam com execucao NULL.
-- ---------------------------------------------------------------------------
CREATE TABLE execucao_cenario (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cenario        TEXT NOT NULL,
    -- adaptativo = sistema completo; as linhas de base de 3.11 tambem podem
    -- ser executadas para que a aderencia ao envelope seja medida igual.
    regime         TEXT NOT NULL DEFAULT 'adaptativo'
                   CHECK (regime IN ('adaptativo','pleno_constante','horario_fixo')),
    -- antecipado = inferencia recebe a previsao; reativo = nao recebe (H3).
    modo_previsao  TEXT NOT NULL DEFAULT 'antecipado'
                   CHECK (modo_previsao IN ('antecipado','reativo')),
    iniciada_em    TIMESTAMPTZ NOT NULL DEFAULT now(),
    encerrada_em   TIMESTAMPTZ,
    observacao     TEXT,
    CHECK (encerrada_em IS NULL OR encerrada_em >= iniciada_em)
);

-- ---------------------------------------------------------------------------
-- Decisao: nucleo do registro de auditoria. Separar nivel_pretendido de
-- nivel_emitido e o que torna mensuravel a camada de verificacao.
-- ---------------------------------------------------------------------------
CREATE TABLE decisao (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    criado_em              TIMESTAMPTZ NOT NULL DEFAULT now(),
    ponto_de_luz_id        BIGINT NOT NULL REFERENCES ponto_de_luz (id),
    versao_base_regras_id  BIGINT NOT NULL REFERENCES versao_base_regras (id),
    versao_modelo_id       BIGINT NOT NULL REFERENCES versao_modelo_previsao (id),
    execucao_id            BIGINT REFERENCES execucao_cenario (id),
    -- Classe vigente no momento da decisao: congela o criterio aplicado
    -- mesmo que a via seja reclassificada depois (4.7.2).
    classe_codigo          TEXT NOT NULL REFERENCES classe_iluminacao (codigo),
    -- Entrada da inferencia: saida da camada de previsao (NULL no modo reativo).
    previsao_movimentacao  NUMERIC(10,3),
    -- Fracao do fluxo pleno. 1,000 = 10 lux (P3); 0,500 = 5 lux (P5).
    nivel_pretendido       NUMERIC(4,3) NOT NULL CHECK (nivel_pretendido BETWEEN 0 AND 1),
    nivel_emitido          NUMERIC(4,3) NOT NULL CHECK (nivel_emitido    BETWEEN 0 AND 1),
    -- Qual regra da camada de verificacao corrigiu o nivel pretendido.
    restricao_aplicada     TEXT NOT NULL DEFAULT 'nenhuma'
                           CHECK (restricao_aplicada IN ('nenhuma','piso','taxa')),
    -- Nivel emitido na decisao anterior, base do limite de taxa.
    nivel_anterior         NUMERIC(4,3) CHECK (nivel_anterior BETWEEN 0 AND 1),
    publicado_em           TIMESTAMPTZ,
    -- Por que (painel e RNF04): entradas da inferencia (presenca, pessoas por
    -- trecho, ocorrencia, previsao, nivel recente, faixa horaria) e o grau de
    -- ativacao de cada regra.
    entrada                JSONB,
    ativacoes              JSONB,
    -- Invariante estrutural: correcao registrada <=> nivel alterado.
    CHECK ((restricao_aplicada = 'nenhuma') = (nivel_emitido = nivel_pretendido))
);

CREATE INDEX decisao_ponto_tempo_idx ON decisao (ponto_de_luz_id, criado_em DESC);
CREATE INDEX decisao_execucao_idx    ON decisao (execucao_id, criado_em)
    WHERE execucao_id IS NOT NULL;
CREATE INDEX decisao_restricao_idx   ON decisao (restricao_aplicada)
    WHERE restricao_aplicada <> 'nenhuma';

-- Entidade associativa (4.7.2): uma decisao apoia-se em varios eventos e um
-- evento sustenta decisoes sucessivas enquanto permanecer vigente.
CREATE TABLE decisao_evento (
    decisao_id  UUID   NOT NULL REFERENCES decisao (id) ON DELETE CASCADE,
    evento_id   BIGINT NOT NULL REFERENCES evento_urbano (id),
    PRIMARY KEY (decisao_id, evento_id)
);

CREATE INDEX decisao_evento_evento_idx ON decisao_evento (evento_id);

-- ---------------------------------------------------------------------------
-- Sessao de medicao (3.4.3): antes de cada sessao registra-se a iluminancia
-- residual com o modulo de luz desligado; ela e subtraida das leituras.
-- Sessao com residual acima de 5 % do valor da classe e descartada.
-- ---------------------------------------------------------------------------
CREATE TABLE sessao_medicao (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ponto_de_luz_id  BIGINT NOT NULL REFERENCES ponto_de_luz (id),
    iniciada_em      TIMESTAMPTZ NOT NULL DEFAULT now(),
    encerrada_em     TIMESTAMPTZ,
    lux_residual     NUMERIC(8,2) NOT NULL CHECK (lux_residual >= 0),
    -- Valor da classe do ponto no inicio da sessao, congelado como na decisao.
    lux_classe       NUMERIC(6,2) NOT NULL CHECK (lux_classe > 0),
    -- Criterio metodologico de 3.4.3 (nao normativo).
    descartada       BOOLEAN GENERATED ALWAYS AS (lux_residual > 0.05 * lux_classe) STORED,
    observacao       TEXT
);

-- ---------------------------------------------------------------------------
-- Telemetria: 1:1 com a decisao (4.7.2). Leituras periodicas que nao
-- correspondam a comando nao sao registradas aqui.
-- ---------------------------------------------------------------------------
CREATE TABLE telemetria (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    decisao_id       UUID NOT NULL UNIQUE REFERENCES decisao (id),
    ponto_de_luz_id  BIGINT NOT NULL REFERENCES ponto_de_luz (id),
    sessao_id        BIGINT REFERENCES sessao_medicao (id),
    -- Relogio do no (NTP); a latencia do RNF03 usa so relogios do servidor.
    medido_em        TIMESTAMPTZ NOT NULL,
    recebido_em      TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Ciclo de trabalho aplicado, 0..1 (PWM de 12 bits no no).
    duty             NUMERIC(5,4) NOT NULL CHECK (duty BETWEEN 0 AND 1),
    lux_medido       NUMERIC(8,2) NOT NULL CHECK (lux_medido >= 0)
);

CREATE INDEX telemetria_ponto_tempo_idx ON telemetria (ponto_de_luz_id, medido_em DESC);

-- ---------------------------------------------------------------------------
-- Calibracao do no (3.3, 3.4.2, 3.4.4): varredura de duty x lux medido, em
-- series independentes. Fonte da tabela nivel -> duty gravada no firmware e
-- base da repetibilidade que fixa a tolerancia do diagnostico (3.4.5).
-- ---------------------------------------------------------------------------
CREATE TABLE calibracao (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sessao_id   BIGINT NOT NULL REFERENCES sessao_medicao (id),
    serie       INTEGER NOT NULL CHECK (serie > 0),
    duty        NUMERIC(5,4) NOT NULL CHECK (duty BETWEEN 0 AND 1),
    lux_medido  NUMERIC(8,2) NOT NULL CHECK (lux_medido >= 0),
    medido_em   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (sessao_id, serie, duty)
);

-- ---------------------------------------------------------------------------
-- Alertas de diagnostico (RF11, 3.4.5).
-- ---------------------------------------------------------------------------
CREATE TABLE alerta_diagnostico (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ponto_de_luz_id  BIGINT NOT NULL REFERENCES ponto_de_luz (id),
    -- Decisao em que a condicao foi constatada.
    decisao_id       UUID REFERENCES decisao (id),
    tipo             TEXT NOT NULL CHECK (tipo IN ('falha_total','perda_controle')),
    -- Razao entregue/esperado que disparou o alerta e parametros usados.
    razao            NUMERIC(6,3),
    tolerancia       NUMERIC(6,3),
    ciclos           INTEGER CHECK (ciclos > 0),
    aberto_em        TIMESTAMPTZ NOT NULL DEFAULT now(),
    encerrado_em     TIMESTAMPTZ,
    CHECK (encerrado_em IS NULL OR encerrado_em >= aberto_em)
);

CREATE INDEX alerta_aberto_idx ON alerta_diagnostico (ponto_de_luz_id)
    WHERE encerrado_em IS NULL;

-- ---------------------------------------------------------------------------
-- Visao de auditoria: cadeia evento -> decisao -> medicao.
--   latencia_evento: RNF03, do recebimento do evento ate a chegada da
--     telemetria da PRIMEIRA decisao que o consumiu (so relogios do
--     servidor; inclui a volta). NULL nas decisoes seguintes, que apenas
--     mantem o evento vigente.
--   razao_entregue: diagnostico por RAZAO (3.4.4/3.4.5) - um erro de escala
--     do sensor cancela-se; a residual da sessao e subtraida (3.4.3).
-- ---------------------------------------------------------------------------
CREATE VIEW auditoria_decisao AS
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
           / NULLIF(d.nivel_emitido * c.iluminancia_media_min_lux, 0) AS razao_entregue,
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
