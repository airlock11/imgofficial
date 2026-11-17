/* IMG navigation: real inline SVG icons; no icon font or CSS mask dependency. */
(()=>{
  const shapes={
    Home:'<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z"/>',
    Sports:'<circle cx="12" cy="12" r="9"/><path d="M3.8 8.3c5.1.2 9.7 4.4 11.7 11.9M12 3a14 14 0 0 1-8.9 11M19.7 8c-4.7.1-8.6 3.1-10 7.5"/>',
    Scores:'<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M8 13h2m4 0h2M8 17h8"/>',
    News:'<rect x="5" y="3" width="15" height="18" rx="2"/><path d="M9 7h7M9 11h7M9 15h4M5 18H4a1 1 0 0 1-1-1V7"/>',
    Odds:'<path d="M4 20V11h4v9m4 0V5h4v15m4 0v-8h2v8M2 20h20"/>'
  };
  const svg=k=>'<svg class="img-nav-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'+shapes[k]+'</svg>';
  const style=document.createElement('style');
  style.textContent='.img-nav-svg{display:block!important;width:18px;height:18px;min-width:18px;flex:none;overflow:visible;fill:none!important;stroke:currentColor!important;stroke-width:1.8!important;stroke-linecap:round;stroke-linejoin:round;background:none!important;mask:none!important;-webkit-mask:none!important}.site-nav a,.navlinks a,.league-site-nav a{display:inline-flex;align-items:center;justify-content:center;gap:7px}.bottomnav a b .img-nav-svg,.league-bottomnav a b .img-nav-svg{width:20px!important;height:20px!important;min-width:20px!important}.bottomnav a.active .img-nav-svg,.league-bottomnav a.active .img-nav-svg{stroke-width:2.2!important}@media(max-width:760px){.site-nav .img-nav-svg,.navlinks .img-nav-svg,.league-site-nav .img-nav-svg{display:none!important}}';
  document.head.append(style);
  document.querySelectorAll('.bottomnav a,.league-bottomnav a,.site-nav a,.navlinks a,.league-site-nav a').forEach(a=>{
    const key=String(a.textContent||'').trim();
    if(!Object.prototype.hasOwnProperty.call(shapes,key))return;
    if(a.closest('.bottomnav,.league-bottomnav')){
      const host=a.querySelector('b');if(host)host.innerHTML=svg(key);
    }else if(!a.querySelector('.img-nav-svg'))a.insertAdjacentHTML('afterbegin',svg(key));
    if(a.classList.contains('active'))a.setAttribute('aria-current','page');
  });
})();
