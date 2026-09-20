(()=>{
const API='https://img-api-proxy.magsipocarnie.workers.dev';
const divisionEl=document.getElementById('boxingDivision');
const bodyEl=document.getElementById('boxingBody');
const searchEl=document.getElementById('boxingSearch');
const content=document.getElementById('boxingContent');
const statusEl=document.getElementById('boxingStatus');
const sourcesEl=document.getElementById('boxingSources');
const pager=document.getElementById('boxingPager');
const prev=document.getElementById('boxingPrev');
const next=document.getElementById('boxingNext');
const pageLabel=document.getElementById('boxingPageLabel');
const dialog=document.getElementById('boxerDialog');
const dialogContent=document.getElementById('boxerDialogContent');

let meta={divisions:[],api_divisions:[],organizations:[],sources:[],configured:false};
let local={fighters:[],divisions:[],updated_at:null,total_fighters:0,refresh_hours:12};
let view='fighters',page=1,totalPages=1,searchTimer;

const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const n=v=>Number.isFinite(Number(v))?Number(v):0;
const boxerId=x=>x?.fighter_id||x?.id||'';
const boxerName=x=>x?.fighter_name||x?.name||x?.full_name||'Vacant';
const orgName=x=>x?.organization?.name||x?.organization_name||x?.org?.name||x?.name||'Organization';
const orgCode=name=>{const m=String(name||'').toUpperCase().match(/\b(WBC|WBA|IBF|WBO)\b/);return m?m[1]:String(name||'').toUpperCase()};

function setStatus(t){statusEl.textContent=t||''}

function officialSources(){
  const blocks=[];
  if(view==='fighters'){
    const updated=local.updated_at?new Date(local.updated_at):null;
    const when=updated&&!Number.isNaN(updated.getTime())?updated.toLocaleString():'waiting for first update';
    blocks.push('<div class="boxing-feed-note">Boxer records are loaded from the GitHub data cache generated from Boxing Data API. '+esc(local.total_fighters||local.fighters.length)+' fighters in cache · Updated '+esc(when)+'.</div>');
  }
  if(meta.sources?.length){
    blocks.push('<div class="boxing-feed-note">Official ranking references</div><div class="official-boxing-sources">'+meta.sources.map(s=>'<a class="official-boxing-source" href="'+esc(s.url)+'" target="_blank" rel="noopener noreferrer"><strong>'+esc(s.body)+'</strong><span>'+esc(s.label)+'</span></a>').join('')+'</div>');
  }
  sourcesEl.innerHTML=blocks.join('');
}

function selectedDivision(){
  return meta.divisions.find(d=>String(d.page)===divisionEl.value)||meta.divisions[0];
}

function apiDivisionId(){
  const d=selectedDivision();
  const m=(meta.api_divisions||[]).find(x=>String(x.name||'').toLowerCase()===String(d?.name||'').toLowerCase());
  return m?.id||'';
}

async function get(path,params={}){
  const q=new URLSearchParams(params);
  const r=await fetch(API+path+(q.toString()?'?'+q:''),{cache:'no-store'});
  if(!r.ok)throw new Error('HTTP '+r.status);
  return r.json();
}

async function loadBoxingCache(bust=false){
  const r=await fetch('boxing-data.json'+(bust?'?v='+Date.now():''),{cache:'no-store'});
  if(!r.ok)throw new Error('Boxing cache unavailable');
  const j=await r.json();
  local={
    fighters:Array.isArray(j.fighters)?j.fighters:[],
    divisions:Array.isArray(j.divisions)?j.divisions:[],
    updated_at:j.updated_at||null,
    total_fighters:Number(j.total_fighters)||0,
    refresh_hours:Number(j.refresh_hours)||12
  };
  return local;
}

function populateDivisionControl(){
  if(view==='fighters'){
    const current=divisionEl.value;
    divisionEl.innerHTML='<option value="">All divisions</option>'+local.divisions.map(d=>'<option value="'+esc(d.id||d.name||'')+'">'+esc(d.name||'Division')+'</option>').join('');
    if([...divisionEl.options].some(o=>o.value===current))divisionEl.value=current;
  }else{
    const current=divisionEl.value;
    divisionEl.innerHTML=(meta.divisions||[]).map(d=>'<option value="'+esc(d.page)+'">'+esc(d.name)+'</option>').join('');
    if([...divisionEl.options].some(o=>o.value===current))divisionEl.value=current;
  }
  bodyEl.disabled=view!=='rankings';
  searchEl.disabled=view!=='fighters';
}

function record(f){
  const s=f?.stats||{};
  return [n(s.wins),n(s.losses),n(s.draws)].join('-');
}

function renderBoxerCard(f){
  const s=f?.stats||{};
  return '<button class="boxer-card" type="button" data-boxer-id="'+esc(boxerId(f))+'">'+
    '<div><h3>'+esc(boxerName(f))+'</h3>'+(f.nickname?'<div class="tag">“'+esc(f.nickname)+'”</div>':'')+'</div>'+
    '<div class="record">'+record(f)+'</div>'+
    '<div class="boxer-meta">'+[
      f.division?.name,
      f.nationality,
      f.stance,
      s.ko_wins!=null?s.ko_wins+' KO wins':''
    ].filter(Boolean).map(x=>'<span>'+esc(x)+'</span>').join('')+'</div>'+
  '</button>';
}

function filteredLocalFighters(){
  const q=searchEl.value.trim().toLowerCase();
  const division=divisionEl.value;
  return local.fighters.filter(f=>{
    if(division&&String(f?.division?.id||f?.division?.name||'')!==division)return false;
    if(!q)return true;
    return [
      f.name,f.nickname,f.alias,f.nationality,f.nationality_code,
      f.division?.name,f.stance
    ].filter(Boolean).join(' ').toLowerCase().includes(q);
  });
}

function renderLocalFighters(){
  const fighters=filteredLocalFighters();
  const pageSize=24;
  totalPages=Math.max(1,Math.ceil(fighters.length/pageSize));
  page=Math.min(Math.max(1,page),totalPages);
  const start=(page-1)*pageSize;
  const shown=fighters.slice(start,start+pageSize);
  content.innerHTML=shown.length?'<div class="boxer-grid">'+shown.map(renderBoxerCard).join('')+'</div>':'<div class="empty">No boxers found.</div>';
  updatePager({page,total_pages:totalPages});
  const first=fighters.length?start+1:0,last=Math.min(start+pageSize,fighters.length);
  const updated=local.updated_at?new Date(local.updated_at):null;
  const updatedText=updated&&!Number.isNaN(updated.getTime())?' · Data '+updated.toLocaleDateString():'';
  setStatus((fighters.length?('Showing '+first+'–'+last+' of '+fighters.length+' boxers'):'No matching boxers')+updatedText);
  officialSources();
}

function renderSourcesOnly(){
  content.innerHTML='<div class="boxing-feed-note">Official ranking sources are connected below. The boxer directory is stored separately in GitHub and remains available under the Boxers tab.</div>';
  pager.hidden=true;
  officialSources();
}

function renderRankings(data){
  const selected=bodyEl.value;
  const items=(data.data||[]).filter(x=>!selected||orgCode(orgName(x))===selected);
  content.innerHTML=items.length?'<div class="boxing-rankings">'+items.map(g=>{
    const org=orgCode(orgName(g)),ch=g.champions||[],rs=g.rankings||[];
    return '<section class="boxing-body"><div class="boxing-body-head"><strong>'+esc(org)+'</strong><span>'+esc(g.updated_at||'')+'</span></div>'+
      (ch.length?'<div class="boxing-champions">'+ch.map(c=>'<div class="boxing-champion"><b>'+esc(c.title_type||'Champion')+'</b><button class="boxer-link" type="button" data-boxer-id="'+esc(boxerId(c))+'">'+esc(boxerName(c))+'</button></div>').join('')+'</div>':'')+
      '<table class="boxing-table"><thead><tr><th>Rank</th><th>Boxer</th><th>Country</th><th>Status</th></tr></thead><tbody>'+
      rs.map(r=>'<tr><td>'+esc(r.rank??'—')+'</td><td>'+(r.is_vacant?'Vacant':'<button class="boxer-link" type="button" data-boxer-id="'+esc(boxerId(r))+'">'+esc(boxerName(r))+'</button>')+'</td><td>'+esc(r.nationality||r.country||'—')+'</td><td>'+esc(r.title_type||r.status||'')+'</td></tr>').join('')+
      '</tbody></table></section>';
  }).join('')+'</div>':'<div class="empty">No ranking data returned for this division.</div>';
  pager.hidden=true;
  setStatus('');
  officialSources();
}

function fightNames(f){
  const a=f?.fighters?.fighter_1||{},b=f?.fighters?.fighter_2||{};
  return[a.full_name||a.name||'Fighter A',b.full_name||b.name||'Fighter B'];
}

function renderFights(data){
  const fights=Array.isArray(data.data)?data.data:[];
  content.innerHTML=fights.length?'<div class="fight-grid">'+fights.map(f=>{
    const[a,b]=fightNames(f),res=f.results||{};
    return '<article class="fight-card"><div class="fight-date">'+esc(f.date?new Date(f.date).toLocaleDateString():f.status||'')+'</div><h3>'+esc(a)+' vs '+esc(b)+'</h3><div class="boxer-meta">'+[f.status,f.division?.name,f.location].filter(Boolean).map(x=>'<span>'+esc(typeof x==='string'?x:(x.name||''))+'</span>').join('')+'</div>'+(res.outcome?'<div class="fight-result">'+esc(res.outcome_long||res.outcome)+(res.round?' · Round '+esc(res.round):'')+'</div>':'')+'</article>';
  }).join('')+'</div>':'<div class="empty">No fights returned.</div>';
  updatePager(data.pagination);
  setStatus('');
  officialSources();
}

function updatePager(p={}){
  page=Number(p.page||page||1);
  totalPages=Math.max(1,Number(p.total_pages||1));
  pager.hidden=totalPages<=1;
  pageLabel.textContent='Page '+page+' of '+totalPages;
  prev.disabled=page<=1;
  next.disabled=page>=totalPages;
}

async function load(){
  content.innerHTML='<div class="empty">Loading boxing data…</div>';
  setStatus('Loading');

  try{
    if(view==='fighters'){
      if(!local.fighters.length){
        try{await loadBoxingCache(true);populateDivisionControl()}catch{}
      }
      if(local.fighters.length){
        renderLocalFighters();
        return;
      }
      if(meta.configured){
        const p={page_num:page,page_size:24},q=searchEl.value.trim(),d=apiDivisionId();
        if(q)p.name=q;
        if(d)p.division_id=d;
        const data=await get('/boxing/fighters',p);
        const fighters=Array.isArray(data.data)?data.data:[];
        content.innerHTML=fighters.length?'<div class="boxer-grid">'+fighters.map(renderBoxerCard).join('')+'</div>':'<div class="empty">No boxers found.</div>';
        updatePager(data.pagination);
        setStatus('');
        officialSources();
        return;
      }
      content.innerHTML='<div class="empty">The boxer directory is waiting for its first GitHub data update.</div>';
      pager.hidden=true;
      setStatus('Waiting for boxing-data.json');
      officialSources();
      return;
    }

    if(!meta.configured){
      renderSourcesOnly();
      setStatus('');
      return;
    }

    if(view==='rankings'){
      renderRankings(await get('/boxing/rankings',{page_num:selectedDivision()?.page||1}));
    }else{
      const p={page_num:page,page_size:24,date_sort:'DESC'},d=apiDivisionId();
      if(d)p.division_id=d;
      renderFights(await get('/boxing/fights',p));
    }
  }catch(e){
    content.innerHTML='<div class="empty">Boxing data is temporarily unavailable.</div>';
    pager.hidden=true;
    setStatus('Feed unavailable');
    officialSources();
  }
}

function renderBoxerDialog(f){
  const s=f?.stats||{};
  dialogContent.innerHTML=
    '<h2>'+esc(boxerName(f))+'</h2>'+
    (f.nickname?'<div class="tag">“'+esc(f.nickname)+'”</div>':'')+
    '<div class="boxer-record-row">'+
      '<div class="boxer-stat"><b>'+n(s.wins)+'</b><span>Wins</span></div>'+
      '<div class="boxer-stat"><b>'+n(s.losses)+'</b><span>Losses</span></div>'+
      '<div class="boxer-stat"><b>'+n(s.draws)+'</b><span>Draws</span></div>'+
      '<div class="boxer-stat"><b>'+n(s.ko_wins)+'</b><span>KO wins</span></div>'+
    '</div>'+
    '<div class="boxer-detail-grid">'+[
      ['Division',f.division?.name],
      ['Nationality',f.nationality],
      ['Stance',f.stance],
      ['Age',f.age],
      ['Height',f.height||f.height_ft||(f.height_cm?f.height_cm+' cm':null)],
      ['Reach',f.reach||(f.reach_cm?f.reach_cm+' cm':null)],
      ['Pro debut',f.debut],
      ['Total bouts',s.total_bouts]
    ].map(([k,v])=>'<div><small>'+k+'</small>'+esc(v??'—')+'</div>').join('')+'</div>'+
    (Array.isArray(f.titles)&&f.titles.length?'<div class="boxer-titles">'+f.titles.map(t=>'<span class="boxer-title">'+esc(t.name||t.title||'Title')+'</span>').join('')+'</div>':'');
}

async function openBoxer(id){
  if(!id)return;
  const localFighter=local.fighters.find(f=>String(boxerId(f))===String(id));
  dialogContent.innerHTML='<div class="empty">Loading boxer…</div>';
  dialog.showModal();
  if(localFighter){
    renderBoxerDialog(localFighter);
    return;
  }
  if(!meta.configured){
    dialogContent.innerHTML='<div class="empty">Boxer profile unavailable.</div>';
    return;
  }
  try{
    const j=await get('/boxing/fighter',{id});
    renderBoxerDialog(j.data||{});
  }catch{
    dialogContent.innerHTML='<div class="empty">Boxer profile unavailable.</div>';
  }
}

async function init(){
  const [cacheResult,metaResult]=await Promise.allSettled([
    loadBoxingCache(),
    get('/boxing/meta')
  ]);

  if(metaResult.status==='fulfilled')meta=metaResult.value||meta;
  if(cacheResult.status!=='fulfilled')setStatus('Waiting for boxer directory update');

  document.querySelectorAll('[data-boxing-view]').forEach(btn=>{
    btn.classList.toggle('active',btn.dataset.boxingView===view);
  });
  populateDivisionControl();
  officialSources();
  await load();
}

document.querySelectorAll('[data-boxing-view]').forEach(btn=>btn.addEventListener('click',()=>{
  document.querySelectorAll('[data-boxing-view]').forEach(x=>x.classList.toggle('active',x===btn));
  view=btn.dataset.boxingView;
  page=1;
  searchEl.value=view==='fighters'?searchEl.value:'';
  populateDivisionControl();
  load();
}));

divisionEl.addEventListener('change',()=>{page=1;load()});
bodyEl.addEventListener('change',load);

document.getElementById('boxingRefresh').addEventListener('click',async()=>{
  if(view==='fighters'){
    setStatus('Refreshing');
    try{
      await loadBoxingCache(true);
      page=1;
      populateDivisionControl();
    }catch{}
  }
  load();
});

searchEl.addEventListener('input',()=>{
  clearTimeout(searchTimer);
  if(view==='fighters'){
    page=1;
    searchTimer=setTimeout(load,250);
  }
});

prev.addEventListener('click',()=>{if(page>1){page--;load()}});
next.addEventListener('click',()=>{if(page<totalPages){page++;load()}});

document.addEventListener('click',e=>{
  const b=e.target.closest('[data-boxer-id]');
  if(b)openBoxer(b.dataset.boxerId);
});

dialog.querySelector('.boxer-dialog-close').addEventListener('click',()=>dialog.close());
dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close()});

init();
})();