(()=>{
const qs=s=>document.querySelector(s);
const qsa=s=>[...document.querySelectorAll(s)];
const esc=v=>String(v??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[ch]));
const now=()=>Date.now();
const ROOT="/";
const POLL_MS=30000;

const CONFIG={
  soccer:{name:"Premier League",region:"England",scoreKey:"soccer",espn:"eng.1",path:"premier-league",highlightsFile:"premier-league-highlights.json",aliases:["premier league","epl"],description:"England's top-flight football competition.",competition:"Premier League"},
  jamaica_pl:{name:"Jamaican Premier League",region:"Jamaica",scoreKey:"jamaica_pl",path:"jamaican-premier-league",highlightsFile:"jamaica-pl-highlights.json",aliases:["jamaican premier league","jamaica premier league","jpl"],description:"Top-flight club football in Jamaica.",competition:"Premier League",category:"Jamaica",logo:"https://r2.thesportsdb.com/images/media/league/badgearchive/pg49fr1727716904.png"},
  mizoram_pl:{name:"Mizoram Premier League",region:"India",scoreKey:"mizoram_pl",path:"mizoram-premier-league",highlightsFile:"mizoram-pl-highlights.json",aliases:["mizoram premier league"],description:"Club football from Mizoram, India.",competition:"Mizoram Premier League",category:"India",logo:"https://static.toiimg.com/thumb/msid-92395083%2Cwidth-1280%2Cheight-720%2Cresizemode-4/92395083.jpg"},
  laliga:{name:"La Liga",region:"Spain",scoreKey:"laliga",espn:"esp.1",path:"la-liga",highlightsFile:"laliga-highlights.json",aliases:["la liga","laliga"],description:"Spain's top-flight football competition.",competition:"LaLiga"},
  el_salvador_reserves:{name:"Primera Division, Reserves",region:"El Salvador",scoreKey:"el_salvador_reserves",path:"el-salvador-reserves",highlightsFile:"el-salvador-reserves-highlights.json",aliases:["primera division reserves","el salvador reserves"],description:"Reserve competition football from El Salvador.",competition:"Primera Division, Reserves",category:"El Salvador",logo:"https://cdn.resfu.com/media/img/league_logos/primera-el-salvador.png"},
  seriea:{name:"Serie A",region:"Italy",scoreKey:"seriea",espn:"ita.1",path:"serie-a",highlightsFile:"seriea-highlights.json",aliases:["serie a"],description:"Italy's top-flight football competition.",competition:"Serie A"},
  bundesliga:{name:"Bundesliga",region:"Germany",scoreKey:"bundesliga",espn:"ger.1",path:"bundesliga",highlightsFile:"bundesliga-highlights.json",aliases:["bundesliga"],description:"Germany's top-flight football competition.",competition:"Bundesliga"},
  champions:{name:"UEFA Champions League",region:"Europe",scoreKey:"champions",espn:"uefa.champions",path:"champions-league",highlightsFile:"champions-highlights.json",aliases:["uefa champions league","champions league","ucl"],description:"UEFA's premier men's club competition.",competition:"UEFA Champions League"},
  ucl_women:{name:"UEFA Champions League Women",region:"Europe",scoreKey:"ucl_women",path:"champions-league-women",highlightsFile:"ucl-women-highlights.json",aliases:["women's champions league","womens champions league","uefa champions league women","uwcl"],description:"UEFA's premier women's club competition.",competition:"UEFA Champions League Women",category:"International Clubs",logo:"https://commons.wikimedia.org/wiki/Special:Redirect/file/UEFA%20Women%27s%20Champions%20League%20logo.svg"},
  mls:{name:"MLS",region:"United States / Canada",scoreKey:"mls",espn:"usa.1",path:"mls",highlightsFile:"mls-highlights.json",aliases:["major league soccer","mls"],description:"Major League Soccer in the United States and Canada.",competition:"MLS"},
  pfl:{name:"PFL",region:"Philippines",scoreKey:"pfl",path:"pfl",highlightsFile:"pfl-highlights.json",aliases:["philippines football league","philippine football league","pfl"],description:"Professional club football in the Philippines.",competition:"Philippines Football League",category:"Philippines",logo:"https://webcdn.ticketmax.ph/uploads/20241008/1728401723_895c0017ad979c1b70f1.jpg"}
};

const key=document.body?.dataset?.footballLeague||"soccer";
const cfg=CONFIG[key]||CONFIG.soccer;
let gameController=null;
let pollTimer=0;
let cachedGames=[];
let teamLogoMap=new Map();
let espnCachePromise=null;

function withTs(url){return url+(url.includes("?")?"&":"?")+"ts="+now()}
async function getJSON(url,fallback={}){
  try{
    const r=await fetch(withTs(url),{cache:"no-store"});
    if(!r.ok)throw new Error(String(r.status));
    return await r.json();
  }catch{return fallback}
}
function getEspnCache(){
  if(!espnCachePromise)espnCachePromise=getJSON("/football-espn-cache.json",{});
  return espnCachePromise;
}
function fmtDate(v){
  try{return new Date(v).toLocaleDateString(undefined,{month:"short",day:"numeric",year:"numeric"})}catch{return String(v||"")}
}
function fmtTime(v){
  try{return new Date(v).toLocaleString(undefined,{month:"short",day:"numeric",hour:"numeric",minute:"2-digit"})}catch{return String(v||"")}
}
function eventId(g){return String(g?.eventId||g?.id||[g?.away,g?.home,g?.date].filter(Boolean).join("|"))}

function normalizeEspnEvent(e){
  const comp=e?.competitions?.[0]||{};
  const competitors=comp.competitors||[];
  const home=competitors.find(x=>x?.homeAway==="home")||{};
  const away=competitors.find(x=>x?.homeAway==="away")||{};
  const state=e?.status?.type?.state||comp?.status?.type?.state||"pre";
  const logo=x=>x?.team?.logo||x?.team?.logos?.[0]?.href||"";
  const homeName=home?.team?.displayName||home?.team?.name||"Home";
  const awayName=away?.team?.displayName||away?.team?.name||"Away";
  if(logo(home))teamLogoMap.set(homeName,logo(home));
  if(logo(away))teamLogoMap.set(awayName,logo(away));
  return {
    eventId:String(e?.id||""),
    date:e?.date||comp?.date||"",
    displayTime:fmtTime(e?.date||comp?.date||""),
    home:homeName,away:awayName,
    homeLogo:logo(home),awayLogo:logo(away),
    homeScore:home?.score??"",
    awayScore:away?.score??"",
    state:state==="in"?"live":state==="post"?"final":"scheduled",
    status:e?.status?.type?.shortDetail||e?.status?.type?.detail||comp?.status?.type?.shortDetail||"",
    venue:comp?.venue?.fullName||"",
    competition:cfg.name
  };
}

function validLocalGame(g){
  const comp=String(g?.competition||"").toLowerCase();
  const cat=String(g?.category||"").toLowerCase();
  const wantComp=String(cfg.competition||cfg.name).toLowerCase();
  const wantCat=String(cfg.category||"").toLowerCase();
  if(wantCat&&cat!==wantCat)return false;
  if(wantComp&&comp&&comp!==wantComp){
    const aliases=cfg.aliases||[];
    if(!aliases.some(a=>comp.includes(a)))return false;
  }
  return true;
}
function normalizeLocalGame(g){
  return {
    eventId:String(g?.eventId||""),
    date:g?.date||"",
    displayTime:g?.displayTime||fmtTime(g?.date),
    home:g?.home||"Home",away:g?.away||"Away",
    homeLogo:g?.homeLogo||"",awayLogo:g?.awayLogo||"",
    homeScore:g?.homeScore??"",awayScore:g?.awayScore??"",
    state:g?.state==="final"?"final":g?.state==="live"?"live":"scheduled",
    status:g?.status||"",
    venue:g?.venue||"",
    competition:g?.competition||cfg.name
  };
}

async function fetchGames(){
  let cached=[];
  if(cfg.espn){
    const cache=await getEspnCache();
    const cachedLeague=cache?.leagues?.[key];
    if(cachedLeague?.leagueLogo)setLeagueLogo(cachedLeague.leagueLogo);
    cached=(Array.isArray(cachedLeague?.games)?cachedLeague.games:[])
      .filter(validLocalGame)
      .map(normalizeLocalGame);

    const today=new Date().toISOString().slice(0,10).replaceAll("-","");
    const worker="https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league="+encodeURIComponent(cfg.scoreKey)+"&dates="+today;
    const direct="https://site.api.espn.com/apis/site/v2/sports/soccer/"+cfg.espn+"/scoreboard?dates="+today;
    for(const url of [worker,direct]){
      try{
        const r=await fetch(withTs(url),{cache:"no-store"});
        if(!r.ok)continue;
        const j=await r.json();
        const fresh=(j?.events||[]).map(normalizeEspnEvent);
        if(fresh.length){
          const lg=j?.leagues?.[0];
          const logo=lg?.logos?.find?.(x=>/default|full/i.test(String(x?.rel||"")))?.href||lg?.logos?.[0]?.href||lg?.logo||"";
          if(logo)setLeagueLogo(logo);
          const map=new Map();
          for(const g of [...cached,...fresh])map.set(eventId(g),g);
          return [...map.values()].sort((a,b)=>(Date.parse(a.date)||0)-(Date.parse(b.date)||0));
        }
      }catch{}
    }
    if(cached.length)return cached;
  }
  const local=await getJSON("/sportradar-soccer-data.json",{});
  return (local?.leagues?.[key]?.games||[]).filter(validLocalGame).map(normalizeLocalGame);
}

function setLeagueLogo(src){
  const img=qs("#football-league-logo");
  const fb=qs("#football-league-logo-fallback");
  if(!img)return;
  if(src){
    img.src=src;
    img.hidden=false;
    img.onerror=()=>{img.hidden=true;if(fb)fb.classList.add("visible")};
  }else{
    img.hidden=true;
    if(fb)fb.classList.add("visible");
  }
}

const TEAM_LOGO_ALIASES={
  bundesliga:{
    "bayern munich":"FC Bayern Munchen",
    "borussia dortmund":"BV Borussia 09 Dortmund",
    "borussia monchengladbach":"Borussia Monchengladbach",
    "fsv mainz":"1. FSV Mainz 05",
    "fc cologne":"1. FC Koln",
    "tsg hoffenheim":"TSG 1899 Hoffenheim",
    "werder bremen":"SV Werder Bremen",
    "bayer leverkusen":"Bayer 04 Leverkusen",
    "union berlin":"1. FC Union Berlin"
  },
  ucl_women:{
    "inter milano":"FC Internazionale Milano",
    "bayern munich":"FC Bayern Munchen",
    "real madrid":"Real Madrid CF Femenino",
    "juventus turin":"Juventus FC",
    "sl benfica":"Sport Lisboa e Benfica",
    "olympique lyon":"OL Lyonnes",
    "hacken gothenburg":"BK Hacken FF",
    "oud-heverlee leuven":"Oud-Heverlee Leuven Women",
    "paris saint-germain":"Paris Saint-Germain FC",
    "servette fc chenois feminin":"Servette FC Chenois Feminin"
  },
  pfl:{
    "mendiola fc 1991":"Valenzuela PB Mendiola FC",
    "azkals development club":"PFF Development Team",
    "azkals development team":"PFF Development Team",
    "kaya fc iloilo":"Kaya FC-Iloilo"
  },
  mizoram_pl:{
    "mls fc lawtngtlai":"MLS FC",
    "kanan fc aizawl":"Kanan FC"
  }
};
function normalizedTeamName(value){
  return String(value||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9]+/g," ").trim();
}
function loadLocalTeamLogos(){
  const registry=window.IMG_FOOTBALL_TEAM_LOGOS?.[key]||{};
  for(const [name,logo] of Object.entries(registry)){
    if(name&&logo)teamLogoMap.set(normalizedTeamName(name),logo);
  }
  const aliases=TEAM_LOGO_ALIASES[key]||{};
  for(const [alias,canonical] of Object.entries(aliases)){
    const logo=teamLogoMap.get(normalizedTeamName(canonical));
    if(logo)teamLogoMap.set(normalizedTeamName(alias),logo);
  }
}
async function fetchTeamLogos(){
  loadLocalTeamLogos();
  if(!cfg.espn)return;
  try{
    const r=await fetch("https://site.api.espn.com/apis/site/v2/sports/soccer/"+cfg.espn+"/teams?limit=100",{cache:"force-cache"});
    if(!r.ok)return;
    const j=await r.json();
    const teams=j?.sports?.[0]?.leagues?.[0]?.teams||[];
    for(const row of teams){
      const t=row?.team||row;
      const name=t?.displayName||t?.name;
      const logo=t?.logos?.[0]?.href||t?.logo||"";
      if(name&&logo&&!teamLogoMap.has(normalizedTeamName(name)))teamLogoMap.set(normalizedTeamName(name),logo);
    }
  }catch{}
}
function teamLogo(name,provided=""){return teamLogoMap.get(normalizedTeamName(name))||provided||teamLogoMap.get(name)||""}

function teamBlock(name,side,score="",logo=""){
  const src=teamLogo(name,logo);
  const hasScore=score!==null&&score!==undefined&&String(score)!=="";
  const scoreHtml=hasScore?'<div class="team-score" data-score-side="'+side+'">'+esc(score)+'</div>':"";
  return '<div class="game-team '+(side==="right"?"right":"")+'">'+
    (side!=="right"&&src?'<img class="team-logo" src="'+esc(src)+'" alt="'+esc(name)+' logo">':"")+
    '<div class="team-copy"><div class="team-main">'+
      (side==="right"?scoreHtml:"")+
      '<div class="team-name">'+esc(name)+'</div>'+
      (side!=="right"?scoreHtml:"")+
    '</div><div class="team-side">'+(side==="right"?"Home":"Away")+'</div></div>'+
    (side==="right"&&src?'<img class="team-logo" src="'+esc(src)+'" alt="'+esc(name)+' logo">':"")+
  '</div>';
}

function splitGames(games){
  return {
    live:games.filter(g=>g.state==="live").sort((a,b)=>Date.parse(a.date)-Date.parse(b.date)),
    upcoming:games.filter(g=>g.state==="scheduled"&&Date.parse(g.date)>=Date.now()-6*3600000).sort((a,b)=>Date.parse(a.date)-Date.parse(b.date)),
    finals:games.filter(g=>g.state==="final").sort((a,b)=>Date.parse(b.date)-Date.parse(a.date))
  };
}

function renderGames(games){
  const {live,upcoming,finals}=splitGames(games);
  const groups={live,upcoming,results:finals};
  const slot=qs("#game-slot");
  if(!slot)return;
  let active=live.length?"live":upcoming.length?"upcoming":"results";
  let shown="";

  const patch=g=>{
    const card=slot.querySelector(".featured-game");
    if(!card||card.dataset.eventId!==eventId(g))return false;
    const away=card.querySelector('[data-score-side="left"]');
    const home=card.querySelector('[data-score-side="right"]');
    if(away&&away.textContent!==String(g.awayScore??""))away.textContent=String(g.awayScore??"");
    if(home&&home.textContent!==String(g.homeScore??""))home.textContent=String(g.homeScore??"");
    const status=card.querySelector(".game-status");
    if(status){
      const next=g.state==="live"?"LIVE":g.state==="final"?"FINAL":(g.displayTime||fmtTime(g.date));
      if(status.textContent!==next)status.textContent=next;
    }
    return true;
  };
  const paint=(tab,force=false)=>{
    active=tab;
    qsa(".tab-btn").forEach(b=>b.classList.toggle("active",b.dataset.tab===tab));
    const g=(groups[tab]||[])[0];
    if(!g){
      shown="";
      slot.innerHTML='<div class="empty-card">No verified '+esc(cfg.name)+' game is available for this tab.</div>';
      return;
    }
    if(!force&&shown===eventId(g)&&patch(g))return;
    shown=eventId(g);
    const showScore=g.state==="live"||g.state==="final";
    const center=g.state==="live"?"LIVE":g.state==="final"?"FINAL":(g.displayTime||fmtTime(g.date));
    slot.innerHTML='<article class="featured-game" data-event-id="'+esc(shown)+'" data-competition="'+esc(cfg.name)+'">'+
      teamBlock(g.away,"left",showScore?g.awayScore:"",g.awayLogo)+
      '<div class="game-center"><div class="game-status">'+esc(center)+'</div>'+(g.venue?'<div class="game-meta">'+esc(g.venue)+'</div>':"")+'</div>'+
      teamBlock(g.home,"right",showScore?g.homeScore:"",g.homeLogo)+
    '</article>';
  };
  qsa(".tab-btn").forEach(b=>b.onclick=()=>paint(b.dataset.tab,true));
  paint(active,true);
  gameController={
    update(next){
      const nextGroups=splitGames(next);
      groups.live=nextGroups.live;groups.upcoming=nextGroups.upcoming;groups.results=nextGroups.finals;
      if(groups.live.length&&active==="live")paint("live");
      else if(groups.live.length&&active!=="live")paint("live",true);
      else if(!groups.live.length&&active==="live")paint(groups.upcoming.length?"upcoming":"results",true);
    }
  };
}

function renderPreviousGames(games){
  const wrap=qs("#previous-games");
  if(!wrap)return;
  const finals=splitGames(games).finals.slice(0,8);
  wrap.innerHTML=finals.length?finals.map(g=>{
    const a=teamLogo(g.away,g.awayLogo),h=teamLogo(g.home,g.homeLogo);
    return '<article class="media-card"><div class="logo-pair">'+
      (a?'<img src="'+esc(a)+'" alt="">':"")+(h?'<img src="'+esc(h)+'" alt="">':"")+
      '</div><div class="media-card-content"><div class="media-kicker">'+esc(cfg.name)+' · Final</div>'+
      '<div class="media-title">'+esc(g.away)+' '+esc(g.awayScore)+' — '+esc(g.homeScore)+' '+esc(g.home)+'</div>'+
      '<div class="media-meta">'+esc(g.displayTime||fmtDate(g.date))+(g.venue?" · "+esc(g.venue):"")+'</div></div></article>';
  }).join(""):'<div class="empty-card">No recent verified '+esc(cfg.name)+' results are available.</div>';
}

async function fetchEspnHighlights(games){
  if(!cfg.espn)return [];
  const finals=splitGames(games).finals.filter(g=>g.eventId).slice(0,4);
  const found=[];
  await Promise.allSettled(finals.map(async g=>{
    const url="https://site.api.espn.com/apis/site/v2/sports/soccer/"+cfg.espn+"/summary?event="+encodeURIComponent(g.eventId);
    const r=await fetch(withTs(url),{cache:"no-store"});
    if(!r.ok)return;
    const j=await r.json();
    const videos=[...(Array.isArray(j?.videos)?j.videos:[]),...(Array.isArray(j?.highlights)?j.highlights:[])];
    for(const v of videos){
      const link=v?.links?.web?.href||v?.links?.api?.self?.href||v?.href||v?.url||"";
      const image=v?.thumbnail||v?.image||v?.poster||v?.images?.[0]?.url||"";
      const title=v?.headline||v?.title||v?.description||[g.away,g.home].join(" vs ");
      if(link||image)found.push({title,link,image,meta:[g.away,g.home].join(" vs ")});
    }
  }));
  return found.filter((x,i,a)=>i===a.findIndex(y=>(y.link||y.title)===(x.link||x.title))).slice(0,8);
}
function decodeEntities(value){
  const t=document.createElement("textarea");
  t.innerHTML=String(value??"");
  return t.value;
}
function ensureFootballHighlightDialog(){
  let d=document.getElementById("footballHighlightDialog");
  if(d)return d;
  d=document.createElement("dialog");
  d.id="footballHighlightDialog";
  d.className="football-highlight-dialog";
  d.innerHTML='<div class="football-highlight-shell"><button type="button" class="football-highlight-close" aria-label="Close highlight">×</button><div id="footballHighlightPlayer"></div></div>';
  document.body.appendChild(d);
  d.querySelector(".football-highlight-close").addEventListener("click",()=>d.close());
  d.addEventListener("click",e=>{if(e.target===d)d.close()});
  d.addEventListener("close",()=>{const p=d.querySelector("#footballHighlightPlayer");if(p)p.innerHTML=""});
  return d;
}
function playFootballHighlight(item){
  if(!item?.embedUrl)return false;
  const d=ensureFootballHighlightDialog();
  const host=d.querySelector("#footballHighlightPlayer");
  host.innerHTML='<div class="football-highlight-video"><iframe src="'+esc(item.embedUrl)+'?autoplay=1&playsinline=1&rel=0" title="'+esc(decodeEntities(item.title||cfg.name+" highlight"))+'" allow="autoplay; encrypted-media; picture-in-picture; web-share" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div>';
  d.showModal();
  return true;
}
function renderHighlights(items){
  const wrap=qs("#highlights");
  if(!wrap)return;
  const seenTitles=new Set();
  items=(Array.isArray(items)?items:[]).filter(x=>{
    const title=decodeEntities(x?.title||"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim();
    if(!title)return false;
    if(seenTitles.has(title))return false;
    seenTitles.add(title);
    return true;
  });
  if(!items.length){
    wrap.innerHTML='<div class="empty-card">No verified '+esc(cfg.name)+' highlight video is available from the current feed.</div>';
    return;
  }
  wrap.innerHTML=items.map((x,i)=>{
    const link=x.url||x.link||"#";
    const image=x.thumbnail||x.image||"";
    const meta=[x.sourceName||x.provider||cfg.name,x.publishedAt?fmtDate(x.publishedAt):""].filter(Boolean).join(" · ");
    const tag=x.embedUrl?"button":"a";
    const attrs=x.embedUrl
      ?'type="button" data-football-highlight="'+i+'"'
      :(link!=="#"? 'href="'+esc(link)+'" target="_blank" rel="noopener"':'href="#"');
    return '<'+tag+' class="football-highlight-link" '+attrs+'><article class="media-card highlight-card">'+
      (image?'<img class="media-bg" src="'+esc(image)+'" alt="" loading="lazy">':"")+
      '<span class="play-button" aria-hidden="true">▶</span><div class="media-card-content"><div class="media-kicker">HIGHLIGHT</div><div class="media-title">'+esc(decodeEntities(x.title))+'</div><div class="media-meta">'+esc(meta||cfg.name)+'</div></div>'+
    '</article></'+tag+'>';
  }).join("");
  wrap.querySelectorAll("[data-football-highlight]").forEach(btn=>btn.addEventListener("click",()=>{
    const item=items[Number(btn.dataset.footballHighlight)];
    playFootballHighlight(item);
  }));
}

function normalizeEspnStandings(j){
  const entries=[];
  const walk=node=>{
    if(!node||typeof node!=="object")return;
    if(Array.isArray(node?.standings?.entries)){
      for(const e of node.standings.entries){
        const stats=Object.fromEntries((e?.stats||[]).map(s=>[String(s?.name||s?.abbreviation||"").toLowerCase(),s?.value??s?.displayValue]));
        entries.push({
          rank:e?.stats?.find?.(s=>/rank/i.test(String(s?.name||s?.abbreviation)))?.value??e?.seed??entries.length+1,
          team:e?.team?.displayName||e?.team?.name||"",
          logo:e?.team?.logos?.[0]?.href||e?.team?.logo||"",
          played:stats.gamesplayed??stats.games??stats.gp??"",
          wins:stats.wins??stats.w??"",
          draws:stats.ties??stats.draws??stats.d??"",
          losses:stats.losses??stats.l??"",
          goalDiff:stats.pointdifferential??stats.goaldifferential??stats.gd??"",
          points:stats.points??stats.pts??""
        });
      }
    }
    for(const c of (node.children||[]))walk(c);
  };
  walk(j);
  return entries.filter(x=>x.team);
}
async function fetchStandings(localLeague){
  let rows=(localLeague?.standings||[]).filter(x=>x?.team);
  if(rows.length)return rows;
  if(!cfg.espn)return [];
  const cache=await getEspnCache();
  const cachedRows=cache?.leagues?.[key]?.standings;
  if(Array.isArray(cachedRows)&&cachedRows.length)return cachedRows;
  const urls=[
    "https://site.api.espn.com/apis/v2/sports/soccer/"+cfg.espn+"/standings",
    "https://site.web.api.espn.com/apis/v2/sports/soccer/"+cfg.espn+"/standings"
  ];
  for(const url of urls){
    try{
      const r=await fetch(withTs(url),{cache:"no-store"});
      if(!r.ok)continue;
      const j=await r.json();
      rows=normalizeEspnStandings(j);
      if(rows.length)return rows;
    }catch{}
  }
  return [];
}
function renderStandings(rows,sourceName=""){
  const body=qs("#football-standings");
  const panel=qs("#standings-panel");
  if(!body||!panel)return;
  if(!rows.length){
    panel.innerHTML='<div class="panel-title">Standings</div><div class="empty-card">Current verified standings are not available from this league feed.</div>';
    return;
  }
  body.innerHTML=rows.slice(0,40).map((x,i)=>{
    const logo=x.logo||teamLogo(x.team);
    if(logo)teamLogoMap.set(x.team,logo);
    return '<tr><td>'+esc(x.rank||i+1)+'</td><td><div class="standing-team">'+(logo?'<img src="'+esc(logo)+'" alt="">':"")+'<span>'+esc(x.team)+'</span></div></td>'+
      '<td>'+esc(x.played??"")+'</td><td>'+esc(x.wins??"")+'</td><td>'+esc(x.draws??"")+'</td><td>'+esc(x.losses??"")+'</td><td>'+esc(x.goalDiff??"")+'</td><td>'+esc(x.points??"")+'</td></tr>';
  }).join("");
  const note=qs("#standings-source");
  if(note)note.textContent=sourceName?"Source: "+sourceName:"";
}

function renderTopPlayers(stats){
  const wrap=qs("#top-players");
  if(!wrap)return;
  const groups=Array.isArray(stats?.groups)?stats.groups:[];
  const cards=[];
  for(const group of groups){
    for(const row of (group?.rows||[]).slice(0,4)){
      cards.push({
        label:group.title||"Leader",
        name:row.player||row.name||"",
        team:row.team||"",
        value:row.displayValue??row.value??"",
        suffix:group.suffix||""
      });
    }
  }
  const unique=cards.filter((x,i,a)=>x.name&&i===a.findIndex(y=>y.name===x.name&&y.label===x.label)).slice(0,10);
  wrap.innerHTML=unique.length?unique.map((x,i)=>
    '<article class="top-player-card no-photo"><div class="top-player-rank">#'+(i+1)+'</div><div class="top-player-label">'+esc(x.label)+'</div>'+
    '<div class="top-player-name">'+esc(x.name)+'</div><div class="media-meta">'+esc(x.team)+'</div>'+
    '<div class="top-player-value">'+esc(x.value)+' <small>'+esc(x.suffix)+'</small></div></article>'
  ).join(""):'<div class="empty-card">Verified player leaders are not available from the current '+esc(cfg.name)+' data feed.</div>';
}

function articleMatches(item){
  const text=[item?.title,item?.description,item?.sport,item?.region].join(" ").toLowerCase();
  if((cfg.aliases||[]).some(a=>text.includes(a)))return true;
  const teamNames=[...teamLogoMap.keys()].slice(0,40).map(x=>x.toLowerCase());
  return teamNames.some(t=>t.length>4&&text.includes(t));
}
function renderNews(news){
  const wrap=qs("#news");
  if(!wrap)return;
  const all=Array.isArray(news?.items)?news.items:[];
  let items=all.filter(articleMatches);
  if(items.length<6){
    const football=all.filter(x=>/football|soccer/i.test([x?.title,x?.description].join(" ")));
    items=[...items,...football.filter(x=>!items.includes(x))];
  }
  items=items.slice(0,9);
  wrap.innerHTML=items.length?items.map(x=>
    '<a class="news-card" href="'+esc(x.link||"#")+'" target="_blank" rel="noopener">'+
      (x.image?'<img class="news-photo" src="'+esc(x.image)+'" alt="" loading="lazy">':"")+
      '<span class="news-copy"><small>'+esc(x.source||"Football")+'</small><strong>'+esc(x.title||"Football update")+'</strong></span></a>'
  ).join(""):'<div class="empty-card">No current '+esc(cfg.name)+' headlines matched the verified IMG news feed.</div>';
}

async function load(){
  if(cfg.logo)setLeagueLogo(cfg.logo);
  const [local,stats,news,highlightData,games]=await Promise.all([
    getJSON("/sportradar-soccer-data.json",{}),
    getJSON("/stats-data.json",{}),
    getJSON("/news-data.json",{}),
    getJSON("/"+cfg.highlightsFile,{highlights:[]}),
    fetchGames()
  ]);
  cachedGames=games;
  await fetchTeamLogos();
  renderGames(games);
  renderPreviousGames(games);

  const localLeague=local?.leagues?.[key]||{};
  const standings=await fetchStandings(localLeague);
  renderStandings(standings,localLeague?.sourceName|| (cfg.espn?"ESPN public football data":""));
  const highlights=(Array.isArray(highlightData?.highlights)?highlightData.highlights:[]).filter(x=>x?.verified===true);
  renderHighlights(highlights);
  renderTopPlayers(stats?.leagues?.[key]||{});
  renderNews(news);
  startPolling();
}

async function poll(){
  clearTimeout(pollTimer);
  if(document.hidden){pollTimer=setTimeout(poll,30000);return}
  const games=await fetchGames();
  if(games.length){
    const hadLive=cachedGames.some(g=>g.state==="live");
    const hasLive=games.some(g=>g.state==="live");
    cachedGames=games;
    if(gameController)gameController.update(games);
    if(hadLive!==hasLive)renderPreviousGames(games);
  }
  pollTimer=setTimeout(poll,POLL_MS);
}
function startPolling(){
  clearTimeout(pollTimer);
  pollTimer=setTimeout(poll,POLL_MS);
  document.addEventListener("visibilitychange",()=>{if(!document.hidden){clearTimeout(pollTimer);poll()}});
  addEventListener("focus",()=>{if(!document.hidden){clearTimeout(pollTimer);poll()}});
  addEventListener("online",()=>{if(!document.hidden){clearTimeout(pollTimer);poll()}});
}
load();
})();