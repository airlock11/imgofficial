import fs from "node:fs";

const API_KEY=process.env.SPORTRADAR_API_KEY;
if(!API_KEY){
  console.error("SPORTRADAR_API_KEY is not configured.");
  process.exit(2);
}

const MODE=(process.argv[2]||"live").toLowerCase();
const OUT="sportradar-soccer-data.json";
const BASE="https://api.sportradar.com/soccer/trial/v4/en";
const EXT_BASE="https://api.sportradar.com/soccer-extended/trial/v4/en";
const REQUEST_BUDGET=Number(process.env.SPORTRADAR_REQUEST_BUDGET||900);
const LIVE_RUN_CAP=Number(process.env.SPORTRADAR_LIVE_RUN_CAP||6);
const DEEP_RUN_CAP=Number(process.env.SPORTRADAR_DEEP_RUN_CAP||16);
const PRETRACKING_REQUESTS=Number(process.env.SPORTRADAR_PRETRACKING_REQUESTS||0);
const PRETRACKING_AT=Date.parse(process.env.SPORTRADAR_PRETRACKING_AT||"")||0;
const now=new Date();
const iso=now.toISOString();

const TARGETS=[
  {key:"soccer",names:["premier league","english premier league"],label:"Premier League"},
  {key:"jamaica_pl",names:["premier league"],label:"Jamaica Premier League"},
  {key:"mizoram_pl",names:["mizoram premier league"],label:"Mizoram Premier League"},
  {key:"laliga",names:["laliga","la liga","primera division"],label:"La Liga"},
  {key:"el_salvador_reserves",names:["primera division, reserves","primera division reserves"],label:"Primera Division, Reserves"},
  {key:"seriea",names:["serie a"],label:"Serie A"},
  {key:"bundesliga",names:["bundesliga"],label:"Bundesliga"},
  {key:"champions",names:["uefa champions league","champions league"],label:"UEFA Champions League"},
  {key:"ucl_women",names:["uefa champions league women"],label:"UEFA Champions League Women"},
  {key:"mls",names:["major league soccer","mls"],label:"MLS"},
  {key:"pfl",names:["philippines football league","philippine football league"],label:"Philippine Football League"},
  {key:"j1",names:["j1 league","j.league","j league"],label:"J1 League"}
];

const data=readExisting();
data.usage=data.usage||{requests:[]};
const cutoff30=Date.now()-30*24*60*60*1000;
data.usage.requests=safeArray(data.usage.requests).filter(x=>(Date.parse(x?.at)||0)>=cutoff30);
const trackedRolling=data.usage.requests.reduce((sum,x)=>sum+(Number(x?.count)||0),0);
const pretrackingRolling=PRETRACKING_AT>=cutoff30?PRETRACKING_REQUESTS:0;
const rollingUsed=trackedRolling+pretrackingRolling;
const runCap=MODE==="deep"?DEEP_RUN_CAP:LIVE_RUN_CAP;

const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let requests=0;
let lastRequestAt=0;
async function requestJson(base,path,{optional=false}={}){
  if(requests>=runCap){
    console.warn(`Per-run request cap reached (${requests}/${runCap}); skipping ${path}`);
    return null;
  }
  if(rollingUsed+requests>=REQUEST_BUDGET){
    console.warn(`Rolling 30-day request budget reached (${rollingUsed+requests}/${REQUEST_BUDGET}); skipping ${path}`);
    return null;
  }
  const minGap=2300;
  const wait=Math.max(0,minGap-(Date.now()-lastRequestAt));
  if(wait)await sleep(wait);

  let attempt=0;
  while(attempt<5){
    if(requests>=runCap||rollingUsed+requests>=REQUEST_BUDGET)return null;
    attempt++;
    requests++;
    lastRequestAt=Date.now();

    const res=await fetch(base+path,{headers:{"x-api-key":API_KEY,"accept":"application/json"}});
    if(res.ok)return res.json();

    const body=await res.text().catch(()=>"");
    const safeMessage=`Sportradar ${res.status} for ${path}: ${body.slice(0,180)}`;

    if(res.status===429&&attempt<5){
      const retryAfter=Number(res.headers.get("retry-after"));
      const backoff=Number.isFinite(retryAfter)&&retryAfter>0
        ? retryAfter*1000
        : Math.min(30000,2500*Math.pow(2,attempt-1));
      console.warn(`${safeMessage} · retrying in ${Math.ceil(backoff/1000)}s`);
      await sleep(backoff);
      continue;
    }

    if(optional){
      console.warn(safeMessage);
      return null;
    }
    throw new Error(safeMessage);
  }

  if(optional)return null;
  throw new Error(`Sportradar request failed after retries for ${path}`);
}
async function sr(path,opts){return requestJson(BASE,path,opts)}
async function sx(path,opts){return requestJson(EXT_BASE,path,opts)}

function readExisting(){
  try{return JSON.parse(fs.readFileSync(OUT,"utf8"))}catch{return {}}
}
function norm(s){return String(s||"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}
function targetKey(name,category=""){
  const n=norm(name);
  const cat=norm(category);

  if(n==="premier league"&&cat.includes("jamaica"))return "jamaica_pl";
  if(n==="premier league"&&(cat.includes("england")||cat.includes("england amateur")))return "soccer";
  if(n==="mizoram premier league")return "mizoram_pl";
  if((n==="primera division reserves"||n==="primera division reserve")&&cat.includes("el salvador"))return "el_salvador_reserves";
  if(n==="uefa champions league women")return "ucl_women";
  if(n==="uefa champions league")return "champions";
  if((n==="la liga"||n==="laliga"||n==="primera division")&&cat.includes("spain"))return "laliga";

  const exact=TARGETS.find(t=>t.names.some(x=>n===norm(x)));
  return exact?.key||null;
}
function eventItems(payload){
  if(Array.isArray(payload?.schedules))return payload.schedules;
  if(Array.isArray(payload?.sport_events))return payload.sport_events;
  if(Array.isArray(payload?.events))return payload.events;
  return [];
}
function normalizeGame(item){
  const event=item?.sport_event||item?.event||item||{};
  const status=item?.sport_event_status||item?.status||{};
  const context=event?.sport_event_context||item?.sport_event_context||{};
  const comp=context?.competition||event?.competition||{};
  const competitors=Array.isArray(event?.competitors)?event.competitors:[];
  const home=competitors.find(x=>x.qualifier==="home")||competitors[0]||{};
  const away=competitors.find(x=>x.qualifier==="away")||competitors[1]||{};
  const srState=String(status?.status||status?.match_status||event?.status||"").toLowerCase();
  const live=["live","inprogress","in_progress","1st_half","2nd_half","halftime","overtime","penalties","extra_time"].some(x=>srState.includes(x));
  const final=["closed","ended","complete","completed"].some(x=>srState.includes(x));
  const state=live?"live":final?"final":"scheduled";
  const homeScore=status?.home_score ?? status?.period_scores?.at?.(-1)?.home_score ?? "—";
  const awayScore=status?.away_score ?? status?.period_scores?.at?.(-1)?.away_score ?? "—";
  return {
    eventId:event?.id||"",
    date:event?.start_time||event?.start_time_confirmed||"",
    displayTime:"",
    title:event?.name||"",
    home:home?.name||"TBD",
    away:away?.name||"TBD",
    homeLogo:"",
    awayLogo:"",
    homeScore,
    awayScore,
    status:status?.match_status||status?.status||"Scheduled",
    state,
    venue:event?.venue?.name||"",
    round:context?.round?.name||context?.round?.number||"",
    seasonId:context?.season?.id||"",
    competitionId:comp?.id||"",
    competition:comp?.name||"",
    category:context?.category?.name||"",
    categoryId:context?.category?.id||"",
    sourceName:"Sportradar Soccer API",
    sourceUrl:"https://developer.sportradar.com/soccer"
  };
}
function coverageFromSeasonInfo(payload){
  const info=payload?.season_info||payload?.season||payload||{};
  const coverage=info?.coverage||payload?.coverage||{};
  return coverage&&typeof coverage==="object"?coverage:{};
}
function competitorsFromSeasonInfo(payload){
  const found=[];
  const push=x=>{
    if(!x||typeof x!=="object")return;
    found.push({
      id:x.id||"",
      name:x.name||"",
      abbreviation:x.abbreviation||"",
      country:x.country||"",
      countryCode:x.country_code||"",
      gender:x.gender||""
    });
  };

  for(const x of safeArray(payload?.competitors))push(x);
  for(const x of safeArray(payload?.season?.competitors))push(x);
  for(const stage of safeArray(payload?.stages)){
    for(const group of safeArray(stage?.groups)){
      for(const x of safeArray(group?.competitors))push(x);
    }
  }

  return [...new Map(found.filter(x=>x.id||x.name).map(x=>[x.id||x.name,x])).values()];
}
function safeArray(v){return Array.isArray(v)?v:[]}
function statsSummary(payload){
  if(!payload||typeof payload!=="object")return null;
  const out={};
  for(const key of ["statistics","competitor","players","player_statistics","team_statistics"]){
    if(payload[key]!==undefined)out[key]=payload[key];
  }
  return Object.keys(out).length?out:payload;
}

function standingsRows(payload){
  const all=Array.isArray(payload?.standings)?payload.standings:[];
  const preferred=all.filter(s=>String(s?.type||"").toLowerCase()==="total");
  const sources=preferred.length?preferred:all.slice(0,1);
  const rows=[];

  for(const table of sources){
    for(const group of safeArray(table?.groups)){
      for(const s of safeArray(group?.standings)){
        const c=s.competitor||{};
        rows.push({
          competitorId:c.id||"",
          rank:s.rank??s.position??"",
          team:c.name||"",
          played:s.played??s.games_played??"",
          wins:s.win??s.wins??"",
          draws:s.draw??s.draws??"",
          losses:s.loss??s.losses??"",
          goalsFor:s.goals_for??"",
          goalsAgainst:s.goals_against??"",
          goalDiff:s.goals_diff??s.goal_difference??"",
          points:s.points??""
        });
      }
    }
    for(const s of safeArray(table?.standings)){
      const c=s.competitor||{};
      rows.push({
        competitorId:c.id||"",
        rank:s.rank??s.position??"",
        team:c.name||"",
        played:s.played??s.games_played??"",
        wins:s.win??s.wins??"",
        draws:s.draw??s.draws??"",
        losses:s.loss??s.losses??"",
        goalsFor:s.goals_for??"",
        goalsAgainst:s.goals_against??"",
        goalDiff:s.goals_diff??s.goal_difference??"",
        points:s.points??""
      });
    }
  }

  return [...new Map(rows.filter(x=>x.team).map(x=>[x.competitorId||x.team,x])).values()]
    .sort((a,b)=>(Number(a.rank)||999)-(Number(b.rank)||999));
}
function mergeGames(existing,incoming){
  const map=new Map();
  for(const g of [...(existing||[]),...(incoming||[])]) map.set(String(g.eventId||[g.date,g.away,g.home].join("|")),g);
  return [...map.values()].sort((a,b)=>(Date.parse(a.date)||0)-(Date.parse(b.date)||0));
}

data.version=4;
data.provider="Sportradar";
data.product="Soccer API";
data.access="trial";
data.updatedAt=iso;
data.requestsLastRun=0;
data.leagues=data.leagues||{};
data.catalog=data.catalog||{};

const live=await sr("/schedules/live/schedules.json",{optional:true});
const day=iso.slice(0,10);
const daily=await sr(`/schedules/${day}/schedules.json`,{optional:true});

if(!live&&!daily){
  throw new Error("Sportradar live and daily schedule requests were both unavailable. See the HTTP status messages above.");
}

data.latestFeeds={
  live:live||null,
  daily:daily||null,
  updatedAt:iso
};

const combined=[...eventItems(live),...eventItems(daily)].map(normalizeGame).filter(g=>g.eventId);
const grouped={};
for(const g of combined){
  const key=targetKey(g.competition,g.category);
  if(!key)continue;
  (grouped[key]??=[]).push(g);
}
for(const t of TARGETS){
  const fresh=grouped[t.key]||[];
  const old=data.leagues[t.key]?.games||[];
  const keepOld=old.filter(g=>{
    const age=Math.abs(Date.now()-(Date.parse(g.date)||0));
    if(age>=8*24*60*60*1000)return false;
    const mapped=targetKey(g.competition,g.category||"");
    if(mapped!==t.key)return false;
    if(t.key==="soccer"&&norm(g.competition)==="premier league"&&!g.category)return false;
    return true;
  });
  data.leagues[t.key]={
    ...(data.leagues[t.key]||{}),
    league:t.label,
    sourceName:"Sportradar Soccer API",
    sourceUrl:"https://developer.sportradar.com/soccer",
    updatedAt:iso,
    games:mergeGames(keepOld,fresh)
  };
}

if(MODE==="deep"){
  data.entities=data.entities||{competitors:{},players:{}};
  data.catalog=data.catalog||{};

  const catalogAge=Date.now()-(Date.parse(data.catalog.updatedAt||"")||0);
  const shouldRefreshCatalog=!data.catalog.competitions?.length||!data.catalog.seasons?.length||catalogAge>7*24*60*60*1000;

  if(shouldRefreshCatalog){
    const competitions=await sr("/competitions.json",{optional:true});
    const seasons=await sr("/seasons.json",{optional:true});
    const extendedSeasons=await sx("/seasons.json",{optional:true});
    if(competitions?.competitions)data.catalog.competitions=competitions.competitions;
    if(seasons?.seasons)data.catalog.seasons=seasons.seasons;
    if(extendedSeasons?.seasons)data.catalog.extendedSeasons=extendedSeasons.seasons;
    if(competitions||seasons||extendedSeasons)data.catalog.updatedAt=iso;
  }

  const comps=safeArray(data.catalog.competitions);
  const seasonList=safeArray(data.catalog.seasons);
  const dayIndex=Math.floor(Date.now()/86400000)%TARGETS.length;
  const selected=[TARGETS[dayIndex]];

  for(const t of selected){
    if(!t)continue;
    const comp=comps.find(c=>{
      const cname=norm(c?.name);
      const cat=norm(c?.category?.name||c?.category_name||"");
      const mapped=targetKey(c?.name||"",cat);
      return mapped===t.key||t.names.some(n=>cname===norm(n));
    });
    if(!comp?.id)continue;

    let candidates=seasonList.filter(s=>s?.competition_id===comp.id&&!s?.disabled);
    if(!candidates.length){
      const compSeasons=await sr(`/competitions/${encodeURIComponent(comp.id)}/seasons.json`,{optional:true});
      candidates=safeArray(compSeasons?.seasons).filter(s=>!s?.disabled);
    }

    const current=candidates
      .filter(s=>(Date.parse(s.start_date)||0)<=Date.now()+30*86400000&&(Date.parse(s.end_date)||Infinity)>=Date.now()-30*86400000)
      .sort((a,b)=>(Date.parse(b.start_date)||0)-(Date.parse(a.start_date)||0))[0]
      || candidates.sort((a,b)=>(Date.parse(b.start_date)||0)-(Date.parse(a.start_date)||0))[0];
    if(!current?.id)continue;

    const seasonPath=`/seasons/${encodeURIComponent(current.id)}`;

    // Start with Season Info so coverage flags decide which expensive feeds are worth calling.
    const seasonInfo=await sr(seasonPath+"/info.json",{optional:true});
    const coverage=coverageFromSeasonInfo(seasonInfo);
    const competitionProperties=coverage?.competition_properties||coverage?.competition||{};
    const sportEventProperties=coverage?.sport_event_properties||coverage?.sport_event||{};

    const schedule=await sr(seasonPath+"/schedules.json",{optional:true});
    const competitorsPayload=await sr(seasonPath+"/competitors.json",{optional:true});
    const venuesPayload=await sr(seasonPath+"/venues.json",{optional:true});

    const standingsSupported=competitionProperties?.standings!==false&&String(competitionProperties?.standings||"").toLowerCase()!=="false";
    const leadersSupported=Boolean(competitionProperties?.season_stats_leaders||competitionProperties?.season_player_statistics||competitionProperties?.season_team_statistics);
    const missingSupported=Boolean(competitionProperties?.missing_players);
    const squadsSupported=Boolean(competitionProperties?.team_squads);
    const lineupsSupported=Boolean(sportEventProperties?.lineups);
    const summariesSupported=Boolean(
      sportEventProperties?.basic_team_stats||
      sportEventProperties?.basic_player_stats||
      sportEventProperties?.extended_team_stats||
      sportEventProperties?.extended_player_stats||
      sportEventProperties?.deeper_team_stats||
      sportEventProperties?.deeper_player_stats
    );

    const standings=standingsSupported?await sr(seasonPath+"/standings.json",{optional:true}):null;
    const leadersPayload=leadersSupported?await sr(seasonPath+"/leaders.json",{optional:true}):null;
    const missingPayload=missingSupported?await sr(seasonPath+"/missing_players.json",{optional:true}):null;
    const playersPayload=squadsSupported?await sx(seasonPath+"/competitor_players.json",{optional:true}):null;
    const summariesPayload=summariesSupported?await sr(seasonPath+"/summaries.json?limit=100",{optional:true}):null;
    const lineupsPayload=lineupsSupported?await sx(seasonPath+"/lineups.json?limit=100",{optional:true}):null;
    const transfersPayload=await sr(seasonPath+"/transfers.json",{optional:true});

    const normalizedSchedule=eventItems(schedule).map(normalizeGame).filter(g=>g.eventId);
    const competitors=safeArray(competitorsPayload?.competitors);
    const players=[
      ...safeArray(playersPayload?.players),
      ...safeArray(playersPayload?.competitors).flatMap(x=>safeArray(x?.players))
    ];
    for(const x of competitors){
      if(x?.id)data.entities.competitors[x.id]={...(data.entities.competitors[x.id]||{}),...x,lastSeenAt:iso};
    }
    for(const x of players){
      if(x?.id)data.entities.players[x.id]={...(data.entities.players[x.id]||{}),...x,lastSeenAt:iso};
    }

    // Enrich one team per deep run. Cached profiles/stats are refreshed only every 7 days.
    let teamProfile=null;
    let basicStats=null;
    let extendedStats=null;
    const firstTeam=competitors.find(x=>x?.id);
    if(firstTeam?.id){
      const cached=data.entities.competitors[firstTeam.id]||{};
      const profileAge=Date.now()-(Date.parse(cached.profileUpdatedAt||"")||0);
      if(profileAge>7*24*60*60*1000){
        const profile=await sr(`/competitors/${encodeURIComponent(firstTeam.id)}/profile.json`,{optional:true});
        if(profile){
          teamProfile=profile;
          data.entities.competitors[firstTeam.id]={...cached,profile,profileUpdatedAt:iso,lastSeenAt:iso};
        }
      }else{
        teamProfile=cached.profile||null;
      }

      const statsAge=Date.now()-(Date.parse(cached.statsUpdatedAt||"")||0);
      if(statsAge>7*24*60*60*1000){
        const stats=await sx(`${seasonPath}/competitors/${encodeURIComponent(firstTeam.id)}/statistics.json`,{optional:true});
        if(stats){
          basicStats=stats;
          data.entities.competitors[firstTeam.id]={
            ...(data.entities.competitors[firstTeam.id]||cached),
            statistics:stats,
            statsUpdatedAt:iso,
            lastSeenAt:iso
          };
        }
      }else{
        basicStats=cached.statistics||null;
      }

      const extendedAllowed=Boolean(
        competitionProperties?.season_team_statistics||
        competitionProperties?.season_player_statistics||
        sportEventProperties?.extended_team_stats||
        sportEventProperties?.extended_player_stats||
        sportEventProperties?.deeper_team_stats||
        sportEventProperties?.deeper_player_stats
      );
      const extAge=Date.now()-(Date.parse(cached.extendedStatsUpdatedAt||"")||0);
      if(extendedAllowed&&extAge>7*24*60*60*1000){
        const ext=await sx(`${seasonPath}/competitors/${encodeURIComponent(firstTeam.id)}/extended_statistics.json`,{optional:true});
        if(ext){
          extendedStats=ext;
          data.entities.competitors[firstTeam.id]={
            ...(data.entities.competitors[firstTeam.id]||cached),
            extendedStatistics:ext,
            extendedStatsUpdatedAt:iso,
            lastSeenAt:iso
          };
        }
      }else{
        extendedStats=cached.extendedStatistics||null;
      }
    }

    data.leagues[t.key]={
      ...(data.leagues[t.key]||{}),
      league:t.label,
      competitionId:comp.id,
      competition:comp,
      seasonId:current.id,
      season:current.name||"",
      seasonStart:current.start_date||"",
      seasonEnd:current.end_date||"",
      coverage,
      competitors,
      players,
      venues:safeArray(venuesPayload?.venues),
      leaders:leadersPayload||null,
      missingPlayers:missingPayload||null,
      transfers:transfersPayload||null,
      summaries:summariesPayload||null,
      lineups:lineupsPayload||null,
      standings:standingsRows(standings),
      games:mergeGames(data.leagues[t.key]?.games||[],normalizedSchedule),
      enrichment:{
        teamProfile:teamProfile||null,
        statistics:basicStats||null,
        extendedStatistics:extendedStats||null
      },
      raw:{
        seasonInfo:seasonInfo||null,
        schedule:schedule||null,
        standings:standings||null,
        competitors:competitorsPayload||null,
        venues:venuesPayload||null,
        players:playersPayload||null,
        leaders:leadersPayload||null,
        missingPlayers:missingPayload||null,
        summaries:summariesPayload||null,
        lineups:lineupsPayload||null,
        transfers:transfersPayload||null
      },
      deepUpdatedAt:iso
    };
  }
}

data.requestsLastRun=requests;
if(requests>0)data.usage.requests.push({at:iso,count:requests,mode:MODE});
data.usage.requests=data.usage.requests.filter(x=>(Date.parse(x?.at)||0)>=cutoff30);
data.usage.trackedRolling30Day=data.usage.requests.reduce((sum,x)=>sum+(Number(x?.count)||0),0);
data.usage.preTrackingRolling30Day=pretrackingRolling;
data.usage.rolling30Day=data.usage.trackedRolling30Day+pretrackingRolling;
data.requestBudget=REQUEST_BUDGET;
data.requestBudgetRemaining=Math.max(0,REQUEST_BUDGET-data.usage.rolling30Day);
data.runRequestCap=runCap;
data.harvestMode=MODE;
fs.writeFileSync(OUT,JSON.stringify(data,null,2)+"\n");
console.log(`Wrote ${OUT} using ${requests} Sportradar requests (${MODE}).`);
