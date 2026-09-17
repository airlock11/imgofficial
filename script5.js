
/* IMG media protection: blocks common right-click/save/drag gestures.
   This deters casual copying; web images can never be made completely impossible to retrieve. */
(function(){
  document.addEventListener('contextmenu', function(e){
    if (e.target.closest && (e.target.closest('img') || e.target.closest('.sport-image, .feature-card, .about-visual, .hero'))) {
      e.preventDefault();
    }
  }, true);
  document.addEventListener('dragstart', function(e){
    if (e.target.closest && e.target.closest('img, .sport-image, .feature-card, .about-visual, .hero')) {
      e.preventDefault();
    }
  }, true);
  document.addEventListener('selectstart', function(e){
    if (e.target.closest && e.target.closest('img, .sport-image, .feature-card, .about-visual, .hero')) {
      e.preventDefault();
    }
  }, true);
})();
