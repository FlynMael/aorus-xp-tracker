path = "docs/index.html"
s = open(path, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)

CSS = r'''
  /* ===== ANÁLISE ===== */
  #bottom-nav button{ font-size:9.5px; letter-spacing:.08em; }
  .an-pick{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin-bottom:10px; }
  .an-pick label{ display:block; font-family:'IBM Plex Mono', monospace; font-size:11px; letter-spacing:.16em; text-transform:uppercase; margin-bottom:6px; }
  .an-pick select{
    width:100%; min-height:44px; padding:0 12px; border-radius:12px; border:1px solid var(--line);
    background:var(--bg-elevated); color:var(--text); font-family:'Cinzel', serif; font-weight:600; font-size:15px;
  }
  .an-a{ color:var(--gold); } .an-b{ color:var(--kills); }
  .an-duel{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin-bottom:10px; }
  .an-side{ padding:14px; background:var(--bg-elevated); border:1px solid var(--line); border-radius:14px; min-width:0; }
  .an-side.win{ border-color:var(--gold); }
  .an-name{ font-family:'Cinzel', serif; font-weight:600; font-size:16px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .an-xp{ font-family:'IBM Plex Mono', monospace; font-weight:600; font-size:20px; margin-top:6px; overflow-wrap:anywhere; }
  .an-sub{ font-family:'IBM Plex Mono', monospace; font-size:11.5px; color:var(--text-muted); margin-top:2px; }
  .an-split{ display:flex; height:14px; border-radius:999px; overflow:hidden; border:1px solid var(--line); background:var(--bg); margin:4px 0 8px; }
  .an-split div:first-child{ background:var(--gold); } .an-split div:last-child{ background:var(--kills); }
  .an-split-legend{ display:flex; justify-content:space-between; font-family:'IBM Plex Mono', monospace; font-size:12px; }
  .an-insight{ margin:0; padding:0; list-style:none; display:flex; flex-direction:column; gap:10px; }
  .an-insight li{ font-size:14px; line-height:1.45; }
  .an-insight b{ font-weight:600; }
  .an-table{ width:100%; border-collapse:collapse; font-family:'IBM Plex Mono', monospace; font-size:12.5px; }
  .an-table th, .an-table td{ padding:9px 4px; border-bottom:1px solid var(--line); text-align:right; }
  .an-table th:first-child, .an-table td:first-child{ text-align:left; color:var(--text-muted); font-weight:400; }
  .an-table tr:last-child td{ border-bottom:none; }
  .an-chart{ display:flex; align-items:flex-end; gap:8px; height:140px; }
  .an-day{ flex:1; display:flex; align-items:flex-end; justify-content:center; gap:3px; height:100%; }
  .an-day i{ display:block; width:45%; border-radius:4px 4px 1px 1px; min-height:2px; }
  .an-day i.a{ background:var(--gold); } .an-day i.b{ background:var(--kills); }
  .an-legend{ display:flex; gap:14px; font-family:'IBM Plex Mono', monospace; font-size:11.5px; color:var(--text-muted); }
  .an-legend span::before{ content:""; display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:6px; vertical-align:-1px; }
  .an-legend .la::before{ background:var(--gold); } .an-legend .lb::before{ background:var(--kills); }
'''

JS = r'''// ---------- ANÁLISE (comparação entre dois players) ----------
let anA = null, anB = null, anPeriod = "today";
const AN_PERIODS = [["today", "Hoje"], ["24h", "24h"], ["7d", "7 dias"], ["30d", "30 dias"]];
const AN_VIEWS = ["players-view", "ranking-view", "pvp-view", "rankpvp-view", "drops-view", "patentes-view", "daily-view", "bosses-view"];

function showAnalise(){
  AN_VIEWS.forEach(id => { const el = document.getElementById(id); if(el) el.style.display = "none"; });
  document.getElementById("analise-view").style.display = "block";
  navSection = "analise";
  renderNav();
  renderAnalise();
}

function xpAbs(r){ return getAbsoluteXp(Number(r.level), Number(r.percent)); }
function fmtXp(n){ return Math.round(n).toLocaleString("pt-BR"); }
function fmtPct(n){ return n.toLocaleString("pt-BR", { maximumFractionDigits: 1 }); }

function anGains(name, mode){
  const r = latestAndPast(name, mode);
  if(!r) return null;
  const { latest, past } = r;
  return {
    name: latest.name,
    level: Number(latest.level),
    percent: Number(latest.percent),
    xp: Math.max(0, xpAbs(latest) - xpAbs(past)),
    bexp: Number(latest.battleEXP) - Number(past.battleEXP),
    kills: Number(latest.kills) - Number(past.kills),
  };
}

function anDaily(name){
  const rows = allRows.filter(r => r.name.toLowerCase() === name.toLowerCase()).sort((a, b) => a.ts - b.ts);
  const out = [];
  const wd = ["Dom","Seg","Ter","Qua","Qui","Sex","Sáb"];
  for(let i = 6; i >= 0; i--){
    const d = new Date(); d.setDate(d.getDate() - i);
    const { startTs, endTs } = getDayBoundsTs(localISODate(d));
    let gain = 0;
    if(rows.length && rows[0].ts <= endTs){
      const end = findSnapshotAtOrBefore(rows, endTs);
      const start = rows[0].ts <= startTs ? findSnapshotAtOrBefore(rows, startTs) : rows[0];
      gain = Math.max(0, xpAbs(end) - xpAbs(start));
    }
    out.push({ wd: wd[d.getDay()], day: d.getDate(), gain });
  }
  return out;
}

function renderAnalise(){
  const el = document.getElementById("analise-view");
  if(!el) return;
  const players = TRACKED_PLAYERS.slice();
  if(players.length < 2){ el.innerHTML = `<div class="empty">Precisa de pelo menos 2 players no grupo.</div>`; return; }
  if(!anA || !players.includes(anA)) anA = players[0];
  if(!anB || !players.includes(anB) || anB === anA) anB = players.find(p => p !== anA);

  const opts = sel => players.map(p => `<option value="${esc(p)}" ${p === sel ? "selected" : ""}>${esc(p)}</option>`).join("");
  const seg = AN_PERIODS.map(([k, l]) => `<button class="${k === anPeriod ? "active" : ""}" data-anp="${k}">${l}</button>`).join("");
  const label = (AN_PERIODS.find(p => p[0] === anPeriod) || [, ""])[1].toLowerCase();

  const A = anGains(anA, anPeriod), B = anGains(anB, anPeriod);
  let body = "";
  if(!A || !B){
    body = `<div class="empty">Ainda sem dados suficientes pra comparar.</div>`;
  }else{
    const total = A.xp + B.xp;
    const shareA = total > 0 ? A.xp / total * 100 : 50;
    const shareB = 100 - shareA;
    const winner = A.xp === B.xp ? null : (A.xp > B.xp ? A : B);
    const loser = winner ? (winner === A ? B : A) : null;
    const diff = winner ? winner.xp - loser.xp : 0;

    const insights = [];
    if(total === 0){
      insights.push(`Nenhum dos dois ganhou XP ${label === "hoje" ? "hoje" : "no período (" + label + ")"}.`);
    }else if(!winner){
      insights.push(`Empate: os dois fizeram <b>${fmtXp(A.xp)} XP</b>.`);
    }else{
      const cls = winner === A ? "an-a" : "an-b";
      const lcls = winner === A ? "an-b" : "an-a";
      if(loser.xp > 0){
        insights.push(`<b class="${cls}">${esc(winner.name)}</b> fez <b>${fmtPct(diff / loser.xp * 100)}% mais XP</b> que <b class="${lcls}">${esc(loser.name)}</b>.`);
      }else{
        insights.push(`<b class="${lcls}">${esc(loser.name)}</b> não ganhou XP no período; <b class="${cls}">${esc(winner.name)}</b> fez tudo.`);
      }
      insights.push(`<b class="${lcls}">${esc(loser.name)}</b> deixou de ganhar <b>${fmtXp(diff)} XP</b> em relação a <b class="${cls}">${esc(winner.name)}</b>.`);
      insights.push(`Do total de XP dos dois, <b class="${cls}">${esc(winner.name)}</b> ficou com <b>${fmtPct(Math.max(shareA, shareB))}%</b>.`);
      const nextLoser = LEVEL_XP_TABLE[loser.level] && LEVEL_XP_TABLE[loser.level].next;
      if(nextLoser) insights.push(`Essa diferença equivale a <b>${fmtPct(diff / nextLoser * 100)}%</b> de um level ${loser.level} de <b class="${lcls}">${esc(loser.name)}</b>.`);
    }

    const days = { a: anDaily(anA), b: anDaily(anB) };
    const max = Math.max(1, ...days.a.map(d => d.gain), ...days.b.map(d => d.gain));
    const sumA = days.a.reduce((s, d) => s + d.gain, 0), sumB = days.b.reduce((s, d) => s + d.gain, 0);
    const winsA = days.a.filter((d, i) => d.gain > days.b[i].gain).length;
    const winsB = days.b.filter((d, i) => d.gain > days.a[i].gain).length;
    const signedN = n => `${n > 0 ? "+" : ""}${n.toLocaleString("pt-BR")}`;

    body = `
      <div class="an-duel">
        <div class="an-side ${winner === A ? "win" : ""}"><div class="an-name an-a">${esc(A.name)}</div><div class="an-xp">${fmtXp(A.xp)}</div><div class="an-sub">XP · ${label}</div></div>
        <div class="an-side ${winner === B ? "win" : ""}"><div class="an-name an-b">${esc(B.name)}</div><div class="an-xp">${fmtXp(B.xp)}</div><div class="an-sub">XP · ${label}</div></div>
      </div>
      <div class="panel">
        <div class="panel-head"><span class="sum-label">Divisão da XP</span></div>
        <div class="an-split" role="img" aria-label="${esc(A.name)} ${fmtPct(shareA)}%, ${esc(B.name)} ${fmtPct(shareB)}%"><div style="width:${shareA}%"></div><div style="width:${shareB}%"></div></div>
        <div class="an-split-legend"><span class="an-a">${fmtPct(shareA)}%</span><span class="an-b">${fmtPct(shareB)}%</span></div>
      </div>
      <div class="panel"><ul class="an-insight">${insights.map(t => `<li>${t}</li>`).join("")}</ul></div>
      <div class="panel">
        <div class="panel-head"><span class="sum-label">Lado a lado · ${label}</span></div>
        <table class="an-table">
          <tr><th></th><th class="an-a">${esc(A.name)}</th><th class="an-b">${esc(B.name)}</th></tr>
          <tr><td>XP ganha</td><td>${fmtXp(A.xp)}</td><td>${fmtXp(B.xp)}</td></tr>
          <tr><td>Level atual</td><td>${A.level} · ${fmtPct(A.percent)}%</td><td>${B.level} · ${fmtPct(B.percent)}%</td></tr>
          <tr><td>Battle XP</td><td>${signedN(A.bexp)}</td><td>${signedN(B.bexp)}</td></tr>
          <tr><td>Kills</td><td>${signedN(A.kills)}</td><td>${signedN(B.kills)}</td></tr>
        </table>
      </div>
      <div class="panel">
        <div class="panel-head"><span class="sum-label">XP por dia · 7 dias</span></div>
        <div class="an-chart">${days.a.map((d, i) => `<div class="an-day"><i class="a" style="height:${d.gain / max * 100}%" title="${fmtXp(d.gain)}"></i><i class="b" style="height:${days.b[i].gain / max * 100}%" title="${fmtXp(days.b[i].gain)}"></i></div>`).join("")}</div>
        <div class="chart-labels">${days.a.map(d => `<div>${d.wd}<br>${d.day}</div>`).join("")}</div>
        <div class="an-legend" style="margin-top:12px;"><span class="la">${esc(A.name)} · ${fmtXp(sumA)}</span><span class="lb">${esc(B.name)} · ${fmtXp(sumB)}</span></div>
        <div class="an-sub" style="margin-top:8px;">Dias vencidos: ${esc(A.name)} ${winsA} × ${winsB} ${esc(B.name)}</div>
      </div>`;
  }

  el.innerHTML = `
    <div class="sec-title"><h2>Análise</h2><span>compare dois players</span></div>
    <div class="an-pick">
      <div><label for="an-a" class="an-a">Player A</label><select id="an-a">${opts(anA)}</select></div>
      <div><label for="an-b" class="an-b">Player B</label><select id="an-b">${opts(anB)}</select></div>
    </div>
    <div class="seg" id="an-period">${seg}</div>
    ${body}`;

  document.getElementById("an-a").addEventListener("change", e => {
    const v = e.target.value; if(v === anB) anB = anA; anA = v; renderAnalise();
  });
  document.getElementById("an-b").addEventListener("change", e => {
    const v = e.target.value; if(v === anA) anA = anB; anB = v; renderAnalise();
  });
  el.querySelectorAll("#an-period button").forEach(b => b.addEventListener("click", () => { anPeriod = b.dataset.anp; renderAnalise(); }));
}

const _anRenderPlayerList = renderPlayerList;
renderPlayerList = function(){
  _anRenderPlayerList();
  if(navSection === "analise") renderAnalise();
};

'''

NAV_BTN = '<button data-section="analise"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 20h18"></path><path d="M6 20v-7"></path><path d="M11 20V5"></path><path d="M16 20v-10"></path><path d="M20 8l-4-3-5 3-5-2"></path></svg><span>Análise</span></button>'

rep("</style>", CSS + "</style>")
rep('<button data-section="drops">', NAV_BTN + '<button data-section="drops">')
rep('    <section id="drops-view" style="display:none;">', '    <section id="analise-view" style="display:none;"></section>\n\n    <section id="drops-view" style="display:none;">')
rep('  else if(s === "drops") goTab("drops");', '  else if(s === "analise") showAnalise();\n  else if(s === "drops") goTab("drops");')
rep('function syncNavFromTab(tab){\n', 'function syncNavFromTab(tab){\n  const av = document.getElementById("analise-view"); if(av) av.style.display = "none";\n')
rep('          <div class="guide-item">\n            <div class="guide-item-title">🏆 Rank</div>',
    '          <div class="guide-item">\n            <div class="guide-item-title">📊 Análise</div>\n            <p>Escolha <b>dois players do grupo</b> e compare a XP de level que cada um fez <b>hoje, em 24h, 7 ou 30 dias</b>: quem fez mais, quantos % a mais, quanto o outro deixou de ganhar e o gráfico dia a dia.</p>\n          </div>\n          <div class="guide-item">\n            <div class="guide-item-title">🏆 Rank</div>')
rep("// Se já desbloqueou antes nesse aparelho", JS + "// Se já desbloqueou antes nesse aparelho")
open(path, "w", encoding="utf-8").write(s)
print("ok")
