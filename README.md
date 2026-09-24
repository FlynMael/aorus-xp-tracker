# Aorus XP Tracker

Coleta automática (a cada 30 min, disparada pelo cron-job.org) dos dados de XP/level/kills/battleEXP dos players
listados em `players.txt`, a partir da API pública do
https://aorus-xp-tracker.vercel.app/. O histórico fica em `data/history.csv`.

## Como ativar

1. Crie um repositório novo no GitHub e suba todos estes arquivos.
2. O workflow `.github/workflows/track.yml` é disparado a cada 30 min pelo
   cron-job.org (via `workflow_dispatch`). Não usa o cron nativo do GitHub.
3. Para rodar manualmente: aba **Actions** → **Aorus XP Tracker** → **Run workflow**.

## Editar a lista de players

Edite `players.txt` (um nome por linha) e faça commit. Na próxima execução o
script já passa a coletar os novos nomes.

## Onde ficam os dados

`data/history.csv` — uma linha por player a cada snapshot novo, com colunas:
`created_at, name, clan, level, percent, battleEXP, kills, classId`.
`data/drops.csv` — drops dos players listados.
`data/pvp_rank.json` — rank PvP de todos os players do servidor (top 30 geral e top do dia).
