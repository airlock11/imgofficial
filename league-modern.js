(()=>{'use strict';
const slug=location.pathname.split('/').filter(Boolean).pop()||'';
const feeds={
 'nba':{name:'NBA',key:'basketball',score:'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard',stand:'https://site.api.espn.com/apis/v2/sports/basketball/nba/standings?region=us&lang=en',news:'NBA'},
 'wnba':{name:'WNBA',key:'wnba',score:'https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard',stand:'https://site.api.espn.com/apis/v2/sports/basketball/wnba/standings?region=us&lang=en',news:'WNBA'},
 'pba':{name:'PBA',key:'pba',regional:true,news:'PBA|Philippine Basketball Association'},
 'mpbl':{name:'MPBL',key:'mpbl',regional:true,news:'MPBL|Maharlika Pilipinas Basketball League'},
 'nbl-pilipinas':{name:'NBL-Pilipinas',key:'nbl',regional:true,news:'NBL-Pilipinas|NBL Pilipinas'},
 'nbl-australia':{name:'NBL Australia',key:'nblaus',regional:true,news:'NBL Australia|National Basketball League'},
 'vba':{name:'VBA',key:'vba',regional:true,news:'Vietnam Basketball Association|VBA'},
 'b-league':{name:'B.League',key:'bleague',local:true,news:'B\\.League|B League'},
 'euroleague':{name:'EuroLeague',key:'euroleague',local:true,news:'EuroLeague'},
 'uaap':{name:'UAAP',key:'uaap',local:true,news:'UAAP'},
 'ncaa-philippines':{name:'NCAA Philippines',key:'ncaa_ph',local:true,news:'NCAA Philippines|NCAA Season'},
 'premier-league':{name:'Premier League',key:'soccer',score:'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard',stand:'https://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings?region=us&lang=en',news:'Premier League'},
 'la-liga':{name:'La Liga',key:'laliga',score:'https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard',stand:'https://site.api.espn.com/apis/v2/sports/soccer/esp.1/standings?region=us&lang=en',news:'La Liga'},
 'serie-a':{name:'Serie A',key:'seriea',score:'https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard',stand:'https://site.api.espn.com/apis/v2/sports/soccer/ita.1/standings?region=us&lang=en',news:'Serie A'},
 'bundesliga':{name:'Bundesliga',key:'bundesliga',score:'https://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/scoreboard',stand:'https://site.api.espn.com/apis/v2/sports/soccer/ger.1/standings?region=us&lang=en',news:'Bundesliga'},
 'champions-league':{name:'UEFA Champions League',key:'champions',score:'https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard',stand:'https://site.api.espn.com/apis/v2/sports/soccer/uefa.champions/standings?region=us&lang=en',news:'Champions League'},
 'mls':{name:'MLS',key:'mls',score:'https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/scoreboard',stand:'https://site.api.espn.com/apis/v2/sports/soccer/usa.1/standings?region=us&lang=en',news:'MLS|Major League Soccer'},
 'atp':{name:'ATP Tour',key:'atp',score:'https://site.api.espn.com/apis/site/v2/sports/tennis/atp/scoreboard',news:'ATP'},
 'wta':{name:'WTA Tour',key:'wta',score:'https://site.api.espn.com/apis/site/v2/sports/tennis/wta/scoreboard',news:'WTA'},
 'ipl':{name:'IPL',key:'ipl',score:'https://site.api.espn.com/apis/site/v2/sports/cricket/ipl/scoreboard',news:'IPL|Indian Premier League'},
 'mlb':{name:'MLB',key:'baseball',score:'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard',stand:'https://site.api.espn.com/apis/v2/sports/baseball/mlb/standings?region=us&lang=en',news:'MLB|Major League Baseball'},
 'nhl':{name:'NHL',key:'hockey',score:'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard',stand:'https://site.api.espn.com/apis/v2/sports/hockey/nhl/standings?region=us&lang=en',news:'NHL'},
 'nfl':{name:'NFL',key:'football',score:'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard',stand:'https://site.api.espn.com/apis/v2/sports/football/nfl/standings?region=us&lang=en',news:'NFL'},
 'formula-1':{name:'Formula 1',key:'f1',score:'https://site.api.espn.com/apis/site/v2/sports/racing/f1/scoreboard',news:'Formula 1|F1'},
 'ufc':{name:'UFC',key:'ufc',score:'https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard',news:'UFC'}
};
const cfg=feeds[slug];if(!cfg)return;
const worker='https://img-api-proxy.magsipocarnie.workers.dev';
const q=s=>document.querySelector(s), esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dt=v=>{const d=new Date(v);return Number.isNaN(d.getTime())?'':new Intl.DateTimeFormat(undefined,{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}).format(d)};
const dateKey=d=>{const x=new Date(d),y=x.getUTCFullYear(),m=String(x.getUTCMonth()+1).padStart(2,'0'),z=String(x.getUTCDate()).padStart(2,'0');return ''+y+m+z};
const saved=localStorage.getItem('img-theme');document.documentElement.dataset.theme=saved||((matchMedia('(prefers-color-scheme: light)').matches)?'light':'dark');
const nav=q('header nav');if(nav&&!q('.img-theme-toggle')){const b=document.createElement('button');b.className='img-theme-toggle';b.type='button';b.setAttribute('aria-label','Switch color theme');b.innerHTML='<svg viewBox="0 0 24 24"><path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5 8.5 8.5 0 1 0 20.5 14.2Z"/></svg>';b.onclick=()=>{const n=document.documentElement.dataset.theme==='light'?'dark':'light';document.documentElement.dataset.theme=n;localStorage.setItem('img-theme',n)};nav.append(b)}
q('.league-data')?.remove();
const content=q('main .content');if(content)content.classList.add('img-reveal');
const hero=q('.hero');if(!hero)return;
const app=document.createElement('section');app.className='img-league-app';app.id='imgLeagueApp';app.innerHTML='<div class="shell">'+
'<div class="img-livebar"><div class="img-livebar-left"><span class="img-pulse"></span><div><strong>IMG Auto Update</strong> <span id="imgUpdateText">Connecting to verified sources…</span></div></div><div class="img-livebar-links"><a href="/scores/?from=league&league='+encodeURIComponent(cfg.key)+'">Full scores</a><a href="/news/">News</a></div></div>'+
'<div class="img-kpis" id="imgKpis"></div>'+
'<div class="img-dashboard"><div class="img-stack"><section class="img-panel img-reveal" id="imgGamesPanel" hidden><div class="img-panel-head"><div><h2>Games</h2><p>Live, upcoming and recent results</p></div><button class="img-panel-action" id="imgGamesMode" type="button">Upcoming</button></div><div class="img-game-strip" id="imgGames"></div></section>'+
'<section class="img-panel img-reveal" id="imgHistoryPanel"><div class="img-panel-head"><div><h2>Previous games gallery</h2><p>Swipe through verified final results</p></div><div class="img-history-controls"><button type="button" id="imgHistoryPrev" aria-label="Previous games">‹</button><button type="button" id="imgHistoryNext" aria-label="Next games">›</button></div></div><div class="img-history-rail" id="imgHistory"></div></section>'+
'<section class="img-panel img-reveal" id="imgHighlightsPanel" hidden><div class="img-panel-head"><div><h2>Highlights</h2><p>Verified clips · swipe like Reels</p></div><span class="img-panel-action">Auto refreshed</span></div><div class="img-reels"><div class="img-reel-rail" id="imgReels"></div></div></section>'+
'<section class="img-panel img-reveal" id="imgStandingsPanel" hidden><div class="img-panel-head"><div><h2>Standings</h2><p>Current table from connected data</p></div></div><div class="img-standings" id="imgStandings"></div></section></div>'+
'<aside class="img-stack"><section class="img-panel img-reveal" id="imgNewsPanel" hidden><div class="img-panel-head"><div><h2>Latest '+esc(cfg.name)+' news</h2><p>From IMG news sources</p></div></div><div class="img-news-list" id="imgNews"></div></section></aside></div></div>';
hero.insertAdjacentElement('afterend',app);

let lastEvents=[],modes=[],modeIndex=0,lastSource='IMG';
function stateOf(e){const t=e?.status?.type||{},s=String(t.state||t.name||t.description||e?.state||'').toLowerCase();if(/(^|\b)(in|live|progress)/.test(s)&&!/final|post|complete|ended/.test(s))return'live';if(/post|final|complete|ended/.test(s))return'final';return'scheduled'}
function teamPair(e){if(e?.competitions?.[0]){const c=e.competitions[0].competitors||[],h=c.find(x=>x.homeAway==='home')||c[0]||{},a=c.find(x=>x.homeAway==='away')||c[1]||{};const m=x=>({name:x?.team?.displayName||x?.team?.name||'Team',logo:x?.team?.logo||x?.team?.logos?.[0]?.href||'',score:x?.score??''});return{home:m(h),away:m(a)}}return{home:{name:e?.home||'Home',score:e?.homeScore??'',logo:e?.homeLogo||''},away:{name:e?.away||'Away',score:e?.awayScore??'',logo:e?.awayLogo||''}}}
function eventDate(e){return e?.date||e?.competitions?.[0]?.date||''}
function gameCard(e){const st=stateOf(e),t=teamPair(e),detail=e?.status?.type?.shortDetail||e?.status?.type?.description||e?.status||e?.displayTime||dt(eventDate(e));const team=(x)=>'<div class="img-team">'+(x.logo?'<img src="'+esc(x.logo)+'" alt="" loading="lazy">':'<span class="img-team-logo-fallback">'+esc((x.name||'?').slice(0,2).toUpperCase())+'</span>')+'<strong>'+esc(x.name)+'</strong><b>'+(st==='scheduled'?'':esc(x.score))+'</b></div>';return'<article class="img-game-card '+(st==='live'?'live':'')+'"><div class="img-game-meta"><span>'+(st==='live'?'<b class="img-live-chip">LIVE</b>':esc(st==='final'?'FINAL':'SCHEDULED'))+'</span><span class="img-game-time">'+esc(detail||dt(eventDate(e)))+'</span></div>'+team(t.away)+team(t.home)+'</article>'}
function updateGameMode(){if(!modes.length){q('#imgGamesPanel').hidden=true;return}const m=modes[modeIndex%modes.length],list=m.items;q('#imgGamesMode').textContent=m.label;q('#imgGames').innerHTML=list.map(gameCard).join('');q('#imgGamesPanel').hidden=false}
q('#imgGamesMode').onclick=()=>{if(modes.length>1){modeIndex=(modeIndex+1)%modes.length;updateGameMode()}};
async function loadUserLogoMap(){
 if(window.IMG_SCORE_LEAGUE_LOGOS)return window.IMG_SCORE_LEAGUE_LOGOS;
 return new Promise(resolve=>{
   const sc=document.createElement('script');sc.src='/score-league-user-logos.js?v=20260923-2';
   sc.onload=()=>resolve(window.IMG_SCORE_LEAGUE_LOGOS||{});sc.onerror=()=>resolve({});
   document.head.append(sc);
 });
}
async function officialFallbackLogo(){
 try{
   const r=await fetch('/league-sources.json?v=20260923-2',{cache:'no-store'});if(!r.ok)throw 0;
   const j=await r.json(),u=j?.leagues?.[slug]?.official||'';if(!u)return'';
   const host=new URL(u).hostname;return 'https://www.google.com/s2/favicons?domain='+encodeURIComponent(host)+'&sz=256';
 }catch{return''}
}
function setLeagueIdentityLogo(src){
 if(!src)return;
 let box=document.querySelector('.img-league-identity');
 if(!box){box=document.createElement('div');box.className='img-league-identity';document.querySelector('.hero .shell')?.append(box)}
 box.innerHTML='<img src="'+esc(src)+'" alt="'+esc(cfg.name)+' logo" referrerpolicy="no-referrer">';
 const img=box.querySelector('img');if(img)img.onerror=()=>{box.innerHTML='<span class="img-league-identity-fallback">'+esc(cfg.name.replace(/[^A-Za-z0-9]/g,'').slice(0,4).toUpperCase())+'</span>'};
}
async function resolveLeagueIdentity(){
 const map=await loadUserLogoMap(),mapped=map?.[cfg.key]||'';
 if(mapped){setLeagueIdentityLogo(mapped);return}
 const fallback=await officialFallbackLogo();if(fallback)setLeagueIdentityLogo(fallback);
 else{let box=document.querySelector('.img-league-identity');if(!box){box=document.createElement('div');box.className='img-league-identity';document.querySelector('.hero .shell')?.append(box)}box.innerHTML='<span class="img-league-identity-fallback">'+esc(cfg.name.replace(/[^A-Za-z0-9]/g,'').slice(0,4).toUpperCase())+'</span>'}
}
function setLeagueIdentityFromPayload(j){
 const logo=j?.leagues?.[0]?.logos?.[0]?.href||j?.leagues?.[0]?.logo||'';
 if(logo)setLeagueIdentityLogo(logo);
}
function renderHistory(finals){
 const host=q('#imgHistory');if(!host)return;
 if(!finals.length){
   host.innerHTML='<article class="img-history-card"><div class="img-history-date"><span>IMG archive</span><span class="img-history-final">VERIFYING</span></div><strong style="display:block;font-size:.92rem;line-height:1.5">Previous verified results will appear here automatically as IMG receives them from the league data sources.</strong></article>';
   return;
 }
 host.innerHTML=finals.slice(0,24).map(e=>{
   const t=teamPair(e),d=eventDate(e),logo=x=>x.logo?'<img src="'+esc(x.logo)+'" alt="" loading="lazy">':'<span class="img-team-logo-fallback">'+esc((x.name||'?').slice(0,2).toUpperCase())+'</span>';
   return '<article class="img-history-card"><div class="img-history-date"><span>'+esc(dt(d))+'</span><span class="img-history-final">FINAL</span></div>'+
    '<div class="img-history-team">'+logo(t.away)+'<span>'+esc(t.away.name)+'</span><b>'+esc(t.away.score)+'</b></div>'+
    '<div class="img-history-team">'+logo(t.home)+'<span>'+esc(t.home.name)+'</span><b>'+esc(t.home.score)+'</b></div></article>';
 }).join('');
}
async function localLeague(){const [a,b]=await Promise.allSettled([fetch('/special-sports-data.json?v='+Date.now(),{cache:'no-store'}).then(r=>r.ok?r.json():null),fetch('/extended-sports-data.json?v='+Date.now(),{cache:'no-store'}).then(r=>r.ok?r.json():null)]);return a.value?.leagues?.[cfg.key]||b.value?.leagues?.[cfg.key]||null}
function specialToEvent(g){return{id:g?.eventId||'',date:g?.date||'',state:g?.state||'',status:g?.status||g?.displayTime||'',home:g?.home||'',away:g?.away||'',homeScore:g?.homeScore??'',awayScore:g?.awayScore??'',homeLogo:g?.homeLogo||'',awayLogo:g?.awayLogo||''}}
async function getEvents(){if(cfg.local){const l=await localLeague();lastSource=l?.sourceName||'IMG data';return(Array.isArray(l?.games)?l.games:[]).map(specialToEvent)}if(cfg.regional){const r=await fetch(worker+'/regional-scores?league='+encodeURIComponent(cfg.key),{cache:'no-store'});if(!r.ok)throw 0;const j=await r.json();lastSource=j.source||'IMG regional feed';return Array.isArray(j.events)?j.events:[]}if(cfg.score){const now=new Date(),a=new Date(now-60*86400000),b=new Date(now.getTime()+21*86400000),url=cfg.score+(cfg.score.includes('?')?'&':'?')+'dates='+dateKey(a)+'-'+dateKey(b);try{const r=await fetch(url,{cache:'no-store'});if(r.ok){const j=await r.json();setLeagueIdentityFromPayload(j);lastSource=j?.leagues?.[0]?.name||'Connected sports feed';return j.events||[]}}catch{}const r=await fetch(worker+'/scoreboard?league='+encodeURIComponent(cfg.key)+'&dates='+dateKey(a)+'-'+dateKey(b),{cache:'no-store'});if(!r.ok)throw 0;const j=await r.json();lastSource='IMG proxy';return j.events||[]}return[]}
async function renderEvents(){try{const ev=await getEvents();lastEvents=ev;const now=Date.now(),live=ev.filter(e=>stateOf(e)==='live'),up=ev.filter(e=>stateOf(e)==='scheduled'&&new Date(eventDate(e)||0).getTime()>=now).sort((a,b)=>new Date(eventDate(a))-new Date(eventDate(b))).slice(0,10),finals=ev.filter(e=>stateOf(e)==='final').sort((a,b)=>new Date(eventDate(b))-new Date(eventDate(a))).slice(0,10);modes=[];if(live.length)modes.push({label:'Live now',items:live});if(up.length)modes.push({label:'Upcoming',items:up});if(finals.length)modes.push({label:'Results',items:finals});modeIndex=0;updateGameMode();renderHistory(finals);q('#imgUpdateText').textContent='Updated '+new Intl.DateTimeFormat(undefined,{hour:'numeric',minute:'2-digit'}).format(new Date())+' · '+lastSource;renderKpis(live,up,finals);queueHighlights()}catch{q('#imgGamesPanel').hidden=true;q('#imgUpdateText').textContent='Waiting for the next verified data refresh';renderKpis([],[],[])}}
function renderKpis(live,up,finals){const next=up[0],nextPair=next?teamPair(next):null;const data=[['Live now',live.length?live.length+' game'+(live.length>1?'s':''):'No live game'],['Next',nextPair?nextPair.away.name+' vs '+nextPair.home.name:'Check back soon'],['Recent results',finals.length?finals.length+' available':'No recent result'],['Source',lastSource]];q('#imgKpis').innerHTML=data.map(x=>'<div class="img-kpi img-reveal"><small>'+esc(x[0])+'</small><strong>'+esc(x[1])+'</strong></div>').join('');observe()}
function stat(e,names){for(const s of(Array.isArray(e?.stats)?e.stats:[])){if(names.includes(String(s.name||s.type||'').toLowerCase()))return s.displayValue??s.value??''}return''}
function standardEntries(j){const groups=[];if(Array.isArray(j?.children))groups.push(...j.children);if(j?.standings)groups.push({standings:j.standings});return groups.flatMap(g=>g?.standings?.entries||g?.entries||[])}
function table(rows){return'<table><thead><tr><th>Team</th><th>W</th><th>L</th><th>PCT</th></tr></thead><tbody>'+rows.map(e=>{if(e.team&&typeof e.team==='string'){const w=Number(e.wins)||0,l=Number(e.losses)||0,p=w+l?(w/(w+l)).toFixed(3):'';return'<tr><td>'+esc(e.team)+'</td><td>'+w+'</td><td>'+l+'</td><td>'+p+'</td></tr>'}const t=e?.team||{};return'<tr><td>'+esc(t.displayName||t.name||'Team')+'</td><td>'+esc(stat(e,['wins']))+'</td><td>'+esc(stat(e,['losses']))+'</td><td>'+esc(stat(e,['winpercent','winpercent']))+'</td></tr>'}).join('')+'</tbody></table>'}
async function renderStandings(){const panel=q('#imgStandingsPanel'),host=q('#imgStandings');try{if(cfg.local){const l=await localLeague(),st=l?.standings;if(Array.isArray(st)&&st.length){host.innerHTML=table(st);panel.hidden=false;return}if(st&&typeof st==='object'){const g=Object.entries(st).filter(([,v])=>Array.isArray(v)&&v.length);if(g.length){host.innerHTML=g.map(([n,v])=>'<h4>'+esc(n.replace(/([A-Z])/g,' $1'))+'</h4>'+table(v)).join('');panel.hidden=false;return}}}if(cfg.stand){const r=await fetch(cfg.stand,{cache:'no-store'});if(r.ok){const rows=standardEntries(await r.json());if(rows.length){host.innerHTML=table(rows.slice(0,40));panel.hidden=false;return}}}panel.hidden=true}catch{panel.hidden=true}}
async function renderNews(){const panel=q('#imgNewsPanel'),host=q('#imgNews');try{const r=await fetch('/news-data.json?v='+Date.now(),{cache:'no-store'});if(!r.ok)throw 0;const j=await r.json(),rx=new RegExp(cfg.news,'i'),items=(j.items||[]).filter(x=>rx.test((x.title||'')+' '+(x.description||''))).slice(0,7);if(!items.length){panel.hidden=true;return}host.innerHTML=items.map(x=>'<a class="img-news-item" href="'+esc(x.link)+'" target="_blank" rel="noopener noreferrer">'+(x.image?'<img src="'+esc(x.image)+'" alt="" loading="lazy" referrerpolicy="no-referrer">':'<span></span>')+'<div class="img-news-copy"><strong>'+esc(x.title)+'</strong><span>'+esc(x.source||'Sports news')+' · '+esc(dt(x.published))+'</span></div></a>').join('');panel.hidden=false}catch{panel.hidden=true}}
function collectUrls(node,out=[]){if(!node)return out;if(typeof node==='string'){if(/^https?:\/\//i.test(node))out.push(node);return out}if(Array.isArray(node)){node.forEach(x=>collectUrls(x,out));return out}if(typeof node==='object')Object.values(node).forEach(v=>collectUrls(v,out));return out}
function clipOf(v){const urls=[...new Set(collectUrls(v))],media=urls.find(u=>/\.mp4(?:\?|$)/i.test(u))||'',thumb=v?.thumbnail||v?.image?.url||v?.images?.[0]?.url||v?.posterImage?.href||v?.poster?.href||'',title=v?.headline||v?.title||v?.description||'Game highlight',source=v?.links?.web?.href||v?.link?.href||v?.href||'';return media?{title,media,thumb,source,label:'Highlight'}:null}
async function espnClips(){if(!cfg.score)return[];const finished=lastEvents.filter(e=>stateOf(e)!=='scheduled'&&(e.id||e.uid)).slice(0,12),clips=[];await Promise.allSettled(finished.map(async e=>{const id=e.id||e.uid,u=cfg.score.replace(/\/scoreboard(?:\?.*)?$/,'/summary?event='+encodeURIComponent(id));const r=await fetch(u,{cache:'no-store'});if(!r.ok)return;const j=await r.json();[...(j.videos||[]),...(j.highlights||[])].forEach(v=>{const c=clipOf(v);if(c)clips.push(c)})}));return clips}
async function newsClips(){try{const r=await fetch('/news-data.json?v='+Date.now(),{cache:'no-store'});if(!r.ok)return[];const j=await r.json(),rx=new RegExp(cfg.news,'i');return (j.videos||[]).filter(v=>rx.test((v.title||'')+' '+(v.description||''))).map(v=>{const media=v.media||v.video||v.url||'',id=v.youtubeId||v.videoId||'';if(id)return{title:v.title||'Video highlight',youtube:id,thumb:v.image||v.thumbnail||'',source:v.link||'',label:'IMG video'};return /\.mp4(?:\?|$)/i.test(media)?{title:v.title||'Video highlight',media,thumb:v.image||v.thumbnail||'',source:v.link||'',label:'IMG video'}:null}).filter(Boolean)}catch{return[]}}
let highlightBusy=false;async function queueHighlights(){if(highlightBusy)return;highlightBusy=true;try{const clips=[...(await espnClips()),...(await newsClips())],seen=new Set(),uniq=clips.filter(c=>{const k=c.media||c.youtube||c.title;if(!k||seen.has(k))return false;seen.add(k);return true}).slice(0,12);renderReels(uniq)}finally{highlightBusy=false}}
function renderReels(clips){const panel=q('#imgHighlightsPanel'),host=q('#imgReels');if(!clips.length){panel.hidden=true;return}host.innerHTML=clips.map((c,i)=>'<article class="img-reel" data-reel="'+i+'">'+(c.thumb?'<img src="'+esc(c.thumb)+'" alt="" loading="lazy" referrerpolicy="no-referrer">':'')+'<div class="img-reel-gradient"></div><span class="img-reel-source">'+esc(c.label||'Highlight')+'</span><div class="img-reel-info"><strong>'+esc(c.title)+'</strong><span>Tap to play</span></div><button class="img-reel-play" type="button" aria-label="Play highlight"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></button></article>').join('');host.querySelectorAll('.img-reel').forEach((el,i)=>el.querySelector('button').onclick=()=>playReel(el,clips[i]));panel.hidden=false;observe()}
function playReel(el,c){document.querySelectorAll('.img-reel video').forEach(v=>{v.pause();v.remove()});if(c.youtube){const f=document.createElement('iframe');f.src='https://www.youtube-nocookie.com/embed/'+encodeURIComponent(c.youtube)+'?autoplay=1&playsinline=1&rel=0';f.allow='autoplay; encrypted-media; picture-in-picture';f.allowFullscreen=true;Object.assign(f.style,{position:'absolute',inset:'0',width:'100%',height:'100%',border:'0',zIndex:'1'});el.append(f);return}const v=document.createElement('video');v.src=c.media;v.controls=true;v.autoplay=true;v.playsInline=true;v.poster=c.thumb||'';el.append(v);v.play().catch(()=>{})}
function observe(){const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)e.target.classList.add('in')}),{threshold:.08});document.querySelectorAll('.img-reveal:not(.in)').forEach(x=>io.observe(x))}
async function refreshAll(){await Promise.allSettled([renderEvents(),renderStandings(),renderNews()]);observe()}
resolveLeagueIdentity();
q('#imgHistoryPrev')?.addEventListener('click',()=>q('#imgHistory')?.scrollBy({left:-420,behavior:'smooth'}));
q('#imgHistoryNext')?.addEventListener('click',()=>q('#imgHistory')?.scrollBy({left:420,behavior:'smooth'}));
refreshAll();setInterval(()=>{if(!document.hidden)renderEvents()},60000);setInterval(()=>{if(!document.hidden){renderNews();queueHighlights();renderStandings()}},300000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshAll()});
})();