(()=>{
  const filters=document.getElementById('scoreLeagueFilters');
  const leftZone=document.querySelector('.score-league-edge-zone-left');
  const rightZone=document.querySelector('.score-league-edge-zone-right');
  if(!filters||!leftZone||!rightZone||!window.matchMedia('(hover:hover) and (pointer:fine)').matches)return;

  const DELAY=1000;
  const SPEED=420;
  let dir=0;
  let timer=0;
  let frame=0;
  let active=false;
  let last=0;
  let rampStart=0;

  const canScroll=d=>{
    const max=Math.max(0,filters.scrollWidth-filters.clientWidth);
    return d<0?filters.scrollLeft>1:filters.scrollLeft<max-1;
  };

  const clear=()=>{
    if(timer){clearTimeout(timer);timer=0}
    if(frame){cancelAnimationFrame(frame);frame=0}
    active=false;
    dir=0;
    last=0;
    rampStart=0;
    filters.classList.remove('edge-scroll-left','edge-scroll-right');
  };

  const step=now=>{
    if(!active||!dir||!canScroll(dir)){clear();return}
    if(!last)last=now;
    const dt=Math.min(32,now-last)/1000;
    last=now;
    const ramp=Math.min(1,(now-rampStart)/400);
    const eased=1-Math.pow(1-ramp,3);
    filters.scrollLeft+=dir*SPEED*eased*dt;
    frame=requestAnimationFrame(step);
  };

  const arm=d=>{
    clear();
    if(!canScroll(d))return;
    dir=d;
    filters.classList.add(d<0?'edge-scroll-left':'edge-scroll-right');
    timer=setTimeout(()=>{
      timer=0;
      if(!dir||!canScroll(dir))return;
      active=true;
      rampStart=performance.now();
      frame=requestAnimationFrame(step);
    },DELAY);
  };

  leftZone.addEventListener('pointerenter',()=>arm(-1));
  rightZone.addEventListener('pointerenter',()=>arm(1));
  leftZone.addEventListener('pointerleave',clear);
  rightZone.addEventListener('pointerleave',clear);
  leftZone.addEventListener('pointerdown',clear);
  rightZone.addEventListener('pointerdown',clear);
  window.addEventListener('blur',clear);
  window.addEventListener('resize',clear,{passive:true});
})();
