path = "docs/index.html"
s = open(path, encoding="utf-8").read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)
rep('${on ? "Avisos de boss ligados" : "Ativar avisos de boss"}', '${on ? "Avisos ligados · toque para desligar" : "Ativar avisos de boss"}')
rep('document.getElementById("bh-notif").addEventListener("click", () => document.getElementById("notif-btn").click());',
    'document.getElementById("bh-notif").addEventListener("click", () => { document.getElementById("notif-btn").click(); setTimeout(renderBosses, 2500); });')
open(path, "w", encoding="utf-8").write(s)
print("ok")
