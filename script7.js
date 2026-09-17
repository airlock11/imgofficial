
(function(){
  const IMG_AUTO_WORKER="https://img-api-proxy.magsipocarnie.workers.dev";
  const supported={PBA:1,NBA:1,WNBA:1,UAAP:1};
  function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));}
  function cardByTitle(title){
    return Array.from(document.querySelectorAll("#ld-content .ld-card")).find(c=>{
      const h=c.querySelector("h2,h3");
      return h && h.textContent.trim().toUpperCase()===title;
    });
  }
  function renderRows(items,empty){
    if(!items||!items.length) return '<div class="ld-placeholder">'+esc(empty)+'</div>';
    return '<div class="img-live-list">'+items.slice(0,12).map(x=>{
      if(x.text) return '<div class="img-live-row">'+esc(x.text)+'</div>';
      const score=(x.home_score!=null&&x.away_score!=null)?' · '+esc(x.away_score)+'–'+esc(x.home_score):'';
      return '<div class="img-live-row"><b>'+esc(x.away||"")+'</b> @ <b>'+esc(x.home||"")+'</b><small>'+esc(x.date||"")+' · '+esc(x.status||"")+score+'</small></div>';
    }).join("")+'</div>';
  }
  async function load(name){
    if(!supported[name]) return;
    try{
      const res=await fetch(IMG_AUTO_WORKER+"/league-data?league="+encodeURIComponent(name),{cache:"no-store"});
      const data=await res.json();
      if(!data || data.status!=="ok") return;
      const s=cardByTitle("SCHEDULE"), r=cardByTitle("RESULTS"), st=cardByTitle("STANDINGS");
      if(s) s.innerHTML='<div class="ld-card-head"><h3>SCHEDULE</h3><span class="ld-badge">Auto</span></div>'+renderRows(data.schedule,"No verified upcoming schedule available.");
      if(r) r.innerHTML='<div class="ld-card-head"><h3>RESULTS</h3><span class="ld-badge">Auto</span></div>'+renderRows(data.results,"No verified recent results available.");
      if(st && data.standings && data.standings.length) st.innerHTML='<div class="ld-card-head"><h3>STANDINGS</h3><span class="ld-badge">Auto</span></div>'+renderRows(data.standings,"No verified standings available.");
      const note=document.createElement("div");
      note.className="img-auto-note";
      note.textContent="Automatically refreshed from public league sources · "+new Date(data.updated_at||Date.now()).toLocaleString();
      const c=document.getElementById("ld-content");
      if(c) c.appendChild(note);
    }catch(e){ console.warn("IMG automatic league data unavailable",name,e); }
  }
  const originalOpen=window.IMGOpenLeagueDetail;
  if(originalOpen){
    window.IMGOpenLeagueDetail=function(name,sport){
      originalOpen(name,sport);
      setTimeout(function(){load(name);},250);
    };
  }
})();
