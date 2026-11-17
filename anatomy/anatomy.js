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
    if (btn && btn.scrollIntoView) {
      try { btn.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'smooth' }); } catch (e) {}
    }
  }

  function anatomyData() {
    var dataEl = document.getElementById('anatomy-data');
    try { return dataEl ? JSON.parse(dataEl.textContent) : {}; } catch (e) { return {}; }
  }

  function evidenceLabel(k) {
    return ({
      source: '源码确认',
      claim: '作者宣称',
      infer: '推断',
      pending: '待验证',
      sim: '模拟演示'
    })[k] || k;
  }

  function renderDetail(box, title, evidence, detail) {
    if (!box) return;
    box.innerHTML = '<strong>[' + title + ']</strong>' +
      (evidence ? '<span class="ev ev-' + evidence + '">' + evidenceLabel(evidence) + '</span>' : '') +
      '<div class="detail-body">' + (detail || '') + '</div>';
  }

  function showStage(id) {
    var data = anatomyData();
    var stages = data.stages || [];
    var st = stages.find(function (s) { return s.id === id; }) || stages[0];
    if (!st) return;
    document.querySelectorAll('.flow-node, .arch-node, .pipe-node').forEach(function (n) {
      n.classList.toggle('selected', n.getAttribute('data-stage') === st.id);
    });
    renderDetail(document.getElementById('flow-detail'), st.title, st.evidence, st.detail);
  }

  function bindStages() {
    document.querySelectorAll('.flow-node, .arch-node, .pipe-node').forEach(function (n) {
      if (!n.hasAttribute('tabindex')) n.setAttribute('tabindex', '0');
      if (!n.hasAttribute('role')) n.setAttribute('role', 'button');
      n.addEventListener('click', function () { showStage(n.getAttribute('data-stage')); });
      n.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); showStage(n.getAttribute('data-stage')); }
      });
    });
    // 旧文仍自动展开第一格；新文的流程图本身已可读，不自动打开抽屉。
    var first = document.querySelector('.flow-node, .arch-node');
    if (first) showStage(first.getAttribute('data-stage'));
  }

  function bindSchema() {
    var data = anatomyData();
    var schemas = data.schemas || {};
    if (!Object.keys(schemas).length) return;
    function show(id) {
      var sc = schemas[id];
      if (!sc) return;
      document.querySelectorAll('[data-schema]').forEach(function (n) {
        n.classList.toggle('selected', n.getAttribute('data-schema') === id);
      });
      renderDetail(document.getElementById('schema-detail'), sc.title || id, sc.evidence, sc.detail);
    }
    document.querySelectorAll('[data-schema]').forEach(function (n) {
      if (!n.hasAttribute('tabindex')) n.setAttribute('tabindex', '0');
      n.addEventListener('click', function () { show(n.getAttribute('data-schema')); });
      n.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); show(n.getAttribute('data-schema')); }
      });
    });
    var first = document.querySelector('[data-schema]');
    if (first) show(first.getAttribute('data-schema'));
  }

  var player = { i: 0, timer: null, steps: [] };

  function reduceMotion() {
    try { return matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { return false; }
  }

  function renderPlay(i) {
    var steps = player.steps;
    if (!steps.length) return;
    player.i = (i + steps.length) % steps.length;
    var st = steps[player.i];
    document.querySelectorAll('[data-play-step]').forEach(function (n) {
      n.classList.toggle('selected', Number(n.getAttribute('data-play-step')) === player.i);
    });
    var status = document.getElementById('play-status');
    if (status) status.textContent = '第 ' + (player.i + 1) + ' / ' + steps.length + ' 步：' + st.title;
    var bar = document.getElementById('play-bar');
    if (bar) bar.style.width = (((player.i + 1) / steps.length) * 100) + '%';
    renderDetail(document.getElementById('play-detail'), st.title, st.evidence, st.detail);
    var sim = document.getElementById('play-sim');
    if (sim) sim.innerHTML = st.sim || '';
  }

  function stopPlay() {
    if (player.timer) { clearInterval(player.timer); player.timer = null; }
    var btn = document.getElementById('play-toggle');
    if (btn) { btn.textContent = '播放'; btn.setAttribute('aria-pressed', 'false'); }
  }

  function startPlay() {
    if (player.timer) return;
    var btn = document.getElementById('play-toggle');
    if (btn) { btn.textContent = '暂停'; btn.setAttribute('aria-pressed', 'true'); }
    var ms = reduceMotion() ? 0 : 2200;
    if (!ms) {
      renderPlay(player.i + 1);
      stopPlay();
      return;
    }
    player.timer = setInterval(function () {
      if (player.i >= player.steps.length - 1) {
        renderPlay(player.steps.length - 1);
        stopPlay();
        return;
      }
      renderPlay(player.i + 1);
    }, ms);
  }

  function bindPlayer() {
    var data = anatomyData();
    player.steps = data.play || [];
    if (!player.steps.length) return;
    var list = document.getElementById('play-steps');
    if (list && !list.children.length) {
      player.steps.forEach(function (st, idx) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'flow-node';
        b.setAttribute('data-play-step', String(idx));
        b.innerHTML = '<div class="node-step">步骤 ' + (idx + 1) + '</div><div class="node-title"></div>';
        b.querySelector('.node-title').textContent = st.title;
        b.addEventListener('click', function () { stopPlay(); renderPlay(idx); });
        list.appendChild(b);
      });
    } else {
      document.querySelectorAll('[data-play-step]').forEach(function (n) {
        n.addEventListener('click', function () {
          stopPlay();
          renderPlay(Number(n.getAttribute('data-play-step')));
        });
      });
    }
    var prev = document.getElementById('play-prev');
    var next = document.getElementById('play-next');
    var tog = document.getElementById('play-toggle');
    var rst = document.getElementById('play-reset');
    if (prev) prev.addEventListener('click', function () { stopPlay(); renderPlay(player.i - 1); });
    if (next) next.addEventListener('click', function () { stopPlay(); renderPlay(player.i + 1); });
    if (tog) tog.addEventListener('click', function () { if (player.timer) stopPlay(); else startPlay(); });
    if (rst) rst.addEventListener('click', function () { stopPlay(); renderPlay(0); });
    var wrap = document.getElementById('play-controls');
    if (wrap) {
      wrap.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowLeft') { e.preventDefault(); stopPlay(); renderPlay(player.i - 1); }
        if (e.key === 'ArrowRight') { e.preventDefault(); stopPlay(); renderPlay(player.i + 1); }
        if (e.key === ' ') { e.preventDefault(); if (player.timer) stopPlay(); else startPlay(); }
        if (e.key === 'Home') { e.preventDefault(); stopPlay(); renderPlay(0); }
        if (e.key === 'End') { e.preventDefault(); stopPlay(); renderPlay(player.steps.length - 1); }
      });
    }
    renderPlay(0);
  }

  function bindQuiz() {
    document.querySelectorAll('[data-quiz]').forEach(function (root) {
      var answers = root.querySelector('.quiz-answers');
      root.querySelectorAll('[data-ok]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var ok = btn.getAttribute('data-ok') === '1';
          root.querySelectorAll('[data-ok]').forEach(function (b) { b.disabled = true; });
          btn.classList.add(ok ? 'quiz-ok' : 'quiz-bad');
          if (answers) {
            answers.hidden = false;
            answers.classList.add(ok ? 'ok' : 'bad');
          }
        });
      });
    });
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
    bindSchema();
    bindPlayer();
    bindQuiz();
    bindIndexFilter();
    document.querySelectorAll('.seg-btn').forEach(function (btn) {
      btn.addEventListener('click', function () { switchTab(btn.getAttribute('data-tab'), btn); });
    });
    document.querySelectorAll('[data-tab-jump]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        var id = a.getAttribute('data-tab-jump');
        var btn = document.querySelector('.seg-btn[data-tab="' + id + '"]');
        if (btn) {
          e.preventDefault();
          switchTab(id, btn);
          var panel = document.getElementById('tab-' + id);
          if (panel && panel.scrollIntoView) {
            try { panel.scrollIntoView({ block: 'start', behavior: reduceMotion() ? 'auto' : 'smooth' }); } catch (err) {}
          }
        }
      });
    });
  });

  window.xhotAnatomy = {
    switchTab: switchTab,
    showStage: showStage,
    renderPlay: renderPlay,
    stopPlay: stopPlay,
    getPlayer: function () { return { i: player.i, n: player.steps.length, playing: !!player.timer }; }
  };
})();
