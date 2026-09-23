(()=>{'use strict';
const body=document.body;
const key=body.dataset.leagueKey||'';
const league=body.dataset.leagueName||'League';
const scoreUrl=body.dataset.scoreUrl||'';
const standingsUrl=body.dataset.standingsUrl||'';
const newsPattern=body.dataset.newsPattern||league;
const refreshMs=Math.max(30000,Number(body.dataset.refreshMs)||60000);
const worker='https://img-api-proxy.magsipocarnie.workers.dev';

const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dateKey=d=>{const x=new Date(d),y=x.getUTCFullYear(),m=String(x.getUTCMonth()+1).padStart(2,'0'),day=String(x.getUTCDate()).padStart(2,'0');return ''+y+m+day};
const fmtTime=v=>{const d=new Date(v);if(Number.isNaN(d.getTime()))return'';return new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}).format(d)};
const stateOf=e=>{
  const t=e?.status?.type||{};
  const s=String(t.state||t.name||t.description||'').toLowerCase();
  if(/in|live|progress/.test(s)&&!/final|post|complete/.test(s))return'live';
  if(/post|final|complete|ended/.test(s))return'final';
  return'scheduled';
};
const competitors=e=>{
  const c=e?.competitions?.[0]?.competitors||[];
  const home=c.find(x=>x.homeAway==='home')||c[0]||{};
  const away=c.find(x=>x.homeAway==='away')||c[1]||{};
  const map=x=>({name:x?.team?.displayName||x?.team?.shortDisplayName||x?.team?.name||'Team',logo:x?.team?.logo||x?.team?.logos?.[0]?.href||'',score:x?.score??''});
  return {home:map(home),away:map(away)};
};
function gameMarkup(e){
  const st=stateOf(e),t=competitors(e),detail=e?.status?.type?.shortDetail||e?.status?.type?.description||'';
  const date=e?.date||e?.competitions?.[0]?.date||'';
  const showScore=st!=='scheduled'&&(String(t.home.score)!==''||String(t.away.score)!=='');
  return '<div class="game-row"><div><div class="game-meta">'+
    (st==='live'?'<span class="live-chip">LIVE</span>':'')+
    '<span>'+esc(detail||fmtTime(date))+'</span></div><div class="game-teams">'+
    '<div class="game-team">'+(t.away.logo?'<img src="'+esc(t.away.logo)+'" alt="" loading="lazy">':'')+'<span>'+esc(t.away.name)+'</span></div>'+
    '<div class="game-team">'+(t.home.logo?'<img src="'+esc(t.home.logo)+'" alt="" loading="lazy">':'')+'<span>'+esc(t.home.name)+'</span></div>'+
    '</div></div><div class="game-score">'+(showScore?esc(t.away.score)+'<br>'+esc(t.home.score):esc(fmtTime(date)))+'</div></div>';
}
function renderList(id,items,empty){
 const el=document.getElementById(id);if(!el)return;
 el.innerHTML=items.length?'<div class="game-list">'+items.map(gameMarkup).join('')+'</div>':'<p class="data-empty">'+empty+'</p>';
}
async function fetchScoreboard(){
 if(key==='pba'){
   const r=await fetch(worker+'/regional-scores?league=pba',{cache:'no-store'});
   if(!r.ok)throw new Error('PBA feed unavailable');
   return r.json();
 }
 if(!scoreUrl)return {events:[]};
 const now=new Date(),a=new Date(now.getTime()-7*86400000),b=new Date(now.getTime()+21*86400000);
 const sep=scoreUrl.includes('?')?'&':'?';
 const url=scoreUrl+sep+'dates='+dateKey(a)+'-'+dateKey(b);
 try{
   const r=await fetch(url,{cache:'no-store'});
   if(r.ok)return r.json();
 }catch{}
 const r=await fetch(worker+'/scoreboard?league='+encodeURIComponent(key)+'&dates='+encodeURIComponent(dateKey(a)+'-'+dateKey(b)),{cache:'no-store'});
 if(!r.ok)throw new Error('Score feed unavailable');
 return r.json();
}
async function renderScores(){
 const status=document.getElementById('leagueDataStatus');
 try{
   const j=await fetchScoreboard();
   const events=Array.isArray(j?.events)?j.events:[];
   const now=Date.now();
   const live=events.filter(e=>stateOf(e)==='live');
   const upcoming=events.filter(e=>stateOf(e)==='scheduled'&&new Date(e.date||0).getTime()>=now).sort((a,b)=>new Date(a.date)-new Date(b.date)).slice(0,6);
   const recent=events.filter(e=>stateOf(e)==='final').sort((a,b)=>new Date(b.date)-new Date(a.date)).slice(0,6);
   renderList('leagueLive',live,'No verified '+esc(league)+' game is live right now.');
   renderList('leagueUpcoming',upcoming,key==='pba'?'No verified upcoming PBA games are available from the current live feed. <a href="/scores/?from=league&league=pba">Open PBA Scores</a> for the latest available data.':'No upcoming games are available in the current schedule window.');
   renderList('leagueRecent',recent,key==='pba'?'Recent PBA results are not supplied by the current live-only feed. <a href="/scores/?from=league&league=pba">Open PBA Scores</a>.':'No recent final results are available in the current window.');
   if(status)status.textContent='Updated '+new Intl.DateTimeFormat(undefined,{hour:'numeric',minute:'2-digit'}).format(new Date());
 }catch{
   renderList('leagueLive',[],'Live data is temporarily unavailable. <a href="/scores/?from=league&league='+encodeURIComponent(key)+'">Open IMG Scores</a>.');
   renderList('leagueUpcoming',[],'Schedule data is temporarily unavailable.');
   renderList('leagueRecent',[],'Recent results are temporarily unavailable.');
   if(status)status.textContent='Data temporarily unavailable';
 }
}
function statValue(entry,names){
 const stats=Array.isArray(entry?.stats)?entry.stats:[];
 for(const n of names){
   const hit=stats.find(x=>String(x.name||x.type||'').toLowerCase()===n.toLowerCase());
   if(hit)return hit.displayValue??hit.value??'';
 }
 return'';
}
function standingsEntries(j){
 const groups=[];
 if(Array.isArray(j?.children))groups.push(...j.children);
 if(j?.standings)groups.push({standings:j.standings});
 const out=[];
 for(const g of groups){
   const entries=g?.standings?.entries||g?.entries||[];
   for(const e of entries)out.push(e);
 }
 return out;
}
async function renderStandings(){
 const host=document.getElementById('leagueStandings');if(!host)return;
 if(!standingsUrl){host.innerHTML='<p class="data-empty">Verified standings are not available from IMG’s current '+esc(league)+' feed.</p>';return}
 try{
   const r=await fetch(standingsUrl,{cache:'no-store'});if(!r.ok)throw 0;
   const j=await r.json(),entries=standingsEntries(j).slice(0,30);
   if(!entries.length)throw 0;
   host.innerHTML='<div class="standings-wrap"><table class="standings-table"><thead><tr><th>Team</th><th>W</th><th>L</th><th>PCT</th><th>GB</th></tr></thead><tbody>'+
     entries.map(e=>{const team=e?.team||{};return '<tr><td>'+esc(team.displayName||team.name||'Team')+'</td><td>'+esc(statValue(e,['wins']))+'</td><td>'+esc(statValue(e,['losses']))+'</td><td>'+esc(statValue(e,['winPercent','winpercent']))+'</td><td>'+esc(statValue(e,['gamesBehind','gamesbehind']))+'</td></tr>'}).join('')+
     '</tbody></table></div>';
 }catch{host.innerHTML='<p class="data-empty">Standings are temporarily unavailable. IMG will display them when the verified feed responds.</p>'}
}
async function renderNews(){
 const host=document.getElementById('leagueNews');if(!host)return;
 try{
   const r=await fetch('/news-data.json?v='+Date.now(),{cache:'no-store'});if(!r.ok)throw 0;
   const j=await r.json();const rx=new RegExp(newsPattern,'i');
   const items=(Array.isArray(j?.items)?j.items:[]).filter(x=>rx.test((x.title||'')+' '+(x.description||''))).slice(0,4);
   if(!items.length)throw 0;
   host.innerHTML='<div class="news-list">'+items.map(x=>'<a class="news-item" href="'+esc(x.link)+'" target="_blank" rel="noopener noreferrer">'+
    (x.image?'<img src="'+esc(x.image)+'" alt="" loading="lazy" referrerpolicy="no-referrer">':'<span></span>')+
    '<span><strong>'+esc(x.title)+'</strong><small>'+esc(x.source||'Sports news')+' · '+esc(fmtTime(x.published))+'</small></span></a>').join('')+'</div>';
 }catch{host.innerHTML='<p class="data-empty">No matching '+esc(league)+' article is in the current IMG news feed. <a href="/news/">Browse all sports news</a>.</p>'}
}
async function refresh(){await Promise.allSettled([renderScores(),renderStandings(),renderNews()])}
refresh();
setInterval(()=>{if(!document.hidden)renderScores()},refreshMs);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)renderScores()});
})();