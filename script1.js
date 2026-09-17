
(function(){
const data={
 Basketball:[
  ["NBA","USA / Canada"],["WNBA","USA"],["NCAA","USA"],["NBA G League","USA"],["World Basketball Super League (WBSL)","International"],["EuroLeague","Europe"],
  ["EuroCup","Europe"],["Liga Endesa (ACB)","Spain"],["Super League Basketball","United Kingdom"],["Betclic Élite (LNB Pro A)","France"],
  ["easyCredit BBL","Germany"],["Lega Basket Serie A","Italy"],["Türkiye Sigorta Basketbol Süper Ligi","Türkiye"],["ABA League","Balkans"],
  ["VTB United League","Eastern Europe"],["Greek Basket League","Greece"],["LNB Pro A","France"],
  ["Chinese Basketball Association (CBA)","China"],["PBA","Philippines"],["NBL–Pilipinas","Philippines"],["Vietnam Basketball Association (VBA)","Vietnam"],["Maharlika Pilipinas Basketball League (MPBL)","Philippines"],["PBA D-League","Philippines"],["UAAP Basketball","Philippines"],["NCAA Philippines","Philippines"],["Pilipinas Super League","Philippines"],["B.LEAGUE","Japan"],["KBL","South Korea"],["National Basketball League (NBL)","Australia"],
  ["Basketball Super League (BSL)","Canada / North America"],["Liga Nacional de Baloncesto Profesional (LNBP)","Mexico"],["BCLA","Americas"],["BAL","Africa"],["FIBA Basketball World Cup","International"]
 ],
 Football:[
  ["Premier League","England"],["La Liga","Spain"],["Serie A","Italy"],["Bundesliga","Germany"],["Ligue 1","France"],
  ["UEFA Champions League","Europe"],["UEFA Europa League","Europe"],["UEFA Conference League","Europe"],
  ["MLS","USA / Canada"],["Liga MX","Mexico"],["Brasileirão Série A","Brazil"],["Liga Portugal","Portugal"],
  ["Eredivisie","Netherlands"],["Saudi Pro League","Saudi Arabia"],["J1 League","Japan"],["A-League","Australia"],
  ["Philippine Football League","Philippines"],["FIFA World Cup","International"]
 ],
 Baseball:[
  ["MLB","USA / Canada"],["NPB","Japan"],["KBO League","South Korea"],["KBO Futures League","South Korea"],
  ["CPBL","Chinese Taipei"],["LMB","Mexico"],["Liga de Béisbol Profesional","Latin America"],["World Baseball Classic","International"]
 ],
 Tennis:[
  ["ATP Tour","International"],["WTA Tour","International"],["Grand Slam — Australian Open","Australia"],
  ["Grand Slam — Roland-Garros","France"],["Grand Slam — Wimbledon","United Kingdom"],["Grand Slam — US Open","USA"],
  ["Davis Cup","International"],["Billie Jean King Cup","International"]
 ],
 Hockey:[
  ["NHL","USA / Canada"],["KHL","Eurasia"],["SHL","Sweden"],["Liiga","Finland"],["National League","Switzerland"],
  ["DEL","Germany"],["ICE Hockey League","Central Europe"],["IIHF World Championship","International"]
 ],
 Cricket:[
  ["IPL","India"],["Big Bash League","Australia"],["The Hundred","United Kingdom"],["T20 Blast","United Kingdom"],
  ["PSL","Pakistan"],["BPL","Bangladesh"],["SA20","South Africa"],["CPL","Caribbean"],
  ["Major League Cricket","USA"],["ICC Cricket World Cup","International"]
 ],
 Volleyball:[
  ["Nations League","International"],["CEV Champions League","Europe"],["PlusLiga","Poland"],
  ["SuperLega","Italy"],["Superliga","Brazil"],["V.League","Japan"],["PVL","Philippines"],["Asian Volleyball Championship","Asia"]
 ],
 Rugby:[
  ["Six Nations","Europe"],["Rugby Championship","International"],["Premiership Rugby","England"],
  ["Top 14","France"],["United Rugby Championship","Europe"],["Super Rugby Pacific","Oceania"],["Rugby World Cup","International"]
 ],
 Golf:[
  ["PGA Tour","USA / International"],["DP World Tour","Europe / International"],["LPGA Tour","International"],
  ["LIV Golf","International"],["Asian Tour","Asia"],["PGA Tour Champions","USA"],["The Masters","USA"],["Ryder Cup","International"]
 ],
 Boxing:[
  ["WBC","International"],["WBA","International"],["IBF","International"],["WBO","International"]
 ],
 Motorsport:[
  ["Formula 1","International"],["MotoGP","International"],["NASCAR Cup Series","USA"],["IndyCar Series","USA"],
  ["World Rally Championship","International"],["Formula E","International"]
 ],
 Cycling:[
  ["UCI WorldTour","International"],["Tour de France","France"],["Giro d'Italia","Italy"],["Vuelta a España","Spain"]
 ],
 Athletics:[
  ["Diamond League","International"],["World Athletics Championships","International"],["World Indoor Championships","International"]
 ],
 Swimming:[
  ["World Aquatics Championships","International"],["World Aquatics Swimming World Cup","International"]
 ],
 "Combat Sports":[
  ["UFC","International"],["ONE Championship","International"],["PFL","International"],["Bellator","International"]
 ]
};
const sports=Object.keys(data);
window.IMGLeagueData=data;
const root=document.getElementById('img-league-browser');
const tabs=document.getElementById('img-sports-tabs');
const list=document.getElementById('img-league-list');
const title=document.getElementById('img-league-title');
function render(sport){
 title.textContent=sport;
 tabs.querySelectorAll('button').forEach(b=>b.classList.toggle('active',b.dataset.sport===sport));
 const q=document.getElementById('img-league-search').value.trim().toLowerCase();
 const filtered=data[sport].filter(x=>(x[0]+' '+x[1]).toLowerCase().includes(q));
 list.innerHTML=filtered.length ? filtered.map(x=>`<a class="lb-league" href="#" data-league="${x[0].replace(/"/g,'&quot;')}" data-sport="${sport}"><b>${x[0]}</b><small>${x[1]}</small></a>`).join('') : '<div class="empty">No leagues found.</div>';
}
const search=document.getElementById('img-league-search');
search.addEventListener('input',()=>render(title.textContent));
sports.forEach(s=>{
 const b=document.createElement('button'); b.type='button'; b.className='lb-sport'; b.dataset.sport=s; b.textContent=s;
 b.onclick=()=>render(s); tabs.appendChild(b);
});
render('Basketball');
document.getElementById('img-league-close').onclick=()=>{root.style.display='none';document.body.classList.remove('league-browser-open')};
window.IMGOpenSportsLeagues=(sport)=>{
  window.homeSearchOpenedLeague=false;
  root.style.display='block';
  document.body.classList.add('league-browser-open');
  search.value='';
  render(data[sport] ? sport : 'Basketball');
};
list.addEventListener('click',function(e){
 const card=e.target.closest('.lb-league');
 if(!card) return;
 e.preventDefault();
 e.stopPropagation();
 const name=card.getAttribute('data-league');
 const sport=card.getAttribute('data-sport') || title.textContent;
 // Keep the Sports browser from swallowing the selection. Open the league profile explicitly.
 root.style.display='none';
 document.body.classList.remove('league-browser-open');
 if(typeof window.IMGOpenLeagueDetail==='function'){
   window.IMGOpenLeagueDetail(name,sport);
 }else if(typeof IMGOpenLeagueDetail==='function'){
   IMGOpenLeagueDetail(name,sport);
 }
});
})();
