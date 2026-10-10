// GERADO por bancada/calibrar.py - nao edite a mao.
// Sessao 113 (bancada real),
// 2026-10-10T03:04:44.372841+00:00. Classe P3: 1,0 = 10.0 lx, piso = 5.0 lx.
// duty(1,0) = 2687 e duty(piso) = 1392 foram MEDIDOS (3.4.2).
#pragma once

struct PontoCalibracao { float nivel; int duty; };

const PontoCalibracao CALIBRACAO[] = {
  {0.0000f, 0},
  {0.0230f, 128},
  {0.0680f, 256},
  {0.1250f, 384},
  {0.1700f, 512},
  {0.2150f, 640},
  {0.2640f, 768},
  {0.3170f, 896},
  {0.3620f, 1024},
  {0.4097f, 1152},
  {0.4640f, 1280},
  {0.5000f, 1392},
  {0.5090f, 1408},
  {0.5550f, 1536},
  {0.6110f, 1664},
  {0.6560f, 1792},
  {0.7020f, 1920},
  {0.7580f, 2048},
  {0.8040f, 2175},
  {0.8514f, 2303},
  {0.9060f, 2431},
  {0.9510f, 2559},
  {1.0000f, 2687}
};
const int N_CALIBRACAO = 23;
const int CALIBRACAO_SESSAO = 113;
