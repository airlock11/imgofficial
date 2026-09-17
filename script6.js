
/* IMG automatic sports news feed with source-provided article images. */
(function(){
  const NEWS_API='https://img-api-proxy.magsipocarnie.workers.dev/news';
  const feature=document.getElementById('img-feature-news');
  const list=document.getElementById('img-news-list');
  const status=document.getElementById('img-news-status');
  if(!feature||!list||!status)return;
  function esc(v){return String(v||'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
  function safeImage(v){try{const u=new URL(String(v||''));return u.protocol==='https:'?u.href:'';}catch{return '';}}
  function timeLabel(v){const d=new Date(v);if(Number.isNaN(d.getTime()))return '';return d.toLocaleString(undefined,{month:'short',day:'numeric',year:'numeric'});}
  function render(items){
    if(!items.length){
      feature.classList.remove('has-image');
      feature.innerHTML='<div class="feature-news-content"><div class="news-tag">IMG SPORTS NEWS</div><h4>No current stories available.</h4><p>The news source did not return new stories right now.</p></div>';
      list.innerHTML='';status.textContent='';return;
    }
    const first=items[0], firstImage=safeImage(first.image);
    feature.classList.toggle('has-image',!!firstImage);
    feature.innerHTML=(firstImage?'<img class="feature-news-image" src="'+esc(firstImage)+'" alt="" loading="eager" referrerpolicy="no-referrer">':'')+
      '<div class="feature-news-content"><div class="news-tag">'+esc(first.region==='Philippines'?'PH · '+(first.sport||'SPORTS'):(first.sport||'SPORTS'))+'</div><a href="'+esc(first.link)+'" target="_blank" rel="noopener noreferrer"><h4>'+esc(first.title)+'</h4></a><p>'+esc(first.description||'Read the full story at the original source.')+'</p><div class="news-meta">'+esc(first.source||'Source')+' · '+esc(timeLabel(first.published))+'</div></div>';
    list.innerHTML=items.slice(1,6).map(item=>{
      const image=safeImage(item.image);
      return '<div class="news-item"><div class="news-thumb">'+(image?'<img src="'+esc(image)+'" alt="" loading="lazy" referrerpolicy="no-referrer">':'<span aria-hidden="true"></span>')+'</div><div><div class="news-tag">'+esc(item.region==='Philippines'?'PH · '+(item.sport||'SPORTS'):(item.sport||'SPORTS'))+'</div><a href="'+esc(item.link)+'" target="_blank" rel="noopener noreferrer"><h4>'+esc(item.title)+'</h4></a><p>'+esc(item.description||'Read the full story at the original source.')+'</p><div class="news-source">'+esc(item.source||'Source')+' · '+esc(timeLabel(item.published))+'</div></div></div>';
    }).join('');
    status.textContent='';
  }
  async function loadNews(){
    try{const r=await fetch(NEWS_API,{cache:'no-store'});if(!r.ok)throw new Error('News request failed');const data=await r.json();render(Array.isArray(data.items)?data.items:[]);}
    catch(e){status.textContent='News feed temporarily unavailable. IMG will try again automatically.';}
  }
  loadNews();setInterval(loadNews,15*60*1000);
})();
