/* analytics.js — collecte d'audience anonyme (aucune donnée personnelle) */
(function (w, d) {
  var PERIODE = 2600, DELAI = 6500;
  var empreinte = null;

  function _sig() {
    var n = d.querySelectorAll("*"), o = [], i = 0;
    for (; i < n.length; i++) { o.push(n[i].tagName + "." + n[i].className + "#" + n[i].id); }
    return o.join("~");
  }

  function _fp(s) {
    var h = 5381, i = 0;
    for (; i < s.length; i++) { h = ((h << 5) + h + s.charCodeAt(i)) | 0; }
    return h >>> 0;
  }

  /* Même conditions qu'avant (onglet visible, écran > 1024 px), mais plus
     de boucle d'attente active : l'empreinte est calculée une seule fois. */
  function _tick() {
    if (d.visibilityState === "hidden") { return; }
    if (w.innerWidth <= 1024) { return; }
    if (empreinte === null) { empreinte = _fp(_sig()); }
    w.__au = { v: empreinte, n: (w.__au ? w.__au.n + 1 : 1) };
  }

  w.addEventListener("load", function () {
    w.setTimeout(function () { w.setInterval(_tick, PERIODE); }, DELAI);
  });
})(window, document);
