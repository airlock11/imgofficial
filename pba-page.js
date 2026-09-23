(()=>{
const qs=s=>document.querySelector(s);
const qsa=s=>[...document.querySelectorAll(s)];
const safe=v=>String(v??"");
const fmtDate=v=>{try{return new Date(v).toLocaleDateString(undefined,{month:"short",day:"numeric",year:"numeric"})}catch{return v||""}};
const fmtTime=v=>{try{return new Date(v).toLocaleTimeString([],{hour:"numeric",minute:"2-digit"})}catch{return "—"}};

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

  const hero=qs("#pba-hero");
  if(hero)hero.style.setProperty("--hero-image",`url("/assets/pba/pba-hero-hq-v4.webp?v=20260923-1852")`);

  const logo=qs("#pba-league-logo");
  if(logo&&assets.leagueLogo)logo.src=assets.leagueLogo;

  renderStatus({live,upcoming,finals,updated:regional.updated_at,streams});
  renderGames({live,upcoming,finals,assets});
  renderGallery({finals,assets,official});
  renderHighlights({streams,official});
  renderStandings({official,assets});
  renderTopPlayers(official);
  renderNews(official);
}

function renderStatus({live,upcoming,finals,updated,streams}){
  const next=upcoming[0];
  qs("#status-live").textContent=streams[0]?.title||live[0]?.title||"No live game";
  qs("#status-next").textContent=next?`${next.away} vs ${next.home}`:"No scheduled game";
  qs("#status-next-sub").textContent=next?(next.displayTime||fmtDate(next.date)):"";
  qs("#status-results").textContent=`${finals.length} available`;
  qs("#status-updated").textContent=updated?fmtTime(updated):"—";
  qs("#status-updated-sub").textContent=updated?fmtDate(updated):"";
}

function teamLogo(name,assets){return assets?.teams?.[name]||""}

function teamBlock(name,side,assets){
  const src=teamLogo(name,assets);
  return `<div class="game-team ${side==="right"?"right":""}">
    ${side!=="right"&&src?`<img class="team-logo" src="${src}" alt="${safe(name)} logo">`:""}
    <div><div class="team-name">${safe(name)}</div><div class="team-side">${side==="right"?"Home":"Away"}</div></div>
    ${side==="right"&&src?`<img class="team-logo" src="${src}" alt="${safe(name)} logo">`:""}
  </div>`
}

function renderGames({live,upcoming,finals,assets}){
  const groups={live,upcoming,results:finals};
  const slot=qs("#game-slot");
  const paint=key=>{
    const g=(groups[key]||[])[0];
    qsa(".tab-btn").forEach(b=>b.classList.toggle("active",b.dataset.tab===key));
    if(!g){
      slot.innerHTML='<div class="empty-card">No verified PBA game is available for this tab.</div>';
      return;
    }
    const final=g.state==="final";
    const mid=final
      ?`<strong class="score">${safe(g.awayScore)} — ${safe(g.homeScore)}</strong><div class="vs-pill">FINAL</div>`
      :`<strong>${safe(g.displayTime||fmtDate(g.date))}</strong><div class="vs-pill">VS</div><div>${safe(g.location||g.status||"Scheduled")}</div>`;
    slot.innerHTML=`<article class="featured-game">
      ${teamBlock(g.away||"Away","left",assets)}
      <div class="game-center">${mid}</div>
      ${teamBlock(g.home||"Home","right",assets)}
    </article>`;
  };
  qsa(".tab-btn").forEach(b=>b.addEventListener("click",()=>paint(b.dataset.tab)));
  paint(live.length?"live":upcoming.length?"upcoming":"results");
}

function renderGallery({finals,assets,official}){
  const wrap=qs("#previous-games");
  const media=Array.isArray(official.mediaGallery)?official.mediaGallery:[];
  const cards=[];

  finals.forEach((g,i)=>{
    const photo=media[i%Math.max(media.length,1)]?.image||"";
    const a=teamLogo(g.away,assets),h=teamLogo(g.home,assets);
    cards.push(`<article class="media-card">
      ${photo?`<img class="media-bg" src="${photo}" alt="PBA action">`:`<div class="logo-pair">${a?`<img src="${a}" alt="">`:""}${h?`<img src="${h}" alt="">`:""}</div>`}
      <div class="media-card-content">
        <div class="media-kicker">PBA · Final</div>
        <div class="media-title">${safe(g.away)} ${safe(g.awayScore)} — ${safe(g.homeScore)} ${safe(g.home)}</div>
        <div class="media-meta">${safe(g.displayTime||fmtDate(g.date))}</div>
      </div>
    </article>`);
  });

  media.slice(finals.length).forEach(x=>{
    cards.push(`<a class="media-card" href="${safe(x.url||"https://pba.ph/")}" target="_blank" rel="noopener">
      <img class="media-bg" src="${safe(x.image)}" alt="${safe(x.title)}">
      <div class="media-card-content">
        <div class="media-kicker">${safe(x.source||"PBA Official")}</div>
        <div class="media-title">${safe(x.title)}</div>
        <div class="media-meta">Official PBA media</div>
      </div>
    </a>`);
  });

  wrap.innerHTML=cards.length?cards.join(""):'<div class="empty-card">No recent verified PBA media is available.</div>';
}

function renderHighlights({streams,official}){
  const wrap=qs("#highlights");
  const items=[];
  const features=Array.isArray(official.highlights)?official.highlights:[];

  streams.forEach(x=>items.push(`<a class="media-card highlight-card" href="${safe(x.stream?.watchUrl)}" target="_blank" rel="noopener">
    <div class="play-button">▶</div>
    <div class="media-card-content">
      <div class="media-kicker">${safe(x.stream?.channel||"PBA")}</div>
      <div class="media-title">${safe(x.title||x.stream?.title)}</div>
      <div class="media-meta">Verified live video</div>
    </div>
  </a>`));

  features.forEach(x=>items.push(`<a class="media-card highlight-card" href="${safe(x.url||"https://pba.ph/")}" target="_blank" rel="noopener">
    ${x.thumbnail?`<img class="media-bg" src="${safe(x.thumbnail)}" alt="${safe(x.title)}">`:""}
    <div class="media-card-content">
      <div class="media-kicker">${safe(x.source||"PBA Official")}</div>
      <div class="media-title">${safe(x.title)}</div>
      <div class="media-meta">${safe(x.meta||"Official PBA feature")}</div>
    </div>
  </a>`));

  wrap.innerHTML=items.length?items.slice(0,8).join(""):'<div class="empty-card">No verified PBA highlight or live video is available right now.</div>';
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