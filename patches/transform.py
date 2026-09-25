import sys, os
here = os.path.dirname(os.path.abspath(__file__))
path = sys.argv[1] if len(sys.argv) > 1 else "docs/index.html"
s = open(path, encoding="utf-8").read()
css = open(os.path.join(here, "new.css"), encoding="utf-8").read()
js = open(os.path.join(here, "new.js"), encoding="utf-8").read()

def rep(a, b):
    global s
    n = s.count(a)
    if n != 1:
        raise SystemExit(f"trecho encontrado {n}x: {a[:70]!r}")
    s = s.replace(a, b)

NAV_ICONS = {
 "grupo": '<circle cx="9" cy="8" r="3.5"></circle><path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6"></path><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8"></path><path d="M18 14.3c2.2.7 3.5 2.8 3.5 5.7"></path>',
 "ranking": '<path d="M8 4h8v5a4 4 0 0 1-8 0z"></path><path d="M8 6H4.5v1.5A3.5 3.5 0 0 0 8 11"></path><path d="M16 6h3.5v1.5A3.5 3.5 0 0 1 16 11"></path><path d="M12 13v4"></path><path d="M9 20h6"></path>',
 "drops": '<path d="M6 4h12l3 5-9 11L3 9z"></path><path d="M3 9h18"></path><path d="M9 4l3 5 3-5"></path>',
 "boss": '<circle cx="12" cy="12" r="8.5"></circle><path d="M12 7.5V12l3 2"></path>',
}
LABELS = {"grupo": "Grupo", "ranking": "Ranking", "drops": "Drops", "boss": "Boss"}
btns = "".join(
    f'<button data-section="{k}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{v}</svg><span>{LABELS[k]}</span></button>'
    for k, v in NAV_ICONS.items())
nav = f'\n  <nav id="bottom-nav" aria-label="Navegação principal"><div class="nav-inner">{btns}</div></nav>\n'

rep("</style>", css + "</style>")
rep('<meta name="theme-color" content="#0E0B08" />', '<meta name="theme-color" content="#0F0C09" />')
rep('<div class="tab" data-tab="bosses">Boss</div>\n    </div>\n',
    '<div class="tab" data-tab="bosses">Boss</div>\n    </div>\n\n'
    '    <div id="subnav" style="display:none;">\n'
    '      <div class="seg" id="seg-scope"><button data-scope="grupo">Grupo</button><button data-scope="servidor">Servidor</button></div>\n'
    '      <div class="seg seg-sm" id="seg-group"><button data-gtab="ranking">Nível</button><button data-gtab="pvp">PvP</button><button data-gtab="daily">Diário</button><button data-gtab="patentes">Patentes</button></div>\n'
    '    </div>\n')
rep('<section id="players-view">\n', '<section id="players-view">\n      <div id="home-summary"></div>\n')
rep('<section id="bosses-view" style="display:none;">\n', '<section id="bosses-view" style="display:none;">\n      <div id="boss-hero"></div>\n')
rep("  </footer>\n", "  </footer>\n" + nav)
rep('    if(target === "rankpvp") renderRankPvp();\n', '    if(target === "rankpvp") renderRankPvp();\n    syncNavFromTab(target);\n')
rep('  document.getElementById("app-footer").style.display = "flex";\n',
    '  document.getElementById("app-footer").style.display = "flex";\n  document.getElementById("bottom-nav").style.display = "flex";\n  renderNav();\n')
rep('  document.getElementById("app-footer").style.display = "none";\n',
    '  document.getElementById("app-footer").style.display = "none";\n  document.getElementById("bottom-nav").style.display = "none";\n')
rep("// Se já desbloqueou antes nesse aparelho", js + "// Se já desbloqueou antes nesse aparelho")

open(path, "w", encoding="utf-8").write(s)
print("index.html transformado")
