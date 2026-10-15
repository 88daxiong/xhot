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
function copy(b,t){function done(ok){b.textContent=ok?'已复制 ✓':'复制失败';b.classList.toggle('ok',ok);clearTimeout(b._t);b._t=setTimeout(function(){b.textContent=b.dataset.l||'复制原文';b.classList.remove('ok')},1600)}
if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t).then(function(){done(true)},function(){done(fb(t))})}else done(fb(t))}
function rawt(pt){var c=pt.cloneNode(true);$$('a',c).forEach(function(a){a.replaceWith(a.getAttribute('href')||a.textContent)});return c.textContent}
function ctext(p){if(p.classList.contains('dh')){var hn=$('.hh b',p),hs=$('.hh small',p),op=$('.op',p);return rawt($('.dor .pt:not([hidden])',p))+'\n— '+(hn?hn.textContent:'')+' ('+(hs?hs.textContent:'')+')\n'+(op?op.href:'')}var k=p.dataset.k;if(TXT[k])return TXT[k];var w=$('.who a',p),h=$('.who small',p);return $('.pt',p).innerText+'\n— '+(w?w.textContent+' ('+h.textContent+')':(M?M.name+' (@'+M.handle+')':''))+'\n'+$('.op',p).href}
document.addEventListener('click',function(ev){var b=ev.target.closest('.cp');if(b){copy(b,ctext(b.closest('.post,.dh')));return}
var ol=ev.target.closest('[data-ol]');if(ol){var q=ol.closest('.dh'),v=ol.dataset.ol;$$('[data-ol]',q).forEach(function(z){var on=z===ol;z.classList.toggle('on',on);z.setAttribute('aria-pressed',on)});$('.ptz',q).hidden=v!=='zh';$('.pto',q).hidden=v!=='en';var cb=$('.cp',q);if(cb){cb.dataset.l=v==='zh'?'复制译文':'复制原文';cb.textContent=cb.dataset.l}return}
var x=ev.target.closest('.ex');if(x){var p=x.closest('.post,.dh');var o=p.classList.toggle('open');x.textContent=o?'收起':'展开';x.setAttribute('aria-expanded',o);if(p.classList.contains('dh')){var dr=$('.dor',p);if(dr)dr.hidden=!o}}});
/* 悬停预取 */
var pf={};['mouseover','touchstart','focusin'].forEach(function(e){document.addEventListener(e,function(ev){var a=ev.target.closest&&ev.target.closest('a[href]');if(!a)return;var h=a.getAttribute('href');if(!h||pf[h]||/^https?:/.test(h)||!/\.html$/.test(h))return;pf[h]=1;var l=document.createElement('link');l.rel='prefetch';l.href=h;document.head.appendChild(l)},{passive:true})});
lazyAv(document);document.addEventListener('click',function(ev){$$('details.fr[open]').forEach(function(d){if(!d.contains(ev.target))d.open=false})});
if($('#daily')){var oh=location.hash.slice(1);if(/(^|&)(sort|dom)=|^(ai|money|growth)$/.test(oh)){location.replace('hot.html#'+oh);return}}
/* 吸顶分隔条位置 = 顶栏实际高度 */
function toph(){var t=$('.top');if(t)document.documentElement.style.setProperty('--toph',t.offsetHeight+'px')}toph();addEventListener('resize',toph);
relabel(document);
/* ===== 统一日期控件：‹ [日期 ▾] ›；state = 页内筛选（空 = 全部日期），nav = 跳转（日报） ===== */
var DRE=/^\d{4}-\d\d-\d\d$/;
function dfull(k){var md=(+k.slice(5,7))+'月'+(+k.slice(8))+'日';return k===dkey(Date.now())?'今天 · '+md:k===dkey(Date.now()-864e5)?'昨天 · '+md:md+' 周'+WD[new Date(k+'T12:00:00+08:00').getUTCDay()]}
function dinit(el,cb){var days=(el.dataset.days||'').split(',').filter(function(x){return DRE.test(x)}),nav=el.dataset.mode==='nav',cur=DRE.test(el.dataset.cur||'')?el.dataset.cur:'',lab=$('.dcl',el),bp=$('.dcp',el),bn=$('.dcn',el),bm=$('.dcm',el),pop=null,vm='';
function z(n){return n<10?'0'+n:''+n}
function show(){lab.textContent=cur?dfull(cur):(nav?'选择日期':'全部日期');if(!nav){var i=days.indexOf(cur);bp.disabled=cur?i<0||i>=days.length-1:!days.length;bn.disabled=!cur}}
function close(){if(pop){pop.remove();pop=null;bm.setAttribute('aria-expanded','false')}}
function go(k){if(nav){if(k&&k!==cur&&days.indexOf(k)>=0)location.href=el.dataset.href.replace('{d}',k);return}cur=k;show();close();if(cb)cb(k)}
function render(){var y=+vm.slice(0,4),m=+vm.slice(5),wd=(new Date(Date.UTC(y,m-1,1)).getUTCDay()+6)%7,n=new Date(Date.UTC(y,m,0)).getUTCDate(),t=dkey(Date.now()),lo=days.length?days[days.length-1].slice(0,7):vm,hi=days.length?days[0].slice(0,7):vm;
var h='<div class="dch"><button type="button" class="dcb" data-m="-1" aria-label="上个月"'+(vm<=lo?' disabled':'')+'>‹</button><b>'+y+'年'+m+'月</b><button type="button" class="dcb" data-m="1" aria-label="下个月"'+(vm>=hi?' disabled':'')+'>›</button></div><div class="dcg">'+'一二三四五六日'.split('').map(function(c){return '<span>'+c+'</span>'}).join('');
for(var i=0;i<wd;i++)h+='<i></i>';
for(var d=1;d<=n;d++){var k=y+'-'+z(m)+'-'+z(d),has=days.indexOf(k)>=0;h+='<button type="button" class="dcd'+(has?'':' off')+(k===cur?' on':'')+(k===t?' td':'')+'" data-d="'+k+'"'+(has?'':' disabled')+'>'+d+'</button>'}
h+='</div>'+(nav?'':'<div class="dcf"><button type="button" class="btn dcall">全部日期</button></div>');pop.innerHTML=h}
bm.addEventListener('click',function(){if(pop)return close();pop=document.createElement('div');pop.className='dcpop';pop.setAttribute('role','dialog');pop.setAttribute('aria-label','选择日期');el.appendChild(pop);vm=(cur||days[0]||dkey(Date.now())).slice(0,7);render();bm.setAttribute('aria-expanded','true');
pop.addEventListener('click',function(ev){var d=ev.target.closest('.dcd');if(d){go(d.dataset.d);return}var m=ev.target.closest('[data-m]');if(m){var y=+vm.slice(0,4),mo=+vm.slice(5)+(+m.dataset.m);if(mo<1){mo=12;y--}if(mo>12){mo=1;y++}vm=y+'-'+z(mo);render();return}if(ev.target.closest('.dcall'))go('')})});
document.addEventListener('click',function(ev){if(pop&&!el.contains(ev.target))close()});
document.addEventListener('keydown',function(ev){if(ev.key==='Escape'&&pop){close();bm.focus()}});
if(!nav){bp.addEventListener('click',function(){var i=days.indexOf(cur);go(cur?days[i+1]:days[0])});bn.addEventListener('click',function(){var i=days.indexOf(cur);go(i>0?days[i-1]:'')})}
show();return{set:function(k){cur=DRE.test(k||'')&&days.indexOf(k)>=0?k:'';show()}}}
var DCT=$('.dctl');if(DCT&&DCT.dataset.mode==='nav')dinit(DCT,null);
var M=null,feed=$('#feed'),more=$('#more'),cnt=$('#cnt'),STEP=36;
/* 通用领域过滤（资讯/趋势/账号榜） */
function domFilter(dom){$$('[data-dom]').forEach(function(el){if(el.tagName==='BUTTON')return;el.hidden=dom!=='all'&&el.dataset.dom!==dom})}
/* ===== 热帖 ===== */
if(feed&&feed.dataset.src){var H=null,HD=null,st={dom:'all',sort:'t',day:'',_def:'t'},list=[],shown=+feed.dataset.pre,wait=[],dwait=[],hdc=DCT?dinit(DCT,function(k){st.day=k;apply()}):null;
function load(f){if(H)return f();wait.push(f);if(wait.length>1)return;fetch(feed.dataset.src).then(function(r){return r.json()}).then(function(j){H=j;H.P.forEach(function(p){var u=H.U[p[10]];TXT[p[0]]=p[2]+'\n— '+u[1]+' (@'+u[2]+')\n'+xurl(p,u[2])});wait.splice(0).forEach(function(f){f()})})}
function dload(f){if(HD)return f();dwait.push(f);if(dwait.length>1)return;fetch(feed.dataset.dsrc).then(function(r){return r.json()}).then(function(j){HD=j;HD.P.forEach(function(p){var u=H.U[p[10]];TXT[p[0]]=p[2]+'\n— '+u[1]+' (@'+u[2]+')\n'+xurl(p,u[2])});dwait.splice(0).forEach(function(f){f()})})}
function ready(f){load(function(){if(st.day)dload(f);else f()})}
function curlist(){if(!st.day)return H.L[st.dom][st.sort].map(function(i){return H.P[i]});var L=(HD.D[st.day]||[]).map(function(i){return HD.P[i]}).filter(function(p){return st.dom==='all'||H.U[p[10]][6].split(',').indexOf(st.dom)>=0});if(st.sort==='t')L.sort(function(a,b){return a[1]<b[1]?1:a[1]>b[1]?-1:0});else L.sort(function(a,b){return b[8]-a[8]});return L}
function lab(){var v=hq&&hq.value.trim();return (v?'「'+v+'」匹配 ':'')+(st.day?dfull(st.day)+' · '+(st.sort==='t'?'按时间':'按热度'):({w:'近一周',g:'全局',t:'最新'})[st.sort])+' '+list.length+' 条 · 每人最多 3 条'}
var hq=$('#hq');function render(reset){list=curlist();var v=hq&&hq.value.trim().toLowerCase();if(v)list=list.filter(function(p){var u=H.U[p[10]];return (p[2]+' '+u[1]+' '+u[2]).toLowerCase().indexOf(v)>=0});if(reset){feed.innerHTML='';shown=0}feed.classList.toggle('tl',st.sort==='t');var ld=reset?null:lastSep(feed),h='',end=Math.min(list.length,shown+STEP);for(var k=shown;k<end;k++){var p=list[k],u=H.U[p[10]];if(st.sort==='t'){var dk=dkey(p[1]);if(dk!==ld){h+=sep(dk);ld=dk}}h+=card(p,u,st.dom==='all'?u[3]:st.dom,'',0)}feed.insertAdjacentHTML('beforeend',h);shown=end;
if(!list.length)feed.innerHTML='<div class="empty">这个范围内暂无帖子</div>';more.hidden=shown>=list.length;more.textContent='再显示 '+Math.min(STEP,list.length-shown)+' 条（已显示 '+shown+' / '+list.length+'）';cnt.textContent=lab();fixEx(feed)}
function apply(){seg('data-sort',st.sort);seg('data-dom',st.dom);hset(st);ready(function(){render(true)})}
$$('[data-sort]').forEach(function(b){b.addEventListener('click',function(){st.sort=b.dataset.sort;apply()})});
$$('button[data-dom]').forEach(function(b){b.addEventListener('click',function(){st.dom=b.dataset.dom;apply()})});
more.addEventListener('click',function(){ready(function(){render(false)})});if(hq){var ht;hq.addEventListener('input',function(){clearTimeout(ht);ht=setTimeout(function(){ready(function(){render(true)})},150)})}
var h0=hget();if(h0.dom||h0.sort||h0.day){st.dom=H0ok(h0.dom,['all','ai','money','growth'],'all');st.sort=H0ok(h0.sort,['w','g','t'],'t');if(DRE.test(h0.day||'')&&hdc){st.day=h0.day;hdc.set(st.day);if(!DCT.dataset.days.split(',').some(function(x){return x===st.day}))st.day=''}apply()}else{fixEx(feed);more.textContent='再显示 '+STEP+' 条'}
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
/* ===== 资讯：工具条筛选（精选/全部/来源 + 日期），桌面右侧阅读窗格、手机行内展开（正文 JSON 按需加载，生成器已转义） ===== */
if(ng){var NB=null,nw=[],wide=matchMedia('(min-width:1001px)');function nload(f){if(NB)return f&&f();if(f)nw.push(f);if(nw.length>1||nload.busy)return;nload.busy=1;fetch(ng.dataset.body).then(function(r){return r.json()}).then(function(B){NB=B;nw.splice(0).forEach(function(f){f()})})}
var cur=null,nst={src:'top',day:''};
/* 首条已在 HTML 里静态渲染（避免窗格成为晚渲染的最大元素）；窄屏不用窗格，去掉选中态 */
(function(){var f=$('#ntop .nr.sel');if(!f)return;if(wide.matches)cur=f;else f.classList.remove('sel')})();
function psel(li){if(cur)cur.classList.remove('sel');cur=li;if(li)li.classList.add('sel')}
function pempty(){psel(null);$('#nptitle').textContent='阅读窗格';$('#npmeta').innerHTML='';$('#npbody').innerHTML='<p class="nph">这个范围内没有资讯。</p>'}
function popen(li){psel(li);$('#nptitle').textContent=$('.nt2',li).textContent;$('#npmeta').innerHTML=$('.nrm',li).innerHTML;var bd=$('#npbody');bd.innerHTML='<p class="nph">加载中…</p>';
nload(function(){if(cur!==li)return;var x=NB[+li.dataset.i];if(typeof x==='string')bd.innerHTML=x;bd.scrollTop=0})}
function nopen(li,on){var bd=$('.nrb',li),b=$('.nrh',li);if(on===undefined)on=bd.hidden;if(on&&!bd.dataset.ok){nload(function(){var x=NB[+li.dataset.i];if(typeof x==='string'){bd.innerHTML=x;bd.dataset.ok=1}})}bd.hidden=!on;li.classList.toggle('open',on);b.setAttribute('aria-expanded',on)}
function nact(li){if(wide.matches)popen(li);else nopen(li)}
function autosel(){if(!wide.matches)return;if(cur&&cur.offsetParent!==null)return;var f=$$('.nr',nst.src==='top'?$('#ntop'):$('#nall')).filter(function(li){return li.offsetParent!==null})[0];if(f)popen(f);else pempty()}
ng.addEventListener('click',function(ev){var b=ev.target.closest('.nrh');if(b)nact(b.closest('.nr'))});
var ndc=DCT?dinit(DCT,function(k){nst.day=k;nsr()}):null;
function nsr(){var s=nst.src,dk=nst.day;if(dk&&s==='top')s=nst.src='all';seg('data-src',s);var top=s==='top';$('#ntop').hidden=!top;$('#nall').hidden=top;var n=0;
if(!top){$$('#nall .ndg').forEach(function(g){var c=0,gd=!dk||g.dataset.d===dk;$$('.nr',g).forEach(function(li){var ok=gd&&(s==='all'||li.dataset.s===s);li.hidden=!ok;if(ok)c++});g.hidden=!c;n+=c})}else n=1;$('#nempty').hidden=n>0;hset({src:s==='top'?'':s==='all'?'a':s,day:dk});autosel()}
$$('[data-src]').forEach(function(b){b.addEventListener('click',function(){nst.src=b.dataset.src;if(nst.src==='top'){nst.day='';if(ndc)ndc.set('')}nsr()})});
$('#nmore').addEventListener('click',function(){nst.src='all';nsr();$('#nall').scrollIntoView({block:'start'})});
/* 阅读窗格高度 = 视口剩余高度（页面顶部时从工具条下方算起，吸顶后从顶栏下方算起），始终不超出视口 */
function nph(){if(!wide.matches)return;var r=ng.getBoundingClientRect(),t=Math.max(r.top,$('.top').offsetHeight+12);ng.style.setProperty('--nph',Math.max(360,innerHeight-t-16)+'px')}
addEventListener('scroll',nph,{passive:true});addEventListener('resize',nph);nph();
wide.addEventListener?wide.addEventListener('change',function(){nph();autosel()}):wide.addListener(function(){nph();autosel()});
var s0=hget();if(s0.src&&/^(a|h|d|s|x)$/.test(s0.src))nst.src=s0.src==='a'?'all':s0.src;if(DRE.test(s0.day||'')&&ndc&&DCT.dataset.days.split(',').indexOf(s0.day)>=0){nst.day=s0.day;ndc.set(s0.day);if(nst.src==='top')nst.src='all'}
if(nst.src!=='top'||nst.day)nsr();
if(s0.n&&/^\d+$/.test(s0.n)){var li=$('#ntop .nr[data-i="'+s0.n+'"]');if(!li){nst.src='all';nsr();li=$('#nall .nr[data-i="'+s0.n+'"]')}if(li){nact(li);li.classList.add('hl');setTimeout(function(){li.scrollIntoView({block:'center'})},60)}}
autosel();
addEventListener('load',function(){(window.requestIdleCallback||function(f){setTimeout(f,2000)})(function(){nload()},{timeout:5000})})}
if(!ag&&!(feed)&&$('button[data-dom]')){var ns={dom:'all'};function nr(){seg('data-dom',ns.dom);domFilter(ns.dom);hset(ns)}
$$('button[data-dom]').forEach(function(b){b.addEventListener('click',function(){ns.dom=b.dataset.dom;nr()})});var n0=hget();if(n0.dom){ns.dom=H0ok(n0.dom,['all','ai','money','growth'],'all');nr()}}
/* ===== 个人页 ===== */
var mt=$('#tw-meta');if(!mt)return;M=JSON.parse(mt.textContent);var D=null,ps={sort:feed.dataset.mode,day:'',_def:feed.dataset.mode},pdc=DCT?dinit(DCT,function(k){ps.day=k;hset(ps);pload(prun)}):null,pl=[],pshown=+feed.dataset.pre,q=$('#q'),all=$('#alll'),first=true;
var who=null;
function prun(){if(!D)return;var v=q.value.trim().toLowerCase(),A=all&&all.checked,base=0;pl=[];
D.forEach(function(r,i){if(!r[10]&&!A)return;if(ps.sort==='w'&&r[1]<M.week)return;if(ps.day&&dkey(r[1])!==ps.day)return;base++;if(v&&r.lc.indexOf(v)<0)return;pl.push(i)});
if(ps.sort!=='t')pl.sort(function(a,b){return D[b][8]-D[a][8]});
feed.innerHTML='';pshown=0;ppage();cnt.textContent=(ps.day?dfull(ps.day):({w:'近一周',g:'全局',t:'全部'})[ps.sort])+(v?' 匹配 '+pl.length+' / '+base:' '+base)+' 条';if(!pl.length)feed.innerHTML='<div class="empty">'+(ps.day?'这一天没有匹配的推文':ps.sort==='w'?'近一周没有新帖，试试「全局热度」或「时间」':'没有匹配的推文')+'</div>'}
function ppage(){feed.classList.toggle('tl',ps.sort==='t');var ld=pshown?lastSep(feed):null,h='',end=Math.min(pl.length,pshown+24);for(var k=pshown;k<end;k++){var r=D[pl[k]];if(ps.sort==='t'){var dk=dkey(r[1]);if(dk!==ld){h+=sep(dk);ld=dk}}h+=card(r,null,M.dom,'../',M.week)}feed.insertAdjacentHTML('beforeend',h);pshown=end;more.hidden=pshown>=pl.length;more.textContent='再显示 '+Math.min(24,pl.length-pshown)+' 条（已显示 '+pshown+' / '+pl.length+'）';fixEx(feed)}
function pload(f){if(D)return f();fetch(M.src).then(function(r){return r.json()}).then(function(d){D=d;D.forEach(function(r){r.lc=r[2].toLowerCase();TXT[r[0]]=r[2]+'\n— '+M.name+' (@'+M.handle+')\n'+xurl(r,M.handle)});f()})}
$$('[data-sort]').forEach(function(b){b.addEventListener('click',function(){ps.sort=b.dataset.sort;seg('data-sort',ps.sort);hset(ps);pload(prun)})});
var tm;q.addEventListener('input',function(){clearTimeout(tm);tm=setTimeout(function(){pload(prun)},120)});if(all)all.addEventListener('change',function(){pload(prun)});
more.addEventListener('click',function(){pload(ppage)});fixEx(feed);
var p0=hget();pload(function(){if(DRE.test(p0.day||'')&&DCT.dataset.days.split(',').indexOf(p0.day)>=0){ps.day=p0.day;pdc.set(p0.day);if(p0.sort&&/^[wgt]$/.test(p0.sort)){ps.sort=p0.sort;seg('data-sort',ps.sort)}prun()}else if(p0.sort&&/^[wgt]$/.test(p0.sort)){ps.sort=p0.sort;seg('data-sort',ps.sort);prun()}else{pl=[];D.forEach(function(r,i){if(r[10]&&(ps.sort!=='w'||r[1]>=M.week))pl.push(i)});if(ps.sort!=='t')pl.sort(function(a,b){return D[b][8]-D[a][8]});more.hidden=pshown>=pl.length;more.textContent='再显示 '+Math.min(24,pl.length-pshown)+' 条（已显示 '+pshown+' / '+pl.length+'）'}})})();
