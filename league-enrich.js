(()=>{'use strict';
const slug=location.pathname.split('/').filter(Boolean).pop()||'';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function loadRegistry(){const r=await fetch('/league-sources.json?v=20260923-1',{cache:'no-store'});if(!r.ok)throw 0;return r.json()}
function labelFor(k){return({official:'Official site',schedule:'Schedule / results',standings:'Standings',rankings:'Rankings',stats:'Stats',teams:'Teams',players:'Players',athletes:'Athletes',news:'News',highlights:'Highlights',secondary:'Data feed'})[k]||k}
function insertHub(src){
 const aside=document.querySelector('.img-dashboard > aside.img-stack');
 if(!aside)return;
 const panel=document.createElement('section');
 panel.className='img-panel img-reveal';panel.id='imgInfoHub';
 const keys=['official','schedule','standings','rankings','stats','teams','players','athletes','news','highlights'];
 const items=keys.filter(k=>src[k]).map(k=>'<a class="img-source-card" href="'+esc(src[k])+'" target="_blank" rel="noopener noreferrer"><small>'+esc(labelFor(k))+'</small><strong>'+esc(src.name||'League')+'</strong></a>').join('');
 const coverage=keys.filter(k=>src[k]).map(k=>'<span>'+esc(labelFor(k))+'</span>').join('');
 panel.innerHTML='<div class="img-panel-head"><div><h2>League information hub</h2><p>Official and verified sources IMG monitors for this league</p></div></div><div class="img-infohub"><div class="img-source-grid">'+items+'</div></div><div class="img-coverage">'+coverage+'</div>';
 aside.append(panel);
}
async function insertTeams(src){
 const left=document.querySelector('.img-dashboard > .img-stack');if(!left||!src.secondary)return;
 if(!/site\.api\.espn\.com\/apis\/site\/v2\/sports\//.test(src.secondary))return;
 const u=src.secondary.replace(/\/scoreboard(?:\?.*)?$/,'/teams?limit=100');
 try{
   const r=await fetch(u,{cache:'no-store'});if(!r.ok)return;
   const j=await r.json();
   const rows=j?.sports?.[0]?.leagues?.[0]?.teams||[];
   const teams=rows.map(x=>x?.team||x).filter(Boolean).filter(t=>t.displayName||t.name).slice(0,40);
   if(!teams.length)return;
   const p=document.createElement('section');p.className='img-panel img-reveal';p.id='imgTeamsPanel';
   p.innerHTML='<div class="img-panel-head"><div><h2>Teams & participants</h2><p>Current league directory</p></div></div><div class="img-teams-grid">'+teams.map(t=>{const logo=t?.logos?.[0]?.href||t.logo||'';return'<div class="img-team-tile">'+(logo?'<img src="'+esc(logo)+'" alt="" loading="lazy">':'')+'<span>'+esc(t.displayName||t.name)+'</span></div>'}).join('')+'</div>';
   const standings=document.getElementById('imgStandingsPanel');
   if(standings)standings.insertAdjacentElement('afterend',p);else left.append(p);
 }catch{}
}
(async()=>{try{const reg=await loadRegistry(),src=reg?.leagues?.[slug];if(!src)return;insertHub(src);insertTeams(src);setTimeout(()=>document.querySelectorAll('.img-reveal').forEach(x=>x.classList.add('in')),80)}catch{}})();
})();