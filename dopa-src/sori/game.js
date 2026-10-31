/* ゆきやまソリダッシュ：3レーンのよけゲー。ものが上から流れてくる。 */
const LX=[110,210,310],PY=560;
const GAME={...META,sprites:['icon','peng','tree','rock','log'],unit:'点',fullBleed:true,
  bgm:{bpm:150,root:62,scale:'major',prog:[1,5,6,4],seed:24,lead:'square',drums:'four',density:.62},
  ranks:[[0,'ゆきだま'],[300,'ソリ初心者'],[800,'ゲレンデ常連'],[1600,'雪山の風'],[3000,'ソリの達人'],[5000,'雪山の王者']],
  shareText:(v,f)=>`ゆきやまソリダッシュで ${f}点！`,
  icon(c,x,y,s){this.tree(c,x+s*.3,y-s*.15,s*.35);this.peng(c,x-s*.05,y+s*.08,s*.5,0)},
  peng(c,x,y,s,jump){const k=s/60;c.save();c.translate(x,y-jump);
    D.rrect(c,-28*k,8*k,56*k,16*k,8*k,'#e2645a');c.lineWidth=3;c.strokeStyle=OL;c.beginPath();c.moveTo(-30*k,24*k);c.quadraticCurveTo(-38*k,24*k,-36*k,14*k);c.stroke();
    D.ellipse(c,0,-12*k,22*k,26*k,'#59606e');D.ellipse(c,0,-6*k,15*k,19*k,'#fbf7f0',0);D.poly(c,[[-5*k,-12*k],[5*k,-12*k],[0,-5*k]],'#f2b45a',2);
    c.fillStyle=OL;c.beginPath();c.arc(-7*k,-18*k,2.6*k,0,7);c.arc(7*k,-18*k,2.6*k,0,7);c.fill();
    D.rrect(c,-20*k,-40*k,40*k,8*k,4*k,'#f2a5b5');c.restore()},
  tree(c,x,y,s){D.rrect(c,x-s*.08,y+s*.2,s*.16,s*.25,3,'#9a6a4e');D.poly(c,[[x,y-s*.55],[x+s*.4,y+s*.25],[x-s*.4,y+s*.25]],'#7fa874');D.poly(c,[[x,y-s*.55],[x+s*.22,y-s*.1],[x-s*.22,y-s*.1]],'#fbfaf6',0)},
  rock(c,x,y,s){D.path(c,c=>{c.moveTo(x-s*.45,y+s*.25);c.lineTo(x-s*.35,y-s*.15);c.lineTo(x-s*.05,y-s*.32);c.lineTo(x+s*.35,y-s*.2);c.lineTo(x+s*.45,y+s*.25);c.closePath()},'#a7a3ad')},
  log(c,x,y,w){D.rrect(c,x-w/2,y-13,w,26,13,'#b98450');D.ellipse(c,x-w/2+10,y,7,11,'#e3b47a',2.5);D.ellipse(c,x+w/2-10,y,7,11,'#e3b47a',2.5)},
  reset(api){this.st={lane:1,x:LX[1],jump:0,jv:0,o:[],dist:0,sp:300,spawn:0,t:0,trail:[],stars:0,dead:false};api.score=0},
  go(d,api){const st=this.st;if(d==='U'){if(st.jump<=0){st.jv=520;st.jump=.1;S.whoosh()}return}const n=clamp(st.lane+(d==='L'?-1:1),0,2);if(n!==st.lane){st.lane=n;S.swish()}},
  down(x,y){this.st.sw={x,y,used:false}},
  move(x,y,api){const s=this.st.sw;if(!s||s.used)return;const dx=x-s.x,dy=y-s.y;if(Math.hypot(dx,dy)<20)return;s.used=true;this.go(Math.abs(dx)>Math.abs(dy)?(dx>0?'R':'L'):(dy<0?'U':'D'),api)},
  up(x,y,api){const s=this.st.sw;if(s&&!s.used){this.go(x<W/2?'L':'R',api)}this.st.sw=null},
  key(k,api){const m={ArrowLeft:'L',ArrowRight:'R',ArrowUp:'U',' ':'U'}[k];if(m)this.go(m,api)},
  pattern(){const st=this.st,y=-80,r=Math.random(),free=rndi(0,2),T=st.dist/1000;
    if(r<.2){st.o.push({t:'log',lane:-1,y});for(let i=0;i<3;i++)st.o.push({t:'star',lane:free,y:y-60-i*50})}
    else if(r<.55){for(let l=0;l<3;l++)if(l!==free&&(Math.random()<.5+T*.05||l===(free+1)%3))st.o.push({t:Math.random()<.5?'tree':'rock',lane:l,y});for(let i=0;i<4;i++)st.o.push({t:'star',lane:free,y:y+i*-50})}
    else{const l=rndi(0,2);st.o.push({t:pick(['tree','rock']),lane:l,y});const sl=(l+rndi(1,2))%3;for(let i=0;i<5;i++)st.o.push({t:'star',lane:sl,y:y-i*50})}},
  update(dt,api){const st=this.st;st.t+=dt;st.sp=Math.min(760,300+st.t*9);st.dist+=st.sp*dt;api.bgmRate=1+(st.sp-300)/1200;
    st.x+=(LX[st.lane]-st.x)*Math.min(1,dt*16);
    if(st.jump>0){st.jump+=st.jv*dt;st.jv-=1700*dt;if(st.jump<=0){st.jump=0;S.thud()}}
    st.spawn-=st.sp*dt;if(st.spawn<=0){this.pattern();st.spawn=rnd(300,420)}
    const pts=Math.floor(st.dist/40);if(pts>(st.lastP||0)){api.add(pts-(st.lastP||0));st.lastP=pts}
    for(let i=st.o.length-1;i>=0;i--){const o=st.o[i];o.y+=st.sp*dt;if(o.y>H+80){st.o.splice(i,1);continue}
      const hitY=Math.abs(o.y-PY)<(o.t==='star'?28:30);const inLane=o.lane<0||Math.abs(LX[o.lane]-st.x)<44;
      if(hitY&&inLane){
        if(o.t==='star'){st.o.splice(i,1);st.stars++;api.combo++;api.add(10+Math.min(api.combo,30));S.coin(1+Math.min(api.combo,15)*.03);api.burst(st.x,PY-20,{c:['#f4d66d','#fff'],n:6,sp:120,shape:'star'});st.starT=.8}
        else if(o.t==='log'&&st.jump>18){if(!o.cleared){o.cleared=true;api.add(30);api.float(st.x,PY-80,'ジャンプ +30',{size:22,c:'#f3c84b'});S.good()}}
        else{st.dead=true;S.boom();api.shake(14);api.flash('#fff',.6);api.burst(st.x,PY,{c:['#fff','#dfe8f0'],n:30,sp:300});api.end();return}}}
    st.starT=(st.starT||0)-dt;if(st.starT<=0)api.combo=0;
    st.trail.unshift([st.x,0]);if(st.trail.length>30)st.trail.pop()},
  overText:'ドッシーン！',
  draw(c,api){const st=this.st;c.fillStyle='#f4f8fb';c.fillRect(0,api.top,W,api.bottom-api.top);
    const off=st.dist%120;c.fillStyle='#e3edf3';for(let y=api.top-120+off;y<api.bottom;y+=120){c.fillRect(0,y,W,40)}
    c.fillStyle='#dbe6ee';c.fillRect(0,api.top,40,api.bottom-api.top);c.fillRect(W-40,api.top,40,api.bottom-api.top);
    for(let y=api.top-200+(st.dist*1)%200;y<api.bottom;y+=200){this.tree(c,20,y,46);this.tree(c,W-20,y+100,46)}
    // ソリのあと
    c.strokeStyle='#d5e2ec';c.lineWidth=4;for(const dx of[-14,14]){c.beginPath();st.trail.forEach((p,i)=>{const y=PY+20+i*st.sp/60;i?c.lineTo(p[0]+dx,y):c.moveTo(p[0]+dx,y)});c.stroke()}
    const objs=st.o.slice().sort((a,b)=>a.y-b.y);
    for(const o of objs){const x=o.lane<0?W/2:LX[o.lane];if(o.t==='star')D.star(c,x,o.y,16,'#f4d66d',3,Math.sin(st.t*4+o.y)*.3);else if(o.t==='tree')this.tree(c,x,o.y-10,80);else if(o.t==='rock')this.rock(c,x,o.y,70);else this.log(c,x,o.y,300)}
    c.globalAlpha=.2;D.ellipse(c,st.x,PY+20,30*(1-st.jump/200),8,'#5b4d45',0);c.globalAlpha=1;
    this.peng(c,st.x,PY,60,st.jump)},
  __bot(api){const st=this.st;const danger=l=>st.o.some(o=>o.t!=='star'&&o.t!=='log'&&o.lane===l&&o.y>PY-260&&o.y<PY+40);
    const log=st.o.find(o=>o.t==='log'&&o.y>PY-90&&o.y<PY-30&&!o.cleared);if(log&&st.jump<=0)this.go('U',api);
    if(danger(st.lane)){for(const l of[st.lane-1,st.lane+1])if(l>=0&&l<3&&!danger(l)){this.go(l<st.lane?'L':'R',api);break}}},
};
