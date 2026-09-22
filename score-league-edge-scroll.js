(()=>{
  const filters=document.getElementById('scoreLeagueFilters');
  if(!filters||!window.matchMedia('(hover:hover) and (pointer:fine)').matches)return;

  const EDGE=96;
  const DELAY=1000;
  const MAX_SPEED=520; // px/second at the outermost edge
  let direction=0;
  let edgeStrength=0;
  let hoverTimer=0;
  let scrolling=false;
  let frame=0;
  let lastTime=0;
  let rampStarted=0;

  const canScroll=dir=>{
    const max=Math.max(0,filters.scrollWidth-filters.clientWidth);
    return dir<0?filters.scrollLeft>1:filters.scrollLeft<max-1;
  };

  const stop=()=>{
    if(hoverTimer){clearTimeout(hoverTimer);hoverTimer=0}
    direction=0;
    edgeStrength=0;
    scrolling=false;
    rampStarted=0;
    lastTime=0;
    if(frame){cancelAnimationFrame(frame);frame=0}
    filters.classList.remove('edge-scroll-left','edge-scroll-right');
  };

  const tick=now=>{
    if(!scrolling||!direction||!canScroll(direction)){stop();return}
    if(!lastTime)lastTime=now;
    const dt=Math.min(32,now-lastTime)/1000;
    lastTime=now;

    // Ease in over ~350ms so movement starts gently after the one-second hold.
    const ramp=Math.min(1,(now-rampStarted)/350);
    const easedRamp=1-Math.pow(1-ramp,3);
    const easedEdge=edgeStrength*edgeStrength;
    filters.scrollLeft+=direction*MAX_SPEED*easedEdge*easedRamp*dt;
    frame=requestAnimationFrame(tick);
  };

  const begin=dir=>{
    if(scrolling||hoverTimer||!canScroll(dir))return;
    hoverTimer=setTimeout(()=>{
      hoverTimer=0;
      if(direction!==dir||!canScroll(dir))return;
      scrolling=true;
      rampStarted=performance.now();
      lastTime=0;
      frame=requestAnimationFrame(tick);
    },DELAY);
  };

  const setEdge=(dir,strength)=>{
    strength=Math.max(0,Math.min(1,strength));
    if(dir===direction){
      edgeStrength=strength;
      if(dir&&!scrolling)begin(dir);
      return;
    }
    if(hoverTimer){clearTimeout(hoverTimer);hoverTimer=0}
    if(frame){cancelAnimationFrame(frame);frame=0}
    scrolling=false;
    rampStarted=0;
    lastTime=0;
    direction=dir;
    edgeStrength=strength;
    filters.classList.toggle('edge-scroll-left',dir<0);
    filters.classList.toggle('edge-scroll-right',dir>0);
    if(dir)begin(dir);
  };

  filters.addEventListener('pointermove',event=>{
    const rect=filters.getBoundingClientRect();
    if(rect.width<=EDGE*2||filters.scrollWidth<=filters.clientWidth+1){stop();return}
    const x=event.clientX-rect.left;
    if(x<EDGE){
      setEdge(-1,(EDGE-x)/EDGE);
    }else if(x>rect.width-EDGE){
      setEdge(1,(x-(rect.width-EDGE))/EDGE);
    }else{
      setEdge(0,0);
    }
  },{passive:true});

  filters.addEventListener('pointerleave',stop,{passive:true});
  filters.addEventListener('pointerdown',stop,{passive:true});
  window.addEventListener('blur',stop);
  window.addEventListener('resize',stop,{passive:true});
})();
