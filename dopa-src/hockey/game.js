/* ぺちぺちホッケー：エアホッケー。3点先取で勝ち抜き。相手は勝つたびに強くなる。 */
const TL=30,TR=390,TT=140,TB=700,GW=130,MR=30,PKR=18,MID=(TT+TB)/2;
const RIV=[{n:'まるまる',c:'#9cc86a',sp:260,re:.5},{n:'ぷるぷる',c:'#7fb2e0',sp:340,re:.38},{n:'もちもち',c:'#f2a5c0',sp:420,re:.28},{n:'ぴかぴか',c:'#f2c84b',sp:520,re:.2},{n:'ごろごろ',c:'#a07bd0',sp:620,re:.13},{n:'ぼす',c:'#e2645a',sp:760,re:.08}];
const GAME={...META,sprites:['icon','mallet','puck'],unit:'人ぬき',hudUnit:false,fullBleed:true,comboHud:false,countdown:true,
  bgm:{bpm:140,root:57,scale:'minor',prog:[1,6,3,7],seed:52,lead:'square',drums:'four',density:.6},
  ranks:[[0,'ざんねん'],[1,'ホッケーデビュー'],[2,'カンカン上手'],[3,'リンクの主'],[4,'ホッケー名人'],[6,'無敵のマレット']],
  shareText:(v,f)=>`ぺちぺちホッケーで ${f}人ぬき！`,
  icon(c,x,y,s){this.mallet(c,x+s*.15,y-s*.18,s*.22,'#7fb2e0','angry');this.puck(c,x-s*.05,y+s*.02,s*.12);this.mallet(c,x-s*.15,y+s*.25,s*.24,'#f08a8a','smile')},
  mallet(c,x,y,r,col,mood){D.circle(c,x,y,r,col);c.globalAlpha=.12;D.circle(c,x,y,r*.72,'#5b4d45',0);c.globalAlpha=1;D.circle(c,x,y,r*.62,col,Math.max(2,r*.08));D.face(c,x,y+r*.05,r*.85,mood)},
  puck(c,x,y,r){D.circle(c,x,y,r,'#5b5560');D.circle(c,x,y,r*.6,'#6d6672',0)},
  reset(api){this.st={lv:0,my:0,cp:0,p:null,me:{x:W/2,y:TB-80,vx:0,vy:0,tx:W/2,ty:TB-80},cpu:{x:W/2,y:TT+80,vx:0,vy:0},serve:1,wait:1,t:0,flash:0};this.newRound(1);api.score=0},
  newRound(to){const st=this.st;st.p={x:W/2,y:to>0?MID+70:MID-70,vx:0,vy:0};st.wait=.8},
  down(x,y){const m=this.st.me;m.tx=x;m.ty=y-20},move(x,y){const m=this.st.me;m.tx=x;m.ty=y-20},
  keyRepeat:true,key(k){const m=this.st.me;if(k==='ArrowLeft')m.tx-=30;if(k==='ArrowRight')m.tx+=30;if(k==='ArrowUp')m.ty-=30;if(k==='ArrowDown')m.ty+=30},
  mv(m,tx,ty,maxsp,dt,top){tx=clamp(tx,TL+MR,TR-MR);ty=top?clamp(ty,TT+MR,MID-MR):clamp(ty,MID+MR,TB-MR);let dx=tx-m.x,dy=ty-m.y,d=Math.hypot(dx,dy),s=Math.min(d,maxsp*dt);const nx=d?m.x+dx/d*s:m.x,ny=d?m.y+dy/d*s:m.y;m.vx=(nx-m.x)/Math.max(dt,1e-3);m.vy=(ny-m.y)/Math.max(dt,1e-3);m.x=nx;m.y=ny},
  collide(m,p,api){const d=dist(m.x,m.y,p.x,p.y),rr=MR+PKR;if(d<rr&&d>0){const nx=(p.x-m.x)/d,ny=(p.y-m.y)/d;p.x=m.x+nx*rr;p.y=m.y+ny*rr;const rv=(p.vx-m.vx)*nx+(p.vy-m.vy)*ny;if(rv<0){p.vx-=1.9*rv*nx;p.vy-=1.9*rv*ny;const sp=Math.hypot(p.vx,p.vy);if(sp>1300){p.vx*=1300/sp;p.vy*=1300/sp}
      const t=performance.now();if(!this.lh||t-this.lh>80){this.lh=t;S.tone(900,.05,{type:'square',v:.2});S.noise(.04,{v:.4,f:3000});if(sp>700){api.shake(4);api.burst(p.x,p.y,{c:'#fff',n:6,sp:150,r:3})}}}}},
  update(dt,api){const st=this.st,p=st.p,me=st.me,cpu=st.cpu,R=RIV[Math.min(st.lv,RIV.length-1)];st.t+=dt;st.flash-=dt;
    this.mv(me,me.tx,me.ty,2600,dt,false);
    // CPU：パックが自陣なら打ちにいく、そうでなければゴール前で守る
    const react=p.y<MID+40&&p.vy<=60;let tx,ty;if(react){tx=p.x+(p.x-W/2)*.15;ty=p.y-26}else{tx=W/2+(p.x-W/2)*.5;ty=TT+70}
    if(st.wait>0){tx=W/2;ty=TT+70}
    st.cpuT=(st.cpuT||0)-dt;if(st.cpuT<=0){st.cpuT=R.re;st.ctx=tx+rnd(-10,10);st.cty=ty}this.mv(cpu,st.ctx??W/2,st.cty??TT+70,R.sp,dt,true);
    if(st.wait>0){st.wait-=dt;return}
    const sub=4,h=dt/sub;for(let s=0;s<sub;s++){p.x+=p.vx*h;p.y+=p.vy*h;
      if(p.x<TL+PKR){p.x=TL+PKR;p.vx=Math.abs(p.vx)*.9;S.tap(.6)}if(p.x>TR-PKR){p.x=TR-PKR;p.vx=-Math.abs(p.vx)*.9;S.tap(.6)}
      const inG=Math.abs(p.x-W/2)<GW/2;
      if(p.y<TT+PKR&&!inG){p.y=TT+PKR;p.vy=Math.abs(p.vy)*.9;S.tap(.6)}if(p.y>TB-PKR&&!inG){p.y=TB-PKR;p.vy=-Math.abs(p.vy)*.9;S.tap(.6)}
      if(p.y<TT-10){this.goal(1,api);return}if(p.y>TB+10){this.goal(-1,api);return}
      this.collide(me,p,api);this.collide(cpu,p,api)}
    const f=Math.pow(.75,dt);p.vx*=f;p.vy*=f;
    // 止まりそうなら少し動かす
    if(Math.hypot(p.vx,p.vy)<20&&Math.abs(p.y-MID)<20)p.vy+=(Math.random()<.5?-1:1)*60},
  goal(who,api){const st=this.st;if(who>0){st.my++;S.perfect();api.flash('#fff6c8',.5);api.float(W/2,MID,'ゴール！',{size:44,c:'#f3c84b'});api.burst(W/2,TT,{c:['#f4d66d','#fff','#e2645a'],n:24,shape:'star',sp:300})}
    else{st.cp++;S.bad();api.shake(10);api.float(W/2,MID,'とられた…',{size:34})}
    if(st.my>=3){st.lv++;api.score=st.lv;S.fanfare();api.float(W/2,MID+60,'勝ち！ つぎの相手へ',{size:24,c:'#fff',life:1.4});st.my=st.cp=0;st.wait=1.8;st.cpu.x=W/2;st.cpu.y=TT+70;this.st.p={x:W/2,y:MID+70,vx:0,vy:0};return}
    if(st.cp>=3){api.end();return}this.newRound(who>0?-1:1)},
  overText:'まけちゃった…',
  drawHud(c,api){const st=this.st,R=RIV[Math.min(st.lv,RIV.length-1)];D.rrect(c,40,20,340,60,30,'#fffdf8',3.5);
    this.mallet(c,80,50,18,R.c,'angry');D.text(c,(st.lv+1)+'人め '+R.n,170,50,18,'#5b4d45');D.text(c,st.my+' - '+st.cp,320,50,28,'#5b4d45')},
  draw(c,api){const st=this.st,R=RIV[Math.min(st.lv,RIV.length-1)];c.fillStyle='#c9cfe0';c.fillRect(0,api.top,W,api.bottom-api.top);
    D.rrect(c,TL-14,TT-14,TR-TL+28,TB-TT+28,30,'#7d6aa8',4);c.fillStyle='#eef1f8';c.fillRect(TL,TT,TR-TL,TB-TT);
    c.strokeStyle='#e2a5b0';c.lineWidth=3;c.beginPath();c.moveTo(TL,MID);c.lineTo(TR,MID);c.stroke();c.beginPath();c.arc(W/2,MID,50,0,7);c.stroke();
    c.strokeStyle='#a9c7e6';c.beginPath();c.arc(W/2,TT,70,0,Math.PI);c.stroke();c.beginPath();c.arc(W/2,TB,70,Math.PI,0);c.stroke();
    c.fillStyle='#4b3e37';c.fillRect(W/2-GW/2,TT-14,GW,12);c.fillRect(W/2-GW/2,TB+2,GW,12);
    this.mallet(c,st.cpu.x,st.cpu.y,MR,R.c,'angry');this.puck(c,st.p.x,st.p.y,PKR);this.mallet(c,st.me.x,st.me.y,MR,'#f08a8a','smile')},
  __bot(api){const st=this.st,p=st.p;if(p.y>MID-20){st.me.tx=p.x+rnd(-8,8);st.me.ty=p.y+30}else{st.me.tx=W/2+(p.x-W/2)*.5;st.me.ty=TB-70}},
};
