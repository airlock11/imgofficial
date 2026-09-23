(()=>{
const qs=s=>document.querySelector(s);
const qsa=s=>[...document.querySelectorAll(s)];
const safe=v=>String(v??"");
const fmtDate=v=>{try{return new Date(v).toLocaleDateString(undefined,{month:"short",day:"numeric",year:"numeric"})}catch{return v||""}};
const fmtTime=v=>{try{return new Date(v).toLocaleTimeString([],{hour:"numeric",minute:"2-digit"})}catch{return "—"}};
const PBA_LIVE_URL="https://img-api-proxy.magsipocarnie.workers.dev/regional-scores?league=pba";
let gameController=null;
let livePollTimer=null;

async function getJSON(url,fallback={}){
  try{
    const r=await fetch(url+"?ts="+Date.now(),{cache:"no-store"});
    if(!r.ok)throw new Error(r.status);
    return await r.json();
  }catch{return fallback}
}

async function load(){
  const [regional,official,yt,assets]=await Promise.all([
    getJSON("/regional-web.json",{}),
    getJSON("/pba-official.json",{}),
    getJSON("/youtube-live.json",{}),
    getJSON("/pba-assets.json",{teams:{}})
  ]);

  const league=regional?.leagues?.pba||{};
  const games=Array.isArray(league.games)?league.games:[];
  const live=games.filter(g=>g.state==="in"||/live/i.test(g.status||""));
  const upcoming=games.filter(g=>g.state==="scheduled").sort((a,b)=>new Date(a.date)-new Date(b.date));
  const finals=games.filter(g=>g.state==="final").sort((a,b)=>new Date(b.date)-new Date(a.date));
  const streams=(yt.streams||[]).filter(x=>x.leagueKey==="pba"&&String(x.verificationStatus||x.stream?.verificationStatus||"")==="verified");

  const logo=qs("#pba-league-logo");
  if(logo&&assets.leagueLogo)logo.src=assets.leagueLogo;
  renderGames({live,upcoming,finals,assets});
  startLiveScorePolling();
  renderGallery({finals,assets,official});
  renderHighlights({streams,official});
  renderStandings({official,assets});
  renderTopPlayers(official);
  renderNews(official);
}

function teamLogo(name,assets){return assets?.teams?.[name]||""}

function teamBlock(name,side,assets,score=""){
  const src=teamLogo(name,assets);
  const hasScore=score!==null&&score!==undefined&&String(score)!=="";
  const scoreHtml=hasScore?`<div class="team-score" data-score-side="${side}">${safe(score)}</div>`:"";
  const nameHtml=`<div class="team-name">${safe(name)}</div>`;
  return `<div class="game-team ${side==="right"?"right":""}">
    ${side!=="right"&&src?`<img class="team-logo" src="${src}" alt="${safe(name)} logo">`:""}
    <div class="team-copy">
      <div class="team-main">
        ${side==="right"?scoreHtml:""}
        ${nameHtml}
        ${side!=="right"?scoreHtml:""}
      </div>
      <div class="team-side">${side==="right"?"Home":"Away"}</div>
    </div>
    ${side==="right"&&src?`<img class="team-logo" src="${src}" alt="${safe(name)} logo">`:""}
  </div>`
}

function renderGames({live,upcoming,finals,assets}){
  const groups={live:[...live],upcoming:[...upcoming],results:[...finals]};
  const slot=qs("#game-slot");
  let active=live.length?"live":upcoming.length?"upcoming":"results";
  let shownEventId="";

  const eventId=g=>safe(g?.eventId||g?.id||[g?.away,g?.home,g?.date].filter(Boolean).join("|"));

  const patchLiveCard=g=>{
    const id=eventId(g);
    const card=slot?.querySelector(".featured-game");
    if(!card||card.dataset.eventId!==id)return false;
    const away=slot.querySelector('[data-score-side="left"]');
    const home=slot.querySelector('[data-score-side="right"]');
    if(away&&away.textContent!==safe(g.awayScore))away.textContent=safe(g.awayScore);
    if(home&&home.textContent!==safe(g.homeScore))home.textContent=safe(g.homeScore);
    const status=slot.querySelector(".game-status");
    if(status&&status.textContent!=="LIVE")status.textContent="LIVE";
    return true;
  };

  const paint=(key,force=false)=>{
    active=key;
    const g=(groups[key]||[])[0];
    qsa(".tab-btn").forEach(b=>b.classList.toggle("active",b.dataset.tab===key));
    if(!g){
      shownEventId="";
      slot.innerHTML='<div class="empty-card">No verified PBA game is available for this tab.</div>';
      return;
    }
    const final=g.state==="final";
    const liveGame=g.state==="in"||/live/i.test(g.status||"");
    if(!force&&key==="live"&&liveGame&&shownEventId===eventId(g)&&patchLiveCard(g))return;
    const showScore=final||liveGame;
    const centerMain=final
      ?"FINAL"
      :liveGame
        ?"LIVE"
        :safe(g.displayTime||fmtDate(g.date));
    shownEventId=eventId(g);
    slot.innerHTML=`<article class="featured-game" data-event-id="${shownEventId}">
      ${teamBlock(g.away||"Away","left",assets,showScore?g.awayScore:"")}
      <div class="game-center">
        <div class="game-status">${centerMain}</div>
      </div>
      ${teamBlock(g.home||"Home","right",assets,showScore?g.homeScore:"")}
    </article>`;
  };

  qsa(".tab-btn").forEach(b=>b.addEventListener("click",()=>paint(b.dataset.tab,true)));
  paint(active,true);

  gameController={
    updateLive(nextLive){
      const hadLive=groups.live.length>0;
      groups.live=Array.isArray(nextLive)?nextLive:[];
      const hasLive=groups.live.length>0;
      if(hasLive&&active==="live"){
        paint("live");
      }else if(hasLive&&!hadLive){
        paint("live",true);
      }else if(!hasLive&&hadLive&&active==="live"){
        paint(groups.upcoming.length?"upcoming":"results",true);
      }
    }
  };
}

function normalizeWorkerLiveEvent(event){
  const competitors=event?.competitions?.[0]?.competitors||[];
  const home=competitors.find(x=>x?.homeAway==="home")||{};
  const away=competitors.find(x=>x?.homeAway==="away")||{};
  const state=event?.status?.type?.state;
  if(state&&state!=="in")return null;
  return {
    eventId:safe(event?.id),
    date:event?.date||new Date().toISOString(),
    displayTime:"LIVE",
    away:away?.team?.displayName||"Away",
    home:home?.team?.displayName||"Home",
    awayScore:safe(away?.score??"0"),
    homeScore:safe(home?.score??"0"),
    status:event?.status?.type?.shortDetail||"Live",
    state:"in"
  };
}

async function fetchLiveScores(){
  const controller=new AbortController();
  const timeout=setTimeout(()=>controller.abort(),8000);
  try{
    const r=await fetch(PBA_LIVE_URL+"&ts="+Date.now(),{
      cache:"no-store",
      signal:controller.signal
    });
    if(!r.ok)throw new Error(r.status);
    const data=await r.json();
    if(!Array.isArray(data?.events))throw new Error("Invalid live-score payload");
    return data.events.map(normalizeWorkerLiveEvent).filter(Boolean);
  }catch{
    return null;
  }finally{
    clearTimeout(timeout);
  }
}

async function pollLiveScores(){
  if(document.visibilityState==="visible"){
    const live=await fetchLiveScores();
    if(live!==null&&gameController)gameController.updateLive(live);
    clearTimeout(livePollTimer);
    livePollTimer=setTimeout(pollLiveScores,live?.length?10000:30000);
  }else{
    clearTimeout(livePollTimer);
    livePollTimer=setTimeout(pollLiveScores,30000);
  }
}

function startLiveScorePolling(){
  clearTimeout(livePollTimer);
  pollLiveScores();
  document.addEventListener("visibilitychange",()=>{
    if(document.visibilityState==="visible"){
      clearTimeout(livePollTimer);
      pollLiveScores();
    }
  });
}

function renderGallery({finals,assets,official}){
  const wrap=qs("#previous-games");
  const exactPhotos=Array.isArray(official.previousGamePhotos)?official.previousGamePhotos:[];
  const cards=[];
  const recentFinals=(Array.isArray(finals)?finals:[]).slice(0,3);
  const norm=v=>safe(v).trim().toLowerCase();

  recentFinals.forEach(g=>{
    const day=safe(g.date).slice(0,10);
    const photo=exactPhotos.find(x=>
      (x.eventId&&x.eventId===g.eventId) ||
      (
        x.date===day &&
        norm(x.away)===norm(g.away) &&
        norm(x.home)===norm(g.home)
      )
    );
    const a=teamLogo(g.away,assets),h=teamLogo(g.home,assets);
    const image=photo?.image||"";
    cards.push(`<article class="media-card">
      ${image?`<img class="media-bg" src="${safe(image)}" alt="${safe(g.away)} vs ${safe(g.home)} PBA game photo">`:`<div class="logo-pair">${a?`<img src="${a}" alt="">`:""}${h?`<img src="${h}" alt="">`:""}</div>`}
      <div class="media-card-content">
        <div class="media-kicker">PBA · Final</div>
        <div class="media-title">${safe(g.away)} ${safe(g.awayScore)} — ${safe(g.homeScore)} ${safe(g.home)}</div>
        <div class="media-meta">${safe(g.displayTime||fmtDate(g.date))}</div>
      </div>
    </article>`);
  });

  wrap.innerHTML=cards.length?cards.join(""):'<div class="empty-card">No recent verified PBA games are available.</div>';
}

function renderHighlights({streams,official}){
  const wrap=qs("#highlights");
  const shorts=Array.isArray(official.shorts)?official.shorts:[];

  if(!shorts.length){
    wrap.innerHTML='<div class="empty-card">PBA Official Shorts are temporarily unavailable.</div>';
    return;
  }

  wrap.innerHTML=shorts.slice(0,10).map(x=>`<article class="reel-card">
    <div class="reel-media" tabindex="0" data-short-id="${safe(x.id)}" aria-label="Play ${safe(x.title)}">
      <img class="reel-thumb" src="${safe(x.thumbnail)}" alt="${safe(x.title)}" loading="lazy">
      <span class="reel-shade"></span>
      <span class="reel-source">PBA SHORTS</span>
    </div>
    <div class="reel-caption">
      <strong>${safe(x.title)}</strong>
      <span>PBA Official</span>
    </div>
  </article>`).join("");

  const startPreview=stage=>{
    const id=stage.dataset.shortId;
    if(!id||stage.querySelector(".reel-frame"))return;
    const frame=document.createElement("iframe");
    frame.className="reel-frame";
    frame.src=`https://www.youtube.com/embed/${encodeURIComponent(id)}?autoplay=1&mute=1&controls=0&playsinline=1&rel=0&disablekb=1&fs=0&iv_load_policy=3&loop=1&playlist=${encodeURIComponent(id)}`;
    frame.title=stage.getAttribute("aria-label")||"PBA Short";
    frame.loading="eager";
    frame.allow="autoplay; encrypted-media; picture-in-picture";
    frame.referrerPolicy="strict-origin-when-cross-origin";
    stage.appendChild(frame);
    stage.classList.add("is-playing");
  };

  const stopPreview=stage=>{
    const frame=stage.querySelector(".reel-frame");
    if(frame)frame.remove();
    stage.classList.remove("is-playing");
  };

  qsa("#highlights .reel-media").forEach(stage=>{
    stage.addEventListener("mouseenter",()=>startPreview(stage));
    stage.addEventListener("mouseleave",()=>stopPreview(stage));
    stage.addEventListener("focus",()=>startPreview(stage));
    stage.addEventListener("blur",()=>stopPreview(stage));
    stage.addEventListener("click",()=>startPreview(stage));
  });
}

function renderStandings({official,assets}){
  const rows=list=>(list||[]).map((x,i)=>{
    const logo=teamLogo(x.team,assets);
    return `<tr>
      <td>${i+1}</td>
      <td><div class="standing-team">${logo?`<img src="${logo}" alt="${safe(x.team)} logo">`:""}<span>${safe(x.team)}</span></div></td>
      <td>${safe(x.wins)}</td><td>${safe(x.losses)}</td>
    </tr>`
  }).join("");
  qs("#group-a").innerHTML=rows(official?.rankings?.groupA);
  qs("#group-b").innerHTML=rows(official?.rankings?.groupB);
}

function initials(name){
  return safe(name).split(/\s+/).map(x=>x[0]).join("").slice(0,3).toUpperCase()
}

function playerCard(x,rank,label,value){
  return `<article class="top-player-card">
    <div class="top-player-rank">${rank}</div>
    ${x.photo?`<img class="top-player-photo" src="${safe(x.photo)}" alt="${safe(x.player)} photo">`:`<div class="top-player-fallback">${initials(x.player)}</div>`}
    <div class="top-player-label">${safe(label)}</div>
    <div class="top-player-name">${safe(x.player)}</div>
    <div class="top-player-value">${safe(value)}<small>${label==="Points"?"PPG":label==="Rebounds"?"RPG":label==="Assists"?"APG":""}</small></div>
  </article>`
}

function renderTopPlayers(official){
  const wrap=qs("#top-players");
  const cards=[];
  const pog=official.playerOfGame||[];
  const leaders=official.leaders||[];
  if(pog[0])cards.push(playerCard(pog[0],1,"Player of Game",`${pog[0].pts} PTS`));
  leaders.forEach((x,i)=>cards.push(playerCard(x,i+2,x.category,x.value)));
  if(pog[1])cards.push(playerCard(pog[1],cards.length+1,"Player of Game",`${pog[1].pts} PTS`));
  wrap.innerHTML=cards.length?cards.join(""):'<div class="empty-card">No official player data is available.</div>';
}

function renderNews(official){
  const news=official.headlines||[];
  qs("#news").innerHTML=news.length?news.map(x=>`<a class="news-card" href="${safe(x.url||"https://pba.ph/")}" target="_blank" rel="noopener">
    <small>PBA Official</small><strong>${safe(x.title)}</strong>
  </a>`).join(""):'<div class="empty-card">No official PBA headlines available.</div>';
}

load();
})();