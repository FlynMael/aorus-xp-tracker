path = "docs/index.html"
s = open(path, encoding="utf-8").read()
old = 'players: ["Katinga", "DarkFury", "Stelar", "SrVittar", "Curse", "LekJhonson95"],'
new = 'players: ["Katinga", "DarkFury", "LeilaPereira", "SrVittar", "Curse", "LekJhonson95"],'
assert s.count(old) == 1
s = s.replace(old, new)
open(path, "w", encoding="utf-8").write(s)
print("ok")
