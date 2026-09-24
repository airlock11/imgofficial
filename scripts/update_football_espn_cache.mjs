import fs from "node:fs";

const OUT="football-espn-cache.json";
const DAY=86400000;
const now=new Date();
const LEAGUES={
  soccer:{name:"Premier League",espn:"eng.1",category:"England"},
  laliga:{name:"La Liga",espn:"esp.1",category:"Spain"},
  bundesliga:{name:"Bundesliga",espn:"ger.1",category:"Germany"},
  seriea:{name:"Serie A",espn:"ita.1",category:"Italy"}
};

const seasonYear=String(now.getUTCFullYear());
const windowStart=now.getTime()-14*DAY;
const windowEnd=now.getTime()+30*DAY;
const previous=(()=>{try{return JSON.parse(fs.readFileSync(OUT,"utf8"))}catch{return {version:1,leagues:{}}}})();

async function json(url){
  const r=await fetch(url,{headers:{"accept":"application/json","user-agent":"IMG-Football-Cache/1.0"}});
  if(!r.ok)throw new Error(String(r.status)+" "+url);
  return r.json();
}
function logoOf(x){return x?.team?.logo||x?.team?.logos?.[0]?.href||""}
function event(e,cfg){
  const comp=e?.competitions?.[0]||{};
  const teams=comp?.competitors||[];
  const home=teams.find(x=>x?.homeAway==="home")||{};
  const away=teams.find(x=>x?.homeAway==="away")||{};
  const raw=e?.status?.type?.state||comp?.status?.type?.state||"pre";
  return {
    eventId:String(e?.id||""),
    date:e?.date||comp?.date||"",
    displayTime:"",
    home:home?.team?.displayName||home?.team?.name||"Home",
    away:away?.team?.displayName||away?.team?.name||"Away",
    homeLogo:logoOf(home),
    awayLogo:logoOf(away),
    homeScore:home?.score??"",
    awayScore:away?.score??"",
    state:raw==="in"?"live":raw==="post"?"final":"scheduled",
    status:e?.status?.type?.shortDetail||e?.status?.type?.detail||comp?.status?.type?.shortDetail||"",
    venue:comp?.venue?.fullName||"",
    competition:cfg.name,
    category:cfg.category
  };
}
function standings(payload){
  const out=[];
  const walk=node=>{
    if(!node||typeof node!=="object")return;
    if(Array.isArray(node?.standings?.entries)){
      for(const e of node.standings.entries){
        const stats=Object.fromEntries((e?.stats||[]).map(s=>[String(s?.name||s?.abbreviation||"").toLowerCase(),s?.value??s?.displayValue]));
        out.push({
          rank:e?.stats?.find?.(s=>/rank/i.test(String(s?.name||s?.abbreviation)))?.value??e?.seed??out.length+1,
          team:e?.team?.displayName||e?.team?.name||"",
          logo:e?.team?.logos?.[0]?.href||e?.team?.logo||"",
          played:stats.gamesplayed??stats.games??stats.gp??"",
          wins:stats.wins??stats.w??"",
          draws:stats.ties??stats.draws??stats.d??"",
          losses:stats.losses??stats.l??"",
          goalDiff:stats.pointdifferential??stats.goaldifferential??stats.gd??"",
          points:stats.points??stats.pts??""
        });
      }
    }
    for(const c of node?.children||[])walk(c);
  };
  walk(payload);
  return out.filter(x=>x.team);
}

const leagues={};
for(const [key,cfg] of Object.entries(LEAGUES)){
  const old=previous?.leagues?.[key]||{};
  let games=Array.isArray(old.games)?old.games:[];
  let table=Array.isArray(old.standings)?old.standings:[];
  let leagueLogo=old.leagueLogo||"";
  let scoreboardOk=false, standingsOk=false;
  try{
    const sb=await json("https://site.api.espn.com/apis/site/v2/sports/soccer/"+cfg.espn+"/scoreboard?dates="+seasonYear+"&limit=1000");
    games=(sb?.events||[]).map(x=>event(x,cfg)).filter(x=>x.eventId&&(Date.parse(x.date)||0)>=windowStart&&(Date.parse(x.date)||0)<=windowEnd);
    const lg=sb?.leagues?.[0];
    leagueLogo=lg?.logos?.find?.(x=>String(x?.rel||"").includes("full"))?.href||lg?.logos?.[0]?.href||lg?.logo||leagueLogo;
    scoreboardOk=true;
  }catch(e){console.warn(key,"scoreboard",e.message)}
  try{
    const st=await json("https://site.api.espn.com/apis/v2/sports/soccer/"+cfg.espn+"/standings");
    const rows=standings(st);
    if(rows.length)table=rows;
    standingsOk=true;
  }catch(e){console.warn(key,"standings",e.message)}
  leagues[key]={
    name:cfg.name,
    category:cfg.category,
    espn:cfg.espn,
    leagueLogo,
    games,
    standings:table,
    verifiedAt:(scoreboardOk||standingsOk)?new Date().toISOString():(old.verifiedAt||null)
  };
}

const prevStable=JSON.stringify(previous?.leagues||{});
const nextStable=JSON.stringify(leagues);
if(prevStable===nextStable){
  console.log("ESPN football cache unchanged.");
  process.exit(0);
}
const payload={version:1,source:"ESPN public football data",updatedAt:new Date().toISOString(),leagues};
fs.writeFileSync(OUT,JSON.stringify(payload,null,2)+"\n");
console.log("Updated",OUT);
