(() => {
  const LIVE_ORIGIN = 'https://www.imgofficial.com';
  const originalFetch = window.fetch.bind(window);

  window.fetch = (input, init) => {
    try {
      const raw = typeof input === 'string' ? input : input?.url;
      if (raw) {
        const url = new URL(raw, window.location.href);
        const localOrigin = window.location.origin;
        const isLocalJson = url.origin === localOrigin && /\.json$/i.test(url.pathname);
        if (isLocalJson) {
          const liveUrl = new URL(url.pathname + url.search, LIVE_ORIGIN);
          if (typeof input === 'string') {
            return originalFetch(liveUrl.toString(), init);
          }
          return originalFetch(new Request(liveUrl.toString(), input), init);
        }
      }
    } catch {}
    return originalFetch(input, init);
  };
})();
