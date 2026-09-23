(()=>{
const qs=s=>document.querySelector(s),qsa=s=>[...document.querySelectorAll(s)];
const fmtDate=v=>{try{return new Date(v).toLocaleDateString(undefined,{month:"short",day:"numeric",year:"numeric"})}catch{return v||""}};
const short=n=>String(n||"").split(/\s+/).map(x=>x[0]).join("").slice(0,3).toUpperCase();

async function load(){
 let regional={},official={},yt={},assets={teams:{}};
 try{regional=await fetch("/regional-web.json?ts="+Date.now(),{cache:"no-store"}).then(r=>r.json())}catch{}
 try{official=await fetch("/pba-official.json?ts="+Date.now(),{cache:"no-store"}).then(r=>r.json())}catch{}
 try{yt=await fetch("/youtube-live.json?ts="+Date.now(),{cache:"no-store"}).then(r=>r.json())}catch{}
 try{assets=await fetch("/pba-assets.json?ts="+Date.now(),{cache:"no-store"}).then(r=>r.json())}catch{}
 const league=regional&&regional.leagues&&regional.leagues.pba?regional.leagues.pba:{};
 const games=Array.isArray(league.games)?league.games:[];
 const live=games.filter(g=>g.state==="in"||String(g.status||"").toLowerCase().includes("live"));
 const upcoming=games.filter(g=>g.state==="scheduled").sort((a,b)=>new Date(a.date)-new Date(b.date));
 const finals=games.filter(g=>g.state==="final").sort((a,b)=>new Date(b.date)-new Date(a.date));
 const pbaStreams=(yt.streams||[]).filter(x=>x.leagueKey==="pba"&&String(x.verificationStatus||(x.stream&&x.stream.verificationStatus)||"")==="verified");
 renderStatus(live,upcoming,finals,regional.updated_at,pbaStreams);
 renderGames(live,upcoming,finals,assets);
 renderPrevious(finals,assets);
 renderHighlights(pbaStreams);
 renderOfficial(official,assets);
 renderLeagueLogo(assets);
}
function renderStatus(live,upcoming,finals,updated,pbaStreams){
 const liveText=(pbaStreams[0]&&pbaStreams[0].title)||(live[0]&&live[0].title)||"No live game";
 const next=upcoming[0];
 qs("#status-live").textContent=liveText;
 qs("#status-next").textContent=next?(next.away+" vs "+next.home):"No scheduled game";
 qs("#status-next-sub").textContent=next?(next.displayTime||fmtDate(next.date)):"";
 qs("#status-results").textContent=finals.length+" available";
 qs("#status-source").textContent="PBA";
 qs("#status-updated").textContent=updated?new Date(updated).toLocaleTimeString([], {hour:"numeric",minute:"2-digit"}):"—";
 qs("#status-updated-sub").textContent=updated?fmtDate(updated):"";
}
function logoFor(name,assets){return assets&&assets.teams&&assets.teams[name]?assets.teams[name]:""}
function badge(name,assets){
 const src=logoFor(name,assets);
 return src?'<div class="team-badge image"><img src="'+src+'" alt="'+name+' logo" loading="lazy"></div>':'<div class="team-badge">'+short(name)+'</div>';
}
function gameCard(g,assets){
 if(!g)return '<div class="empty">No verified game available for this tab.</div>';
 const a=g.away||"Away",h=g.home||"Home",isFinal=g.state==="final";
 const center=isFinal
  ?'<strong class="score">'+g.awayScore+' — '+g.homeScore+'</strong><span>Final</span>'
  :'<strong>'+(g.displayTime||fmtDate(g.date))+'</strong><span>'+(g.location||g.status||"")+'</span>';
 return '<div class="game-feature">'+
 '<div class="team">'+badge(a,assets)+'<div><div class="team-name">'+a+'</div><div class="status-sub">'+(isFinal?"Final score":"Away")+'</div></div></div>'+
 '<div class="game-center">'+center+'</div>'+
 '<div class="team right"><div><div class="team-name">'+h+'</div><div class="status-sub">'+(isFinal?"Final score":"Home")+'</div></div>'+badge(h,assets)+'</div>'+
 '</div>';
}
function renderGames(live,upcoming,finals,assets){
 const map={live:live,upcoming:upcoming,results:finals};
 const target=qs("#game-slot");
 const paint=k=>{target.innerHTML=gameCard((map[k]||[])[0],assets);qsa(".tab").forEach(b=>b.classList.toggle("active",b.dataset.tab===k))};
 qsa(".tab").forEach(b=>b.onclick=()=>paint(b.dataset.tab));
 paint(live.length?"live":upcoming.length?"upcoming":"results");
}
function renderPrevious(finals,assets){
 const wrap=qs("#previous-games");
 if(!finals.length){wrap.innerHTML='<div class="empty">No recent verified PBA results available.</div>';return}
 wrap.innerHTML=finals.slice(0,8).map(g=>'<article class="media-card game-gallery-card"><div class="gallery-logos">'+(logoFor(g.away,assets)?'<img src="'+logoFor(g.away,assets)+'" alt="'+g.away+' logo">':'')+(logoFor(g.home,assets)?'<img src="'+logoFor(g.home,assets)+'" alt="'+g.home+' logo">':'')+'</div><div class="media-content"><div class="media-kicker">PBA · Final</div><div class="media-title">'+g.away+' '+g.awayScore+' — '+g.homeScore+' '+g.home+'</div><div class="media-meta">'+(g.displayTime||fmtDate(g.date))+'</div></div></article>').join("");
}
function renderHighlights(streams){
 const wrap=qs("#highlights");
 if(!streams.length){wrap.innerHTML='<div class="empty">No verified PBA highlight or live video is available right now.</div>';return}
 wrap.innerHTML=streams.slice(0,8).map(x=>'<a class="media-card" href="'+x.stream.watchUrl+'" target="_blank" rel="noopener"><div class="play">▶</div><div class="media-content"><div class="media-kicker">'+(x.stream.channel||"PBA")+'</div><div class="media-title">'+(x.title||x.stream.title)+'</div><div class="media-meta">Verified live source</div></div></a>').join("");
}
function rows(list,assets){return (list||[]).map((x,i)=>'<tr><td>'+(i+1)+'</td><td><div class="standing-team">'+(logoFor(x.team,assets)?'<img src="'+logoFor(x.team,assets)+'" alt="'+x.team+' logo" loading="lazy">':'')+'<span>'+x.team+'</span></div></td><td>'+x.wins+'</td><td>'+x.losses+'</td></tr>').join("")}
function renderOfficial(o,assets){
 o=o||{};
 qs("#group-a").innerHTML=rows(o.rankings&&o.rankings.groupA,assets);
 qs("#group-b").innerHTML=rows(o.rankings&&o.rankings.groupB,assets);
 const leaders=o.leaders||[];
 qs("#leaders").innerHTML=leaders.length?leaders.map(x=>'<div class="leader"><span>'+x.category+'</span><strong>'+x.player+'<br>'+x.value+'</strong></div>').join(""):'<div class="empty">No official leader data available.</div>';
 const pog=o.playerOfGame||[];
 qs("#players").innerHTML=pog.length?pog.map(x=>'<div class="leader"><span>'+x.matchup+'<br>'+fmtDate(x.date)+'</span><strong>'+x.player+'<br>'+x.pts+' PTS · '+x.reb+' REB · '+x.ast+' AST</strong></div>').join(""):'<div class="empty">No player data available.</div>';
 const news=o.headlines||[];
 qs("#news").innerHTML=news.length?news.map(x=>'<a class="news-item" href="'+x.url+'" target="_blank" rel="noopener"><small>PBA Official</small><strong>'+x.title+'</strong></a>').join(""):'<div class="empty">No official PBA headlines available.</div>';
}
function renderLeagueLogo(assets){
 const img=qs("#pba-league-logo");
 if(img&&assets&&assets.leagueLogo)img.src=assets.leagueLogo;
}
load();
})();