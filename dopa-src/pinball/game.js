/* おまつりピンボール：円バンパー＋線分フリッパー。 */
const L=40,Rr=380,TOP=130,BOT=700,BR=11;
const BUMP=[{x:140,y:260,r:28,c:'#e2645a'},{x:280,y:260,r:28,c:'#7fb2e0'},{x:210,y:360,r:30,c:'#f2c84b'},{x:110,y:440,r:22,c:'#9cc86a'},{x:310,y:440,r:22,c:'#c49ae0'}];
const LAN=[{x:120,y:180},{x:210,y:170},{x:300,y:180}];
const FL={lx:120,rx:300,y:640,len:75};
const GAME={...META,sprites:['icon','bumper','lantern'],unit:'点',fullBleed:true,comboHud:false,
  bgm:{bpm:132,root:57,scale:'major',prog:[1,4,5,1],seed:11,lead:'square',drums:'four',density:.6},
  ranks:[[0,'玉ぽろり'],[500,'ピンボール初心者'],[1500,'カンカン上手'],[3500,'フィーバー常連'],[7000,'ピンボール名人'],[12000,'おまつりの王']],
  shareText:(v,f)=>`おまつりピンボールで ${f}点！`,
  icon(c,x,y,s){this.bumper(c,x-s*.2,y-s*.15,s*.16,'#e2645a',0);this.bumper(c,x+s*.2,y-s*.15,s*.16,'#7fb2e0',0);this.bumper(c,x,y+s*.1,s*.14,'#f2c84b',0);D.circle(c,x+s*.08,y+s*.38,s*.07,'#b9c3cc')},
  bumper(c,x,y,r,col,hit){const k=1+hit*.2;D.circle(c,x,y,r*k,col);D.circle(c,x,y,r*.55*k,'#fbf7f0',2.5);D.face(c,x,y+r*.05,r*.7,hit>0?'o':'smile')},
  lantern(c,x,y,on){D.rrect(c,x-6,y-30,12,6,2,'#5b4d45',2);D.ellipse(c,x,y,20,26,on?'#f2a24a':'#8a8392');c.strokeStyle=on?'#e2645a':'#6d6672';c.lineWidth=2;for(let i=-1;i<=1;i++){c.beginPath();c.moveTo(x-20,y+i*12);c.lineTo(x+20,y+i*12);c.stroke()}if(on)D.text(c,'祭',x,y+2,16,'#5b4d45')},
  reset(api){this.st={b:null,balls:3,fl:{l:0,r:0},lit:[false,false,false],fever:0,hit:BUMP.map(()=>0),t:0,wait:.3,mul:1};api.score=0},
  launch(){const st=this.st;st.b={x:Rr-25,y:BOT-80,vx:0,vy:-rnd(900,1000)}},
  down(x,y,api){const st=this.st;if(x<W/2)st.fl.l=1;else st.fl.r=1;S.tone(300,.04,{type:'square',v:.1})},
  up(x,y){const st=this.st;if(x<W/2)st.fl.l=0;else st.fl.r=0},
  key(k){if(k==='ArrowLeft')this.st.fl.l=1;if(k==='ArrowRight')this.st.fl.r=1},keyUp(k){if(k==='ArrowLeft')this.st.fl.l=0;if(k==='ArrowRight')this.st.fl.r=0},
  flipper(side){const st=this.st;const a=side==='l'?(st.fl.l?-.6:.35):(st.fl.r?.6:-.35);const x0=side==='l'?FL.lx-60:FL.rx+60;const x1=side==='l'?x0+Math.cos(a)*FL.len*1.6:x0-Math.cos(a)*FL.len*1.6;const y1=FL.y+Math.sin(a)*FL.len*1.6*(side==='l'?1:-1)*(side==='l'?1:-1);return{x0,y0:FL.y,x1,y1:FL.y+Math.sin(a)*FL.len*1.6}},
  update(dt,api){const st=this.st;st.t+=dt;st.hit=st.hit.map(h=>Math.max(0,h-dt*4));if(st.fever>0){st.fever-=dt;if(st.fever<=0){api.fever=false;st.mul=1}}
    if(!st.b){st.wait-=dt;if(st.wait<=0){if(st.balls<=0){api.end();return}st.balls--;this.launch();S.whoosh()}return}
    const b=st.b,sub=6,h=dt/sub;
    for(let s=0;s<sub;s++){b.vy+=900*h;b.x+=b.vx*h;b.y+=b.vy*h;
      if(b.x<L+BR){b.x=L+BR;b.vx=Math.abs(b.vx)*.8}if(b.x>Rr-BR){b.x=Rr-BR;b.vx=-Math.abs(b.vx)*.8}if(b.y<TOP+BR){b.y=TOP+BR;b.vy=Math.abs(b.vy)*.8}
      BUMP.forEach((bp,i)=>{const d=dist(b.x,b.y,bp.x,bp.y);if(d<bp.r+BR){const nx=(b.x-bp.x)/d,ny=(b.y-bp.y)/d;b.x=bp.x+nx*(bp.r+BR);b.y=bp.y+ny*(bp.r+BR);const vn=b.vx*nx+b.vy*ny;b.vx-=2*vn*nx;b.vy-=2*vn*ny;b.vx+=nx*200;b.vy+=ny*200;st.hit[i]=1;const pts=50*st.mul;api.add(pts);S.tone(700+i*100,.06,{type:'square',v:.2});S.noise(.04,{v:.3,f:3000});api.shake(2);api.float(bp.x,bp.y-bp.r-14,'+'+pts,{size:16,life:.5})}});
      LAN.forEach((ln,i)=>{if(!st.lit[i]&&dist(b.x,b.y,ln.x,ln.y)<30){st.lit[i]=true;S.coin(1.3);api.add(100);api.burst(ln.x,ln.y,{c:['#f2a24a','#f4d66d'],n:10,sp:150});if(st.lit.every(Boolean)){st.fever=8;api.fever=true;st.mul=3;S.fanfare();api.flash('#fff6c8',.5);api.float(W/2,400,'フィーバー！ ×3',{size:40,c:'#f3c84b',life:1.5});setTimeout(()=>{},0);st.lit=[false,false,false]}}});
      for(const side of['l','r']){const f=this.flipper(side);const dx=f.x1-f.x0,dy=f.y1-f.y0,len=Math.hypot(dx,dy);const t=clamp(((b.x-f.x0)*dx+(b.y-f.y0)*dy)/(len*len),0,1);const px=f.x0+dx*t,py=f.y0+dy*t;const d=dist(b.x,b.y,px,py);
        if(d<BR+6){const nx=(b.x-px)/d,ny=(b.y-py)/d;b.x=px+nx*(BR+6);b.y=py+ny*(BR+6);const vn=b.vx*nx+b.vy*ny;if(vn<0){b.vx-=1.8*vn*nx;b.vy-=1.8*vn*ny}const pressed=side==='l'?st.fl.l:st.fl.r;if(pressed&&ny<0){b.vy-=700*t;b.vx+=(side==='l'?1:-1)*200*t;S.tone(220,.08,{type:'square',v:.15})}}}
      // 下の壁（フリッパーの外側）
      if(b.y>FL.y+40&&(b.x<FL.lx-60||b.x>FL.rx+60)){b.y=FL.y+40;b.vy=-Math.abs(b.vy)*.5}
      if(b.y>BOT+20){st.b=null;st.wait=.8;S.bad();api.float(W/2,600,'玉ぽろり…',{size:26});break}}},
  drawHud(c,api){const st=this.st;D.text(c,api.score.toLocaleString(),W/2,48,32,'#fff','center',OL,8);for(let i=0;i<3;i++)D.circle(c,40+i*24,96,8,i<st.balls?'#b9c3cc':'#4b4660',2);if(st.fever>0)D.text(c,'FEVER ×3',W-80,96,18,'#f3c84b','center',OL,5)},
  draw(c,api){const st=this.st;c.fillStyle='#2f2b45';c.fillRect(0,api.top,W,api.bottom-api.top);D.rrect(c,L-12,TOP-12,Rr-L+24,BOT-TOP+30,24,'#4b3e37',4);c.fillStyle='#3b3550';c.fillRect(L,TOP,Rr-L,BOT-TOP+10);
    c.fillStyle='#352f4a';for(let y=TOP;y<BOT;y+=40)c.fillRect(L,y,Rr-L,20);
    LAN.forEach((ln,i)=>this.lantern(c,ln.x,ln.y,st.lit[i]));BUMP.forEach((bp,i)=>this.bumper(c,bp.x,bp.y,bp.r,bp.c,st.hit[i]));
    D.rrect(c,L,FL.y+40,FL.lx-60-L,BOT-FL.y,6,'#6d6672');D.rrect(c,FL.rx+60,FL.y+40,Rr-FL.rx-60,BOT-FL.y,6,'#6d6672');
    for(const side of['l','r']){const f=this.flipper(side);c.lineCap='round';c.lineWidth=20;c.strokeStyle=OL;c.beginPath();c.moveTo(f.x0,f.y0);c.lineTo(f.x1,f.y1);c.stroke();c.lineWidth=13;c.strokeStyle='#e2645a';c.stroke()}
    if(st.b)D.circle(c,st.b.x,st.b.y,BR,'#b9c3cc',2.5);
    if(api.t<3&&api.state==='play')D.text(c,'左半分タップ＝左、右半分＝右',W/2,560,15,'#fff','center',OL,4)},
  __bot(api){const st=this.st;const b=st.b;if(!b){st.fl.l=st.fl.r=0;return}st.fl.l=b.y>560&&b.x<W/2&&b.vy>0?1:0;st.fl.r=b.y>560&&b.x>=W/2&&b.vy>0?1:0},
};
