
const API='https://img-api-proxy.magsipocarnie.workers.dev/games';
let allGames=[], current='All';

function localDate(offsetDays=0){
  const d=new Date();
  d.setDate(d.getDate()+offsetDays);
  const y=d.getFullYear();
  const m=String(d.getMonth()+1).padStart(2,'0');
  const day=String(d.getDate()).padStart(2,'0');
  return `${y}-${m}-${day}`;
}

function gameIsLive(g){
  return /live|in progress|halftime|quarter|period|overtime/i.test(
    g.status_state || g.status || ''
  );
}

function gameStatus(g){
  if(gameIsLive(g)) return 'LIVE';
  const s=(g.status || '').toLowerCase();
  if(s === 'final') return 'FINAL';
  if(s === 'postponed') return 'POSTPONED';
  if(s === 'canceled' || s === 'cancelled') return 'CANCELLED';
  return 'SCHEDULED';
}

function teamName(team){
  return team?.full_name || team?.name || 'Team';
}

function formatTime(value){
  if(!value) return '';
  const d=new Date(value);
  if(Number.isNaN(d.getTime())) return '';
  return d.toLocaleTimeString([], {hour:'numeric', minute:'2-digit'});
}

async function fetchGames(){
  const today=localDate(0);
  const url=`${API}?start_date=${today}&end_date=${today}&per_page=100`;
  const r=await fetch(url, {cache:'no-store'});
  if(!r.ok) throw new Error(`API ${r.status}`);
  const j=await r.json();
  return j.data || [];
}

async function loadHeroGame(){
  try{
    const events=await fetchGames();
    if(!events.length){
      document.getElementById('heroHome').textContent='No NBA game today';
      document.getElementById('heroAway').textContent='Check Live Scores';
      document.getElementById('heroHomeScore').textContent='—';
      document.getElementById('heroAwayScore').textContent='—';
      document.getElementById('heroStatus').textContent='● TODAY';
      document.getElementById('heroMeta').textContent='No NBA games returned for today';
      document.getElementById('heroSport').textContent='BASKETBALL · NBA';
      document.getElementById('heroBar').style.width='18%';
      return;
    }

    const live=events.find(gameIsLive);
    const g=live || events[0];
    const home=teamName(g.home_team);
    const away=teamName(g.visitor_team);
    const hs=g.home_team_score ?? '—';
    const as=g.visitor_team_score ?? '—';
    const status=gameStatus(g);

    document.getElementById('heroHome').textContent=home;
    document.getElementById('heroAway').textContent=away;
    document.getElementById('heroHomeScore').textContent=hs;
    document.getElementById('heroAwayScore').textContent=as;
    document.getElementById('heroSport').textContent='BASKETBALL · NBA';
    document.getElementById('heroStatus').textContent=live ? '● LIVE' : '● '+status;
    document.getElementById('heroMeta').textContent=
      live ? (g.period ? `Period ${g.period}` : 'In progress') :
      (formatTime(g.datetime) ? `Today · ${formatTime(g.datetime)}` : status);
    document.getElementById('heroBar').style.width=live ? '68%' : '38%';
  }catch(e){
    document.getElementById('heroHome').textContent='Live data unavailable';
    document.getElementById('heroAway').textContent='Please refresh';
    document.getElementById('heroHomeScore').textContent='—';
    document.getElementById('heroAwayScore').textContent='—';
    document.getElementById('heroStatus').textContent='● OFFLINE';
    document.getElementById('heroMeta').textContent='Unable to load live NBA game data';
  }
}


const IMG_HIGHLIGHTS_API = 'https://img-api-proxy.magsipocarnie.workers.dev/highlights';
function IMG_openHighlight(item){
  const modal=document.getElementById('img-highlight-modal');
  document.getElementById('img-highlight-league').textContent=item.league || 'OFFICIAL HIGHLIGHT';
  document.getElementById('img-highlight-title').textContent=item.title || 'Sports Highlight';
  document.getElementById('img-highlight-meta').textContent=item.source ? `Official video via ${item.source}` : 'Official sports highlight';
  document.getElementById('img-highlight-frame').src=item.embed_url || '';
  modal.hidden=false; modal.setAttribute('aria-hidden','false'); document.body.style.overflow='hidden';
}
function IMG_closeHighlight(){
  const modal=document.getElementById('img-highlight-modal');
  document.getElementById('img-highlight-frame').src=''; modal.hidden=true; modal.setAttribute('aria-hidden','true'); document.body.style.overflow='';
}
const IMG_STATIC_HIGHLIGHTS=[
  {league:'FIBA',title:'Philippines 🇵🇭 v Iran 🇮🇷 | Highlights | FIBA Basketball World Cup 2027 Asian Qualifiers',source:'FIBA Basketball (Official)',video_id:'MNIx0Ky0wIs',watch_url:'https://www.youtube.com/watch?v=MNIx0Ky0wIs',embed_url:'https://www.youtube.com/embed/MNIx0Ky0wIs?autoplay=1&rel=0',thumbnail:'https://i.ytimg.com/vi/MNIx0Ky0wIs/hqdefault.jpg'},
  {league:'FIBA',title:'Philippines 🇵🇭 v Iran 🇮🇷 | Extended Highlights | FIBA Basketball World Cup 2027 Asian Qualifiers',source:'FIBA Basketball (Official)',video_id:'vIidwJlqwQk',watch_url:'https://www.youtube.com/watch?v=vIidwJlqwQk',embed_url:'https://www.youtube.com/embed/vIidwJlqwQk?autoplay=1&rel=0',thumbnail:'https://i.ytimg.com/vi/vIidwJlqwQk/hqdefault.jpg'},
  {league:'FIBA',title:'Jordan vs Philippines | Game Highlights | FIBA Basketball World Cup 2027 Asian Qualifiers',source:'FIBA Basketball (Official)',video_id:'k4FJ6SjxFBM',watch_url:'https://www.youtube.com/watch?v=k4FJ6SjxFBM',embed_url:'https://www.youtube.com/embed/k4FJ6SjxFBM?autoplay=1&rel=0',thumbnail:'https://i.ytimg.com/vi/k4FJ6SjxFBM/hqdefault.jpg'}
];
function IMG_bindStaticHighlights(){
  document.querySelectorAll('[data-static-highlight]').forEach(btn=>btn.addEventListener('click',()=>IMG_openHighlight(IMG_STATIC_HIGHLIGHTS[Number(btn.dataset.staticHighlight)])));
}
function IMG_renderHighlights(items){
  const grid=document.getElementById('img-highlights-grid');
  if(!grid || !Array.isArray(items) || !items.length) return;
  grid.innerHTML=items.slice(0,12).map((item,i)=>`<button type="button" class="highlight-card" data-highlight-index="${i}" aria-label="Watch ${IMG_escapeHighlightText(item.title||'Sports highlight')}"><div class="highlight-thumb">${item.thumbnail?`<img src="${IMG_escapeHighlightText(item.thumbnail)}" alt="" loading="lazy">`:''}<span class="highlight-play">▶</span></div><div class="highlight-body"><div class="highlight-league">${IMG_escapeHighlightText(item.league||'Sports')}</div><div class="highlight-title">${IMG_escapeHighlightText(item.title||'Sports Highlight')}</div><div class="highlight-meta">${IMG_escapeHighlightText(item.source||'Official channel')}</div></div></button>`).join('');
  grid.querySelectorAll('[data-highlight-index]').forEach(btn=>btn.addEventListener('click',()=>IMG_openHighlight(items[Number(btn.dataset.highlightIndex)])));
}
async function IMG_loadHighlights(){
  try{
    const r=await fetch(IMG_HIGHLIGHTS_API,{cache:'no-store'});
    if(!r.ok) throw new Error('highlights endpoint '+r.status);
    const data=await r.json();
    const items=Array.isArray(data.items)?data.items.filter(x=>x && x.title && (x.embed_url || x.watch_url)):[];
    if(items.length) IMG_renderHighlights(items);
  }catch(e){
    console.warn('IMG highlights API unavailable; keeping built-in official highlights:',e);
  }
}
IMG_bindStaticHighlights();
IMG_loadHighlights();
setInterval(IMG_loadHighlights,900000);

document.addEventListener('click',e=>{if(e.target.matches('[data-highlight-close]')) IMG_closeHighlight();});
document.addEventListener('keydown',e=>{if(e.key==='Escape') IMG_closeHighlight();});
IMG_loadHighlights();
setInterval(IMG_loadHighlights,900000);


loadHeroGame();
setInterval(loadHeroGame,60000);

function showHome(){
  document.getElementById('platform').style.display='none';
  document.getElementById('home').style.display='block';
  window.location.hash='home';
  window.scrollTo({top:0,behavior:'smooth'});
}

function showPlatform(){
  document.getElementById('home').style.display='none';
  const platform=document.getElementById('platform');
  platform.style.display='block';
  window.location.hash='platform';
  requestAnimationFrame(()=>platform.scrollIntoView({behavior:'smooth',block:'start'}));
  loadGames();
}

function showHomeSection(id){
  document.getElementById('platform').style.display='none';
  document.getElementById('home').style.display='block';
  window.location.hash=id;
  const target=document.getElementById(id);
  if(target){
    setTimeout(function(){
      const y=target.getBoundingClientRect().top + window.pageYOffset - 78;
      window.scrollTo({top:y,behavior:'smooth'});
    },10);
  }
}

async function loadGames(){
  const box=document.getElementById('games');
  box.innerHTML='<div class="empty">Loading NBA live scores…</div>';
  try{
    allGames=await fetchGames();
    render();
  }catch(e){
    box.innerHTML='<div class="empty">Live NBA score data is temporarily unavailable. Please refresh.</div>';
  }
}

function filterSport(s,b){
  current=s;
  document.querySelectorAll('.filter').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  render();
}

function render(){
  let arr=allGames;

  if(!arr.length){
    document.getElementById('games').innerHTML=
      '<div class="empty">No NBA games available today.</div>';
    return;
  }

  // Show live games first, then scheduled/final games.
  arr=[...arr].sort((a,b)=>Number(gameIsLive(b))-Number(gameIsLive(a)));

  document.getElementById('games').innerHTML=arr.slice(0,100).map(g=>{
    const home=teamName(g.home_team);
    const away=teamName(g.visitor_team);
    const hs=g.home_team_score ?? '—';
    const as=g.visitor_team_score ?? '—';
    const st=gameStatus(g);
    const live=gameIsLive(g);
    const time=formatTime(g.datetime);
    const meta=live ? 'Basketball · NBA' :
      (time ? `Basketball · NBA · ${time}` : 'Basketball · NBA');

    return `<div class="game">
      <div class="status ${live?'live':''}">${live?'● LIVE':st}</div>
      <div class="teams2">
        <div style="font-size:11px;color:#8f98a5;text-transform:uppercase;letter-spacing:.7px;margin-bottom:3px">${meta}</div>
        <div class="teamrow"><span>${home}</span></div>
        <div class="teamrow"><span>${away}</span></div>
      </div>
      <div class="score2"><div>${hs}</div><div>${as}</div></div>
    </div>`;
  }).join('');
}
