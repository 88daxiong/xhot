(function(){var X=XH,$=X.$,$$=X.$$,seg=X.seg,hget=X.hget,hset=X.hset,dinit=X.dinit,DRE=X.DRE,DCT=X.DCT;
var ng=$('#ng');
if(ng){var NSH=+ng.dataset.nsh||10,NHH=ng.dataset.nh.split(','),NB={},NP={},wide=matchMedia('(min-width:1001px)');
function nget(i){var k=Math.floor(i/NSH),a=NB[k];return a?a[i-k*NSH]:undefined}
function nload(i,f){var k=Math.floor(i/NSH);if(NB[k])return f&&f();if(!NP[k])NP[k]=fetch(X.P+'assets/nb/'+k+'.json?v='+NHH[k]).then(function(r){if(!r.ok)throw 0;return r.json()}).then(function(B){NB[k]=B}).catch(function(){delete NP[k]});if(f)NP[k].then(function(){if(NB[k])f()})}
function npre(ev){var b=ev.target.closest&&ev.target.closest('.nrh');if(b){var li=b.closest('.nr');if(li)nload(+li.dataset.i)}}
var cur=null,nst={src:'top',day:''};
/* 首条已在 HTML 里静态渲染（避免窗格成为晚渲染的最大元素）；窄屏不用窗格，去掉选中态 */
(function(){var f=$('#ntop .nr.sel');if(!f)return;if(wide.matches)cur=f;else f.classList.remove('sel')})();
function psel(li){if(cur)cur.classList.remove('sel');cur=li;if(li)li.classList.add('sel')}

function pempty(){psel(null);$('#nptitle').textContent='阅读窗格';$('#npmeta').innerHTML='';$('#npbody').innerHTML='<p class="nph">这个范围内没有资讯。</p>'}
function pnum(li){var s=li.closest('.nsec2'),a=$$('.nr',s),n=0;for(var i=0;i<a.length;i++){var x=a[i],g=x.closest('.ndg');if(x.hidden||(g&&g.hidden))continue;n++;if(x===li)return n}return n}
function popen(li){psel(li);var n=pnum(li);$('#nptitle').textContent=$('.nt2',li).textContent;$('#npmeta').innerHTML='<span class="nn">'+(n<10?'0':'')+n+'</span>'+$('.nrm',li).innerHTML;var bd=$('#npbody');bd.scrollTop=0;
var x0=nget(+li.dataset.i);if(typeof x0==='string')bd.innerHTML=x0;else{bd.innerHTML='<p class="nph">加载中…</p>';nload(+li.dataset.i,function(){if(cur!==li)return;var x=nget(+li.dataset.i);if(typeof x==='string')bd.innerHTML=x;bd.scrollTop=0})}nsch()}
function nopen(li,on){var bd=$('.nrb',li),b=$('.nrh',li);if(on===undefined)on=bd.hidden;if(on&&!bd.dataset.ok){nload(+li.dataset.i,function(){var x=nget(+li.dataset.i);if(typeof x==='string'){bd.innerHTML=x;bd.dataset.ok=1}})}bd.hidden=!on;li.classList.toggle('open',on);b.setAttribute('aria-expanded',on)}
var sheet=$('.nside'),nb=$('#nback'),sopen=false,sret=null;
function sclose(fromPop){if(!sopen)return;sopen=false;sheet.classList.remove('open');document.documentElement.classList.remove('nlock');sheet.removeAttribute('role');sheet.removeAttribute('aria-modal');if(!fromPop&&history.state&&history.state.nsheet)history.back();if(sret){try{sret.focus({preventScroll:true})}catch(e){}if(cur){var r=cur.getBoundingClientRect();if(r.top<70||r.bottom>innerHeight)cur.scrollIntoView({block:'center'})}}}
function sshow(li){sret=li.querySelector('.nrh');popen(li);sopen=true;sheet.classList.add('open');document.documentElement.classList.add('nlock');sheet.setAttribute('role','dialog');sheet.setAttribute('aria-modal','true');history.pushState({nsheet:1},'');setTimeout(function(){if(nb)nb.focus({preventScroll:true})},30)}
if(nb)nb.addEventListener('click',function(){sclose(false)});
addEventListener('popstate',function(){if(sopen)sclose(true)});
addEventListener('keydown',function(ev){if(ev.key==='Escape'&&sopen){ev.preventDefault();sclose(false)}});
function nact(li){if(wide.matches)popen(li);else sshow(li)}
function autosel(){if(!wide.matches)return;if(cur&&cur.offsetParent!==null)return;var f=$$('.nr',nst.src==='top'?$('#ntop'):$('#nall')).filter(function(li){return li.offsetParent!==null})[0];if(f)popen(f);else pempty()}
ng.addEventListener('click',function(ev){var b=ev.target.closest('.nrh');if(b)nact(b.closest('.nr'))});
var ndc=DCT?dinit(DCT,function(k){nst.day=k;nsr()}):null;
function nsr(){var s=nst.src,dk=nst.day;if(dk&&s==='top')s=nst.src='all';seg('data-src',s);var top=s==='top';$('#ntop').hidden=!top;$('#nall').hidden=top;var n=0;
if(!top){$$('#nall .ndg').forEach(function(g){var c=0,gd=!dk||g.dataset.d===dk;$$('.nr',g).forEach(function(li){var ok=gd&&(s==='all'||li.dataset.s===s);li.hidden=!ok;if(ok)c++});g.hidden=!c;n+=c})}else n=1;$('#nempty').hidden=n>0;hset({src:s==='top'?'':s==='all'?'a':s,day:dk});autosel()}
$$('[data-src]').forEach(function(b){b.addEventListener('click',function(){nst.src=b.dataset.src;if(nst.src==='top'){nst.day='';if(ndc)ndc.set('')}nsr()})});
$('#nmore').addEventListener('click',function(){nst.src='all';nsr();$('#nall').scrollIntoView({block:'start'})});
/* 阅读窗格高度 = 视口剩余高度（页面顶部时从工具条下方算起，吸顶后从顶栏下方算起），始终不超出视口 */
var pane=$('#npane'),notch=$('#nnotch'),lastH=0,raf=0;
function nupd(){raf=0;if(!wide.matches)return;var r=ng.getBoundingClientRect(),t=Math.max(r.top,$('.top').offsetHeight+12),h=Math.max(360,Math.round(innerHeight-t-16)),ph=Math.min(h,r.height),pt=Math.min(t,r.bottom-ph),y=24,off=true;
if(cur&&cur.getClientRects().length){var c=cur.getBoundingClientRect();y=c.top+Math.min(c.height,72)/2-pt-7;off=y<14||y>ph-28;y=Math.max(14,Math.min(ph-28,y))}
if(h!==lastH){pane.style.setProperty('--nph',h+'px');lastH=h}
if(notch){notch.style.transform='translateY('+Math.round(y)+'px) rotate(45deg)';notch.classList.toggle('off',off)}}
function nsch(){if(!raf)raf=requestAnimationFrame(nupd)}
addEventListener('scroll',nsch,{passive:true});addEventListener('resize',nsch);nupd();
wide.addEventListener?wide.addEventListener('change',function(){if(sopen)sclose(false);nsch();autosel()}):wide.addListener(function(){nsch();autosel()});
var s0=hget();if(s0.src&&/^(a|h|d|s|x)$/.test(s0.src))nst.src=s0.src==='a'?'all':s0.src;if(DRE.test(s0.day||'')&&ndc&&DCT.dataset.days.split(',').indexOf(s0.day)>=0){nst.day=s0.day;ndc.set(s0.day);if(nst.src==='top')nst.src='all'}
if(nst.src!=='top'||nst.day)nsr();
if(s0.n&&/^\d+$/.test(s0.n)){var li=$('#ntop .nr[data-i="'+s0.n+'"]');if(!li){nst.src='all';nsr();li=$('#nall .nr[data-i="'+s0.n+'"]')}if(li){nact(li);li.classList.add('hl');setTimeout(function(){li.scrollIntoView({block:'center'})},60)}}
autosel();
ng.addEventListener('pointerover',npre,{passive:true});ng.addEventListener('touchstart',npre,{passive:true});ng.addEventListener('focusin',npre)}
})();
