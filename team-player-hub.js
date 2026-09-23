(()=>{'use strict';
const slug=location.pathname.split('/').filter(Boolean).pop()||'';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const qs=s=>document.querySelector(s);
let sourceCfg=null,leagueData=null,allTeams=[];

async function jfetch(url){const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw new Error(String(r.status));return r.json()}
async function loadSources(){const j=await jfetch('/team-player-sources.json?v=20260923-1');return j?.leagues?.[slug]||null}
async function loadPublished(){
 try{const j=await jfetch('/team-player-data.json?v='+Date.now());return j?.leagues?.[slug]||null}catch{return null}
}
function espnBase(c){return c?.structured?('https://site.api.espn.com/apis/site/v2/sports/'+encodeURIComponent(c.structured.sport)+'/'+encodeURIComponent(c.structured.league)):''}
async function liveEspnTeams(c){
 const base=espnBase(c);if(!base)return[];
 try{
   const j=await jfetch(base+'/teams?limit=100');
   const rows=j?.sports?.[0]?.leagues?.[0]?.teams||[];
   const out=[];
   for(const row of rows){
     const t=row?.team||row||{},id=String(t.id||'');if(!id)continue;
     let roster=[];
     for(const ident of [id,t.slug].filter(Boolean)){
       try{
         const r=await jfetch(base+'/teams/'+encodeURIComponent(ident)+'/roster');
         const pools=[];
         for(const key of ['athletes','items','roster','players'])if(Array.isArray(r?.[key]))pools.push(...r[key]);
         const flat=[];
         for(const x of pools){
           if(Array.isArray(x?.items))flat.push(...x.items);
           else flat.push(x?.athlete||x);
         }
         roster=flat.filter(Boolean).map(a=>({
           id:String(a.id||''),name:a.displayName||a.fullName||a.name||'Player',
           shortName:a.shortName||'',number:a.jersey||a.number||'',
           position:a?.position?.abbreviation||a?.position?.displayName||a.position||'',
           age:a.age||'',height:a.displayHeight||a.height||'',weight:a.displayWeight||a.weight||'',
           headshot:a?.headshot?.href||a.headshot||'',
           profile:(a.links||[]).find(x=>x?.href)?.href||'',
           stats:a.statistics||a.stats||null
         }));
         if(roster.length)break;
       }catch{}
     }
     out.push({id,slug:t.slug||'',name:t.displayName||t.name||'Team',abbreviation:t.abbreviation||'',logo:t?.logos?.[0]?.href||t.logo||'',profile:(t.links||[]).find(x=>x?.href)?.href||'',roster});
   }
   return out;
 }catch{return[]}
}
async function regionalTeams(key){
 const files=['/regional-web.json','/special-sports-data.json','/extended-sports-data.json'],names=new Map();
 for(const file of files){
  try{
   const j=await jfetch(file+'?v='+Date.now()),l=j?.leagues?.[key]||{};
   for(const g of(l.games||[]))for(const n of[g.away,g.home])if(n)names.set(String(n).toLowerCase(),{id:String(n).toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,''),name:n,roster:[]});
  }catch{}
 }
 return [...names.values()];
}
function mergeTeams(a,b){
 const m=new Map();
 for(const t of [...(b||[]),...(a||[])]){
   const k=String(t.id||t.slug||t.name).toLowerCase();if(!k)continue;
   const old=m.get(k)||{};
   m.set(k,{...old,...t,roster:(t.roster&&t.roster.length)?t.roster:(old.roster||[])});
 }
 return [...m.values()];
}
function panel(){
 const left=qs('.img-dashboard > .img-stack');if(!left)return null;
 let p=qs('#imgRosterPanel');if(p)return p;
 p=document.createElement('section');p.id='imgRosterPanel';p.className='img-panel img-reveal';
 p.innerHTML='<div class="img-panel-head"><div><h2>Teams, rosters & player stats</h2><p>Auto-updated from official and verified league sources</p></div></div><div id="imgRosterBody"></div>';
 const news=qs('#imgNewsPanel');if(news&&news.parentElement===left)left.insertBefore(p,news);else left.append(p);
 setTimeout(()=>p.classList.add('in'),30);return p;
}
function teamButton(t,i){
 return '<button type="button" data-team-index="'+i+'">'+(t.logo?'<img src="'+esc(t.logo)+'" alt="" loading="lazy">':'')+'<strong>'+esc(t.name)+'</strong></button>';
}
function renderTeams(){
 panel();const host=qs('#imgRosterBody');if(!host)return;
 if(sourceCfg?.mode!=='teams'){renderParticipantSources(host);return}
 host.innerHTML='<div class="img-roster-tools"><input id="imgRosterSearch" class="img-roster-search" type="search" placeholder="Search teams or players" aria-label="Search teams or players"></div><div class="img-team-browser" id="imgTeamBrowser">'+allTeams.map(teamButton).join('')+'</div><div class="img-roster-shell" id="imgRosterShell" hidden></div>';
 const search=qs('#imgRosterSearch');
 const browser=qs('#imgTeamBrowser');
 browser?.addEventListener('click',e=>{const b=e.target.closest('[data-team-index]');if(b)openTeam(Number(b.dataset.teamIndex))});
 search?.addEventListener('input',()=>{
   const q=search.value.trim().toLowerCase();
   browser.innerHTML=allTeams.map((t,i)=>({t,i})).filter(({t})=>!q||String(t.name).toLowerCase().includes(q)||(t.roster||[]).some(p=>String(p.name).toLowerCase().includes(q))).map(({t,i})=>teamButton(t,i)).join('');
 });
}
function renderParticipantSources(host){
 const label=sourceCfg.mode==='drivers'?'Drivers':sourceCfg.mode==='fighters'?'Fighters':'Players';
 const links=[['players',label],['rankings','Rankings'],['stats','Statistics'],['youtube','YouTube'],['facebook','Facebook']].filter(([k])=>sourceCfg[k]);
 host.innerHTML='<div class="img-athlete-sources">'+links.map(([k,l])=>'<a href="'+esc(sourceCfg[k])+'" target="_blank" rel="noopener noreferrer"><small>'+esc(l)+'</small><strong>'+esc(leagueData?.name||slug)+'</strong></a>').join('')+'</div>';
}
function openTeam(i){
 const t=allTeams[i];if(!t)return;
 const shell=qs('#imgRosterShell'),browser=qs('#imgTeamBrowser');if(!shell)return;
 if(browser)browser.hidden=true;shell.hidden=false;
 const roster=t.roster||[];
 shell.innerHTML='<div class="img-roster-head"><div><h3>'+esc(t.name)+'</h3><span style="color:var(--muted);font-size:.68rem">'+roster.length+' players</span></div><button type="button" id="imgRosterBack">Back to teams</button></div>'+
 (roster.length?'<div class="img-roster-grid">'+roster.map((p,pi)=>'<button class="img-player-card" type="button" data-player-index="'+pi+'">'+(p.headshot?'<img src="'+esc(p.headshot)+'" alt="" loading="lazy">':'<span class="img-team-logo-fallback">'+esc((p.name||'?').slice(0,2).toUpperCase())+'</span>')+'<span><strong>'+esc(p.name)+'</strong><span>'+esc([p.number?('#'+p.number):'',p.position].filter(Boolean).join(' · ')||'Player profile')+'</span></span></button>').join('')+'</div>':
 '<div style="padding:4px 0 12px;color:var(--muted);font-size:.78rem;line-height:1.55">IMG is syncing this roster from the league and team sources. The team remains listed so the roster will populate automatically when the verified source becomes available.</div>'+
 '<div class="img-player-links">'+officialTeamLinks(t)+'</div>');
 qs('#imgRosterBack')?.addEventListener('click',()=>{shell.hidden=true;if(browser)browser.hidden=false});
 shell.querySelectorAll('[data-player-index]').forEach(b=>b.addEventListener('click',()=>openPlayer(t,roster[Number(b.dataset.playerIndex)])));
}
function officialTeamLinks(t){
 const ls=[];if(t.profile)ls.push('<a href="'+esc(t.profile)+'" target="_blank" rel="noopener noreferrer">Team profile</a>');
 if(sourceCfg?.teams)ls.push('<a href="'+esc(sourceCfg.teams)+'" target="_blank" rel="noopener noreferrer">Official teams</a>');
 if(sourceCfg?.facebook)ls.push('<a href="'+esc(sourceCfg.facebook)+'" target="_blank" rel="noopener noreferrer">Facebook</a>');
 if(sourceCfg?.youtube)ls.push('<a href="'+esc(sourceCfg.youtube)+'" target="_blank" rel="noopener noreferrer">YouTube</a>');
 return ls.join('');
}
function statPairs(stats){
 const out=[];
 if(!stats)return out;
 if(Array.isArray(stats)){
   for(const group of stats){
     if(Array.isArray(group?.stats))for(const s of group.stats.slice(0,8))out.push([s.displayName||s.name||'Stat',s.displayValue??s.value??'']);
     else if(group&&typeof group==='object'&&('value'in group||'displayValue'in group))out.push([group.displayName||group.name||'Stat',group.displayValue??group.value??'']);
   }
 }else if(typeof stats==='object'){
   for(const [k,v] of Object.entries(stats).slice(0,10))if(typeof v!=='object')out.push([k,v]);
 }
 return out.slice(0,9);
}
function ensureDialog(){
 let d=qs('#imgPlayerDialog');if(d)return d;
 d=document.createElement('dialog');d.id='imgPlayerDialog';d.className='img-player-dialog';d.innerHTML='<button type="button" class="img-dialog-close" aria-label="Close">×</button><div id="imgPlayerProfile"></div>';document.body.append(d);
 d.querySelector('.img-dialog-close').onclick=()=>d.close();d.addEventListener('click',e=>{if(e.target===d)d.close()});return d;
}
function openPlayer(team,p){
 const d=ensureDialog(),host=qs('#imgPlayerProfile'),stats=statPairs(p.stats);
 host.innerHTML='<div class="img-player-profile"><div class="img-player-top">'+(p.headshot?'<img src="'+esc(p.headshot)+'" alt="" loading="lazy">':'<div class="img-team-logo-fallback" style="width:110px;height:110px;border-radius:22px;font-size:1.5rem">'+esc((p.name||'?').slice(0,2).toUpperCase())+'</div>')+'<div><h2>'+esc(p.name)+'</h2><div style="color:var(--muted);font-size:.78rem;margin-top:5px">'+esc(team.name)+'</div><div class="img-player-meta">'+[['No.',p.number],['Pos',p.position],['Age',p.age],['Height',p.height],['Weight',p.weight]].filter(x=>x[1]).map(x=>'<span>'+esc(x[0])+' '+esc(x[1])+'</span>').join('')+'</div></div></div>'+
 (stats.length?'<div class="img-player-stats">'+stats.map(([k,v])=>'<div class="img-player-stat"><small>'+esc(k)+'</small><strong>'+esc(v)+'</strong></div>').join('')+'</div>':'')+
 '<div class="img-player-links">'+(p.profile?'<a href="'+esc(p.profile)+'" target="_blank" rel="noopener noreferrer">Player profile</a>':'')+(sourceCfg?.stats?'<a href="'+esc(sourceCfg.stats)+'" target="_blank" rel="noopener noreferrer">League stats</a>':'')+(sourceCfg?.players?'<a href="'+esc(sourceCfg.players)+'" target="_blank" rel="noopener noreferrer">Official players</a>':'')+'</div></div>';
 d.showModal();
}
async function start(){
 try{
  sourceCfg=await loadSources();if(!sourceCfg)return;
  leagueData=await loadPublished();
  let published=leagueData?.teams||[],live=[],regional=[];
  if(sourceCfg.mode==='teams'&&sourceCfg.structured)live=await liveEspnTeams(sourceCfg);
  if(sourceCfg.mode==='teams'&&sourceCfg.regionalKey)regional=await regionalTeams(sourceCfg.regionalKey);
  allTeams=mergeTeams(live,mergeTeams(published,regional));
  renderTeams()
 }catch{}
}
start();
})();