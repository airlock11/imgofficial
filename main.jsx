import React, {useMemo, useState} from "react";
import {createRoot} from "react-dom/client";
import {Activity, Bell, ChevronRight, Clock3, Flame, Menu, Search, Star, TrendingUp, Trophy, X} from "lucide-react";
import "./styles.css";

const sports = ["All Sports","Basketball","Football","Tennis","Baseball","Hockey","Cricket","Volleyball","Motorsports","MMA & Boxing"];
const liveGames = [
  {id:1,sport:"Basketball",league:"NBA",home:"Los Angeles",away:"Golden State",hs:87,as:84,period:"Q4",clock:"03:42",status:"LIVE",hot:true},
  {id:2,sport:"Football",league:"Premier League",home:"Arsenal",away:"Chelsea",hs:1,as:0,period:"2H",clock:"71:23",status:"LIVE",hot:true},
  {id:3,sport:"Tennis",league:"ATP • Beijing",home:"A. Player",away:"J. Player",hs:1,as:1,period:"Set 3",clock:"4–3",status:"LIVE"},
  {id:4,sport:"Baseball",league:"MLB",home:"New York",away:"Boston",hs:4,as:3,period:"7th",clock:"2 out",status:"LIVE"},
];
const upcoming = [
  {sport:"Basketball",league:"NBA",home:"Boston",away:"Miami",time:"8:00 PM"},
  {sport:"Football",league:"Champions League",home:"Madrid",away:"Milan",time:"9:30 PM"},
  {sport:"Tennis",league:"WTA • Tokyo",home:"A. Player",away:"B. Player",time:"10:00 PM"},
  {sport:"Hockey",league:"NHL",home:"Toronto",away:"Montreal",time:"10:30 PM"}
];
const odds = [
  {game:"Los Angeles vs Golden State",market:"Moneyline",a:"+120",b:"-140"},
  {game:"Arsenal vs Chelsea",market:"1X2",a:"-135",b:"+390"},
  {game:"Boston vs Miami",market:"Spread",a:"-2.5",b:"+2.5"},
  {game:"Boston vs Miami",market:"Total",a:"O 218.5",b:"U 218.5"}
];

function Badge({children}){return <span className="badge">{children}</span>}
function SportIcon({name}){return <span className="sport-icon">{name==="All Sports"?"★":name.slice(0,2).toUpperCase()}</span>}

function App(){
  const [selected,setSelected]=useState("All Sports");
  const [mobile,setMobile]=useState(false);
  const [search,setSearch]=useState("");
  const filteredLive=useMemo(()=>liveGames.filter(g=>
    (selected==="All Sports"||g.sport===selected) &&
    `${g.home} ${g.away} ${g.league}`.toLowerCase().includes(search.toLowerCase())
  ),[selected,search]);

  return <div className="app">
    <header className="topbar">
      <div className="brand"><div className="brand-mark">IMG</div><div><strong>IMGOFFICIAL</strong><small>LIVE SPORTS DATA</small></div></div>
      <nav className="desktop-nav"><a className="active">Live</a><a>Scores</a><a>Statistics</a><a>Odds</a></nav>
      <div className="actions">
        <label className="search"><Search size={17}/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search teams, games..." /></label>
        <button className="icon-btn"><Bell size={18}/></button>
        <button className="menu-btn icon-btn" onClick={()=>setMobile(!mobile)}>{mobile?<X size={19}/>:<Menu size={19}/>}</button>
      </div>
    </header>

    {mobile && <div className="mobile-nav"><a>Live</a><a>Scores</a><a>Statistics</a><a>Odds</a></div>}

    <main>
      <section className="hero">
        <div><Badge>● LIVE DATA CENTER</Badge><h1>Every game.<br/><span>Every moment.</span></h1><p>Live scores, statistics, schedules and market data across the world's biggest sports.</p></div>
        <div className="hero-card"><Activity size={22}/><div><strong>LIVE UPDATES</strong><small>Interface ready for real-time API streaming</small></div><span className="pulse"></span></div>
      </section>

      <div className="sport-strip">{sports.map(s=><button key={s} className={selected===s?"selected":""} onClick={()=>setSelected(s)}><SportIcon name={s}/>{s}</button>)}</div>

      <section className="content-grid">
        <div className="main-col">
          <div className="section-head"><div><h2><span className="live-dot"></span> Live Now</h2><p>{filteredLive.length} games currently displayed</p></div><button className="view-btn">View all <ChevronRight size={16}/></button></div>
          <div className="cards">
            {filteredLive.length===0 && <div className="empty">No matching games in this sport.</div>}
            {filteredLive.map(g=><article className="game-card" key={g.id}>
              <div className="game-top"><span>{g.league}</span><span className="live-label">● {g.status}</span></div>
              <div className="teams"><div><b>{g.home}</b><small>{g.sport}</small></div><div className="score"><strong>{g.hs}</strong><strong>{g.as}</strong></div></div>
              <div className="teams secondary"><div><span>vs</span></div><div className="game-time">{g.period} · {g.clock}</div></div>
              <div className="card-footer"><button><Star size={15}/> Follow</button><button>Game Center <ChevronRight size={14}/></button></div>
            </article>)}
          </div>

          <div className="section-head upcoming-head"><div><h2>Upcoming</h2><p>Next events on the schedule</p></div><button className="view-btn">Calendar <ChevronRight size={16}/></button></div>
          <div className="upcoming-list">{upcoming.map((g,i)=><div className="upcoming" key={i}><div className="mini-sport">{g.sport.slice(0,2).toUpperCase()}</div><div className="up-teams"><strong>{g.home}</strong><span>vs</span><strong>{g.away}</strong><small>{g.league}</small></div><div className="up-time"><Clock3 size={15}/>{g.time}</div><button className="chev"><ChevronRight size={17}/></button></div>)}</div>
        </div>

        <aside>
          <div className="side-head"><h2><TrendingUp size={18}/> Market Watch</h2><span>Sample data</span></div>
          <div className="odds-list">{odds.map((o,i)=><div className="odd" key={i}><small>{o.game}</small><b>{o.market}</b><div><span>{o.a}</span><span>{o.b}</span></div></div>)}</div>
          <div className="side-card"><Flame size={19}/><div><strong>Trending</strong><p>Games with the most activity</p></div><ChevronRight size={16}/></div>
          <div className="side-card"><Trophy size={19}/><div><strong>Top Leagues</strong><p>NBA · Premier League · ATP · MLB</p></div><ChevronRight size={16}/></div>
          <div className="notice"><strong>Ready for live API</strong><p>Replace the sample data layer with your licensed sports-data provider to stream genuine live scores and odds.</p></div>
        </aside>
      </section>
    </main>
    <footer><span>© {new Date().getFullYear()} IMGOFFICIAL</span><span>Live Sports Data Platform</span></footer>
  </div>
}
createRoot(document.getElementById("root")).render(<App/>);