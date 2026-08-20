// Service worker "no-op": nao guarda nada em cache, so existe pra permitir
// instalar o app na tela inicial. Assim toda atualizacao aparece na hora,
// sem precisar desinstalar/reinstalar.

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Sem handler de "fetch" -> o navegador busca tudo direto da rede, sempre.
