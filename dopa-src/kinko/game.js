/* 金庫あけマスター：Pop the Lock 系。針が点に重なる間にタップ、通過したら失敗。 */
const CX=W/2,CY=360,RR=118,WIN=.2;
const GAME={...META,unit:'カチッ',hud:false,
  bgm:{bpm:132,root:57,scale:'minor',prog:[1,4,7,3],seed:66,lead:'square',drums:'four',density:.6},
  ranks:[[0,'鍵をなくした人'],[10,'見習い錠前師'],[25,'金庫の常連'],[45,'金庫あけ職人'],[70,'伝説の大泥棒（ねこ）'],[100,'金庫の方から開く']],
  shareText:(v,f)=>`金庫あけマスターで ${f}カチッ！`,
  icon(c,x,y,s){this.safe(c,x,y,s*.8,0,-.6,true)},
  safe(c,x,y,s,lv,ang,small){const k=s/300;D.rrect(c,x-s*.5,y-s*.5,s,s,s*.08,'#7c8a96',Math.max(2,4*k));D.rrect(c,x-s*.44,y-s*.44,s*.88,s*.88,s*.05,'#93a1ac',Math.max(1.5,3*k));
    D.circle(c,x,y,s*.33,'#4b5560',Math.max(2,4*k));D.circle(c,x,y,s*.26,'#e9e3d3',Math.max(2,3*k));
    if(small){c.save();c.translate(x,y);c.rotate(ang);D.rrect(c,-s*.02,-s*.26,s*.04,s*.18,s*.02,'#e2645a',2);c.restore();D.face(c,x,y+s*.06,s*.2,'smile')}},
  reset(api){this.st={lv:1,left:0,a:-Math.PI/2,dir:1,w:1.8,dot:0,inside:false,open:0,coins:[],fail:0};this.newLv();api.score=0},
  newLv(){const st=this.st;st.left=Math.min(5+st.lv*2,30);st.w=1.7+st.lv*.18;st.open=0;st.dir=st.lv%2?1:-1;this.newDot()},
  newDot(){const st=this.st;st.dot=st.a+st.dir*rnd(.9,2.7);st.inside=false},
  ad(a,b){let d=(a-b)%(Math.PI*2);if(d>Math.PI)d-=Math.PI*2;if(d<-Math.PI)d+=Math.PI*2;return d},
  tap(api){const st=this.st;if(st.open>0)return;const d=Math.abs(this.ad(st.a,st.dot));
    if(d<WIN){st.left--;api.score++;api.combo++;S.tick();S.good(1+(api.combo%10)*.05);api.hitstop(30);api.shake(3);
      const px=CX+Math.cos(st.dot)*RR,py=CY+Math.sin(st.dot)*RR;api.burst(px,py,{c:['#f3c84b','#fff'],n:10,sp:200,shape:'star',r:4});api.ring(px,py,{c:'#f3c84b',r:40});
      if(d<.06){api.score++;api.float(px,py-30,'ジャスト +2',{c:'#f3c84b',size:22})}
      if(st.left<=0){st.open=.01;S.fanfare();api.flash('#fff',.6);api.shake(12);api.float(CX,CY-200,'ガチャン！ ひらいた！',{size:34});
        for(let i=0;i<40;i++)st.coins.push({x:CX+rnd(-40,40),y:CY,vx:rnd(-300,300),vy:rnd(-700,-300),r:rnd(6,12),c:pick(['#f3c84b','#f3c84b','#7fc6d8','#e2645a','#9fd27c']),rot:rnd(6)});
        api.score+=st.lv*5;api.float(CX,CY+190,'ボーナス +'+st.lv*5,{c:'#f3c84b',size:26})}
      else{st.dir*=-1;this.newDot()}}
    else this.fail(api)},
  fail(api){const st=this.st;S.bad();api.shake(12);api.flash('#e2645a',.35);api.combo=0;api.end()},
  down(x,y,api){this.tap(api)},key(k,api){if(k===' '||k==='Enter')this.tap(api)},
  update(dt,api){const st=this.st;
    for(const c of st.coins){c.vy+=1300*dt;c.x+=c.vx*dt;c.y+=c.vy*dt;c.rot+=dt*8;if(c.y>H-70){c.y=H-70;c.vy*=-.4;c.vx*=.7}}
    if(st.open>0){st.open+=dt;if(st.open>1.6){st.lv++;st.coins=st.coins.filter(c=>c.y<H-80||Math.random()<.5).slice(-40);this.newLv()}return}
    st.a+=st.dir*st.w*dt;const d=this.ad(st.a,st.dot);
    if(Math.abs(d)<WIN)st.inside=true;else if(st.inside&&Math.sign(d)===st.dir)this.fail(api)},
  overText:'ハズレ！',
  draw(c,api){const st=this.st;c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.fillStyle='#ddd8e2';for(let i=0;i<10;i++)c.fillRect(0,i*80,W,40);
    D.rrect(c,-20,H-70,W+40,120,0,'#b49b84',4);
    for(const co of st.coins){c.save();c.translate(co.x,co.y);c.scale(Math.abs(Math.cos(co.rot))*.8+.2,1);D.circle(c,0,0,co.r,co.c,2.5);c.restore()}
    const op=st.open>0?ease.out(Math.min(1,st.open*3)):0;
    // 金庫本体
    D.rrect(c,CX-170,CY-170,340,340,26,'#7c8a96',4.5);D.rrect(c,CX-158,CY-158,316,316,20,'#4b5560',4);
    if(op>0){D.rrect(c,CX-150,CY-150,300,300,16,'#2e3438',3);c.fillStyle='#f3c84b';c.globalAlpha=.6;c.beginPath();c.arc(CX,CY+60,90,0,7);c.fill();c.globalAlpha=1}
    c.save();c.translate(CX-158,CY);c.scale(1-op*.85,1);c.translate(-(CX-158),-CY);
    D.rrect(c,CX-152,CY-152,304,304,18,'#93a1ac',4);
    // ダイヤル
    c.lineWidth=26;c.strokeStyle='#4b5560';c.beginPath();c.arc(CX,CY,RR,0,7);c.stroke();c.lineWidth=4;c.strokeStyle=OL;c.beginPath();c.arc(CX,CY,RR+13,0,7);c.stroke();c.beginPath();c.arc(CX,CY,RR-13,0,7);c.stroke();
    if(api.state!=='title'&&st.open<=0){const px=CX+Math.cos(st.dot)*RR,py=CY+Math.sin(st.dot)*RR,gl=.5+.5*Math.sin(api.t*12);D.circle(c,px,py,11+gl*2,'#f3c84b',3)}
    D.circle(c,CX,CY,RR-20,'#e9e3d3',4);D.text(c,st.left,CX,CY+4,56,'#4a3428');D.text(c,'のこり',CX,CY-44,14,'#7a6658');
    c.save();c.translate(CX,CY);c.rotate(st.a);D.rrect(c,RR-22,-6,44,12,6,'#e2645a',3);c.restore();
    c.restore();
    D.text(c,'金庫 '+st.lv+'こめ',CX,CY+210,22,'#4a3428');D.text(c,api.score+' カチッ',CX,90,34,'#fff','center',OL,8);
  },
  __bot(api){const st=this.st;if(st.open>0)return;if(Math.abs(this.ad(st.a,st.dot))<.08)this.tap(api)},
};
