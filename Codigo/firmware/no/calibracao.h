// GERADO por bancada/calibrar.py - nao edite a mao.
// Sessao 115 (bancada real),
// 2026-10-10T19:26:51.755460+00:00. Classe P3: 1,0 = 10.0 lx, piso = 5.0 lx.
// duty(1,0) = 2462 e duty(piso) = 1275 foram MEDIDOS (3.4.2).
#pragma once

struct PontoCalibracao { float nivel; int duty; };

const PontoCalibracao CALIBRACAO[] = {
  {0.0000f, 0},
  {0.0230f, 128},
  {0.0790f, 256},
  {0.1360f, 384},
  {0.1822f, 512},
  {0.2380f, 640},
  {0.2940f, 768},
  {0.3498f, 896},
  {0.3960f, 1024},
  {0.4530f, 1152},
  {0.5000f, 1275},
  {0.5090f, 1280},
  {0.5550f, 1408},
  {0.6110f, 1536},
  {0.6680f, 1664},
  {0.7228f, 1792},
  {0.7700f, 1920},
  {0.8260f, 2048},
  {0.8830f, 2175},
  {0.9329f, 2303},
  {0.9850f, 2431},
  {1.0000f, 2462}
};
const int N_CALIBRACAO = 22;
const int CALIBRACAO_SESSAO = 115;
