/* ころがしボウリング：真上から見たレーン。ボールとピンは円どうしの衝突で動く。 */
const LL=120,LR=300,BY=640,BR=17,PR=10,FR=5;
const GAME={...META,sprites:['icon','pin','ball'],unit:'点',fullBleed:true,comboHud:false,
  bgm:{bpm:112,root:58,scale:'major',prog:[1,4,1,5],seed:47,lead:'square',drums:'pop',density:.5},
  ranks:[[0,'ガター'],[300,'ボウリング初心者'],[600,'ナイスピン'],[900,'ストライカー'],[1200,'プロボウラー'],[1450,'パーフェクトの神']],
  shareText:(v,f)=>`ころがしボウリングで ${f}点！`,
  icon(c,x,y,s){this.pin(c,x+s*.12,y-s*.05,s*.42,0);this.pin(c,x+s*.32,y,s*.36,0);this.ball(c,x-s*.2,y+s*.18,s*.2,0)},
  pin(c,x,y,h,lay,alpha=1){c.save();c.translate(x,y);c.rotate(lay);c.globalAlpha=alpha;const w=h*.32;
    D.path(c,c=>{c.moveTo(0,-h*.5);c.bezierCurveTo(w*.7,-h*.5,w*.7,-h*.2,w*.35,-h*.08);c.bezierCurveTo(w*1.1,h*.1,w*.9,h*.45,w*.5,h*.5);c.lineTo(-w*.5,h*.5);c.bezierCurveTo(-w*.9,h*.45,-w*1.1,h*.1,-w*.35,-h*.08);c.bezierCurveTo(-w*.7,-h*.2,-w*.7,-h*.5,0,-h*.5)},'#fbf7f0',Math.max(2,h*.07));
    c.fillStyle='#e2645a';c.fillRect(-w*.42,-h*.17,w*.84,h*.06);c.fillRect(-w*.42,-h*.08,w*.84,h*.035);D.face(c,0,h*.15,w*.95);c.restore()},
  ball(c,x,y,r,rot){D.circle(c,x,y,r,'#7d6aa8');c.fillStyle=OL;for(const[a,d]of[[0,.4],[.6,.45],[-.6,.45]]){c.beginPath();c.arc(x+Math.cos(rot+a-1.57)*r*d,y+Math.sin(rot+a-1.57)*r*d,r*.12,0,7);c.fill()}},
  rack(){const p=[];const rows=[[0],[-1,1],[-2,0,2],[-3,-1,1,3]];rows.forEach((row,ri)=>row.forEach(k=>p.push({x:(LL+LR)/2+k*17,y:250-ri*30,vx:0,vy:0,down:false,lay:0,a:1,sx:0,sy:0})));p.forEach(q=>{q.sx=q.x;q.sy=q.y});return p},
  reset(api){this.st={frame:0,roll:0,pins:this.rack(),b:null,ph:'aim',bx:(LL+LR)/2,score:0,marks:[],wait:0,first:0,rot:0};api.score=0},
  down(x,y){const st=this.st;if(st.ph!=='aim')return;st.sw={x,y,t:performance.now(),x0:x};st.bx=clamp(x,LL+BR,LR-BR)},
  move(x,y){const st=this.st;if(st.ph!=='aim'||!st.sw)return;if(y>BY-60)st.bx=clamp(x,LL+BR,LR-BR)},
  up(x,y,api){const st=this.st;if(st.ph!=='aim'||!st.sw)return;const s=st.sw;st.sw=null;const dy=y-s.y,dx=x-s.x;if(dy>-40){return}
    const dt=Math.max(60,performance.now()-s.t),sp=clamp(Math.hypot(dx,dy)/dt*1000,500,1300);const a=Math.atan2(dy,dx);this.throw(a,sp,api)},
  throw(a,sp,api){const st=this.st;st.b={x:st.bx,y:BY,vx:Math.cos(a)*sp,vy:Math.sin(a)*sp,g:false};st.ph='roll';st.wait=0;S.whoosh();st.rollSnd=0},
  key(k,api){const st=this.st;if(st.ph!=='aim')return;if(k==='ArrowLeft')st.bx=Math.max(LL+BR,st.bx-8);if(k==='ArrowRight')st.bx=Math.min(LR-BR,st.bx+8);if(k===' '||k==='ArrowUp')this.throw(-Math.PI/2,1000,api)},keyRepeat:true,
  update(dt,api){const st=this.st;
    if(st.ph==='roll'||st.ph==='settle'){const b=st.b;st.wait+=dt;const sub=4,h=dt/sub;
      for(let s=0;s<sub;s++){if(b){b.x+=b.vx*h;b.y+=b.vy*h;st.rot+=h*b.vy*.02;if(!b.g&&(b.x<LL+4||b.x>LR-4)){b.g=true;b.x=b.x<LL+4?LL-14:LR+14;b.vx=0;S.thud();api.float(b.x<W/2?100:320,500,'ガター…',{size:22})}}
        for(const p of st.pins){if(p.out)continue;p.x+=p.vx*h;p.y+=p.vy*h;const f=Math.pow(.2,h);p.vx*=f;p.vy*=f;
          if(p.x<LL-6||p.x>LR+6||p.y<90){p.out=true;p.down=true}
          if(b&&!b.g){const d=dist(p.x,p.y,b.x,b.y);if(d<PR+BR&&d>0){const nx=(p.x-b.x)/d,ny=(p.y-b.y)/d,rv=(b.vx-p.vx)*nx+(b.vy-p.vy)*ny;if(rv>0){const j=rv*1.75;p.vx+=nx*j*.85+rnd(-30,30);p.vy+=ny*j*.85;b.vx-=nx*j*.3;b.vy-=ny*j*.3;this.hitSnd(rv)}p.x=b.x+nx*(PR+BR);p.y=b.y+ny*(PR+BR);p.down=true}}}
        for(let i=0;i<st.pins.length;i++)for(let j=i+1;j<st.pins.length;j++){const a=st.pins[i],c=st.pins[j];if(a.out||c.out)continue;const d=dist(a.x,a.y,c.x,c.y);if(d<PR*2&&d>0){const nx=(c.x-a.x)/d,ny=(c.y-a.y)/d,rv=(a.vx-c.vx)*nx+(a.vy-c.vy)*ny;
          if(rv>0){const j2=rv*.95;a.vx-=nx*j2;a.vy-=ny*j2;c.vx+=nx*j2;c.vy+=ny*j2;if(rv>40){a.down=c.down=true;this.hitSnd(rv*.7)}}const o=(PR*2-d)/2;a.x-=nx*o;a.y-=ny*o;c.x+=nx*o;c.y+=ny*o}}}
      for(const p of st.pins)if(p.down){p.lay=Math.min(1.5,p.lay+dt*8)}
      if(b&&b.y<80)st.b=null;
      const moving=st.pins.some(p=>!p.out&&Math.hypot(p.vx,p.vy)>8);
      if((!st.b&&!moving&&st.wait>1)||st.wait>4.5)this.endRoll(api)}
    else if(st.ph==='show'){st.wait-=dt;if(st.wait<=0)this.next(api)}},
  hitSnd(v){const t=performance.now();if(this.lastHit&&t-this.lastHit<25)return;this.lastHit=t;S.noise(.07,{v:Math.min(.6,v/1200),f:rnd(1800,2600),q:3});S.tone(rnd(700,900),.07,{type:'triangle',v:Math.min(.25,v/2500)})},
  endRoll(api){const st=this.st;const n=st.pins.filter(p=>p.down).length-st.first;st.ph='show';st.wait=1.3;let msg='',pts=n*10;
    if(st.roll===0&&n===10){msg='ストライク！';pts+=200;S.fanfare();api.flash('#fff',.5);api.shake(10);for(let i=0;i<4;i++)api.burst(rnd(LL,LR),rnd(150,300),{c:['#f4d66d','#e2645a','#fff'],n:18,shape:'star',sp:300});st.marks[st.frame]='★'}
    else if(st.roll===1&&st.first+n===10){msg='スペア！';pts+=100;S.perfect();api.flash('#fff',.3);st.marks[st.frame]='/'}
    else if(n===0){msg=st.b===null&&st.roll===0?'ざんねん…':'0本';S.bad()}else{msg=n+'本！';S.good()}
    if(st.roll===1&&st.marks[st.frame]!=='/')st.marks[st.frame]=String(st.first+n);
    api.add(pts);api.float(W/2,380,msg,{size:msg.length>4?40:34,c:n===10||msg==='スペア！'?'#f3c84b':'#fff',life:1.2});if(pts)api.float(W/2,430,'+'+pts,{size:24});st.lastN=n;st.firstNext=st.first+n},
  next(api){const st=this.st;const total=st.firstNext;
    if(st.roll===0&&total<10){st.roll=1;st.first=total;for(const p of st.pins)if(p.down)p.out=true}
    else{st.frame++;st.roll=0;st.first=0;if(st.frame>=FR){api.end();return}st.pins=this.rack()}
    st.ph='aim';st.b=null;st.bx=(LL+LR)/2},
  drawHud(c,api){const st=this.st;D.text(c,api.score+'点',W/2,40,30,'#fff','center',OL,8);
    for(let i=0;i<FR;i++){const x=W/2-130+i*52;D.rrect(c,x,64,48,40,8,i===st.frame?'#fff6d8':'#fffdf8',3);D.text(c,(i+1)+'',x+10,76,11,'#8e8077');D.text(c,st.marks[i]||'',x+26,90,18,st.marks[i]==='★'||st.marks[i]==='/'?'#e2645a':'#5b4d45')}},
  draw(c,api){const st=this.st;c.fillStyle='#5e4f63';c.fillRect(0,api.top,W,api.bottom-api.top);
    c.fillStyle='#4b3f50';c.fillRect(LL-26,api.top,26,api.bottom-api.top);c.fillRect(LR,api.top,26,api.bottom-api.top);
    c.fillStyle='#e9c98f';c.fillRect(LL,api.top,LR-LL,api.bottom-api.top);c.fillStyle='#ddb97b';for(let x=LL+20;x<LR;x+=20)c.fillRect(x,api.top,2,api.bottom-api.top);
    c.lineWidth=4;c.strokeStyle=OL;c.strokeRect(LL,api.top-4,LR-LL,api.bottom-api.top+8);
    for(let i=0;i<5;i++)D.poly(c,[[LL+30+i*35,470],[LL+38+i*35,490],[LL+22+i*35,490]],'#c7746a',2);
    c.fillStyle='#c98a5b';c.fillRect(LL,BY+40,LR-LL,4);
    const ps=st.pins.filter(p=>!p.out).sort((a,b)=>a.y-b.y);for(const p of ps){if(!p.down){c.globalAlpha=.2;D.ellipse(c,p.x,p.y+2,10,4,'#5b4d45',0);c.globalAlpha=1}this.pin(c,p.x,p.y-16+p.lay*10,34,p.lay*(p.vx>=0?1:-1))}
    for(const p of st.pins)if(p.out&&p.y>90&&st.ph!=='aim'){}
    if(st.b)this.ball(c,st.b.x,st.b.y,BR,st.rot);else if(st.ph==='aim'){this.ball(c,st.bx,BY,BR,0);
      c.fillStyle='rgba(91,77,69,.35)';for(let i=1;i<6;i++){c.beginPath();c.arc(st.bx,BY-i*26-14,3,0,7);c.fill()}
      if(api.state==='play')D.text(c,'↑ 上へスワイプ',W/2,BY+70,16,'#fffdf8','center',OL,4)}},
  __bot(api){const st=this.st;if(st.ph!=='aim')return;const tgt=st.pins.filter(p=>!p.down);let tx=(LL+LR)/2;if(tgt.length)tx=tgt.reduce((a,p)=>a+p.x,0)/tgt.length;st.bx=clamp(tx+rnd(-20,20),LL+BR,LR-BR);
    this.throw(Math.atan2(240-BY,tx+rnd(-8,8)-st.bx),rnd(800,1200),api)},
};
