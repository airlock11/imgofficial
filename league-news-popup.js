(()=>{
const API="https://img-api-proxy.magsipocarnie.workers.dev/article-preview";
let modal=null,titleEl=null,metaEl=null,imageEl=null,loader=null,bodyEl=null,sourceLink=null,lastTrigger=null,requestToken=0;

function ensureModal(){
  if(modal)return modal;
  modal=document.createElement("div");
  modal.className="img-news-modal";
  modal.setAttribute("aria-hidden","true");
  modal.innerHTML=
    '<div class="img-news-modal__backdrop" data-news-close></div>'+
    '<section class="img-news-modal__panel" role="dialog" aria-modal="true" aria-labelledby="imgNewsModalTitle">'+
      '<header class="img-news-modal__header">'+
        '<div class="img-news-modal__heading">'+
          '<span class="img-news-modal__eyebrow">IMG NEWS</span>'+
          '<h2 id="imgNewsModalTitle"></h2>'+
          '<div class="img-news-modal__meta"></div>'+
        '</div>'+
        '<button class="img-news-modal__close" type="button" aria-label="Close article" data-news-close>×</button>'+
      '</header>'+
      '<div class="img-news-modal__hero" hidden><img alt=""></div>'+
      '<div class="img-news-modal__viewer">'+
        '<div class="img-news-modal__loader">Loading article preview…</div>'+
        '<div class="img-news-modal__body" hidden>'+
          '<p class="img-news-modal__description"></p>'+
          '<div class="img-news-modal__notice">This preview is fetched only when you open the article.</div>'+
          '<a class="img-news-modal__source" href="">Read full source <span>›</span></a>'+
        '</div>'+
      '</div>'+
    '</section>';
  document.body.appendChild(modal);
  titleEl=modal.querySelector("#imgNewsModalTitle");
  metaEl=modal.querySelector(".img-news-modal__meta");
  imageEl=modal.querySelector(".img-news-modal__hero img");
  loader=modal.querySelector(".img-news-modal__loader");
  bodyEl=modal.querySelector(".img-news-modal__body");
  sourceLink=modal.querySelector(".img-news-modal__source");

  modal.addEventListener("click",e=>{
    if(e.target.closest("[data-news-close]"))closeModal();
  });
  document.addEventListener("keydown",e=>{
    if(e.key==="Escape"&&modal?.classList.contains("is-open"))closeModal();
  });
  return modal;
}

function cardDetails(card){
  const title=(card.querySelector("strong")?.textContent||card.getAttribute("aria-label")||"News article").trim();
  const meta=(card.querySelector("small")?.textContent||"").trim();
  const img=card.querySelector("img");
  return {title,meta,image:img?.currentSrc||img?.src||""};
}

function setHero(src,title){
  const hero=modal.querySelector(".img-news-modal__hero");
  if(src){
    imageEl.src=src;
    imageEl.alt=title||"Article image";
    hero.hidden=false;
  }else{
    imageEl.removeAttribute("src");
    imageEl.alt="";
    hero.hidden=true;
  }
}

function cleanDate(value){
  if(!value)return "";
  const d=new Date(value);
  return Number.isNaN(d.getTime())?"":d.toLocaleDateString(undefined,{month:"short",day:"numeric",year:"numeric"});
}

function publisherName(url){
  try{
    return new URL(url).hostname.replace(/^www\./,"");
  }catch{return "Source"}
}

async function openModal(card){
  const href=card.href||card.getAttribute("href");
  if(!href)return;
  ensureModal();
  const token=++requestToken;
  const d=cardDetails(card);
  lastTrigger=card;

  titleEl.textContent=d.title;
  metaEl.textContent=d.meta;
  setHero(d.image,d.title);
  loader.hidden=false;
  loader.textContent="Loading article preview…";
  bodyEl.hidden=true;
  bodyEl.querySelector(".img-news-modal__description").textContent="";
  sourceLink.href=href;
  sourceLink.removeAttribute("target");
  sourceLink.setAttribute("rel","noopener");

  modal.classList.add("is-open");
  modal.setAttribute("aria-hidden","false");
  document.documentElement.classList.add("img-news-modal-open");
  modal.querySelector(".img-news-modal__close")?.focus();

  try{
    const endpoint=API+"?url="+encodeURIComponent(href)+"&ts="+Date.now();
    const response=await fetch(endpoint,{cache:"no-store"});
    const data=await response.json().catch(()=>({}));
    if(token!==requestToken)return;
    if(!response.ok||!data?.ok)throw new Error(data?.error||"Article preview unavailable");

    const title=String(data.title||d.title||"News article").trim();
    const sourceUrl=String(data.sourceUrl||href);
    const date=cleanDate(data.published);
    const author=String(data.author||"").trim();
    const source=publisherName(sourceUrl);

    titleEl.textContent=title;
    metaEl.textContent=[author,source,date].filter(Boolean).join(" · ")||d.meta;
    setHero(data.image||d.image,title);

    const description=String(data.description||"").trim();
    bodyEl.querySelector(".img-news-modal__description").textContent=
      description||"A preview is not available for this article. You can continue to the original publisher.";
    sourceLink.href=sourceUrl;
    sourceLink.textContent="Read full source ›";
    loader.hidden=true;
    bodyEl.hidden=false;
  }catch(error){
    if(token!==requestToken)return;
    loader.hidden=true;
    bodyEl.hidden=false;
    bodyEl.querySelector(".img-news-modal__description").textContent=
      "IMG could not load this publisher’s preview right now. You can still open the original article.";
    sourceLink.href=href;
    sourceLink.textContent="Read full source ›";
  }
}

function closeModal(){
  if(!modal)return;
  requestToken++;
  modal.classList.remove("is-open");
  modal.setAttribute("aria-hidden","true");
  document.documentElement.classList.remove("img-news-modal-open");
  if(loader){
    loader.hidden=false;
    loader.textContent="Loading article preview…";
  }
  if(bodyEl)bodyEl.hidden=true;
  if(lastTrigger&&document.contains(lastTrigger))lastTrigger.focus({preventScroll:true});
}

document.addEventListener("click",e=>{
  const card=e.target.closest("a.news-card[href]");
  if(!card)return;
  e.preventDefault();
  e.stopPropagation();
  openModal(card);
},true);
})();