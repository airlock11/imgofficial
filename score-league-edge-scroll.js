(()=>{
  const filters=document.getElementById('scoreLeagueFilters');
  const leftZone=document.querySelector('.score-league-edge-zone-left');
  const rightZone=document.querySelector('.score-league-edge-zone-right');
  if(!filters||!leftZone||!rightZone||window.innerWidth<=760)return;

  const DELAY=1000;
  const SPEED=420;
  let dir=0;
  let timer=0;
  let frame=0;
  let active=false;
  let last=0;
  let rampStart=0;
  let visibilityFrame=0;

  const maxScroll=()=>Math.max(0,filters.scrollWidth-filters.clientWidth);
  const canScroll=d=>d<0?filters.scrollLeft>1:filters.scrollLeft<maxScroll()-1;

  const updateEdgeVisibility=()=>{
    const max=maxScroll();
    const atLeft=max<=1||filters.scrollLeft<=1;
    const atRight=max<=1||filters.scrollLeft>=max-1;
    leftZone.classList.toggle('is-edge-hidden',atLeft);
    rightZone.classList.toggle('is-edge-hidden',atRight);
    leftZone.setAttribute('aria-hidden',atLeft?'true':'false');
    rightZone.setAttribute('aria-hidden',atRight?'true':'false');
  };

  const queueVisibilityUpdate=()=>{
    if(visibilityFrame)return;
    visibilityFrame=requestAnimationFrame(()=>{
      visibilityFrame=0;
      updateEdgeVisibility();
    });
  };

  const clear=()=>{
    if(timer){clearTimeout(timer);timer=0}
    if(frame){cancelAnimationFrame(frame);frame=0}
    active=false;
    dir=0;
    last=0;
    rampStart=0;
    filters.classList.remove('edge-scroll-left','edge-scroll-right');
    queueVisibilityUpdate();
  };

  const step=now=>{
    if(!active||!dir||!canScroll(dir)){clear();return}
    if(!last)last=now;
    const dt=Math.min(32,now-last)/1000;
    last=now;
    const ramp=Math.min(1,(now-rampStart)/400);
    const eased=1-Math.pow(1-ramp,3);
    filters.scrollLeft+=dir*SPEED*eased*dt;
    queueVisibilityUpdate();
    frame=requestAnimationFrame(step);
  };

  const arm=d=>{
    clear();
    if(!canScroll(d)){updateEdgeVisibility();return}
    dir=d;
    filters.classList.add(d<0?'edge-scroll-left':'edge-scroll-right');
    timer=setTimeout(()=>{
      timer=0;
      if(!dir||!canScroll(dir)){clear();return}
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
  filters.addEventListener('scroll',queueVisibilityUpdate,{passive:true});
  window.addEventListener('blur',clear);
  window.addEventListener('resize',()=>{clear();queueVisibilityUpdate()},{passive:true});

  if('ResizeObserver'in window){
    new ResizeObserver(queueVisibilityUpdate).observe(filters);
  }
  if('MutationObserver'in window){
    new MutationObserver(queueVisibilityUpdate).observe(filters,{childList:true,subtree:true});
  }

  updateEdgeVisibility();
})();
