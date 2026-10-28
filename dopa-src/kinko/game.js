/* 金庫あけマスター：Pop the Lock 系。針が点に重なる間にタップ、通過したら失敗。
   開けるとジャックポット：コインと宝石がジャラジャラあふれて、下に山になってたまっていく。 */
const CX=W/2,CY=340,RR=118,WIN=.2,FLOOR=H-70,CW=6,NC=Math.ceil(W/CW)+1,PILEMAX=150;
const GEMS=['#7fc6d8','#e2645a','#9fd27c','#c49be0'];
const GAME={...META,sprites:['icon','safe'],unit:'枚',hud:false,
  bgm:{bpm:132,root:57,scale:'minor',prog:[1,4,7,3],seed:66,lead:'square',drums:'four',density:.6},
  ranks:[[0,'鍵をなくした人'],[20,'見習い錠前師'],[60,'金庫の常連'],[120,'金庫あけ職人'],[200,'伝説の大泥棒（ねこ）'],[300,'金庫の方から開く']],
  shareText:(v,f)=>`金庫あけマスターで コイン${f}枚 ジャラジャラ！`,
  icon(c,x,y,s){this.safe(c,x,y,s*.8,0,-.6,true)},
  safe(c,x,y,s,lv,ang,small){const k=s/300;D.rrect(c,x-s*.5,y-s*.5,s,s,s*.08,'#7c8a96',Math.max(2,4*k));D.rrect(c,x-s*.44,y-s*.44,s*.88,s*.88,s*.05,'#93a1ac',Math.max(1.5,3*k));
    D.circle(c,x,y,s*.33,'#4b5560',Math.max(2,4*k));D.circle(c,x,y,s*.26,'#e9e3d3',Math.max(2,3*k));
    if(small){c.save();c.translate(x,y);c.rotate(ang);D.rrect(c,-s*.02,-s*.26,s*.04,s*.18,s*.02,'#e2645a',2);c.restore();D.face(c,x,y+s*.06,s*.2,'smile')}},
  reset(api){this.st={lv:1,left:0,a:-Math.PI/2,dir:1,w:1.8,dot:0,inside:false,open:0,coins:[],fail:0,pour:0,emit:0,toEmit:0,clinkT:0,jaraT:0,hp:new Float32Array(NC)};
    if(!this.pile){this.pile=document.createElement('canvas');this.pile.width=W*2;this.pile.height=H*2}
    const pc=this.pile.getContext('2d');pc.setTransform(1,0,0,1,0,0);pc.clearRect(0,0,W*2,H*2);pc.setTransform(2,0,0,2,0,0);
    this.newLv();api.score=0},
  // 1枚（1粒）を山にのせる：低いとなりへ転がってから止まる
  land(co,api){const st=this.st,hp=st.hp;let i=clamp(Math.round(co.x/CW),1,NC-2);
    for(let k=0;k<6;k++){const l=hp[i-1],r=hp[i+1],m=Math.min(l,r);if(hp[i]-m>11)i+=(l<r||(l===r&&Math.random()<.5))?-1:1;else break;if(i<1||i>NC-2)break}
    i=clamp(i,1,NC-2);const x=i*CW+rnd(-2,2),y=FLOOR-hp[i];
    if(hp[i]<PILEMAX){hp[i]+=co.gem?6:4.5;hp[i-1]=Math.max(hp[i-1],hp[i]-7);hp[i+1]=Math.max(hp[i+1],hp[i]-7)}
    this.drawItem(this.pile.getContext('2d'),co,x,y-co.r*.4,rnd(-.4,.4),true);
    api.score+=co.v;if(co.gem){api.float(x,y-20,'+'+co.v,{c:co.c,size:20});S.coin(1.3)}
    if(st.clinkT<=0){S.clink(rnd(.85,1.15));st.clinkT=.035}},
  drawItem(c,co,x,y,rot,flat){c.save();c.translate(x,y);c.rotate(rot);
    if(co.gem){const r=co.r;D.poly(c,[[-r,-r*.2],[-r*.5,-r*.75],[r*.5,-r*.75],[r,-r*.2],[0,r*.9]],co.c,2.5)}
    else{const sy=flat?.55:Math.abs(Math.cos(co.spin))*.8+.2;D.ellipse(c,0,0,co.r,co.r*sy,'#f3c84b',2.5);if(sy>.4)D.ellipse(c,0,0,co.r*.55,co.r*.55*sy,'#f6d87a',1.5)}
    c.restore()},
  newLv(){const st=this.st;st.left=Math.min(5+st.lv*2,30);st.w=1.7+st.lv*.18;st.open=0;st.dir=st.lv%2?1:-1;this.newDot()},
  newDot(){const st=this.st;st.dot=st.a+st.dir*rnd(.9,2.7);st.inside=false},
  ad(a,b){let d=(a-b)%(Math.PI*2);if(d>Math.PI)d-=Math.PI*2;if(d<-Math.PI)d+=Math.PI*2;return d},
  tap(api){const st=this.st;if(st.open>0)return;const d=Math.abs(this.ad(st.a,st.dot));
    if(d<WIN){st.left--;api.score++;api.combo++;S.tick();S.good(1+(api.combo%10)*.05);api.hitstop(30);api.shake(3);
      const px=CX+Math.cos(st.dot)*RR,py=CY+Math.sin(st.dot)*RR;api.burst(px,py,{c:['#f3c84b','#fff'],n:10,sp:200,shape:'star',r:4});api.ring(px,py,{c:'#f3c84b',r:40});
      if(d<.06){api.score++;api.float(px,py-30,'ジャスト +2',{c:'#f3c84b',size:22})}
      if(st.left<=0){st.open=.01;st.pour=Math.min(3.2,1.3+st.lv*.3);st.emit=0;st.toEmit=10+st.lv*12+Math.max(0,st.lv-1)*2;
        S.fanfare();S.boom();api.flash('#f6d87a',.8);api.shake(16);api.bgmRate=1.3;api.fever=true;
        api.burst(CX,CY,{c:['#f3c84b','#fff','#f6d87a'],n:40,sp:520,shape:'star',r:7})}
      else{st.dir*=-1;this.newDot()}}
    else this.fail(api)},
  fail(api){const st=this.st;S.bad();api.shake(12);api.flash('#e2645a',.35);api.combo=0;api.end()},
  down(x,y,api){this.tap(api)},key(k,api){if(k===' '||k==='Enter')this.tap(api)},
  update(dt,api){const st=this.st;
    st.clinkT-=dt;
    for(const co of st.coins){co.vy+=1500*dt;co.x+=co.vx*dt;co.y+=co.vy*dt;co.spin+=dt*14;
      if(co.x<co.r){co.x=co.r;co.vx=Math.abs(co.vx)*.5}if(co.x>W-co.r){co.x=W-co.r;co.vx=-Math.abs(co.vx)*.5}
      const i=clamp(Math.round(co.x/CW),0,NC-1);if(co.vy>0&&co.y>FLOOR-st.hp[i]-co.r*.4){if(co.bounce&&co.vy>380){co.vy*=-.35;co.vx*=.6;co.bounce--;if(st.clinkT<=0){S.clink();st.clinkT=.035}}else{co.dead=true;this.land(co,api)}}}
    st.coins=st.coins.filter(co=>!co.dead);
    if(st.open>0){st.open+=dt;
      // ジャラジャラ：口から噴き出す
      if(st.open>.25&&st.emit<st.toEmit){const want=Math.min(st.toEmit,Math.ceil(st.toEmit*(st.open-.25)/st.pour));
        while(st.emit<want){st.emit++;const gem=st.lv>1&&st.emit%5===0;
          st.coins.push({x:CX+rnd(-90,90),y:CY+rnd(40,120),vx:rnd(-170,170),vy:rnd(-720,-260),r:gem?rnd(9,12):rnd(8,11),spin:rnd(6),gem,v:gem?5:1,c:gem?pick(GEMS):'#f3c84b',bounce:1})}
        st.jaraT-=dt;if(st.jaraT<=0){st.jaraT=.07;S.noise(.09,{v:.07,f:rnd(5000,7500),type:'highpass'})}}
      if(st.emit>=st.toEmit&&!st.coins.length&&st.open>st.pour+.9){api.bgmRate=1;api.fever=false;st.lv++;this.newLv()}
      return}
    st.a+=st.dir*st.w*dt;const d=this.ad(st.a,st.dot);
    if(Math.abs(d)<WIN)st.inside=true;else if(st.inside&&Math.sign(d)===st.dir)this.fail(api)},
  overText:'ハズレ！',
  draw(c,api){const st=this.st;c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.fillStyle='#ddd8e2';for(let i=0;i<10;i++)c.fillRect(0,i*80,W,40);
    const op=st.open>0?ease.out(Math.min(1,st.open*3)):0,jp=st.open>0&&st.open<st.pour+.6;
    // ジャックポットの光
    if(jp){c.save();c.translate(CX,CY);c.rotate(api.t*.8);c.globalAlpha=.35*Math.min(1,st.open*3);c.fillStyle='#f6d87a';
      for(let i=0;i<12;i++){c.rotate(Math.PI/6);c.beginPath();c.moveTo(0,0);c.lineTo(-60,-520);c.lineTo(60,-520);c.closePath();c.fill()}c.restore()}
    D.rrect(c,-20,FLOOR,W+40,120,0,'#b49b84',4);
    // 金庫本体
    D.rrect(c,CX-170,CY-170,340,340,26,'#7c8a96',4.5);D.rrect(c,CX-158,CY-158,316,316,20,'#4b5560',4);
    if(op>0){D.rrect(c,CX-150,CY-150,300,300,16,'#2e3438',3);{const g=c.createRadialGradient(CX,CY+60,10,CX,CY+60,170);g.addColorStop(0,'rgba(255,236,160,.95)');g.addColorStop(1,'rgba(255,236,160,0)');c.fillStyle=g;c.fillRect(CX-150,CY-150,300,300)}
      // 中のお宝：金ののべ棒・宝石・コインの山
      const left=1-Math.min(1,st.emit/Math.max(1,st.toEmit))*.6;
      D.path(c,c=>{c.moveTo(CX-140,CY+148);c.quadraticCurveTo(CX,CY+148-150*left,CX+140,CY+148);c.closePath()},'#f3c84b',3);
      for(let i=0;i<3;i++)D.poly(c,[[CX-70+i*46,CY+120-60*left],[CX-30+i*46,CY+120-60*left],[CX-22+i*46,CY+140-60*left],[CX-78+i*46,CY+140-60*left]],'#f6d87a',3);
      D.poly(c,[[CX-14,CY+40-70*left],[CX-7,CY+28-70*left],[CX+7,CY+28-70*left],[CX+14,CY+40-70*left],[CX,CY+58-70*left]],'#e2645a',3);
      D.poly(c,[[CX+60,CY+70-60*left],[CX+66,CY+60-60*left],[CX+78,CY+60-60*left],[CX+84,CY+70-60*left],[CX+72,CY+84-60*left]],'#7fc6d8',3)}
    c.save();c.translate(CX-158,CY);c.scale(1-op*.85,1);c.translate(-(CX-158),-CY);
    D.rrect(c,CX-152,CY-152,304,304,18,'#93a1ac',4);
    // ダイヤル
    c.lineWidth=26;c.strokeStyle='#4b5560';c.beginPath();c.arc(CX,CY,RR,0,7);c.stroke();c.lineWidth=4;c.strokeStyle=OL;c.beginPath();c.arc(CX,CY,RR+13,0,7);c.stroke();c.beginPath();c.arc(CX,CY,RR-13,0,7);c.stroke();
    if(api.state!=='title'&&st.open<=0){const px=CX+Math.cos(st.dot)*RR,py=CY+Math.sin(st.dot)*RR,gl=.5+.5*Math.sin(api.t*12);D.circle(c,px,py,11+gl*2,'#f3c84b',3)}
    D.circle(c,CX,CY,RR-20,'#e9e3d3',4);D.text(c,st.left,CX,CY+4,56,'#5b4d45');D.text(c,'のこり',CX,CY-44,14,'#8e8077');
    c.save();c.translate(CX,CY);c.rotate(st.a);D.rrect(c,RR-22,-6,44,12,6,'#e2645a',3);c.restore();
    c.restore();
    // たまったコインの山
    c.drawImage(this.pile,0,0,W,H);
    for(const co of st.coins)this.drawItem(c,co,co.x,co.y,co.spin*.2,false);
    if(jp){const k=Math.min(1,st.open*2.5),b=1+Math.sin(api.t*10)*.05;c.save();c.translate(CX,CY-205);c.scale(ease.outBack(k)*b,ease.outBack(k)*b);D.text(c,'JACKPOT!',0,0,52,Math.sin(api.t*14)>0?'#f3c84b':'#fff','center',OL,10);c.restore()}
    D.text(c,'金庫 '+st.lv+'こめ',CX,FLOOR+38,20,'#fff','center',OL,5);D.text(c,api.score+' 枚',CX,82,34,'#fff','center',OL,8);
  },
  __bot(api){const st=this.st;if(st.open>0)return;if(Math.abs(this.ad(st.a,st.dot))<.08)this.tap(api)},
};
