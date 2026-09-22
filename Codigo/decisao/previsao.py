"""Camada de previsao (TCC 3.6).

Enquanto o modelo XGBoost nao e treinado (Etapa 3, passo 8), a previsao e a
referencia ingenua de PERSISTENCIA: a movimentacao esperada na proxima
janela e a observada agora. E tambem uma das duas referencias contra as
quais o modelo treinado sera comparado.

Consequencia a lembrar: com persistencia, os modos antecipado e reativo
produzem as mesmas decisoes. A comparacao de H3 so tem sentido com o modelo.
"""

from __future__ import annotations

from typing import Protocol


class Previsor(Protocol):
    rotulo: str  # deve existir em versao_modelo_previsao

    def prever(self, observada: float) -> float: ...


class Persistencia:
    rotulo = "persistencia"

    def prever(self, observada: float) -> float:
        return observada
