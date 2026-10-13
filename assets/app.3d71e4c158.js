(function(){var d=document.documentElement,mq=matchMedia('(prefers-color-scheme: dark)');
function sync(){document.querySelectorAll('[data-set-theme]').forEach(function(b){var on=b.dataset.setTheme===d.dataset.pref;b.classList.toggle('on',on);b.setAttribute('aria-pressed',on)})}
function theme(){var p=d.dataset.pref;d.dataset.theme=p==='auto'?(mq.matches?'dark':'light'):p}
document.querySelectorAll('[data-set-theme]').forEach(function(b){b.addEventListener('click',function(){d.dataset.pref=b.dataset.setTheme;try{localStorage.setItem('xhot-theme',b.dataset.setTheme)}catch(e){}theme();sync()})});
(mq.addEventListener?mq.addEventListener('change',theme):mq.addListener(theme));sync();
/* 领域 tab（URL hash 记录） */
var tabs=document.querySelectorAll('[data-t]');
function setTab(t,scroll){if(!document.querySelector('.pane[data-p="'+t+'"]'))return;tabs.forEach(function(x){var on=x.dataset.t===t;x.classList.toggle('on',on);x.setAttribute('aria-selected',on)});
document.querySelectorAll('.pane').forEach(function(x){x.classList.toggle('on',x.dataset.p===t)});if(scroll)scrollTo({top:0})}
tabs.forEach(function(b){b.addEventListener('click',function(){setTab(b.dataset.t,true);history.replaceState(null,'','#'+b.dataset.t)})});
if(tabs.length&&location.hash)setTab(location.hash.slice(1),false);
/* 复制 */
function fb(t){var a=document.createElement('textarea');a.value=t;a.setAttribute('readonly','');a.style.cssText='position:fixed;top:-1000px;opacity:0';document.body.appendChild(a);a.select();var ok=false;try{ok=document.execCommand('copy')}catch(e){}document.body.removeChild(a);return ok}
function copy(b,t){function done(ok){b.textContent=ok?'已复制 ✓':'复制失败';b.classList.toggle('ok',ok);clearTimeout(b._t);b._t=setTimeout(function(){b.textContent='复制原文';b.classList.remove('ok')},1600)}
if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t).then(function(){done(true)},function(){done(fb(t))})}else done(fb(t))}
document.addEventListener('click',function(ev){var b=ev.target.closest('.cp');if(b){var t=b.getAttribute('data-copy');if(t==null&&window.XP){var i=+b.closest('.post').dataset.i;XP.ready(function(){copy(b,XP.copyText(i))});return}copy(b,t);return}
var x=ev.target.closest('.ex');if(x){var p=x.closest('.post');var o=p.classList.toggle('open');x.textContent=o?'收起':'展开';x.setAttribute('aria-expanded',o)}});
/* 悬停预取个人页 */
var pf={};function pre(a){var h=a.getAttribute('href');if(!h||pf[h]||!/(^|\/)p\/[^/]+\.html$/.test(h))return;pf[h]=1;var l=document.createElement('link');l.rel='prefetch';l.href=h;document.head.appendChild(l)}
['mouseover','touchstart','focusin'].forEach(function(e){document.addEventListener(e,function(ev){var a=ev.target.closest&&ev.target.closest('a[href]');if(a)pre(a)},{passive:true})});
/* 个人页 */
var mt=document.getElementById('tw-meta');if(!mt)return;var M=JSON.parse(mt.textContent),D=null,waiters=[];
var feed=document.getElementById('feed'),q=document.getElementById('q'),cnt=document.getElementById('cnt'),all=document.getElementById('alll'),more=document.getElementById('more');
window.XP={copyText:function(i){var r=D[i];return r[2]+'\n— '+M.name+' (@'+M.handle+')\n'+r[10]},ready:function(f){D?f():waiters.push(f)}};
var df=new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});
function dt(s){var p={};df.formatToParts(new Date(s)).forEach(function(x){p[x.type]=x.value});return p.year+'-'+p.month+'-'+p.day+' '+p.hour+':'+p.minute}
function fmt(n){if(n>=1e8)return(n/1e8).toFixed(2)+'亿';if(n>=1e4)return(n/1e4).toFixed(1)+'万';return n.toLocaleString('en-US')}
function esc(s){return s.replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function lnk(s){return esc(s).replace(/https?:\/\/[^\s<]+/g,function(u){return '<a href="'+u+'" target="_blank" rel="noopener">'+u.replace(/^https?:\/\//,'')+'</a>'})}
/* D 每行：[id, created_at, text, ok, like, rt, reply, quote, view, heat, url] */

var sort='t',list=[],shown=0,STEP=24,first=true;
function card(i){var r=D[i],long=r[2].length>280;
return '<article class="post c7'+(long?' long':'')+'" data-i="'+i+'"><header><time datetime="'+r[1]+'">'+dt(r[1])+'</time><span class="heat" title="热度 = 赞 + 2×转 + 3×引用 + 评论 + 收藏">🔥 '+fmt(r[9])+'</span></header><div class="pt">'+lnk(r[2])+'</div><footer><div class="act">'+(long?'<button class="ex" type="button" aria-expanded="false">展开</button>':'')+'<button class="cp" type="button">复制原文</button><a class="op" href="'+r[10]+'" target="_blank" rel="noopener">在 X 打开</a></div><div class="met"><span title="点赞"><i aria-hidden="true">♥</i>'+fmt(r[4])+'</span><span title="转发"><i aria-hidden="true">⇄</i>'+fmt(r[5])+'</span><span title="评论"><i aria-hidden="true">💬</i>'+fmt(r[6])+'</span><span title="浏览"><i aria-hidden="true">👁</i>'+fmt(r[8])+'</span></div></footer></article>'}
function page(){var h='',end=Math.min(list.length,shown+STEP);for(var k=shown;k<end;k++)h+=card(list[k]);feed.insertAdjacentHTML('beforeend',h);shown=end;more.hidden=shown>=list.length;more.textContent='再显示 '+Math.min(STEP,list.length-shown)+' 条（共 '+list.length+'）'}
function run(){if(!D)return;var v=q.value.trim().toLowerCase(),A=all&&all.checked,base=0;list=[];
D.forEach(function(r,i){if(!r[3]&&!A)return;base++;if(v&&r.lc.indexOf(v)<0)return;list.push(i)});
if(sort==='h')list.sort(function(a,b){return D[b][9]-D[a][9]});
if(first&&+feed.dataset.pre){first=false;shown=+feed.dataset.pre;more.hidden=shown>=list.length;more.textContent='再显示 '+Math.min(STEP,list.length-shown)+' 条（共 '+list.length+'）'}else{first=false;feed.innerHTML='';shown=0;page()}cnt.textContent=v?('匹配 '+list.length+' / '+base+' 条'):(base+' 条')}
var tm;q.addEventListener('input',function(){clearTimeout(tm);tm=setTimeout(run,120)});if(all)all.addEventListener('change',run);
document.querySelectorAll('[data-sort]').forEach(function(b){b.addEventListener('click',function(){sort=b.dataset.sort;document.querySelectorAll('[data-sort]').forEach(function(x){var on=x===b;x.classList.toggle('on',on);x.setAttribute('aria-pressed',on)});run()})});
more.addEventListener('click',page);
if('IntersectionObserver'in window)new IntersectionObserver(function(es){if(es[0].isIntersecting&&!more.hidden)page()},{rootMargin:'600px'}).observe(more);
fetch(M.src).then(function(r){return r.json()}).then(function(d){D=d;D.forEach(function(r){r.lc=r[2].toLowerCase()});run();waiters.splice(0).forEach(function(f){f()})})})();
