(()=>{
const qs=s=>document.querySelector(s);
const qsa=s=>[...document.querySelectorAll(s)];
const safe=v=>String(v??"");
const fmtDate=v=>{try{return new Date(v).toLocaleDateString(undefined,{month:"short",day:"numeric",year:"numeric"})}catch{return v||""}};
const UAAP_LIVE_URL="https://img-api-proxy.magsipocarnie.workers.dev/regional-scores?league=uaap";
let gameController=null,livePollTimer=null;

async function getJSON(url,fallback={}){
  try{const r=await fetch(url+"?ts="+Date.now(),{cache:"no-store"});if(!r.ok)throw new Error(r.status);return await r.json()}catch{return fallback}
}
function initials(name){return safe(name).split(/\s+/).filter(Boolean).map(x=>x[0]).join("").slice(0,3).toUpperCase()}
function teamVisual(name){
  return '<div class="team-initial" aria-hidden="true">'+safe(initials(name))+'</div>';
}
function teamBlock(name,side,score=""){
  const hasScore=score!==null&&score!==undefined&&String(score)!=="";
  const scoreHtml=hasScore?'<div class="team-score" data-score-side="'+side+'">'+safe(score)+'</div>':"";
  const nameHtml='<div class="team-name">'+safe(name)+'</div>';
  return '<div class="game-team '+(side==="right"?"right":"")+'">'+
    (side!=="right"?teamVisual(name):"")+
    '<div class="team-copy"><div class="team-main">'+
    (side==="right"?scoreHtml:"")+nameHtml+(side!=="right"?scoreHtml:"")+
    '</div><div class="team-side">'+(side==="right"?"Home":"Away")+'</div></div>'+
    (side==="right"?teamVisual(name):"")+'</div>';
}
function eventId(g){return safe(g?.eventId||g?.id||[g?.away,g?.home,g?.date].filter(Boolean).join("|"))}

function renderGames({live,upcoming,finals}){
  const groups={live:[...live],upcoming:[...upcoming],results:[...finals]};
  const slot=qs("#game-slot");
  let active=live.length?"live":upcoming.length?"upcoming":"results",shown="";
  const patch=g=>{
    const card=slot?.querySelector(".featured-game");
    if(!card||card.dataset.eventId!==eventId(g))return false;
    const a=slot.querySelector('[data-score-side="left"]'),h=slot.querySelector('[data-score-side="right"]');
    if(a)a.textContent=safe(g.awayScore);if(h)h.textContent=safe(g.homeScore);
    const st=slot.querySelector(".game-status");if(st)st.textContent="LIVE";
    return true;
  };
  const paint=(key,force=false)=>{
    active=key;const g=(groups[key]||[])[0];
    qsa(".tab-btn").forEach(b=>b.classList.toggle("active",b.dataset.tab===key));
    if(!g){shown="";slot.innerHTML='<div class="empty-card">No verified UAAP game is available for this tab.</div>';return}
    const final=g.state==="final",isLive=g.state==="in"||/live/i.test(g.status||"");
    if(!force&&key==="live"&&isLive&&shown===eventId(g)&&patch(g))return;
    const showScore=final||isLive;
    const center=final?"FINAL":isLive?"LIVE":safe(g.displayTime||fmtDate(g.date));
    shown=eventId(g);
    slot.innerHTML='<article class="featured-game" data-event-id="'+shown+'">'+
      teamBlock(g.away||"Away","left",showScore?g.awayScore:"")+
      '<div class="game-center"><div class="game-status">'+center+'</div></div>'+
      teamBlock(g.home||"Home","right",showScore?g.homeScore:"")+
      '</article>';
  };
  qsa(".tab-btn").forEach(b=>b.addEventListener("click",()=>paint(b.dataset.tab,true)));
  paint(active,true);
  gameController={updateLive(next){const had=groups.live.length>0;groups.live=Array.isArray(next)?next:[];const has=groups.live.length>0;if(has&&active==="live")paint("live");else if(has&&!had)paint("live",true);else if(!has&&had&&active==="live")paint(groups.upcoming.length?"upcoming":"results",true)}};
}

function normalizeLive(event){
  const competitors=event?.competitions?.[0]?.competitors||[];
  const home=competitors.find(x=>x?.homeAway==="home")||{},away=competitors.find(x=>x?.homeAway==="away")||{};
  if(event?.status?.type?.state&&event.status.type.state!=="in")return null;
  return {eventId:safe(event?.id),date:event?.date||new Date().toISOString(),displayTime:"LIVE",away:away?.team?.displayName||"Away",home:home?.team?.displayName||"Home",awayScore:safe(away?.score??"0"),homeScore:safe(home?.score??"0"),status:event?.status?.type?.shortDetail||"Live",state:"in"};
}
async function fetchLive(){
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),8000);
  try{const r=await fetch(UAAP_LIVE_URL+"&ts="+Date.now(),{cache:"no-store",signal:controller.signal});if(!r.ok)throw new Error(r.status);const d=await r.json();if(!Array.isArray(d?.events))throw new Error("Invalid");return d.events.map(normalizeLive).filter(Boolean)}catch{return null}finally{clearTimeout(timeout)}
}
async function pollLive(){
  if(document.visibilityState==="visible"){const live=await fetchLive();if(live!==null&&gameController)gameController.updateLive(live);clearTimeout(livePollTimer);livePollTimer=setTimeout(pollLive,live?.length?10000:30000)}
  else{clearTimeout(livePollTimer);livePollTimer=setTimeout(pollLive,30000)}
}
function startLive(){clearTimeout(livePollTimer);pollLive();document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible"){clearTimeout(livePollTimer);pollLive()}})}

function renderGallery(finals,official){
  const wrap=qs("#previous-games"),photos=Array.isArray(official.previousGamePhotos)?official.previousGamePhotos:[],cards=[];
  finals.slice(0,3).forEach(g=>{
    const day=safe(g.date).slice(0,10),photo=photos.find(x=>(x.eventId&&x.eventId===g.eventId)||(x.date===day&&safe(x.away).toLowerCase()===safe(g.away).toLowerCase()&&safe(x.home).toLowerCase()===safe(g.home).toLowerCase()));
    cards.push('<article class="media-card">'+
      (photo?.image?'<img class="media-bg" src="'+safe(photo.image)+'" alt="'+safe(g.away)+' vs '+safe(g.home)+' UAAP game photo" loading="lazy">':'<div class="logo-pair">'+teamVisual(g.away)+teamVisual(g.home)+'</div>')+
      '<div class="media-card-content"><div class="media-kicker">UAAP · Final</div><div class="media-title">'+safe(g.away)+' '+safe(g.awayScore)+' — '+safe(g.homeScore)+' '+safe(g.home)+'</div><div class="media-meta">'+safe(g.displayTime||fmtDate(g.date))+'</div></div></article>');
  });
  wrap.innerHTML=cards.length?cards.join(""):'<div class="empty-card">No recent verified UAAP games are available.</div>';
}
function renderHighlights(official){
  const wrap=qs("#highlights"),items=Array.isArray(official.highlights)?official.highlights.slice(0,10):[];
  wrap.innerHTML=items.length?items.map(x=>'<article class="reel-card"><a class="highlight-link" href="'+safe(x.url||"https://uaap.org/posts/video_gallery")+'" target="_blank" rel="noopener">'+
    (x.thumbnail?'<img class="highlight-thumb" src="'+safe(x.thumbnail)+'" alt="'+safe(x.title)+'" loading="lazy">':'<div class="highlight-thumb"></div>')+
    '<div class="highlight-copy"><strong>'+safe(x.title)+'</strong><span>UAAP Official</span></div></a></article>').join(""):'<div class="empty-card">No verified Season 89 highlights are available yet.</div>';
}
function renderStandings(regional,official){
  const list=(Array.isArray(official.standings)&&official.standings.length?official.standings:regional.standings)||[];
  qs("#standings-body").innerHTML=list.map((x,i)=>'<tr><td>'+(i+1)+'</td><td><div class="standing-team">'+teamVisual(x.team)+'<span>'+safe(x.team)+'</span></div></td><td>'+safe(x.wins)+'</td><td>'+safe(x.losses)+'</td></tr>').join("");
}
function playerCard(x,rank){
  const average=x.ppg!==null&&x.ppg!==undefined;
  const value=average?safe(x.ppg):(x.pts!==null&&x.pts!==undefined?safe(x.pts):"—");
  const reb=average?x.rpg:x.reb,ast=average?x.apg:x.ast;
  return '<article class="top-player-card"><div class="top-player-rank">'+rank+'</div><div class="top-player-fallback">'+safe(initials(x.player))+'</div><div class="top-player-label">'+safe(x.team||"UAAP")+'</div><div class="top-player-name">'+safe(x.player)+'</div><div class="top-player-value">'+value+'<small>'+(average?'PPG':'PTS')+'</small></div><div class="top-player-meta">'+(reb!=null?safe(reb)+(average?' RPG':' REB')+' · ':'')+(ast!=null?safe(ast)+(average?' APG':' AST'):'')+(average&&x.games?' · '+safe(x.games)+' GP':'')+'</div></article>';
}
function renderTopPlayers(official){
  const list=Array.isArray(official.topPlayers)?official.topPlayers:[];
  qs("#top-players").innerHTML=list.length?list.slice(0,8).map((x,i)=>playerCard(x,i+1)).join(""):'<div class="empty-card">Official Season 89 player statistics will appear here when the UAAP stats feed exposes them.</div>';
}
function renderNews(official){
  const news=Array.isArray(official.headlines)?official.headlines.slice(0,6):[];
  qs("#news").innerHTML=news.length?news.map(x=>{
    const image=String(x.image||"").startsWith("http")?safe(x.image):"";
    const d=x.published?new Date(x.published):null,date=d&&!Number.isNaN(d.getTime())?d.toLocaleDateString(undefined,{month:"short",day:"numeric"}):"";
    return '<a class="news-card'+(image?" has-photo":"")+'" href="'+safe(x.url||"https://uaap.org/posts/articles")+'" target="_blank" rel="noopener">'+
      (image?'<img class="news-photo" src="'+image+'" alt="" loading="lazy" decoding="async">':"")+
      '<span class="news-copy"><small>UAAP Official'+(date?" · "+safe(date):"")+'</small><strong>'+safe(x.title)+'</strong></span></a>';
  }).join(""):'<div class="empty-card">No verified Season 89 UAAP Men\'s Basketball headlines are available yet.</div>';
}
async function load(){
  const [regional,official]=await Promise.all([getJSON("/regional-web.json",{}),getJSON("/uaap-official.json",{})]);
  const league=regional?.leagues?.uaap||{},games=Array.isArray(league.games)?league.games:[];
  const live=games.filter(g=>g.state==="in"||/live/i.test(g.status||""));
  const upcoming=games.filter(g=>g.state==="scheduled").sort((a,b)=>new Date(a.date)-new Date(b.date));
  const finals=games.filter(g=>g.state==="final").sort((a,b)=>new Date(b.date)-new Date(a.date));
  const logo=qs("#uaap-league-logo"),logoSrc=window.IMG_SCORE_LEAGUE_LOGOS?.uaap||"";
  if(logo&&logoSrc)logo.src=logoSrc;
  renderGames({live,upcoming,finals});startLive();renderGallery(finals,official);renderHighlights(official);renderStandings(league,official);renderTopPlayers(official);renderNews(official);
}
load();
})();