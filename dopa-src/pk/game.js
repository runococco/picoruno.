/* ぴたっとPK：スワイプ方向にボールを飛ばし、キーパーの位置とゴール枠で判定。 */
const GL=80,GR=W-80,GT=250,GB=400,BY=600;
const GAME={...META,sprites:['icon','keeper','ball'],unit:'点',fullBleed:true,
  bgm:{bpm:128,root:60,scale:'major',prog:[1,5,6,4],seed:34,lead:'saw',drums:'four',density:.6},
  ranks:[[0,'はずしっぱなし'],[300,'PK見習い'],[600,'ストライカー'],[900,'すみっこ名人'],[1200,'PKの達人'],[1500,'伝説のキッカー']],
  shareText:(v,f)=>`ぴたっとPKで ${f}点！`,
  icon(c,x,y,s){D.rrect(c,x-s*.45,y-s*.3,s*.9,s*.5,4,'#fbf7f0');c.lineWidth=2;c.strokeStyle='#cfc6b8';for(let i=1;i<5;i++){c.beginPath();c.moveTo(x-s*.45+i*s*.18,y-s*.3);c.lineTo(x-s*.45+i*s*.18,y+s*.2);c.stroke()}for(let i=1;i<3;i++){c.beginPath();c.moveTo(x-s*.45,y-s*.3+i*s*.17);c.lineTo(x+s*.45,y-s*.3+i*s*.17);c.stroke()}
    this.keeper(c,x+s*.1,y,s*.22);this.ball(c,x-s*.25,y+s*.3,s*.14)},
  keeper(c,x,y,s,dive=0){c.save();c.translate(x,y);c.rotate(dive*.5);D.ellipse(c,0,s*.1,s*.9,s*.95,'#f2a24a');D.ellipse(c,-s*.75,-s*.3-Math.abs(dive)*s*.5,s*.28,s*.2,'#f2a24a',2.5);D.ellipse(c,s*.75,-s*.3-Math.abs(dive)*s*.5,s*.28,s*.2,'#f2a24a',2.5);D.face(c,0,-s*.05,s*1.3,dive?'o':'smile');c.restore()},
  ball(c,x,y,r){D.circle(c,x,y,r,'#fbf7f0');D.poly(c,[[x,y-r*.45],[x+r*.42,y-r*.14],[x+r*.26,y+r*.36],[x-r*.26,y+r*.36],[x-r*.42,y-r*.14]],'#5b4d45',0)},
  reset(api){this.st={n:0,kx:W/2,kt:0,b:null,wait:0,res:'',goals:0,t:0,sw:null,dive:0,tx:W/2};api.score=0},
  down(x,y){const st=this.st;if(st.b||st.wait>0||st.n>=10)return;st.sw={x,y,t:performance.now()}},
  up(x,y,api){const st=this.st,s=st.sw;st.sw=null;if(!s||st.b||st.wait>0)return;const dx=x-s.x,dy=y-s.y;if(dy>-30)return;const dt=Math.max(60,performance.now()-s.t);
    const v=clamp(Math.hypot(dx,dy)/dt*1000,500,1400);const ang=Math.atan2(dy,dx);this.kick(ang,v,api)},
  kick(ang,v,api){const st=this.st;st.n++;st.b={x:W/2,y:BY,vx:Math.cos(ang)*v*1.1,vy:Math.sin(ang)*v*1.1,r:22,z:0};S.thud();S.whoosh();
    // keeper guesses: mostly toward ball side, sometimes wrong
    const side=Math.sign(Math.cos(ang))||1;const wrong=Math.random()<.3;st.dive=wrong?-side:side;st.tx=W/2+st.dive*rnd(60,130);api.shake(3)},
  update(dt,api){const st=this.st;st.t+=dt;st.kt+=dt;
    if(st.wait>0){st.wait-=dt;if(st.wait<=0){st.b=null;st.dive=0;st.tx=W/2;if(st.n>=10)api.end()}return}
    if(!st.b){st.kx+=(W/2+Math.sin(st.kt*1.5)*60-st.kx)*3*dt;return}
    const b=st.b;st.kx+=(st.tx-st.kx)*6*dt;b.x+=b.vx*dt;b.y+=b.vy*dt;b.r=22-(BY-b.y)/(BY-GT)*8;
    if(b.y<=GT+70){ // reached goal line
      const inG=b.x>GL+16&&b.x<GR-16;const kd=Math.abs(b.x-st.kx);let pts=0,txt='';
      if(!inG){txt='はずれ…';S.bad();api.combo=0}
      else if(kd<58){txt='とめられた！';S.thud();api.shake(6);api.combo=0;b.vx*=-.3;b.vy=200}
      else{const edge=Math.min(b.x-GL,GR-b.x);pts=edge<45?150:edge<80?120:100;api.combo++;pts+=Math.min(api.combo,5)*10;txt=edge<45?'すみっこ！+'+pts:'ゴール！+'+pts;st.goals++;api.add(pts);S.perfect();api.burst(b.x,b.y,{c:['#e2645a','#f2c84b','#fff'],n:16,sp:240,shape:'s'});api.flash('#fff',.3)}
      api.float(W/2,180,txt,{size:pts>=150?34:26,c:pts?'#e2645a':'#5b4d45'});st.wait=1.2;b.vx=0;b.vy=0;b.y=inG&&kd>=58?GT+30:b.y}
  },
  draw(c,api){const st=this.st;c.fillStyle='#dff0d0';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#cfe6bc';for(let y=GB;y<api.bottom;y+=60)c.fillRect(0,y,W,30);
    // goal
    D.rrect(c,GL,GT,GR-GL,GB-GT,6,'#fbf7f0',4);c.lineWidth=1.5;c.strokeStyle='#d8d0c4';for(let x=GL+20;x<GR;x+=20){c.beginPath();c.moveTo(x,GT);c.lineTo(x,GB);c.stroke()}for(let y=GT+20;y<GB;y+=20){c.beginPath();c.moveTo(GL,y);c.lineTo(GR,y);c.stroke()}
    c.lineWidth=8;c.strokeStyle='#fff';c.beginPath();c.moveTo(GL,GB);c.lineTo(GL,GT);c.lineTo(GR,GT);c.lineTo(GR,GB);c.stroke();c.lineWidth=3;c.strokeStyle=OL;c.stroke();
    D.rrect(c,W/2-70,BY+40,140,10,5,'#fff',2);
    this.keeper(c,st.kx,GB-40,34,st.dive*(st.b?1:0));
    const b=st.b;if(b){D.ellipse(c,b.x,b.y+b.r+6,b.r*.9,b.r*.35,'rgba(90,77,69,.15)',0);this.ball(c,b.x,b.y,b.r)}else this.ball(c,W/2,BY,22);
    for(let i=0;i<10;i++)D.circle(c,W/2-99+i*22,150,8,i<st.n?'#e2645a':'#fff',2.5);
    if(api.state==='play'&&st.n===0)D.text(c,'ボールを上にスワイプ！',W/2,520,20,'#5b4d45');
    D.text(c,st.goals+'ゴール',W/2,110,18,'#5b4d45')},
  __bot(api){const st=this.st;if(st.b||st.wait>0||st.n>=10)return;if(Math.random()<.4){const a=-Math.PI/2+(Math.random()<.5?-1:1)*rnd(.22,.4);this.kick(a,rnd(800,1200),api)}},
};
