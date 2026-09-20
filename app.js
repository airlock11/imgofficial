const root=document.documentElement,savedTheme=localStorage.getItem('img-theme')||'dark';
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
  const savedPosition=JSON.parse(localStorage.getItem('img-theme-position')||'null');
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
    localStorage.setItem('img-theme-position',JSON.stringify({x:Math.round(r.left),y:Math.round(r.top)}));
  }else{
    root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';
    localStorage.setItem('img-theme',root.dataset.theme);
    paint();
  }
});
theme.addEventListener('click',()=>{
  if(isMobileTheme())return;
  root.dataset.theme=root.dataset.theme==='dark'?'light':'dark';
  localStorage.setItem('img-theme',root.dataset.theme);
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
document.querySelectorAll('.bottomnav a').forEach(a=>{let label=a.textContent.trim();if(label==='Tools'){a.href='odds.html';a.childNodes[a.childNodes.length-1].textContent='Odds';label='Odds'}const b=a.querySelector('b');if(b&&navIcons[label])b.innerHTML='<span class="navglyph icon-'+navIcons[label]+'" aria-hidden="true"></span>';if(a.classList.contains('active'))a.setAttribute('aria-current','page')});
document.querySelectorAll('.navlinks a').forEach(a=>{const label=a.textContent.trim();if(a.classList.contains('active'))a.setAttribute('aria-current','page')});
document.querySelector('header nav')?.setAttribute('aria-label','Primary navigation');document.querySelectorAll('.bottomnav').forEach(n=>{n.setAttribute('role','navigation');n.setAttribute('aria-label','Mobile navigation')});
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const leagues={Basketball:[['NBA','United States / Canada'],['WNBA','United States / Canada'],['PBA','Philippines'],['MPBL','Philippines'],['NBL-Pilipinas','Philippines'],['NBL Australia','Australia / New Zealand'],['VBA','Vietnam'],['B.League','Japan'],['EuroLeague','Europe'],['WBSL','International']],Football:[['Premier League','England'],['La Liga','Spain'],['Serie A','Italy'],['Bundesliga','Germany'],['UEFA Champions League','Europe'],['Philippine Football League','Philippines']],Tennis:[['ATP Tour','International'],['WTA Tour','International'],['Australian Open','Australia'],['Wimbledon','United Kingdom'],['US Open','United States']],Baseball:[['MLB','USA / Canada'],['NPB','Japan'],['KBO League','South Korea']],Hockey:[['NHL','USA / Canada'],['KHL','Eurasia'],['IIHF World Championship','International']],Cricket:[['IPL','India'],['Big Bash League','Australia'],['ICC Cricket World Cup','International']],Volleyball:[['Volleyball Nations League','International'],['PVL','Philippines'],['V.League','Japan']],Motorsport:[['Formula 1','International'],['MotoGP','International'],['Formula E','International']],Boxing:[['WBC','International'],['WBA','International'],['IBF','International'],['WBO','International'],['Professional Boxing','Worldwide']],'Combat Sports':[['UFC','International'],['ONE Championship','Asia']],'American Football':[['NFL','United States'],['NCAA Football','United States']]};
function openSport(name){if(name==='Boxing'){location.href='boxing.html';return}const modal=document.getElementById('sportModal');if(!modal)return;modal.querySelector('h2').textContent=name;modal.querySelector('.modalbody').innerHTML=(leagues[name]||[]).map(x=>'<div class="league-row"><strong>'+esc(x[0])+'</strong><small>'+esc(x[1])+'</small></div>').join('');modal.showModal()}
document.addEventListener('click',e=>{const sport=e.target.closest('[data-sport]');if(sport)openSport(sport.dataset.sport);if(e.target.matches('.close'))e.target.closest('dialog').close();const highlightButton=e.target.closest('[data-highlight-event]');if(highlightButton)openHighlights(highlightButton.dataset.highlightEvent);const liveButton=e.target.closest('[data-live-event]');if(liveButton)openLiveStream(liveButton.dataset.liveEvent)});
const scoreFeeds={
  soccer:'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard',
  laliga:'https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard',
  seriea:'https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard',
  bundesliga:'https://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/scoreboard',
  champions:'https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard',
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

async function fetchScorePayload(sport,{fallbackOnly=false}={}){
  if(!fallbackOnly&&scoreFeeds[sport]){
    try{
      const r=await fetch(scoreFeeds[sport],{cache:'no-store'});
      if(r.ok){
        const j=await r.json();
        if(Array.isArray(j?.events))return j;
      }
    }catch{}
  }

  const fallback=cloudflareFallbackFeeds[sport];
  if(!fallback)throw new Error('Score feed unavailable');
  const r=await fetch(fallback,{cache:'no-store'});
  if(!r.ok)throw new Error('Fallback score feed unavailable');
  const j=await r.json();
  if(!Array.isArray(j?.events))throw new Error('Invalid fallback score feed');
  return j;
}
const liveNowLabels={
  soccer:{sport:'Football',league:'Premier League'},
  laliga:{sport:'Football',league:'La Liga'},
  seriea:{sport:'Football',league:'Serie A'},
  bundesliga:{sport:'Football',league:'Bundesliga'},
  champions:{sport:'Football',league:'UEFA Champions League'},
  basketball:{sport:'Basketball',league:'NBA'},
  wnba:{sport:'Basketball',league:'WNBA'},
  atp:{sport:'Tennis',league:'ATP Tour'},
  wta:{sport:'Tennis',league:'WTA Tour'},
  ipl:{sport:'Cricket',league:'IPL'},
  volleyball_w:{sport:'Volleyball',league:'FIVB Women'},
  volleyball_m:{sport:'Volleyball',league:'FIVB Men'},
  f1:{sport:'Motorsport',league:'Formula 1'},
  ufc:{sport:'Combat Sports',league:'UFC'},
  pba:{sport:'Basketball',league:'PBA'},
  mpbl:{sport:'Basketball',league:'MPBL'},
  nbl:{sport:'Basketball',league:'NBL-Pilipinas'},
  nblaus:{sport:'Basketball',league:'NBL Australia'},
  vba:{sport:'Basketball',league:'VBA'},
  baseball:{sport:'Baseball',league:'MLB'},
  hockey:{sport:'Hockey',league:'NHL'},
  football:{sport:'American Football',league:'NFL'},
  ncaaf:{sport:'American Football',league:'NCAA Football'}
};
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
  return snapshot?(snapshot.games||[]).map(g=>({...g,homeLogo:g.homeLogo||'',awayLogo:g.awayLogo||'',odds:null,oddsList:[],highlights:[],highlightsChecked:true,streams:[],streamsChecked:true})):[];
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
const oddsLeagueNames={nfl:'NFL',ncaaf:'NCAA Football',nba:'NBA',wnba:'WNBA',ncaam:"NCAA Men's Basketball",mlb:'MLB',nhl:'NHL',epl:'Premier League',laliga:'La Liga',seriea:'Serie A',bundesliga:'Bundesliga',ligue1:'Ligue 1',champions:'UEFA Champions League',mls:'MLS'};let availableOdds={};
function mapOdds(o){return{provider:o.provider?.displayName||o.provider?.name||'Odds provider',details:o.details||'—',total:o.overUnder??'—',home:o.moneyline?.home?.close?.odds||'—',away:o.moneyline?.away?.close?.odds||'—',draw:o.moneyline?.draw?.close?.odds||'—'}}function teamLogoUrl(team){return team?.team?.logo||team?.team?.logos?.[0]?.href||team?.logo||team?.logos?.[0]?.href||''}
function teamLogoMarkup(url,name,extraClass=''){return url?'<img class="team-logo '+extraClass+'" src="'+esc(url)+'" alt="'+esc(name)+' logo" loading="lazy" decoding="async" referrerpolicy="no-referrer" onerror="this.remove()">':''}
async function getNbaLogoMap(){try{const r=await fetch('https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams?limit=100',{cache:'force-cache'});if(!r.ok)return{};const j=await r.json(),list=j.sports?.[0]?.leagues?.[0]?.teams||[];return Object.fromEntries(list.flatMap(x=>{const t=x.team||x,names=[t.displayName,t.name,t.shortDisplayName].filter(Boolean),logo=t.logos?.[0]?.href||t.logo||'';return names.map(n=>[String(n).toLowerCase(),logo])}))}catch{return{}}}
function summaryUrlForGame(sport,eventId){const feed=scoreFeeds[sport];return feed&&eventId?feed.replace(/\/scoreboard(?:\?.*)?$/,'/summary?event='+encodeURIComponent(eventId)):''}
function collectMediaUrls(node,out=[]){if(!node)return out;if(typeof node==='string'){if(/^https?:\/\//i.test(node))out.push(node);return out}if(Array.isArray(node)){node.forEach(x=>collectMediaUrls(x,out));return out}if(typeof node==='object'){for(const [k,val] of Object.entries(node)){if(['href','url','src'].includes(k)&&typeof val==='string'&&/^https?:\/\//i.test(val))out.push(val);else if(typeof val==='object')collectMediaUrls(val,out)}}return out}
function pickPlayableMedia(v){const pools=[v?.links?.source,v?.links?.mobile?.source,v?.links?.streaming,v?.source,v?.sources,v?.media,v?.playback].filter(Boolean),urls=[...new Set(pools.flatMap(x=>collectMediaUrls(x)))];const ranked=urls.sort((a,b)=>{const score=u=>/\.mp4(?:\?|$)/i.test(u)?3:/\.m3u8(?:\?|$)/i.test(u)?2:/video|motion|media/i.test(u)?1:0;return score(b)-score(a)});return ranked.find(u=>/\.mp4(?:\?|$)/i.test(u))||ranked.find(u=>/\.m3u8(?:\?|$)/i.test(u))||ranked[0]||''}
function normalizeHighlightVideo(v){const title=v?.headline||v?.title||v?.description||'Game highlight',thumb=v?.thumbnail||v?.image?.url||v?.images?.[0]?.url||v?.posterImage?.href||v?.poster?.href||'',media=pickPlayableMedia(v),sourceUrl=v?.links?.web?.href||v?.link?.href||v?.href||'';return title&&media?{title,thumb,media,sourceUrl}:null}
function uniqueHighlights(items){const seen=new Set();return items.filter(Boolean).filter(v=>{const key=v.url||v.title;if(seen.has(key))return false;seen.add(key);return true}).slice(0,8)}
function ensureHighlightsDialog(){let d=document.getElementById('highlightsDialog');if(d)return d;d=document.createElement('dialog');d.id='highlightsDialog';d.className='highlights-dialog';d.innerHTML='<div class="highlights-shell"><button class="highlights-close" type="button" aria-label="Close highlights"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg></button><div id="highlightsContent"></div></div>';document.body.append(d);d.addEventListener('click',e=>{if(e.target===d)d.close()});d.querySelector('.highlights-close').addEventListener('click',()=>d.close());d.addEventListener('close',()=>{const v=d.querySelector('#highlightPlayer');if(v){v.pause();v.removeAttribute('src');v.load()}});return d}
function playHighlightClip(index){const d=document.getElementById('highlightsDialog'),gId=d?.dataset?.gameId,g=allGames.find(x=>String(x.eventId)===String(gId));if(!d||!g||!g.highlights?.[index])return;const clip=g.highlights[index],video=d.querySelector('#highlightPlayer'),title=d.querySelector('#highlightNowTitle');if(!video)return;d.dataset.clipIndex=String(index);video.pause();video.poster=clip.thumb||'';video.src=clip.media;video.load();if(title)title.textContent=clip.title;d.querySelectorAll('[data-highlight-index]').forEach((el,i)=>el.classList.toggle('active',i===index));const p=video.play();if(p?.catch)p.catch(()=>{})}
function openHighlights(eventId){const g=allGames.find(x=>String(x.eventId)===String(eventId));if(!g||!g.highlights?.length)return;const d=ensureHighlightsDialog(),host=d.querySelector('#highlightsContent'),first=g.highlights[0];d.dataset.gameId=String(eventId);host.innerHTML='<div class="highlights-head"><h2>'+esc(g.away)+' vs '+esc(g.home)+'</h2><div class="highlight-teams"><span>'+teamLogoMarkup(g.awayLogo,g.away,'highlight-team-logo')+esc(g.away)+'</span><span>'+teamLogoMarkup(g.homeLogo,g.home,'highlight-team-logo')+esc(g.home)+'</span></div></div><div class="highlight-player-wrap"><video id="highlightPlayer" class="highlight-player" controls playsinline preload="metadata" poster="'+esc(first.thumb||'')+'"></video><div class="highlight-now"><strong id="highlightNowTitle">'+esc(first.title)+'</strong><span>ESPN highlight</span></div></div>'+(g.highlights.length>1?'<div class="highlight-playlist">'+g.highlights.map((v,i)=>'<button type="button" class="highlight-card '+(i===0?'active':'')+'" data-highlight-index="'+i+'"><div class="highlight-thumb">'+(v.thumb?'<img src="'+esc(v.thumb)+'" alt="" loading="lazy" referrerpolicy="no-referrer">':'<div class="highlight-placeholder"></div>')+'<span class="highlight-play" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span></div><div class="highlight-copy"><strong>'+esc(v.title)+'</strong><span>Play highlight</span></div></button>').join('')+'</div>':'');d.querySelectorAll('[data-highlight-index]').forEach(btn=>btn.addEventListener('click',()=>playHighlightClip(Number(btn.dataset.highlightIndex))));d.showModal();playHighlightClip(0)}
async function hydrateHighlights(sport){const snapshot=allGames,candidates=snapshot.filter(g=>g.eventId&&g.state!=='scheduled').slice(0,20);if(!candidates.length)return;await Promise.allSettled(candidates.map(async g=>{const url=summaryUrlForGame(sport,g.eventId);if(!url)return;try{const r=await fetch(url,{cache:'no-store'});if(!r.ok)return;const j=await r.json(),raw=[...(Array.isArray(j.videos)?j.videos:[]),...(Array.isArray(j.highlights)?j.highlights:[])];g.highlights=uniqueHighlights(raw.map(normalizeHighlightVideo));g.highlightsChecked=true}catch{g.highlights=[];g.highlightsChecked=true}}));if(allGames===snapshot&&document.getElementById('sportFilter')?.value===sport)renderGames()}

function ensureLiveDialog(){let d=document.getElementById('liveDialog');if(d)return d;d=document.createElement('dialog');d.id='liveDialog';d.className='live-dialog';d.innerHTML='<div class="live-shell"><button class="live-close" type="button" aria-label="Close live stream"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg></button><div id="liveContent"></div></div>';document.body.append(d);d.addEventListener('click',e=>{if(e.target===d)d.close()});d.querySelector('.live-close').addEventListener('click',()=>d.close());d.addEventListener('close',()=>{const frame=d.querySelector('iframe');if(frame)frame.src='about:blank'});return d}
function openLiveStream(eventId){const g=allGames.find(x=>String(x.eventId)===String(eventId));if(!g||!g.streams?.length)return;const d=ensureLiveDialog(),host=d.querySelector('#liveContent'),stream=g.streams[0];host.innerHTML='<div class="live-head"><div class="live-badge"><span></span>Live</div><h2>'+esc(g.away)+' vs '+esc(g.home)+'</h2><div class="highlight-teams"><span>'+teamLogoMarkup(g.awayLogo,g.away,'highlight-team-logo')+esc(g.away)+'</span><span>'+teamLogoMarkup(g.homeLogo,g.home,'highlight-team-logo')+esc(g.home)+'</span></div></div><div class="live-player-wrap"><iframe class="live-player" src="'+esc(stream.embedUrl)+'" title="'+esc(stream.title||'Live stream')+'" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div><div class="live-meta"><strong>'+esc(stream.title||'Live stream')+'</strong><span>'+esc([stream.provider,stream.channel].filter(Boolean).join(' · '))+'</span></div>'+(g.streams.length>1?'<div class="live-sources">'+g.streams.map((s,i)=>'<button type="button" data-live-source="'+i+'">'+esc(s.provider||'Stream')+(s.channel?' · '+esc(s.channel):'')+'</button>').join('')+'</div>':'');d.querySelectorAll('[data-live-source]').forEach(btn=>btn.addEventListener('click',()=>{const s=g.streams[Number(btn.dataset.liveSource)];const frame=d.querySelector('.live-player');if(s&&frame){frame.src=s.embedUrl;d.querySelector('.live-meta strong').textContent=s.title||'Live stream';d.querySelector('.live-meta span').textContent=[s.provider,s.channel].filter(Boolean).join(' · ')}}));d.showModal()}
async function hydrateLiveStreams(sport){const snapshot=allGames,now=Date.now(),candidates=snapshot.filter(g=>g.eventId&&(g.state==='live'||(g.state==='scheduled'&&Math.abs(Date.parse(g.date)-now)<=90*60000))).slice(0,4);if(!candidates.length)return;await Promise.allSettled(candidates.map(async g=>{const key=sport+':'+g.eventId,hit=liveStreamCache.get(key);if(hit&&Date.now()-hit.time<120000){g.streams=hit.items;g.streamsChecked=true;return}try{const q=new URLSearchParams({sport,event:g.eventId,home:g.home,away:g.away}),r=await fetch('https://img-api-proxy.magsipocarnie.workers.dev/streams?'+q.toString(),{cache:'no-store'});if(!r.ok)throw 0;const j=await r.json(),items=Array.isArray(j.items)?j.items.filter(x=>x?.embedUrl):[];g.streams=items;g.streamsChecked=true;liveStreamCache.set(key,{time:Date.now(),items})}catch{g.streams=[];g.streamsChecked=true}}));if(allGames===snapshot&&document.getElementById('sportFilter')?.value===sport)renderGames()}
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
function normalizeEvent(e){
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
  const c=competitions[0],teams=c?.competitors||[],home=teams.find(x=>x.homeAway==='home')||teams[0],away=teams.find(x=>x.homeAway==='away')||teams[1],state=e.status?.type?.state||'pre',oddsList=(c?.odds||[]).filter(o=>o?.provider?.displayName||o?.provider?.name).map(mapOdds);
  return{eventId:e.id||c?.id||'',date:e.date,home:home?.team?.displayName||'Home',away:away?.team?.displayName||'Away',homeLogo:teamLogoUrl(home),awayLogo:teamLogoUrl(away),homeScore:home?.score||'—',awayScore:away?.score||'—',status:e.status?.type?.shortDetail||e.status?.type?.description||'Scheduled',state:state==='in'?'live':state==='post'?'final':'scheduled',odds:oddsList[0]||null,oddsList,highlights:[],highlightsChecked:false,streams:[],streamsChecked:false};
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
      for(const event of (j.events||[])){
        const game=normalizeEvent(event);
        if(game.state==='live')updates.push(game);
      }
    }catch{}
  }));
  updateAllLiveScoreNumbers(updates);
}

let liveSportFilter='all';
let liveNowItems=[];

function liveSportSlug(label){
  return String(label||'sport').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');
}

function liveSportIconMarkup(label){
  const key=String(label||'').toLowerCase();
  const common='viewBox="0 0 24 24" aria-hidden="true" focusable="false"';
  if(key==='all')return '<svg '+common+'><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>';
  if(key==='basketball')return '<svg '+common+'><circle cx="12" cy="12" r="9"/><path d="M3.4 10.2c4.7.2 8.7-2.2 11.4-6.1M9.2 20.2c.2-4.9-2.1-9.2-6-11.7M20.6 13.8c-4.6-.2-8.5 2.1-11.2 6M14.8 3.9c-.2 4.8 2.1 9 6 11.5"/></svg>';
  if(key==='football')return '<svg '+common+'><circle cx="12" cy="12" r="9"/><path d="m12 7 3.4 2.5-1.3 4H9.9l-1.3-4L12 7Zm-3.4 2.5L5.4 8M9.9 13.5l-2 3.7m6.2-3.7 2 3.7m-.7-7.7L18.6 8M7.9 17.2l-.7 2.2m8.9-2.2.7 2.2"/></svg>';
  if(key==='tennis')return '<svg '+common+'><circle cx="12" cy="12" r="9"/><path d="M5.1 6.3c4 2.5 5.8 6.3 5.2 11.2M18.9 17.7c-4-2.5-5.8-6.3-5.2-11.2"/></svg>';
  if(key==='cricket')return '<svg '+common+'><path d="m7 19 4-14 4 1-3.5 14H8.4L7 19Z"/><circle cx="18.2" cy="17.7" r="2.1"/><path d="M6 21h7"/></svg>';
  if(key==='volleyball')return '<svg '+common+'><circle cx="12" cy="12" r="9"/><path d="M12 3c2.2 2 3.5 4.6 3.6 7.3M15.6 10.3c-4.1-.8-7.3.2-9.8 3M5.8 13.3c1.8 3.4 4.5 5.5 8.4 6.6M14.2 19.9c1.8-3.4 2.1-6.7.9-9.8M15.1 10.1c2.8.6 4.6 2.1 5.7 4.4"/></svg>';
  if(key==='baseball')return '<svg '+common+'><circle cx="12" cy="12" r="9"/><path d="M8 4.7c1.1 1.4 1.7 2.9 1.8 4.6M7 7.3l1.5.6M6.5 9.5l1.7.4M16 19.3c-1.1-1.4-1.7-2.9-1.8-4.6M17 16.7l-1.5-.6m2-1.6-1.7-.4"/></svg>';
  if(key==='hockey')return '<svg '+common+'><path d="M6 3h3l4.3 13.4c.3.9 1.2 1.6 2.2 1.6H21v3h-6.1a4.7 4.7 0 0 1-4.5-3.3L6 3Z"/><ellipse cx="5.5" cy="19.5" rx="3.2" ry="1.5"/></svg>';
  if(key==='american football')return '<svg '+common+'><path d="M4 15.7C1.8 11.5 4.4 5 9.2 3.6c4.8-1.4 9.7 2.6 10.8 6.7 1.1 4.2-1.8 9.5-6.6 10.2C8.6 21.2 5.2 18 4 15.7Z"/><path d="m9 9 6 6m-4.7-7.3 1.2 1.2m1.1.1 1.2 1.2m1.1.1 1.2 1.2"/></svg>';
  if(key==='motorsport')return '<svg '+common+'><path d="M5 3v18M6 5h6v5H6m6-5h6v5h-6m0 0h6v5h-6m-6-5h6v5H6"/></svg>';
  if(key==='combat sports')return '<svg '+common+'><path d="M8 5.5V3.8a1.8 1.8 0 0 1 3.6 0V6m0-.5V3.3a1.8 1.8 0 0 1 3.6 0V6m0-.2V4.2a1.8 1.8 0 0 1 3.6 0v6.3c0 5-3 9.5-8.7 9.5H9c-3.9 0-6.5-2.3-6.5-5.5V11a1.8 1.8 0 0 1 3.6 0v2.2H8V5.5Z"/></svg>';
  return '<svg '+common+'><circle cx="12" cy="12" r="8"/><path d="M12 8v8M8 12h8"/></svg>';
}

function liveSportOrder(label){
  const order=['Basketball','Football','Tennis','Cricket','Volleyball','Baseball','Hockey','American Football','Motorsport','Combat Sports'];
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

function renderAllLiveGames(items,{preserveItems=false}={}){
  const section=document.getElementById('allLiveSection');
  const host=document.getElementById('allLiveGames');
  const status=document.getElementById('allLiveStatus');
  if(!host||!section)return;

  if(!preserveItems)liveNowItems=[...items];

  const live=[...liveNowItems].sort((a,b)=>{
    const as=a.sportLabel||'Sport',bs=b.sportLabel||'Sport';
    return liveSportOrder(as)-liveSportOrder(bs)||as.localeCompare(bs)||(a.leagueLabel||'').localeCompare(b.leagueLabel||'')||((Date.parse(a.date||'')||0)-(Date.parse(b.date||'')||0));
  });

  if(!live.length){
    if(liveNowLocked||host.querySelector('.live-game-card')){
      liveNowLocked=true;
      section.hidden=false;
      return;
    }
    section.hidden=true;
    if(status)status.textContent='';
    return;
  }

  section.hidden=false;
  liveNowLocked=true;
  renderLiveSportSorter(live);

  const visible=liveSportFilter==='all'?live:live.filter(g=>(g.sportLabel||'Sport')===liveSportFilter);
  if(status)status.innerHTML='<span class="live-count-dot" aria-hidden="true"></span><span>'+visible.length+' live</span>';

  host.innerHTML=visible.map(g=>{
    if(g.isRacing){
      const place=[g.raceCircuit,g.raceCity].filter(Boolean).join(' · ');
      return '<article class="live-game-card race-live-card" data-game-key="'+esc(gameDomKey(g))+'" data-sport-key="'+esc(g.sportKey||'')+'">'+
        '<div class="live-card-top"><div class="live-sport-label"><span>Motorsport</span><b>Formula 1</b></div><span class="live-badge">LIVE</span></div>'+
        '<div class="race-live-title">'+esc(g.raceTitle||g.home)+'</div>'+
        '<div class="race-live-session">'+esc(g.raceSession||g.away)+'</div>'+
        (place?'<div class="live-card-time">'+esc(place)+'</div>':'')+
        '<div class="live-card-status">'+esc(g.status||'Live')+'</div>'+
      '</article>';
    }
    return '<article class="live-game-card" data-game-key="'+esc(gameDomKey(g))+'" data-sport-key="'+esc(g.sportKey||'')+'">'+
      '<div class="live-card-top"><div class="live-sport-label"><span>'+esc(g.sportLabel||'Sport')+'</span><b>'+esc(g.leagueLabel||'')+'</b></div><span class="live-badge">LIVE</span></div>'+
      '<div class="live-card-time">'+esc(g.displayTime||g.status||'Live')+'</div>'+
      '<div class="live-card-teams">'+
        '<div class="live-card-team"><span>'+teamLogoMarkup(g.awayLogo,g.away,'live-card-logo')+esc(g.away)+'</span><b data-score-side="away">'+esc(g.awayScore)+'</b></div>'+
        '<div class="live-card-team"><span>'+teamLogoMarkup(g.homeLogo,g.home,'live-card-logo')+esc(g.home)+'</span><b data-score-side="home">'+esc(g.homeScore)+'</b></div>'+
      '</div>'+
      '<div class="live-card-status">'+esc(g.status||'Live')+'</div>'+
    '</article>';
  }).join('');
}

async function loadAllLiveGames({silent=false}={}){
  const host=document.getElementById('allLiveGames');
  const status=document.getElementById('allLiveStatus');
  if(!host)return;
  const section=document.getElementById('allLiveSection');
  if(host.querySelector('.live-game-card')){
    liveNowLocked=true;
    if(section)section.hidden=false;
  }

  if(!silent&&!host.querySelector('.live-game-card')){
    if(status)status.textContent='Checking live games';
  }

  const live=[];
  const webKeys=['pba','mpbl','nbl','nblaus','vba'];
  const apiKeys=['soccer','laliga','seriea','bundesliga','champions','basketball','wnba','atp','wta','ipl','volleyball_w','volleyball_m','f1','ufc','baseball','hockey','football','ncaaf'];

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
        for(const event of (j.events||[])){
          const game=normalizeEvent(event);
          if(game.state==='live')live.push({...game,sportKey:key,sportLabel:labels.sport,leagueLabel:labels.league});
        }
      }catch{}
    }));
  })();

  const apiPromise=Promise.all(apiKeys.map(async key=>{
    try{
      const j=await fetchScorePayload(key);
      const labels=liveNowLabels[key]||{};
      for(const event of (j.events||[])){
        const game=normalizeEvent(event);
        if(game.state==='live')live.push({...game,sportKey:key,sportLabel:labels.sport,leagueLabel:labels.league});
      }
    }catch{}
  }));

  await Promise.all([regionalPromise,apiPromise]);
  if(silent||host.querySelector('.live-game-card'))updateAllLiveScoreNumbers(live);
  else renderAllLiveGames(live);
}
function renderGames(){
  const host=document.getElementById('games');
  if(!host)return;

  const filter=document.getElementById('gameFilter')?.value||'all';
  const byDate=(a,b)=>{
    const ad=Date.parse(a.date||'')||0,bd=Date.parse(b.date||'')||0;
    if(a.state==='final'&&b.state==='final')return bd-ad;
    return ad-bd;
  };
  const live=allGames.filter(g=>g.state==='live').sort(byDate);
  const other=allGames.filter(g=>g.state!=='live');

  let items;
  if(filter==='live'){
    items=live;
  }else{
    const filtered=filter==='all'?other:other.filter(g=>g.state===filter);
    items=[...live,...filtered.sort(byDate)].slice(0,20);
  }

  host.innerHTML=items.length?items.map(g=>{
    if(g.isRacing){
      const place=[g.raceCircuit,g.raceCity].filter(Boolean).join(' · ');
      return '<article class="game race-game'+(g.state==='live'?' game-is-live':'')+'" data-game-key="'+esc(gameDomKey(g))+'">'+
        '<div class="time">'+esc(g.displayTime||new Date(g.date).toLocaleString([],{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}))+'</div>'+
        '<div class="race-game-main"><div class="race-game-top"><strong>'+esc(g.raceTitle||g.home)+'</strong><span class="race-session">'+esc(g.raceSession||g.away)+'</span></div>'+
        (place?'<small>'+esc(place)+'</small>':'')+
        '<div class="state '+(g.state==='live'?'live':'')+'">'+esc(g.status)+'</div>'+
        (g.raceBroadcast?'<div class="race-broadcast">Broadcast: '+esc(g.raceBroadcast)+'</div>':'')+
        (g.streams?.length?'<button class="watch-live-btn" type="button" data-live-event="'+esc(g.eventId)+'"><span class="live-dot" aria-hidden="true"></span>Watch Live</button>':'')+
        '</div></article>';
    }
    return '<article class="game'+(g.state==='live'?' game-is-live':'')+'" data-game-key="'+esc(gameDomKey(g))+'"><div class="time">'+esc(g.displayTime||new Date(g.date).toLocaleString([],{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}))+'</div><div class="teams"><div class="team"><span class="team-identity">'+teamLogoMarkup(g.awayLogo,g.away)+'<span>'+esc(g.away)+'</span></span><b data-score-side="away">'+esc(g.awayScore)+'</b></div><div class="team"><span class="team-identity">'+teamLogoMarkup(g.homeLogo,g.home)+'<span>'+esc(g.home)+'</span></span><b data-score-side="home">'+esc(g.homeScore)+'</b></div></div><div class="state '+(g.state==='live'?'live':'')+'">'+esc(g.status)+'</div>'+(g.streams?.length?'<button class="watch-live-btn" type="button" data-live-event="'+esc(g.eventId)+'"><span class="live-dot" aria-hidden="true"></span>Watch Live</button>':'')+(g.highlights?.length?'<button class="highlights-btn" type="button" data-highlight-event="'+esc(g.eventId)+'"><span class="highlights-btn-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span>Highlights <b>'+esc(g.highlights.length)+'</b></button>':'')+(g.odds?'<div class="oddsline"><span>'+esc(g.odds.provider)+'</span><span>Line <b>'+esc(g.odds.details)+'</b></span><span>Total <b>'+esc(g.odds.total)+'</b></span></div>':'')+'</article>';
  }).join(''):'<div class="empty">No verified games were returned for this sport right now.</div>';
}
async function loadGames({silent=false}={}){
  if(!document.getElementById('games'))return;
  const st=document.getElementById('gameStatus');
  const sport=document.getElementById('sportFilter')?.value||'soccer';
  const isWebLeague=['pba','mpbl','nbl','nblaus','vba'].includes(sport);
  if(!silent)st.textContent='Updating';

  if(isWebLeague){
    await loadRegionalAutoData();
    const webGames=regionalSnapshotGames(sport);

    // GitHub-hosted regional data is the stable primary layer.
    // Never clear or replace it just because the Cloudflare fallback is unavailable.
    if(!silent&&webGames.length){
      allGames=webGames;
      st.textContent='';
      renderRegionalContext(sport,'web');
      renderGames();
    }else if(!allGames.length&&webGames.length){
      allGames=webGames;
    }

    try{
      const j=await fetchScorePayload(sport,{fallbackOnly:true});
      const liveGames=(j.events||[]).map(normalizeEvent).filter(g=>g.state==='live');

      if(liveGames.length){
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

    if(webGames.length){
      st.textContent='';
      if(silent)updateScoreNumbers();else if(!document.querySelector('#games .game'))renderGames();
      return;
    }
  }

  const hasRegionalSnapshot=Boolean(getRegionalSnapshot(sport));
  let mode='api';
  try{
    const j=await fetchScorePayload(sport);
    allGames=(j.events||[]).map(normalizeEvent);

    if(hasRegionalSnapshot&&!allGames.length){
      allGames=regionalSnapshotGames(sport);
      mode='web';
    }

    if(sport==='basketball'&&!allGames.length){
      const now=new Date(),end=new Date(now);
      end.setDate(end.getDate()+14);
      const [backup,logoMap]=await Promise.all([
        fetch('https://img-api-proxy.magsipocarnie.workers.dev/games?start_date='+now.toISOString().slice(0,10)+'&end_date='+end.toISOString().slice(0,10)+'&per_page=100',{cache:'no-store'}),
        getNbaLogoMap()
      ]);
      if(backup.ok){
        const b=await backup.json();
        allGames=(b.data||[]).map(g=>{
          const home=g.home_team?.full_name||'Home',away=g.visitor_team?.full_name||'Away';
          return{eventId:'',date:g.date,home,away,homeLogo:logoMap[String(home).toLowerCase()]||'',awayLogo:logoMap[String(away).toLowerCase()]||'',homeScore:g.home_team_score||'—',awayScore:g.visitor_team_score||'—',status:g.status||'Scheduled',state:/live|q[1-4]|half|quarter|ot|in progress/i.test(String(g.status||''))?'live':String(g.status||'').toLowerCase().includes('final')?'final':'scheduled',odds:null,highlights:[],highlightsChecked:true,streams:[],streamsChecked:true}
        });
      }
    }

    st.textContent='';
    renderRegionalContext(sport,mode);
    if(silent)updateScoreNumbers();else renderGames();
    if(mode!=='web'&&!silent){
      void hydrateHighlights(sport);
      void hydrateLiveStreams(sport);
    }
  }catch{
    if(hasRegionalSnapshot){
      allGames=regionalSnapshotGames(sport);
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

  const videoRows=(Array.isArray(videos)?videos:[]).slice(0,2);
  const videosHtml=videoRows.length
    ? '<section class="news-videos" aria-label="Sports videos">'+videoRows.map(v=>
        '<article class="news-video-card">'+
          '<div class="news-video-frame"><iframe src="'+esc(v.embed||'')+'" title="'+esc(v.title||'Sports video')+'" loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div>'+
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
function renderOdds(){
  const host=document.getElementById('oddsFeed'),league=document.getElementById('oddsSport')?.value,items=availableOdds[league]||[];
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
  const host=document.getElementById('oddsFeed'),select=document.getElementById('oddsSport'),status=document.getElementById('oddsStatus');
  if(!host||!select)return;
  status.textContent='Updating';
  host.setAttribute('aria-busy','true');
  const previous=select.value;

  const [bet365Data,espnResults]=await Promise.all([
    loadBet365Odds(),
    Promise.all(Object.entries(oddsFeeds).map(async([key,url])=>{
      try{
        const r=await fetch(url,{cache:'no-store'});
        if(!r.ok)return null;
        const j=await r.json(),items=(j.events||[]).map(normalizeEvent).filter(x=>x.oddsList.length);
        return items.length?[key,items]:null;
      }catch{
        return null;
      }
    }))
  ]);

  availableOdds=Object.fromEntries(espnResults.filter(Boolean));
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

  const keys=Object.keys(availableOdds);
  select.innerHTML=keys.map(key=>'<option value="'+esc(key)+'">'+esc(oddsLeagueNames[key]||key.toUpperCase())+'</option>').join('');
  select.hidden=!keys.length;
  if(keys.length){
    select.value=keys.includes(previous)?previous:keys[0];
    renderOdds();
  }else{
    host.innerHTML='';
  }
  status.textContent='';
  host.setAttribute('aria-busy','false');
}

if(document.getElementById('games')){
  let scoreAutoRefreshTimer=0;
  let scoreRefreshInFlight=false;

  const hasLiveScores=()=>allGames.some(g=>g.state==='live')||!document.getElementById('allLiveSection')?.hidden;
  const nextScoreRefreshDelay=()=>30000;

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
      const selectedSport=document.getElementById('sportFilter')?.value||'';
      await loadGames({silent:true});
      await refreshExistingAllLiveScores(selectedSport);
    }finally{
      scoreRefreshInFlight=false;
      scheduleScoreAutoRefresh();
    }
  }

  async function refreshScoresManually(){
    clearTimeout(scoreAutoRefreshTimer);
    if(scoreRefreshInFlight)return;
    scoreRefreshInFlight=true;
    try{
      const selectedSport=document.getElementById('sportFilter')?.value||'';
      await loadGames({silent:true});
      await refreshExistingAllLiveScores(selectedSport);
    }finally{
      scoreRefreshInFlight=false;
      scheduleScoreAutoRefresh();
    }
  }

  Promise.allSettled([loadGames(),loadAllLiveGames()]).finally(()=>scheduleScoreAutoRefresh());
  document.getElementById('gameFilter').onchange=renderGames;
  document.getElementById('sportFilter').onchange=async()=>{
    clearTimeout(scoreAutoRefreshTimer);
    await loadGames();
    scheduleScoreAutoRefresh();
  };
  document.getElementById('refreshGames').onclick=refreshScoresManually;

  document.addEventListener('visibilitychange',()=>{
    clearTimeout(scoreAutoRefreshTimer);
    if(!document.hidden)refreshScoresAutomatically();
  });
}if(document.getElementById('newsFeed')){loadNews();setInterval(loadNews,300000)}if(document.getElementById('oddsFeed')){discoverOdds();setInterval(discoverOdds,300000);document.getElementById('oddsSport').onchange=renderOdds;document.getElementById('refreshOdds').onclick=discoverOdds}
