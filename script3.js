
/* IMG homepage league search: tapping a suggestion opens the league detail popup */
(function(){
  function initSearch(){
    const input=document.getElementById('home-league-search');
    const drop=document.getElementById('home-search-dropdown');
    if(!input||!drop||input.dataset.imgSearchReady==='1') return;
    input.dataset.imgSearchReady='1';

    function matches(q){
      const source=window.IMGLeagueData||{};
      const out=[];
      Object.keys(source).forEach(sp=>{
        (source[sp]||[]).forEach(x=>{
          if(x && x[0] && (x[0]+' '+(x[1]||'')).toLowerCase().includes(q)) out.push([x[0],x[1]||'',sp]);
        });
      });
      return out.slice(0,10);
    }

    function renderSearch(){
      const q=input.value.trim().toLowerCase();
      if(!q){drop.innerHTML='';drop.classList.remove('show');return;}
      const rows=matches(q);
      drop.innerHTML=rows.length ? rows.map(x=>
        '<button type="button" class="home-search-item" data-league="'+x[0].replace(/&/g,'&amp;').replace(/"/g,'&quot;')+'" data-sport="'+x[2].replace(/&/g,'&amp;').replace(/"/g,'&quot;')+'"><b>'+x[0]+'</b><small>'+x[1]+' · '+x[2]+'</small></button>'
      ).join('') : '<div class="home-search-empty">No leagues found.</div>';
      drop.classList.add('show');
    }

    input.addEventListener('input',renderSearch);
    input.addEventListener('focus',function(){if(input.value.trim()) renderSearch();});

    function openSuggestion(item){
      if(!item) return;
      const name=item.getAttribute('data-league');
      const sport=item.getAttribute('data-sport');
      input.value=name;
      drop.innerHTML='';
      drop.classList.remove('show');
      window.homeSearchOpenedLeague=true;
      window.IMGLeagueSearchOrigin=true;
      if(typeof window.IMGOpenLeagueDetail==='function') window.IMGOpenLeagueDetail(name,sport);
    }

    drop.addEventListener('click',function(e){
      const item=e.target.closest('.home-search-item');
      if(!item) return;
      e.preventDefault();
      e.stopPropagation();
      openSuggestion(item);
    });

    input.addEventListener('keydown',function(e){
      if(e.key==='Escape'){drop.innerHTML='';drop.classList.remove('show');return;}
      if(e.key==='Enter'){
        const first=drop.querySelector('.home-search-item');
        if(first){e.preventDefault();openSuggestion(first);}
      }
    });
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',initSearch); else initSearch();
})();
