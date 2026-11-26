// Stand mode helpers shared by clock.html and frame.html.
// Tap the screen to show the "Clock | Photo frame" choice; the choice is remembered.
function go(mode) {
  try { localStorage.setItem('standMode', mode); } catch (e) {}
  location.href = '/' + mode;
  return false;
}
(function () {
  var t;
  document.addEventListener('click', function (e) {
    if (e.target.tagName === 'A') return;
    var m = document.getElementById('modes');
    if (!m) return;
    m.style.display = 'block';
    clearTimeout(t);
    t = setTimeout(function () { m.style.display = 'none'; }, 5000);
  });
})();
