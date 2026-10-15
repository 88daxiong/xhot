/* XHOT v15 core：主题/密度 · 工具 · 相对时间 · 日期控件 · 复制/展开/译文 · 过滤 · ⌘K 搜索 · 新/已读（仅本机 localStorage） */
(function(){var d=document.documentElement,mq=matchMedia('(prefers-color-scheme: dark)');
var $=function(s,r){return(r||document).querySelector(s)},$$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
var P=d.dataset.p||'',LS={get:function(k){try{return localStorage.getItem(k)}catch(e){return null}},set:function(k,v){try{localStorage.setItem(k,v)}catch(e){}}};
function sync(){$$('[data-set-theme]').forEach(function(b){var on=b.dataset.setTheme===d.dataset.pref;b.classList.toggle('on',on);b.setAttribute('aria-pressed',on)})}
function theme(){var p=d.dataset.pref;d.dataset.theme=p==='auto'?(mq.matches?'dark':'light'):p}
$$('[data-set-theme]').forEach(function(b){b.addEventListener('click',function(){d.dataset.pref=b.dataset.setTheme;LS.set('xhot-theme',b.dataset.setTheme);theme();sync()})});
(mq.addEventListener?mq.addEventListener('change',theme):mq.addListener(theme));sync();
var db=$('[data-density]');if(db){var dsy=function(){var c=d.dataset.density==='compact';db.textContent=c?'舒适':'紧凑';db.setAttribute('aria-pressed',c)};dsy();db.addEventListener('click',function(){var c=d.dataset.density==='compact';if(c)d.removeAttribute('data-density');else d.dataset.density='compact';LS.set('xhot-density',c?'comfortable':'compact');dsy()})}
var hxb=$('.hxb'),hx=$('#hx');if(hxb){hxb.addEventListener('click',function(ev){ev.stopPropagation();var o=hx.classList.toggle('open');hxb.setAttribute('aria-expanded',o)});document.addEventListener('click',function(ev){if(hx.classList.contains('open')&&!hx.contains(ev.target)){hx.classList.remove('open');hxb.setAttribute('aria-expanded','false')}})}
function seg(attr,v){$$('['+attr+']').forEach(function(x){var on=x.getAttribute(attr)===v;x.classList.toggle('on',on);x.setAttribute('aria-pressed',on)})}
function hget(){var o={};location.hash.slice(1).split('&').forEach(function(kv){var p=kv.split('=');if(p[0])o[p[0]]=decodeURIComponent(p[1]||'')});return o}
function hset(o){var s=Object.keys(o).filter(function(k){return o[k]&&o[k]!=='all'&&!(k==='sort'&&o[k]===o._def)&&k[0]!=='_'}).map(function(k){return k+'='+encodeURIComponent(o[k])}).join('&');history.replaceState(null,'',s?'#'+s:location.pathname+location.search)}
function fmt(n){if(n>=1e8)return(n/1e8).toFixed(2)+'亿';if(n>=1e4)return(n/1e4).toFixed(1)+'万';return n.toLocaleString('en-US')}
function esc(s){return String(s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function safeUrl(u){u=String(u==null?'':u).trim();return /^https?:\/\//i.test(u)?esc(u):'#'}
function lnk(s){return esc(s).replace(/https?:\/\/[^\s<&"']+/g,function(u){return '<a href="'+u+'" target="_blank" rel="noopener noreferrer">'+u.replace(/^https?:\/\//,'')+'</a>'})}
var df=new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',hour:'2-digit',minute:'2-digit',hour12:false}),dkf=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}),WD='日一二三四五六';
function dkey(s){return dkf.format(new Date(s))}
function hm(s){return df.format(new Date(s)).replace(/^24/,'00')}
function dsub(k){return (+k.slice(5,7))+'月'+(+k.slice(8))+'日 周'+WD[new Date(k+'T12:00:00+08:00').getUTCDay()]}
function dlab(k){return k===dkey(Date.now())?'今天':k===dkey(Date.now()-864e5)?'昨天':(+k.slice(5,7))+'月'+(+k.slice(8))+'日'}
function dchip(k){return dlab(k)+' · '+dsub(k).split(' ')[1]}
function dfull(k){var l=dlab(k);return (l==='今天'||l==='昨天')?l+' · '+(+k.slice(5,7))+'月'+(+k.slice(8))+'日':dsub(k)}
function rel(s){var m=(Date.now()-new Date(s))/6e4;if(m<1)return '刚刚';if(m<60)return Math.floor(m)+' 分钟前';if(m<1440)return Math.floor(m/60)+' 小时前';var k=dkey(s);return k===dkey(Date.now()-864e5)?'昨天':k.slice(5)}
function tmh(s){return '<time class="tm" datetime="'+esc(s)+'"><b>'+hm(s)+'</b><span class="rl">'+rel(s)+'</span></time>'}
function sep(k){var l=dlab(k),sb=dsub(k);if(l!=='今天'&&l!=='昨天')sb=sb.split(' ')[1];return '<div class="dsep" data-d="'+esc(k)+'"><b>'+l+'</b><span>'+sb+'</span></div>'}
function relabel(root){$$('details.fr[data-t]',root).forEach(function(x){var h=(Date.now()-Date.parse(x.dataset.t))/36e5,c=h>48?'bad':h>26?'warn':'ok';x.classList.remove('ok','warn','bad');x.classList.add(c)});$$('.dtag[data-d]',root).forEach(function(x){x.textContent=dchip(x.dataset.d)});$$('.dsep[data-d]',root).forEach(function(x){var b=$('b',x);if(b)b.textContent=dlab(x.dataset.d)});$$('.ddl[data-d]',root).forEach(function(x){x.textContent=dfull(x.dataset.d)});$$('time.tm[datetime]',root).forEach(function(t){var r=$('.rl',t);if(r)r.textContent=rel(t.getAttribute('datetime'))})}
document.addEventListener('error',function(ev){var t=ev.target;if(t&&t.tagName==='IMG'&&t.parentNode&&t.parentNode.classList&&t.parentNode.classList.contains('av'))t.remove()},true);
function toph(){var t=$('.top');if(t)d.style.setProperty('--toph',t.offsetHeight+'px')}toph();addEventListener('resize',toph);
document.addEventListener('click',function(ev){$$('details.fr[open]').forEach(function(x){if(!x.contains(ev.target))x.open=false})});
/* 悬停预取同站页面 */
var pf={};['mouseover','touchstart','focusin'].forEach(function(e){document.addEventListener(e,function(ev){var a=ev.target.closest&&ev.target.closest('a[href]');if(!a)return;var h=a.getAttribute('href');if(!h||pf[h]||/^https?:/.test(h)||!/\.html/.test(h))return;pf[h]=1;var l=document.createElement('link');l.rel='prefetch';l.href=h;document.head.appendChild(l)},{passive:true})});
/* 复制 */
function fb(t){var a=document.createElement('textarea');a.value=t;a.setAttribute('readonly','');a.style.cssText='position:fixed;top:-1000px;opacity:0';document.body.appendChild(a);a.select();var ok=false;try{ok=document.execCommand('copy')}catch(e){}document.body.removeChild(a);return ok}
function copy(b,t){function done(ok){b.textContent=ok?'已复制 ✓':'复制失败';b.classList.toggle('ok',ok);clearTimeout(b._t);b._t=setTimeout(function(){b.textContent=b.dataset.l||'复制摘录';b.classList.remove('ok')},1600)}
if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t).then(function(){done(true)},function(){done(fb(t))})}else done(fb(t))}
function rawt(pt){var c=pt.cloneNode(true);$$('a',c).forEach(function(a){a.replaceWith(a.getAttribute('href')||a.textContent)});return c.textContent}
function ctext(p){var op=$('.op',p),u=op?op.href:'';
if(p.classList.contains('dh')){var hn=$('.hh b',p),hs=$('.hh small',p);return rawt($('.dor .pt:not([hidden])',p))+'\n— '+(hn?hn.textContent:'')+' ('+(hs?hs.textContent:'')+')\n'+u}
var w=$('.who a',p),h=$('.who small',p),t=$('.pt',p),M=window.XM;var who=w?w.textContent+' ('+h.textContent+')':(M?M.name+' (@'+M.handle+')':$('.trh b',p)?$('.trh b',p).textContent+' ('+$('.trh small',p).textContent+')':'');return rawt(t)+'\n— '+who+'\n'+u}
/* 已读（仅本机） */
var RD={};try{(JSON.parse(LS.get('xhot-read')||'[]')).forEach(function(k){RD[k]=1})}catch(e){}
function markRead(el){var fi=el.closest&&el.closest('.fi[data-k]');if(!fi)return;var k=fi.dataset.k;if(RD[k])return;RD[k]=1;fi.classList.add('rd');var a=Object.keys(RD).slice(-400);LS.set('xhot-read',JSON.stringify(a))}
function applyRead(root){$$('.fi[data-k]',root).forEach(function(x){if(RD[x.dataset.k])x.classList.add('rd')})}
document.addEventListener('click',function(ev){var t=ev.target;
var b=t.closest('.cp');if(b){copy(b,ctext(b.closest('.post,.dh,.trw')));markRead(b);return}
var ol=t.closest('[data-ol]');if(ol){var q=ol.closest('.dh'),v=ol.dataset.ol;$$('[data-ol]',q).forEach(function(z){var on=z===ol;z.classList.toggle('on',on);z.setAttribute('aria-pressed',on)});$('.ptz',q).hidden=v!=='zh';$('.pto',q).hidden=v!=='en';var cb=$('.cp',q);if(cb){cb.dataset.l=v==='zh'?'复制译文':'复制摘录';cb.textContent=cb.dataset.l}return}
var x=t.closest('.ex');if(x){var p=x.closest('.dh'),o=p.classList.toggle('open');x.textContent=o?'收起':'展开';x.setAttribute('aria-expanded',o);var dr=$('.dor',p);if(dr)dr.hidden=!o;markRead(x);return}
if(t.closest('.op,summary,.who a,.hh,.wkh'))markRead(t)});
/* ===== 日期控件：‹ [日期 ▾] ›；state = 页内筛选（空 = 「全部」文案由 data-all 指定），nav = 跳转 ===== */
var DRE=/^\d{4}-\d\d-\d\d$/;
function dinit(el,cb){var days=(el.dataset.days||'').split(',').filter(function(x){return DRE.test(x)}),nav=el.dataset.mode==='nav',cur=DRE.test(el.dataset.cur||'')?el.dataset.cur:'',alll=el.dataset.all||'全部日期',lab=$('.dcl',el),bp=$('.dcp',el),bn=$('.dcn',el),bm=$('.dcm',el),pop=null,vm='';
function z(n){return n<10?'0'+n:''+n}
function show(){lab.textContent=cur?dfull(cur):(nav?'选择日期':alll);if(!nav){var i=days.indexOf(cur);bp.disabled=cur?i<0||i>=days.length-1:!days.length;bn.disabled=!cur}}
function close(){if(pop){pop.remove();pop=null;bm.setAttribute('aria-expanded','false')}}
function go(k){if(nav){if(k&&k!==cur&&days.indexOf(k)>=0)location.href=el.dataset.href.replace('{d}',k);return}cur=k;show();close();if(cb)cb(k)}
function render(){var y=+vm.slice(0,4),m=+vm.slice(5),wd=(new Date(Date.UTC(y,m-1,1)).getUTCDay()+6)%7,n=new Date(Date.UTC(y,m,0)).getUTCDate(),t=dkey(Date.now()),lo=days.length?days[days.length-1].slice(0,7):vm,hi=days.length?days[0].slice(0,7):vm;
var h='<div class="dch"><button type="button" class="dcb" data-m="-1" aria-label="上个月"'+(vm<=lo?' disabled':'')+'>‹</button><b>'+y+'年'+m+'月</b><button type="button" class="dcb" data-m="1" aria-label="下个月"'+(vm>=hi?' disabled':'')+'>›</button></div><div class="dcg">'+'一二三四五六日'.split('').map(function(c){return '<span>'+c+'</span>'}).join('');
for(var i=0;i<wd;i++)h+='<i></i>';
for(var dd=1;dd<=n;dd++){var k=y+'-'+z(m)+'-'+z(dd),has=days.indexOf(k)>=0;h+='<button type="button" class="dcd'+(has?'':' off')+(k===cur?' on':'')+(k===t?' td':'')+'" data-d="'+k+'"'+(has?'':' disabled')+'>'+dd+'</button>'}
h+='</div>'+(nav?'':'<div class="dcf"><button type="button" class="btn dcall">'+esc(alll)+'</button></div>');pop.innerHTML=h}
bm.addEventListener('click',function(){if(pop)return close();pop=document.createElement('div');pop.className='dcpop';pop.setAttribute('role','dialog');pop.setAttribute('aria-label','选择日期');el.appendChild(pop);vm=(cur||days[0]||dkey(Date.now())).slice(0,7);render();bm.setAttribute('aria-expanded','true');
pop.addEventListener('click',function(ev){var x=ev.target.closest('.dcd');if(x){go(x.dataset.d);return}var m=ev.target.closest('[data-m]');if(m){var y=+vm.slice(0,4),mo=+vm.slice(5)+(+m.dataset.m);if(mo<1){mo=12;y--}if(mo>12){mo=1;y++}vm=y+'-'+z(mo);render();return}if(ev.target.closest('.dcall'))go('')})});
document.addEventListener('click',function(ev){if(pop&&!el.contains(ev.target))close()});
document.addEventListener('keydown',function(ev){if(ev.key==='Escape'&&pop){close();bm.focus()}});
if(!nav){bp.addEventListener('click',function(){var i=days.indexOf(cur);go(cur?days[i+1]:days[0])});bn.addEventListener('click',function(){var i=days.indexOf(cur);go(i>0?days[i-1]:'')})}
show();return{set:function(k){cur=DRE.test(k||'')&&days.indexOf(k)>=0?k:'';show()}}}
var DCT=$('.dctl');if(DCT&&DCT.dataset.mode==='nav')dinit(DCT,null);
/* ===== 通用过滤：[data-fl] 容器里的 .fi，按 领域按钮 [data-dom]、标签按钮 [data-ftag]；人物目录 data-fl="p" 另有排序与搜索 ===== */
function oneOf(v,a,dv){return a.indexOf(v)>=0?v:dv}
$$('[data-fl]').forEach(function(F){var p=F.dataset.fl==='p',sc=p?document:F.closest('section')||document,st={dom:'all',tag:'all',sort:p?'f':'',q:''},kids=$$('.fi',F),empty=$('.empty',F.parentNode),aq=$('#aq'),ac=$('#acnt');
function run(){seg('data-dom',st.dom);if(!p)$$('[data-ftag]',sc).forEach(function(b){var on=b.dataset.ftag===st.tag;b.classList.toggle('on',on);b.setAttribute('aria-pressed',on)});
if(p){seg('data-asort',st.sort);var k=st.sort;var fr=document.createDocumentFragment();kids.slice().sort(function(a,b){return b.dataset[k]-a.dataset[k]}).forEach(function(x){fr.appendChild(x)});F.appendChild(fr)}
var n=0;kids.forEach(function(x){var ok=(st.dom==='all'||(x.dataset.dom||'').split(' ').indexOf(st.dom)>=0)&&(st.tag==='all'||(x.dataset.tags||'').split(' ').indexOf(st.tag)>=0)&&(!st.q||(x.dataset.q||'').indexOf(st.q)>=0);x.hidden=!ok;if(ok)n++});
if(empty)empty.hidden=n>0;if(p){if(ac)ac.textContent=n+' 人';$$('.wkg .fi').forEach(function(x){x.hidden=st.dom!=='all'&&(x.dataset.dom||'').split(' ').indexOf(st.dom)<0});hset({dom:st.dom,sort:st.sort,_def:'f'})}else hset({dom:p?st.dom:'',tag:st.tag==='all'?'':st.tag})}
$$('button[data-dom]',sc).forEach(function(b){b.addEventListener('click',function(){st.dom=b.dataset.dom;run()})});
$$('[data-ftag]',sc).forEach(function(b){b.addEventListener('click',function(){st.tag=b.dataset.ftag;run()})});
if(p){$$('[data-asort]').forEach(function(b){b.addEventListener('click',function(){st.sort=b.dataset.asort;run()})});if(aq)aq.addEventListener('input',function(){st.q=aq.value.trim().toLowerCase();run()})}
var h0=hget();if(p){if(h0.dom||h0.sort){st.dom=oneOf(h0.dom,['all','ai','money','growth'],'all');st.sort=oneOf(h0.sort,['f','w','d'],'f');run()}}else if(h0.tag&&sc.querySelector('[data-ftag="'+h0.tag.replace(/[^a-z]/g,'')+'"]')){st.tag=h0.tag.replace(/[^a-z]/g,'');run()}});
/* ===== 新 / 已读：只存在本机 localStorage，没有任何上报 ===== */
(function(){var prev=0;try{var s=sessionStorage.getItem('xhot-prev');if(s===null){s=LS.get('xhot-last')||'0';sessionStorage.setItem('xhot-prev',s)}prev=+s}catch(e){}
if(prev){var n=0;$$('.fi[data-ts]').forEach(function(x){if(new Date(x.dataset.ts).getTime()>prev){x.classList.add('isnew');if(x.closest('#daily'))n++}});var nc=$('#newc');if(nc&&n){nc.textContent='· 自上次访问新增 '+n+' 条（标「新」）';nc.hidden=false}}
setTimeout(function(){LS.set('xhot-last',String(Date.now()))},4000);applyRead(document)})();
relabel(document);
/* 同页内只改 #hash 的跳转（如 ⌘K 选了当前页的日期 / 标签）：重新载入以应用；筛选自己用 replaceState，不会触发 */
addEventListener('hashchange',function(){if(/^#(day|tag|dom|sort)=/.test(location.hash))location.reload()});
/* ===== ⌘K 搜索 ===== */
var SJ=null,SJP=null;
function people(){if(SJP)return SJP;return SJP=fetch(P+'assets/'+d.dataset.sj).then(function(r){return r.json()}).then(function(j){SJ=j;j.M={};j.p.forEach(function(x){j.M[x[0]]=x});return j})}
var kp=null,kpi,kpl,items=[],act=0,lastF=null,pq=0;
var PAGES=[['今日','index.html','每日 10 分钟'],['AI','d/ai.html','领域'],['搞钱','d/money.html','领域'],['成长','d/growth.html','领域'],['全部归档','d/all.html','按天 / 领域 / 重要度'],['人物','people.html','本周要点'],['资讯','news.html','AIHOT / X 新闻'],['趋势','trends.html','话题涨跌 · GitHub']];
function hl(t,q){if(!q)return esc(t);var i=t.toLowerCase().indexOf(q.toLowerCase());if(i<0)return esc(t);return esc(t.slice(0,i))+'<mark>'+esc(t.slice(i,i+q.length))+'</mark>'+esc(t.slice(i+q.length))}
function row(t,s,h,ext,k){return {t:t,s:s,h:h,ext:ext,k:k||''}}
function build(){kp=document.createElement('div');kp.className='kp';kp.hidden=true;kp.innerHTML='<div class="kpb" role="dialog" aria-modal="true" aria-label="搜索"><input class="kpi" type="search" placeholder="搜索人物、标签、话题、日期，或在帖子摘录里查找…" aria-label="搜索" autocomplete="off" spellcheck="false"><ul class="kpl" role="listbox" aria-label="结果"></ul><div class="kpf"><span><kbd>↑</kbd><kbd>↓</kbd> 选择</span><span><kbd>↵</kbd> 打开</span><span><kbd>Esc</kbd> 关闭</span></div></div>';document.body.appendChild(kp);kpi=$('.kpi',kp);kpl=$('.kpl',kp);
kp.addEventListener('mousedown',function(ev){if(ev.target===kp)kclose()});kpl.addEventListener('click',function(ev){var li=ev.target.closest('li[data-i]');if(li)pick(+li.dataset.i)});kpl.addEventListener('mousemove',function(ev){var li=ev.target.closest('li[data-i]');if(li&&+li.dataset.i!==act){act=+li.dataset.i;mark()}});
var comp=false;kpi.addEventListener('compositionstart',function(){comp=true});kpi.addEventListener('compositionend',function(){comp=false;act=0;query(kpi.value.trim())});
kpi.addEventListener('input',function(){if(comp)return;act=0;query(kpi.value.trim())});
kpi.addEventListener('keydown',function(ev){if(ev.isComposing||ev.keyCode===229)return;if(ev.key==='ArrowDown'){ev.preventDefault();act=Math.min(items.length-1,act+1);mark()}else if(ev.key==='ArrowUp'){ev.preventDefault();act=Math.max(0,act-1);mark()}else if(ev.key==='Enter'){ev.preventDefault();pick(act)}else if(ev.key==='Escape'){kclose()}else if(ev.key==='Tab'){ev.preventDefault()}})}
function mark(){$$('li[data-i]',kpl).forEach(function(li){var on=+li.dataset.i===act;li.classList.toggle('on',on);li.setAttribute('aria-selected',on);if(on)li.scrollIntoView({block:'nearest'})})}
function paint(q,note){var h='',g='',i=0;items.forEach(function(it){if(it.g&&it.g!==g){g=it.g;h+='<li class="kg" role="presentation">'+esc(g)+'</li>'}h+='<li role="option" data-i="'+i+'" aria-selected="false"><b>'+it.t+'</b><span>'+it.s+'</span><i>'+(it.ext?'↗':'↵')+'</i></li>';i++});
if(note)h+='<li class="kn" role="presentation">'+note+'</li>';kpl.innerHTML=h||'<li class="kn" role="presentation">没有匹配项</li>';mark()}
function mk(arr,g){arr.forEach(function(x){x.g=g});return arr}
function nz(t){return String(t).toLowerCase().normalize('NFKC')}
function query(q){var ql=nz(q),TS=ql.split(/\s+/).filter(Boolean);function hit(h){h=nz(h);return TS.every(function(t){return h.indexOf(t)>=0})}if(!SJ){people().then(function(){query(kpi.value.trim())});if(!q){items=mk(PAGES.map(function(p){return row(esc(p[0]),esc(p[2]),P+p[1])}),'前往');paint('')}return}
items=[];var pp=[],tg=[],tp=[],dy=[],pg=[];
if(!q){items=mk(PAGES.map(function(p){return row(esc(p[0]),esc(p[2]),P+p[1])}),'前往');items=items.concat(mk(SJ.p.slice().sort(function(a,b){return b[7]-a[7]}).slice(0,5).map(function(x){return row(esc(x[2]),'@'+esc(x[1])+' · '+fmt(x[7])+' 粉丝',P+'p/'+x[0]+'.html')}),'热门人物'));paint('');return}
SJ.p.forEach(function(x){var n=nz(x[2]),h=nz(x[1]),sc=n===ql||h===ql?0:n.indexOf(ql)===0||h.indexOf(ql)===0?1:n.indexOf(ql)>=0||h.indexOf(ql)>=0?2:hit(x[2]+' '+x[1]+' '+(x[9]||''))?3:9;if(sc<9)pp.push([sc,-x[7],x])});pp.sort(function(a,b){return a[0]-b[0]||a[1]-b[1]});
items=mk(pp.slice(0,6).map(function(z){var x=z[2];return row(hl(x[2],q),'@'+hl(x[1],q)+' · '+fmt(x[7])+' 粉丝',P+'p/'+x[0]+'.html')}),'人物');
SJ.t.forEach(function(x){if(hit(x[1]))tg.push(row(hl(x[1],q),'标签 · 打开「'+({ai:'AI',money:'搞钱',growth:'成长'})[x[2]]+'」领域并筛选',P+'d/'+x[2]+'.html#tag='+x[0]))});items=items.concat(mk(tg.slice(0,3),'标签'));
SJ.tp.forEach(function(x){if(hit(x[0]))tp.push(row(hl(x[0],q),'话题 · '+({ai:'AI',money:'搞钱',growth:'成长'})[x[1]],P+'trends.html'))});items=items.concat(mk(tp.slice(0,3),'话题'));
var m=q.match(/^(\d{4}-)?(\d{1,2})[-\/.月](\d{1,2})日?$/);if(m){var y=m[1]?m[1].slice(0,4):String(new Date().getFullYear()),k=y+'-'+('0'+m[2]).slice(-2)+'-'+('0'+m[3]).slice(-2);if((SJ.dy||[]).indexOf(k)>=0)dy.push(row(esc(dfull(k)),'当日日报',P+'day/'+k+'.html'));else if(SJ.d.some(function(x){return x[0]===k}))dy.push(row(esc(dfull(k)),'当日全部归档（按重要度）',P+'d/all.html#day='+k))}items=items.concat(mk(dy,'日期'));
PAGES.forEach(function(p){if(hit(p[0]))pg.push(row(hl(p[0],q),esc(p[2]),P+p[1]))});items=items.concat(mk(pg,'页面'));
var gz=[];(SJ.g||[]).forEach(function(x){var u=SJ.M[x[1]]||null;if(u&&hit(x[2]+' '+u[2]+' '+u[1])&&gz.length<5)gz.push({t:hl(x[2].length>46?x[2].slice(0,46)+'…':x[2],TS[0]),s:esc(u[2])+' · '+esc(x[3])+' 日报要点',h:'https://x.com/'+encodeURIComponent(u[1])+'/status/'+encodeURIComponent(x[0]),ext:1})});items=items.concat(mk(gz,'日报要点'));
if(q.length>=2)items.push({g:'帖子',t:'在帖子摘录中搜索「'+esc(q)+'」',s:'按需读取最近 '+SJ.d.length+' 天分片，只搜摘录',h:'',k:'posts',q:q});
paint(q)}
function pick(i){var it=items[i];if(!it)return;if(it.k==='posts'){psearch(it.q);return}if(it.ext){window.open(it.h.replace(/&amp;/g,'&'),'_blank','noopener');return}kclose();location.href=it.h}
function psearch(q){var id=++pq,ql=q.toLowerCase(),days=SJ.d.slice(),hits=[],i=0;items=[];paint(q,'正在搜索帖子摘录… 0 / '+days.length);
(function next(){if(id!==pq)return;if(i>=days.length||hits.length>=30){items=mk(hits.slice(0,30),'帖子');paint(q,hits.length?'共找到 '+hits.length+(hits.length>=30?'+':'')+' 条 · 点击在 X 打开':'最近 '+days.length+' 天的摘录里没有「'+esc(q)+'」');return}
var dd=days[i++];fetch(P+'feed/'+dd[0]+'.'+dd[1]+'.json').then(function(r){return r.json()}).then(function(rows){rows.forEach(function(r){var u=SJ.M[r[10]];if(!u)return;if((r[2]+' '+u[2]+' '+u[1]).toLowerCase().indexOf(ql)>=0){var k=r[2].toLowerCase().indexOf(ql),s=Math.max(0,k-18);hits.push({t:esc(u[2])+' <small>'+dfull(dkey(r[1]))+'</small>',s:k>=0?(s?'…':'')+hl(r[2].slice(s,s+90),q):esc(r[2].slice(0,90)),h:'https://x.com/'+u[1]+'/status/'+r[0],ext:1})}});items=mk(hits.slice(0,30),'帖子');paint(q,'正在搜索… '+i+' / '+days.length);setTimeout(next,0)},function(){setTimeout(next,0)})})()}
function kopen(){if(!kp)build();lastF=document.activeElement;kp.hidden=false;document.body.classList.add('kpo');kpi.value='';act=0;query('');kpi.focus()}
function kclose(){if(!kp||kp.hidden)return;pq++;kp.hidden=true;document.body.classList.remove('kpo');if(lastF&&lastF.focus)lastF.focus()}
$$('[data-kp]').forEach(function(b){b.addEventListener('click',kopen)});
var mac=/Mac|iPhone|iPad/.test(navigator.platform||navigator.userAgent);$$('.kb kbd').forEach(function(k){k.textContent=mac?'⌘K':'Ctrl K'});
document.addEventListener('keydown',function(ev){var t=ev.target,typing=t&&(t.tagName==='INPUT'||t.tagName==='TEXTAREA'||t.isContentEditable);if((ev.metaKey||ev.ctrlKey)&&ev.key.toLowerCase()==='k'){ev.preventDefault();kp&&!kp.hidden?kclose():kopen()}else if(ev.key==='/'&&!typing&&!ev.metaKey&&!ev.ctrlKey){ev.preventDefault();kopen()}else if(ev.key==='Escape'&&kp&&!kp.hidden)kclose()});
window.XH={$:$,$$:$$,esc:esc,safeUrl:safeUrl,lnk:lnk,fmt:fmt,dkey:dkey,dlab:dlab,dchip:dchip,dsub:dsub,dfull:dfull,hm:hm,rel:rel,tmh:tmh,sep:sep,relabel:relabel,dinit:dinit,seg:seg,hget:hget,hset:hset,people:people,DRE:DRE,oneOf:oneOf,applyRead:applyRead,P:P,DCT:DCT};
})();
