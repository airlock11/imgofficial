(function(){
  const MAX_VERIFIED_AGE_MS=10*60*1000;
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
    loadVerifiedChannelLive=async function(){
      try{
        const r=await fetch("/youtube-live.json?ts="+Date.now(),{cache:"no-store"});
        if(!r.ok)throw new Error("youtube live unavailable");
        const y=await r.json();
        const updated=Date.parse(y&&y.updatedAt||"");
        const fileFresh=Number.isFinite(updated)&&Date.now()-updated<=MAX_VERIFIED_AGE_MS;
        const rows=Array.isArray(y&&y.streams)?y.streams:[];
        const entries=rows.filter(x=>{
          if(!x||!x.stream||!x.stream.watchUrl)return false;
          if(x.leagueKey!=="asian_games")return true;
          return fileFresh&&asianVerificationFresh(x);
        });
        return {ok:true,updatedAt:y&&y.updatedAt||"",entries};
      }catch{
        return {ok:false,updatedAt:"",entries:[]};
      }
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
