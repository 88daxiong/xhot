(function(){var d=document.documentElement,t;try{t=localStorage.getItem('xhot-theme')}catch(e){}t=(t==='light'||t==='dark')?t:'auto';d.setAttribute('data-pref',t);d.setAttribute('data-theme',t==='auto'?(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t)})();
/*@@BODY@@*/
(function(){var d=document.documentElement,mq=matchMedia('(prefers-color-scheme: dark)');
function sync(){document.querySelectorAll('[data-set-theme]').forEach(function(b){b.classList.toggle('on',b.dataset.setTheme===d.dataset.pref)})}
function theme(){var p=d.dataset.pref;d.dataset.theme=p==='auto'?(mq.matches?'dark':'light'):p}
document.querySelectorAll('[data-set-theme]').forEach(function(b){b.onclick=function(){d.dataset.pref=b.dataset.setTheme;try{localStorage.setItem('xhot-theme',b.dataset.setTheme)}catch(e){}theme();sync()}});
(mq.addEventListener?mq.addEventListener('change',theme):mq.addListener(theme));
document.querySelectorAll('[data-t]').forEach(function(b){b.onclick=function(){var t=b.dataset.t;
document.querySelectorAll('[data-t]').forEach(function(x){x.classList.toggle('on',x.dataset.t===t)});
document.querySelectorAll('.pane').forEach(function(x){x.classList.toggle('on',x.dataset.p===t)});
document.querySelectorAll('.li-d').forEach(function(x){x.hidden=x.dataset.p!==t});scrollTo({top:0})}});sync();
function fb(t){var a=document.createElement('textarea');a.value=t;a.setAttribute('readonly','');a.style.cssText='position:fixed;top:-1000px;opacity:0';document.body.appendChild(a);a.select();var ok=false;try{ok=document.execCommand('copy')}catch(e){}document.body.removeChild(a);return ok}
document.addEventListener('click',function(ev){var b=ev.target.closest('.cp');if(b){var t=b.getAttribute('data-copy');
function done(ok){b.textContent=ok?'已复制 ✓':'复制失败';b.classList.toggle('ok',ok);clearTimeout(b._t);b._t=setTimeout(function(){b.textContent='复制原文';b.classList.remove('ok')},1600)}
if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t).then(function(){done(true)},function(){done(fb(t))})}else done(fb(t));return}
var x=ev.target.closest('.ex');if(x){var c=x.closest('.post').querySelector('.xp');var o=c.classList.toggle('open');x.textContent=o?'收起':'展开'}})})();
