(function () {
  'use strict';

  function themeValue() {
    try { return localStorage.getItem('xhot-theme') || 'auto'; } catch (e) { return 'auto'; }
  }
  function applyTheme(pref) {
    var d = document.documentElement;
    var t = (pref === 'light' || pref === 'dark') ? pref : 'auto';
    d.setAttribute('data-pref', t);
    d.setAttribute('data-theme', t === 'auto'
      ? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : t);
    document.querySelectorAll('[data-set-theme]').forEach(function (btn) {
      btn.classList.toggle('on', btn.getAttribute('data-set-theme') === t);
    });
  }
  function bindTheme() {
    applyTheme(themeValue());
    document.querySelectorAll('[data-set-theme]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var v = btn.getAttribute('data-set-theme');
        try { localStorage.setItem('xhot-theme', v); } catch (e) {}
        applyTheme(v);
      });
    });
    try {
      matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
        if (themeValue() === 'auto') applyTheme('auto');
      });
    } catch (e) {}
  }

  function switchTab(tabId, btn) {
    document.querySelectorAll('.tab-panel').forEach(function (el) { el.classList.remove('active'); });
    document.querySelectorAll('.seg-btn').forEach(function (el) {
      el.classList.remove('active');
      el.setAttribute('aria-selected', 'false');
    });
    var panel = document.getElementById('tab-' + tabId);
    if (panel) panel.classList.add('active');
    if (btn) {
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
    }
  }

  function showStage(id) {
    var dataEl = document.getElementById('anatomy-data');
    var data = {};
    try { data = dataEl ? JSON.parse(dataEl.textContent) : {}; } catch (e) { data = {}; }
    var stages = data.stages || [];
    var st = stages.find(function (s) { return s.id === id; }) || stages[0];
    if (!st) return;
    document.querySelectorAll('.flow-node, .arch-node').forEach(function (n) {
      n.classList.toggle('selected', n.getAttribute('data-stage') === st.id);
    });
    var box = document.getElementById('flow-detail');
    if (box) {
      box.innerHTML = '<strong>[' + st.title + '] 底层执行细节</strong>' +
        (st.evidence ? '<span class="ev ev-' + st.evidence + '">' + evidenceLabel(st.evidence) + '</span>' : '') +
        '<div class="detail-body">' + st.detail + '</div>';
    }
  }

  function evidenceLabel(k) {
    return ({
      source: '源码确认',
      claim: '作者宣称',
      infer: '推断',
      pending: '待验证'
    })[k] || k;
  }

  function bindStages() {
    document.querySelectorAll('.flow-node, .arch-node').forEach(function (n) {
      n.addEventListener('click', function () { showStage(n.getAttribute('data-stage')); });
      n.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); showStage(n.getAttribute('data-stage')); }
      });
    });
    var first = document.querySelector('.flow-node, .arch-node');
    if (first) showStage(first.getAttribute('data-stage'));
  }

  function bindIndexFilter() {
    var q = document.getElementById('anatomy-q');
    var chips = document.querySelectorAll('[data-filter-tag]');
    var cards = document.querySelectorAll('.proj-card');
    var empty = document.getElementById('filter-empty');
    if (!cards.length) return;
    var tag = 'all';
    function apply() {
      var text = (q && q.value || '').trim().toLowerCase();
      var shown = 0;
      cards.forEach(function (card) {
        var hay = (card.getAttribute('data-hay') || '').toLowerCase();
        var tags = (card.getAttribute('data-tags') || '');
        var ok = (!text || hay.indexOf(text) !== -1) && (tag === 'all' || tags.split(/\s+/).indexOf(tag) !== -1);
        card.hidden = !ok;
        if (ok) shown++;
      });
      if (empty) empty.hidden = shown !== 0;
    }
    if (q) q.addEventListener('input', apply);
    chips.forEach(function (chip) {
      chip.addEventListener('click', function () {
        tag = chip.getAttribute('data-filter-tag');
        chips.forEach(function (c) {
          c.classList.toggle('on', c === chip);
          c.setAttribute('aria-pressed', c === chip ? 'true' : 'false');
        });
        apply();
      });
    });
    apply();
  }

  document.addEventListener('DOMContentLoaded', function () {
    bindTheme();
    bindStages();
    bindIndexFilter();
    document.querySelectorAll('.seg-btn').forEach(function (btn) {
      btn.addEventListener('click', function () { switchTab(btn.getAttribute('data-tab'), btn); });
    });
  });

  window.xhotAnatomy = { switchTab: switchTab, showStage: showStage };
})();
