
(function(){
  const modal=document.getElementById('img-coverage-modal');
  const list=document.getElementById('icm-list');
  const title=document.getElementById('icm-title');
  const sub=document.getElementById('icm-sub');
  if(!modal||!list||!title||!sub) return;

  function show(){ modal.classList.add('is-open'); modal.setAttribute('aria-hidden','false'); document.body.style.overflow='hidden'; }
  function hide(){ modal.classList.remove('is-open'); modal.setAttribute('aria-hidden','true'); document.body.style.overflow=''; }

  function leaguesFor(sport){
    const d=window.IMGLeagueData && window.IMGLeagueData[sport];
    return Array.isArray(d) ? d : [];
  }

  function openSportDirectory(sport){
    title.textContent=sport;
    sub.textContent='Leagues and competitions covered by IMG.';
    list.replaceChildren();
    const leagues=leaguesFor(sport);
    if(!leagues.length){
      const empty=document.createElement('div'); empty.className='icm-card';
      empty.innerHTML='<h3>No leagues available</h3><p class="icm-muted">IMG has not added a verified league entry for this sport yet.</p>';
      list.appendChild(empty); show(); return;
    }
    leagues.forEach(function(row){
      const name=row[0], location=row[1]||'';
      const item=document.createElement('div');
      item.className='icm-league';
      item.setAttribute('aria-label',name+' league');
      item.innerHTML='<strong>'+escapeHtml(name)+'</strong><small style="display:block;color:#8f98a5;margin-top:4px">'+escapeHtml(location)+'</small>';
      list.appendChild(item);
    });
    show();
  }

  function escapeHtml(v){
    return String(v).replace(/[&<>'"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','\"':'&quot;'}[c]});
  }

  window.IMG_Coverage_Click=openSportDirectory;

  // Capture-phase handler guarantees the Sports Coverage cards reach this directory
  // even if an older click handler exists elsewhere in the page.
  document.addEventListener('click',function(e){
    const card=e.target.closest && e.target.closest('[data-coverage-sport]');
    if(!card) return;
    const sport=card.getAttribute('data-coverage-sport');
    if(!sport) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    openSportDirectory(sport);
  },true);

  const close=modal.querySelector('.icm-close');
  const backdrop=modal.querySelector('.icm-backdrop');
  if(close) close.addEventListener('click',hide);
  if(backdrop) backdrop.addEventListener('click',hide);
  document.addEventListener('keydown',function(e){ if(e.key==='Escape' && modal.classList.contains('is-open')) hide(); });
})();
