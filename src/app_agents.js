/* Agent 页：榜单标签页 + 子标签筛选 + 分页（每页 9）+ 详情抽屉（桌面右侧抽屉 / 手机整页，返回键关闭）。
   详情数据 agents.json 首次打开时才加载；所有外部文本一律 textContent 渲染，不拼 HTML。 */
(function(){var R=document.querySelector('.dtp');if(!R)return;
var PG=9,d=document,P=d.documentElement.dataset.p||'',st={tab:'',tag:'all',p:{}},DJ=null,DJP=null;
function $(s,e){return(e||d).querySelector(s)}function $$(s,e){return[].slice.call((e||d).querySelectorAll(s))}
var tabs=$$('.dtabs [data-tab]',R),pans=$$('.dtpan',R),chips=$$('[data-ftag]',R);
var TAGS=chips.map(function(b){return b.dataset.ftag}),TABS=tabs.map(function(b){return b.dataset.tab});
function hget(){var o={};location.hash.replace(/^#/,'').split('&').forEach(function(kv){var p=kv.split('=');if(p[0])o[p[0]]=decodeURIComponent(p[1]||'')});return o}
function hset(){var a=[];if(st.tab!==TABS[0])a.push('tab='+st.tab);if(st.tag!=='all')a.push('tag='+st.tag);var pg=st.p[st.tab]||1;if(pg>1)a.push('p='+pg);var h=a.length?'#'+a.join('&'):'';if(h!==location.hash)history.replaceState(history.state,'',h||location.pathname+location.search)}
function mk(t,c,txt){var e=d.createElement(t);if(c)e.className=c;if(txt!=null)e.textContent=txt;return e}
function run(focusPager){
 tabs.forEach(function(b){var on=b.dataset.tab===st.tab;b.classList.toggle('on',on);b.setAttribute('aria-selected',on);b.tabIndex=on?0:-1});
 chips.forEach(function(b){var on=b.dataset.ftag===st.tag;b.classList.toggle('on',on);b.setAttribute('aria-pressed',on)});
 pans.forEach(function(pn){var on=pn.id===st.tab;pn.hidden=!on;if(!on)return;
  var cs=$$('.dcard',pn),ok=cs.filter(function(c){return st.tag==='all'||(c.dataset.tags||'').split(' ').indexOf(st.tag)>=0});
  var n=Math.max(1,Math.ceil(ok.length/PG)),pg=Math.min(Math.max(1,st.p[st.tab]||1),n);st.p[st.tab]=pg;
  cs.forEach(function(c){c.hidden=true});ok.slice((pg-1)*PG,pg*PG).forEach(function(c,i){c.hidden=false;var rk=$('.rk',c);if(rk)rk.textContent=(pg-1)*PG+i+1});
  var em=$('.empty',pn);if(em)em.hidden=ok.length>0;
  var nv=$('.dpg',pn);nv.textContent='';if(n>1){
   var add=function(lbl,to,cur,dis,aria){var b=mk('button',cur?'on':'',lbl);b.type='button';if(cur)b.setAttribute('aria-current','page');if(aria)b.setAttribute('aria-label',aria);if(dis)b.disabled=true;else b.dataset.pg=to;nv.appendChild(b)};
   add('‹ 上一页',pg-1,false,pg<=1,'上一页');for(var i=1;i<=n;i++)add(String(i),i,i===pg,false,'第 '+i+' 页');add('下一页 ›',pg+1,false,pg>=n,'下一页');
   var s=mk('span','dpn',pg+' / '+n+' 页 · '+ok.length+' 个');nv.appendChild(s)}
  if(focusPager){var f=$('button.on',nv);if(f)f.focus()}});
 hset()}
var h0=hget();st.tab=TABS.indexOf(h0.tab)>=0?h0.tab:TABS[0];st.tag=TAGS.indexOf(h0.tag)>=0?h0.tag:'all';st.p[st.tab]=Math.max(1,parseInt(h0.p,10)||1);run();
tabs.forEach(function(b,i){b.addEventListener('click',function(){st.tab=b.dataset.tab;run()});
 b.addEventListener('keydown',function(ev){var k=ev.key,j=k==='ArrowRight'?i+1:k==='ArrowLeft'?i-1:k==='Home'?0:k==='End'?tabs.length-1:-9;if(j===-9)return;ev.preventDefault();j=(j+tabs.length)%tabs.length;st.tab=tabs[j].dataset.tab;run();tabs[j].focus()})});
chips.forEach(function(b){b.addEventListener('click',function(){st.tag=b.dataset.ftag;pans.forEach(function(p){st.p[p.id]=1});run()})});
R.addEventListener('click',function(ev){var b=ev.target.closest('.dpg button[data-pg]');if(b){st.p[st.tab]=+b.dataset.pg;run(true);var pn=$('#'+st.tab);var top=pn.getBoundingClientRect().top+scrollY-120;if(scrollY>top)scrollTo(0,top);return}
 if(ev.target.closest('a'))return;var c=ev.target.closest('.dcard');if(c&&!(getSelection&&String(getSelection()).length>2))show(c)});
/* ---- 详情抽屉 ---- */
var sh=$('#dsh'),pnl=sh&&$('.dshp',sh),body=sh&&$('.dshc',sh),ttl=sh&&$('#dshT',sh),ret=null,open=false;
function data(){if(DJ)return Promise.resolve(DJ);if(DJP)return DJP;return DJP=fetch(P+'assets/'+R.dataset.dj).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(j){DJ=j;return j}).catch(function(){DJP=null;return {}})}
function fmt(n){n=+n||0;return n>=1e4?(Math.round(n/1e3)/10)+'万':String(n)}
function row(k,v){if(!v)return;var p=mk('p','dsr');p.appendChild(mk('b','',k));p.appendChild(d.createTextNode(v));body.appendChild(p)}
function fill(c,x){var k=c.dataset.k||'';body.textContent='';ttl.textContent=k;
 var zh=x?x[9]:($('.gd',c)||{}).textContent;if(zh)body.appendChild(mk('p','dsz',zh));
 body.appendChild(c.querySelector('.dtg').cloneNode(true));
 if(!x){body.appendChild(mk('p','dsl mu','正在读取详情…'));return}
 if(x[1])row('中文摘要',x[1]);
 var st2=['★ '+fmt(x[4])];if(x[5])st2.push('今日 +'+x[5]);if(x[6])st2.push('本周 +'+x[6]);if(x[7])st2.push(x[7]);if(x[8])st2.push(x[8]+' 创建');
 body.appendChild(mk('p','dss mu',st2.join(' · ')));
 if(x[2])row('项目描述',x[2]);
 if(x[0]){body.appendChild(mk('h3','','README 摘要'));body.appendChild(mk('p','dsm',x[0]))}else body.appendChild(mk('p','dsl mu','暂无 README 摘要。'));
 if(x[3]&&x[3].length){var t=mk('p','dtt');x[3].forEach(function(s){t.appendChild(mk('span','src',s))});body.appendChild(t)}
 var a=mk('a','btn dgh','在 GitHub 打开 ↗');a.href='https://github.com/'+k.split('/').map(encodeURIComponent).join('/');a.target='_blank';a.rel='noopener noreferrer';var w=mk('div','dca');w.appendChild(a);body.appendChild(w)}
function show(c){if(!sh)return;ret=c.querySelector('.dmore')||c;fill(c,DJ&&DJ[c.dataset.k]);sh.hidden=false;open=true;d.documentElement.classList.add('nlock');
 requestAnimationFrame(function(){sh.classList.add('open')});history.pushState({dsh:1},'',location.href);var x=$('.dshx',sh);(matchMedia('(max-width:1000px)').matches?$('.nback',sh):x).focus();
 data().then(function(j){if(open&&ttl.textContent===c.dataset.k)fill(c,j[c.dataset.k]||null)})}
function close(fromPop){if(!open)return;open=false;sh.classList.remove('open');d.documentElement.classList.remove('nlock');sh.hidden=true;if(!fromPop&&history.state&&history.state.dsh)history.back();if(ret&&ret.focus)ret.focus()}
if(sh){sh.addEventListener('click',function(ev){if(ev.target.closest('[data-close]'))close()});
 d.addEventListener('keydown',function(ev){if(!open)return;if(ev.key==='Escape'){ev.preventDefault();close();return}
  if(ev.key==='Tab'){var f=$$('button,a[href]',pnl).filter(function(e){return e.offsetParent!==null});if(!f.length)return;var a=f[0],z=f[f.length-1];if(ev.shiftKey&&d.activeElement===a){ev.preventDefault();z.focus()}else if(!ev.shiftKey&&d.activeElement===z){ev.preventDefault();a.focus()}}});
 addEventListener('popstate',function(){if(open)close(true)})}
})();
