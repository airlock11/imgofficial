(()=>{
let modal=null,frame=null,titleEl=null,metaEl=null,imageEl=null,loader=null,lastTrigger=null;

function ensureModal(){
  if(modal)return modal;
  modal=document.createElement("div");
  modal.className="img-news-modal";
  modal.setAttribute("aria-hidden","true");
  modal.innerHTML=`
    <div class="img-news-modal__backdrop" data-news-close></div>
    <section class="img-news-modal__panel" role="dialog" aria-modal="true" aria-labelledby="imgNewsModalTitle">
      <header class="img-news-modal__header">
        <div class="img-news-modal__heading">
          <span class="img-news-modal__eyebrow">IMG NEWS</span>
          <h2 id="imgNewsModalTitle"></h2>
          <div class="img-news-modal__meta"></div>
        </div>
        <button class="img-news-modal__close" type="button" aria-label="Close article" data-news-close>×</button>
      </header>
      <div class="img-news-modal__hero" hidden><img alt=""></div>
      <div class="img-news-modal__viewer">
        <div class="img-news-modal__loader">Loading article…</div>
        <iframe class="img-news-modal__frame" title="News article" referrerpolicy="strict-origin-when-cross-origin" allow="fullscreen"></iframe>
      </div>
    </section>`;
  document.body.appendChild(modal);
  frame=modal.querySelector(".img-news-modal__frame");
  titleEl=modal.querySelector("#imgNewsModalTitle");
  metaEl=modal.querySelector(".img-news-modal__meta");
  imageEl=modal.querySelector(".img-news-modal__hero img");
  loader=modal.querySelector(".img-news-modal__loader");

  modal.addEventListener("click",e=>{
    if(e.target.closest("[data-news-close]"))closeModal();
  });
  document.addEventListener("keydown",e=>{
    if(e.key==="Escape"&&modal?.classList.contains("is-open"))closeModal();
  });
  frame.addEventListener("load",()=>{
    if(loader)loader.hidden=true;
  });
  return modal;
}

function cardDetails(card){
  const title=(card.querySelector("strong")?.textContent||card.getAttribute("aria-label")||"News article").trim();
  const meta=(card.querySelector("small")?.textContent||"").trim();
  const img=card.querySelector("img");
  return {title,meta,image:img?.currentSrc||img?.src||""};
}

function openModal(card){
  const href=card.href||card.getAttribute("href");
  if(!href)return;
  ensureModal();
  const d=cardDetails(card);
  lastTrigger=card;
  titleEl.textContent=d.title;
  metaEl.textContent=d.meta;
  const hero=modal.querySelector(".img-news-modal__hero");
  if(d.image){
    imageEl.src=d.image;
    imageEl.alt=d.title;
    hero.hidden=false;
  }else{
    imageEl.removeAttribute("src");
    imageEl.alt="";
    hero.hidden=true;
  }
  loader.hidden=false;
  frame.src=href;
  modal.classList.add("is-open");
  modal.setAttribute("aria-hidden","false");
  document.documentElement.classList.add("img-news-modal-open");
  modal.querySelector(".img-news-modal__close")?.focus();
}

function closeModal(){
  if(!modal)return;
  modal.classList.remove("is-open");
  modal.setAttribute("aria-hidden","true");
  document.documentElement.classList.remove("img-news-modal-open");
  if(frame)frame.src="about:blank";
  if(loader)loader.hidden=false;
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