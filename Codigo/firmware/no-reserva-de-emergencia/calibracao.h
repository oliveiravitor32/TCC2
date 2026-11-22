// GERADO por bancada/calibrar.py - nao edite a mao.
// Sessao 124 (bancada real),
// 2026-11-22T04:37:52.468236+00:00. Classe P3: 1,0 = 10.0 lx, piso = 5.0 lx.
// duty(1,0) = 2099 e duty(piso) = 1077 foram MEDIDOS (3.4.2).
#pragma once

struct PontoCalibracao { float nivel; int duty; };

const PontoCalibracao CALIBRACAO[] = {
  {0.0000f, 0},
  {0.0450f, 128},
  {0.1020f, 256},
  {0.1700f, 384},
  {0.2260f, 512},
  {0.2940f, 640},
  {0.3510f, 768},
  {0.4190f, 896},
  {0.4750f, 1024},
  {0.5000f, 1077},
  {0.5430f, 1152},
  {0.6000f, 1280},
  {0.6680f, 1408},
  {0.7240f, 1536},
  {0.7920f, 1664},
  {0.8490f, 1792},
  {0.9170f, 1920},
  {0.9730f, 2048},
  {1.0000f, 2099}
};
const int N_CALIBRACAO = 19;
const int CALIBRACAO_SESSAO = 124;
