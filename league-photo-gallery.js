(()=>{'use strict';
const slug=location.pathname.split('/').filter(Boolean).pop()||'';
const body=document.body;
const league=body.dataset.leagueName||slug;
const key=body.dataset.leagueKey||'';
const pattern=body.dataset.newsPattern||league;
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const sportMap={
 nba:'basketball',wnba:'basketball',pba:'basketball',mpbl:'basketball','nbl-pilipinas':'basketball','nbl-australia':'basketball',vba:'basketball','b-league':'basketball',euroleague:'basketball',uaap:'basketball','ncaa-philippines':'basketball',
 'premier-league':'football','la-liga':'football','serie-a':'football',bundesliga:'football','champions-league':'football',mls:'football',
 atp:'tennis',wta:'tennis',ipl:'cricket',mlb:'baseball',nhl:'hockey',nfl:'american football','formula-1':'motorsport',ufc:'combat'
};
const fallbacks={basketball:'/basketball.jpg',football:'/football.jpg',tennis:'/tennis.jpg',cricket:'/cricket.jpg',baseball:'/baseball.jpg',hockey:'/hockey.jpg','american football':'/american.jpg',motorsport:'/motorsports.jpg',combat:'/combat.jpg'};
const formatDate=v=>{const d=new Date(v);return Number.isNaN(d.getTime())?'':new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric',year:'numeric'}).format(d)};
async function waitPanel(){
 for(let i=0;i<40;i++){const p=document.getElementById('imgHistoryPanel');if(p)return p;await new Promise(r=>setTimeout(r,150))}
 return null
}
function unique(items){
 const seen=new Set();
 return items.filter(x=>{const k=x.image||x.thumbnail||x.link||x.title;if(!k||seen.has(k))return false;seen.add(k);return true})
}
async function load(){
 const panel=await waitPanel();if(!panel)return;
 const head=panel.querySelector('.img-panel-head div');
 if(head)head.innerHTML='<h2>Previous Games Gallery</h2><p>Photos and visual coverage from recent '+esc(league)+' games and league activity.</p>';
 let items=[];
 try{
  const r=await fetch('/news-data.json?v='+Date.now(),{cache:'no-store'});
  if(r.ok){
   const j=await r.json(),all=[...(j.items||[]),...(j.videos||[])].filter(x=>x.image||x.thumbnail);
   let rx;try{rx=new RegExp(pattern,'i')}catch{rx=new RegExp(league,'i')}
   items=all.filter(x=>rx.test((x.title||'')+' '+(x.description||'')+' '+(x.sport||'')));
   const sport=sportMap[slug]||'';
   if(items.length<6&&sport){
    const sx=new RegExp(sport==='football'?'football|soccer':sport,'i');
    items.push(...all.filter(x=>sx.test((x.title||'')+' '+(x.description||'')+' '+(x.sport||''))));
   }
   if(items.length<6)items.push(...all);
   items=unique(items).slice(0,10);
  }
 }catch{}
 if(!items.length){
  const sport=sportMap[slug]||'basketball',img=fallbacks[sport]||'/hero-sports-bg.png';
  items=[{title:league+' game coverage',image:img,link:'/scores/?league='+encodeURIComponent(key),published:''}];
 }
 let rail=panel.querySelector('.img-photo-gallery-rail');
 if(!rail){rail=document.createElement('div');rail.className='img-photo-gallery-rail';panel.append(rail)}
 rail.innerHTML=items.map(x=>{
  const sport=sportMap[slug]||'basketball';
  const img=x.image||x.thumbnail||fallbacks[sport]||'/hero-sports-bg.png';
  const href=x.link||x.watchUrl||('/scores/?league='+encodeURIComponent(key));
  return '<a class="img-photo-gallery-card" href="'+esc(href)+'" '+(/^https?:/i.test(href)?'target="_blank" rel="noopener noreferrer"':'')+'><img src="'+esc(img)+'" alt="" loading="lazy" referrerpolicy="no-referrer"><div class="img-photo-gallery-copy"><strong>'+esc(x.title||league+' game coverage')+'</strong><span>'+esc(formatDate(x.published||x.date))+(x.source?' · '+esc(x.source):'')+'</span></div></a>'
 }).join('');
 panel.hidden=false;
}
load();
setInterval(()=>{if(!document.hidden)load()},300000);
})();