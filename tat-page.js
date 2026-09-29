(()=>{
const qs=s=>document.querySelector(s);
const qsa=s=>[...document.querySelectorAll(s)];
const safe=v=>String(v??"");
const fmtDate=v=>{try{return new Date(v).toLocaleDateString(undefined,{month:"short",day:"numeric",year:"numeric"})}catch{return v||""}};

async function getJSON(url,fallback={}){
  try{
    const r=await fetch(url+(url.includes("?")?"&":"?")+"ts="+Date.now(),{cache:"no-store"});
    if(!r.ok)throw new Error(r.status);
    return await r.json();
  }catch{return fallback}
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
  </div>`;
}

function renderGames({games,assets}){
  const live=games.filter(g=>g.state==="live"||g.state==="in"||/live/i.test(g.status||""));
  const upcoming=games.filter(g=>g.state==="scheduled").sort((a,b)=>new Date(a.date)-new Date(b.date));
  const finals=games.filter(g=>g.state==="final").sort((a,b)=>new Date(b.date)-new Date(a.date));
  const groups={live,upcoming,results:finals};
  const slot=qs("#game-slot");
  let active=live.length?"live":upcoming.length?"upcoming":"results";

  const paint=key=>{
    active=key;
    qsa(".tab-btn").forEach(b=>b.classList.toggle("active",b.dataset.tab===key));
    const g=(groups[key]||[])[0];
    if(!g){
      const msg=key==="upcoming"
        ?"TAT has not published a verified matchup for the next 2026 leg yet."
        :key==="live"
          ?"No verified TAT game is live right now."
          :"No verified TAT result is available.";
      slot.innerHTML=`<div class="empty-card">${msg}</div>`;
      return;
    }
    const final=g.state==="final";
    const liveGame=g.state==="live"||g.state==="in"||/live/i.test(g.status||"");
    const showScore=final||liveGame;
    const center=final?"FINAL":liveGame?"LIVE":safe(g.displayTime||fmtDate(g.date));
    slot.innerHTML=`<article class="featured-game" data-event-id="${safe(g.eventId)}">
      ${teamBlock(g.away||"Away","left",assets,showScore?g.awayScore:"")}
      <div class="game-center"><div class="game-status">${center}</div></div>
      ${teamBlock(g.home||"Home","right",assets,showScore?g.homeScore:"")}
    </article>`;
  };
  qsa(".tab-btn").forEach(b=>b.addEventListener("click",()=>paint(b.dataset.tab)));
  paint(active);
  return finals;
}

function renderGallery({finals,official,assets}){
  const wrap=qs("#previous-games");
  const photos=Array.isArray(official.previousGamePhotos)?official.previousGamePhotos:[];
  const cards=(finals||[]).slice(0,3).map((g,i)=>{
    const a=teamLogo(g.away,assets),h=teamLogo(g.home,assets);
    const photo=photos[i];
    return `<article class="media-card">
      ${photo?.image?`<img class="media-bg" src="${safe(photo.image)}" alt="${safe(g.away)} vs ${safe(g.home)} TAT game image" loading="lazy" decoding="async">`:`<div class="logo-pair">${a?`<img src="${a}" alt="">`:""}${h?`<img src="${h}" alt="">`:""}</div>`}
      <div class="media-card-content">
        <div class="media-kicker">TAT · Final</div>
        <div class="media-title">${safe(g.away)} ${safe(g.awayScore)} — ${safe(g.homeScore)} ${safe(g.home)}</div>
        <div class="media-meta">${safe(g.displayTime||fmtDate(g.date))}</div>
      </div>
    </article>`;
  });
  wrap.innerHTML=cards.length?cards.join(""):'<div class="empty-card">No recent verified TAT games are available.</div>';
}

function renderHighlights({official,streams}){
  const wrap=qs("#highlights");
  const officialVideos=Array.isArray(official.highlights)?official.highlights.map(x=>({...x,isLive:false})):[];
  const liveVideos=(streams||[]).map(x=>({
    id:x.stream?.videoId||x.videoId||"",
    title:x.title||"TAT live stream",
    watchUrl:x.stream?.watchUrl||x.watchUrl||"",
    thumbnail:x.stream?.thumbnail||x.thumbnail||"",
    source:"The Asian Tournament",
    isLive:true
  }));
  const seen=new Set();
  const items=[...liveVideos,...officialVideos].filter(x=>{
    const k=x.id||x.watchUrl||x.title;
    if(!k||seen.has(k))return false;
    seen.add(k); return true;
  }).slice(0,10);

  if(!items.length){
    wrap.innerHTML='<div class="empty-card">Official TAT video coverage will appear here when available.</div>';
    return;
  }

  wrap.innerHTML=items.map((x,index)=>`<article class="reel-card">
    <div class="reel-media" role="button" tabindex="0" data-tat-video="${safe(x.id)}" data-index="${index}" aria-label="Play ${safe(x.title)} inside IMG">
      <img class="reel-thumb" src="${safe(x.thumbnail||(`https://i.ytimg.com/vi/${x.id}/maxresdefault.jpg`))}" alt="${safe(x.title)}" loading="lazy" decoding="async"
        onerror="if(this.dataset.fallback!=='1'){this.dataset.fallback='1';this.src='https://i.ytimg.com/vi/${safe(x.id)}/hqdefault.jpg'}">
      <span class="reel-shade"></span>
      <span class="reel-play" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span>
      <span class="reel-source">${x.isLive?"LIVE":"TAT VIDEO"}</span>
    </div>
    <div class="reel-caption"><strong>${safe(x.title)}</strong><span>${safe(x.source||"The Asian Tournament")}</span></div>
  </article>`).join("");

  const stages=qsa("#highlights .reel-media");
  const stopStage=stage=>{
    const frame=stage.querySelector(".reel-frame");
    if(frame)frame.remove();
    stage.classList.remove("is-playing");
    stage.setAttribute("role","button");
    stage.tabIndex=0;
  };
  const playStage=stage=>{
    if(!stage||stage.classList.contains("is-playing"))return;
    const id=safe(stage.dataset.tatVideo).trim();
    if(!id)return;
    stages.forEach(other=>{if(other!==stage)stopStage(other)});
    const frame=document.createElement("iframe");
    frame.className="reel-frame";
    frame.src=`https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?autoplay=1&playsinline=1&rel=0&modestbranding=1`;
    frame.title=stage.getAttribute("aria-label")||"TAT video";
    frame.allow="autoplay; encrypted-media; picture-in-picture; web-share";
    frame.allowFullscreen=true;
    frame.referrerPolicy="strict-origin-when-cross-origin";
    stage.appendChild(frame);
    stage.classList.add("is-playing");
    stage.removeAttribute("role");
    stage.removeAttribute("tabindex");
  };
  stages.forEach(stage=>{
    stage.addEventListener("click",()=>playStage(stage));
    stage.addEventListener("keydown",e=>{
      if(e.key==="Enter"||e.key===" "){
        e.preventDefault();
        playStage(stage);
      }
    });
  });
}
function renderCompetition({official,assets}){
  const teamRows=(official.teams||[]).map((x,i)=>{
    const logo=teamLogo(x.team,assets);
    return `<tr>
      <td>${i+1}</td>
      <td><div class="standing-team">${logo?`<img src="${logo}" alt="${safe(x.team)} logo">`:""}<span>${safe(x.team)}</span></div></td>
      <td>${safe(x.country)}</td><td>${safe(x.legs)}</td>
    </tr>`;
  }).join("");
  const legRows=(official.legs||[]).map((x,i)=>`<tr>
    <td>${i+1}</td><td><div class="standing-team"><span>${safe(x.leg)}</span></div></td><td>${safe(x.dates)}</td><td>${safe(x.status)}</td>
  </tr>`).join("");
  qs("#group-a").innerHTML=teamRows||'<tr><td colspan="4">No verified TAT teams available.</td></tr>';
  qs("#group-b").innerHTML=legRows||'<tr><td colspan="4">No verified TAT legs available.</td></tr>';
}

function initials(name){return safe(name).split(/\s+/).map(x=>x[0]).join("").slice(0,3).toUpperCase()}

function renderPlayers(official){
  const rows=Array.isArray(official.playersToWatch)?official.playersToWatch:[];
  qs("#top-players").innerHTML=rows.length?rows.map((x,i)=>`<article class="top-player-card">
    <div class="top-player-rank">${i+1}</div>
    <div class="top-player-fallback">${initials(x.player)}</div>
    <div class="top-player-label">Player to Watch</div>
    <div class="top-player-name">${safe(x.player)}</div>
    <div class="top-player-value" style="font-size:1rem;line-height:1.15">${safe(x.team)}</div>
  </article>`).join(""):'<div class="empty-card">No official TAT player features are available.</div>';
}

function renderNews(official){
  const news=Array.isArray(official.headlines)?official.headlines:[];
  qs("#news").innerHTML=news.length?news.slice(0,6).map(x=>{
    const published=x.published?new Date(x.published):null;
    const date=published&&!Number.isNaN(published.getTime())?published.toLocaleDateString(undefined,{month:"short",day:"numeric"}):"";
    return `<a class="news-card" href="${safe(x.url||"https://www.theasiantournament.com/news")}" target="_blank" rel="noopener">
      <span class="news-copy"><small>${safe(x.sourceName||"The Asian Tournament")}${date?` · ${date}`:""}</small><strong>${safe(x.title)}</strong></span>
    </a>`;
  }).join(""):'<div class="empty-card">No official TAT headlines available.</div>';
}

async function load(){
  const [official,assets,yt]=await Promise.all([
    getJSON("/tat-official.json",{}),
    getJSON("/tat-assets.json",{teams:{}}),
    getJSON("/youtube-live.json",{})
  ]);
  const logo=qs("#tat-league-logo");
  if(logo&&assets.leagueLogo)logo.src=assets.leagueLogo;
  const games=Array.isArray(official.games)?official.games:[];
  const finals=renderGames({games,assets});
  const streams=(yt.streams||[]).filter(x=>
    String(x.leagueKey||x.delivery?.leagueKey||x.stream?.deliveryLeagueKey||"")==="tat" &&
    String(x.verificationStatus||x.stream?.verificationStatus||"")==="verified"
  );
  renderGallery({finals,official,assets});
  renderHighlights({official,streams});
  renderCompetition({official,assets});
  renderPlayers(official);
  renderNews(official);
}

load();
})();