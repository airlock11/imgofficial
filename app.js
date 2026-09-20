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
const leagues={Basketball:[['NBA','United States / Canada'],['PBA','Philippines'],['MPBL','Philippines'],['NBL-Pilipinas','Philippines'],['NBL Australia','Australia / New Zealand'],['VBA','Vietnam'],['B.League','Japan'],['EuroLeague','Europe'],['WBSL','International']],Football:[['Premier League','England'],['La Liga','Spain'],['Serie A','Italy'],['Bundesliga','Germany'],['UEFA Champions League','Europe'],['Philippine Football League','Philippines']],Tennis:[['ATP Tour','International'],['WTA Tour','International'],['Australian Open','Australia'],['Wimbledon','United Kingdom'],['US Open','United States']],Baseball:[['MLB','USA / Canada'],['NPB','Japan'],['KBO League','South Korea']],Hockey:[['NHL','USA / Canada'],['KHL','Eurasia'],['IIHF World Championship','International']],Cricket:[['IPL','India'],['Big Bash League','Australia'],['ICC Cricket World Cup','International']],Volleyball:[['Volleyball Nations League','International'],['PVL','Philippines'],['V.League','Japan']],Motorsport:[['Formula 1','International'],['MotoGP','International'],['Formula E','International']],Boxing:[['WBC','International'],['WBA','International'],['IBF','International'],['WBO','International'],['Professional Boxing','Worldwide']],'Combat Sports':[['UFC','International'],['ONE Championship','Asia']],'American Football':[['NFL','United States'],['NCAA Football','United States']]};
function openSport(name){if(name==='Boxing'){location.href='boxing.html';return}const modal=document.getElementById('sportModal');if(!modal)return;modal.querySelector('h2').textContent=name;modal.querySelector('.modalbody').innerHTML=(leagues[name]||[]).map(x=>'<div class="league-row"><strong>'+esc(x[0])+'</strong><small>'+esc(x[1])+'</small></div>').join('');modal.showModal()}
document.addEventListener('click',e=>{const sport=e.target.closest('[data-sport]');if(sport)openSport(sport.dataset.sport);if(e.target.matches('.close'))e.target.closest('dialog').close();const highlightButton=e.target.closest('[data-highlight-event]');if(highlightButton)openHighlights(highlightButton.dataset.highlightEvent);const liveButton=e.target.closest('[data-live-event]');if(liveButton)openLiveStream(liveButton.dataset.liveEvent)});
const scoreFeeds={soccer:'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard',basketball:'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard',pba:'https://img-api-proxy.magsipocarnie.workers.dev/regional-scores?league=pba',mpbl:'https://img-api-proxy.magsipocarnie.workers.dev/regional-scores?league=mpbl',nbl:'https://img-api-proxy.magsipocarnie.workers.dev/regional-scores?league=nbl',nblaus:'https://img-api-proxy.magsipocarnie.workers.dev/regional-scores?league=nblaus',vba:'https://img-api-proxy.magsipocarnie.workers.dev/regional-scores?league=vba',baseball:'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard',hockey:'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard',football:'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard'};
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
function mapOdds(o){return{provider:o.provider?.displayName||o.provider?.name||'Odds provider',details:o.details||'—',total:o.overUnder??'—',home:o.moneyline?.home?.close?.odds||'—',away:o.moneyline?.away?.close?.odds||'—'}}function teamLogoUrl(team){return team?.team?.logo||team?.team?.logos?.[0]?.href||team?.logo||team?.logos?.[0]?.href||''}
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
function normalizeEvent(e){const c=e.competitions?.[0],teams=c?.competitors||[],home=teams.find(x=>x.homeAway==='home')||teams[0],away=teams.find(x=>x.homeAway==='away')||teams[1],state=e.status?.type?.state||'pre',oddsList=(c?.odds||[]).filter(o=>o?.provider?.displayName||o?.provider?.name).map(mapOdds);return{eventId:e.id||c?.id||'',date:e.date,home:home?.team?.displayName||'Home',away:away?.team?.displayName||'Away',homeLogo:teamLogoUrl(home),awayLogo:teamLogoUrl(away),homeScore:home?.score||'—',awayScore:away?.score||'—',status:e.status?.type?.shortDetail||e.status?.type?.description||'Scheduled',state:state==='in'?'live':state==='post'?'final':'scheduled',odds:oddsList[0]||null,oddsList,highlights:[],highlightsChecked:false,streams:[],streamsChecked:false}}
function renderGames(){const host=document.getElementById('games');if(!host)return;const filter=document.getElementById('gameFilter')?.value||'all',items=allGames.filter(g=>filter==='all'||g.state===filter).slice(0,20);host.innerHTML=items.length?items.map(g=>'<article class="game"><div class="time">'+esc(g.displayTime||new Date(g.date).toLocaleString([],{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}))+'</div><div class="teams"><div class="team"><span class="team-identity">'+teamLogoMarkup(g.awayLogo,g.away)+'<span>'+esc(g.away)+'</span></span><b>'+esc(g.awayScore)+'</b></div><div class="team"><span class="team-identity">'+teamLogoMarkup(g.homeLogo,g.home)+'<span>'+esc(g.home)+'</span></span><b>'+esc(g.homeScore)+'</b></div></div><div class="state '+(g.state==='live'?'live':'')+'">'+esc(g.status)+'</div>'+(g.streams?.length?'<button class="watch-live-btn" type="button" data-live-event="'+esc(g.eventId)+'"><span class="live-dot" aria-hidden="true"></span>Watch Live</button>':'')+(g.highlights?.length?'<button class="highlights-btn" type="button" data-highlight-event="'+esc(g.eventId)+'"><span class="highlights-btn-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span>Highlights <b>'+esc(g.highlights.length)+'</b></button>':'')+(g.odds?'<div class="oddsline"><span>'+esc(g.odds.provider)+'</span><span>Line <b>'+esc(g.odds.details)+'</b></span><span>Total <b>'+esc(g.odds.total)+'</b></span></div>':'')+'</article>').join(''):'<div class="empty">No verified games were returned for this sport right now.</div>'}
async function loadGames(){
  if(!document.getElementById('games'))return;
  const st=document.getElementById('gameStatus');
  const sport=document.getElementById('sportFilter')?.value||'soccer';
  const isWebLeague=['pba','mpbl','nbl'].includes(sport);
  st.textContent='Updating';

  if(isWebLeague){
    await loadRegionalAutoData();
    const webGames=regionalSnapshotGames(sport);
    if(webGames.length){
      allGames=webGames;
      st.textContent='';
      renderRegionalContext(sport,'web-auto');
      renderGames();
      return;
    }
  }

  const hasRegionalSnapshot=Boolean(getRegionalSnapshot(sport));
  let mode='api';
  try{
    const r=await fetch(scoreFeeds[sport],{cache:'no-store'});
    if(!r.ok)throw 0;
    const j=await r.json();
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
    renderGames();
    if(mode!=='web'){
      void hydrateHighlights(sport);
      void hydrateLiveStreams(sport);
    }
  }catch{
    if(hasRegionalSnapshot){
      allGames=regionalSnapshotGames(sport);
      st.textContent='';
      renderRegionalContext(sport,'web');
      renderGames();
    }else{
      renderRegionalContext(sport,'');
      st.textContent='Feed unavailable';
      document.getElementById('games').innerHTML='<div class="empty">This public score feed is temporarily unavailable.</div>';
    }
  }
}
function clean(html){const d=document.createElement('div');d.innerHTML=html||'';return d.textContent.trim().replace(/Continue reading.*$/i,'').slice(0,260)}function parseXML(x){const d=new DOMParser().parseFromString(x,'application/xml');return [...d.querySelectorAll('item')].map(i=>({title:i.querySelector('title')?.textContent||'',link:i.querySelector('link')?.textContent||'',description:clean(i.querySelector('description')?.textContent),source:d.querySelector('channel>title')?.textContent||'Sports News',sport:i.querySelector('category')?.textContent||'Sports',image:i.getElementsByTagName('media:content')[0]?.getAttribute('url')||''})).filter(x=>x.title&&x.link)}
function renderNews(items){const host=document.getElementById('newsFeed');if(!host||!items.length)return;const first=items[0];host.innerHTML='<article class="lead-story">'+(first.image?'<img src="'+esc(first.image)+'" alt="" referrerpolicy="no-referrer">':'<div></div>')+'<div><div class="tag">'+esc(first.sport)+'</div><a href="'+esc(first.link)+'" target="_blank" rel="noopener"><h2>'+esc(first.title)+'</h2></a><p>'+esc(first.description)+'</p><small>'+esc(first.source)+'</small></div></article><div class="news-list">'+items.slice(1,9).map(n=>'<article class="news-row"><img src="'+esc(n.image||'about-sports.jpg')+'" alt="" loading="lazy" referrerpolicy="no-referrer"><div><div class="tag">'+esc(n.sport)+'</div><a href="'+esc(n.link)+'" target="_blank" rel="noopener"><h3>'+esc(n.title)+'</h3></a><small>'+esc(n.source)+'</small></div><span class="arrow">↗</span></article>').join('')+'</div>';const s=document.getElementById('newsStatus');if(s){s.textContent='';s.closest('.news-livebar')?.classList.add('is-empty')}}
async function loadNews(){if(!document.getElementById('newsFeed'))return;const ns=document.getElementById('newsStatus');ns?.closest('.news-livebar')?.classList.remove('is-empty');try{const r=await fetch('https://img-api-proxy.magsipocarnie.workers.dev/news',{cache:'no-store'});if(!r.ok)throw 0;const t=await r.text();const items=t.trim().startsWith('{')?(JSON.parse(t).items||[]):parseXML(t);renderNews(items)}catch{document.getElementById('newsFeed').innerHTML='<div class="empty">The live news feed is temporarily unavailable.</div>'}}
function renderOdds(){const host=document.getElementById('oddsFeed'),league=document.getElementById('oddsSport')?.value,items=availableOdds[league]||[];if(!host)return;host.innerHTML=items.map(g=>'<article class="odds-event"><div class="tag">'+esc(new Date(g.date).toLocaleString([],{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}))+'</div><div class="odds-matchup"><div class="odds-team">'+teamLogoMarkup(g.awayLogo,g.away,'odds-team-logo')+'<span>'+esc(g.away)+'</span></div><span class="versus">vs</span><div class="odds-team">'+teamLogoMarkup(g.homeLogo,g.home,'odds-team-logo')+'<span>'+esc(g.home)+'</span></div></div>'+g.oddsList.map(o=>'<div class="bookmaker"><strong>'+esc(o.provider)+'</strong><span><i class="market-label">Spread / line</i>'+esc(o.details)+'</span><span><i class="market-label">Away to win odds</i>'+esc(o.away)+'</span><span><i class="market-label">Home to win odds</i>'+esc(o.home)+'</span><span><i class="market-label">Over / under</i>'+esc(o.total)+'</span></div>').join('')+'</article>').join('')}
async function discoverOdds(){const host=document.getElementById('oddsFeed'),select=document.getElementById('oddsSport'),status=document.getElementById('oddsStatus');if(!host||!select)return;status.textContent='Updating';host.setAttribute('aria-busy','true');const previous=select.value;const results=await Promise.all(Object.entries(oddsFeeds).map(async([key,url])=>{try{const r=await fetch(url,{cache:'no-store'});if(!r.ok)return null;const j=await r.json(),items=(j.events||[]).map(normalizeEvent).filter(x=>x.oddsList.length);return items.length?[key,items]:null}catch{return null}}));availableOdds=Object.fromEntries(results.filter(Boolean));const keys=Object.keys(availableOdds);select.innerHTML=keys.map(key=>'<option value="'+esc(key)+'">'+esc(oddsLeagueNames[key])+'</option>').join('');select.hidden=!keys.length;if(keys.length){select.value=keys.includes(previous)?previous:keys[0];renderOdds()}else host.innerHTML='';status.textContent='';host.setAttribute('aria-busy','false')}
if(document.getElementById('games')){loadGames();setInterval(loadGames,60000);document.getElementById('gameFilter').onchange=renderGames;document.getElementById('sportFilter').onchange=loadGames;document.getElementById('refreshGames').onclick=loadGames}if(document.getElementById('newsFeed')){loadNews();setInterval(loadNews,300000)}if(document.getElementById('oddsFeed')){discoverOdds();setInterval(discoverOdds,300000);document.getElementById('oddsSport').onchange=renderOdds;document.getElementById('refreshOdds').onclick=discoverOdds}
