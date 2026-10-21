/* XHOT v15 feed：全部归档（按天分片）+ 人物页时间线。分片只含摘录与指标，渲染前全部转义 */
(function(){var X=XH,$=X.$,$$=X.$$,esc=X.esc,fmt=X.fmt,seg=X.seg,hget=X.hget,hset=X.hset,feed=$('#feed');if(!feed)return;
var P=X.P,more=$('#more'),cnt=$('#cnt'),hq=$('#hq')||$('#q'),DCT=X.DCT,STEP=36,PERSON=!!$('#tw-meta'),M=PERSON?JSON.parse($('#tw-meta').textContent):null;window.XM=M;
var DCOL={ai:'var(--ai)',money:'var(--money)',growth:'var(--growth)'};
function card(r,who,pref){var heat='<div class="pm"><span class="heat" title="热度 = 赞 + 2×转 + 3×引用 + 评论 + 收藏">🔥 '+fmt(r.heat)+'</span>'+X.tmh(r.ts)+'</div>',u=who?who[0]:M.u,H=who?who[1]:M.handle,dom=who?who[5]:M.dom;
var hd=who?'<header><span class="av" style="--h:'+who[4]+'" aria-hidden="true">'+esc((who[2]||u).charAt(0).toUpperCase())+(who[3]?'<img src="'+pref+'assets/av/'+esc(who[3])+'" alt="" width="96" height="96" decoding="async" loading="lazy">':'')+'</span><div class="who"><a href="'+pref+'p/'+esc(u)+'.html">'+esc(who[2])+'</a><small>@'+esc(H)+'</small></div>'+heat+'</header>':'<header><span class="tag dtag" data-d="'+X.dkey(r.ts)+'">'+X.dchip(X.dkey(r.ts))+'</span><div class="who"></div>'+heat+'</header>';
var tg=(r.tags||[]).filter(function(k){return TG[k]}).map(function(k){return '<span class="tc">'+esc(TG[k])+'</span>'}).join('');
return '<article class="post fi" style="--dc:'+(DCOL[dom]||'var(--ac)')+'" data-k="'+esc(r.id)+'" data-ts="'+esc(r.ts)+'" data-tags="'+esc((r.tags||[]).join(' '))+'" data-m="'+esc([r.like,r.rt,r.reply,r.quote,r.view,r.heat].join(','))+'">'+hd+'<div class="pt'+(ptlong(r.ex)?' clp':'')+'"'+(r.en?' lang="en"':'')+'>'+X.lnk(r.ex)+'</div>'+(tg?'<div class="tcs">'+tg+'</div>':'')+'<div class="pxd" hidden></div><footer><div class="met"><span title="点赞"><i aria-hidden="true">♥</i>'+fmt(r.like)+'</span><span title="转发"><i aria-hidden="true">⇄</i>'+fmt(r.rt)+'</span><span title="评论"><i aria-hidden="true">💬</i>'+fmt(r.reply)+'</span><span title="浏览"><i aria-hidden="true">👁</i>'+fmt(r.view)+'</span></div><div class="act">'+'<button class="btn ex2" type="button" aria-expanded="false">展开</button>'+'<button class="btn cp" type="button" data-l="复制摘录">复制摘录</button><a class="btn op" href="'+X.safeUrl('https://x.com/'+H+'/status/'+r.id)+'" target="_blank" rel="noopener noreferrer">在 X 打开 ↗</a><button type="button" class="cpy" data-copy="'+X.safeUrl('https://x.com/'+H+'/status/'+r.id)+'" aria-label="复制帖子链接" title="复制帖子链接"></button></div></footer></article>'}
var TG={};
function ptlong(t){t=String(t||'');var c=(t.match(/[\u2e80-\u9fff\uac00-\ud7af\uff00-\uffef]/g)||[]).length;return c*1.8+(t.length-c)>190||(t.split('\n').length-1)>=5}
function fetchJ(u){return fetch(u).then(function(r){return r.json()})}
function norm(a,k){return a.map(function(r){return PERSON?{id:r[0],ts:r[1],ex:r[2],like:r[3],rt:r[4],reply:r[5],quote:r[6],view:r[7],heat:r[8],score:r[9],tags:r[10]?r[10].split(','):[],en:r[11],lc:r[2].toLowerCase()}:{id:r[0],ts:r[1],ex:r[2],like:r[3],rt:r[4],reply:r[5],quote:r[6],view:r[7],heat:r[8],score:r[9],u:r[10],tags:r[11]?r[11].split(','):[],en:r[12],lc:r[2].toLowerCase()}})}
var list=[],shown=0,load={};
/* ===== 个人页 ===== */
if(PERSON){var D=null,ps={sort:'t',day:''},pdc=DCT?X.dinit(DCT,function(k){ps.day=k;run()}):null,tm;
var tot=+feed.dataset.pre;if(more){more.hidden=+feed.dataset.total<=tot;more.textContent='再显示更多'}
function pload(f){if(D)return f();if(pload.w)return pload.w.push(f);pload.w=[f];Promise.all([fetchJ(M.src),Promise.resolve(M.t?{t:M.t}:X.people())]).then(function(r){D=norm(r[0]);r[1].t.forEach(function(x){TG[x[0]]=x[1]});pload.w.splice(0).forEach(function(g){g()})})}
function run(){var v=(hq.value||'').trim().toLowerCase();pload(function(){list=D.filter(function(r){return(!ps.day||X.dkey(r.ts)===ps.day)&&(!v||r.lc.indexOf(v)>=0)});if(ps.sort==='s')list=list.slice().sort(function(a,b){return b.score-a.score});feed.innerHTML='';shown=0;page();cnt.textContent=(ps.day?X.dfull(ps.day)+' ':'')+(v?'匹配 ':'共 ')+list.length+' 条摘录'+(ps.sort==='s'?' · 按重要度':'');if(!list.length)feed.innerHTML='<div class="empty">'+(v?'没有匹配的推文':'这一天没有推文')+'</div>';hset({sort:ps.sort,day:ps.day,_def:'t'})})}
function page(){var h='',end=Math.min(list.length,shown+24);for(var k=shown;k<end;k++)h+=card(list[k],null,'../');feed.insertAdjacentHTML('beforeend',h);shown=end;more.hidden=shown>=list.length;more.textContent='再显示 '+Math.min(24,list.length-shown)+' 条（已显示 '+shown+' / '+list.length+'）';X.relabel(feed);X.applyRead(feed)}
$$('[data-sort]').forEach(function(b){b.addEventListener('click',function(){ps.sort=b.dataset.sort;seg('data-sort',ps.sort);run()})});
hq.addEventListener('input',function(){clearTimeout(tm);tm=setTimeout(run,120)});
/* 首次点「再显示」：载入分片并接在 SSR 的 12 条后面；之后每次追加 24 条 */
more.addEventListener('click',function(){pload(function(){if(list===null){list=D.slice();if(ps.sort==='s')list.sort(function(a,b){return b.score-a.score});shown=feed.querySelectorAll('.post').length}page()})});
var p0=hget();if(/^[st]$/.test(p0.sort||''))ps.sort=p0.sort;seg('data-sort',ps.sort);var wantDay=X.DRE.test(p0.day||'')&&DCT&&DCT.dataset.days.split(',').indexOf(p0.day)>=0;if(wantDay){ps.day=p0.day;pdc.set(ps.day)}
list=null;if(wantDay||ps.sort==='s')run();
if(!(navigator.connection&&navigator.connection.saveData))addEventListener('load',function(){(window.requestIdleCallback||function(f){setTimeout(f,1500)})(function(){pload(function(){})},{timeout:4000})});
return}
/* ===== 全部归档 ===== */
var SJ=null,st={dom:'all',sort:'s',day:''},SH={},tmr;
fetchJ(P+'assets/pm.json').then(function(j){SJ=j;j.M={};j.p.forEach(function(x){j.M[x[0]]=x});j.t.forEach(function(x){TG[x[0]]=x[1]});init()});
function shard(dd){var k=dd[0];if(SH[k])return Promise.resolve(SH[k]);return fetchJ(P+'feed/'+k+'.json?v='+dd[1]).then(function(a){return SH[k]=norm(a)})}
function days(){var A=SJ.d;if(st.day)return A.filter(function(x){return x[0]===st.day});var t=X.dkey(Date.now()-7*864e5);return A.filter(function(x){return x[0]>=t}).slice(0,8)}
function ready(){return Promise.all(days().map(shard))}
function who(r){return SJ.M[r.u]}
function lab(v){return (v?'「'+v+'」匹配 ':'')+(st.day?X.dfull(st.day):'最近 7 天')+' · '+(st.sort==='t'?'按时间':'重要度排序'+(st.day?'':' · 每人最多 3 条'))+' · '+list.length+' 条'}
function render(reset){ready().then(function(arr){var v=(hq&&hq.value||'').trim().toLowerCase(),L=[].concat.apply([],arr).filter(function(r){var u=who(r);if(!u)return false;if(st.dom!=='all'&&u[6].split(',').indexOf(st.dom)<0)return false;return !v||(r.lc+' '+u[2].toLowerCase()+' '+u[1].toLowerCase()).indexOf(v)>=0});
if(st.sort==='t')L.sort(function(a,b){return a.ts<b.ts?1:a.ts>b.ts?-1:0});else{L.sort(function(a,b){return b.score-a.score});if(!st.day){var c={};L=L.filter(function(r){c[r.u]=(c[r.u]||0)+1;return c[r.u]<=3})}}
list=L;if(reset!==false){feed.innerHTML='';shown=0}feed.classList.toggle('tl',st.sort==='t');var ld=null,h='',end=Math.min(list.length,shown+STEP);
if(reset===false){var s=$$('.dsep',feed);ld=s.length?s[s.length-1].dataset.d:null}
for(var k=shown;k<end;k++){var r=list[k];if(st.sort==='t'){var dk=X.dkey(r.ts);if(dk!==ld){h+=X.sep(dk);ld=dk}}h+=card(r,who(r),P)}
feed.insertAdjacentHTML('beforeend',h);shown=end;if(!list.length)feed.innerHTML='<div class="empty">这个范围内暂无帖子</div>';more.hidden=shown>=list.length;more.textContent='再显示 '+Math.min(STEP,list.length-shown)+' 条（已显示 '+shown+' / '+list.length+'）';cnt.textContent=lab(v);X.relabel(feed);X.applyRead(feed)})}
function apply(){seg('data-sort',st.sort);seg('data-dom',st.dom);hset({dom:st.dom,sort:st.sort,day:st.day,_def:'s'});render(true)}
function init(){var dc=DCT?X.dinit(DCT,function(k){st.day=k;apply()}):null;
$$('[data-sort]').forEach(function(b){b.addEventListener('click',function(){st.sort=b.dataset.sort;apply()})});
$$('button[data-dom]').forEach(function(b){b.addEventListener('click',function(){st.dom=b.dataset.dom;apply()})});
more.addEventListener('click',function(){render(false)});if(hq)hq.addEventListener('input',function(){clearTimeout(tmr);tmr=setTimeout(function(){render(true)},150)});
var h0=hget();if(h0.dom||h0.sort||h0.day){st.dom=X.oneOf(h0.dom,['all','ai','money','growth'],'all');st.sort=X.oneOf(h0.sort,['s','t'],'s');if(X.DRE.test(h0.day||'')&&SJ.d.some(function(x){return x[0]===h0.day})){st.day=h0.day;dc&&dc.set(st.day)}apply()}
else if(!(navigator.connection&&navigator.connection.saveData))addEventListener('load',function(){(window.requestIdleCallback||function(f){setTimeout(f,1500)})(function(){ready()},{timeout:4000})})}
more.textContent='再显示 36 条';X.applyRead(feed);
})();
