(()=>{
const qs=s=>document.querySelector(s);
const qsa=s=>[...document.querySelectorAll(s)];

const fmtDate=v=>{
  try{return new Date(v).toLocaleDateString(undefined,{month:"short",day:"numeric",year:"numeric"})}
  catch{return v||""}
};

const fmtTime=v=>{
  try{return new Date(v).toLocaleTimeString([],{hour:"numeric",minute:"2-digit"})}
  catch{return "—"}
};

const safe=v=>String(v??"");

async function getJSON(url,fallback={}){
  try{
    const res=await fetch(url+"?ts="+Date.now(),{cache:"no-store"});
    if(!res.ok)throw new Error(res.status);
    return await res.json();
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
  const pbaStreams=(yt.streams||[]).filter(x=>x.leagueKey==="pba"&&String(x.verificationStatus||x.stream?.verificationStatus||"")==="verified");

  if(assets.leagueLogo){
    const logo=qs("#pba-league-logo");
    if(logo)logo.src=assets.leagueLogo;
  }

  renderStatus({live,upcoming,finals,updated:regional.updated_at,pbaStreams});
  renderGames({live,upcoming,finals,assets});
  renderPrevious({finals,assets,official});
  renderHighlights({streams:pbaStreams,official});
  renderStandings({official,assets});
  renderPlayers(official);
  renderNews(official);
}

function renderStatus({live,upcoming,finals,updated,pbaStreams}){
  const next=upcoming[0];
  const liveText=pbaStreams[0]?.title||live[0]?.title||"No live game";

  qs("#status-live").textContent=liveText;
  qs("#status-next").textContent=next?(`${next.away} vs ${next.home}`):"No scheduled game";
  qs("#status-next-sub").textContent=next?(next.displayTime||fmtDate(next.date)):"";
  qs("#status-results").textContent=`${finals.length} available`;
  qs("#status-updated").textContent=updated?fmtTime(updated):"—";
  qs("#status-updated-sub").textContent=updated?fmtDate(updated):"";
}

function teamLogo(name,assets){
  return assets?.teams?.[name]||"";
}

function teamBlock(name,side,assets){
  const src=teamLogo(name,assets);
  return `
    <div class="game-team ${side==="right"?"right":""}">
      ${side==="right"?"":src?`<img class="team-logo" src="${src}" alt="${safe(name)} logo">`:""}
      <div>
        <div class="team-name">${safe(name)}</div>
        <div class="team-side">${side==="right"?"Home":"Away"}</div>
      </div>
      ${side==="right"&&src?`<img class="team-logo" src="${src}" alt="${safe(name)} logo">`:""}
    </div>`;
}

function renderGames({live,upcoming,finals,assets}){
  const sets={live,upcoming,results:finals};
  const slot=qs("#game-slot");

  const paint=key=>{
    const g=(sets[key]||[])[0];
    qsa(".tab-btn").forEach(btn=>btn.classList.toggle("active",btn.dataset.tab===key));

    if(!g){
      slot.innerHTML=`<div class="empty-card">No verified PBA game is available for this tab.</div>`;
      return;
    }

    const final=g.state==="final";
    const middle=final
      ?`<strong class="score">${safe(g.awayScore)} — ${safe(g.homeScore)}</strong><div class="vs-pill">Final</div>`
      :`<strong>${safe(g.displayTime||fmtDate(g.date))}</strong><div class="vs-pill">vs</div><div>${safe(g.location||g.status||"")}</div>`;

    slot.innerHTML=`
      <article class="featured-game">
        ${teamBlock(g.away||"Away","left",assets)}
        <div class="game-center">${middle}</div>
        ${teamBlock(g.home||"Home","right",assets)}
      </article>`;
  };

  qsa(".tab-btn").forEach(btn=>btn.addEventListener("click",()=>paint(btn.dataset.tab)));
  paint(live.length?"live":upcoming.length?"upcoming":"results");
}

function galleryImage(g,official){
  const map=official?.gameImages||{};
  return map[g.eventId]||g.image||"";
}

function renderPrevious({finals,assets,official}){
  const wrap=qs("#previous-games");
  if(!finals.length){
    wrap.innerHTML=`<div class="empty-card">No recent verified PBA results available.</div>`;
    return;
  }

  wrap.innerHTML=finals.slice(0,8).map(g=>{
    const img=galleryImage(g,official);
    const a=teamLogo(g.away,assets);
    const h=teamLogo(g.home,assets);

    return `
      <article class="media-card">
        ${img?`<img class="media-bg" src="${img}" alt="${safe(g.away)} vs ${safe(g.home)}">`:`
          <div class="logo-pair">
            ${a?`<img src="${a}" alt="${safe(g.away)} logo">`:""}
            ${h?`<img src="${h}" alt="${safe(g.home)} logo">`:""}
          </div>`}
        <div class="media-card-content">
          <div class="media-kicker">PBA · Final</div>
          <div class="media-title">${safe(g.away)} ${safe(g.awayScore)} — ${safe(g.homeScore)} ${safe(g.home)}</div>
          <div class="media-meta">${safe(g.displayTime||fmtDate(g.date))}</div>
        </div>
      </article>`;
  }).join("");
}

function renderHighlights({streams,official}){
  const wrap=qs("#highlights");
  const highlights=Array.isArray(official?.highlights)?official.highlights:[];

  if(highlights.length){
    wrap.innerHTML=highlights.slice(0,8).map(x=>`
      <a class="media-card highlight-card" href="${safe(x.url||"#")}" target="_blank" rel="noopener">
        ${x.thumbnail?`<img class="media-bg" src="${x.thumbnail}" alt="${safe(x.title)}">`:""}
        <div class="play-button">▶</div>
        <div class="media-card-content">
          <div class="media-kicker">${safe(x.source||"PBA")}</div>
          <div class="media-title">${safe(x.title)}</div>
          <div class="media-meta">${safe(x.duration||x.meta||"Highlight")}</div>
        </div>
      </a>`).join("");
    return;
  }

  if(streams.length){
    wrap.innerHTML=streams.slice(0,8).map(x=>`
      <a class="media-card highlight-card" href="${safe(x.stream?.watchUrl)}" target="_blank" rel="noopener">
        <div class="play-button">▶</div>
        <div class="media-card-content">
          <div class="media-kicker">${safe(x.stream?.channel||"PBA")}</div>
          <div class="media-title">${safe(x.title||x.stream?.title)}</div>
          <div class="media-meta">Verified live video</div>
        </div>
      </a>`).join("");
    return;
  }

  wrap.innerHTML=`<div class="empty-card">No verified PBA highlight or live video is available right now.</div>`;
}

function renderStandings({official,assets}){
  const rows=list=>(list||[]).map((x,i)=>{
    const logo=teamLogo(x.team,assets);
    return `<tr>
      <td>${i+1}</td>
      <td><div class="standing-team">${logo?`<img src="${logo}" alt="${safe(x.team)} logo">`:""}<span>${safe(x.team)}</span></div></td>
      <td>${safe(x.wins)}</td>
      <td>${safe(x.losses)}</td>
    </tr>`;
  }).join("");

  qs("#group-a").innerHTML=rows(official?.rankings?.groupA);
  qs("#group-b").innerHTML=rows(official?.rankings?.groupB);
}

function photoBlock(x){
  const name=safe(x?.player||"Player");
  if(x?.photo)return `<div class="player-photo"><img src="${x.photo}" alt="${name} photo"></div>`;
  const initials=name.split(/\s+/).map(n=>n[0]).join("").slice(0,3).toUpperCase();
  return `<div class="player-photo fallback">${initials}</div>`;
}

function renderPlayers(official){
  const pog=official?.playerOfGame||[];
  const leaders=official?.leaders||[];

  qs("#players").innerHTML=pog.length?pog.map(x=>`
    <div class="player-card">
      ${photoBlock(x)}
      <div class="player-copy">
        <span>${safe(x.matchup)} · ${fmtDate(x.date)}</span>
        <strong>${safe(x.player)}</strong>
        <b>${safe(x.pts)} PTS · ${safe(x.reb)} REB · ${safe(x.ast)} AST</b>
      </div>
    </div>`).join(""):`<div class="empty-card">No official Player of the Game data available.</div>`;

  qs("#leaders").innerHTML=leaders.length?leaders.map(x=>`
    <div class="player-card">
      ${photoBlock(x)}
      <div class="player-copy">
        <span>${safe(x.category)}</span>
        <strong>${safe(x.player)}</strong>
        <b>${safe(x.value)}</b>
      </div>
    </div>`).join(""):`<div class="empty-card">No official leader data available.</div>`;
}

function renderNews(official){
  const news=official?.headlines||[];
  qs("#news").innerHTML=news.length?news.map(x=>`
    <a class="news-card" href="${safe(x.url||"https://pba.ph/")}" target="_blank" rel="noopener">
      <small>PBA Official</small>
      <strong>${safe(x.title)}</strong>
    </a>`).join(""):`<div class="empty-card">No official PBA headlines available.</div>`;
}

load();
})();