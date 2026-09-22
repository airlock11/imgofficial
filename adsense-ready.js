(()=>{
  const cfg=window.IMG_ADSENSE_CONFIG||{};
  const id=String(cfg.publisherId||"").trim();
  if(!cfg.enabled||!/^ca-pub-\d+$/.test(id)) return;
  if(document.querySelector('script[data-img-adsense],script[src*="pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"]')) return;

  const script=document.createElement('script');
  script.async=true;
  script.crossOrigin='anonymous';
  script.dataset.imgAdsense='true';
  script.src='https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client='+encodeURIComponent(id);
  script.onerror=()=>{ document.documentElement.dataset.adsense='unavailable'; };
  script.onload=()=>{ document.documentElement.dataset.adsense='ready'; };
  document.head.appendChild(script);
})();
