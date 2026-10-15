(function(){var d=document.documentElement,mq=matchMedia('(prefers-color-scheme: dark)');
function sync(){document.querySelectorAll('[data-set-theme]').forEach(function(b){var on=b.dataset.setTheme===d.dataset.pref;b.classList.toggle('on',on);b.setAttribute('aria-pressed',on)})}
function theme(){var p=d.dataset.pref;d.dataset.theme=p==='auto'?(mq.matches?'dark':'light'):p}
document.querySelectorAll('[data-set-theme]').forEach(function(b){b.addEventListener('click',function(){d.dataset.pref=b.dataset.setTheme;try{localStorage.setItem('xhot-theme',b.dataset.setTheme)}catch(e){}theme();sync()})});
(mq.addEventListener?mq.addEventListener('change',theme):mq.addListener(theme));sync();
var $=function(s,r){return(r||document).querySelector(s)},$$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
function seg(attr,v){$$('['+attr+']').forEach(function(x){var on=x.getAttribute(attr)===v;x.classList.toggle('on',on);x.setAttribute('aria-pressed',on)})}
/* hash 状态：#dom=ai&sort=g */
function hget(){var o={};location.hash.slice(1).split('&').forEach(function(kv){var p=kv.split('=');if(p[0])o[p[0]]=decodeURIComponent(p[1]||'')});if(/^(ai|money|growth)$/.test(location.hash.slice(1)))o.dom=location.hash.slice(1);return o}
function hset(o){var s=Object.keys(o).filter(function(k){return o[k]&&o[k]!=='all'&&!(k==='sort'&&o[k]===o._def)&&k[0]!=='_'}).map(function(k){return k+'='+o[k]}).join('&');history.replaceState(null,'',s?'#'+s:location.pathname+location.search)}
/* 工具 */
function fmt(n){if(n>=1e8)return(n/1e8).toFixed(2)+'亿';if(n>=1e4)return(n/1e4).toFixed(1)+'万';return n.toLocaleString('en-US')}
function esc(s){return String(s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
/* 只保留 http(s) 链接，其它一律 '#'（结果已转义） */
function safeUrl(u){u=String(u==null?'':u).trim();return /^https?:\/\//i.test(u)?esc(u):'#'}
/* url 省略时按 handle + id 还原 */
function xurl(r,h){return r[9]||('https://x.com/'+h+'/status/'+r[0])}
function lnk(s){return esc(s).replace(/https?:\/\/[^\s<&"']+/g,function(u){return '<a href="'+u+'" target="_blank" rel="noopener noreferrer">'+u.replace(/^https?:\/\//,'')+'</a>'})}
var df=new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});
function jdt(s){var p={};df.formatToParts(new Date(s)).forEach(function(x){p[x.type]=x.value});return p.month+'-'+p.day+' '+p.hour+':'+p.minute}
/* 时间：北京时间日期键、今天/昨天、HH:MM、相对时间 */
var dkf=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'});
function dkey(s){return dkf.format(new Date(s))}
var WD='日一二三四五六';
function dlab(k){return k===dkey(Date.now())?'今天':k===dkey(Date.now()-864e5)?'昨天':(+k.slice(5,7))+'月'+(+k.slice(8))+'日'}
function dsub(k){return (+k.slice(5,7))+'月'+(+k.slice(8))+'日 周'+WD[new Date(k+'T12:00:00+08:00').getUTCDay()]}
function hm(s){var p={};df.formatToParts(new Date(s)).forEach(function(x){p[x.type]=x.value});return p.hour+':'+p.minute}
function rel(s){var m=(Date.now()-new Date(s))/6e4;if(m<1)return '刚刚';if(m<60)return Math.floor(m)+' 分钟前';if(m<1440)return Math.floor(m/60)+' 小时前';var k=dkey(s);return k===dkey(Date.now()-864e5)?'昨天':k.slice(5)}
function tmh(s){return '<time class="tm" datetime="'+esc(s)+'"><b>'+hm(s)+'</b><span class="rl">'+rel(s)+'</span></time>'}
function sep(k){var l=dlab(k),sb=dsub(k);if(l!=='今天'&&l!=='昨天')sb=sb.split(' ')[1];return '<div class="dsep" data-d="'+esc(k)+'"><b>'+l+'</b><span>'+sb+'</span></div>'}
/* 页面打开时刷新「今天/昨天」与相对时间（静态页可能是昨天生成的） */
function relabel(root){$$('.dsep[data-d]',root).forEach(function(x){var b=$('b',x);if(b)b.textContent=dlab(x.dataset.d)});$$('time.tm[datetime]',root).forEach(function(t){var r=$('.rl',t);if(r)r.textContent=rel(t.getAttribute('datetime'))})}
function lastSep(root){var s=$$('.dsep',root);return s.length?s[s.length-1].dataset.d:null}
var DC={ai:'var(--ai)',money:'var(--money)',growth:'var(--growth)'};
function avh(u,n,f,h,pref){return '<span class="av" style="--h:'+h+'" aria-hidden="true">'+esc((n||u).charAt(0).toUpperCase())+(f?'<img data-src="'+pref+'assets/av/'+f+'" alt="" width="96" height="96" decoding="async">':'')+'</span>'}
/* r=[id,t,text,like,rt,reply,quote,view,heat,url]；who=null 表示个人页 */
function card(r,who,dom,pref,week){var t=r[2],lg=t.length>150||t.split('\n').length>5;
var hd='<div class="pm"><span class="heat" title="热度 = 赞 + 2×转 + 3×引用 + 评论 + 收藏">🔥 '+fmt(r[8])+'</span>'+tmh(r[1])+'</div>';
hd=who?'<header>'+avh(who[0],who[1],who[4],who[5],pref)+'<div class="who"><a href="'+pref+'p/'+who[0]+'.html">'+esc(who[1])+'</a><small>@'+esc(who[2])+'</small></div>'+hd+'</header>':'<header><span class="tag">'+(r[1]>=week?'近一周':'更早')+'</span><div class="who"></div>'+hd+'</header>';
return '<article class="post" style="--dc:'+DC[dom]+'" data-k="'+r[0]+'">'+hd+'<div class="pt ptc">'+lnk(t)+'</div><footer><div class="act"><button class="btn ex" type="button" aria-expanded="false"'+(lg?'':' hidden')+'>展开</button><button class="btn cp" type="button">复制原文</button><a class="btn op" href="'+safeUrl(xurl(r,who?who[2]:M.handle))+'" target="_blank" rel="noopener noreferrer">在 X 打开 ↗</a></div><div class="met"><span title="点赞"><i aria-hidden="true">♥</i>'+fmt(r[3])+'</span><span title="转发"><i aria-hidden="true">⇄</i>'+fmt(r[4])+'</span><span title="评论"><i aria-hidden="true">💬</i>'+fmt(r[5])+'</span><span title="浏览"><i aria-hidden="true">👁</i>'+fmt(r[7])+'</span></div></footer></article>'}
/* 展开按钮：只有真溢出才显示 */
var avIO='IntersectionObserver' in window?new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){var i=x.target;i.src=i.dataset.src;i.removeAttribute('data-src');avIO.unobserve(i)}})},{rootMargin:'300px'}):null;
/* 头像加载失败就移除（替代内联 onerror，便于严格 CSP） */
document.addEventListener('error',function(ev){var t=ev.target;if(t&&t.tagName==='IMG'&&t.parentNode&&t.parentNode.classList&&t.parentNode.classList.contains('av'))t.remove()},true);
function lazyAv(root){$$('img[data-src]',root).forEach(function(i){if(avIO)avIO.observe(i);else{i.src=i.dataset.src;i.removeAttribute('data-src')}})}
function fixEx(root){lazyAv(root);$$('.post',root).forEach(function(p){var pt=$('.ptc,.nbc',p),b=$('.ex',p);if(!pt||!b||p.classList.contains('open'))return;b.hidden=pt.scrollHeight<=pt.clientHeight+2;pt.classList.toggle('fit',b.hidden)})}
/* 复制 */
var TXT={};
function fb(t){var a=document.createElement('textarea');a.value=t;a.setAttribute('readonly','');a.style.cssText='position:fixed;top:-1000px;opacity:0';document.body.appendChild(a);a.select();var ok=false;try{ok=document.execCommand('copy')}catch(e){}document.body.removeChild(a);return ok}
function copy(b,t){function done(ok){b.textContent=ok?'已复制 ✓':'复制失败';b.classList.toggle('ok',ok);clearTimeout(b._t);b._t=setTimeout(function(){b.textContent='复制原文';b.classList.remove('ok')},1600)}
if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t).then(function(){done(true)},function(){done(fb(t))})}else done(fb(t))}
function ctext(p){var k=p.dataset.k;if(TXT[k])return TXT[k];var w=$('.who a',p),h=$('.who small',p);return $('.pt',p).innerText+'\n— '+(w?w.textContent+' ('+h.textContent+')':(M?M.name+' (@'+M.handle+')':''))+'\n'+$('.op',p).href}
document.addEventListener('click',function(ev){var b=ev.target.closest('.cp');if(b){copy(b,ctext(b.closest('.post')));return}
var x=ev.target.closest('.ex');if(x){var p=x.closest('.post');var o=p.classList.toggle('open');x.textContent=o?'收起':'展开';x.setAttribute('aria-expanded',o)}});
/* 悬停预取 */
var pf={};['mouseover','touchstart','focusin'].forEach(function(e){document.addEventListener(e,function(ev){var a=ev.target.closest&&ev.target.closest('a[href]');if(!a)return;var h=a.getAttribute('href');if(!h||pf[h]||/^https?:/.test(h)||!/\.html$/.test(h))return;pf[h]=1;var l=document.createElement('link');l.rel='prefetch';l.href=h;document.head.appendChild(l)},{passive:true})});
lazyAv(document);document.addEventListener('click',function(ev){$$('details.fr[open]').forEach(function(d){if(!d.contains(ev.target))d.open=false})});
if($('#daily')){var oh=location.hash.slice(1);if(/(^|&)(sort|dom)=|^(ai|money|growth)$/.test(oh)){location.replace('hot.html#'+oh);return}}
/* 吸顶分隔条位置 = 顶栏实际高度 */
function toph(){var t=$('.top');if(t)document.documentElement.style.setProperty('--toph',t.offsetHeight+'px')}toph();addEventListener('resize',toph);
relabel(document);
var M=null,feed=$('#feed'),more=$('#more'),cnt=$('#cnt'),STEP=36;
/* 通用领域过滤（资讯/趋势/账号榜） */
function domFilter(dom){$$('[data-dom]').forEach(function(el){if(el.tagName==='BUTTON')return;el.hidden=dom!=='all'&&el.dataset.dom!==dom})}
/* ===== 热帖 ===== */
if(feed&&feed.dataset.src){var H=null,st={dom:'all',sort:'t',_def:'t'},list=[],shown=+feed.dataset.pre,wait=[];
function load(f){if(H)return f();wait.push(f);if(wait.length>1)return;fetch(feed.dataset.src).then(function(r){return r.json()}).then(function(j){H=j;H.P.forEach(function(p){var u=H.U[p[10]];TXT[p[0]]=p[2]+'\n— '+u[1]+' (@'+u[2]+')\n'+xurl(p,u[2])});wait.splice(0).forEach(function(f){f()})})}
function lab(){var v=hq&&hq.value.trim();return (v?'「'+v+'」匹配 ':'')+({w:'近一周',g:'全局',t:'最新'})[st.sort]+' '+list.length+' 条 · 每人最多 3 条'}
var hq=$('#hq');function render(reset){list=H.L[st.dom][st.sort];var v=hq&&hq.value.trim().toLowerCase();if(v)list=list.filter(function(i){var p=H.P[i],u=H.U[p[10]];return (p[2]+' '+u[1]+' '+u[2]).toLowerCase().indexOf(v)>=0});if(reset){feed.innerHTML='';shown=0}feed.classList.toggle('tl',st.sort==='t');var ld=reset?null:lastSep(feed),h='',end=Math.min(list.length,shown+STEP);for(var k=shown;k<end;k++){var p=H.P[list[k]],u=H.U[p[10]];if(st.sort==='t'){var dk=dkey(p[1]);if(dk!==ld){h+=sep(dk);ld=dk}}h+=card(p,u,st.dom==='all'?u[3]:st.dom,'',0)}feed.insertAdjacentHTML('beforeend',h);shown=end;
if(!list.length)feed.innerHTML='<div class="empty">这个范围内暂无帖子</div>';more.hidden=shown>=list.length;more.textContent='再显示 '+Math.min(STEP,list.length-shown)+' 条（已显示 '+shown+' / '+list.length+'）';cnt.textContent=lab();fixEx(feed)}
function apply(){seg('data-sort',st.sort);seg('data-dom',st.dom);hset(st);load(function(){render(true)})}
$$('[data-sort]').forEach(function(b){b.addEventListener('click',function(){st.sort=b.dataset.sort;apply()})});
$$('button[data-dom]').forEach(function(b){b.addEventListener('click',function(){st.dom=b.dataset.dom;apply()})});
more.addEventListener('click',function(){load(function(){render(false)})});if(hq){var ht;hq.addEventListener('input',function(){clearTimeout(ht);ht=setTimeout(function(){load(function(){render(true)})},150)})}
var h0=hget();if(h0.dom||h0.sort){st.dom=H0ok(h0.dom,['all','ai','money','growth'],'all');st.sort=H0ok(h0.sort,['w','g','t'],'t');apply()}else{fixEx(feed);more.textContent='再显示 '+STEP+' 条'}
/* 空闲时预取热帖数据，首次切换排序/领域更快（省流量模式不预取） */
if(!(navigator.connection&&navigator.connection.saveData)){var idl=function(){load(function(){})};addEventListener('load',function(){(window.requestIdleCallback||function(f){setTimeout(f,1500)})(idl,{timeout:4000})})}}
function H0ok(v,a,d){return a.indexOf(v)>=0?v:d}
/* ===== 账号榜 ===== */
var ag=$('#ag');if(ag){var as={dom:'all',sort:'grp',_def:'grp'},orig=$$('#ag > *'),aq=$('#aq');
function arender(){var v=(aq.value||'').trim().toLowerCase(),n=0;seg('data-asort',as.sort);seg('data-dom',as.dom);
var cards=orig.filter(function(x){return x.classList.contains('acard')});
if(as.sort==='grp'){orig.forEach(function(x){ag.appendChild(x)})}else{var k=as.sort==='f'?'f':'d';cards.slice().sort(function(a,b){return b.dataset[k]-a.dataset[k]}).forEach(function(x){ag.appendChild(x)})}
orig.forEach(function(x){var ok=as.dom==='all'||x.dataset.dom===as.dom;if(x.classList.contains('gh2'))x.hidden=!ok||as.sort!=='grp'||!!v;else{ok=ok&&(!v||x.dataset.q.indexOf(v)>=0);x.hidden=!ok;if(ok)n++}});
$('#acnt').textContent=n+' 个账号 · 点卡片看主页';hset({dom:as.dom,sort:as.sort,_def:'grp'})}
$$('[data-asort]').forEach(function(b){b.addEventListener('click',function(){as.sort=b.dataset.asort;arender()})});
$$('button[data-dom]').forEach(function(b){b.addEventListener('click',function(){as.dom=b.dataset.dom;arender()})});
aq.addEventListener('input',arender);var a0=hget();if(a0.dom||a0.sort){as.dom=H0ok(a0.dom,['all','ai','money','growth'],'all');as.sort=H0ok(a0.sort,['grp','f','d'],'grp');arender()}}
/* ===== 资讯 ===== */
var ng=$('#ng');
/* ===== 资讯：精选/全部/来源筛选，点标题行内展开全文（正文 JSON 按需加载，生成器已转义） ===== */
if(ng){var NB=null,nw=[];function nload(f){if(NB)return f&&f();if(f)nw.push(f);if(nw.length>1||nload.busy)return;nload.busy=1;fetch(ng.dataset.body).then(function(r){return r.json()}).then(function(B){NB=B;nw.splice(0).forEach(function(f){f()})})}
function nopen(li,on){var b=$('.nrh',li),bd=$('.nrb',li);if(on===undefined)on=bd.hidden;if(on&&!bd.dataset.ok){nload(function(){var x=NB[+li.dataset.i];if(typeof x==='string'){bd.innerHTML=x;bd.dataset.ok=1}})}bd.hidden=!on;li.classList.toggle('open',on);b.setAttribute('aria-expanded',on)}
ng.addEventListener('click',function(ev){var b=ev.target.closest('.nrh');if(b)nopen(b.closest('.nr'))});
var nst={src:'top'};function nsr(){var s=nst.src;seg('data-src',s);var top=s==='top';$('#ntop').hidden=!top;$('#nall').hidden=top;var n=0;
if(!top){$$('#nall .ndg').forEach(function(g){var c=0;$$('.nr',g).forEach(function(li){var ok=s==='all'||li.dataset.s===s;li.hidden=!ok;if(ok)c++});g.hidden=!c;n+=c})}else n=1;$('#nempty').hidden=n>0;hset({src:s==='top'?'':s})}
$$('[data-src]').forEach(function(b){b.addEventListener('click',function(){nst.src=b.dataset.src;nsr()})});
$('#nmore').addEventListener('click',function(){nst.src='all';nsr();$('#nall').scrollIntoView({block:'start'})});
var s0=hget();if(s0.src&&/^(all|h|d|s|x)$/.test(s0.src)){nst.src=s0.src;nsr()}
if(s0.n&&/^\d+$/.test(s0.n)){var li=$('#ntop .nr[data-i="'+s0.n+'"]');if(!li){nst.src='all';nsr();li=$('#nall .nr[data-i="'+s0.n+'"]')}if(li){nopen(li,true);li.classList.add('hl');setTimeout(function(){li.scrollIntoView({block:'center'})},60)}}
addEventListener('load',function(){(window.requestIdleCallback||function(f){setTimeout(f,2000)})(function(){nload()},{timeout:5000})})}
if(!ag&&!(feed)&&$('button[data-dom]')){var ns={dom:'all'};function nr(){seg('data-dom',ns.dom);domFilter(ns.dom);hset(ns)}
$$('button[data-dom]').forEach(function(b){b.addEventListener('click',function(){ns.dom=b.dataset.dom;nr()})});var n0=hget();if(n0.dom){ns.dom=H0ok(n0.dom,['all','ai','money','growth'],'all');nr()}}
/* ===== 个人页 ===== */
var mt=$('#tw-meta');if(!mt)return;M=JSON.parse(mt.textContent);var D=null,ps={sort:feed.dataset.mode,_def:feed.dataset.mode},pl=[],pshown=+feed.dataset.pre,q=$('#q'),all=$('#alll'),first=true;
var who=null;
function prun(){if(!D)return;var v=q.value.trim().toLowerCase(),A=all&&all.checked,base=0;pl=[];
D.forEach(function(r,i){if(!r[10]&&!A)return;if(ps.sort==='w'&&r[1]<M.week)return;base++;if(v&&r.lc.indexOf(v)<0)return;pl.push(i)});
if(ps.sort!=='t')pl.sort(function(a,b){return D[b][8]-D[a][8]});
feed.innerHTML='';pshown=0;ppage();cnt.textContent=({w:'近一周',g:'全局',t:'全部'})[ps.sort]+(v?' 匹配 '+pl.length+' / '+base:' '+base)+' 条';if(!pl.length)feed.innerHTML='<div class="empty">'+(ps.sort==='w'?'近一周没有新帖，试试「全局热度」或「时间」':'没有匹配的推文')+'</div>'}
function ppage(){feed.classList.toggle('tl',ps.sort==='t');var ld=pshown?lastSep(feed):null,h='',end=Math.min(pl.length,pshown+24);for(var k=pshown;k<end;k++){var r=D[pl[k]];if(ps.sort==='t'){var dk=dkey(r[1]);if(dk!==ld){h+=sep(dk);ld=dk}}h+=card(r,null,M.dom,'../',M.week)}feed.insertAdjacentHTML('beforeend',h);pshown=end;more.hidden=pshown>=pl.length;more.textContent='再显示 '+Math.min(24,pl.length-pshown)+' 条（已显示 '+pshown+' / '+pl.length+'）';fixEx(feed)}
function pload(f){if(D)return f();fetch(M.src).then(function(r){return r.json()}).then(function(d){D=d;D.forEach(function(r){r.lc=r[2].toLowerCase();TXT[r[0]]=r[2]+'\n— '+M.name+' (@'+M.handle+')\n'+xurl(r,M.handle)});f()})}
$$('[data-sort]').forEach(function(b){b.addEventListener('click',function(){ps.sort=b.dataset.sort;seg('data-sort',ps.sort);hset(ps);pload(prun)})});
var tm;q.addEventListener('input',function(){clearTimeout(tm);tm=setTimeout(function(){pload(prun)},120)});if(all)all.addEventListener('change',function(){pload(prun)});
more.addEventListener('click',function(){pload(ppage)});fixEx(feed);
var p0=hget();pload(function(){if(p0.sort&&/^[wgt]$/.test(p0.sort)){ps.sort=p0.sort;seg('data-sort',ps.sort);prun()}else{pl=[];D.forEach(function(r,i){if(r[10]&&(ps.sort!=='w'||r[1]>=M.week))pl.push(i)});if(ps.sort!=='t')pl.sort(function(a,b){return D[b][8]-D[a][8]});more.hidden=pshown>=pl.length;more.textContent='再显示 '+Math.min(24,pl.length-pshown)+' 条（已显示 '+pshown+' / '+pl.length+'）'}})})();
