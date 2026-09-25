path = "docs/index.html"
s = open(path, encoding="utf-8").read()
start = 'document.getElementById("notif-btn").addEventListener("click", async () => {'
assert s.count(start) == 1
a = s.index(start)
b = s.index("const ACCESS_CONFIG", a)
new = r'''document.getElementById("notif-btn").addEventListener("click", async () => {
  if(!oneSignalReady){
    if(window.__oneSignalInitError){
      alert("Erro ao carregar notificações: " + window.__oneSignalInitError);
    }else{
      alert("As notificações ainda estão carregando — espera uns segundos e tenta de novo.");
    }
    return;
  }
  const withTimeout = (p, ms) => Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error("o OneSignal não respondeu")), ms))]);
  const perm = () => ("Notification" in window) ? Notification.permission : "indisponível";
  try{
    const sub = oneSignalReady.User.PushSubscription;
    if(sub.optedIn){
      if(!confirm("Os avisos de boss estão ligados. Quer desligar?")) return;
      await withTimeout(sub.optOut(), 10000);
      alert("Avisos de boss desligados.");
    }else{
      if(perm() === "denied"){
        alert("As notificações estão bloqueadas para este site.\n\nAbra o Chrome → ⋮ → Configurações → Configurações do site → Notificações, permita flynmael.github.io e tente de novo.");
        return;
      }
      await withTimeout(oneSignalReady.Notifications.requestPermission(), 20000);
      await withTimeout(sub.optIn(), 15000);
      await new Promise(r => setTimeout(r, 1500));
      const ok = oneSignalReady.User.PushSubscription.optedIn;
      const id = oneSignalReady.User.PushSubscription.id;
      alert(ok ? "Avisos de boss ativados ✅" : `Não consegui ativar.\nPermissão: ${perm()}\nInscrição: ${id || "nenhuma"}`);
    }
  }catch(err){
    console.error("Erro ao ativar notificações:", err);
    alert(`Erro ao ativar notificações: ${err && err.message ? err.message : err}\nPermissão: ${perm()}`);
  }finally{
    document.getElementById("notif-btn").classList.toggle("active", !!oneSignalReady.User.PushSubscription.optedIn);
    if(document.getElementById("bosses-view").style.display !== "none") renderBosses();
  }
});

'''
s = s[:a] + new + s[b:]
open(path, "w", encoding="utf-8").write(s)
print("ok")
