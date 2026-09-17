
(function(){
  var original=window.IMGOpenLeagueDetail;
  if(!original || original.__imgPopupSafeguard) return;
  function wrapped(name,sport){
    var fromSearch=!!(window.homeSearchOpenedLeague || window.IMGLeagueSearchOrigin);
    original(name,sport);
    var root=document.getElementById('img-league-detail');
    if(root){
      root.classList.toggle('search-origin',fromSearch);
      if(fromSearch) root.style.display='block';
    }
  }
  wrapped.__imgPopupSafeguard=true;
  window.IMGOpenLeagueDetail=wrapped;
})();
