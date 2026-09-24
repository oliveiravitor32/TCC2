# Painel de acompanhamento

Interface de apresentação do sistema (TCC 4.6.1, RF08). Mostra, lado a lado,
**o dado recebido**, **o nível pretendido pela inferência**, **a correção imposta pela
camada de verificação** e **a iluminância medida no nó** — a cadeia que torna a
conformidade normativa observável durante a execução e durante a defesa.

É um aplicativo **só de leitura**: não publica evento e não comanda nada. Consome a
interface REST do Quadro 14 (`/pontos`, `/decisoes`, `/telemetria`, `/eventos`,
`/alertas`), atualizando a cada 2 s.

Stack: Vite + React + Tailwind CSS 4 + lucide-react.

## Rodar localmente

Com o banco, a API, o serviço de decisão e o nó (real ou simulado) no ar:

```bash
cd Codigo && docker compose up -d
```

```bash
cd Codigo && .venv/Scripts/python -m uvicorn api_eventos.app:app --port 8000
```

```bash
cd Codigo && .venv/Scripts/python -m decisao.servico
```

```bash
cd Codigo && .venv/Scripts/python -m simulador.no_simulado
```

E então o painel:

```bash
cd Codigo/painel && npm install && npm run dev
```

O endereço da API vem de `VITE_API_URL` (veja `.env.example`). Em desenvolvimento,
`.env.local` aponta para `http://localhost:8000`.

## Publicar na Vercel

O painel é o único componente que **não** sobe na VM: ele é estático e vai para a
Vercel. O resto (API, decisão, broker, banco) continua em Docker na VM Oracle.

1. Importe o repositório na Vercel.
2. Em **Root Directory**, selecione `Codigo/painel`. Sem isso, o build falha, porque
   a raiz do repositório não é um projeto Node.
3. Framework: **Vite** (detectado sozinho). Build: `npm run build`. Saída: `dist`.
4. Em **Environment Variables**, defina `VITE_API_URL` com a URL pública da API na VM,
   por exemplo `https://api.seu-dominio.com`. A variável é lida **na hora do build**:
   ao trocá-la, refaça o deploy.

### Dois cuidados do lado da VM

- **CORS**: a API precisa autorizar a origem da Vercel. Defina `ORIGENS_PAINEL` com a
  URL do painel (ex.: `https://painel.vercel.app`). O padrão é `*`, que serve para
  testar, mas convém restringir antes da defesa.
- **HTTPS**: a Vercel serve o painel por HTTPS, e o navegador **bloqueia** chamadas a
  uma API em HTTP puro (conteúdo misto). A API precisa estar atrás de HTTPS — é o que
  o proxy do passo 10 resolve.

## Estrutura

```
src/api.js                  cliente REST e rótulos (restrições, estados)
src/App.jsx                 layout, ciclo de atualização e cálculo da latência
src/componentes/Cartoes.jsx a cadeia da decisão em quatro cartões
src/componentes/Trajetoria.jsx  gráfico SVG: pretendido × emitido × medido × piso
src/componentes/Listas.jsx  registro de decisões, eventos e alertas (RF11)
```
