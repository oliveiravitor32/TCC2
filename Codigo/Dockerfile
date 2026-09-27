# Imagem unica dos servicos Python (API de eventos e servico de decisao).
# Serve para x86 e ARM (a VM da Oracle e ARM): todas as dependencias tem
# pacote pronto para as duas arquiteturas.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Dependencias primeiro (camada em cache): a lista vem do pyproject.toml,
# para nao existirem duas listas que possam divergir.
COPY pyproject.toml .
RUN python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']))" > /tmp/req.txt \
 && pip install --no-cache-dir -r /tmp/req.txt

COPY api_eventos ./api_eventos
COPY decisao ./decisao
COPY modelo/__init__.py modelo/modelo_previsao.json ./modelo/
COPY modelo/resultados/metricas.json ./modelo/resultados/

# Sem privilegio de root dentro do conteiner.
RUN useradd --create-home --uid 10001 app
USER app
