
(function(){
const pbaTeams=[
 ['Converge FiberXers','Group A','5-4'],['Macau Giant Pandas','Group A','2-6'],['NLEX Road Warriors','Group A','7-2'],['San Miguel Beermen','Group A','7-2'],['Terrafirma Dyip','Group A','3-5'],['Titan Ultra Giant Risers','Group A','2-7'],['TNT Tropang 5G','Group A','4-4'],
 ['Barangay Ginebra San Miguel','Group B','2-4'],['Blackwater Bossing','Group B','3-3'],['Magnolia Chicken Timplados Hotshots','Group B','4-3'],['Meralco Bolts','Group B','3-5'],['Phoenix Super LPG Fuel Masters','Group B','4-3'],['Rain or Shine Elasto Painters','Group B','4-2']
];
const nbaTeams=['Atlanta Hawks','Boston Celtics','Brooklyn Nets','Charlotte Hornets','Chicago Bulls','Cleveland Cavaliers','Dallas Mavericks','Denver Nuggets','Detroit Pistons','Golden State Warriors','Houston Rockets','Indiana Pacers','LA Clippers','Los Angeles Lakers','Memphis Grizzlies','Miami Heat','Milwaukee Bucks','Minnesota Timberwolves','New Orleans Pelicans','New York Knicks','Oklahoma City Thunder','Orlando Magic','Philadelphia 76ers','Phoenix Suns','Portland Trail Blazers','Sacramento Kings','San Antonio Spurs','Toronto Raptors','Utah Jazz','Washington Wizards'];
const gLeagueTeams=['Austin Spurs','Capital City Go-Go','Cleveland Charge','Coachella Valley Lakers','College Park Skyhawks','Delaware Blue Coats','Grand Rapids Gold','Greensboro Swarm','Iowa Wolves','Laketown Squadron','Long Island Nets','Maine Celtics','Memphis Hustle','Motor City Cruise','Noblesville Boom','Oklahoma City Blue','Osceola Magic','Raptors 905','Rio Grande Valley Vipers','Rip City Remix','Salt Lake City Stars','San Diego Clippers','Santa Cruz Warriors','Sioux Falls Skyforce','South Bay Lakers','Stockton Kings','Texas Legends','Westchester Knicks','Windy City Bulls','Wisconsin Herd','Valley Suns'];
const bPremier=['Levanga Hokkaido','Sendai 89ERS','Akita Northern Happinets','Ibaraki Robots','Utsunomiya Brex','Gunma Crane Thunders','Altiri Chiba','Chiba Jets','Alvark Tokyo','Sunrockers Shibuya','Kawasaki Brave Thunders','Yokohama B Corsairs','Toyama Grouses','San-En NeoPhoenix','Nagoya Diamond Dolphins','Shimane Susanoo Magic','Hiroshima Dragonflies','Saga Ballooners','Ryukyu Golden Kings','SeaHorses Mikawa','Shiga Lakes','Kobe Storks','Nagasaki Velca','FE Nagoya','Koshigaya Alphas','Fukushima Firebonds'];
const officialPBA='https://www.pba.ph/';
const officialNBA='https://www.nba.com/teams';
const officialGLEAGUE='https://gleague.nba.com/about';
const officialBLEAGUE='https://www.bleague.jp/new-bleague/club/';
const standingsSource='https://www.gmanetwork.com/news/sports/basketball/999140/2026-pba-governors-cup-standings-as-of-august-14-before-conference-break/';
function esc(x){return String(x).replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\\':'&#92;'}[c]));}
function teamCards(arr, note){return arr.map(t=>`<div class="ld-team"><b>${esc(t)}</b>${note?`<small>${esc(note)}</small>`:''}</div>`).join('');}
function source(url,label){return `<a href="${url}" target="_blank" rel="noopener">${label}</a>`;}
function canonicalLeagueName(name){
 const aliases={
  'PBA':'PBA',
  'NBA':'NBA',
  'G League':'NBA G League',
  'NBA G League':'NBA G League',
  'B.League':'B.LEAGUE',
  'B.LEAGUE':'B.LEAGUE',
  'VBA':'Vietnam Basketball Association (VBA)',
  'Vietnam Basketball Association':'Vietnam Basketball Association (VBA)',
  'Vietnam Basketball Association (VBA)':'Vietnam Basketball Association (VBA)',
  'MPBL':'Maharlika Pilipinas Basketball League (MPBL)',
  'Maharlika Pilipinas Basketball League':'Maharlika Pilipinas Basketball League (MPBL)',
  'NBL Philippines':'NBL–Pilipinas',
  'NBL–Pilipinas':'NBL–Pilipinas'
 };
 return aliases[name] || name;
}

function IMGUniversalLeagueProfile(name,sport){
 const fromHomeSearch=(window.homeSearchOpenedLeague || homeSearchOpenedLeague);
 const searchClose=document.getElementById("ld-search-close");
 if(searchClose) searchClose.style.display=fromHomeSearch?"block":"none";
 const backLeagues=document.getElementById("ld-back-leagues");
 if(backLeagues) backLeagues.style.display=fromHomeSearch?"none":"inline-block";
 const custom={
  "PBA":1,"NBA":1,"NBA G League":1,"B.LEAGUE":1,
  "NBL–Pilipinas":1,"Vietnam Basketball Association (VBA)":1,
  "Maharlika Pilipinas Basketball League (MPBL)":1,
  "Basketball Super League (BSL)":1,"UAAP Basketball":1,
  "Philippine Football League":1
 };
 if(custom[name]) return false;
 const data=window.IMGLeagueData||{};
 const item=((data[sport]||[]).find(x=>x[0]===name)||[name,""]);
 const location=item[1]||"International";
 const content=document.getElementById("ld-content");
 const title=document.getElementById("ld-title");
 const sub=document.getElementById("ld-sub");
 const browser=document.getElementById("img-league-browser");
 const root=document.getElementById("img-league-detail");
 if(!content||!title||!sub||!browser||!root) return false;
 root.classList.toggle("search-origin", !!fromHomeSearch);
 content.replaceChildren();
 title.textContent=name;
 sub.textContent=(sport||"Sports")+" · "+location+" · League Profile";
 browser.style.display="none";
 root.style.display="block";
 const esc=s=>String(s).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
 content.innerHTML=`
  <div class="league-detail">
   <div class="ld-card">
    <div class="ld-card-head"><h2>${esc(name)} PROFILE</h2><span class="ld-badge">Reference profile</span></div>
    <p><strong>${esc(name)}</strong><br>${esc(location)} · ${esc(sport||"Sports")}</p>
    <h3>League Overview</h3>
    <p>This IMG profile organizes the competition's key information in one place, including teams or participants, standings, schedule, results, statistics and verified news.</p>
    <div class="ld-stat-grid">
     <div><small>Region</small><b>${esc(location)}</b></div>
     <div><small>Sport</small><b>${esc(sport||"Sports")}</b></div>
     <div><small>Profile year</small><b>2026</b></div>
    </div>
   </div>
   <div class="ld-grid">
    <div class="ld-card"><div class="ld-card-head"><h3>TEAMS / PARTICIPANTS</h3><span class="ld-badge">Ready</span></div><p class="ld-placeholder">Team or participant data will be displayed here when verified league data is available.</p></div>
    <div class="ld-card"><div class="ld-card-head"><h3>STANDINGS</h3><span class="ld-badge">Ready</span></div><p class="ld-placeholder">Standings will be displayed here when verified competition data is available.</p></div>
   </div>
   <div class="ld-two-col">
    <div class="ld-card"><div class="ld-card-head"><h3>SCHEDULE</h3></div><div class="ld-placeholder">No verified schedule feed connected.</div></div>
    <div class="ld-card"><div class="ld-card-head"><h3>RESULTS</h3></div><div class="ld-placeholder">No verified results feed connected.</div></div>
   </div>
   <div class="ld-two-col">
    <div class="ld-card"><div class="ld-card-head"><h3>STATISTICS</h3></div><div class="ld-placeholder">Statistics feed not connected.</div></div>
    <div class="ld-card"><div class="ld-card-head"><h3>NEWS</h3></div><div class="ld-placeholder">League news module ready for verified articles.</div></div>
   </div>
   <div class="ld-card">
    <div class="ld-card-head"><h3>SOURCES</h3></div>
    <p class="ld-placeholder">Official league or federation resources should be used to verify season, schedule, results and statistics before publication.</p>
   </div>
  </div>`;
 window.IMGCurrentLeague={name:name,sport:sport||"Sports"};
 window.scrollTo({top:0,behavior:"smooth"});
 return true;
}
function openDetail(name,sport){
 const searchClose=document.getElementById('ld-search-close');
 const fromHomeSearch=(homeSearchOpenedLeague || window.homeSearchOpenedLeague);
 if(searchClose) searchClose.style.display=fromHomeSearch?'block':'none';
 const backLeagues=document.getElementById('ld-back-leagues');
 if(backLeagues) backLeagues.style.display=fromHomeSearch?'none':'inline-block';
 name=canonicalLeagueName(name);
 if(IMGUniversalLeagueProfile(name,sport))return;
 const browser=document.getElementById('img-league-browser');
 const root=document.getElementById('img-league-detail');
 root.classList.toggle('search-origin', !!fromHomeSearch);
 const title=document.getElementById('ld-title'),sub=document.getElementById('ld-sub'),content=document.getElementById('ld-content');
 // Always clear the previous league before rendering the next one. This prevents stale PBA/NBA content.
 content.replaceChildren();
 title.textContent=name;
 sub.textContent=(sport||'Sports')+' · League information';
 browser.style.display='none';
 root.style.display='block';
 window.IMGCurrentLeague={name:name,sport:sport||'Sports'};
 if(name==='PBA'){
  const pbaTeams=[
   ['Converge FiberXers','Group A','5-4'],['Macau Giant Pandas','Group A','2-6'],['NLEX Road Warriors','Group A','7-2'],['San Miguel Beermen','Group A','7-2'],['Terrafirma Dyip','Group A','3-5'],['Titan Ultra Giant Risers','Group A','2-7'],['TNT Tropang 5G','Group A','4-4'],
   ['Barangay Ginebra San Miguel','Group B','2-4'],['Blackwater Bossing','Group B','3-3'],['Magnolia Chicken Timplados Hotshots','Group B','4-3'],['Meralco Bolts','Group B','3-5'],['Phoenix Super LPG Fuel Masters','Group B','4-3'],['Rain or Shine Elasto Painters','Group B','4-2']
  ];
  const sorted=[...pbaTeams].sort((a,b)=>{
    const aw=parseInt(a[2]),bw=parseInt(b[2]);
    if(bw!==aw)return bw-aw;
    return parseInt(a[2].split('-')[1])-parseInt(b[2].split('-')[1]);
  });
  const groupA=pbaTeams.filter(t=>t[1]==='Group A').length;
  const groupB=pbaTeams.filter(t=>t[1]==='Group B').length;
  content.innerHTML=`
   <div class="league-detail">
    <div class="ld-card">
     <div class="ld-card-head"><h2>PBA PROFILE</h2><span class="ld-badge">Reference data</span></div>
     <p><strong>Philippine Basketball Association</strong><br>Philippines · 2026 Governors’ Cup</p>
     <h3>League Overview</h3>
     <p>The PBA is the Philippines' premier professional basketball league. This profile organizes competition information, team reference data, standings and space for future verified schedules, results, statistics and news.</p>
     <div class="ld-stat-grid">
      <div><b>${pbaTeams.length}</b><small>Total teams</small></div>
      <div><b>${groupA}</b><small>Group A</small></div>
      <div><b>${groupB}</b><small>Group B</small></div>
     </div>
    </div>
    <div class="ld-card">
     <div class="ld-card-head"><h3>2026 GOVERNORS' CUP</h3><span class="ld-badge">Competition</span></div>
     <p>Two groups are shown in the stored reference data before the crossover playoff stage.</p>
    </div>
    <div class="ld-card">
     <div class="ld-card-head"><h3>STANDINGS</h3><span class="ld-badge">Reference data</span></div>
     <div class="table-wrap"><table><thead><tr><th>Team</th><th>Group</th><th>Record</th></tr></thead><tbody>
      ${sorted.map(t=>`<tr><td>${t[0]}</td><td>${t[1]}</td><td><strong>${t[2]}</strong></td></tr>`).join('')}
     </tbody></table></div>
     <p class="ld-placeholder">Reference data only; this table is not a live standings feed.</p>
    </div>
    <div class="ld-card">
     <div class="ld-card-head"><h3>TEAM DIRECTORY</h3><span class="ld-badge">${pbaTeams.length} teams</span></div>
     <div class="team-grid">${pbaTeams.map(t=>`<div class="team-item"><strong>${t[0]}</strong><small>${t[1]} · ${t[2]}</small></div>`).join('')}</div>
    </div>
    <div class="ld-two-col">
     <div class="ld-card"><div class="ld-card-head"><h3>SCHEDULE</h3></div><div class="ld-placeholder">No verified schedule feed connected.</div></div>
     <div class="ld-card"><div class="ld-card-head"><h3>RESULTS</h3></div><div class="ld-placeholder">No verified results feed connected.</div></div>
    </div>
    <div class="ld-two-col">
     <div class="ld-card"><div class="ld-card-head"><h3>STATISTICS</h3></div><div class="ld-placeholder">Statistics feed not connected.</div></div>
     <div class="ld-card"><div class="ld-card-head"><h3>NEWS</h3></div><div class="ld-placeholder">League news module ready for verified articles.</div></div>
    </div>
    <div class="ld-card">
     <div class="ld-card-head"><h3>SOURCES</h3></div>
     <ul class="source-list">
      <li>Official PBA resources</li>
      <li>Inquirer Sports</li>
      <li>GMA Sports</li>
     </ul>
    </div>
   </div>`;
}else if(name==='NBA'){
  title.textContent='NBA'; sub.textContent='National Basketball Association · USA / Canada · 2026–27 season';
  content.innerHTML=`<div class="ld-grid"><div class="ld-card"><h3>Season Status</h3><p class="ld-sub">The 2026–27 regular-season schedule has been released. IMG therefore shows the current upcoming season rather than treating the league as inactive.</p><div class="ld-note"><b>Current season:</b> 2026–27 · 30 teams.</div></div><div class="ld-card"><h3>What IMG will show</h3><p class="ld-sub">Teams, schedule, results, standings and statistics are separated by season. When a season is completed, IMG can retain it as the latest completed season instead of leaving the league page empty.</p></div></div><div class="ld-card" style="margin-top:16px"><h3>30 Teams</h3><div class="ld-team-grid">${teamCards(nbaTeams,'NBA team')}</div></div><div class="ld-card" style="margin-top:16px"><h3>Sources</h3><div class="ld-source">Official NBA team directory: ${source(officialNBA,'NBA.com')}<br>2026–27 schedule: ${source('https://www.nba.com/news/2026-27-nba-regular-season-schedule','NBA.com')}</div></div>`;
 }else if(name==='NBA G League'){
  title.textContent='NBA G League'; sub.textContent='NBA G League · USA / Canada · 2026–27 season';
  content.innerHTML=`<div class="ld-grid"><div class="ld-card"><h3>Season Status</h3><p class="ld-sub">The 2026–27 G League season is scheduled to feature 31 teams. IMG treats this as an active/upcoming season.</p></div><div class="ld-card"><h3>Historical fallback</h3><p class="ld-sub">If the selected season is not active, the league hub should automatically display the most recent completed season available in IMG rather than a blank page.</p></div></div><div class="ld-card" style="margin-top:16px"><h3>2026–27 Team Directory</h3><div class="ld-team-grid">${teamCards(gLeagueTeams,'2026–27')}</div></div><div class="ld-card" style="margin-top:16px"><h3>Source</h3><div class="ld-source">Official G League information: ${source(officialGLEAGUE,'NBA G League')}</div></div>`;
 }else if(name==='B.LEAGUE'){
  title.textContent='B.LEAGUE'; sub.textContent='Japan · 2026–27 season · B.LEAGUE PREMIER / ONE / NEXT';
  content.innerHTML=`<div class="ld-grid"><div class="ld-card"><h3>Season Status</h3><p class="ld-sub">Japan’s professional basketball system moves to the new B.LEAGUE PREMIER, B.LEAGUE ONE and B.LEAGUE NEXT categories for 2026–27.</p><div class="ld-note"><b>Verified structure:</b> B.LEAGUE’s official materials list 55 clubs across the three categories for 2026–27.</div></div><div class="ld-card"><h3>IMG display rule</h3><p class="ld-sub">The league page keeps the latest verified season visible during an off-season instead of showing an empty league page.</p></div></div><div class="ld-card" style="margin-top:16px"><h3>B.LEAGUE PREMIER clubs</h3><div class="ld-team-grid">${teamCards(bPremier,'2026–27 B.LEAGUE PREMIER')}</div></div><div class="ld-card" style="margin-top:16px"><h3>Source</h3><div class="ld-source">Official B.LEAGUE club information: ${source(officialBLEAGUE,'B.LEAGUE Official Website')}</div></div>`;
 }else if(name==='Maharlika Pilipinas Basketball League (MPBL)'){
  title.textContent='Maharlika Pilipinas Basketball League (MPBL)'; sub.textContent='Basketball · Philippines · 2026 season';
  const mpbl=['Abra Weavers','San Juan Knights','Batang Kankaloo','Meycauayan Marilao Gems','Ilagan Isabela Cowboys','Pasay Voyagers','Bataan Risers','Pasig City','Quezon City Capitals','Valenzuela Classics','Marikina Shoemasters','Bulacan Kuyas','Manila','Parañaque Patriots'];
  content.innerHTML=`<div class="ld-grid"><div class="ld-card"><h3>2026 Season</h3><p class="ld-sub">IMG has verified current 2026 MPBL standings data from a live competition source. The page is marked as a current-season profile.</p><div class="ld-note"><b>Current leaders in the retrieved table:</b> Abra Weavers 23–2, San Juan Knights 21–3, Batang Kankaloo 20–4.</div></div><div class="ld-card"><h3>Source policy</h3><p class="ld-sub">For MPBL, IMG can cross-check official league/team announcements with current competition data.</p></div></div><div class="ld-card" style="margin-top:16px"><h3>Teams appearing in the current verified table</h3><div class="ld-team-grid">${teamCards(mpbl,'2026 MPBL')}</div></div><div class="ld-card" style="margin-top:16px"><h3>Sources</h3><div class="ld-source">Current standings: ${source('https://www.sofascore.com/basketball/tournament/philippines/mpbl/34113','Sofascore MPBL')}<br>Team directory: ${source('https://philsports.ph/mpbl/teams/','PhilSports MPBL')}</div></div>`;
 }else if(name==='NBL–Pilipinas'){
  title.textContent='NBL–Pilipinas'; sub.textContent='National Basketball League · Philippines · Governors’ Cup 2026';
  const nblTeams=[
   ['Taguig Generals',1,9,0,'+9'],
   ['Tikas Kapampangan',2,7,2,'-2'],
   ['CamSur Express',3,6,3,'+5'],
   ['Pangasinan Asinderos',4,6,3,'-1'],
   ['Quezon Starhorse',5,5,4,'-1'],
   ['Nueva Ecija Granary Buffaloes',6,4,5,'-1'],
   ['Batangas Barako Venom Art',7,3,6,'+2'],
   ['Manila MLB',8,2,7,'-2'],
   ['Quezon City Titans',9,2,7,'-4'],
   ['Zamboanga Valientes',10,1,8,'+1']
  ];
  const rows=nblTeams.map(t=>`<tr><td>${t[1]}</td><td><b>${esc(t[0])}</b></td><td>${t[2]}</td><td>${t[3]}</td><td>${t[4]}</td></tr>`).join('');
  const cards=nblTeams.map(t=>`<div class="ld-team"><b>${esc(t[0])}</b><small>#${t[1]} · ${t[2]}-${t[3]} · Streak ${esc(t[4])}</small></div>`).join('');
  content.innerHTML=`
  <div class="ld-grid">
   <div class="ld-card"><h3>League Profile</h3><p class="ld-sub">NBL–Pilipinas is a Philippine men’s basketball competition. This IMG profile is based on the NBL Pilipinas Governors’ Cup 2026 standings and playoff graphic supplied for IMG.</p><div class="ld-note"><b>Source note:</b> The supplied graphics do not show a publication date, so IMG labels the data as “Governors’ Cup 2026” rather than claiming a specific retrieval date.</div></div>
  </div>
  <div class="ld-card" style="margin-top:16px"><h3>Governors’ Cup 2026 — Team Standings</h3><div style="overflow:auto"><table class="ld-table"><thead><tr><th>Rank</th><th>Team</th><th>Win</th><th>Loss</th><th>Streak</th></tr></thead><tbody>${rows}</tbody></table></div></div>
  <div class="ld-card" style="margin-top:16px"><h3>Team Directory</h3><div class="ld-team-grid">${cards}</div></div>
  <div class="ld-card" style="margin-top:16px"><h3>2026 Playoffs</h3><p class="ld-sub">The supplied playoff graphic shows a play-in feeding the semifinals, followed by a best-of-five final.</p><div class="ld-grid">
   <div><h4>Left Bracket</h4><p class="ld-sub"><b>#1 Taguig Generals</b> — twice-to-beat<br>vs. winner of <b>#8 Manila MLB</b> vs <b>#9 Quezon City Titans</b></p><p class="ld-sub"><b>#4 Pangasinan Asinderos</b> — twice-to-beat<br>vs. <b>#5 Quezon Starhorse</b></p></div>
   <div><h4>Right Bracket</h4><p class="ld-sub"><b>#2 Tikas Kapampangan</b> — twice-to-beat<br>vs. winner of <b>#7 Batangas Barako Venom Art</b> vs <b>#10 Zamboanga Valientes</b></p><p class="ld-sub"><b>#3 CamSur Express</b> — twice-to-beat<br>vs. <b>#6 Nueva Ecija Granary Buffaloes</b></p></div>
  </div><div class="ld-note"><b>Semifinals:</b> Best of 3 · <b>Finals:</b> Best of 5.</div></div>
  <div class="ld-card" style="margin-top:16px"><h3>Source</h3><div class="ld-source">Primary source supplied to IMG: NBL Pilipinas Governors’ Cup 2026 Team Standings and Playoffs graphics.</div></div>`;
 }else if(name==='Vietnam Basketball Association (VBA)'){
  title.textContent='Vietnam Basketball Association (VBA)'; sub.textContent='Basketball · Vietnam · 2026 season';
  const vbaTeams=['Hanoi Buffaloes','Danang Dragons','Nha Trang Dolphins','Saigon Heat','Ho Chi Minh City Wings','Cantho Catfish'];
  content.innerHTML=`<div class="ld-grid"><div class="ld-card"><h3>League Profile</h3><p class="ld-sub">The Vietnam Basketball Association (VBA) is Vietnam’s professional basketball league. VBA was established in July 2016 and is described by the league as the first professional basketball league in Vietnam.</p><div class="ld-note"><b>2026 status:</b> The official VBA website identifies the 2026 season as ongoing.</div></div><div class="ld-card"><h3>2026 Teams</h3><div class="ld-team-grid">${teamCards(vbaTeams,'VBA 2026')}</div></div></div><div class="ld-card" style="margin-top:16px"><h3>Competition information</h3><p class="ld-sub">IMG will use the official VBA fixtures, results and standings pages for current-season data and retain the latest completed season when the league is inactive.</p></div><div class="ld-card" style="margin-top:16px"><h3>Sources</h3><div class="ld-source">Official VBA: ${source('https://vba.vn/','Vietnam Basketball Association')}<br>Official fixtures/results: ${source('https://vba.vn/fixtures','VBA Fixtures')}<br>Official standings: ${source('https://vba.vn/standings','VBA Standings')}<br>League history: ${source('https://vba.vn/history','VBA History')}</div></div>`;
 }else if(name==='UAAP Basketball'){
  title.textContent='UAAP Basketball'; sub.textContent='University Athletic Association of the Philippines · Basketball';
  content.innerHTML=`<div class="ld-grid"><div class="ld-card"><h3>Competition</h3><p class="ld-sub">UAAP basketball is the collegiate basketball competition under the University Athletic Association of the Philippines.</p><div class="ld-note"><b>Official source:</b> UAAP publishes basketball standings and participants on its sports pages.</div></div><div class="ld-card"><h3>Data Sections</h3><p class="ld-sub">Participants · Standings · Schedule · Results</p></div></div><div class="ld-card" style="margin-top:16px"><h3>Source</h3><div class="ld-source">${source('https://uaap.org/sports/basketball','UAAP Official Basketball')}</div></div>`;
 }else if(name==='Philippine Football League'){
  title.textContent='Philippine Football League'; sub.textContent='Football · Philippines · 2025–26 season';
  content.innerHTML=`<div class="ld-grid"><div class="ld-card"><h3>Current competition</h3><p class="ld-sub">The Philippine Football Federation publishes Philippine Football League competition information and standings.</p><div class="ld-note"><b>Retrieved standings example:</b> the PFF source currently lists Maharlika Taguig FC, KAYA FC–ILOILO, Aguilas-UMak FC, Stallion Laguna FC and other clubs.</div></div><div class="ld-card"><h3>Source</h3><p class="ld-sub">IMG will use the federation as the primary source when available.</p></div></div><div class="ld-card" style="margin-top:16px"><h3>Official source</h3><div class="ld-source">${source('https://pff.org.ph/','Philippine Football Federation')}</div></div>`;
 }else if(name==='Basketball Super League (BSL)'){
  title.textContent='Basketball Super League (BSL)'; sub.textContent='Basketball · Canada / North America';
  content.innerHTML=`<div class="ld-grid"><div class="ld-card"><h3>League Profile</h3><p class="ld-sub">IMG lists the current Canadian competition under the corrected Basketball Super League name.</p><div class="ld-note"><b>Data rule:</b> season-specific teams and records are shown only after verification from the league or a reliable competition data provider.</div></div><div class="ld-card"><h3>Data Sections</h3><p class="ld-sub">Teams · Standings · Schedule · Results · Statistics · Players</p></div></div>`;
  }else{
  title.textContent=name;
  const leagueData=window.IMGLeagueData||{};
  const location=((leagueData[sport]||[]).find(x=>x[0]===name)||['',''])[1];
  sub.textContent=(sport||'Sports')+' · '+location+' · League Profile';
  const facts={
   // Basketball
   'WNBA':['Women’s professional basketball league in the United States.','Professional league; U.S. women’s basketball.','WNBA official website'],
   'NCAA':['U.S. intercollegiate athletics association; its basketball championships are organized through member schools and conferences.','College sport; men’s and women’s basketball.','NCAA official website'],
   'World Basketball Super League (WBSL)':['International basketball competition listed by IMG; season-specific details are shown only when verified from the organizer or official channels.','Club competition; international.','Official competition channels'],
   'EuroLeague':['Top-level European professional men’s club basketball competition organized by Euroleague Basketball.','Club competition; Europe.','EuroLeague official website'],
   'EuroCup':['European professional men’s club basketball competition organized by Euroleague Basketball.','Club competition; Europe.','EuroCup / Euroleague Basketball'],
   'Liga Endesa (ACB)':['Spain’s top professional men’s basketball league, operated by the Asociación de Clubes de Baloncesto.','Professional league; Spain.','ACB official website'],
   'Super League Basketball':['Professional basketball competition in Great Britain.','Professional league; United Kingdom.','Super League Basketball official channels'],
   'Betclic Élite (LNB Pro A)':['France’s top professional men’s basketball division.','Professional league; France.','LNB official website'],
   'easyCredit BBL':['Germany’s top professional men’s basketball division.','Professional league; Germany.','easyCredit BBL official website'],
   'Lega Basket Serie A':['Italy’s top professional men’s basketball division.','Professional league; Italy.','Lega Basket official website'],
   'Türkiye Sigorta Basketbol Süper Ligi':['Türkiye’s top professional men’s basketball division.','Professional league; Türkiye.','Turkish Basketball Federation'],
   'ABA League':['Regional professional men’s basketball competition involving clubs from the Adriatic/Balkan region.','Regional club competition; Balkans.','ABA League official website'],
   'VTB United League':['International professional basketball competition centered in Eastern Europe.','Regional club competition.','VTB United League official website'],
   'Greek Basket League':['Greece’s top professional men’s basketball division.','Professional league; Greece.','Greek Basketball Federation / league channels'],
   'LNB Pro A':['France’s top professional men’s basketball division.','Professional league; France.','LNB official website'],
   'Chinese Basketball Association (CBA)':['China’s top professional men’s basketball league.','Professional league; China.','CBA / Chinese Basketball Association'],
   'PBA D-League':['Philippine developmental basketball competition connected to the PBA system.','Developmental league; Philippines.','PBA official website'],
   'UAAP Basketball':['University basketball competition within the University Athletic Association of the Philippines.','Collegiate sport; Philippines.','UAAP official website'],
   'NCAA Philippines':['Collegiate basketball competition under the National Collegiate Athletic Association of the Philippines.','Collegiate sport; Philippines.','NCAA Philippines official channels'],
   'Pilipinas Super League':['Philippine basketball competition; season-specific teams and records are shown only from verified league sources.','Club basketball; Philippines.','Official league channels'],
   'B.LEAGUE':['Japan’s professional men’s basketball league system operated by the Japan Professional Basketball League.','Professional league system; Japan.','B.LEAGUE official website'],
   'KBL':['South Korea’s top professional men’s basketball league.','Professional league; South Korea.','KBL official website'],
   'National Basketball League (NBL)':['Australia’s premier professional men’s basketball league.','Professional league; Australia / New Zealand.','NBL Australia official website'],
   'Basketball Super League (BSL)':['Professional basketball competition in Canada; season-specific details are displayed only after source verification.','Professional club competition; Canada.','League / Basketball Canada sources'],
   'Liga Nacional de Baloncesto Profesional (LNBP)':['Mexico’s top professional men’s basketball league.','Professional league; Mexico.','LNBP official website'],
   'BCLA':['Basketball Champions League Americas is an international men’s club competition in the Americas.','International club competition; Americas.','FIBA official website'],
   'BAL':['Basketball Africa League is a professional men’s club competition in Africa, organized through a partnership involving FIBA Africa and the NBA.','International club competition; Africa.','BAL official website'],
   'FIBA Basketball World Cup':['FIBA’s global men’s national-team basketball championship.','National teams; international.','FIBA official website'],
   'NBA':['North American professional men’s basketball league with 30 teams.','Professional league; USA / Canada.','NBA official website'],
   'NBA G League':['NBA’s official minor league and development competition for professional players.','Developmental professional league; USA.','NBA G League official website'],
   'PBA':['Professional men’s basketball league in the Philippines.','Professional league; Philippines.','PBA official website'],
   'NBL–Pilipinas':['Philippine professional basketball competition. IMG uses verified league schedules, standings and official social posts when available.','Professional club competition; Philippines.','NBL–Pilipinas official channels'],
   'Vietnam Basketball Association (VBA)':['Vietnam’s professional basketball league. The 2026 competition information is maintained by VBA and its official channels.','Professional league; Vietnam.','VBA official website'],
   'Maharlika Pilipinas Basketball League (MPBL)':['Philippine regional professional basketball league featuring teams representing cities and provinces.','Professional league; Philippines.','MPBL official channels'],
   // Football
   'Premier League':['Top tier of the English football pyramid. The league has 20 clubs and a 380-match season, with clubs playing each other home and away.','Professional league; England.','Premier League official website'],
   'La Liga':['Spain’s top professional men’s football division.','Professional league; Spain.','LALIGA official website'],
   'Serie A':['Italy’s top professional men’s football division.','Professional league; Italy.','Lega Serie A official website'],
   'Bundesliga':['Germany’s top professional men’s football division.','Professional league; Germany.','Bundesliga official website'],
   'Ligue 1':['France’s top professional men’s football division.','Professional league; France.','Ligue 1 official website'],
   'UEFA Champions League':['UEFA’s premier European men’s club football competition.','International club competition; Europe.','UEFA official website'],
   'UEFA Europa League':['UEFA’s second-tier European men’s club football competition.','International club competition; Europe.','UEFA official website'],
   'UEFA Conference League':['UEFA’s third-tier European men’s club football competition.','International club competition; Europe.','UEFA official website'],
   'MLS':['Top-level professional men’s football league in the United States and Canada.','Professional league; USA / Canada.','MLS official website'],
   'Liga MX':['Mexico’s top professional men’s football division.','Professional league; Mexico.','Liga MX official website'],
   'Brasileirão Série A':['Brazil’s top national men’s football division.','Professional league; Brazil.','CBF / Brasileirão official channels'],
   'Liga Portugal':['Portugal’s top professional men’s football division.','Professional league; Portugal.','Liga Portugal official website'],
   'Eredivisie':['Netherlands’ top professional men’s football division.','Professional league; Netherlands.','Eredivisie official website'],
   'Saudi Pro League':['Saudi Arabia’s top professional men’s football division.','Professional league; Saudi Arabia.','Saudi Pro League official website'],
   'J1 League':['Japan’s top professional men’s football division.','Professional league; Japan.','J.LEAGUE official website'],
   'A-League':['Australia and New Zealand’s professional football competition.','Professional league; Australia / New Zealand.','A-Leagues official website'],
   'Philippine Football League':['Top domestic men’s football league in the Philippines, under the Philippine Football Federation structure.','Professional league; Philippines.','Philippine Football Federation'],
   'FIFA World Cup':['FIFA’s global men’s national-team football championship.','National teams; international.','FIFA official website'],
   // Baseball
   'MLB':['Major League Baseball is the top professional baseball league in the United States and Canada.','Professional league; USA / Canada.','MLB official website'],
   'NPB':['Nippon Professional Baseball is Japan’s top professional baseball organization.','Professional league; Japan.','NPB official website'],
   'KBO League':['South Korea’s top professional baseball league.','Professional league; South Korea.','KBO official website'],
   'KBO Futures League':['Developmental baseball competition connected to the KBO system.','Developmental league; South Korea.','KBO official website'],
   'CPBL':['Chinese Professional Baseball League is the professional baseball league in Taiwan.','Professional league; Chinese Taipei / Taiwan.','CPBL official website'],
   'LMB':['Liga Mexicana de Béisbol is Mexico’s professional baseball league.','Professional league; Mexico.','LMB official website'],
   'Liga de Béisbol Profesional':['Professional baseball competition in Latin America; IMG displays league-specific data only when the competition source is verified.','Professional baseball; Latin America.','League / federation sources'],
   'World Baseball Classic':['International national-team baseball tournament sanctioned through the World Baseball Softball Confederation and MLB partnership.','National teams; international.','World Baseball Classic official channels'],
   // Tennis
   'ATP Tour':['Global men’s professional tennis circuit operated by the ATP.','Professional individual sport; international.','ATP Tour official website'],
   'WTA Tour':['Global women’s professional tennis circuit operated by the WTA.','Professional individual sport; international.','WTA official website'],
   'Grand Slam — Australian Open':['Grand Slam tennis tournament played annually in Melbourne, Australia.','Grand Slam; Australia.','Australian Open official website'],
   'Grand Slam — Roland-Garros':['Grand Slam tennis tournament played annually in Paris, France.','Grand Slam; France.','Roland-Garros official website'],
   'Grand Slam — Wimbledon':['Grand Slam tennis tournament played annually at the All England Club in London.','Grand Slam; United Kingdom.','Wimbledon official website'],
   'Grand Slam — US Open':['Grand Slam tennis tournament played annually in New York, United States.','Grand Slam; USA.','US Open official website'],
   'Davis Cup':['International men’s team tennis competition.','National teams; international.','ITF / Davis Cup official website'],
   'Billie Jean King Cup':['International women’s team tennis competition.','National teams; international.','ITF / Billie Jean King Cup official website'],
   // Hockey
   'NHL':['North American professional ice hockey league.','Professional league; USA / Canada.','NHL official website'],
   'KHL':['Professional ice hockey league operating across Eurasia.','Professional league; Eurasia.','KHL official website'],
   'SHL':['Sweden’s top professional ice hockey league.','Professional league; Sweden.','SHL official website'],
   'Liiga':['Finland’s top professional ice hockey league.','Professional league; Finland.','Liiga official website'],
   'National League':['Switzerland’s top professional ice hockey competition.','Professional league; Switzerland.','Swiss Ice Hockey official channels'],
   'DEL':['Germany’s top professional ice hockey league.','Professional league; Germany.','DEL official website'],
   'ICE Hockey League':['Central European professional ice hockey competition.','Regional professional league; Central Europe.','ICE Hockey League official website'],
   'IIHF World Championship':['International men’s ice hockey championship organized by the IIHF.','National teams; international.','IIHF official website'],
   // Cricket
   'IPL':['Indian Premier League is India’s professional Twenty20 cricket league.','Professional T20 league; India.','IPL official website'],
   'Big Bash League':['Australia’s professional Twenty20 cricket league.','Professional T20 league; Australia.','Cricket Australia / BBL'],
   'The Hundred':['Professional 100-ball cricket competition in England and Wales.','Professional limited-overs competition; UK.','The Hundred official website'],
   'T20 Blast':['England and Wales professional Twenty20 domestic cricket competition.','Professional T20 competition; UK.','ECB official website'],
   'PSL':['Pakistan Super League is Pakistan’s professional Twenty20 cricket league.','Professional T20 league; Pakistan.','PCB / PSL official website'],
   'BPL':['Bangladesh Premier League is Bangladesh’s professional Twenty20 cricket league.','Professional T20 league; Bangladesh.','BPL / Bangladesh Cricket Board'],
   'SA20':['South Africa’s professional Twenty20 cricket league.','Professional T20 league; South Africa.','SA20 official website'],
   'CPL':['Caribbean Premier League is a professional Twenty20 cricket competition in the Caribbean.','Professional T20 competition; Caribbean.','CPL official website'],
   'Major League Cricket':['Professional Twenty20 cricket league in the United States.','Professional T20 league; USA.','Major League Cricket official website'],
   'ICC Cricket World Cup':['International men’s one-day cricket championship organized by the International Cricket Council.','National teams; international.','ICC official website'],
   // Volleyball
   'Nations League':['FIVB Volleyball Nations League is an annual international competition for national teams.','National teams; international.','FIVB official website'],
   'CEV Champions League':['Europe’s leading club volleyball competition organized by CEV.','Club competition; Europe.','CEV official website'],
   'PlusLiga':['Poland’s top professional men’s volleyball league.','Professional league; Poland.','PlusLiga / PZPS'],
   'SuperLega':['Italy’s top professional men’s volleyball league.','Professional league; Italy.','Lega Pallavolo Serie A'],
   'Superliga':['Brazil’s top professional volleyball competition.','Professional league; Brazil.','CBV / Superliga official channels'],
   'V.League':['Japan’s professional volleyball competition structure.','Professional volleyball; Japan.','SV.LEAGUE / Japan Volleyball'],
   'PVL':['Premier Volleyball League is a major professional volleyball competition in the Philippines.','Professional league; Philippines.','PVL official website'],
   'Asian Volleyball Championship':['Asian national-team volleyball championship organized under the Asian volleyball confederation.','National teams; Asia.','AVC / Asian Volleyball Confederation'],
   // Rugby
   'Six Nations':['Annual European international rugby union championship involving six national teams.','National teams; Europe.','Six Nations Rugby'],
   'Rugby Championship':['Annual southern-hemisphere international rugby union championship involving Argentina, Australia, New Zealand and South Africa.','National teams; international.','SANZAAR / Rugby Championship'],
   'Premiership Rugby':['England’s top professional men’s rugby union club competition.','Professional league; England.','Premiership Rugby official website'],
   'Top 14':['France’s top professional rugby union club competition.','Professional league; France.','LNR official website'],
   'United Rugby Championship':['Professional rugby union competition involving clubs from Ireland, Italy, Scotland, South Africa and Wales.','Professional league; Europe / South Africa.','URC official website'],
   'Super Rugby Pacific':['Professional rugby union competition involving clubs from Australia, Fiji, New Zealand and the Pacific region.','Professional league; Oceania.','Super Rugby Pacific'],
   'Rugby World Cup':['Global men’s rugby union championship organized by World Rugby.','National teams; international.','World Rugby official website'],
   // Golf
   'PGA Tour':['Men’s professional golf tour based in North America and featuring tournaments around the world.','Professional individual sport; international.','PGA TOUR official website'],
   'DP World Tour':['Men’s professional golf tour headquartered in Europe with events internationally.','Professional individual sport; international.','DP World Tour official website'],
   'LPGA Tour':['Women’s professional golf tour with events in North America and internationally.','Professional individual sport; international.','LPGA official website'],
   'LIV Golf':['Professional men’s golf league featuring team and individual competition.','Professional individual/team sport; international.','LIV Golf official website'],
   'Asian Tour':['Men’s professional golf tour serving Asia and other international markets.','Professional individual sport; Asia / international.','Asian Tour official website'],
   'PGA Tour Champions':['Professional golf tour for senior men’s players.','Professional individual sport; USA / international.','PGA TOUR official website'],
   'The Masters':['Major men’s golf championship held annually at Augusta National Golf Club.','Major championship; USA.','Masters Tournament official website'],
   'Ryder Cup':['Biennial men’s team golf competition between Europe and the United States.','Team competition; international.','Ryder Cup official website'],
   // Boxing
   'WBC':['World Boxing Council, one of the major sanctioning bodies in professional boxing.','Boxing sanctioning body; international.','WBC official website'],
   'WBA':['World Boxing Association, one of the major sanctioning bodies in professional boxing.','Boxing sanctioning body; international.','WBA official website'],
   'IBF':['International Boxing Federation, one of the major sanctioning bodies in professional boxing.','Boxing sanctioning body; international.','IBF official website'],
   'WBO':['World Boxing Organization, one of the major sanctioning bodies in professional boxing.','Boxing sanctioning body; international.','WBO official website'],
   // Motorsport
   'Formula 1':['FIA Formula One World Championship, the highest level of international single-seater circuit racing.','World championship; international.','Formula 1 official website'],
   'MotoGP':['Premier international motorcycle road-racing world championship.','World championship; international.','MotoGP official website'],
   'NASCAR Cup Series':['NASCAR’s premier stock-car racing series in the United States.','Professional motorsport; USA.','NASCAR official website'],
   'IndyCar Series':['Premier open-wheel racing championship in the United States.','Professional motorsport; USA.','INDYCAR official website'],
   'World Rally Championship':['FIA world championship for rallying.','World championship; international.','FIA / WRC official website'],
   'Formula E':['FIA world championship for electric single-seater racing.','World championship; international.','Formula E official website'],
   // Cycling
   'UCI WorldTour':['Top tier of men’s professional road cycling, sanctioned by the UCI.','Professional cycling; international.','UCI official website'],
   'Tour de France':['Annual multi-stage men’s road cycling race in France and neighboring countries.','Grand Tour; international.','Tour de France official website'],
   'Giro d’Italia':['Annual multi-stage men’s road cycling Grand Tour centered in Italy.','Grand Tour; international.','Giro d’Italia official website'],
   'Vuelta a España':['Annual multi-stage men’s road cycling Grand Tour centered in Spain.','Grand Tour; international.','La Vuelta official website'],
   // Athletics
   'Diamond League':['World Athletics’ premier one-day athletics series; the 2026 calendar contains 14 qualifying meetings before the final.','Track and field series; international.','World Athletics official website'],
   'World Athletics Championships':['World championship for outdoor track and field organized by World Athletics.','World championship; international.','World Athletics official website'],
   'World Indoor Championships':['World championship for indoor track and field organized by World Athletics.','World championship; international.','World Athletics official website'],
   // Swimming
   'World Aquatics Championships':['World Aquatics’ flagship global championships covering swimming and other aquatic disciplines.','World championship; international.','World Aquatics official website'],
   'World Aquatics Swimming World Cup':['International swimming series organized by World Aquatics.','Swimming series; international.','World Aquatics official website'],
   // Combat sports
   'UFC':['Global mixed martial arts promotion featuring professional MMA events.','Combat-sports promotion; international.','UFC official website'],
   'ONE Championship':['Combat-sports organization based in Asia featuring MMA, Muay Thai, kickboxing and other disciplines.','Combat-sports promotion; international.','ONE Championship official website'],
   'PFL':['Professional mixed martial arts promotion using a season-based competition structure in parts of its format.','Combat-sports promotion; international.','PFL official website'],
   'Bellator':['Professional mixed martial arts promotion; historical Bellator events and records are retained as part of MMA history.','Combat-sports promotion; international.','PFL / Bellator official channels']
  };
  const info=facts[name] || [name+' is a sports competition listed in IMG’s global directory. Season-specific information is added only after verification from the organizer, federation or official social channels.','Competition profile; '+(location||'international')+'.','Official organizer / federation / social channels'];
  const officialSources={
   'Premier League':'https://www.premierleague.com/','La Liga':'https://www.laliga.com/','Serie A':'https://www.legaseriea.it/','Bundesliga':'https://www.bundesliga.com/','Ligue 1':'https://www.ligue1.com/',
   'UEFA Champions League':'https://www.uefa.com/uefachampionsleague/','UEFA Europa League':'https://www.uefa.com/uefaeuropaleague/','UEFA Conference League':'https://www.uefa.com/uefaconferenceleague/',
   'MLS':'https://www.mlssoccer.com/','Liga MX':'https://www.ligamx.net/','Brasileirão Série A':'https://www.cbf.com.br/','Liga Portugal':'https://www.ligaportugal.pt/','Eredivisie':'https://eredivisie.nl/','Saudi Pro League':'https://www.spl.com.sa/','J1 League':'https://www.jleague.co/','A-League':'https://aleagues.com.au/','Philippine Football League':'https://pff.org.ph/','FIFA World Cup':'https://www.fifa.com/en/tournaments/mens/worldcup',
   'MLB':'https://www.mlb.com/','NPB':'https://npb.jp/','KBO League':'https://www.koreabaseball.com/','KBO Futures League':'https://www.koreabaseball.com/','CPBL':'https://www.cpbl.com.tw/','LMB':'https://www.milb.com/mexican','World Baseball Classic':'https://www.mlb.com/world-baseball-classic',
   'ATP Tour':'https://www.atptour.com/','WTA Tour':'https://www.wtatennis.com/','Grand Slam — Australian Open':'https://ausopen.com/','Grand Slam — Roland-Garros':'https://www.rolandgarros.com/','Grand Slam — Wimbledon':'https://www.wimbledon.com/','Grand Slam — US Open':'https://www.usopen.org/','Davis Cup':'https://www.daviscup.com/','Billie Jean King Cup':'https://www.billiejeankingcup.com/',
   'NHL':'https://www.nhl.com/','KHL':'https://www.khl.ru/','SHL':'https://www.shl.se/','Liiga':'https://www.liiga.fi/','National League':'https://www.nationalleague.ch/','DEL':'https://www.penny-del.org/','ICE Hockey League':'https://ice.hockey/','IIHF World Championship':'https://www.iihf.com/en/events',
   'IPL':'https://www.iplt20.com/','Big Bash League':'https://www.cricket.com.au/big-bash-league','The Hundred':'https://www.thehundred.com/','T20 Blast':'https://www.ecb.co.uk/','PSL':'https://www.pcb.com.pk/','BPL':'https://www.tigercricket.com.bd/','SA20':'https://www.sa20.co.za/','CPL':'https://www.cplt20.com/','Major League Cricket':'https://www.majorleaguecricket.com/','ICC Cricket World Cup':'https://www.icc-cricket.com/',
   'Nations League':'https://en.volleyballworld.com/volleyball/competitions/volleyball-nations-league/','CEV Champions League':'https://www.cev.eu/','PlusLiga':'https://www.plusliga.pl/','SuperLega':'https://www.legavolley.it/','Superliga':'https://www.cbv.com.br/','V.League':'https://www.svleague.jp/','PVL':'https://www.pvl.ph/','Asian Volleyball Championship':'https://asianvolleyball.net/',
   'Six Nations':'https://www.sixnationsrugby.com/','Rugby Championship':'https://www.sanzarrugby.com/','Premiership Rugby':'https://www.premiershiprugby.com/','Top 14':'https://www.lnr.fr/','United Rugby Championship':'https://www.unitedrugby.com/','Super Rugby Pacific':'https://super.rugby/superrugby/','Rugby World Cup':'https://www.rugbyworldcup.com/',
   'PGA Tour':'https://www.pgatour.com/','DP World Tour':'https://www.europeantour.com/','LPGA Tour':'https://www.lpga.com/','LIV Golf':'https://www.livgolf.com/','Asian Tour':'https://www.asiantour.com/','PGA Tour Champions':'https://www.pgatour.com/champions','The Masters':'https://www.masters.com/','Ryder Cup':'https://www.rydercup.com/',
   'WBC':'https://wbcboxing.com/','WBA':'https://www.wbaboxing.com/','IBF':'https://www.ibf-usba-boxing.com/','WBO':'https://www.wboboxing.com/',
   'Formula 1':'https://www.formula1.com/','MotoGP':'https://www.motogp.com/','NASCAR Cup Series':'https://www.nascar.com/','IndyCar Series':'https://www.indycar.com/','World Rally Championship':'https://www.wrc.com/','Formula E':'https://www.fiaformulae.com/',
   'UCI WorldTour':'https://www.uci.org/','Tour de France':'https://www.letour.fr/','Giro d’Italia':'https://www.giroditalia.it/','Vuelta a España':'https://www.lavuelta.es/',
   'Diamond League':'https://www.diamondleague.com/','World Athletics Championships':'https://worldathletics.org/competitions/world-athletics-championships','World Indoor Championships':'https://worldathletics.org/competitions/world-athletics-indoor-championships',
   'World Aquatics Championships':'https://www.worldaquatics.com/','World Aquatics Swimming World Cup':'https://www.worldaquatics.com/competitions/swimming-world-cup',
   'UFC':'https://www.ufc.com/','ONE Championship':'https://www.onefc.com/','PFL':'https://pflmma.com/','Bellator':'https://pflmma.com/bellator'
  };
  const search='https://www.google.com/search?q='+encodeURIComponent(name+' official');
  const officialUrl=officialSources[name]||search;
  const officialLabel=officialSources[name]?'Official '+name+' source':'Find official source / Facebook';
  content.innerHTML=`<div class="ld-grid">
   <div class="ld-card"><h3>About ${esc(name)}</h3><p class="ld-sub">${esc(info[0])}</p><div class="ld-note"><b>Competition type:</b> ${esc(info[1])}</div></div>
   <div class="ld-card"><h3>Verified data policy</h3><p class="ld-sub">IMG keeps each league independent. Teams, standings, schedules, results and player statistics are shown only when verified for <b>${esc(name)}</b>.</p><div class="ld-note"><b>Source priority:</b> official league/organizer → federation → official Facebook/social page → reliable sports source.</div></div>
  </div>
  <div class="ld-card" style="margin-top:16px"><h3>League facts</h3><div class="ld-note"><b>Sport:</b> ${esc(sport)}<br><b>Region:</b> ${esc(location||'International')}<br><b>Organizer / source:</b> ${esc(info[2])}</div><p class="ld-source" style="margin-top:14px">${source(officialUrl,officialLabel)}</p></div>
  <div class="ld-card" style="margin-top:16px"><h3>Available competition data</h3><p class="ld-sub">IMG uses the league-specific source above as the starting point for this competition. The page is structured to show real competition data without borrowing information from another league.</p><div class="ld-grid" style="margin-top:12px"><div class="ld-note"><b>Teams / participants</b><br>Show the official participants when published by the league, federation or official social channel.</div><div class="ld-note"><b>Standings / rankings</b><br>Show official table, ranking or points data when published.</div><div class="ld-note"><b>Schedule / results</b><br>Show fixtures, completed results and scores when published.</div><div class="ld-note"><b>Players / statistics</b><br>Show rosters, leaders and statistics when the source publishes them.</div></div><div class="ld-note" style="margin-top:12px"><b>Season rule:</b> Current season first. If inactive, use the most recent completed season with verified information. If a particular statistic cannot be verified, only that statistic remains unavailable. It is never replaced with data from another league.</div></div>`;
 } window.scrollTo(0,0);
}
document.addEventListener('click',function(e){
 const detail=document.getElementById('img-league-detail');
 if(detail.style.display!=='block' || !homeSearchOpenedLeague) return;
 const wrap=e.target.closest('.ld-wrap');
 if(wrap) return;
 detail.style.display='none';
 document.getElementById('ld-content').replaceChildren();
 document.getElementById('img-league-browser').style.display='none';
 homeSearch.value='';
 homeDrop.classList.remove('show');
 homeDrop.innerHTML='';
 homeSearchOpenedLeague=false;
 showHome();
});

window.closeLeagueDetail=function(){
 const fromHomeSearch=(homeSearchOpenedLeague || window.homeSearchOpenedLeague);
 const detail=document.getElementById('img-league-detail');
 const content=document.getElementById('ld-content');
 const browser=document.getElementById('img-league-browser');
 if(detail){ detail.style.display='none'; detail.classList.remove('search-origin'); }
 if(content) content.replaceChildren();
 if(browser){ browser.style.display=fromHomeSearch?'none':'block'; document.body.classList.toggle('league-browser-open', !fromHomeSearch); }
 window.IMGCurrentLeague=null;
 // Clear EVERY homepage search input/dropdown so the search is visibly reset.
 document.querySelectorAll('#home-league-search, .home-league-search input').forEach(function(input){
   input.value='';
   input.blur();
   input.dispatchEvent(new Event('input',{bubbles:true}));
 });
 if(homeDrop){ homeDrop.classList.remove('show'); homeDrop.innerHTML=''; }
 homeSearchOpenedLeague=false;
 window.homeSearchOpenedLeague=false;
  window.IMGLeagueSearchOrigin=false;
 if(fromHomeSearch) showHome();
};
window.IMGOpenLeagueDetail=openDetail;
})();
