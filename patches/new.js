// ---------- NOVO LAYOUT (v2) ----------
const CLASS_NAMES = {1:"Lutador",2:"Mecânico",3:"Arqueira",4:"Pikeman",5:"Atalanta",6:"Cavaleiro",7:"Mago",8:"Sacerdotisa",9:"Assassina",10:"Shaman"};
const TAB_SECTION = { players:"grupo", ranking:"ranking", pvp:"ranking", daily:"ranking", patentes:"ranking", rankpvp:"ranking", drops:"drops", bosses:"boss" };
const DROP_TAG = { fragment:"Fragmento", gem:"Gema", shelton:"Shelton", other:"Outro" };
let navSection = "grupo";
let rankScope = "grupo";
let rankGroupTab = "ranking";
let detailOpen = false;

function goTab(t){
  const el = document.querySelector(`.tab[data-tab="${t}"]`);
  if(el) el.click();
}

function renderNav(){
  document.querySelectorAll("#bottom-nav button").forEach(b => {
    const on = b.dataset.section === navSection;
    b.classList.toggle("active", on);
    if(on) b.setAttribute("aria-current", "page"); else b.removeAttribute("aria-current");
  });
  document.getElementById("subnav").style.display = navSection === "ranking" ? "block" : "none";
  document.getElementById("seg-group").style.display = rankScope === "grupo" ? "flex" : "none";
  document.querySelectorAll("#seg-scope button").forEach(b => b.classList.toggle("active", b.dataset.scope === rankScope));
  document.querySelectorAll("#seg-group button").forEach(b => b.classList.toggle("active", b.dataset.gtab === rankGroupTab));
}

function syncNavFromTab(tab){
  navSection = TAB_SECTION[tab] || "grupo";
  if(tab === "rankpvp") rankScope = "servidor";
  else if(navSection === "ranking"){ rankScope = "grupo"; rankGroupTab = tab; }
  renderNav();
}

function setSection(s){
  if(s === "grupo"){ closePlayerDetail(); goTab("players"); }
  else if(s === "ranking") goTab(rankScope === "servidor" ? "rankpvp" : rankGroupTab);
  else if(s === "drops") goTab("drops");
  else goTab("bosses");
  window.scrollTo(0, 0);
}

document.querySelectorAll("#bottom-nav button").forEach(b => b.addEventListener("click", () => setSection(b.dataset.section)));
document.querySelectorAll("#seg-scope button").forEach(b => b.addEventListener("click", () => {
  rankScope = b.dataset.scope;
  goTab(rankScope === "servidor" ? "rankpvp" : rankGroupTab);
}));
document.querySelectorAll("#seg-group button").forEach(b => b.addEventListener("click", () => goTab(b.dataset.gtab)));

function levelGain(past, latest){
  const lv = Number(latest.level) - Number(past.level);
  const pct = Number(latest.percent) - Number(past.percent) + lv * 100;
  return pct;
}
function fmtNum(n){ return Number(n).toLocaleString("pt-BR"); }
function signed(n, suffix){ return `${n > 0 ? "+" : ""}${fmtNum(n)}${suffix}`; }
function todayDrops(){ const t = localISODate(new Date()); return allDropsCache.filter(d => d.date === t); }

function nextBossInfo(){
  const { now, list } = getAllBossOccurrences();
  const up = list.filter(b => b.next && b.next.getTime() > now.getTime()).sort((a,b) => a.next - b.next);
  if(up.length === 0) return null;
  const ts = up[0].next.getTime();
  const same = up.filter(b => b.next.getTime() === ts);
  const after = up.find(b => b.next.getTime() > ts);
  return { now, first: up[0], names: same.map(b => b.nome).join(", "), after };
}

function renderHomeSummary(){
  const el = document.getElementById("home-summary");
  if(!el) return;
  let kills = 0;
  TRACKED_PLAYERS.forEach(name => {
    const r = latestAndPast(name);
    if(r) kills += Math.max(0, Number(r.latest.kills) - Number(r.past.kills));
  });
  const td = todayDrops();
  const sheltons = td.filter(d => categorizeItem(d.item) === "shelton").length;
  const nb = nextBossInfo();
  const bossHtml = nb ? `
    <button class="next-boss" id="home-boss">
      <span class="nb-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5"></circle><path d="M12 7.5V12l3 2"></path></svg></span>
      <span class="nb-info">
        <span class="nb-name" style="display:block;">${esc(nb.names)}</span>
        <span class="nb-meta" style="display:block;">${formatWhen(nb.first.next, nb.now)}${nb.after ? ` · depois ${esc(nb.after.nome)} ${formatWhen(nb.after.next, nb.now)}` : ""}</span>
      </span>
      <span class="nb-cd">${formatCountdown(nb.first.next - nb.now)}</span>
    </button>` : "";
  el.innerHTML = `
    <div class="sum-row">
      <div class="sum-tile"><div class="sum-label">Kills 24h</div><div class="sum-value" style="color:var(--kills)">${fmtNum(kills)}</div><div class="sum-sub">do grupo</div></div>
      <div class="sum-tile"><div class="sum-label">Drops hoje</div><div class="sum-value" style="color:var(--gold)">${fmtNum(td.length)}</div><div class="sum-sub">${sheltons} shelton${sheltons === 1 ? "" : "s"}</div></div>
    </div>
    ${bossHtml}
    <div class="sec-title"><h2>Players</h2><span>${TRACKED_PLAYERS.length} · ordem por nível</span></div>`;
  const hb = document.getElementById("home-boss");
  if(hb) hb.addEventListener("click", () => setSection("boss"));
}

renderPlayerList = function(){
  const el = document.getElementById("player-list");
  const items = TRACKED_PLAYERS.map(name => ({ name, r: latestAndPast(name) }));
  items.sort((a, b) => {
    if(!a.r) return 1; if(!b.r) return -1;
    return (Number(b.r.latest.level) - Number(a.r.latest.level)) || (Number(b.r.latest.percent) - Number(a.r.latest.percent));
  });
  el.innerHTML = items.map(({ name, r }) => {
    if(!r) return `<div class="pcard"><div class="pc-top"><div class="mono-badge">${esc(name[0].toUpperCase())}</div><div class="pc-id"><div class="pc-name">${esc(name)}</div><div class="pc-sub">sem dados</div></div></div></div>`;
    const { latest, past } = r;
    const pct = Math.min(100, Math.max(0, Number(latest.percent)));
    const lg = levelGain(past, latest);
    const k = Number(latest.kills) - Number(past.kills);
    const x = Number(latest.battleEXP) - Number(past.battleEXP);
    const cls = CLASS_NAMES[Number(latest.classId)] || "";
    return `<button class="pcard" data-name="${esc(name)}">
      <div class="pc-top">
        <div class="mono-badge" aria-hidden="true">${esc(latest.name[0].toUpperCase())}</div>
        <div class="pc-id"><div class="pc-name">${esc(latest.name)}</div><div class="pc-sub">${esc([cls, latest.clan].filter(Boolean).join(" · "))}</div></div>
        <span class="pill gold">Lv ${esc(latest.level)}</span>
      </div>
      <div>
        <div class="bar-head"><span>Progresso do nível</span><b>${pct.toFixed(2).replace(".", ",")}%</b></div>
        <div class="bar"><div class="bar-fill" style="width:${pct}%"></div></div>
      </div>
      <div class="chips">
        <span class="chip ${lg > 0 ? "gold" : ""}">${lg > 0 ? "+" : ""}${lg.toFixed(2).replace(".", ",")}% 24h</span>
        <span class="chip ${k > 0 ? "blue" : ""}">${signed(k, " kills")}</span>
        <span class="chip ${x > 0 ? "gold" : ""}">${signed(x, " XP")}</span>
      </div>
    </button>`;
  }).join("");
  el.querySelectorAll(".pcard[data-name]").forEach(row => row.addEventListener("click", () => openPlayerDetail(row.dataset.name)));
  renderHomeSummary();
};

function openPlayerDetail(name){
  detailOpen = true;
  document.getElementById("home-summary").style.display = "none";
  document.getElementById("player-list").style.display = "none";
  selectPlayer(name);
  window.scrollTo(0, 0);
}

function closePlayerDetail(){
  detailOpen = false;
  document.getElementById("home-summary").style.display = "";
  document.getElementById("player-list").style.display = "";
  document.getElementById("detail").classList.remove("show");
}

selectPlayer = function(name){
  selectedPlayer = name;
  const detail = document.getElementById("detail");
  const backBtn = `<button class="d-back" id="d-back"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"></path></svg>Grupo</button>`;
  const result = latestAndPast(name);
  if(!result){
    detail.innerHTML = backBtn + `<div class="empty">Sem dados pra ${esc(name)} ainda.</div>`;
  }else{
    const { latest, past } = result;
    const pct = Math.min(100, Math.max(0, Number(latest.percent)));
    const lg = levelGain(past, latest);
    const k = Number(latest.kills) - Number(past.kills);
    const x = Number(latest.battleEXP) - Number(past.battleEXP);
    const cls = CLASS_NAMES[Number(latest.classId)] || "";
    const lower = latest.name.toLowerCase();

    let rankTxt = "—", rankSub = "fora do top 30";
    if(rankPvpData && rankPvpData.geral){
      const i = rankPvpData.geral.findIndex(p => String(p.name).toLowerCase() === lower);
      if(i >= 0){ rankTxt = `#${i + 1}`; rankSub = `de ${fmtNum(rankPvpData.total_players || 0)} players`; }
    }
    const myDrops = allDropsCache.filter(d => (d.nick || "").toLowerCase() === lower);
    const myToday = todayDrops().filter(d => (d.nick || "").toLowerCase() === lower);
    const mySheltons = myToday.filter(d => categorizeItem(d.item) === "shelton").length;

    const kills = Number(latest.kills) || 0;
    const { current, next } = getPatente(kills);
    let patBar = `<div class="bar-head"><span>Patente máxima atingida</span></div>`;
    if(next){
      const prog = Math.min(100, Math.max(0, (kills - current.threshold) / (next.threshold - current.threshold) * 100));
      patBar = `<div class="bar"><div class="bar-fill" style="width:${prog}%"></div></div>
        <div class="bar-head" style="margin:8px 0 0;"><span>${fmtNum(kills)} / ${fmtNum(next.threshold)} kills</span><span>faltam ${fmtNum(next.threshold - kills)}</span></div>`;
    }

    const rows = allRows.filter(r => r.name.toLowerCase() === lower).sort((a, b) => a.ts - b.ts);
    const days = [];
    const wd = ["Dom","Seg","Ter","Qua","Qui","Sex","Sáb"];
    for(let i = 6; i >= 0; i--){
      const d = new Date(); d.setDate(d.getDate() - i);
      const { endTs } = getDayBoundsTs(localISODate(d));
      const snap = rows.length && rows[0].ts <= endTs ? findSnapshotAtOrBefore(rows, endTs) : null;
      days.push({ wd: wd[d.getDay()], day: d.getDate(), val: snap ? Number(snap.battleEXP) || 0 : 0 });
    }
    const max = Math.max(1, ...days.map(d => d.val));

    detail.innerHTML = `
      ${backBtn}
      <div class="d-hero">
        <div class="mono-badge big" aria-hidden="true">${esc(latest.name[0].toUpperCase())}</div>
        <div>
          <h2 class="d-name">${esc(latest.name)}</h2>
          <div class="pc-sub">${esc([cls, latest.clan].filter(Boolean).join(" · "))}</div>
          <div class="d-pills"><span class="pill gold">Lv ${esc(latest.level)}</span><span class="pill">${rankTxt === "—" ? "fora do top 30" : rankTxt + " no servidor"}</span></div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-head"><span class="sum-label">Progresso do nível</span><span class="pc-sub" style="color:var(--gold)">${lg > 0 ? "+" : ""}${lg.toFixed(2).replace(".", ",")}% em 24h</span></div>
        <div class="big-num" style="margin-bottom:10px;">${pct.toFixed(2).replace(".", ",")}%</div>
        <div class="bar lg"><div class="bar-fill" style="width:${pct}%"></div></div>
      </div>
      <div class="grid2">
        <div class="sum-tile"><div class="sum-label">Kills PvP</div><div class="sum-value" style="color:var(--kills)">${fmtNum(kills)}</div><div class="sum-sub">${signed(k, "")} em 24h</div></div>
        <div class="sum-tile"><div class="sum-label">Battle XP</div><div class="sum-value" style="color:var(--gold)">${fmtNum(latest.battleEXP)}</div><div class="sum-sub">${signed(x, "")} em 24h</div></div>
        <div class="sum-tile"><div class="sum-label">Drops hoje</div><div class="sum-value">${myToday.length}</div><div class="sum-sub">${mySheltons} shelton${mySheltons === 1 ? "" : "s"}</div></div>
        <div class="sum-tile"><div class="sum-label">Rank servidor</div><div class="sum-value">${rankTxt}</div><div class="sum-sub">${rankSub}</div></div>
      </div>
      <div class="panel">
        <div class="panel-head"><span class="sum-label">Patente</span></div>
        <div class="pat-row">
          <div class="pat-crest band-${current.band}" aria-hidden="true">${current.emoji}</div>
          <div><div class="pat-name">${current.name}</div>${next ? `<div class="pc-sub">Próxima: ${next.name}</div>` : ""}</div>
        </div>
        ${patBar}
      </div>
      <div class="panel">
        <div class="panel-head"><span class="sum-label">Battle XP · 7 dias</span></div>
        <div class="chart">${days.map((d, i) => `<div class="col ${i === 6 ? "now" : ""}" style="height:${Math.round(d.val / max * 100)}%" title="${fmtNum(d.val)}"></div>`).join("")}</div>
        <div class="chart-labels">${days.map(d => `<div>${d.wd}<br>${d.day}</div>`).join("")}</div>
      </div>
      <div class="sec-title" style="margin-top:18px;"><h2>Últimos drops</h2></div>
      ${myDrops.length ? myDrops.slice(0, 3).map(d => {
        const c = categorizeItem(d.item);
        return `<div class="mini-drop"><div class="md-info"><div class="md-item">${esc(d.item)}</div><div class="md-meta">${esc((d.horario || "").replace(" ás ", " · "))} · ${esc(d.monster)}</div></div><span class="tag ${c}">${DROP_TAG[c]}</span></div>`;
      }).join("") : `<div class="empty">Nenhum drop registrado.</div>`}
    `;
  }
  detail.classList.add("show");
  document.getElementById("d-back").addEventListener("click", () => { closePlayerDetail(); window.scrollTo(0, 0); });
};

renderDropsList = function(){
  const el = document.getElementById("drops-list");
  const cutoff = getDropsCutoffDate(dropsPeriod);
  let rows = allDropsCache.filter(d => d.date >= cutoff);
  if(dropsFilter !== "all") rows = rows.filter(d => d.nick.toLowerCase() === dropsFilter.toLowerCase());
  if(dropsCategory !== "all") rows = rows.filter(d => categorizeItem(d.item) === dropsCategory);

  if(rows.length === 0){
    const periodLabel = dropsPeriod === "today" ? "hoje" : "nos últimos 7 dias";
    el.innerHTML = `<div class="empty">Nenhum drop ${periodLabel}${dropsFilter === "all" ? "" : " de " + esc(dropsFilter)}${dropsCategory === "all" ? "" : " nessa categoria"}.</div>`;
  }else{
    let lastDate = null;
    el.innerHTML = rows.map(d => {
      const c = categorizeItem(d.item);
      const m = (d.horario || "").match(/(\d{2}\/\d{2}).*?(\d{2}:\d{2})$/);
      const dayHdr = dropsPeriod !== "today" && d.date !== lastDate ? `<div class="dr-day">${m ? m[1] : esc(d.date)}</div>` : "";
      lastDate = d.date;
      return `${dayHdr}<div class="drop-row">
        <div class="dr-time">${m ? m[2] : ""}</div>
        <div class="dr-rail" aria-hidden="true"><i></i><span class="dr-dot ${c}"></span><i></i></div>
        <div class="dr-card">
          <div class="dr-top"><span class="dr-item">${esc(d.item)}</span><span class="tag ${c}">${DROP_TAG[c]}</span></div>
          <div class="dr-meta">${esc(d.nick)} · ${esc(d.monster)} · ${esc(d.mapa)}</div>
        </div>
      </div>`;
    }).join("");
  }
  renderHomeSummary();
  if(detailOpen && selectedPlayer) selectPlayer(selectedPlayer);
};

const _origRenderRankPvp = renderRankPvp;
renderRankPvp = function(){
  _origRenderRankPvp();
  if(!rankPvpData) return;
  let rows, val;
  if(rankPvpSub === "geral"){ rows = rankPvpData.geral || []; val = r => `${fmtNum(r.battleEXP)} XP`; }
  else{
    if(rankPvpData.day !== localISODate(new Date())) return;
    rows = (rankPvpMetric === "kills" ? rankPvpData.dia_kills : rankPvpData.dia_xp) || [];
    val = r => rankPvpMetric === "kills" ? `+${r.killsDia} kills` : `+${fmtNum(r.xpDia)} XP`;
  }
  if(rows.length < 3) return;
  const el = document.getElementById("rankpvp-list");
  el.querySelectorAll(".rank-row").forEach((r, i) => { if(i < 3) r.remove(); });
  const spot = (r, pos) => `<div class="pod-spot p${pos}">
    <div class="mono-badge" aria-hidden="true">${esc(String(r.name)[0].toUpperCase())}</div>
    <div class="pod-name">${esc(r.name)}</div><div class="pod-clan">${esc(r.clan)}</div>
    <div class="pod-base"><div class="pod-pos">${pos}</div><div class="pod-val">${val(r)}</div></div>
  </div>`;
  el.insertAdjacentHTML("afterbegin", `<div class="pod">${spot(rows[1], 2)}${spot(rows[0], 1)}${spot(rows[2], 3)}</div>`);
  if(detailOpen && selectedPlayer) selectPlayer(selectedPlayer);
};

const _origRenderBosses = renderBosses;
renderBosses = function(){
  _origRenderBosses();
  const el = document.getElementById("boss-hero");
  const nb = nextBossInfo();
  if(!nb){ el.innerHTML = ""; return; }
  const on = document.getElementById("notif-btn").classList.contains("active");
  const hh = nb.first.next.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  el.innerHTML = `<div class="boss-hero">
    <div class="bh-top"><span class="sum-label">Próximo</span><span class="bh-badge">em ${formatCountdown(nb.first.next - nb.now)}</span></div>
    <div class="bh-main"><div><div class="bh-name">${esc(nb.names)}</div><div class="bh-meta">${esc(nb.first.local || formatWhen(nb.first.next, nb.now))}</div></div><div class="bh-time">${hh}</div></div>
    <button class="bh-notif" id="bh-notif">${on ? "Avisos de boss ligados" : "Ativar avisos de boss"}</button>
  </div>`;
  document.getElementById("bh-notif").addEventListener("click", () => document.getElementById("notif-btn").click());
};

const _origRenderBossFloat = renderBossFloat;
renderBossFloat = function(){
  _origRenderBossFloat();
  if(!detailOpen) renderHomeSummary();
};

