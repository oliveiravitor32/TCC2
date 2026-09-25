// GERADO por bancada/calibrar.py - nao edite a mao.
// Sessao 72 (bancada real),
// 2026-09-25T02:46:27.191533+00:00. Classe P3: 1,0 = 10.0 lx, piso = 5.0 lx.
// duty(1,0) = 2352 e duty(piso) = 1217 foram MEDIDOS (3.4.2).
#pragma once

struct PontoCalibracao { float nivel; int duty; };

const PontoCalibracao CALIBRACAO[] = {
  {0.0000f, 0},
  {0.0303f, 128},
  {0.0830f, 256},
  {0.1360f, 384},
  {0.1920f, 512},
  {0.2490f, 640},
  {0.3060f, 768},
  {0.3620f, 896},
  {0.4190f, 1024},
  {0.4750f, 1152},
  {0.5000f, 1217},
  {0.5320f, 1280},
  {0.5890f, 1408},
  {0.6438f, 1536},
  {0.7007f, 1664},
  {0.7531f, 1792},
  {0.8101f, 1920},
  {0.8613f, 2048},
  {0.9182f, 2175},
  {0.9757f, 2303},
  {1.0000f, 2352}
};
const int N_CALIBRACAO = 21;
const int CALIBRACAO_SESSAO = 72;
