(function(){
  const MAX_VERIFIED_AGE_MS=30*60*1000;
  const blocked=["HIGHLIGHTS","REPLAY","FULL MATCH","FULL GAME","OPENING CEREMONY","CLOSING CEREMONY","DRAW CEREMONY","PRESS CONFERENCE","INTERVIEW","PODCAST"];

  function asianTitleAllowed(value){
    const upper=String(value||"").toUpperCase();
    const tagged=upper.includes("ASIAN GAMES")||upper.includes("AICHI-NAGOYA")||upper.includes("AICHI NAGOYA")||upper.includes("AICHI 2026");
    return tagged&&!blocked.some(x=>upper.includes(x));
  }

  function asianVerificationFresh(entry){
    const stream=entry&&entry.stream||{};
    const title=entry&&entry.title||stream.title||"";
    const channel=String(stream.channel||"").trim().toLowerCase();
    const checked=Date.parse(entry&&entry.lastVerifiedLiveAt||stream.lastVerifiedLiveAt||"");
    return asianTitleAllowed(title)
      &&channel==="one sports"
      &&Number.isFinite(checked)
      &&Date.now()-checked>=-2*60*1000
      &&Date.now()-checked<=MAX_VERIFIED_AGE_MS;
  }

  if(typeof loadVerifiedChannelLive==="function"){
    const originalLoadVerifiedChannelLive=loadVerifiedChannelLive;
    loadVerifiedChannelLive=async function(){
      const result=await originalLoadVerifiedChannelLive();
      if(!result||!result.ok)return result||{ok:false,updatedAt:"",entries:[]};

      const updated=Date.parse(result.updatedAt||"");
      const fileFresh=Number.isFinite(updated)&&Date.now()-updated<=MAX_VERIFIED_AGE_MS;
      const rows=Array.isArray(result.entries)?result.entries:[];
      const entries=rows.filter(x=>{
        if(!x||!x.stream||!x.stream.watchUrl)return false;
        if(x.leagueKey!=="asian_games")return true;
        return fileFresh&&asianVerificationFresh(x);
      });
      return {...result,entries};
    };
  }

  if(typeof liveNowItemIsCurrent==="function"){
    const originalLiveNowItemIsCurrent=liveNowItemIsCurrent;
    liveNowItemIsCurrent=function(game){
      if(!originalLiveNowItemIsCurrent(game))return false;
      if(!game||game.sportKey!=="asian_games")return true;
      const direct=String(game.eventId||"").startsWith("ag26-youtube-")||game.standaloneStream===true;
      if(!direct)return true;
      const stream=Array.isArray(game.streams)?game.streams[0]:null;
      return asianVerificationFresh({
        title:game.title,
        lastVerifiedLiveAt:game.lastVerifiedLiveAt,
        stream:stream||{}
      });
    };
  }
})();
