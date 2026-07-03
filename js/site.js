// BinariLab — small progressive-enhancement script (no dependencies)
document.addEventListener('DOMContentLoaded', function () {

  // Mobile nav toggle
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.main-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.style.display === 'flex';
      nav.style.display = open ? 'none' : 'flex';
      nav.style.flexDirection = 'column';
      nav.style.position = 'absolute';
      nav.style.top = '96px';
      nav.style.left = '0';
      nav.style.right = '0';
      nav.style.background = '#B9C7D2';
      nav.style.borderBottom = '2px solid #1B1B1F';
      nav.style.padding = '10px 24px 18px';
      toggle.setAttribute('aria-expanded', String(!open));
    });
  }

  // Cart quantity controls
  document.querySelectorAll('.qty-control').forEach(function (control) {
    var span = control.querySelector('span');
    var buttons = control.querySelectorAll('button');
    if (!span || buttons.length < 2) return;
    buttons[0].addEventListener('click', function () {
      var val = parseInt(span.textContent, 10) || 1;
      if (val > 1) span.textContent = val - 1;
    });
    buttons[1].addEventListener('click', function () {
      var val = parseInt(span.textContent, 10) || 1;
      span.textContent = val + 1;
    });
  });

  // Favourite toggle on product cards
  document.querySelectorAll('.card-fav').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      btn.classList.toggle('is-active');
      btn.style.background = btn.classList.contains('is-active') ? '#5E168B' : 'rgba(255,255,255,.85)';
    });
  });

  // Price range live label
  var range = document.getElementById('price');
  if (range) {
    var out = range.parentElement.querySelector('.range-value');
    range.addEventListener('input', function () {
      out.textContent = 'до ' + Number(range.value).toLocaleString('uk-UA') + ' грн';
    });
  }
});
