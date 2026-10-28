/* やさいスパスパ：放物線でとぶ野菜をスワイプで切る。サラダの注文（左上の伝票）をそろえるとボーナス＋時間。1スワイプ複数切りでボーナス。ウニは-3秒。 */
const VEG=[
  {n:'トマト',r:30,c:'#e8695c',in:'#f6a99c',pts:1},{n:'なす',r:30,c:'#8a6aa8',in:'#efe6c8',pts:1},{n:'にんじん',r:28,c:'#f09a4a',in:'#f7c58e',pts:1},
  {n:'キャベツ',r:36,c:'#a9d38a',in:'#e3f2c9',pts:1},{n:'だいこん',r:30,c:'#f6f2e6',in:'#ffffff',pts:1},{n:'ピーマン',r:28,c:'#5fa65a',in:'#c9e6b6',pts:1}];
const GAME={...META,sprites:['icon','veg'],time:40,unit:'点',
  bgm:{bpm:140,root:57,scale:'minor',prog:[1,6,3,7],seed:41,lead:'square',drums:'four'},
  ranks:[[0,'ピーラー係'],[60,'見習いシェフ'],[130,'スパスパ料理人'],[220,'包丁さばきの達人'],[330,'やさい斬りの剣豪'],[450,'伝説の板前']],
  shareText:(v,f)=>`やさいスパスパで ${f}点！`,
  icon(c,x,y,s){c.save();c.translate(x,y);this.veg(c,{t:0,r:s*.3,rot:-.2},0,0);this.veg(c,{t:2,r:s*.2,rot:.6},s*.28,-s*.26);this.veg(c,{t:1,r:s*.2,rot:-.8},-s*.3,-s*.24);
    c.lineWidth=s*.04;c.strokeStyle='#fff';c.lineCap='round';c.beginPath();c.moveTo(-s*.45,s*.35);c.lineTo(s*.45,-s*.05);c.stroke();c.restore()},
  shape(c,t,r){c.beginPath();
    if(t===1){c.ellipse(0,r*.15,r*.75,r*1.05,0,0,7)}
    else if(t===2){c.moveTo(-r*.6,-r*.8);c.quadraticCurveTo(0,-r*1,r*.6,-r*.8);c.lineTo(r*.12,r*1.1);c.quadraticCurveTo(0,r*1.25,-r*.12,r*1.1);c.closePath()}
    else if(t===4){c.ellipse(0,r*.1,r*.6,r*1.1,0,0,7)}
    else if(t===5){c.moveTo(-r*.9,-r*.3);c.bezierCurveTo(-r*1.1,r*.9,-r*.2,r*1.1,0,r*.8);c.bezierCurveTo(r*.2,r*1.1,r*1.1,r*.9,r*.9,-r*.3);c.bezierCurveTo(r*.6,-r*.9,-r*.6,-r*.9,-r*.9,-r*.3)}
    else if(t==='gold'){c.ellipse(0,0,r*1.15,r*.9,0,0,7)}
    else c.arc(0,0,r,0,7)},
  veg(c,v,x,y,clip=0){
    const t=v.t,r=v.r;c.save();c.translate(x,y);c.rotate(v.rot||0);
    if(clip){c.save();c.rotate(v.cut||0);c.beginPath();c.rect(-200,clip<0?-200:0,400,200);c.restore();c.clip()}
    if(t==='uni'){D.star(c,0,0,r*1.25,'#4b3c5e',3,0,14,.72);D.circle(c,0,0,r*.75,'#5f4c78',3);D.face(c,0,2,r*.9,'angry')}
    else{const col=t==='gold'?'#f2c14e':VEG[t].c;this.shape(c,t,r);c.fillStyle=col;c.fill();c.lineWidth=3.5;c.strokeStyle=OL;c.lineJoin='round';c.stroke();
      if(t==='gold'){c.lineWidth=2.5;for(const k of[-1,1]){c.beginPath();c.ellipse(r*k*.62,0,r*.42,r*.82,0,0,7);c.stroke()}D.rrect(c,-4,-r*1.15,8,r*.35,3,'#7a9b4f',2.5)}
      if(t===0||t===2||t===4){D.path(c,c=>{const yy=t===0?-r*.92:t===2?-r*.9:-r*1.15;for(let i=-1;i<=1;i++){c.moveTo(0,yy);c.quadraticCurveTo(i*r*.3,yy-r*.3,i*r*.5,yy-r*.45)}},null,3);c.lineWidth=5;c.strokeStyle='#6fae55';c.stroke()}
      if(t===1)D.rrect(c,-r*.35,-r*1,r*.7,r*.28,r*.1,'#5c7f45',3);
      if(t===3){c.lineWidth=2.5;c.strokeStyle='#7fb064';c.beginPath();c.arc(0,r*.2,r*.6,Math.PI*1.1,Math.PI*1.9);c.stroke()}
      if(!clip)D.face(c,0,t===2?-r*.2:r*.05,r*.95,v.hit?'o':'smile')}
    if(clip){c.save();c.rotate(v.cut||0);c.fillStyle=t==='uni'?'#f0c070':t==='gold'?'#fbe7a6':VEG[t].in;c.fillRect(-r*1.1,-2.5,r*2.2,5);c.restore()}
    c.restore()},
  reset(api){this.st={items:[],halves:[],trail:[],spawnT:.4,feverT:0,down:false,px:0,py:0,swipeCut:0,swipeT:0,wave:0,orders:0,ord:null,ordPop:0,bowl:0};this.newOrder();api.score=0},
  // 注文：2〜3種類の野菜を1〜3個ずつ。そろうとサラダ完成
  newOrder(){const st=this.st,n=Math.min(3,2+Math.floor(st.orders/2)),ts=[0,1,2,3,4,5].sort(()=>Math.random()-.5).slice(0,n);
    st.ord=ts.map(t=>({t,need:rndi(1,Math.min(3,1+Math.floor(st.orders/2)+1)),got:0}));st.ordPop=1},
  orderHit(v,api){const st=this.st,o=st.ord.find(q=>q.t===v.t&&q.got<q.need);if(!o)return;o.got++;st.ordPop=.6;S.coin(1.2);
    if(st.ord.every(q=>q.got>=q.need)){st.orders++;const b=(10+st.orders*5)*(st.feverT>0?2:1);api.score+=b;api.timeLeft+=4;st.bowl=1.4;
      S.fanfare();api.flash('#fff',.35);api.float(W/2,H/2-40,'サラダ完成！',{c:'#fff',size:44,life:1.2});api.float(W/2,H/2+10,'+'+b+'点  +4秒',{c:'#f3c84b',size:28,life:1.2});
      api.burst(W/2,H/2,{c:['#e8695c','#a9d38a','#f09a4a','#fff'],n:30,sp:380,shape:'star',r:5});this.newOrder()}},
  spawn(api){const st=this.st;st.wave++;const fever=st.feverT>0,n=fever?rndi(3,5):rndi(1,Math.min(5,2+Math.floor(api.t/10)));
    const want=st.ord.filter(q=>q.got<q.need).map(q=>q.t);
    for(let i=0;i<n;i++){let t=want.length&&Math.random()<.5?pick(want):rndi(0,VEG.length-1);
      if(!fever&&Math.random()<Math.min(.22,.06+api.t*.004))t='uni';else if(!fever&&st.wave%9===0&&i===0)t='gold';
      const x=rnd(70,W-70),r=t==='uni'?26:t==='gold'?34:VEG[t].r;
      st.items.push({t,r,x,y:H+40,vx:(W/2-x)*rnd(.4,.9),vy:-rnd(880,1060),rot:0,vr:rnd(-3,3),hit:false})}
    S.whoosh()},
  down(x,y){const st=this.st;st.down=true;st.px=x;st.py=y;st.swipeCut=0;st.trail=[{x,y,a:0}]},
  move(x,y,api){const st=this.st;if(!st.down)return;const d=dist(x,y,st.px,st.py);st.trail.push({x,y,a:0});
    if(d>6){for(const v of st.items){if(v.hit)continue;if(this.segDist(v.x,v.y,st.px,st.py,x,y)<v.r+6)this.cut(v,Math.atan2(y-st.py,x-st.px),api)}}
    st.px=x;st.py=y},
  up(x,y,api){const st=this.st;st.down=false;this.endSwipe(api)},
  endSwipe(api){const st=this.st;if(st.swipeCut>=3){const b=st.swipeCut*st.swipeCut;api.score+=b;api.float(W/2,200,st.swipeCut+'れんぎり！ +'+b,{c:'#f3c84b',size:32});S.perfect();api.flash('#fff',.25)}st.swipeCut=0},
  segDist(px,py,ax,ay,bx,by){const dx=bx-ax,dy=by-ay,l=dx*dx+dy*dy||1,t=clamp(((px-ax)*dx+(py-ay)*dy)/l,0,1);return dist(px,py,ax+dx*t,ay+dy*t)},
  cut(v,ang,api){const st=this.st;v.hit=true;v.cut=ang-(v.rot||0);
    const nx=-Math.sin(ang),ny=Math.cos(ang);
    for(const s of[-1,1])st.halves.push({...v,clip:s,x:v.x,y:v.y,vx:v.vx*.5+nx*s*-140,vy:v.vy*.3+ny*s*-140-80,vr:s*rnd(3,6)});
    if(v.t==='uni'){api.combo=0;api.timeLeft=Math.max(0,api.timeLeft-3);S.bad();S.boom();api.shake(16);api.flash('#4b3c5e',.4);api.float(v.x,v.y-30,'イタッ！ -3秒',{c:'#e2645a',size:30});api.burst(v.x,v.y,{c:['#4b3c5e','#f0c070'],n:18,sp:300});return}
    st.swipeCut++;api.combo++;
    let p=v.t==='gold'?10:1;if(st.feverT>0)p*=2;p+=Math.floor(api.combo/10);api.score+=p;
    if(typeof v.t==='number')this.orderHit(v,api);
    if(v.t==='gold'){st.feverT=6;api.fever=true;api.bgmRate=1.25;S.fanfare();api.flash('#f2c14e',.5);api.float(W/2,H/2,'フィーバー！',{c:'#f2c14e',size:44,life:1.2})}
    S.swish();S.pop(rnd(.8,1.2)*(1+Math.min(st.swipeCut,8)*.08));api.hitstop(25);api.shake(3);
    const col=v.t==='gold'?'#f2c14e':VEG[v.t].in;api.burst(v.x,v.y,{c:[col,'#fff'],n:12,sp:280,r:5});
    api.float(v.x,v.y-v.r-10,'+'+p,{size:22,c:'#fff'})},
  update(dt,api){const st=this.st;
    st.spawnT-=dt;if(st.spawnT<=0){this.spawn(api);st.spawnT=st.feverT>0?.45:Math.max(.5,.9-api.t*.01)}
    if(st.feverT>0){st.feverT-=dt;if(st.feverT<=0){api.fever=false;api.bgmRate=1}}
    for(const v of st.items){v.vy+=1000*dt;v.x+=v.vx*dt;v.y+=v.vy*dt;v.rot+=v.vr*dt}
    st.items=st.items.filter(v=>!v.hit&&v.y<H+80);
    for(const h of st.halves){h.vy+=1200*dt;h.x+=h.vx*dt;h.y+=h.vy*dt;h.rot+=h.vr*dt}
    st.halves=st.halves.filter(h=>h.y<H+100);
    for(const p of st.trail)p.a+=dt;st.trail=st.trail.filter(p=>p.a<.15);
    if(!st.down&&st.swipeCut)this.endSwipe(api);
    st.ordPop=Math.max(0,st.ordPop-dt*3);st.bowl=Math.max(0,st.bowl-dt)},
  drawOrder(c){const st=this.st,o=st.ord,w=76+o.length*52,s=1+st.ordPop*.12;
    c.save();c.translate(14+w/2,128);c.scale(s,s);c.rotate(-.03);D.rrect(c,-w/2,-34,w,74,12,'#fffdf8',3);
    D.text(c,'ちゅうもん',-w/2+38,-2,12,'#8e8077');D.text(c,'サラダ',-w/2+38,14,12,'#8e8077');
    o.forEach((q,i)=>{const x=-w/2+96+i*52,done=q.got>=q.need;c.globalAlpha=done?.45:1;this.veg(c,{t:q.t,r:13,rot:0},x,-6);c.globalAlpha=1;
      D.text(c,done?'OK':(q.need-q.got)+'こ',x,26,14,done?'#7cb35f':'#5b4d45')});
    c.restore();
    if(st.bowl>0){const k=Math.min(1,(1.4-st.bowl)*4),a=Math.min(1,st.bowl*2);c.save();c.globalAlpha=a;c.translate(W/2,H/2+90);c.scale(ease.outBack(k),ease.outBack(k));
      D.path(c,c=>{c.moveTo(-70,-10);c.lineTo(70,-10);c.quadraticCurveTo(66,50,0,52);c.quadraticCurveTo(-66,50,-70,-10)},'#fffdf8',4);
      [[-40,-18,3],[-12,-26,0],[18,-20,5],[42,-14,2],[0,-12,1]].forEach(([x,y,t])=>{D.circle(c,x,y,15,VEG[t].in,3)});
      D.path(c,c=>{c.moveTo(-70,-10);c.lineTo(70,-10);c.quadraticCurveTo(66,50,0,52);c.quadraticCurveTo(-66,50,-70,-10)},'#fffdf8',4);D.face(c,0,18,40,'smile');c.restore()}},
  draw(c,api){const st=this.st;
    c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.fillStyle='#d5e6c9';for(let i=0;i<8;i++){c.fillRect(i*60,0,30,H)}
    D.rrect(c,-20,H-90,W+40,140,30,'#d9b98f',4);for(let i=0;i<6;i++){c.strokeStyle='rgba(91,77,69,.25)';c.lineWidth=2;c.beginPath();c.moveTo(i*80,H-70);c.lineTo(i*80+40,H-70);c.stroke()}
    for(const h of st.halves)this.veg(c,h,h.x,h.y,h.clip);
    for(const v of st.items)this.veg(c,v,v.x,v.y);
    this.drawOrder(c);
    if(st.trail.length>1){c.lineCap='round';c.lineJoin='round';for(let i=1;i<st.trail.length;i++){const a=st.trail[i-1],b=st.trail[i],k=1-b.a/.15;c.strokeStyle=`rgba(255,255,255,${k})`;c.lineWidth=12*k;c.beginPath();c.moveTo(a.x,a.y);c.lineTo(b.x,b.y);c.stroke()}}
  },
  __bot(api){const st=this.st;const v=st.items.find(q=>!q.hit&&q.t!=='uni'&&q.y<330&&Math.random()<.3);if(!v)return;this.down(v.x-60,v.y-20,api);this.move(v.x,v.y,api);this.move(v.x+60,v.y+20,api);this.up(0,0,api)},
};
