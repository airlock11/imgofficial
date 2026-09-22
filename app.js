function readPreference(key){try{return localStorage.getItem(key)}catch{return null}}
function writePreference(key,value){try{localStorage.setItem(key,value)}catch{}}
const root=document.documentElement,savedTheme=readPreference('img-theme')||'dark';
root.dataset.theme=savedTheme;
const theme=document.createElement('button');
theme.className='themebtn';
theme.setAttribute('aria-label','Switch color theme');
theme.setAttribute('type','button');
document.body.append(theme);

const desktopThemeMarkup='<span class="theme-track" aria-hidden="true"><span class="theme-icon sun"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></span><span class="theme-icon moon"><svg viewBox="0 0 24 24"><path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5 8.5 8.5 0 1 0 20.5 14.2Z"/></svg></span><span class="theme-thumb"></span></span>';
const mobileThemeMarkup=()=>'<span class="theme-mobile-icon" aria-hidden="true">'+(root.dataset.theme==='dark'?'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>':'<svg viewBox="0 0 24 24"><path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5 8.5 8.5 0 1 0 20.5 14.2Z"/></svg>')+'</span>';
const isMobileTheme=()=>matchMedia('(max-width:760px)').matches;
const paint=()=>{
  theme.innerHTML=desktopThemeMarkup+mobileThemeMarkup();
  theme.setAttribute('aria-pressed',root.dataset.theme==='light'?'true':'false');
  theme.setAttribute('title',root.dataset.theme==='dark'?'Switch to light mode':'Switch to dark mode');
};
paint();

let drag=false,moved=false,dx=0,dy=0;
function resetDesktopThemePosition(){
  if(!isMobileTheme()){
    theme.style.left='';
    theme.style.top='';
    theme.style.right='';
    theme.style.bottom='';
  }
}
function restoreMobileThemePosition(){
  if(!isMobileTheme())return;
  let savedPosition;
  try{savedPosition=JSON.parse(readPreference('img-theme-position')||'null')}catch{return}
  if(savedPosition){
    const x=Math.max(8,Math.min(innerWidth-theme.offsetWidth-8,Number(savedPosition.x)||8));
    const y=Math.max(8,Math.min(innerHeight-theme.offsetHeight-8,Number(savedPosition.y)||8));
    theme.style.left=x+'px';
    theme.style.top=y+'px';
    theme.style.right='auto';
    theme.style.bottom='auto';
  }
}
resetDesktopThemePosition();
restoreMobileThemePosition();

theme.addEventListener('pointerdown',e=>{
  if(!isMobileTheme())return;
  drag=true;moved=false;
  const r=theme.getBoundingClientRect();
  dx=e.clientX-r.left;dy=e.clientY-r.top;
  theme.setPointerCapture(e.pointerId);
});
theme.addEventListener('pointermove',e=>{
  if(!drag||!isMobileTheme())return;
  moved=true;
  const x=Math.max(8,Math.min(innerWidth-theme.offsetWidth-8,e.clientX-dx));
  const y=Math.max(8,Math.min(innerHeight-theme.offsetHeight-8,e.clientY-dy));
  theme.style.left=x+'px';theme.style.top=y+'px';theme.style.right='auto';theme.style.bottom='auto';
});
theme.addEventListener('pointerup',()=>{
  if(!isMobileTheme()||!drag)return;
  drag=false;
  if(moved){
    const r=theme.getBoundingClientRect();
    writePreference('img-theme-position',JSON.stringify({x:Math.round(r.left),y:Math.round(r.top)}));
  }else{
    root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';
    writePreference('img-theme',root.dataset.theme);
    paint();
  }
});
theme.addEventListener('click',()=>{
  if(isMobileTheme())return;
  root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';
  writePreference('img-theme',root.dataset.theme);
  paint();
});
addEventListener('resize',()=>{
  if(isMobileTheme()){
    if(!theme.style.left)restoreMobileThemePosition();
  }else{
    resetDesktopThemePosition();
  }
});

const navIcons={Home:'home',Sports:'sports',Scores:'scores',News:'news',Odds:'odds'};
document.querySelectorAll('.bottomnav a').forEach(a=>{let label=a.textContent.trim();if(label==='Tools'){a.href='/odds/';a.childNodes[a.childNodes.length-1].textContent='Odds';label='Odds'}const b=a.querySelector('b');if(b&&navIcons[label])b.innerHTML='<span class="navglyph icon-'+navIcons[label]+'" aria-hidden="true"></span>';if(a.classList.contains('active'))a.setAttribute('aria-current','page')});
document.querySelectorAll('.navlinks a').forEach(a=>{const label=a.textContent.trim();if(a.classList.contains('active'))a.setAttribute('aria-current','page')});
document.querySelector('header nav')?.setAttribute('aria-label','Primary navigation');document.querySelectorAll('.bottomnav').forEach(n=>{n.setAttribute('role','navigation');n.setAttribute('aria-label','Mobile navigation')});
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const leagues={Basketball:[['NBA','United States / Canada'],['WNBA','United States / Canada'],['PBA','Philippines'],['MPBL','Philippines'],['NBL-Pilipinas','Philippines'],['NBL Australia','Australia / New Zealand'],['VBA','Vietnam'],['B.League','Japan'],['EuroLeague','Europe'],['WBSL','International']],Football:[['Premier League','England'],['La Liga','Spain'],['Serie A','Italy'],['Bundesliga','Germany'],['UEFA Champions League','Europe'],['Philippine Football League','Philippines']],Tennis:[['ATP Tour','International'],['WTA Tour','International'],['Australian Open','Australia'],['Wimbledon','United Kingdom'],['US Open','United States']],Baseball:[['MLB','USA / Canada'],['NPB','Japan'],['KBO League','South Korea']],Hockey:[['NHL','USA / Canada'],['KHL','Eurasia'],['IIHF World Championship','International']],Cricket:[['IPL','India'],['Big Bash League','Australia'],['ICC Cricket World Cup','International']],Volleyball:[['Volleyball Nations League','International'],['PVL','Philippines'],['V.League','Japan']],Motorsport:[['Formula 1','International'],['MotoGP','International'],['Formula E','International']],Boxing:[['WBC','International'],['WBA','International'],['IBF','International'],['WBO','International'],['Professional Boxing','Worldwide']],'Combat Sports':[['UFC','International'],['ONE Championship','Asia']],'American Football':[['NFL','United States'],['NCAA Football','United States']]};
function openSport(name){if(name==='Boxing'){location.href='/boxing/';return}const modal=document.getElementById('sportModal');if(!modal)return;modal.querySelector('h2').textContent=name;modal.querySelector('.modalbody').innerHTML=(leagues[name]||[]).map(x=>'<div class="league-row"><strong>'+esc(x[0])+'</strong><small>'+esc(x[1])+'</small></div>').join('');modal.showModal()}
document.addEventListener('click',e=>{
  const statsToggle=e.target.closest('[data-stats-toggle]');
  if(statsToggle){
    const section=statsToggle.closest('.sports-statistics');
    if(section){
      const expanded=statsToggle.getAttribute('aria-expanded')==='true';
      statsToggle.setAttribute('aria-expanded',expanded?'false':'true');
      section.classList.toggle('stats-open',!expanded);
    }
    return;
  }
  const standingsToggle=e.target.closest('[data-standings-toggle]');
  if(standingsToggle){
    const section=standingsToggle.closest('.league-standings-dropdown');
    if(section){
      const expanded=standingsToggle.getAttribute('aria-expanded')==='true';
      standingsToggle.setAttribute('aria-expanded',expanded?'false':'true');
      section.classList.toggle('standings-open',!expanded);
    }
    return;
  }
  const newsVideo=e.target.closest('[data-play-news-video]');
  if(newsVideo){
    const id=newsVideo.dataset.playNewsVideo;
    const card=newsVideo.closest('[data-news-video]');
    if(id&&card){
      const frame=card.querySelector('.news-video-frame');
      if(frame){
        frame.outerHTML='<div class="news-video-frame news-video-playing"><iframe src="https://www.youtube-nocookie.com/embed/'+encodeURIComponent(id)+'?autoplay=1&playsinline=1&rel=0" title="Sports video" allow="autoplay; encrypted-media; picture-in-picture; web-share" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div>';
      }
    }
    return;
  }
  const sport=e.target.closest('[data-sport]');if(sport)openSport(sport.dataset.sport);if(e.target.matches('.close'))e.target.closest('dialog').close();const highlightButton=e.target.closest('[data-highlight-event]');if(highlightButton)openHighlights(highlightButton.dataset.highlightEvent);const liveButton=e.target.closest('[data-live-event]');if(liveButton)openLiveStream(liveButton.dataset.liveEvent)});
const scoreFeeds={
  soccer:'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard',
  laliga:'https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard',
  seriea:'https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard',
  bundesliga:'https://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/scoreboard',
  champions:'https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard',
  mls:'https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/scoreboard',
  basketball:'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard',
  wnba:'https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard',
  atp:'https://site.api.espn.com/apis/site/v2/sports/tennis/atp/scoreboard',
  wta:'https://site.api.espn.com/apis/site/v2/sports/tennis/wta/scoreboard',
  ipl:'https://site.api.espn.com/apis/site/v2/sports/cricket/ipl/scoreboard',
  volleyball_w:'https://site.api.espn.com/apis/site/v2/sports/volleyball/fivb.w/scoreboard',
  volleyball_m:'https://site.api.espn.com/apis/site/v2/sports/volleyball/fivb.m/scoreboard',
  f1:'https://site.api.espn.com/apis/site/v2/sports/racing/f1/scoreboard',
  ufc:'https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard',
  baseball:'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard',
  hockey:'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard',
  football:'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard',
  ncaaf:'https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard'
};
const cloudflareFallbackFeeds={
  soccer:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=soccer',
  laliga:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=laliga',
  seriea:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=seriea',
  bundesliga:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=bundesliga',
  champions:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=champions',
  basketball:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=basketball',
  wnba:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=wnba',
  atp:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=atp',
  wta:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=wta',
  ipl:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=ipl',
  volleyball_w:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=volleyball_w',
  volleyball_m:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=volleyball_m',
  f1:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=f1',
  ufc:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=ufc',
  pba:'https://img-api-proxy.magsipocarnie.workers.dev/regional-scores?league=pba',
  mpbl:'https://img-api-proxy.magsipocarnie.workers.dev/regional-scores?league=mpbl',
  nbl:'https://img-api-proxy.magsipocarnie.workers.dev/regional-scores?league=nbl',
  nblaus:'https://img-api-proxy.magsipocarnie.workers.dev/regional-scores?league=nblaus',
  vba:'https://img-api-proxy.magsipocarnie.workers.dev/regional-scores?league=vba',
  baseball:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=baseball',
  hockey:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=hockey',
  football:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=football',
  ncaaf:'https://img-api-proxy.magsipocarnie.workers.dev/scoreboard?league=ncaaf'
};
const regionalScoreKeys=new Set(['pba','mpbl','nbl','nblaus','vba']);

let specialSportsDataCache=null;
let specialSportsDataTime=0;
let specialSportsDataPromise=null;
async function loadSpecialSportsData(){
  if(specialSportsDataCache&&Date.now()-specialSportsDataTime<30000)return specialSportsDataCache;
  if(specialSportsDataPromise)return specialSportsDataPromise;
  specialSportsDataPromise=Promise.allSettled([
    fetch('special-sports-data.json?v='+Date.now(),{cache:'no-store'}).then(r=>r.ok?r.json():null),
    fetch('extended-sports-data.json?v='+Date.now(),{cache:'no-store'}).then(r=>r.ok?r.json():null)
  ]).then(results=>{
    const base=results[0]?.status==='fulfilled'&&results[0].value?results[0].value:{};
    const extended=results[1]?.status==='fulfilled'&&results[1].value?results[1].value:{};
    const baseLeagues=base.leagues||{};
    const extendedLeagues=extended.leagues||{};
    const leagueKeys=new Set([...Object.keys(baseLeagues),...Object.keys(extendedLeagues)]);
    const mergedLeagues={};
    for(const key of leagueKeys){
      mergedLeagues[key]={...(baseLeagues[key]||{}),...(extendedLeagues[key]||{})};
    }
    const merged={...base,...extended,leagues:mergedLeagues};
    specialSportsDataCache=merged;
    specialSportsDataTime=Date.now();
    if(document.getElementById('scoreLeagueFilters'))renderScoreLeagueFilters();
    return merged;
  }).catch(()=>null).finally(()=>{specialSportsDataPromise=null});
  return specialSportsDataPromise;
}

async function specialSportsPayload(sport){
  const data=await loadSpecialSportsData();
  const league=data?.leagues?.[sport];
  if(!league||!Array.isArray(league.games)||!league.games.length)return null;
  return {special:true,games:league.games,sourceName:league.sourceName||'',sourceUrl:league.sourceUrl||''};
}
const specialScoreKeys=new Set(['atp','wta','ipl','volleyball_w','volleyball_m','asian_games','fiba','ncaa_ph','bleague','euroleague','pfl','australian_open','wimbledon','us_open','npb','kbo','khl','iihf','bigbash','cricket_world_cup','pvl','vleague_jp','motogp','formulae','one','wbc','wba','ibf','wbo']);
function scoreGameLooksGeneric(g){
  const names=[g?.away,g?.home].map(x=>String(x||'').trim().toLowerCase());
  const generic=new Set(['','away','home','tbd','team 1','team 2','player 1','player 2']);
  return !g?.eventOnly&&names.every(x=>generic.has(x));
}
function mergeScoreGames(primary,fallback){
  const out=[],seen=new Set();
  for(const g of [...(primary||[]),...(fallback||[])]){
    const key=String(g?.eventId||[g?.date||'',g?.away||'',g?.home||'',g?.title||''].join('|'));
    if(seen.has(key))continue;
    seen.add(key);
    out.push(g);
  }
  return out;
}
async function fetchAsianGamesOfficial(){
  const url='https://results.asiangames2026.org/#/schedule';
  return {officialLive:true,sourceName:'Aichi-Nagoya 2026 Official Live Results',sourceUrl:url,games:[]};
}
async function fetchScorePayload(sport,{fallbackOnly=false}={}){
  if(sport==='asian_games'){
    const local=await specialSportsPayload(sport);
    if(local){
      local.officialLive=true;
      local.sourceName='Aichi-Nagoya 2026 Official Live Results';
      local.sourceUrl='https://results.asiangames2026.org/#/schedule';
    }
    return local||fetchAsianGamesOfficial();
  }
  if(sport==='boxing'){
    const [apiResult,webResult]=await Promise.allSettled([
      fetch('boxing-fights-data.json?v='+Date.now(),{cache:'no-store'}).then(r=>r.ok?r.json():null),
      fetch('boxing-web-data.json?v='+Date.now(),{cache:'no-store'}).then(r=>r.ok?r.json():null)
    ]);
    const api=apiResult.status==='fulfilled'&&apiResult.value?apiResult.value:{};
    const web=webResult.status==='fulfilled'&&webResult.value?webResult.value:{};
    const merged=[];
    const seen=new Set();
    const keyFor=f=>{
      const a=String(f?.fighters?.fighter_1?.name||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
      const b=String(f?.fighters?.fighter_2?.name||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
      const day=String(f?.date||'').slice(0,10);
      return [a,b].sort().join('|')+'|'+day;
    };
    for(const f of [...(api?.fights||[]),...(web?.fights||[])]){
      const key=keyFor(f);
      if(!key||seen.has(key))continue;
      seen.add(key);
      merged.push(f);
    }
    if(!merged.length)throw new Error('Boxing score sources unavailable');
    return {
      boxing:true,
      fights:merged,
      updated_at:api?.updated_at||web?.updated_at||null,
      sources:['Boxing Data API',...(web?.sources||[]).map(x=>x.name)].filter(Boolean)
    };
  }

  if(!fallbackOnly&&scoreFeeds[sport]){
    try{
      const r=await fetch(scoreFeeds[sport],{cache:'no-store'});
      if(r.ok){
        const j=await r.json();
        if(Array.isArray(j?.events)&&j.events.length)return j;
      }
    }catch{}
  }

  const fallback=cloudflareFallbackFeeds[sport];
  if(fallback){
    try{
      const r=await fetch(fallback,{cache:'no-store'});
      if(r.ok){
        const j=await r.json();
        if(Array.isArray(j?.events)&&j.events.length)return j;
      }
    }catch{}
  }

  const special=await specialSportsPayload(sport);
  if(special)return special;
  throw new Error('Score feed unavailable');
}
const liveNowLabels={
  soccer:{sport:'Football',league:'Premier League'},
  laliga:{sport:'Football',league:'La Liga'},
  seriea:{sport:'Football',league:'Serie A'},
  bundesliga:{sport:'Football',league:'Bundesliga'},
  champions:{sport:'Football',league:'UEFA Champions League'},
  mls:{sport:'Football',league:'MLS'},
  basketball:{sport:'Basketball',league:'NBA'},
  wnba:{sport:'Basketball',league:'WNBA'},
  atp:{sport:'Tennis',league:'ATP Tour'},
  wta:{sport:'Tennis',league:'WTA Tour'},
  ipl:{sport:'Cricket',league:'IPL'},
  volleyball_w:{sport:'Volleyball',league:'FIVB Women'},
  volleyball_m:{sport:'Volleyball',league:'FIVB Men'},
  f1:{sport:'Motorsport',league:'Formula 1'},
  ufc:{sport:'Combat Sports',league:'UFC'},
  boxing:{sport:'Boxing',league:'Boxing'},
  asian_games:{sport:'Special',league:'Asian Games'},
  fiba:{sport:'Special',league:'FIBA'},
  pba:{sport:'Basketball',league:'PBA'},
  ncaa_ph:{sport:'Basketball',league:'NCAA Philippines'},
  uaap:{sport:'Basketball',league:'UAAP'},
  mpbl:{sport:'Basketball',league:'MPBL'},
  nbl:{sport:'Basketball',league:'NBL-Pilipinas'},
  nblaus:{sport:'Basketball',league:'NBL Australia'},
  vba:{sport:'Basketball',league:'VBA'},
  baseball:{sport:'Baseball',league:'MLB'},
  hockey:{sport:'Hockey',league:'NHL'},
  football:{sport:'American Football',league:'NFL'},
  ncaaf:{sport:'American Football',league:'NCAA Football'},
  bleague:{sport:'Basketball',league:'B.League'},
  euroleague:{sport:'Basketball',league:'EuroLeague'},
  wbsl:{sport:'Basketball',league:'WBSL'},
  pfl:{sport:'Football',league:'Philippine Football League'},
  australian_open:{sport:'Tennis',league:'Australian Open'},
  wimbledon:{sport:'Tennis',league:'Wimbledon'},
  us_open:{sport:'Tennis',league:'US Open'},
  npb:{sport:'Baseball',league:'NPB'},
  kbo:{sport:'Baseball',league:'KBO League'},
  khl:{sport:'Hockey',league:'KHL'},
  iihf:{sport:'Hockey',league:'IIHF World Championship'},
  bigbash:{sport:'Cricket',league:'Big Bash League'},
  cricket_world_cup:{sport:'Cricket',league:'ICC T20 World Cup'},
  pvl:{sport:'Volleyball',league:'PVL'},
  vleague_jp:{sport:'Volleyball',league:'V.League Japan'},
  motogp:{sport:'Motorsport',league:'MotoGP'},
  formulae:{sport:'Motorsport',league:'Formula E'},
  one:{sport:'Combat Sports',league:'ONE Championship'},
  wbc:{sport:'Boxing',league:'WBC'},
  wba:{sport:'Boxing',league:'WBA'},
  ibf:{sport:'Boxing',league:'IBF'},
  wbo:{sport:'Boxing',league:'WBO'},
  ring:{sport:'Boxing',league:'THE RING'}
};
function asianGamesSportLabel(game){
  const title=String(game?.title||'').trim();
  const divider=' — ';
  const index=title.indexOf(divider);
  return index>0?title.slice(0,index).trim():'Asian Games';
}
function asianGamesEventLabel(game){
  const title=String(game?.title||'').trim();
  const divider=' — ';
  const index=title.indexOf(divider);
  return index>0?title.slice(index+divider.length).trim():(title||'Asian Games event');
}
const scoreLeagueOrder=['asian_games','fiba','soccer','laliga','seriea','bundesliga','champions','mls','pfl','basketball','wnba','pba','ncaa_ph','uaap','mpbl','nbl','nblaus','vba','bleague','euroleague','atp','wta','australian_open','wimbledon','us_open','ipl','bigbash','cricket_world_cup','volleyball_w','volleyball_m','pvl','vleague_jp','baseball','npb','kbo','hockey','khl','iihf','football','ncaaf','f1','motogp','formulae','ufc','one','wbc','wba','ibf','wbo','ring'];
const specialScoreLeagueKeys=new Set(['asian_games','fiba']);
const scoreSportDefaultLeague={
  basketball:'basketball',
  football:'soccer',
  tennis:'atp',
  baseball:'baseball',
  hockey:'hockey',
  cricket:'ipl',
  volleyball:'volleyball_w',
  motorsport:'f1',
  boxing:'wbc',
  'combat-sports':'ufc',
  'american-football':'football'
};
function initialScoreLeagueFromUrl(){
  try{
    const params=new URLSearchParams(location.search);
    const league=String(params.get('league')||'').trim();
    if(league&&scoreLeagueOrder.includes(league))return league;
    const sport=String(params.get('sport')||'').trim().toLowerCase();
    return scoreSportDefaultLeague[sport]||'soccer';
  }catch{
    return 'soccer';
  }
}
const scoreLeagueLogoCache=new Map();
let currentScoreLeague=initialScoreLeagueFromUrl();
let scoreLeagueAutoCenterPending=(()=>{
  try{
    const params=new URLSearchParams(location.search);
    return params.get('from')==='sports'&&scoreLeagueOrder.includes(String(params.get('league')||'').trim());
  }catch{return false}
})();
let scoreLoadToken=0;

function centerSelectedScoreLeagueFromSports(){
  if(!scoreLeagueAutoCenterPending)return;
  const host=document.getElementById('scoreLeagueFilters');
  if(!host)return;
  const selected=host.querySelector('[data-score-league="'+CSS.escape(currentScoreLeague)+'"]');
  const item=selected?.closest('.score-league-item')||selected;
  if(!item)return;
  scoreLeagueAutoCenterPending=false;
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    const maxLeft=Math.max(0,host.scrollWidth-host.clientWidth);
    const target=Math.max(0,Math.min(maxLeft,item.offsetLeft-(host.clientWidth-item.offsetWidth)/2));
    host.scrollTo({left:target,behavior:'smooth'});
  }));
}

function scoreLeagueFallback(key){
  const label=liveNowLabels[key]?.league||key.toUpperCase();
  const short={
    soccer:'EPL',laliga:'LAL',seriea:'SA',bundesliga:'BUN',champions:'UCL',mls:'MLS',
    basketball:'NBA',wnba:'WNBA',pba:'PBA',ncaa_ph:'NCAA-PH',uaap:'UAAP',mpbl:'MPBL',nbl:'NBL-PH',nblaus:'NBL',
    vba:'VBA',wbsl:'WBSL',fiba:'FIBA',atp:'ATP',wta:'WTA',ipl:'IPL',volleyball_w:'FIVB',volleyball_m:'FIVB',
    baseball:'MLB',npb:'NPB',kbo:'KBO',hockey:'NHL',khl:'KHL',iihf:'IIHF',football:'NFL',ncaaf:'NCAA',f1:'F1',motogp:'MGP',formulae:'FE',ufc:'UFC',one:'ONE',wbc:'WBC',wba:'WBA',ibf:'IBF',wbo:'WBO',ring:'RING',pfl:'PFL',bleague:'B.LEAGUE',euroleague:'EL',australian_open:'AO',wimbledon:'WIM',us_open:'USO',bigbash:'BBL',cricket_world_cup:'ICC',pvl:'PVL',vleague_jp:'V.LEAGUE',asian_games:'AG26'
  };
  return '<span class="score-league-fallback">'+esc(short[key]||label.slice(0,5).toUpperCase())+'</span>';
}

function scoreLeagueLogoMarkup(key){
  const supplied=window.IMG_SCORE_LEAGUE_LOGOS?.[key]||'';
  const feedLogo=scoreLeagueLogoCache.get(key)||'';

  if((key==='volleyball_w'||key==='volleyball_m')&&window.IMG_SCORE_LEAGUE_LOGOS?.fivb){
    const fivb=window.IMG_SCORE_LEAGUE_LOGOS.fivb;
    return '<span class="score-league-fivb-crop"><img src="'+esc(fivb)+'" alt="FIVB logo" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.parentElement.style.display=\'none\';this.parentElement.nextElementSibling.style.display=\'grid\'"></span>'+
      '<span class="score-league-fallback score-league-fallback-hidden">FIVB</span>';
  }

  const suppliedFirst=['atp','wta','ipl','boxing','asian_games'].includes(key);
  const logo=suppliedFirst?(supplied||feedLogo):(feedLogo||supplied);
  if(!logo)return scoreLeagueFallback(key);
  return '<img class="score-league-logo" src="'+esc(logo)+'" alt="'+esc(liveNowLabels[key]?.league||key)+' logo" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'grid\'">'+
    '<span class="score-league-fallback score-league-fallback-hidden">'+esc((liveNowLabels[key]?.league||key).replace(/[^A-Za-z0-9]/g,'').slice(0,5).toUpperCase())+'</span>';
}

function scoreLeagueActivityMap(){
  const map=new Map();
  for(const game of liveNowItems){
    if(!liveNowItemIsCurrent(game))continue;
    const key=String(game.sportKey||'');
    if(!key)continue;
    const current=map.get(key)||{live:false,stream:false};
    current.live=true;
    if(liveStreamsForGame(game).length)current.stream=true;
    map.set(key,current);
  }
  return map;
}
function renderScoreLeagueFilters(){
  const host=document.getElementById('scoreLeagueFilters');
  if(!host)return;
  const scoreCategory=String(liveNowLabels[currentScoreLeague]?.sport||'Sports').toLowerCase().replace(/[^a-z0-9]+/g,'-');
  document.body.dataset.scoreCategory=scoreCategory;
  const activity=scoreLeagueActivityMap();
  const fibaAvailable=Boolean(
    activity.get('fiba')||
    (Array.isArray(specialSportsDataCache?.leagues?.fiba?.games)&&specialSportsDataCache.leagues.fiba.games.length)
  );
  const visibleLeagueOrder=scoreLeagueOrder.filter(key=>key!=='fiba'||fibaAvailable||currentScoreLeague==='fiba');
  const baseIndex=new Map(scoreLeagueOrder.map((key,index)=>[key,index]));
  const ordered=[...visibleLeagueOrder].sort((a,b)=>{
    const aSpecial=specialScoreLeagueKeys.has(a);
    const bSpecial=specialScoreLeagueKeys.has(b);
    if(aSpecial!==bSpecial)return aSpecial?-1:1;
    const aa=activity.get(a)||{live:false,stream:false};
    const bb=activity.get(b)||{live:false,stream:false};
    const aRank=aa.stream?0:aa.live?1:2;
    const bRank=bb.stream?0:bb.live?1:2;
    return (aRank-bRank)||((baseIndex.get(a)||0)-(baseIndex.get(b)||0));
  });
  host.innerHTML=ordered.map(key=>{
    const label=liveNowLabels[key]?.league||key.toUpperCase();
    const displayLabel=label.replace(/Philippines/gi,'PH').replace(/Australia/gi,'AUS');
    const state=activity.get(key)||{live:false,stream:false};
    const liveClass=state.live?' has-live-activity':'';
    const streamClass=state.stream?' has-live-stream':'';
    const liveLabel=state.stream?' — live stream':state.live?' — live score':'';
    const specialClass=specialScoreLeagueKeys.has(key)?' is-special-league':'';
    const scoreKind=specialScoreLeagueKeys.has(key)?'special':'league';
    return '<div class="score-league-item'+(key==='champions'?' score-league-item-champions':'')+(key==='one'?' score-league-item-one':'')+specialClass+liveClass+streamClass+'" data-score-kind="'+scoreKind+'">'+
      '<button type="button" class="score-league-filter'+(currentScoreLeague===key?' active':'')+specialClass+liveClass+streamClass+'" data-score-league="'+esc(key)+'" aria-label="'+esc(label+liveLabel)+'" title="'+esc(label+liveLabel)+'">'+
        '<span class="score-league-logo-wrap">'+scoreLeagueLogoMarkup(key)+'</span>'+
      '</button>'+
      '<span class="score-league-name">'+esc(displayLabel)+'</span>'+
    '</div>';
  }).join('');

  centerSelectedScoreLeagueFromSports();

  host.querySelectorAll('[data-score-league]').forEach(btn=>btn.addEventListener('click',async()=>{
    const key=btn.dataset.scoreLeague;
    if(!key)return;
    currentScoreLeague=key;
    renderScoreLeagueFilters();
    const gamesHost=document.getElementById('games');
    if(gamesHost)gamesHost.innerHTML='<div class="empty">Loading '+esc(liveNowLabels[key]?.league||key.toUpperCase())+' schedule and scores…</div>';
    await loadGames({league:key});
  }));
}
async function loadScoreLeagueLogos(){
  const direct=Object.entries(scoreFeeds).map(async([key,url])=>{
    try{
      const r=await fetch(url,{cache:'no-store'});
      if(!r.ok)return;
      const j=await r.json();
      const league=j?.leagues?.[0]||{};
      const logos=Array.isArray(league.logos)?league.logos:[];
      const logo=logos.find(x=>/light|default/i.test(String(x?.rel||'')))?.href||logos[0]?.href||league.logo||'';
      if(logo)scoreLeagueLogoCache.set(key,logo);
    }catch{}
  });

  await Promise.allSettled(direct);
  renderScoreLeagueFilters();
}
let regionalAutoDataCache=null;
let regionalAutoDataPromise=null;
async function loadRegionalAutoData(){
  if(regionalAutoDataCache)return regionalAutoDataCache;
  if(regionalAutoDataPromise)return regionalAutoDataPromise;
  regionalAutoDataPromise=fetch('regional-web.json?v='+Date.now(),{cache:'no-store'})
    .then(r=>r.ok?r.json():null)
    .then(j=>regionalAutoDataCache=j)
    .catch(()=>null)
    .finally(()=>{regionalAutoDataPromise=null});
  return regionalAutoDataPromise;
}
function getRegionalSnapshot(sport){
  return regionalAutoDataCache?.leagues?.[sport]||regionalWebSnapshots[sport]||null;
}
let sportsStatsDataCache=null;
let sportsStatsDataTime=0;
let sportsStatsDataPromise=null;
async function loadSportsStatsData(){
  if(sportsStatsDataCache&&Date.now()-sportsStatsDataTime<120000)return sportsStatsDataCache;
  if(sportsStatsDataPromise)return sportsStatsDataPromise;
  sportsStatsDataPromise=fetch('stats-data.json?v='+Date.now(),{cache:'no-store'})
    .then(r=>r.ok?r.json():null)
    .then(j=>{sportsStatsDataCache=j;sportsStatsDataTime=Date.now();return j})
    .catch(()=>null)
    .finally(()=>{sportsStatsDataPromise=null});
  return sportsStatsDataPromise;
}
function statValue(row,key){
  const v=row?.[key];
  return Number.isFinite(Number(v))?Number(v).toFixed(1):'—';
}
function statsGroupsForLeague(data){
  if(Array.isArray(data?.groups))return data.groups;
  const leaders=data?.leaders||{};
  return [
    ['Points','points','ppg','PPG'],
    ['Rebounds','rebounds','rpg','RPG'],
    ['Assists','assists','apg','APG'],
    ['Steals','steals','spg','SPG'],
    ['Blocks','blocks','bpg','BPG']
  ].map(([title,key,valueKey,suffix])=>({
    title,suffix,
    rows:(leaders[key]||[]).map(r=>({...r,value:r?.[valueKey],displayValue:statValue(r,valueKey)}))
  })).filter(group=>group.rows.length);
}
function leagueStatsMarkup(key){
  const data=sportsStatsDataCache?.leagues?.[key];
  if(!data)return'';
  const groups=statsGroupsForLeague(data);
  if(!groups.length)return'';

  const leaderHtml=groups.map(group=>{
    const rows=(group.rows||[]).slice(0,5);
    if(!rows.length)return'';
    return '<article class="stats-leader-card"><div class="stats-leader-title">'+esc(group.title||'Leaders')+'</div>'+
      '<div class="stats-leader-list">'+rows.map((r,i)=>{
        const meta=[r.team,r.gp!==null&&r.gp!==undefined&&r.gp!==''?(r.gp+' GP'):''].filter(Boolean).join(' · ');
        const value=r.displayValue!==undefined&&r.displayValue!==null&&r.displayValue!==''?r.displayValue:(r.value!==undefined&&r.value!==null?r.value:'—');
        return '<div class="stats-leader-row"><span class="stats-rank">'+(i+1)+'</span><span class="stats-player"><strong>'+esc(r.player||'')+'</strong>'+(meta?'<small>'+esc(meta)+'</small>':'')+'</span><b>'+esc(value)+' <small>'+esc(group.suffix||'')+'</small></b></div>';
      }).join('')+'</div></article>';
  }).join('');

  const g=data.latestGame||{};
  const teams=Array.isArray(g.teams)?g.teams:[];
  const totals=g.teamTotals||{};
  const compareKeys=[
    ['PTS','pts'],['FG%','fgPct'],['3P%','threePtPct'],['FT%','ftPct'],
    ['REB','reb'],['AST','ast'],['STL','stl'],['BLK','blk'],['TO','to']
  ];
  let compare='';
  if(teams.length>=2){
    const a=teams[0],b=teams[1];
    compare='<div class="stats-game-head"><div><strong>'+esc(a)+'</strong><b>'+esc(g.scores?.[a]??totals[a]?.pts??'—')+'</b></div><span>'+esc(g.dateText||'Latest final')+'</span><div><b>'+esc(g.scores?.[b]??totals[b]?.pts??'—')+'</b><strong>'+esc(b)+'</strong></div></div>'+
      '<div class="stats-compare">'+compareKeys.map(([label,statKey])=>
        '<div class="stats-compare-row"><b>'+esc(totals[a]?.[statKey]??'—')+'</b><span>'+esc(label)+'</span><b>'+esc(totals[b]?.[statKey]??'—')+'</b></div>'
      ).join('')+'</div>';
  }

  const topPlayers=teams.flatMap(team=>(g.players?.[team]||[]).map(p=>({...p,team})))
    .sort((a,b)=>(b.pts||0)-(a.pts||0)).slice(0,8);
  const box=topPlayers.length?
    '<div class="stats-box-table"><div class="stats-box-row stats-box-head"><span>Player</span><b>PTS</b><b>REB</b><b>AST</b><b>STL</b><b>BLK</b></div>'+
      topPlayers.map(p=>'<div class="stats-box-row"><span><strong>'+esc(p.player)+'</strong><small>'+esc(p.team)+'</small></span><b>'+esc(p.pts)+'</b><b>'+esc(p.reb)+'</b><b>'+esc(p.ast)+'</b><b>'+esc(p.stl)+'</b><b>'+esc(p.blk)+'</b></div>').join('')+
    '</div>':'';

  const league=data.league||liveNowLabels[key]?.league||key.toUpperCase();
  const source=data.sourceName?(' · '+data.sourceName):'';
  const statsPanelId='stats-panel-'+String(key).replace(/[^a-z0-9_-]/gi,'-');
  const groupCount=groups.length;
  return '<section class="league-games-group sports-statistics" aria-label="'+esc(league)+' statistics">'+
    '<button type="button" class="stats-dropdown-toggle" data-stats-toggle aria-expanded="false" aria-controls="'+esc(statsPanelId)+'">'+
      '<span class="stats-dropdown-copy"><span class="stats-dropdown-kicker">Player leaders</span><strong>Statistics</strong><small>'+esc(data.season||league)+esc(source)+'</small></span>'+
      '<span class="stats-dropdown-side"><span class="stats-dropdown-count">'+esc(groupCount)+' '+(groupCount===1?'category':'categories')+'</span><span class="stats-dropdown-chevron" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg></span></span>'+
    '</button>'+
    '<div id="'+esc(statsPanelId)+'" class="stats-dropdown-content">'+
      '<div class="stats-dropdown-inner">'+
        '<div class="stats-leader-grid">'+leaderHtml+'</div>'+
        (compare?'<div class="stats-subhead"><h4>Latest Box Score</h4><span>'+esc(g.venue||'')+'</span></div>'+compare+box:'')+
      '</div>'+
    '</div>'+
  '</section>';
}
function leagueStandingsMarkup({id,title='Standings',subtitle='',ariaLabel='League standings',rows=[]}={}){
  if(!Array.isArray(rows)||!rows.length)return'';
  const panelId='standings-panel-'+String(id||title).replace(/[^a-z0-9_-]/gi,'-');
  return '<section class="league-games-group league-standings league-standings-dropdown" aria-label="'+esc(ariaLabel)+'">'+
    '<button type="button" class="standings-dropdown-toggle" data-standings-toggle aria-expanded="false" aria-controls="'+esc(panelId)+'">'+
      '<span class="standings-dropdown-copy"><span class="standings-dropdown-kicker">League table</span><strong>'+esc(title)+'</strong><small>'+esc(subtitle)+'</small></span>'+
      '<span class="standings-dropdown-side"><span class="standings-dropdown-count">'+esc(rows.length)+' '+(rows.length===1?'team':'teams')+'</span><span class="standings-dropdown-chevron" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg></span></span>'+
    '</button>'+
    '<div id="'+esc(panelId)+'" class="standings-dropdown-content">'+
      '<div class="standings-dropdown-inner">'+
        '<div class="league-standings-head"><span>Team</span><b>W</b><b>L</b></div>'+
        '<div class="league-standings-body">'+rows.map(s=>'<div class="league-standings-row"><strong>'+esc(s.team)+'</strong><b>'+esc(s.wins)+'</b><b>'+esc(s.losses)+'</b></div>').join('')+'</div>'+
      '</div>'+
    '</div>'+
  '</section>';
}

function wtaRankingsMarkup(data){
  const rankings=Array.isArray(data?.rankings)?data.rankings:[];
  const race=Array.isArray(data?.race)?data.race:[];
  if(!rankings.length&&!race.length)return'';
  const panelId='wta-rankings-panel';
  const table=(rows,label)=>'<div class="wta-ranking-table">'+
    '<div class="wta-ranking-table-title">'+esc(label)+'</div>'+
    '<div class="wta-ranking-head"><span>Rank</span><span>Player</span><span>Country</span><b>Points</b></div>'+
    '<div class="wta-ranking-body">'+rows.slice(0,20).map(r=>
      '<div class="wta-ranking-row">'+
        '<span class="wta-rank">'+esc(r.rank)+'</span>'+
        '<strong>'+esc(r.player)+(r.qualified?' <em>Q</em>':'')+'</strong>'+
        '<span>'+esc(r.country||'')+'</span>'+
        '<b>'+esc(Number(r.points||0).toLocaleString())+'</b>'+
      '</div>'
    ).join('')+'</div>'+
  '</div>';
  return '<section class="league-games-group league-standings-dropdown wta-rankings-dropdown" aria-label="WTA rankings">'+
    '<button type="button" class="standings-dropdown-toggle" data-standings-toggle aria-expanded="false" aria-controls="'+panelId+'">'+
      '<span class="standings-dropdown-copy"><span class="standings-dropdown-kicker">Official WTA data</span><strong>Rankings</strong><small>PIF Singles Rankings · Race to the WTA Finals · '+esc(data?.rankingsUpdated||'Current')+'</small></span>'+
      '<span class="standings-dropdown-side"><span class="standings-dropdown-count">'+esc(rankings.length)+' players</span><span class="standings-dropdown-chevron" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg></span></span>'+
    '</button>'+
    '<div id="'+panelId+'" class="standings-dropdown-content"><div class="standings-dropdown-inner">'+
      '<div class="wta-ranking-grid">'+table(rankings,'World Singles')+table(race,'Race to Finals')+'</div>'+
    '</div></div>'+
  '</section>';
}

function combatTitleholdersMarkup(key){
  const data=specialSportsDataCache?.leagues?.[key]||{};
  const rows=Array.isArray(data.titleholders)?data.titleholders:[];
  if(!rows.length)return'';
  const label=key==='one'?'ONE Championship':'UFC';
  const panelId='combat-titleholders-'+key;
  return '<section class="league-games-group league-standings-dropdown combat-titleholders-dropdown" aria-label="'+esc(label)+' titleholders">'+
    '<button type="button" class="standings-dropdown-toggle" data-standings-toggle aria-expanded="false" aria-controls="'+panelId+'">'+
      '<span class="standings-dropdown-copy"><span class="standings-dropdown-kicker">World champions</span><strong>Titleholders</strong><small>'+esc(label)+' · '+esc(data.titleholdersUpdated||'Current')+'</small></span>'+
      '<span class="standings-dropdown-side"><span class="standings-dropdown-count">'+esc(rows.length)+' '+(rows.length===1?'champion':'champions')+'</span><span class="standings-dropdown-chevron" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg></span></span>'+
    '</button>'+
    '<div id="'+panelId+'" class="standings-dropdown-content"><div class="standings-dropdown-inner">'+
      '<div class="combat-titleholder-list">'+rows.map(r=>
        '<article class="combat-titleholder-row">'+
          '<div><strong>'+esc(r.champion)+'</strong>'+(r.interim?'<span class="combat-titleholder-interim">Interim</span>':'')+'</div>'+
          '<small>'+esc(r.division)+'</small>'+
        '</article>'
      ).join('')+'</div>'+
    '</div></div>'+
  '</section>';
}

const boxingTitleWeightOrder=[
  ['Heavyweight',['heavyweight']],
  ['Bridgerweight',['bridgerweight']],
  ['Cruiserweight',['cruiserweight']],
  ['Light Heavyweight',['light heavyweight','light-heavyweight']],
  ['Super Middleweight',['super middleweight','super-middleweight']],
  ['Middleweight',['middleweight']],
  ['Super Welterweight',['super welterweight','junior middleweight','jr middleweight']],
  ['Welterweight',['welterweight']],
  ['Super Lightweight',['super lightweight','junior welterweight','jr welterweight']],
  ['Lightweight',['lightweight']],
  ['Super Featherweight',['super featherweight','junior lightweight','jr lightweight']],
  ['Featherweight',['featherweight']],
  ['Super Bantamweight',['super bantamweight','junior featherweight','jr featherweight']],
  ['Bantamweight',['bantamweight']],
  ['Super Flyweight',['super flyweight','junior bantamweight','jr bantamweight']],
  ['Flyweight',['flyweight']],
  ['Junior Flyweight',['junior flyweight','light flyweight','jr flyweight']],
  ['Minimumweight',['minimumweight','strawweight']]
];
function boxingWeightClass(game){
  if(game?.weightClass)return String(game.weightClass);
  const text=String(game?.title||'').toLowerCase();
  let best={label:'Other',index:999,length:-1};
  boxingTitleWeightOrder.forEach(([label,aliases],index)=>{
    aliases.forEach(alias=>{
      if(text.includes(alias)&&alias.length>best.length)best={label,index,length:alias.length};
    });
  });
  return best.label;
}
function boxingWeightIndex(game){
  if(Number.isFinite(Number(game?.weightOrder))&&Number(game.weightOrder)!==999)return Number(game.weightOrder);
  const label=boxingWeightClass(game);
  const i=boxingTitleWeightOrder.findIndex(([name])=>name===label);
  return i>=0?i:999;
}
function boxingTitleholderName(game){
  return String(game?.title||'').split(' — ')[0].trim()||'Titleholder';
}
function boxingTitleholdersMarkup(items,leagueName,key){
  if(!Array.isArray(items)||!items.length)return'';
  const sorted=[...items].sort((a,b)=>boxingWeightIndex(a)-boxingWeightIndex(b)||String(a.title||'').localeCompare(String(b.title||'')));
  const groups=[];
  for(const item of sorted){
    const weight=boxingWeightClass(item);
    let group=groups.find(g=>g.weight===weight);
    if(!group){group={weight,items:[]};groups.push(group)}
    group.items.push(item);
  }
  const panelId='boxing-titleholders-'+String(key||leagueName).replace(/[^a-z0-9_-]/gi,'-');
  return '<section class="league-games-group league-standings-dropdown boxing-titleholders-dropdown" aria-label="'+esc(leagueName)+' titleholders">'+
    '<button type="button" class="standings-dropdown-toggle boxing-titleholders-toggle" data-standings-toggle aria-expanded="false" aria-controls="'+esc(panelId)+'">'+
      '<span class="standings-dropdown-copy"><span class="standings-dropdown-kicker">Champions by weight</span><strong>Titleholders</strong><small>Heavyweight to minimumweight</small></span>'+
      '<span class="standings-dropdown-side"><span class="standings-dropdown-count">'+esc(sorted.length)+' '+(sorted.length===1?'champion':'champions')+'</span><span class="standings-dropdown-chevron" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg></span></span>'+
    '</button>'+
    '<div id="'+esc(panelId)+'" class="standings-dropdown-content">'+
      '<div class="standings-dropdown-inner boxing-titleholders-inner">'+
        groups.map(group=>'<section class="boxing-weight-group"><div class="boxing-weight-heading"><strong>'+esc(group.weight)+'</strong><span>'+esc(group.items.length)+'</span></div><div class="boxing-weight-list">'+
          group.items.map(item=>{
            const champion=boxingTitleholderName(item);
            const full=String(item.title||'');
            const belt=full.includes(' — ')?full.split(' — ').slice(1).join(' — '):leagueName+' champion';
            return '<article class="boxing-titleholder-row"><div><strong>'+esc(champion)+'</strong><small>'+esc(belt)+'</small></div><span>'+esc(item.location||'Current champion')+'</span></article>';
          }).join('')+
        '</div></section>').join('')+
      '</div>'+
    '</div>'+
  '</section>';
}

const regionalWebSnapshots={
  pba:{
    league:'PBA',
    season:"2026 Governors' Cup",
    coverage:'Web-verified schedule and results snapshot · updated September 21, 2026',
    note:"The PBA Governors' Cup is on its Asian Games break and is scheduled to resume October 7.",
    sources:[
      {name:'PBA Official',url:'https://pba.ph/'},
      {name:'SkedCheck',url:'https://skedcheck.com/pba-games-schedule-scores/'}
    ],
    games:[
      {eventId:'web-pba-20261007-1',date:'2026-10-07T17:15:00+08:00',displayTime:'Oct 7 · 5:15 PM',away:'NLEX Road Warriors',home:'Macau Black Knights',awayScore:'—',homeScore:'—',status:'Scheduled',state:'scheduled',sourceName:'SkedCheck',sourceUrl:'https://skedcheck.com/pba-games-schedule-scores/'},
      {eventId:'web-pba-20261007-2',date:'2026-10-07T19:30:00+08:00',displayTime:'Oct 7 · 7:30 PM',away:'Terrafirma Dyip',home:'TNT Tropang 5G',awayScore:'—',homeScore:'—',status:'Scheduled',state:'scheduled',sourceName:'SkedCheck',sourceUrl:'https://skedcheck.com/pba-games-schedule-scores/'},
      {eventId:'web-pba-20261009-1',date:'2026-10-09T17:15:00+08:00',displayTime:'Oct 9 · 5:15 PM',away:'Blackwater Bossing',home:'Magnolia Hotshots',awayScore:'—',homeScore:'—',status:'Scheduled',state:'scheduled',sourceName:'SkedCheck',sourceUrl:'https://skedcheck.com/pba-games-schedule-scores/'},
      {eventId:'web-pba-20261009-2',date:'2026-10-09T19:30:00+08:00',displayTime:'Oct 9 · 7:30 PM',away:'Barangay Ginebra',home:'Rain or Shine',awayScore:'—',homeScore:'—',status:'Scheduled',state:'scheduled',sourceName:'SkedCheck',sourceUrl:'https://skedcheck.com/pba-games-schedule-scores/'},
      {eventId:'web-pba-20260814-1',date:'2026-08-14T17:15:00+08:00',displayTime:'Aug 14 · Final',away:'NLEX Road Warriors',home:'Converge FiberXers',awayScore:'110',homeScore:'112',status:'Final',state:'final',sourceName:'SkedCheck',sourceUrl:'https://skedcheck.com/pba-games-schedule-scores/'},
      {eventId:'web-pba-20260814-2',date:'2026-08-14T19:30:00+08:00',displayTime:'Aug 14 · Final',away:'Barangay Ginebra',home:'Meralco Bolts',awayScore:'88',homeScore:'97',status:'Final',state:'final',sourceName:'SkedCheck',sourceUrl:'https://skedcheck.com/pba-games-schedule-scores/'},
      {eventId:'web-pba-20260812-1',date:'2026-08-12T17:15:00+08:00',displayTime:'Aug 12 · Final',away:'Titan Ultra Giant Risers',home:'San Miguel Beermen',awayScore:'113',homeScore:'143',status:'Final',state:'final',sourceName:'SkedCheck',sourceUrl:'https://skedcheck.com/pba-games-schedule-scores/'},
      {eventId:'web-pba-20260812-2',date:'2026-08-12T19:30:00+08:00',displayTime:'Aug 12 · Final',away:'Phoenix Fuel Masters',home:'Magnolia Hotshots',awayScore:'101',homeScore:'115',status:'Final',state:'final',sourceName:'SkedCheck',sourceUrl:'https://skedcheck.com/pba-games-schedule-scores/'}
    ]
  },
  mpbl:{
    league:'MPBL',
    season:'2026 Season',
    coverage:'Web-verified fixtures and recent results · updated September 21, 2026',
    note:'Only fixtures corroborated by current public schedule sources are shown.',
    sources:[
      {name:'MPBL Official',url:'https://mpbl.com.ph/'},
      {name:'Flashscore',url:'https://www.flashscore.ph/en/basketball/philippines/mpbl/fixtures/'},
      {name:'Forebet',url:'https://www.forebet.com/en/basketball/philippines/mpbl/results'}
    ],
    games:[
      {eventId:'web-mpbl-20260921-1',date:'2026-09-21T12:00:00+08:00',displayTime:'Sep 21 · Scheduled',away:'Sarangani Marlins',home:'Imus Braderhood',awayScore:'—',homeScore:'—',status:'Scheduled',state:'scheduled',sourceName:'Flashscore',sourceUrl:'https://www.flashscore.ph/en/basketball/philippines/mpbl/fixtures/'},
      {eventId:'web-mpbl-20260921-2',date:'2026-09-21T14:00:00+08:00',displayTime:'Sep 21 · Scheduled',away:'Rizal Golden Coolers',home:'Quezon Huskers',awayScore:'—',homeScore:'—',status:'Scheduled',state:'scheduled',sourceName:'Flashscore',sourceUrl:'https://www.flashscore.ph/en/basketball/philippines/mpbl/fixtures/'},
      {eventId:'web-mpbl-20260921-3',date:'2026-09-21T16:00:00+08:00',displayTime:'Sep 21 · Scheduled',away:'Bulacan Kuyas',home:'GenSan Warriors',awayScore:'—',homeScore:'—',status:'Scheduled',state:'scheduled',sourceName:'Flashscore',sourceUrl:'https://www.flashscore.ph/en/basketball/philippines/mpbl/fixtures/'},
      {eventId:'web-mpbl-20260922-1',date:'2026-09-22T12:00:00+08:00',displayTime:'Sep 22 · Scheduled',away:'Batang Kankaloo',home:'Zamboanga Sikat',awayScore:'—',homeScore:'—',status:'Scheduled',state:'scheduled',sourceName:'Flashscore',sourceUrl:'https://www.flashscore.ph/en/basketball/philippines/mpbl/fixtures/'},
      {eventId:'web-mpbl-20260922-2',date:'2026-09-22T14:00:00+08:00',displayTime:'Sep 22 · Scheduled',away:'Pasay Voyagers',home:'Pasig City',awayScore:'—',homeScore:'—',status:'Scheduled',state:'scheduled',sourceName:'Flashscore',sourceUrl:'https://www.flashscore.ph/en/basketball/philippines/mpbl/fixtures/'},
      {eventId:'web-mpbl-20260918-1',date:'2026-09-18T18:00:00+08:00',displayTime:'Sep 18 · Final',away:'GenSan Warriors',home:'Batangas City',awayScore:'73',homeScore:'76',status:'Final',state:'final',sourceName:'Forebet',sourceUrl:'https://www.forebet.com/en/basketball/philippines/mpbl/results'},
      {eventId:'web-mpbl-20260918-2',date:'2026-09-18T20:00:00+08:00',displayTime:'Sep 18 · Final',away:'Marikina Shoemasters',home:'Bulacan Kuyas',awayScore:'77',homeScore:'84',status:'Final',state:'final',sourceName:'Forebet',sourceUrl:'https://www.forebet.com/en/basketball/philippines/mpbl/results'},
      {eventId:'web-mpbl-20260915-1',date:'2026-09-15T18:00:00+08:00',displayTime:'Sep 15 · Final',away:'Zamboanga Sikat',home:'Quezon Huskers',awayScore:'67',homeScore:'86',status:'Final',state:'final',sourceName:'Forebet',sourceUrl:'https://www.forebet.com/en/basketball/philippines/mpbl/results'},
      {eventId:'web-mpbl-20260915-2',date:'2026-09-15T20:00:00+08:00',displayTime:'Sep 15 · Final',away:'Bulacan Kuyas',home:'San Juan Knights',awayScore:'67',homeScore:'120',status:'Final',state:'final',sourceName:'Forebet',sourceUrl:'https://www.forebet.com/en/basketball/philippines/mpbl/results'}
    ]
  },
  nbl:{
    league:'NBL-Pilipinas',
    season:"2026 Governor's Cup",
    coverage:'Verified public game records and official broadcasts · updated September 21, 2026',
    note:'NBL-Pilipinas does not expose a complete machine-readable current schedule. IMG shows only matchups and scores confirmed by accessible public sources; unknown scores are left blank.',
    sources:[
      {name:'NBL Pilipinas Official YouTube',url:'https://www.youtube.com/channel/UCJDBLldRGVJPEvyjJdSHefw'},
      {name:'NBL public updates',url:'https://www.findglocal.com/PH/Cabuyao/1997682720482608/NBL-Pilipinas'},
      {name:'Pangasinan Provincial Government',url:'https://www.pangasinan.gov.ph/asinderos-crush-granary-buffalos-129-110-in-nbl-pilipinas-governors-cup/'}
    ],
    games:[
      {eventId:'web-nbl-20260911',date:'2026-09-11T18:00:00+08:00',displayTime:'Sep 11 · Official replay',away:'CamSur Express',home:'Pangasinan Asinderos',awayScore:'—',homeScore:'—',status:'Replay available',state:'final',sourceName:'NBL Pilipinas',sourceUrl:'https://www.youtube.com/watch?v=fgViW-UbnIg'},
      {eventId:'web-nbl-20260908',date:'2026-09-08T18:00:00+08:00',displayTime:'Sep 8 · Official replay',away:'Zamboanga Valientes',home:'Quezon City',awayScore:'—',homeScore:'—',status:'Replay available',state:'final',sourceName:'NBL Pilipinas',sourceUrl:'https://www.youtube.com/watch?v=slZmVgsJxDQ'},
      {eventId:'web-nbl-20260830',date:'2026-08-30T18:00:00+08:00',displayTime:'Aug 30 · Final',away:'TIKAS Kapampangan',home:'Quezon Starhorse',awayScore:'84',homeScore:'87',status:'Final',state:'final',sourceName:'NBL public update',sourceUrl:'https://www.findglocal.com/PH/Cabuyao/1997682720482608/NBL-Pilipinas'},
      {eventId:'web-nbl-20260817',date:'2026-08-17T18:00:00+08:00',displayTime:'Aug 17 · Final',away:'Nueva Ecija Granary Buffalos',home:'Pangasinan Asinderos',awayScore:'110',homeScore:'129',status:'Final',state:'final',sourceName:'Province of Pangasinan',sourceUrl:'https://www.pangasinan.gov.ph/asinderos-crush-granary-buffalos-129-110-in-nbl-pilipinas-governors-cup/'}
    ]
  }
};
function regionalSnapshotGames(sport){
  const snapshot=getRegionalSnapshot(sport);
  return snapshot?(snapshot.games||[]).map(g=>({...g,homeLogo:g.homeLogo||'',awayLogo:g.awayLogo||'',odds:null,oddsList:[],highlights:Array.isArray(g.highlights)?g.highlights:[],highlightsChecked:true,streams:Array.isArray(g.streams)?g.streams:[],streamsChecked:Boolean(g.streamsChecked||Array.isArray(g.streams))})):[];
}
function renderRegionalContext(){const host=document.getElementById('leagueContext');if(host){host.innerHTML='';host.hidden=true;}}

const oddsFeeds={
  nfl:'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard',
  ncaaf:'https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard',
  nba:'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard',
  wnba:'https://site.api.espn.com/apis/site/v2/sports/basketball/wnba/scoreboard',
  ncaam:'https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard',
  mlb:'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard',
  nhl:'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard',
  epl:'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard',
  laliga:'https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard',
  seriea:'https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard',
  bundesliga:'https://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/scoreboard',
  ligue1:'https://site.api.espn.com/apis/site/v2/sports/soccer/fra.1/scoreboard',
  champions:'https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard',
  mls:'https://site.api.espn.com/apis/site/v2/sports/soccer/usa.1/scoreboard'
};let allGames=[];const liveStreamCache=new Map();
const oddsLogoSportKey={nfl:'football',ncaaf:'ncaaf',nba:'basketball',wnba:'wnba',mlb:'baseball',nhl:'hockey',epl:'soccer',laliga:'laliga',seriea:'seriea',bundesliga:'bundesliga',champions:'champions'};
const oddsLeagueNames={nfl:'NFL',ncaaf:'NCAA Football',nba:'NBA',wnba:'WNBA',ncaam:"NCAA Men's Basketball",mlb:'MLB',nhl:'NHL',epl:'Premier League',laliga:'La Liga',seriea:'Serie A',bundesliga:'Bundesliga',ligue1:'Ligue 1',champions:'UEFA Champions League',mls:'MLS'};
const oddsLeagueSports={nfl:'American Football',ncaaf:'American Football',nba:'Basketball',wnba:'Basketball',ncaam:'Basketball',mlb:'Baseball',nhl:'Hockey',epl:'Football',laliga:'Football',seriea:'Football',bundesliga:'Football',ligue1:'Football',champions:'Football',mls:'Football'};
let availableOdds={},oddsLeagueLogos={},currentOddsSport='all',currentOddsLeague='',oddsLeaguePanelOpen=false,oddsLeaguePanelTimer=0;
function mapOdds(o){return{provider:o.provider?.displayName||o.provider?.name||'Odds provider',details:o.details||'—',total:o.overUnder??'—',home:o.moneyline?.home?.close?.odds||'—',away:o.moneyline?.away?.close?.odds||'—',draw:o.moneyline?.draw?.close?.odds||'—'}}function teamLogoUrl(team){return team?.team?.logo||team?.team?.logos?.[0]?.href||team?.logo||team?.logos?.[0]?.href||''}
function teamLogoMarkup(url,name,extraClass=''){return url?'<img class="team-logo '+extraClass+'" src="'+esc(url)+'" alt="'+esc(name)+' logo" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.remove()">':''}

const teamDirectoryFeeds={
  soccer:'soccer/eng.1',
  laliga:'soccer/esp.1',
  seriea:'soccer/ita.1',
  bundesliga:'soccer/ger.1',
  champions:'soccer/uefa.champions',
  mls:'soccer/usa.1',
  basketball:'basketball/nba',
  wnba:'basketball/wnba',
  nblaus:'basketball/nbl',
  ipl:'cricket/ipl',
  volleyball_w:'volleyball/fivb.w',
  volleyball_m:'volleyball/fivb.m',
  baseball:'baseball/mlb',
  hockey:'hockey/nhl',
  football:'football/nfl',
  ncaaf:'football/college-football'
};
const teamLogoDirectoryCache=new Map();

const verifiedTeamLogoOverrides={
  pba:{
    'barangay ginebra':'https://statsspace01.sgp1.digitaloceanspaces.com/basketball_organizer/images/845go3mfbdxvlmrxq4jnv93ema08',
    'barangay ginebra san miguel':'https://statsspace01.sgp1.digitaloceanspaces.com/basketball_organizer/images/845go3mfbdxvlmrxq4jnv93ema08',
    'converge fiberxers':'https://statsspace01.sgp1.digitaloceanspaces.com/organizer/teams/5/logo_L1.png',
    'meralco bolts':'https://statsspace01.sgp1.digitaloceanspaces.com/basketball_organizer/images/5rg0jlac21fve9xix02wncz1t1uy',
    'nlex road warriors':'https://statsspace01.sgp1.digitaloceanspaces.com/basketball_organizer/images/b72j58tho2ipkl065bemw71n9byl',
    'tnt tropang 5g':'https://statsspace01.sgp1.digitaloceanspaces.com/basketball_organizer/images/6a0o355pjdq3syfi83969r81dqp6',
    'terrafirma dyip':'https://statsspace01.sgp1.digitaloceanspaces.com/basketball_organizer/images/oscegdylau0xy1al87thv9grww4h'
  }
};

const regionalWikiTeamTitles={
  pba:{
    'macau black knights':'Macau Black Knights'
  },
  mpbl:{
    'batang kankaloo':'Caloocan Batang Kankaloo',
    'batangas city':'Batangas City Tanduay Rum Masters',
    'bulacan kuyas':'Bulacan Kuyas',
    'gensan warriors':'General Santos Warriors',
    'imus braderhood':'Imus Bandera',
    'marikina shoemasters':'Marikina Shoemasters',
    'quezon huskers':'Quezon Huskers',
    'rizal golden coolers':'Rizal Golden Coolers',
    'sarangani marlins':'Sarangani Marlins'
  },
  vba:{
    'hanoi buffaloes':'Hanoi Buffaloes',
    'saigon heat':'Saigon Heat',
    'nhatrang dolphins':'Nha Trang Dolphins',
    'ho chi minh city wings':'Ho Chi Minh City Wings'
  }
};
const regionalWikiLogoCache=new Map();

function normalizeTeamLogoKey(name){
  return String(name||'').toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/&/g,' and ').replace(/[^a-z0-9]+/g,' ').trim();
}

function addTeamLogoAliases(map,team,logo){
  if(!logo)return;
  const names=[
    team?.displayName,team?.shortDisplayName,team?.name,team?.abbreviation,
    [team?.location,team?.name].filter(Boolean).join(' ')
  ].filter(Boolean);
  names.forEach(name=>map.set(normalizeTeamLogoKey(name),logo));
}

const teamNameLogoAliases={
  soccer:{
    'arsenal fc':'arsenal',
    'brentford fc':'brentford',
    'chelsea fc':'chelsea',
    'everton fc':'everton',
    'fulham fc':'fulham',
    'liverpool fc':'liverpool',
    'sunderland afc':'sunderland',
    'brighton and hove albion':'brighton hove albion'
  },
  laliga:{
    'real sociedad san sebastian':'real sociedad',
    'espanyol barcelona':'espanyol',
    'athletic bilbao':'athletic club',
    'deportivo alaves':'alaves',
    'getafe cf':'getafe',
    'villarreal cf':'villarreal',
    'rc celta de vigo':'celta vigo',
    'ca osasuna':'osasuna',
    'real betis seville':'real betis',
    'valencia cf':'valencia',
    'sevilla fc':'sevilla',
    'levante ud':'levante',
    'fc barcelona':'barcelona',
    'malaga cf':'malaga'
  }
};

function teamLogoTokens(name){
  const noise=new Set(['fc','cf','afc','sc','ac','rc','rcd','cd','ud','club','the','de']);
  return normalizeTeamLogoKey(name).split(' ').filter(Boolean).filter(x=>!noise.has(x));
}

function findTeamLogoInDirectory(sport,directory,name){
  if(!directory?.size||!name)return'';
  const normalized=normalizeTeamLogoKey(name);
  const alias=teamNameLogoAliases[sport]?.[normalized];
  if(alias){
    const hit=directory.get(normalizeTeamLogoKey(alias));
    if(hit)return hit;
  }
  const exact=directory.get(normalized);
  if(exact)return exact;

  const target=teamLogoTokens(name);
  if(!target.length)return'';
  let best='',bestScore=0;
  for(const [key,logo] of directory){
    const candidate=teamLogoTokens(key);
    if(!candidate.length)continue;
    const common=target.filter(x=>candidate.includes(x));
    if(!common.length)continue;
    const score=(2*common.length)/(target.length+candidate.length);
    const firstMatch=target[0]===candidate[0];
    if(score>bestScore&&(score>=.72||(score>=.62&&firstMatch)||(common.length>=2&&score>=.58))){
      bestScore=score;
      best=logo;
    }
  }
  return best;
}

async function getTeamLogoDirectory(sport){
  if(teamLogoDirectoryCache.has(sport))return teamLogoDirectoryCache.get(sport);
  const path=teamDirectoryFeeds[sport];
  if(!path){teamLogoDirectoryCache.set(sport,new Map());return teamLogoDirectoryCache.get(sport);}
  try{
    const r=await fetch('https://site.api.espn.com/apis/site/v2/sports/'+path+'/teams?limit=500',{cache:'force-cache'});
    if(!r.ok)throw 0;
    const j=await r.json();
    const list=j?.sports?.[0]?.leagues?.[0]?.teams||[];
    const map=new Map();
    list.forEach(x=>{
      const t=x?.team||x;
      const logo=t?.logos?.[0]?.href||t?.logo||'';
      addTeamLogoAliases(map,t,logo);
    });
    teamLogoDirectoryCache.set(sport,map);
    return map;
  }catch{
    const map=new Map();
    teamLogoDirectoryCache.set(sport,map);
    return map;
  }
}

async function getRegionalWikiLogoMap(sport,names){
  const titleMap=regionalWikiTeamTitles[sport]||{};
  const pairs=[...new Set((names||[]).map(name=>normalizeTeamLogoKey(name)).filter(key=>titleMap[key]))]
    .map(key=>[key,titleMap[key]]);
  if(!pairs.length)return new Map();

  const result=new Map();
  const missing=[];
  for(const [key,title] of pairs){
    const cacheKey=sport+':'+key;
    if(regionalWikiLogoCache.has(cacheKey)){
      const hit=regionalWikiLogoCache.get(cacheKey);
      if(hit)result.set(key,hit);
    }else missing.push([key,title]);
  }
  if(!missing.length)return result;

  try{
    const titles=[...new Set(missing.map(([,title])=>title))];
    const url='https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&piprop=thumbnail|original&pithumbsize=160&format=json&origin=*&titles='+encodeURIComponent(titles.join('|'));
    const r=await fetch(url,{cache:'force-cache'});
    if(!r.ok)throw 0;
    const j=await r.json();
    const byTitle=new Map(Object.values(j?.query?.pages||{}).map(page=>[
      normalizeTeamLogoKey(page?.title),
      page?.thumbnail?.source||page?.original?.source||''
    ]));
    for(const [key,title] of missing){
      const logo=byTitle.get(normalizeTeamLogoKey(title))||'';
      regionalWikiLogoCache.set(sport+':'+key,logo);
      if(logo)result.set(key,logo);
    }
  }catch{
    missing.forEach(([key])=>regionalWikiLogoCache.set(sport+':'+key,''));
  }
  return result;
}

async function hydrateTeamLogos(sport,games){
  if(!Array.isArray(games)||!games.length)return games;
  const overrides=verifiedTeamLogoOverrides[sport]||{};
  for(const g of games){
    if(!g.awayLogo)g.awayLogo=overrides[normalizeTeamLogoKey(g.away)]||'';
    if(!g.homeLogo)g.homeLogo=overrides[normalizeTeamLogoKey(g.home)]||'';
  }

  const directory=await getTeamLogoDirectory(sport);
  for(const g of games){
    if(!g.awayLogo)g.awayLogo=findTeamLogoInDirectory(sport,directory,g.away);
    if(!g.homeLogo)g.homeLogo=findTeamLogoInDirectory(sport,directory,g.home);
  }

  const unresolved=games.flatMap(g=>[
    !g.awayLogo?g.away:'',
    !g.homeLogo?g.home:''
  ]).filter(Boolean);
  if(unresolved.length){
    const wiki=await getRegionalWikiLogoMap(sport,unresolved);
    for(const g of games){
      if(!g.awayLogo)g.awayLogo=wiki.get(normalizeTeamLogoKey(g.away))||'';
      if(!g.homeLogo)g.homeLogo=wiki.get(normalizeTeamLogoKey(g.home))||'';
    }
  }
  return games;
}
async function getNbaLogoMap(){try{const r=await fetch('https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams?limit=100',{cache:'force-cache'});if(!r.ok)return{};const j=await r.json(),list=j.sports?.[0]?.leagues?.[0]?.teams||[];return Object.fromEntries(list.flatMap(x=>{const t=x.team||x,names=[t.displayName,t.name,t.shortDisplayName].filter(Boolean),logo=t.logos?.[0]?.href||t.logo||'';return names.map(n=>[String(n).toLowerCase(),logo])}))}catch{return{}}}
function summaryUrlForGame(sport,eventId){const feed=scoreFeeds[sport];return feed&&eventId?feed.replace(/\/scoreboard(?:\?.*)?$/,'/summary?event='+encodeURIComponent(eventId)):''}
function collectMediaUrls(node,out=[]){if(!node)return out;if(typeof node==='string'){if(/^https?:\/\//i.test(node))out.push(node);return out}if(Array.isArray(node)){node.forEach(x=>collectMediaUrls(x,out));return out}if(typeof node==='object'){for(const [k,val] of Object.entries(node)){if(['href','url','src'].includes(k)&&typeof val==='string'&&/^https?:\/\//i.test(val))out.push(val);else if(typeof val==='object')collectMediaUrls(val,out)}}return out}
function pickPlayableMedia(v){const pools=[v?.links?.source,v?.links?.mobile?.source,v?.links?.streaming,v?.source,v?.sources,v?.media,v?.playback].filter(Boolean),urls=[...new Set(pools.flatMap(x=>collectMediaUrls(x)))];const ranked=urls.sort((a,b)=>{const score=u=>/\.mp4(?:\?|$)/i.test(u)?3:/\.m3u8(?:\?|$)/i.test(u)?2:/video|motion|media/i.test(u)?1:0;return score(b)-score(a)});return ranked.find(u=>/\.mp4(?:\?|$)/i.test(u))||ranked.find(u=>/\.m3u8(?:\?|$)/i.test(u))||ranked[0]||''}
function normalizeHighlightVideo(v){const title=v?.headline||v?.title||v?.description||'Game highlight',thumb=v?.thumbnail||v?.image?.url||v?.images?.[0]?.url||v?.posterImage?.href||v?.poster?.href||'',media=pickPlayableMedia(v),sourceUrl=v?.links?.web?.href||v?.link?.href||v?.href||'';return title&&media?{title,thumb,media,sourceUrl}:null}
function uniqueHighlights(items){const seen=new Set();return items.filter(Boolean).filter(v=>{const key=v.url||v.title;if(seen.has(key))return false;seen.add(key);return true}).slice(0,8)}
function ensureHighlightsDialog(){let d=document.getElementById('highlightsDialog');if(d)return d;d=document.createElement('dialog');d.id='highlightsDialog';d.className='highlights-dialog';d.innerHTML='<div class="highlights-shell"><button class="highlights-close" type="button" aria-label="Close highlights"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg></button><div id="highlightsContent"></div></div>';document.body.append(d);d.addEventListener('click',e=>{if(e.target===d)d.close()});d.querySelector('.highlights-close').addEventListener('click',()=>d.close());d.addEventListener('close',()=>{const v=d.querySelector('#highlightPlayer');if(v){v.pause();v.removeAttribute('src');v.load()}});return d}
function playHighlightClip(index){const d=document.getElementById('highlightsDialog'),gId=d?.dataset?.gameId,g=allGames.find(x=>String(x.eventId)===String(gId));if(!d||!g||!g.highlights?.[index])return;const clip=g.highlights[index],video=d.querySelector('#highlightPlayer'),title=d.querySelector('#highlightNowTitle');if(!video)return;d.dataset.clipIndex=String(index);video.pause();video.poster=clip.thumb||'';video.src=clip.media;video.load();if(title)title.textContent=clip.title;d.querySelectorAll('[data-highlight-index]').forEach((el,i)=>el.classList.toggle('active',i===index));const p=video.play();if(p?.catch)p.catch(()=>{})}
function openHighlights(eventId){const g=allGames.find(x=>String(x.eventId)===String(eventId));if(!g||!g.highlights?.length)return;const d=ensureHighlightsDialog(),host=d.querySelector('#highlightsContent'),first=g.highlights[0];d.dataset.gameId=String(eventId);host.innerHTML='<div class="highlights-head"><h2>'+esc(g.away)+' vs '+esc(g.home)+'</h2><div class="highlight-teams"><span>'+teamLogoMarkup(g.awayLogo,g.away,'highlight-team-logo')+esc(g.away)+'</span><span>'+teamLogoMarkup(g.homeLogo,g.home,'highlight-team-logo')+esc(g.home)+'</span></div></div><div class="highlight-player-wrap"><video id="highlightPlayer" class="highlight-player" controls playsinline preload="metadata" poster="'+esc(first.thumb||'')+'"></video><div class="highlight-now"><strong id="highlightNowTitle">'+esc(first.title)+'</strong><span>ESPN highlight</span></div></div>'+(g.highlights.length>1?'<div class="highlight-playlist">'+g.highlights.map((v,i)=>'<button type="button" class="highlight-card '+(i===0?'active':'')+'" data-highlight-index="'+i+'"><div class="highlight-thumb">'+(v.thumb?'<img src="'+esc(v.thumb)+'" alt="" loading="lazy" referrerpolicy="no-referrer">':'<div class="highlight-placeholder"></div>')+'<span class="highlight-play" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span></div><div class="highlight-copy"><strong>'+esc(v.title)+'</strong><span>Play highlight</span></div></button>').join('')+'</div>':'');d.querySelectorAll('[data-highlight-index]').forEach(btn=>btn.addEventListener('click',()=>playHighlightClip(Number(btn.dataset.highlightIndex))));d.showModal();playHighlightClip(0)}
async function hydrateHighlights(sport){const snapshot=allGames,candidates=snapshot.filter(g=>g.eventId&&g.state!=='scheduled').slice(0,20);if(!candidates.length)return;await Promise.allSettled(candidates.map(async g=>{const url=summaryUrlForGame(sport,g.eventId);if(!url)return;try{const r=await fetch(url,{cache:'no-store'});if(!r.ok)return;const j=await r.json(),raw=[...(Array.isArray(j.videos)?j.videos:[]),...(Array.isArray(j.highlights)?j.highlights:[])];g.highlights=uniqueHighlights(raw.map(normalizeHighlightVideo));g.highlightsChecked=true}catch{g.highlights=[];g.highlightsChecked=true}}));if(allGames===snapshot&&currentScoreLeague===sport)renderGames()}

function ensureLiveDialog(){let d=document.getElementById('liveDialog');if(d)return d;d=document.createElement('dialog');d.id='liveDialog';d.className='live-dialog';d.innerHTML='<div class="live-shell"><button class="live-close" type="button" aria-label="Close live stream"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg></button><div id="liveContent"></div></div>';document.body.append(d);d.addEventListener('click',e=>{if(e.target===d)d.close()});d.querySelector('.live-close').addEventListener('click',()=>d.close());d.addEventListener('close',()=>{const frame=d.querySelector('iframe');if(frame)frame.src='about:blank'});return d}
function liveStreamsForGame(game){
  if(!game||!['live','scheduled'].includes(game.state))return [];
  return (Array.isArray(game.streams)?game.streams:[]).filter(stream=>{
    const deadline=Date.parse(stream?.expiresAt||'');
    if(Number.isFinite(deadline)&&Date.now()>=deadline)return false;
    if(game.state==='scheduled'&&stream?.status!=='upcoming'&&!stream?.scheduledStartTime)return false;
    try{
      const url=new URL(stream?.watchUrl||stream?.embedUrl||'');
      if(!['https:','http:'].includes(url.protocol))return false;
      const host=url.hostname.toLowerCase();
      if(host==='youtu.be')return /^\/[A-Za-z0-9_-]{11}\/?$/.test(url.pathname);
      if(host==='youtube.com'||host.endsWith('.youtube.com')||host==='youtube-nocookie.com'||host.endsWith('.youtube-nocookie.com')){
        return (url.pathname==='/watch'&&/^[A-Za-z0-9_-]{11}$/.test(url.searchParams.get('v')||''))||/^\/(live|embed)\/[A-Za-z0-9_-]{11}\/?$/.test(url.pathname);
      }
      return true;
    }catch{return false}
  });
}
function inlineStreamUrl(stream){
  const raw=stream?.embedUrl||stream?.watchUrl||'';
  if(!raw)return'';
  try{
    const u=new URL(raw,location.href);
    if(!['http:','https:'].includes(u.protocol))return'';
    const host=u.hostname.toLowerCase();
    let videoId='';
    if(host==='youtu.be')videoId=u.pathname.split('/').filter(Boolean)[0]||'';
    else if(host==='youtube.com'||host.endsWith('.youtube.com')||host==='youtube-nocookie.com'||host.endsWith('.youtube-nocookie.com')){
      videoId=u.searchParams.get('v')||((u.pathname.match(/\/(?:live|embed)\/([^/?]+)/)||[])[1]||'');
    }
    if(/^[A-Za-z0-9_-]{11}$/.test(videoId))return 'https://www.youtube-nocookie.com/embed/'+encodeURIComponent(videoId)+'?playsinline=1&rel=0';
    if(stream?.embedUrl)return u.href;
  }catch{}
  return'';
}
function selectedLeagueLiveStreamMarkup(key){
  const candidates=[
    ...liveNowItems.filter(g=>g.sportKey===key&&liveNowItemIsCurrent(g)),
    ...allGames.filter(g=>g.state==='live')
  ];
  const seen=new Set();
  for(const game of candidates){
    const eventKey=String(game.eventId||[game.date,game.away,game.home].join('|'));
    if(seen.has(eventKey))continue;
    seen.add(eventKey);
    const streams=liveStreamsForGame(game);
    if(!streams.length)continue;
    const stream=streams[0];
    const embed=inlineStreamUrl(stream);
    const league=liveNowLabels[key]?.league||game.leagueLabel||'Live';
    const matchup=game.title||[game.away,game.home].filter(Boolean).join(' vs ')||league+' Live';
    const source=stream.channel||stream.provider||'Official live stream';
    return '<section class="league-live-stream" aria-label="'+esc(league)+' live stream">'+
      '<div class="league-live-stream-head"><span><i aria-hidden="true"></i>LIVE STREAM</span><strong>'+esc(matchup)+'</strong><small>'+esc(source)+'</small></div>'+
      (embed?'<div class="league-live-stream-player"><iframe src="'+esc(embed)+'" title="'+esc(matchup)+' live stream" loading="lazy" allow="autoplay; encrypted-media; picture-in-picture; web-share" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div>':'')+
      '<button type="button" class="league-live-stream-action" data-live-event="'+esc(game.eventId)+'"><span class="live-dot" aria-hidden="true"></span>Watch Live</button>'+
    '</section>';
  }
  return'';
}
function openLiveStream(eventId){
  const g=[...allGames,...liveNowItems].find(x=>String(x.eventId)===String(eventId)&&liveStreamsForGame(x).length);
  if(!g)return;
  const stream=liveStreamsForGame(g)[0];
  const raw=stream?.watchUrl||stream?.embedUrl;
  if(!raw)return;
  let videoId='';
  try{
    const u=new URL(raw,location.href);
    if(u.hostname==='youtu.be')videoId=u.pathname.split('/').filter(Boolean)[0]||'';
    else if(u.hostname==='youtube.com'||u.hostname.endsWith('.youtube.com')||u.hostname==='youtube-nocookie.com'||u.hostname.endsWith('.youtube-nocookie.com'))videoId=u.searchParams.get('v')||((u.pathname.match(/\/(?:live|embed)\/([^/?]+)/)||[])[1]||'');
  }catch{}
  if(!videoId){ window.open(raw,'_blank','noopener,noreferrer'); return; }
  const d=ensureLiveDialog(),host=d.querySelector('#liveContent');
  host.innerHTML='<div class="live-head"><span class="live-badge">LIVE</span></div><div class="live-player-wrap"><iframe class="live-player" src="https://www.youtube.com/embed/'+esc(videoId)+'?autoplay=1&playsinline=1&rel=0" title="Live video" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe></div>';
  d.showModal();
}

async function hydrateLiveStreams(sport){const snapshot=allGames,now=Date.now(),candidates=snapshot.filter(g=>g.eventId&&(g.state==='live'||(g.state==='scheduled'&&Math.abs(Date.parse(g.date)-now)<=90*60000))).slice(0,4);if(!candidates.length)return;await Promise.allSettled(candidates.map(async g=>{const key=sport+':'+g.eventId,hit=liveStreamCache.get(key);if(hit&&Date.now()-hit.time<120000){g.streams=hit.items;g.streamsChecked=true;return}try{const q=new URLSearchParams({sport,event:g.eventId,home:g.home,away:g.away}),r=await fetch('https://img-api-proxy.magsipocarnie.workers.dev/streams?'+q.toString(),{cache:'no-store'});if(!r.ok)throw 0;const j=await r.json(),items=Array.isArray(j.items)?j.items.filter(x=>x?.embedUrl):[];g.streams=items;g.streamsChecked=true;liveStreamCache.set(key,{time:Date.now(),items})}catch{g.streams=[];g.streamsChecked=true}}));if(allGames===snapshot&&currentScoreLeague===sport)renderGames()}
function f1SessionName(comp){
  const abbr=String(comp?.type?.abbreviation||'').toUpperCase();
  if(abbr==='FP1')return 'Practice 1';
  if(abbr==='FP2')return 'Practice 2';
  if(abbr==='FP3')return 'Practice 3';
  if(abbr==='QUAL')return 'Qualifying';
  if(abbr==='SPRINT')return 'Sprint';
  if(abbr==='SPRINT SHOOTOUT'||abbr==='SS')return 'Sprint Qualifying';
  if(abbr==='RACE')return 'Race';
  return comp?.type?.text||comp?.type?.name||comp?.type?.abbreviation||'Session';
}
function competitorName(x){
  if(!x)return 'TBD';
  const athlete=x.athlete||{};
  const team=x.team||{};
  const athletes=Array.isArray(x.athletes)?x.athletes:[];
  return team.displayName||team.shortDisplayName||
    athlete.displayName||athlete.shortDisplayName||
    x.displayName||x.shortDisplayName||x.name||
    (athletes.length?athletes.map(a=>a?.displayName||a?.shortDisplayName).filter(Boolean).join(' / '):'')||
    'TBD';
}
function competitorLogoUrl(x){
  return x?.team?.logo||
    x?.team?.logos?.[0]?.href||
    x?.athlete?.headshot?.href||
    x?.athlete?.flag?.href||
    x?.logo||
    x?.logos?.[0]?.href||'';
}
function competitorScoreValue(x){
  const score=x?.score;
  if(score!==undefined&&score!==null){
    if(typeof score==='object'){
      const value=score.displayValue??score.shortDisplayValue??score.value??score.score;
      if(value!==undefined&&value!==null&&String(value)!=='')return String(value);
    }else if(String(score)!==''){
      return String(score);
    }
  }
  const lines=Array.isArray(x?.linescores)?x.linescores:[];
  if(lines.length){
    const values=lines.map(v=>{
      if(v===undefined||v===null)return '';
      if(typeof v==='object')return v.displayValue??v.value??v.score??'';
      return v;
    }).filter(v=>String(v)!=='');
    if(values.length)return values.join(' ');
  }
  return '—';
}
function normalizedState(c,e){
  const raw=c?.status?.type?.state||e?.status?.type?.state||'pre';
  return raw==='in'?'live':raw==='post'?'final':'scheduled';
}
function normalizedStatus(c,e){
  return c?.status?.type?.shortDetail||
    c?.status?.type?.detail||
    c?.status?.type?.description||
    e?.status?.type?.shortDetail||
    e?.status?.type?.detail||
    e?.status?.type?.description||
    'Scheduled';
}
function normalizeCompetitionEvent(e,c,index=0,sport=''){
  const competitors=Array.isArray(c?.competitors)?c.competitors:[];
  const first=competitors[0],second=competitors[1];
  const home=competitors.find(x=>x?.homeAway==='home')||first;
  const away=competitors.find(x=>x?.homeAway==='away')||second;
  const state=normalizedState(c,e);
  const combat=sport==='ufc';
  const homeWinner=home?.winner===true,awayWinner=away?.winner===true;
  const oddsList=(c?.odds||[]).filter(o=>o?.provider?.displayName||o?.provider?.name).map(mapOdds);
  return{
    eventId:String(c?.id||e?.id||'')+(index?'-'+index:''),
    date:c?.date||c?.startDate||e?.date,
    home:competitorName(home),
    away:competitorName(away),
    homeLogo:competitorLogoUrl(home),
    awayLogo:competitorLogoUrl(away),
    homeScore:combat&&state==='final'?(homeWinner?'W':awayWinner?'L':'—'):competitorScoreValue(home),
    awayScore:combat&&state==='final'?(awayWinner?'W':homeWinner?'L':'—'):competitorScoreValue(away),
    status:normalizedStatus(c,e),
    state,
    odds:oddsList[0]||null,
    oddsList,
    highlights:[],
    highlightsChecked:false,
    streams:[],
    streamsChecked:false
  };
}
function normalizeBoxingFight(f,index=0){
  const one=f?.fighters?.fighter_1||{},two=f?.fighters?.fighter_2||{};
  const raw=String(f?.status||'NOT_STARTED').toUpperCase();
  const state=raw==='LIVE'?'live':raw==='FINISHED'?'final':'scheduled';
  const outcome=f?.results?.outcome_long||f?.results?.outcome||'';
  const round=f?.results?.round;
  const resultText=state==='final'
    ?[outcome,round?'Round '+round:''].filter(Boolean).join(' · ')||'Final'
    :state==='live'?'Live':'Scheduled';
  return{
    eventId:String(f?.id||'boxing-'+index),
    date:f?.date,
    displayTime:f?.displayTime||'',
    sourceName:f?.sourceName||'Boxing Data API',
    sourceUrl:f?.sourceUrl||'',
    home:two?.name||'TBD',
    away:one?.name||'TBD',
    homeLogo:'',
    awayLogo:'',
    homeScore:state==='final'?(two?.winner===true?'W':one?.winner===true?'L':'—'):'—',
    awayScore:state==='final'?(one?.winner===true?'W':two?.winner===true?'L':'—'):'—',
    status:resultText,
    state,
    odds:null,
    oddsList:[],
    highlights:[],
    highlightsChecked:true,
    streams:[],
    streamsChecked:true
  };
}
function normalizeAsianGamesExpiry(game){
  if(!game||game.state!=='live')return game;
  const now=Date.now();
  const suppliedExpiry=Date.parse(game.expiresAt||game.liveExpiresAt||'');
  const start=Date.parse(game.firstLiveAt||game.liveFirstSeenAt||game.date||'');
  const expires=Number.isFinite(suppliedExpiry)?suppliedExpiry:(Number.isFinite(start)?start+2*60*60*1000:NaN);
  if(!Number.isFinite(expires)||now<expires)return game;
  return{
    ...game,
    state:'expired',
    status:'Awaiting official result',
    streams:[],
    streamsChecked:true,
    liveExpired:true
  };
}
function expireVisibleAsianGames(){
  let changed=false;
  if(currentScoreLeague==='asian_games'){
    allGames=allGames.map(g=>{
      const next=normalizeAsianGamesExpiry(g);
      if(next!==g)changed=true;
      const streams=(next.streams||[]).filter(s=>!s.expiresAt||Date.now()<Date.parse(s.expiresAt));
      if(streams.length!==(next.streams||[]).length){changed=true;return {...next,streams};}
      return next;
    });
    if(changed)renderGames();
  }
  const remaining=liveNowItems.filter(liveNowItemIsCurrent).map(g=>{
    if(g.sportKey!=='asian_games')return g;
    const streams=(g.streams||[]).filter(s=>!s.expiresAt||Date.now()<Date.parse(s.expiresAt));
    if(streams.length!==(g.streams||[]).length){changed=true;return {...g,streams};}
    return g;
  });
  if(changed||remaining.length!==liveNowItems.length)renderAllLiveGames(remaining);
}
function normalizeScorePayload(sport,payload){
  if(payload?.special){
    return (payload.games||[]).map((g,i)=>{
      const game={
        eventId:g.eventId||('special-'+sport+'-'+i),
        date:g.date,
        firstLiveAt:g.firstLiveAt||g.liveFirstSeenAt||'',
        expiresAt:g.expiresAt||g.liveExpiresAt||'',
        displayTime:g.displayTime||'',
        home:g.home||'',
        away:g.away||'',
        homeLogo:g.homeLogo||'',
        awayLogo:g.awayLogo||'',
        homeScore:g.homeScore??'—',
        awayScore:g.awayScore??'—',
        title:g.title||'',
        location:g.location||'',
        level:g.level||'',
        surface:g.surface||'',
        singlesDraw:g.singlesDraw||'',
        doublesDraw:g.doublesDraw||'',
        totalCommitment:g.totalCommitment||'',
        status:g.status||'Scheduled',
        state:g.state||'scheduled',
        eventOnly:Boolean(g.eventOnly),
        dataType:g.dataType||'',
        weightClass:g.weightClass||'',
        weightOrder:Number.isFinite(Number(g.weightOrder))?Number(g.weightOrder):999,
        sourceName:g.sourceName||payload.sourceName||'',
        sourceUrl:g.sourceUrl||payload.sourceUrl||'',
        odds:null,oddsList:[],highlights:Array.isArray(g.highlights)?g.highlights:[],highlightsChecked:true,
        streams:Array.isArray(g.streams)?g.streams.filter(s=>s&&(s.watchUrl||s.embedUrl)):[],streamsChecked:Boolean(g.streamsChecked||Array.isArray(g.streams))
      };
      return sport==='asian_games'?normalizeAsianGamesExpiry(game):game;
    });
  }
  if(sport==='boxing'){
    return (payload?.fights||[]).map((f,i)=>normalizeBoxingFight(f,i))
      .filter(g=>g.away!=='TBD'||g.home!=='TBD');
  }

  const events=Array.isArray(payload?.events)?payload.events:[];
  if(sport==='atp'||sport==='wta'||sport==='ufc'){
    const out=[];
    for(const e of events){
      const comps=Array.isArray(e?.competitions)?e.competitions:[];
      if(comps.length){
        comps.forEach((c,i)=>{
          if((c?.competitors||[]).length>=2)out.push(normalizeCompetitionEvent(e,c,i,sport));
        });
      }else{
        out.push(normalizeEvent(e,sport));
      }
    }
    return out.filter(g=>g.away!=='TBD'||g.home!=='TBD');
  }
  return events.map(e=>normalizeEvent(e,sport));
}
function normalizeEvent(e,sport=''){
  const competitions=e.competitions||[];
  const isRacing=Boolean(e.circuit)||String(e?.uid||'').includes('l:2030')||competitions.some(x=>x?.type?.abbreviation&&!(x?.competitors||[]).length);
  if(isRacing){
    const now=Date.now();
    const liveComp=competitions.find(x=>x?.status?.type?.state==='in');
    const nextComp=competitions.find(x=>x?.status?.type?.state==='pre'&&(Date.parse(x.date||x.startDate||'')||0)>=now);
    const completed=[...competitions].reverse().find(x=>x?.status?.type?.state==='post');
    const session=liveComp||nextComp||completed||competitions[0]||{};
    const stateRaw=liveComp?'in':session?.status?.type?.state||e?.status?.type?.state||'pre';
    const sessionName=f1SessionName(session);
    const status=session?.status?.type?.shortDetail||session?.status?.type?.description||e?.status?.type?.shortDetail||'Scheduled';
    return{
      eventId:e.id||session.id||'',
      date:session.date||session.startDate||e.date,
      home:e.shortName||e.name||'Formula 1',
      away:sessionName,
      homeLogo:'',
      awayLogo:'',
      homeScore:'—',
      awayScore:'—',
      status,
      state:stateRaw==='in'?'live':stateRaw==='post'?'final':'scheduled',
      odds:null,
      oddsList:[],
      highlights:[],
      highlightsChecked:false,
      streams:[],
      streamsChecked:false,
      isRacing:true,
      raceTitle:e.name||e.shortName||'Formula 1',
      raceSession:sessionName,
      raceCircuit:e.circuit?.fullName||'',
      raceCity:e.circuit?.address?.city||'',
      raceBroadcast:session.broadcast||session.broadcasts?.[0]?.names?.[0]||''
    };
  }
  const c=competitions[0]||{};
  return normalizeCompetitionEvent(e,c,0,sport);
}
function gameDomKey(g){
  const raw=String(g?.eventId||[g?.date||'',g?.away||'',g?.home||''].join('|'));
  return encodeURIComponent(raw);
}

function updateScoreNumbers(items=allGames){
  const map=new Map((items||[]).map(g=>[gameDomKey(g),g]));
  document.querySelectorAll('#games .game[data-game-key]').forEach(card=>{
    const g=map.get(card.dataset.gameKey);
    if(!g)return;
    const away=card.querySelector('[data-score-side="away"]');
    const home=card.querySelector('[data-score-side="home"]');
    if(away&&away.textContent!==String(g.awayScore??'—'))away.textContent=String(g.awayScore??'—');
    if(home&&home.textContent!==String(g.homeScore??'—'))home.textContent=String(g.homeScore??'—');
  });
}

let liveNowLocked=false;

function updateAllLiveScoreNumbers(items){
  const section=document.getElementById('allLiveSection');
  const cards=[...document.querySelectorAll('#allLiveGames .live-game-card[data-game-key]')];
  if(cards.length){
    liveNowLocked=true;
    if(section)section.hidden=false;
  }

  const map=new Map((items||[]).map(g=>[gameDomKey(g),g]));
  cards.forEach(card=>{
    const g=map.get(card.dataset.gameKey);
    if(!g)return;
    const away=card.querySelector('[data-score-side="away"]');
    const home=card.querySelector('[data-score-side="home"]');
    if(away&&away.textContent!==String(g.awayScore??'—'))away.textContent=String(g.awayScore??'—');
    if(home&&home.textContent!==String(g.homeScore??'—'))home.textContent=String(g.homeScore??'—');
  });
}

async function refreshExistingAllLiveScores(excludeSport=''){
  const cards=[...document.querySelectorAll('#allLiveGames .live-game-card[data-sport-key]')];
  if(!cards.length)return;

  // Reuse the selected league's freshly loaded values instead of fetching it twice.
  if(excludeSport)updateAllLiveScoreNumbers(allGames);

  const keys=[...new Set(cards.map(card=>card.dataset.sportKey).filter(Boolean))]
    .filter(key=>key!==excludeSport);

  if(!keys.length)return;

  const updates=[];
  await Promise.allSettled(keys.map(async key=>{
    try{
      const j=await fetchScorePayload(key,{fallbackOnly:regionalScoreKeys.has(key)});
      for(const game of normalizeScorePayload(key,j)){
        if(game.state==='live')updates.push(game);
      }
    }catch{}
  }));
  updateAllLiveScoreNumbers(updates);
}

let liveSportFilter='all';
let liveNowItems=[];
let mobileLiveToggleBound=false;
function setMobileLiveExpanded(expanded){
  const section=document.getElementById('allLiveSection');
  const toggle=document.getElementById('mobileLiveToggle');
  const body=document.getElementById('mobileLiveBody');
  if(!section||!toggle||!body)return;
  section.classList.toggle('mobile-live-expanded',Boolean(expanded));
  toggle.setAttribute('aria-expanded',expanded?'true':'false');
  body.inert=matchMedia('(max-width:760px)').matches&&!expanded;
}
function ensureMobileLiveToggle(){
  if(mobileLiveToggleBound)return;
  const toggle=document.getElementById('mobileLiveToggle');
  if(!toggle)return;
  mobileLiveToggleBound=true;
  toggle.addEventListener('click',()=>{
    const expanded=toggle.getAttribute('aria-expanded')==='true';
    setMobileLiveExpanded(!expanded);
  });
  const mobileQuery=matchMedia('(max-width:760px)');
  mobileQuery.addEventListener?.('change',()=>setMobileLiveExpanded(toggle.getAttribute('aria-expanded')==='true'));
  setMobileLiveExpanded(toggle.getAttribute('aria-expanded')==='true');
}
let externalLiveCache={time:0,streams:[]};
async function loadExternalLiveData(){
  if(Date.now()-externalLiveCache.time<60000)return externalLiveCache.streams;
  try{
    const r=await fetch('/external-live.json?ts='+Date.now(),{cache:'no-store'});
    if(!r.ok)throw new Error('external live unavailable');
    const j=await r.json();
    const updated=Date.parse(j?.updatedAt||'');
    const freshMinutes=Math.max(5,Number(j?.freshForMinutes)||20);
    const fresh=Number.isFinite(updated)&&Date.now()-updated<=freshMinutes*60000;
    const streams=fresh&&Array.isArray(j?.streams)?j.streams.filter(x=>x?.leagueKey==='asian_games'&&x?.stream?.watchUrl):[];
    externalLiveCache={time:Date.now(),streams};
    return streams;
  }catch{
    externalLiveCache={time:Date.now(),streams:[]};
    return [];
  }
}
function externalMatchTokens(value){
  const ignore=new Set(['asian','games','live','women','womens','men','mens','team','final','round','group','match','game','sports','sport','aichi','nagoya','2026']);
  return new Set(String(value||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').split(/\s+/).filter(x=>x.length>2&&!ignore.has(x)));
}
function externalTeamsMatch(game,entry){
  const teams=Array.isArray(entry?.teams)?entry.teams.filter(Boolean):[];
  if(!teams.length)return null;
  const sides=[game?.away,game?.home].map(externalMatchTokens);
  const scoreTeam=t=>{
    const tt=externalMatchTokens(t);
    return Math.max(...sides.map(side=>[...tt].filter(x=>side.has(x)).length),0);
  };
  return teams.every(t=>scoreTeam(t)>0);
}
function attachExternalAsianGamesStreams(games,entries){
  const list=Array.isArray(games)?games:[];
  const sources=Array.isArray(entries)?entries:[];
  for(const entry of sources){
    if(!Number.isFinite(Date.parse(entry.expiresAt||''))||Date.now()>=Date.parse(entry.expiresAt))continue;
    const sport=String(entry?.sport||'').trim().toLowerCase();
    const candidates=list.filter(g=>g?.sportKey==='asian_games'&&g?.state==='live'&&String(g?.sportLabel||asianGamesSportLabel(g)).trim().toLowerCase()===sport);
    if(!candidates.length)continue;
    let target=null;
    const teamMatched=candidates.filter(g=>externalTeamsMatch(g,entry)===true);
    if(teamMatched.length===1)target=teamMatched[0];
    else if(!Array.isArray(entry?.teams)||!entry.teams.length){
      if(candidates.length===1)target=candidates[0];
    }
    if(!target)continue;
    const stream=entry.stream;
    const current=Array.isArray(target.streams)?target.streams:[];
    if(!current.some(s=>String(s?.watchUrl||'')===String(stream?.watchUrl||'')))target.streams=[...current,stream];
    target.streamsChecked=true;
  }
}


function liveSportSlug(label){
  return String(label||'sport').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
}

function liveSportIconMarkup(label){
  const key=String(label||'').toLowerCase();
  const icons={
    all:'grid_view',
    basketball:'sports_basketball',
    football:'sports_soccer',
    tennis:'sports_tennis',
    cricket:'sports_cricket',
    volleyball:'sports_volleyball',
    baseball:'sports_baseball',
    hockey:'sports_hockey',
    'american football':'sports_football',
    motorsport:'sports_motorsports',
    'combat sports':'sports_mma',
    boxing:'sports_mma'
  };
  return '<span class="material-symbols-rounded sport-material-icon" aria-hidden="true">'+esc(icons[key]||'sports')+'</span>';
}

function liveSportOrder(label){
  const order=['Basketball','Football','Tennis','Cricket','Volleyball','Baseball','Hockey','American Football','Motorsport','Combat Sports','Boxing'];
  const i=order.indexOf(label);
  return i<0?99:i;
}

function renderLiveSportSorter(items){
  const sorter=document.getElementById('liveSportSorter');
  if(!sorter)return;
  const sports=[...new Set(items.map(g=>g.sportLabel||'Sport'))].sort((a,b)=>liveSportOrder(a)-liveSportOrder(b)||a.localeCompare(b));
  const valid=liveSportFilter==='all'||sports.includes(liveSportFilter);
  if(!valid)liveSportFilter='all';
  const choices=[['all','All'],...sports.map(s=>[s,s])];
  sorter.innerHTML=choices.map(([value,label])=>
    '<button type="button" class="live-sport-filter'+(liveSportFilter===value?' active':'')+'" data-live-sport="'+esc(value)+'" aria-label="'+esc(label)+'">'+
      '<span class="live-sport-icon">'+liveSportIconMarkup(value)+'</span>'+
      '<span class="live-sport-name">'+esc(label)+'</span>'+
    '</button>'
  ).join('');
  sorter.querySelectorAll('[data-live-sport]').forEach(btn=>btn.addEventListener('click',()=>{
    liveSportFilter=btn.dataset.liveSport||'all';
    renderAllLiveGames(liveNowItems,{preserveItems:true});
  }));
}

function liveNowItemIsCurrent(g){
  if(!g||g.state!=='live')return false;
  if((g.sportKey==='atp'||g.sportKey==='wta')&&g.eventOnly)return false;

  const now=Date.now();
  const start=Date.parse((g.sportKey==='asian_games'&&(g.firstLiveAt||g.liveFirstSeenAt))||g.date||'');
  const maxHours={
    asian_games:2,
    soccer:4,laliga:4,seriea:4,bundesliga:4,champions:4,mls:4,
    basketball:5,wnba:5,pba:5,ncaa_ph:5,uaap:5,mpbl:5,nbl:5,nblaus:5,vba:5,
    atp:7,wta:7,ipl:7,volleyball_w:5,volleyball_m:5,
    baseball:8,hockey:5,football:7,ncaaf:7,f1:5,ufc:10,boxing:10
  };
  const limit=maxHours[g.sportKey];
  if(Number.isFinite(start)&&limit&&now-start>limit*60*60*1000)return false;

  if(g.sportKey==='asian_games'){
    const expires=Date.parse(g.expiresAt||g.liveExpiresAt||'');
    if(!Number.isFinite(expires)||now>=expires)return false;
    const verifiedTimedStream=String(g.eventId||'').startsWith('ag26-youtube-')
      &&Number.isFinite(Date.parse(g.firstLiveAt||''))
      &&Array.isArray(g.streams)
      &&g.streams.some(s=>s?.watchUrl&&s?.embedUrl);
    if(!verifiedTimedStream){
      const updated=Date.parse(specialSportsDataCache?.updatedAt||specialSportsDataCache?.updated_at||'');
      if(!Number.isFinite(updated)||now-updated>30*60*1000)return false;
    }
  }
  return true;
}

function renderAllLiveGames(items,{preserveItems=false}={}){
  if(!preserveItems)liveNowItems=[...items];
  liveNowItems=liveNowItems.filter(liveNowItemIsCurrent);
  liveNowLocked=liveNowItems.length>0;
  renderScoreLeagueFilters();
  if(document.getElementById('games'))renderGames();
}
async function loadAllLiveGames({silent=false}={}){
  const live=[];
  const webKeys=['pba','mpbl','nbl','nblaus','vba'];
  const apiKeys=['soccer','laliga','seriea','bundesliga','champions','mls','pfl','basketball','wnba','atp','wta','australian_open','wimbledon','us_open','ipl','bigbash','cricket_world_cup','volleyball_w','volleyball_m','pvl','vleague_jp','f1','motogp','formulae','ufc','one','wbc','wba','ibf','wbo','ring','baseball','npb','kbo','hockey','khl','iihf','football','ncaaf','bleague','euroleague','fiba'];

  const regionalPromise=(async()=>{
    await loadRegionalAutoData();
    await Promise.all(webKeys.map(async key=>{
      const labels=liveNowLabels[key]||{};
      const primaryLive=regionalSnapshotGames(key).filter(game=>game.state==='live');

      if(primaryLive.length){
        for(const game of primaryLive){
          live.push({...game,sportKey:key,sportLabel:labels.sport,leagueLabel:labels.league});
        }
        return;
      }

      try{
        const j=await fetchScorePayload(key,{fallbackOnly:true});
        for(const game of normalizeScorePayload(key,j)){
          if(game.state==='live')live.push({...game,sportKey:key,sportLabel:labels.sport,leagueLabel:labels.league});
        }
      }catch{}
    }));
  })();

  const asianGamesPromise=(async()=>{
    try{
      const j=await fetchScorePayload('asian_games');
      const labels=liveNowLabels.asian_games||{sport:'Multi-sport',league:'Asian Games'};
      for(const game of normalizeScorePayload('asian_games',j)){
        if(game.state==='live')live.push({...game,sportKey:'asian_games',sportLabel:asianGamesSportLabel(game),leagueLabel:labels.league});
      }
    }catch{}
  })();

  const apiPromise=Promise.all(apiKeys.map(async key=>{
    try{
      const j=await fetchScorePayload(key);
      const labels=liveNowLabels[key]||{};
      for(const game of normalizeScorePayload(key,j)){
        if(game.state==='live')live.push({...game,sportKey:key,sportLabel:labels.sport,leagueLabel:labels.league});
      }
    }catch{}
  }));

  await Promise.all([regionalPromise,apiPromise,asianGamesPromise]);
  try{
    const external=await loadExternalLiveData();
    attachExternalAsianGamesStreams(live,external);
  }catch{}
  // Merge GitHub-discovered YouTube streams into exact live events when possible.
  // The API key never reaches the browser; only public video IDs/URLs are published.
  try{
    const r=await fetch('/youtube-live.json?ts='+Date.now(),{cache:'no-store'});
    if(r.ok){
      const y=await r.json();
      const ytUpdated=Date.parse(y?.updatedAt||'');
      const ytFreshMinutes=Math.max(5,Number(y?.freshForMinutes)||8);
      const ytFresh=Number.isFinite(ytUpdated)&&Date.now()-ytUpdated<=ytFreshMinutes*60000;
      const ys=(ytFresh&&Array.isArray(y.streams)?y.streams:[]).filter(x=>x.leagueKey!=='asian_games'||(Number.isFinite(Date.parse(x.expiresAt||''))&&Date.now()<Date.parse(x.expiresAt)));
      const byId=new Map(ys.map(x=>[String(x.eventId),x.stream]));
      for(const g of live){
        const s=byId.get(String(g.eventId));
        if(s?.watchUrl)g.streams=[s];
      }
      // Verified channel broadcasts can exist even when the score provider has no
      // matching event ID. Preserve the actual source channel for each league.
      for(const x of ys){
        if(!x?.stream?.watchUrl||!['asian_games','fiba','pba','mpbl','nbl','ncaa_ph','uaap','wta'].includes(x?.leagueKey))continue;
        if(live.some(g=>String(g.eventId)===String(x.eventId)))continue;
        const label=x.league||({asian_games:'2026 ASIAN GAMES',pba:'PBA',mpbl:'MPBL',nbl:'NBL Pilipinas',ncaa_ph:'NCAA Philippines',uaap:'UAAP',wta:'WTA Tour',fiba:'FIBA'}[x.leagueKey]);
        const source=x.stream.channel||x.stream.provider||label;
        live.push({eventId:x.eventId,firstLiveAt:x.firstLiveAt,expiresAt:x.expiresAt,sportKey:x.leagueKey,sportLabel:x.sport||'Sport',leagueLabel:label,date:x.firstLiveAt||y.updatedAt||new Date().toISOString(),displayTime:'LIVE',away:label,home:x.title||(label+' Live'),awayScore:'',homeScore:'',status:'LIVE · '+source,state:'live',streams:[x.stream],streamsChecked:true});
      }
    }
  }catch{}
  // Validate every candidate again immediately before rendering.
  for(let i=live.length-1;i>=0;i--){
    if(!liveNowItemIsCurrent(live[i]))live.splice(i,1);
  }
  const deduped=[];
  const seenLive=new Set();
  for(const game of live){
    const key=String(game.eventId||[game.sportKey,game.away,game.home,game.title].join('|'));
    if(seenLive.has(key))continue;
    seenLive.add(key);deduped.push(game);
  }
  live.length=0;live.push(...deduped);
  await Promise.allSettled([...new Set(live.map(g=>g.sportKey).filter(Boolean))].map(key=>
    hydrateTeamLogos(key,live.filter(g=>g.sportKey===key))
  ));
  // Re-render Live Now so newly discovered stream links/buttons are reflected in the DOM.
  renderAllLiveGames(live);
}
function renderGames(){
  const host=document.getElementById('games');
  if(!host)return;
  // Preserve dropdown state across automatic score/live-data re-renders.
  const openPanels=new Set(
    [...host.querySelectorAll('[aria-expanded="true"][aria-controls]')]
      .map(el=>el.getAttribute('aria-controls'))
      .filter(Boolean)
  );

  const byDateAsc=(a,b)=>(Date.parse(a.date||'')||0)-(Date.parse(b.date||'')||0);
  const byDateDesc=(a,b)=>(Date.parse(b.date||'')||0)-(Date.parse(a.date||'')||0);

  const live=allGames.filter(g=>g.state==='live').sort(byDateAsc);
  const scheduled=allGames.filter(g=>g.state==='scheduled').sort(byDateAsc);
  const finals=allGames.filter(g=>g.state==='final').sort(byDateDesc);
  const info=allGames.filter(g=>g.state==='info'||g.dataType==='titleholder').sort((a,b)=>String(a.title||'').localeCompare(String(b.title||'')));
  const other=allGames.filter(g=>!['live','scheduled','final','info'].includes(g.state)&&g.dataType!=='titleholder').sort(byDateAsc);

  const renderCard=g=>{
    if(currentScoreLeague==='asian_games'){
      const score=value=>String(value??'—');
      const hasAway=g.away&&g.away!=='Asian Games';
      const hasHome=g.home&&g.home!=='Asian Games';
      return '<article class="game asian-games-card'+(g.state==='live'?' game-is-live':'')+'" data-game-key="'+esc(gameDomKey(g))+'">'+
        '<div class="time">'+esc(g.displayTime||new Date(g.date).toLocaleString([],{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}))+'</div>'+
        '<div class="teams asian-games-event-copy">'+
          '<div class="asian-games-sport-name">'+esc(asianGamesSportLabel(g))+'</div>'+
          '<div class="asian-games-event-title">'+esc(asianGamesEventLabel(g))+'</div>'+
          (hasAway?'<div class="team"><span>'+esc(g.away)+'</span>'+(score(g.awayScore)!=='—'?'<b data-score-side="away">'+esc(g.awayScore)+'</b>':'')+'</div>':'')+
          (hasHome?'<div class="team"><span>'+esc(g.home)+'</span>'+(score(g.homeScore)!=='—'?'<b data-score-side="home">'+esc(g.homeScore)+'</b>':'')+'</div>':'')+
        '</div>'+
        '<div class="state '+(g.state==='live'?'live':'')+'">'+esc(g.status||'Scheduled')+'</div>'+
        (liveStreamsForGame(g).length?'<button class="watch-live-btn" type="button" data-live-event="'+esc(g.eventId)+'"><span class="live-dot" aria-hidden="true"></span>'+(g.state==='live'?'Watch Live':'View Stream')+'</button>':'')+
      '</article>';
    }

    if(g.eventOnly){
      const meta=[g.level,g.surface,g.singlesDraw?String(g.singlesDraw)+' singles':'',g.doublesDraw?String(g.doublesDraw)+' doubles':''].filter(Boolean).join(' · ');
      return '<article class="game special-score-event" data-game-key="'+esc(gameDomKey(g))+'">'+
        '<div class="time">'+esc(g.displayTime||'')+'</div>'+
        '<div class="teams"><div class="team special-event-copy"><span><strong>'+esc(g.title||'Event')+'</strong></span></div>'+
        (g.location?'<div class="special-event-location">'+esc(g.location)+'</div>':'')+
        (meta?'<div class="special-event-meta">'+esc(meta)+'</div>':'')+
        (g.totalCommitment?'<div class="special-event-prize">Total commitment '+esc(g.totalCommitment)+'</div>':'')+
        '</div>'+
        '<div class="state '+(g.state==='live'?'live':'')+'">'+esc(g.status||'Scheduled')+'</div>'+
      '</article>';
    }

    if(g.isRacing){
      const place=[g.raceCircuit,g.raceCity].filter(Boolean).join(' · ');
      return '<article class="game race-game'+(g.state==='live'?' game-is-live':'')+'" data-game-key="'+esc(gameDomKey(g))+'">'+
        '<div class="time">'+esc(g.displayTime||new Date(g.date).toLocaleString([],{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}))+'</div>'+
        '<div class="race-game-main"><div class="race-game-top"><strong>'+esc(g.raceTitle||g.home)+'</strong><span class="race-session">'+esc(g.raceSession||g.away)+'</span></div>'+
        (place?'<small>'+esc(place)+'</small>':'')+
        '<div class="state '+(g.state==='live'?'live':'')+'">'+esc(g.status)+'</div>'+
        (g.raceBroadcast?'<div class="race-broadcast">Broadcast: '+esc(g.raceBroadcast)+'</div>':'')+
        (liveStreamsForGame(g).length?'<button class="watch-live-btn" type="button" data-live-event="'+esc(g.eventId)+'"><span class="live-dot" aria-hidden="true"></span>'+(g.state==='live'?'Watch Live':'View Stream')+'</button>':'')+
        '</div></article>';
    }

    return '<article class="game'+(g.state==='live'?' game-is-live':'')+'" data-game-key="'+esc(gameDomKey(g))+'">'+
      '<div class="time">'+esc(g.displayTime||new Date(g.date).toLocaleString([],{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}))+'</div>'+
      '<div class="teams">'+
        '<div class="team"><span class="team-identity">'+teamLogoMarkup(g.awayLogo,g.away)+'<span>'+esc(g.away)+'</span></span><b data-score-side="away">'+esc(g.awayScore)+'</b></div>'+
        '<div class="team"><span class="team-identity">'+teamLogoMarkup(g.homeLogo,g.home)+'<span>'+esc(g.home)+'</span></span><b data-score-side="home">'+esc(g.homeScore)+'</b></div>'+
      '</div>'+
      '<div class="state '+(g.state==='live'?'live':'')+'">'+esc(g.status)+'</div>'+
      (liveStreamsForGame(g).length?'<button class="watch-live-btn" type="button" data-live-event="'+esc(g.eventId)+'"><span class="live-dot" aria-hidden="true"></span>'+(g.state==='live'?'Watch Live':'View Stream')+'</button>':'')+
      (g.highlights?.length?'<button class="highlights-btn" type="button" data-highlight-event="'+esc(g.eventId)+'"><span class="highlights-btn-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span>Highlights <b>'+esc(g.highlights.length)+'</b></button>':'')+
      (g.odds?'<div class="oddsline"><span>'+esc(g.odds.provider)+'</span><span>Line <b>'+esc(g.odds.details)+'</b></span><span>Total <b>'+esc(g.odds.total)+'</b></span></div>':'')+
    '</article>';
  };

  const asianNow=Date.now();
  const asianSchedule=currentScoreLeague==='asian_games'
    ?scheduled.filter(g=>{
        const t=Date.parse(g.date||'');
        return !Number.isFinite(t)||t>=asianNow-6*60*60*1000;
      }).sort(byDateAsc)
    :null;
  const scheduleItems=(asianSchedule||[...scheduled,...other]).slice(0,30);
  const nblHasScore=g=>/^\d{1,3}$/.test(String(g?.awayScore||''))&&/^\d{1,3}$/.test(String(g?.homeScore||''));
  const nblVerifiedScores=currentScoreLeague==='nbl'?finals.filter(nblHasScore).slice(0,30):[];
  const nblRecentReplays=currentScoreLeague==='nbl'?finals.filter(g=>!nblHasScore(g)).slice(0,20):[];
  const scoreItems=currentScoreLeague==='nbl'?nblVerifiedScores:finals.slice(0,30);
  const leagueName=liveNowLabels[currentScoreLeague]?.league||'League';
  const sections=[];

  if(currentScoreLeague==='asian_games'){
    const agData=specialSportsDataCache?.leagues?.asian_games;
    const medals=Array.isArray(agData?.medals)?agData.medals:[];
    if(medals.length){
      const medalPanelId='asian-games-medal-standings';
      sections.push('<section class="league-games-group asian-medal-table league-standings-dropdown" aria-label="Asian Games medal standings">'+
        '<button type="button" class="standings-dropdown-toggle" data-standings-toggle aria-expanded="false" aria-controls="'+medalPanelId+'">'+
          '<span class="standings-dropdown-copy"><span class="standings-dropdown-kicker">Medal table</span><strong>Medal Standings</strong><small>Gold · Silver · Bronze · Total</small></span>'+
          '<span class="standings-dropdown-side"><span class="standings-dropdown-count">'+esc(medals.length)+' '+(medals.length===1?'country':'countries')+'</span><span class="standings-dropdown-chevron" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg></span></span>'+
        '</button>'+
        '<div id="'+medalPanelId+'" class="standings-dropdown-content">'+
          '<div class="standings-dropdown-inner"><div class="medal-table-scroll">'+
            '<div class="medal-table-head"><span>Rank</span><span>Country</span><b>Gold</b><b>Silver</b><b>Bronze</b><b>Total</b></div>'+
            '<div class="medal-table-body">'+medals.map(m=>'<div class="medal-table-row"><span>'+esc(m.rank)+'</span><strong>'+esc(m.country)+'</strong><b>'+esc(m.gold)+'</b><b>'+esc(m.silver)+'</b><b>'+esc(m.bronze)+'</b><b>'+esc(m.total)+'</b></div>').join('')+'</div>'+
          '</div></div>'+
        '</div>'+
      '</section>');
    }
  }

  const liveStreamHtml=selectedLeagueLiveStreamMarkup(currentScoreLeague);
  if(liveStreamHtml)sections.push(liveStreamHtml);

  const leagueStatsHtml=leagueStatsMarkup(currentScoreLeague);
  if(leagueStatsHtml)sections.push(leagueStatsHtml);

  if(currentScoreLeague==='ufc'||currentScoreLeague==='one'){
    const titleholdersHtml=combatTitleholdersMarkup(currentScoreLeague);
    if(titleholdersHtml)sections.push(titleholdersHtml);
  }

  if(currentScoreLeague==='wta'){
    const wtaData=specialSportsDataCache?.leagues?.wta||{};
    const rankingsHtml=wtaRankingsMarkup(wtaData);
    if(rankingsHtml)sections.push(rankingsHtml);
  }

  if(live.length){
    sections.push(
      '<section class="league-games-group selected-live-scores" aria-label="'+esc(leagueName)+' live scores">'+
        '<div class="league-games-group-head"><h3>Live Scores</h3><span>'+esc(leagueName)+'</span></div>'+
        '<div class="league-games-list">'+live.map(renderCard).join('')+'</div>'+
      '</section>'
    );
  }

  if(currentScoreLeague==='uaap'){
    const uaapData=getRegionalSnapshot('uaap')||specialSportsDataCache?.leagues?.uaap||{};
    const standings=Array.isArray(uaapData?.standings)?uaapData.standings:[];
    const standingsHtml=leagueStandingsMarkup({
      id:'uaap',
      title:'Standings',
      subtitle:'UAAP Season 89',
      ariaLabel:'UAAP standings',
      rows:standings
    });
    if(standingsHtml)sections.push(standingsHtml);
  }

  if(currentScoreLeague==='mpbl'){
    const standings=getRegionalSnapshot('mpbl')?.standings||{};
    for(const [groupKey,rows] of Object.entries(standings)){
      if(!Array.isArray(rows)||!rows.length)continue;
      const groupName=groupKey==='northDivision'?'North Division':groupKey==='southDivision'?'South Division':groupKey.replace(/([a-z])([A-Z])/g,'$1 $2').replace(/^./,x=>x.toUpperCase());
      const standingsHtml=leagueStandingsMarkup({
        id:'mpbl-'+groupKey,
        title:groupName+' Standings',
        subtitle:'MPBL 2026',
        ariaLabel:'MPBL '+groupName+' standings',
        rows
      });
      if(standingsHtml)sections.push(standingsHtml);
    }
  }

  if(currentScoreLeague==='ncaa_ph'){
    const standings=specialSportsDataCache?.leagues?.ncaa_ph?.standings||{};
    for(const [groupKey,rows] of Object.entries(standings)){
      if(!Array.isArray(rows)||!rows.length)continue;
      const groupName=groupKey.replace(/([a-z])([A-Z])/g,'$1 $2').replace(/^./,x=>x.toUpperCase());
      const standingsHtml=leagueStandingsMarkup({
        id:'ncaa-ph-'+groupKey,
        title:groupName+' Standings',
        subtitle:'NCAA Season 102',
        ariaLabel:'NCAA Philippines '+groupName+' standings',
        rows
      });
      if(standingsHtml)sections.push(standingsHtml);
    }
  }

  if(currentScoreLeague==='nbl'&&scoreItems.length){
    sections.push(
      '<section class="league-games-group" aria-label="'+esc(leagueName)+' verified scores">'+
        '<div class="league-games-group-head"><h3>Verified Scores</h3><span>'+esc(leagueName)+'</span></div>'+
        '<div class="league-games-list">'+scoreItems.map(renderCard).join('')+'</div>'+
      '</section>'
    );
  }

  if(info.length){
    const boxingTitleKeys=new Set(['wbc','wba','ibf','wbo','ring']);
    if(boxingTitleKeys.has(currentScoreLeague))sections.push(boxingTitleholdersMarkup(info,leagueName,currentScoreLeague));
    else sections.push(
      '<section class="league-games-group" aria-label="'+esc(leagueName)+' titleholders">'+
        '<div class="league-games-group-head"><h3>Titleholders</h3><span>'+esc(leagueName)+'</span></div>'+
        '<div class="league-games-list">'+info.map(renderCard).join('')+'</div>'+
      '</section>'
    );
  }

  if(scheduleItems.length){
    sections.push(
      '<section class="league-games-group" aria-label="'+esc(leagueName)+' schedule">'+
        '<div class="league-games-group-head"><h3>Schedule</h3><span>'+esc(leagueName)+'</span></div>'+
        '<div class="league-games-list">'+scheduleItems.map(renderCard).join('')+'</div>'+
      '</section>'
    );
  }

  if(currentScoreLeague!=='nbl'&&scoreItems.length){
    sections.push(
      '<section class="league-games-group" aria-label="'+esc(leagueName)+' results">'+
        '<div class="league-games-group-head"><h3>'+(currentScoreLeague==='asian_games'?'Results':'Scores')+'</h3><span>'+esc(leagueName)+'</span></div>'+
        '<div class="league-games-list">'+scoreItems.map(renderCard).join('')+'</div>'+
      '</section>'
    );
  }

  if(currentScoreLeague==='nbl'&&nblRecentReplays.length){
    sections.push(
      '<section class="league-games-group" aria-label="'+esc(leagueName)+' recent games">'+
        '<div class="league-games-group-head"><h3>Recent Games</h3><span>Official replays · score not yet verified</span></div>'+
        '<div class="league-games-list">'+nblRecentReplays.map(renderCard).join('')+'</div>'+
      '</section>'
    );
  }

  host.innerHTML=sections.length
    ?sections.join('')
    :'<div class="empty">No verified schedule or scores were returned for this league right now.</div>';

  for(const panelId of openPanels){
    const toggle=[...host.querySelectorAll('[aria-controls]')].find(el=>el.getAttribute('aria-controls')===panelId);
    if(!toggle)continue;
    toggle.setAttribute('aria-expanded','true');
    const statsSection=toggle.closest('.sports-statistics');
    if(statsSection)statsSection.classList.add('stats-open');
    const standingsSection=toggle.closest('.league-standings-dropdown');
    if(standingsSection)standingsSection.classList.add('standings-open');
  }
}

function nblBroadcastScheduleGames(){
  const rows=Array.isArray(getRegionalSnapshot('nbl')?.broadcast)?getRegionalSnapshot('nbl').broadcast:[];
  const now=Date.now();
  return rows.map((b,i)=>{
    const tm=String(b?.time||'').match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
    if(!b?.date||!tm)return null;
    let h=Number(tm[1]),m=Number(tm[2]);
    if(tm[3].toUpperCase()==='PM'&&h<12)h+=12;
    if(tm[3].toUpperCase()==='AM'&&h===12)h=0;
    const iso=String(b.date)+'T'+String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':00+08:00';
    const start=Date.parse(iso);
    if(!Number.isFinite(start)||start<now-60*60000||start>now+14*24*60*60000)return null;
    return{
      eventId:'nbl-broadcast-'+b.date+'-'+String(h).padStart(2,'0')+String(m).padStart(2,'0')+'-'+i,
      date:iso,
      displayTime:new Date(iso).toLocaleString([],{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}),
      title:b.title||"NBL Pilipinas Governor's Cup 2026",
      home:'NBL-Pilipinas',
      away:'Broadcast',
      homeScore:'—',awayScore:'—',
      status:'Scheduled · '+(b.source||'Official broadcaster'),
      state:'scheduled',
      eventOnly:true,
      sourceName:b.source||'Tap Sports',
      sourceUrl:'https://tapdmv.com/tapsports/',
      highlights:[],highlightsChecked:true,
      streams:[],streamsChecked:true,
      odds:null,oddsList:[]
    };
  }).filter(Boolean);
}

async function nblYoutubeScheduledGames(){
  try{
    const r=await fetch('/youtube-live.json?ts='+Date.now(),{cache:'no-store'});
    if(!r.ok)return [];
    const y=await r.json();
    return (Array.isArray(y.upcoming)?y.upcoming:[])
      .filter(x=>x?.leagueKey==='nbl'&&x?.stream?.watchUrl&&x?.scheduledStartTime)
      .map(x=>({
        eventId:x.eventId,
        date:x.scheduledStartTime,
        displayTime:new Date(x.scheduledStartTime).toLocaleString([],{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}),
        away:x.away||'NBL Pilipinas',
        home:x.home||x.title||'Scheduled game',
        awayScore:'—',homeScore:'—',
        status:'Scheduled stream',
        state:'scheduled',
        sourceName:'NBL Pilipinas Official YouTube',
        sourceUrl:x.stream.watchUrl,
        streams:[x.stream],
        streamsChecked:true,
        highlights:[],highlightsChecked:true,
        odds:null,oddsList:[]
      }));
  }catch{return []}
}

async function loadGames({silent=false,league=currentScoreLeague}={}){
  const requestToken=++scoreLoadToken;
  if(!document.getElementById('games'))return;
  const st=document.getElementById('gameStatus');
  const sport=league||currentScoreLeague||'soccer';
  await loadSportsStatsData();
  if(sport==='ufc'||sport==='one')await loadSpecialSportsData();
  const isCurrent=()=>requestToken===scoreLoadToken&&currentScoreLeague===sport;
  const isWebLeague=['pba','uaap','mpbl','nbl','nblaus','vba'].includes(sport);
  if(!silent)st.textContent='';

  if(isWebLeague){
    await loadRegionalAutoData();
    let webGames=regionalSnapshotGames(sport);
    if(sport==='nbl'){
      const upcoming=await nblYoutubeScheduledGames();
      const broadcasts=nblBroadcastScheduleGames();
      const seen=new Set(webGames.map(g=>String(g.eventId)));
      const exactScheduled=[...upcoming,...webGames].some(g=>g?.state==='scheduled'&&!g?.eventOnly);
      const broadcastFallback=exactScheduled?[]:broadcasts;
      webGames=[
        ...upcoming.filter(g=>!seen.has(String(g.eventId))),
        ...broadcastFallback.filter(g=>!seen.has(String(g.eventId))),
        ...webGames
      ];
    }
    await hydrateTeamLogos(sport,webGames);

    // GitHub-hosted regional data is the stable primary layer.
    // Never clear or replace it just because the Cloudflare fallback is unavailable.
    if(!silent&&webGames.length&&isCurrent()){
      allGames=webGames;
      st.textContent='';
      renderRegionalContext(sport,'web');
      renderGames();
    }else if(!allGames.length&&webGames.length&&isCurrent()){
      allGames=webGames;
    }

    try{
      const j=await fetchScorePayload(sport,{fallbackOnly:true});
      const liveGames=normalizeScorePayload(sport,j).filter(g=>g.state==='live');
      await hydrateTeamLogos(sport,liveGames);

      if(liveGames.length&&isCurrent()){
        const base=webGames.length?webGames:allGames;
        const liveMatchups=new Set(liveGames.map(g=>(g.away+'|'+g.home).toLowerCase()));
        allGames=[
          ...liveGames,
          ...base.filter(g=>g.state!=='live'&&!liveMatchups.has((g.away+'|'+g.home).toLowerCase()))
        ];
        st.textContent='';
        renderRegionalContext(sport,'cloudflare-fallback');
        if(silent)updateScoreNumbers();else renderGames();
        if(!silent)void hydrateLiveStreams(sport);
        return;
      }
    }catch{}

    if(webGames.length&&isCurrent()){
      if(!allGames.length)allGames=webGames;
      st.textContent='';
      if(silent)updateScoreNumbers();else renderGames();
      return;
    }
  }

  const hasRegionalSnapshot=Boolean(getRegionalSnapshot(sport));
  let mode='api';
  try{
    const j=await fetchScorePayload(sport);
    let nextGames=normalizeScorePayload(sport,j);

    if(specialScoreKeys.has(sport)){
      const specialPayload=await specialSportsPayload(sport);
      const specialGames=specialPayload?normalizeScorePayload(sport,specialPayload):[];
      const usablePrimary=nextGames.filter(g=>!scoreGameLooksGeneric(g));
      nextGames=usablePrimary.length?mergeScoreGames(usablePrimary,specialGames):specialGames;
      if(specialGames.length)mode='official-web-fallback';
    }

    await hydrateTeamLogos(sport,nextGames);

    if(hasRegionalSnapshot&&!nextGames.length){
      nextGames=regionalSnapshotGames(sport);
      await hydrateTeamLogos(sport,nextGames);
      mode='web';
    }

    if(sport==='basketball'&&!nextGames.length){
      const now=new Date(),end=new Date(now);
      end.setDate(end.getDate()+14);
      const [backup,logoMap]=await Promise.all([
        fetch('https://img-api-proxy.magsipocarnie.workers.dev/games?start_date='+now.toISOString().slice(0,10)+'&end_date='+end.toISOString().slice(0,10)+'&per_page=100',{cache:'no-store'}),
        getNbaLogoMap()
      ]);
      if(backup.ok){
        const b=await backup.json();
        nextGames=(b.data||[]).map(g=>{
          const home=g.home_team?.full_name||'Home',away=g.visitor_team?.full_name||'Away';
          return{eventId:'',date:g.date,home,away,homeLogo:logoMap[String(home).toLowerCase()]||'',awayLogo:logoMap[String(away).toLowerCase()]||'',homeScore:g.home_team_score||'—',awayScore:g.visitor_team_score||'—',status:g.status||'Scheduled',state:/live|q[1-4]|half|quarter|ot|in progress/i.test(String(g.status||''))?'live':String(g.status||'').toLowerCase().includes('final')?'final':'scheduled',odds:null,highlights:[],highlightsChecked:true,streams:[],streamsChecked:true}
        });
      }
    }

    if(sport==='asian_games'){
      try{
        const external=await loadExternalLiveData();
        const liveDecorated=nextGames.map(g=>({...g,sportKey:'asian_games',sportLabel:asianGamesSportLabel(g)}));
        attachExternalAsianGamesStreams(liveDecorated,external);
        nextGames=liveDecorated.map(g=>{const {sportKey,sportLabel,...rest}=g;return rest;});
      }catch{}
    }

    if(!isCurrent())return;
    allGames=nextGames;
    st.textContent='';
    renderRegionalContext(sport,mode);
    if(silent)updateScoreNumbers();else renderGames();
    if(mode!=='web'&&mode!=='official-web-fallback'&&!silent){
      void hydrateHighlights(sport);
      void hydrateLiveStreams(sport);
    }
  }catch{
    if(!isCurrent())return;
    if(hasRegionalSnapshot){
      allGames=regionalSnapshotGames(sport);
      await hydrateTeamLogos(sport,allGames);
      if(!isCurrent())return;
      st.textContent='';
      renderRegionalContext(sport,'web');
      if(silent)updateScoreNumbers();else renderGames();
    }else{
      renderRegionalContext(sport,'');
      st.textContent='Feed unavailable';
      if(!silent)document.getElementById('games').innerHTML='<div class="empty">This public score feed is temporarily unavailable.</div>';
    }
  }
}
function clean(html){const d=document.createElement('div');d.innerHTML=html||'';return d.textContent.trim().replace(/Continue reading.*$/i,'').slice(0,260)}function parseXML(x){const d=new DOMParser().parseFromString(x,'application/xml');return [...d.querySelectorAll('item')].map(i=>({title:i.querySelector('title')?.textContent||'',link:i.querySelector('link')?.textContent||'',description:clean(i.querySelector('description')?.textContent),source:d.querySelector('channel>title')?.textContent||'Sports News',sport:i.querySelector('category')?.textContent||'Sports',image:i.getElementsByTagName('media:content')[0]?.getAttribute('url')||''})).filter(x=>x.title&&x.link)}
function renderNews(items,videos=[]){
  const host=document.getElementById('newsFeed');
  if(!host)return;
  if(!items.length&&!videos.length)return;

  const videoRows=(Array.isArray(videos)?videos:[]).filter(v=>v?.id&&v?.thumbnail).slice(0,2);
  const videosHtml=videoRows.length
    ? '<section class="news-videos" aria-label="Sports videos">'+videoRows.map(v=>
        '<article class="news-video-card" data-news-video="'+esc(v.id)+'">'+
          '<button class="news-video-frame news-video-link" type="button" data-play-news-video="'+esc(v.id)+'" aria-label="Play '+esc(v.title||'sports video')+'">'+
            '<img src="'+esc(v.thumbnail)+'" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src=\'about-sports.jpg\'">'+
            '<span class="news-video-play" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span>'+
          '</button>'+
          '<div class="news-video-copy"><div class="tag">Video</div><h3>'+esc(v.title||'Sports video')+'</h3><small>'+esc(v.source||'Sports')+'</small></div>'+
        '</article>'
      ).join('')+'</section>'
    : '';

  if(!items.length){
    host.innerHTML=videosHtml;
  }else{
    const first=items[0];
    host.innerHTML=videosHtml+
      '<article class="lead-story">'+
        (first.image?'<img src="'+esc(first.image)+'" alt="" referrerpolicy="no-referrer">':'<div></div>')+
        '<div><div class="tag">'+esc(first.sport)+'</div><a href="'+esc(first.link)+'" target="_blank" rel="noopener"><h2>'+esc(first.title)+'</h2></a><p>'+esc(first.description)+'</p><small>'+esc(first.source)+'</small></div>'+
      '</article>'+
      '<div class="news-list">'+items.slice(1,9).map(n=>
        '<article class="news-row"><img src="'+esc(n.image||'about-sports.jpg')+'" alt="" loading="lazy" referrerpolicy="no-referrer"><div><div class="tag">'+esc(n.sport)+'</div><a href="'+esc(n.link)+'" target="_blank" rel="noopener"><h3>'+esc(n.title)+'</h3></a><small>'+esc(n.source)+'</small></div><span class="arrow">↗</span></article>'
      ).join('')+'</div>';
  }

  const s=document.getElementById('newsStatus');
  if(s){
    s.textContent='';
    s.closest('.news-livebar')?.classList.add('is-empty');
  }
}

async function loadNews(){
  const host=document.getElementById('newsFeed');
  if(!host)return;
  const ns=document.getElementById('newsStatus');
  ns?.closest('.news-livebar')?.classList.remove('is-empty');
  if(ns)ns.textContent='Updating';

  const tryItems=async(url,type)=>{
    const r=await fetch(url,{cache:'no-store'});
    if(!r.ok)throw new Error('HTTP '+r.status);
    if(type==='json'){
      const j=await r.json();
      const items=Array.isArray(j?.items)?j.items:[];
      if(!items.length)throw new Error('Empty news feed');
      return {items,videos:Array.isArray(j?.videos)?j.videos:[]};
    }
    const t=await r.text();
    const items=t.trim().startsWith('{')?(JSON.parse(t).items||[]):parseXML(t);
    if(!items.length)throw new Error('Empty news feed');
    return {items,videos:[]};
  };

  try{
    const data=await tryItems('news-data.json?v='+Date.now(),'json');
    renderNews(data.items,data.videos);
    return;
  }catch{}

  try{
    const data=await tryItems('https://img-api-proxy.magsipocarnie.workers.dev/news','worker');
    renderNews(data.items,data.videos);
    return;
  }catch{}

  if(ns)ns.textContent='';
  host.innerHTML='<div class="empty">The live news feed is temporarily unavailable.</div>';
}
function oddsHasValue(value){return value!==undefined&&value!==null&&String(value).trim()!==''&&String(value)!=='—'}
function oddsMarketAvailable(game,market){
  const list=game?.oddsList||[];
  if(market==='win')return list.some(o=>oddsHasValue(o.away)||oddsHasValue(o.home)||oddsHasValue(o.draw));
  if(market==='spread')return list.some(o=>oddsHasValue(o.details));
  if(market==='total')return list.some(o=>oddsHasValue(o.total));
  return false;
}
function oddsTeamInitials(name){return String(name||'').split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join('').toUpperCase()||'IMG'}
function oddsTeamVisual(url,name,side){
  return url?'<img class="odds-hero-logo" src="'+esc(url)+'" alt="'+esc(name)+' logo" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.outerHTML=\'<span class=&quot;odds-team-fallback&quot;>'+esc(oddsTeamInitials(name))+'</span>\'">':'<span class="odds-team-fallback">'+esc(oddsTeamInitials(name))+'</span>';
}
function oddsMarketRows(game,market){
  const rows=(game.oddsList||[]).filter(o=>{
    if(market==='win')return oddsHasValue(o.away)||oddsHasValue(o.home)||oddsHasValue(o.draw);
    if(market==='spread')return oddsHasValue(o.details);
    return oddsHasValue(o.total);
  });
  if(!rows.length)return '<div class="odds-market-empty">This market is not available from the connected feed.</div>';

  if(market==='win'){
    const hasDraw=rows.some(o=>oddsHasValue(o.draw));
    return '<div class="odds-table-head'+(hasDraw?' has-draw':'')+'"><span>Bookmaker</span><span>'+esc(game.away)+'</span>'+(hasDraw?'<span>Draw</span>':'')+'<span>'+esc(game.home)+'</span></div>'+
      rows.map(o=>'<div class="odds-table-row'+(hasDraw?' has-draw':'')+'"><strong>'+esc(o.provider)+'</strong><span class="odds-price">'+esc(oddsHasValue(o.away)?o.away:'—')+'</span>'+(hasDraw?'<span class="odds-price">'+esc(oddsHasValue(o.draw)?o.draw:'—')+'</span>':'')+'<span class="odds-price">'+esc(oddsHasValue(o.home)?o.home:'—')+'</span></div>').join('');
  }

  if(market==='spread'){
    return '<div class="odds-table-head odds-table-two"><span>Bookmaker</span><span>Spread / line</span></div>'+
      rows.map(o=>'<div class="odds-table-row odds-table-two"><strong>'+esc(o.provider)+'</strong><span class="odds-price">'+esc(o.details)+'</span></div>').join('');
  }

  return '<div class="odds-table-head odds-table-two"><span>Bookmaker</span><span>Total</span></div>'+
    rows.map(o=>'<div class="odds-table-row odds-table-two"><strong>'+esc(o.provider)+'</strong><span class="odds-price">'+esc(o.total)+'</span></div>').join('');
}
function oddsSportIcon(label){
  const icons={
    all:'grid_view',
    Football:'sports_soccer',
    Basketball:'sports_basketball',
    Baseball:'sports_baseball',
    Hockey:'sports_hockey',
    'American Football':'sports_football'
  };
  return '<span class="material-symbols-rounded odds-sport-icon" aria-hidden="true">'+esc(icons[label]||'sports')+'</span>';
}

function oddsLeagueFallback(key){
  const name=oddsLeagueNames[key]||key.toUpperCase();
  return '<span class="odds-league-fallback">'+esc(name.replace(/[^A-Za-z0-9]/g,'').slice(0,4).toUpperCase())+'</span>';
}

function oddsLeagueLogoMarkup(key){
  const logo=oddsLeagueLogos[key]||'';
  const fallback=oddsLeagueFallback(key);
  if(!logo)return fallback;
  return '<img class="odds-league-logo-img" src="'+esc(logo)+'" alt="'+esc(oddsLeagueNames[key]||key)+' logo" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'grid\'">'+
    '<span class="odds-league-fallback odds-league-fallback-hidden">'+esc((oddsLeagueNames[key]||key).replace(/[^A-Za-z0-9]/g,'').slice(0,4).toUpperCase())+'</span>';
}

function clearOddsLeaguePanelTimer(){
  clearTimeout(oddsLeaguePanelTimer);
  oddsLeaguePanelTimer=0;
}

function closeOddsLeaguePanel(){
  clearOddsLeaguePanelTimer();
  oddsLeaguePanelOpen=false;
  const row=document.querySelector('.odds-league-row');
  if(row){
    row.classList.remove('is-open');
    row.setAttribute('aria-hidden','true');
  }
  document.querySelectorAll('[data-odds-sport]').forEach(btn=>btn.setAttribute('aria-expanded','false'));
}

function armOddsLeaguePanelTimer(){
  clearOddsLeaguePanelTimer();
  if(!oddsLeaguePanelOpen)return;
  oddsLeaguePanelTimer=setTimeout(closeOddsLeaguePanel,5000);
}

function openOddsLeaguePanel(){
  oddsLeaguePanelOpen=true;
  const row=document.querySelector('.odds-league-row');
  if(row){
    row.classList.add('is-open');
    row.setAttribute('aria-hidden','false');
  }
  document.querySelectorAll('[data-odds-sport]').forEach(btn=>{
    btn.setAttribute('aria-expanded',String(btn.dataset.oddsSport===currentOddsSport));
  });
  armOddsLeaguePanelTimer();
}

function renderOddsFilters(){
  const sportHost=document.getElementById('oddsSportFilters');
  const leagueHost=document.getElementById('oddsLeagueFilters');
  const leagueRow=document.querySelector('.odds-league-row');
  if(!sportHost||!leagueHost||!leagueRow)return;

  const keys=Object.keys(availableOdds);
  const sportOrder=['Football','Basketball','American Football','Baseball','Hockey'];
  const sports=[...new Set(keys.map(k=>oddsLeagueSports[k]).filter(Boolean))].sort((a,b)=>{
    const ai=sportOrder.indexOf(a),bi=sportOrder.indexOf(b);
    return (ai<0?99:ai)-(bi<0?99:bi)||a.localeCompare(b);
  });
  if(currentOddsSport!=='all'&&!sports.includes(currentOddsSport))currentOddsSport='all';

  sportHost.innerHTML=[['all','All'],...sports.map(s=>[s,s])].map(([value,label])=>
    '<button type="button" class="odds-sport-filter'+(currentOddsSport===value?' active':'')+'" data-odds-sport="'+esc(value)+'" aria-label="'+esc(label)+'" aria-expanded="'+String(oddsLeaguePanelOpen&&currentOddsSport===value)+'">'+
      oddsSportIcon(value)+
      '<span>'+esc(label)+'</span>'+
    '</button>'
  ).join('');

  const visibleKeys=keys.filter(k=>currentOddsSport==='all'||oddsLeagueSports[k]===currentOddsSport);

  leagueHost.innerHTML=visibleKeys.map(key=>
    '<button type="button" class="odds-league-filter'+(currentOddsLeague===key?' active':'')+'" data-odds-league="'+esc(key)+'" aria-label="'+esc(oddsLeagueNames[key]||key)+'">'+
      '<span class="odds-league-logo-wrap">'+oddsLeagueLogoMarkup(key)+'</span>'+
      '<span class="odds-league-filter-name">'+esc(oddsLeagueNames[key]||key.toUpperCase())+'</span>'+
    '</button>'
  ).join('');

  leagueRow.classList.toggle('is-open',oddsLeaguePanelOpen);
  leagueRow.setAttribute('aria-hidden',String(!oddsLeaguePanelOpen));

  sportHost.querySelectorAll('[data-odds-sport]').forEach(btn=>btn.addEventListener('click',()=>{
    const selected=btn.dataset.oddsSport||'all';
    if(oddsLeaguePanelOpen&&currentOddsSport===selected){
      closeOddsLeaguePanel();
      return;
    }
    currentOddsSport=selected;
    oddsLeaguePanelOpen=true;
    renderOddsFilters();
    openOddsLeaguePanel();
  }));

  leagueHost.querySelectorAll('[data-odds-league]').forEach(btn=>btn.addEventListener('click',()=>{
    currentOddsLeague=btn.dataset.oddsLeague||'';
    currentOddsSport=oddsLeagueSports[currentOddsLeague]||currentOddsSport;
    renderOddsFilters();
    renderOdds();
    closeOddsLeaguePanel();
  }));
}

function renderOdds(){
  const host=document.getElementById('oddsFeed'),league=currentOddsLeague,items=availableOdds[league]||[];
  if(!host)return;

  const ordered=[...items].sort((a,b)=>{
    const ar=a.state==='live'?0:1,br=b.state==='live'?0:1;
    if(ar!==br)return ar-br;
    return (Date.parse(a.date||'')||0)-(Date.parse(b.date||'')||0);
  });

  host.innerHTML=ordered.map((g,index)=>{
    const win=oddsMarketAvailable(g,'win'),spread=oddsMarketAvailable(g,'spread'),total=oddsMarketAvailable(g,'total');
    const initial=win?'win':spread?'spread':'total';
    const isLive=g.state==='live';
    const eventDate=g.date?new Date(g.date):null;
    const when=isLive?'LIVE · '+esc(g.status||'In progress'):eventDate&&!Number.isNaN(eventDate.getTime())?esc(eventDate.toLocaleString([],{weekday:'short',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})):'Scheduled';
    const score=isLive||g.state==='final';
    const awayScore=score&&g.awayScore!==undefined?'<b data-odds-score-side="away">'+esc(g.awayScore)+'</b>':'';
    const homeScore=score&&g.homeScore!==undefined?'<b data-odds-score-side="home">'+esc(g.homeScore)+'</b>':'';
    const marketLabel=isLive?'Pregame odds shown unless the provider explicitly supplies in-play prices':'Pre-match odds';

    return '<article class="odds-match-card'+(isLive?' odds-match-live':'')+'" data-odds-event="'+esc(g.eventId||String(index))+'">'+
      '<div class="odds-game-hero">'+
        '<div class="odds-game-meta"><span class="odds-league-name">'+esc(oddsLeagueNames[league]||league.toUpperCase())+'</span><span class="odds-game-time">'+when+'</span></div>'+
        '<div class="odds-hero-matchup">'+
          '<div class="odds-hero-team">'+oddsTeamVisual(g.awayLogo,g.away,'away')+'<span>'+esc(g.away)+'</span>'+awayScore+'</div>'+
          '<div class="odds-hero-center"><span>'+(isLive?'LIVE':'VS')+'</span></div>'+
          '<div class="odds-hero-team">'+oddsTeamVisual(g.homeLogo,g.home,'home')+'<span>'+esc(g.home)+'</span>'+homeScore+'</div>'+
        '</div>'+
      '</div>'+
      '<div class="odds-market-card">'+
        '<div class="odds-market-tabs" role="tablist" aria-label="Odds markets">'+
          '<button type="button" data-market="win" class="'+(initial==='win'?'active':'')+'" '+(win?'':'disabled')+'>To Win</button>'+
          '<button type="button" data-market="spread" class="'+(initial==='spread'?'active':'')+'" '+(spread?'':'disabled')+'>Spread</button>'+
          '<button type="button" data-market="total" class="'+(initial==='total'?'active':'')+'" '+(total?'':'disabled')+'>Total Points</button>'+
        '</div>'+
        '<div class="odds-market-note"><span class="'+(isLive?'odds-note-live':'')+'">'+esc(marketLabel)+'</span></div>'+
        '<div class="odds-market-pane '+(initial==='win'?'active':'')+'" data-pane="win">'+oddsMarketRows(g,'win')+'</div>'+
        '<div class="odds-market-pane '+(initial==='spread'?'active':'')+'" data-pane="spread">'+oddsMarketRows(g,'spread')+'</div>'+
        '<div class="odds-market-pane '+(initial==='total'?'active':'')+'" data-pane="total">'+oddsMarketRows(g,'total')+'</div>'+
      '</div>'+
    '</article>';
  }).join('');

  host.querySelectorAll('.odds-market-tabs button:not(:disabled)').forEach(btn=>{
    btn.addEventListener('click',()=>{
      const card=btn.closest('.odds-match-card'),market=btn.dataset.market;
      card.querySelectorAll('.odds-market-tabs button').forEach(x=>x.classList.toggle('active',x===btn));
      card.querySelectorAll('.odds-market-pane').forEach(x=>x.classList.toggle('active',x.dataset.pane===market));
    });
  });
}
async function loadBet365Odds(){
  try{
    const r=await fetch('odds-data.json?v='+Date.now(),{cache:'no-store'});
    if(!r.ok)return{};
    const j=await r.json();
    const leagues=j?.leagues||{};
    return Object.fromEntries(Object.entries(leagues).filter(([,items])=>Array.isArray(items)&&items.length));
  }catch{
    return{};
  }
}
async function discoverOdds(){
  const host=document.getElementById('oddsFeed'),status=document.getElementById('oddsStatus');
  if(!host)return;
  status.textContent='Updating';
  host.setAttribute('aria-busy','true');
  const previous=currentOddsLeague;

  const [bet365Data,espnResults]=await Promise.all([
    loadBet365Odds(),
    Promise.all(Object.entries(oddsFeeds).map(async([key,url])=>{
      try{
        const r=await fetch(url,{cache:'no-store'});
        if(!r.ok)return {key,items:[],logo:''};
        const j=await r.json();
        const leagueMeta=j?.leagues?.[0]||{};
        const logo=leagueMeta?.logos?.[0]?.href||leagueMeta?.logo||'';
        const items=(j.events||[]).map(normalizeEvent).filter(x=>x.oddsList.length);
        return {key,items,logo};
      }catch{
        return {key,items:[],logo:''};
      }
    }))
  ]);

  oddsLeagueLogos=Object.fromEntries(espnResults.filter(x=>x.logo).map(x=>[x.key,x.logo]));
  availableOdds=Object.fromEntries(espnResults.filter(x=>x.items.length).map(x=>[x.key,x.items]));

  for(const [key,items] of Object.entries(bet365Data)){
    if(!Array.isArray(items)||!items.length)continue;
    const current=availableOdds[key]||[];
    const merged=[...current];
    for(const saved of items){
      const match=merged.find(g=>String(g.eventId||'')===String(saved.eventId||'')||(
        String(g.home||'').toLowerCase()===String(saved.home||'').toLowerCase()&&
        String(g.away||'').toLowerCase()===String(saved.away||'').toLowerCase()&&
        String(g.date||'').slice(0,10)===String(saved.date||'').slice(0,10)
      ));
      if(match){
        const providers=new Set((match.oddsList||[]).map(o=>String(o.provider||'').toLowerCase()));
        match.oddsList=[...(match.oddsList||[]),...(saved.oddsList||[]).filter(o=>!providers.has(String(o.provider||'').toLowerCase()))];
      }else{
        merged.push({...saved,state:saved.state||'scheduled',status:saved.status||'Scheduled'});
      }
    }
    availableOdds[key]=merged;
  }

  await Promise.allSettled(Object.entries(availableOdds).map(([key,items])=>
    hydrateTeamLogos(oddsLogoSportKey[key]||key,items)
  ));

  const keys=Object.keys(availableOdds);
  currentOddsLeague=keys.includes(previous)?previous:(keys[0]||'');
  if(currentOddsLeague)currentOddsSport=oddsLeagueSports[currentOddsLeague]||'all';
  renderOddsFilters();
  if(keys.length)renderOdds();else host.innerHTML='';
  status.textContent='';
  host.setAttribute('aria-busy','false');
}

if(document.getElementById('games')){
  // Expiry cannot depend on an upstream request completing successfully.
  setInterval(expireVisibleAsianGames,1000);
  let scoreAutoRefreshTimer=0;
  let scoreRefreshInFlight=false;

  const hasLiveScores=()=>allGames.some(g=>g.state==='live')||liveNowItems.some(liveNowItemIsCurrent);
  const nextScoreRefreshDelay=()=>hasLiveScores()?15000:30000;

  const scheduleScoreAutoRefresh=(delay=nextScoreRefreshDelay())=>{
    clearTimeout(scoreAutoRefreshTimer);
    if(document.hidden)return;
    scoreAutoRefreshTimer=setTimeout(refreshScoresAutomatically,delay);
  };

  async function refreshScoresAutomatically(){
    if(scoreRefreshInFlight){
      scheduleScoreAutoRefresh(30000);
      return;
    }
    scoreRefreshInFlight=true;
    try{
      const selectedSport=currentScoreLeague;
      await loadGames({silent:true,league:selectedSport});
      // Rebuild the complete Live Now feed on every refresh so newly live,
      // finished, removed and newly discovered stream events update automatically.
      await loadAllLiveGames({silent:true});
    }finally{
      scoreRefreshInFlight=false;
      scheduleScoreAutoRefresh();
    }
  }

  renderScoreLeagueFilters();
  void loadScoreLeagueLogos();
  Promise.allSettled([loadGames(),loadAllLiveGames()]).finally(()=>scheduleScoreAutoRefresh());

  document.addEventListener('visibilitychange',()=>{
    expireVisibleAsianGames();
    clearTimeout(scoreAutoRefreshTimer);
    if(!document.hidden)refreshScoresAutomatically();
  });
}if(document.getElementById('newsFeed')){loadNews();setInterval(loadNews,300000)}if(document.getElementById('oddsFeed')){
  discoverOdds();
  setInterval(discoverOdds,300000);

  let oddsLastScrollY=scrollY;
  addEventListener('scroll',()=>{
    const y=scrollY;
    if(oddsLeaguePanelOpen&&y>oddsLastScrollY+2)closeOddsLeaguePanel();
    oddsLastScrollY=y;
  },{passive:true});

  document.addEventListener('pointerdown',e=>{
    if(!oddsLeaguePanelOpen)return;
    if(e.target.closest('#oddsSportFilters')||e.target.closest('.odds-league-row'))return;
    closeOddsLeaguePanel();
  },{passive:true});
}
