(function () {
  'use strict';

  var PHONE = '77002339520';

  // ---- Mobile menu ----
  var burger = document.getElementById('burger');
  var nav = document.getElementById('nav');
  function setMenu(open) {
    nav.classList.toggle('open', open);
    burger.setAttribute('aria-expanded', String(open));
    burger.setAttribute('aria-label', open ? 'Мәзірді жабу' : 'Мәзірді ашу');
  }
  burger.addEventListener('click', function () {
    setMenu(!nav.classList.contains('open'));
  });
  nav.addEventListener('click', function (e) {
    if (e.target.closest('a')) setMenu(false);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setMenu(false);
  });

  // ---- Services / prices ----
  // unit: what qty counts; prices: [with antiplagiat, without]
  var SERVICES = {
    diploma:      { name: 'Дипломдық жұмыс', fixed: '150 000 – 250 000 ₸', note: 'Нақты баға тақырып пен талаптарға қарай келісіледі.' },
    dissertation: { name: 'Диссертация', fixed: '200 000 ₸-ден', note: 'Нақты баға тақырып пен көлемге қарай есептеледі.' },
    course:       { name: 'Курстық жұмыс', unit: 'Бет саны', short: 'бет', prices: [850, 450], note: 'Титул парағы, жоспар және әдебиеттер тізімі тегін.' },
    presentation: { name: 'Презентация', unit: 'Слайд саны', short: 'слайд', prices: [400, 200], freeSlides: 2, note: 'Бірінші және соңғы слайд тегін.' },
    referat:      { name: 'Реферат', unit: 'Бет саны', short: 'бет', prices: [500, 250], note: 'Титул парағы, жоспар және әдебиеттер тізімі тегін.' },
    essay:        { name: 'Эссе', unit: 'Бет саны', short: 'бет', prices: [1500, 800] },
    article:      { name: 'Мақала', unit: 'Бет саны', short: 'бет', prices: [1500], noPlag: true, from: true, note: 'Бет бағасы 1 500 ₸-ден басталады.' },
    video:        { name: 'Видео дайындау', video: { '30': 2500, '60': 5000 } },
    kmzh:         { name: 'Қысқа мерзімді жоспар (ҚМЖ)', unit: 'Жоспар саны', short: 'дана', prices: [2500], noPlag: true },
    resume:       { name: 'Резюме жазу (дизайнмен)', fixed: '1 000 ₸' },
    originality:  { name: 'Оригиналдылықты көтеру / ИИ түсіру', fixed: 'Келісім бойынша', note: 'Кодировка, оригиналдылықты көтеру, ИИ түсіру — 80–100%.' }
  };

  var form = document.getElementById('orderForm');
  var service = document.getElementById('service');
  var qty = document.getElementById('qty');
  var qtyRow = document.getElementById('qtyRow');
  var qtyLabel = document.getElementById('qtyLabel');
  var plagField = document.getElementById('plagField');
  var videoField = document.getElementById('videoField');
  var estimateEl = document.getElementById('estimate');
  var estimateNote = document.getElementById('estimateNote');

  function fmt(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' ') + ' ₸';
  }
  function radio(name) {
    var el = form.querySelector('input[name="' + name + '"]:checked');
    return el ? el.value : null;
  }

  function calc() {
    var s = SERVICES[service.value];
    if (s.fixed) return { text: s.fixed, note: s.note || '' };
    if (s.video) {
      return { text: fmt(s.video[radio('video')]), note: '' };
    }
    var n = Math.max(1, Math.min(500, parseInt(qty.value, 10) || 0));
    var price = s.noPlag ? s.prices[0] : s.prices[radio('plag') === 'yes' ? 0 : 1];
    var paid = s.freeSlides ? Math.max(0, n - s.freeSlides) : n;
    return { text: fmt(paid * price) + (s.from ? '-ден' : ''), note: s.note || '' };
  }

  function update() {
    var s = SERVICES[service.value];
    var hasQty = !!s.unit;
    qtyRow.hidden = !hasQty;
    qtyRow.style.display = hasQty ? '' : 'none';
    videoField.hidden = !s.video;
    if (hasQty) {
      qtyLabel.textContent = s.unit;
      plagField.style.display = s.noPlag ? 'none' : '';
    }
    var r = calc();
    estimateEl.textContent = r.text;
    estimateNote.textContent = r.note;
  }

  service.addEventListener('change', update);
  form.addEventListener('input', update);
  form.addEventListener('change', update);

  // Service buttons preselect the form
  document.querySelectorAll('[data-service]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      service.value = btn.getAttribute('data-service');
      update();
    });
  });

  // Min date = today
  var deadline = document.getElementById('deadline');
  var t = new Date();
  deadline.min = t.getFullYear() + '-' + String(t.getMonth() + 1).padStart(2, '0') + '-' + String(t.getDate()).padStart(2, '0');

  // ---- Send → WhatsApp (real link, works everywhere) ----
  var sendBtn = document.getElementById('sendBtn');

  function validate() {
    var name = document.getElementById('name').value.trim();
    var phone = document.getElementById('phone').value.trim();
    var ok = true;
    [['name', name.length >= 2], ['phone', phone.replace(/\D/g, '').length >= 10]].forEach(function (p) {
      var field = document.getElementById(p[0]).closest('.field');
      field.classList.toggle('invalid', !p[1]);
      if (!p[1]) ok = false;
    });
    return ok;
  }

  function buildUrl() {
    var s = SERVICES[service.value];
    var lines = [
      'Сәлеметсіз бе! KomekStud сайтынан тапсырыс:',
      '',
      '👤 Аты: ' + document.getElementById('name').value.trim(),
      '📞 Телефон: ' + document.getElementById('phone').value.trim(),
      '📌 Жұмыс түрі: ' + s.name
    ];
    if (s.unit) {
      lines.push('🔢 ' + s.unit + ': ' + qty.value);
      if (!s.noPlag) lines.push('🛡️ Антиплагиат: ' + (radio('plag') === 'yes' ? 'иә' : 'жоқ'));
    }
    if (s.video) lines.push('🎬 Ұзақтығы: ' + (radio('video') === '30' ? '30 секунд' : '1 минут'));
    lines.push('🌐 Тілі: ' + document.getElementById('lang').value);
    if (deadline.value) {
      var d = deadline.value.split('-');
      lines.push('📅 Мерзімі: ' + d[2] + '.' + d[1] + '.' + d[0]);
    }
    var topic = document.getElementById('topic').value.trim();
    if (topic) lines.push('📝 Тақырыбы/талаптар: ' + topic);
    lines.push('💰 Болжамды баға: ' + calc().text);
    return 'https://wa.me/' + PHONE + '?text=' + encodeURIComponent(lines.join('\n'));
  }

  sendBtn.addEventListener('click', function (e) {
    if (!validate()) {
      e.preventDefault();
      form.querySelector('.invalid input').focus();
      return;
    }
    sendBtn.href = buildUrl();
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    sendBtn.click();
  });

  form.querySelectorAll('input').forEach(function (inp) {
    inp.addEventListener('input', function () {
      var f = inp.closest('.field');
      if (f) f.classList.remove('invalid');
    });
  });

  update();

  // ---- Footer year ----
  document.getElementById('year').textContent = new Date().getFullYear();

  // ---- Reveal on scroll ----
  if ('IntersectionObserver' in window) {
    var items = document.querySelectorAll('.feature, .card, .step, .term, .section__head');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add('in');
          io.unobserve(en.target);
        }
      });
    }, { threshold: 0.12 });
    items.forEach(function (el) {
      el.classList.add('reveal');
      io.observe(el);
    });
  }
})();
