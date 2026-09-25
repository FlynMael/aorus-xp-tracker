path = "docs/index.html"
s = open(path, encoding="utf-8").read()
old = "  .bh-time{ font-family:'IBM Plex Mono', monospace; font-weight:600; font-size:32px; color:var(--gold); }\n"
new = ("  .bh-time{ flex-shrink:0; font-family:'IBM Plex Mono', monospace; font-weight:600; font-size:28px; color:var(--gold); }\n"
       "  .bh-main > div:first-child{ flex:1; min-width:0; }\n"
       "  .bh-name{ overflow-wrap:anywhere; }\n")
assert s.count(old) == 1
s = s.replace(old, new)
open(path, "w", encoding="utf-8").write(s)
print("ok")
