import fs from "node:fs";

const API_KEY=process.env.SPORTRADAR_API_KEY;
if(!API_KEY){
  console.error("SPORTRADAR_API_KEY is not configured.");
  process.exit(2);
}

const MODE=(process.argv[2]||"live").toLowerCase();
const OUT="sportradar-soccer-data.json";
const BASE="https://api.sportradar.com/soccer/trial/v4/en";
const now=new Date();
const iso=now.toISOString();

const TARGETS=[
  {key:"soccer",names:["premier league","english premier league"],label:"Premier League"},
  {key:"laliga",names:["laliga","la liga","primera division"],label:"La Liga"},
  {key:"seriea",names:["serie a"],label:"Serie A"},
  {key:"bundesliga",names:["bundesliga"],label:"Bundesliga"},
  {key:"champions",names:["uefa champions league","champions league"],label:"UEFA Champions League"},
  {key:"mls",names:["major league soccer","mls"],label:"MLS"},
  {key:"pfl",names:["philippines football league","philippine football league"],label:"Philippine Football League"},
  {key:"j1",names:["j1 league","j.league","j league"],label:"J1 League"}
];

const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let requests=0;
let lastRequestAt=0;
async function sr(path,{optional=false}={}){
  const minGap=2300;
  const wait=Math.max(0,minGap-(Date.now()-lastRequestAt));
  if(wait)await sleep(wait);

  let attempt=0;
  while(attempt<5){
    attempt++;
    requests++;
    lastRequestAt=Date.now();

    const res=await fetch(BASE+path,{headers:{"x-api-key":API_KEY,"accept":"application/json"}});
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

function readExisting(){
  try{return JSON.parse(fs.readFileSync(OUT,"utf8"))}catch{return {}}
}
function norm(s){return String(s||"").toLowerCase().replace(/[^a-z0-9]+/g," ").trim()}
function targetKey(name){
  const n=norm(name);
  const exact=TARGETS.find(t=>t.names.some(x=>n===x||n.includes(x)));
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
    sourceName:"Sportradar Soccer API",
    sourceUrl:"https://developer.sportradar.com/soccer"
  };
}
function standingsRows(payload){
  const groups=Array.isArray(payload?.standings)?payload.standings:[];
  const rows=[];
  for(const group of groups){
    for(const g of (group?.groups||[])){
      for(const s of (g?.standings||[])){
        const c=s.competitor||{};
        rows.push({
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
    for(const s of (group?.standings||[])){
      const c=s.competitor||{};
      rows.push({
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
  return rows.filter(x=>x.team);
}
function mergeGames(existing,incoming){
  const map=new Map();
  for(const g of [...(existing||[]),...(incoming||[])]) map.set(String(g.eventId||[g.date,g.away,g.home].join("|")),g);
  return [...map.values()].sort((a,b)=>(Date.parse(a.date)||0)-(Date.parse(b.date)||0));
}

const data=readExisting();
data.version=2;
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

const combined=[...eventItems(live),...eventItems(daily)].map(normalizeGame).filter(g=>g.eventId);
const grouped={};
for(const g of combined){
  const key=targetKey(g.competition);
  if(!key)continue;
  (grouped[key]??=[]).push(g);
}
for(const t of TARGETS){
  const fresh=grouped[t.key]||[];
  const old=data.leagues[t.key]?.games||[];
  const keepOld=old.filter(g=>{
    const age=Math.abs(Date.now()-(Date.parse(g.date)||0));
    return age<8*24*60*60*1000;
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
  const competitions=await sr("/competitions.json",{optional:true});
  const seasons=await sr("/seasons.json",{optional:true});
  if(!competitions||!seasons){
    console.warn("Deep catalog refresh is partial because competition or season metadata was unavailable.");
  }
  data.catalog.competitions=competitions?.competitions||data.catalog.competitions||[];
  data.catalog.seasons=seasons?.seasons||data.catalog.seasons||[];
  data.catalog.updatedAt=iso;

  const comps=data.catalog.competitions;
  const seasonList=data.catalog.seasons;
  const start=Math.floor((Date.now()/86400000)%TARGETS.length);
  const selected=[0,1,2].map(i=>TARGETS[(start+i)%TARGETS.length]);

  for(const t of selected){
    const comp=comps.find(c=>t.names.some(n=>norm(c?.name).includes(n)));
    if(!comp?.id)continue;
    const candidates=seasonList.filter(s=>s?.competition_id===comp.id&&!s?.disabled);
    const current=candidates
      .filter(s=>(Date.parse(s.start_date)||0)<=Date.now()+30*86400000&&(Date.parse(s.end_date)||Infinity)>=Date.now()-30*86400000)
      .sort((a,b)=>(Date.parse(b.start_date)||0)-(Date.parse(a.start_date)||0))[0]
      || candidates.sort((a,b)=>(Date.parse(b.start_date)||0)-(Date.parse(a.start_date)||0))[0];
    if(!current?.id)continue;

    let schedule=null, standings=null;
    schedule=await sr(`/seasons/${encodeURIComponent(current.id)}/schedules.json`,{optional:true});
    standings=await sr(`/seasons/${encodeURIComponent(current.id)}/standings.json`,{optional:true});

    const normalizedSchedule=eventItems(schedule).map(normalizeGame).filter(g=>g.eventId);
    data.leagues[t.key]={
      ...(data.leagues[t.key]||{}),
      league:t.label,
      competitionId:comp.id,
      seasonId:current.id,
      season:current.name||"",
      seasonStart:current.start_date||"",
      seasonEnd:current.end_date||"",
      standings:standingsRows(standings),
      games:mergeGames(data.leagues[t.key]?.games||[],normalizedSchedule),
      raw:{
        schedule:schedule||null,
        standings:standings||null
      },
      deepUpdatedAt:iso
    };
  }
}

data.requestsLastRun=requests;
fs.writeFileSync(OUT,JSON.stringify(data,null,2)+"\n");
console.log(`Wrote ${OUT} using ${requests} Sportradar requests (${MODE}).`);
