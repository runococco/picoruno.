/* ポップコーン連鎖：Boomshine 系。1タップで爆発→ふれた粒が連鎖。目標数でクリア、失敗3回で終了。 */
const AX=20,AY=150,AW=W-40,AH=530;
const GAME={...META,sprites:['icon','kernel','pop'],unit:'点',comboHud:false,
  bgm:{bpm:112,root:62,scale:'major',prog:[1,6,2,5],seed:73,lead:'triangle',drums:'pop',density:.5},
  ranks:[[0,'コーンの粒'],[100,'ポップコーン屋さん'],[300,'連鎖マニア'],[700,'大連鎖職人'],[1300,'ポップコーンの魔術師'],[2200,'ポップコーン大爆発']],
  shareText:(v,f)=>`ポップコーン連鎖で ${f}点！`,
  icon(c,x,y,s){this.pop(c,x,y+s*.02,s*.32,1);this.kernel(c,x-s*.34,y+s*.3,s*.08,0);this.kernel(c,x+s*.32,y-s*.32,s*.08,1);this.pop(c,x+s*.3,y+s*.28,s*.13,1);this.pop(c,x-s*.3,y-s*.3,s*.12,1)},
  kernel(c,x,y,r,rot){c.save();c.translate(x,y);c.rotate(rot);D.path(c,c=>{c.moveTo(0,-r*1.3);c.bezierCurveTo(r*1.3,-r*.8,r*1.1,r*1.1,0,r*1.1);c.bezierCurveTo(-r*1.1,r*1.1,-r*1.3,-r*.8,0,-r*1.3)},'#f5c94c',Math.max(2,r*.25));c.restore();D.face(c,x,y+r*.15,r*1.5,'smile')},
  pop(c,x,y,r,k){const lw=Math.max(2,r*.08);D.path(c,c=>{for(let i=0;i<7;i++){const a=i/7*Math.PI*2,px=x+Math.cos(a)*r*.55,py=y+Math.sin(a)*r*.5;c.moveTo(px+r*.45,py);c.arc(px,py,r*.45,0,7)}},'#fffbf0',lw);
    c.fillStyle='#fffbf0';c.beginPath();c.arc(x,y,r*.7,0,7);c.fill();c.fillStyle='rgba(245,201,76,.6)';c.beginPath();c.arc(x+r*.2,y+r*.35,r*.15,0,7);c.fill();D.face(c,x,y,r*.8,k>.5?'smile':'o')},
  reset(api){this.st={lv:1,lives:3,ks:[],pops:[],phase:'aim',msgT:0,msg:'',chain:0,cleared:0};api.score=0;this.setup()},
  setup(){const st=this.st,n=Math.min(70,6+st.lv*4);st.need=Math.min(Math.round(n*.85),Math.max(2,Math.round(n*(.15+st.lv*.06))));st.ks=[];st.pops=[];st.chain=0;st.phase='aim';
    for(let i=0;i<n;i++){const a=rnd(Math.PI*2),sp=rnd(30,60)+st.lv*2;st.ks.push({x:rnd(AX+20,AX+AW-20),y:rnd(AY+20,AY+AH-20),vx:Math.cos(a)*sp,vy:Math.sin(a)*sp,rot:rnd(6),vr:rnd(-2,2)})}},
  down(x,y,api){const st=this.st;if(st.phase!=='aim'||y<AY||y>AY+AH)return;st.phase='chain';st.pops.push({x,y,t:0,r:0,src:true});S.boing(1.5);api.ring(x,y,{c:'#e76f51',r:46})},
  update(dt,api){const st=this.st,RM=40,GROW=.18,HOLD=1.0,SHR=.3;
    for(const k of st.ks){k.x+=k.vx*dt;k.y+=k.vy*dt;k.rot+=k.vr*dt;if(k.x<AX+10||k.x>AX+AW-10)k.vx*=-1;if(k.y<AY+10||k.y>AY+AH-10)k.vy*=-1;k.x=clamp(k.x,AX+10,AX+AW-10);k.y=clamp(k.y,AY+10,AY+AH-10)}
    for(const p of st.pops){p.t+=dt;const t=p.t;p.r=t<GROW?RM*ease.outBack(t/GROW):t<GROW+HOLD?RM:RM*Math.max(0,1-(t-GROW-HOLD)/SHR)}
    for(let i=st.ks.length-1;i>=0;i--){const k=st.ks[i];for(const p of st.pops){if(p.r>0&&dist(k.x,k.y,p.x,p.y)<p.r+8){
      st.ks.splice(i,1);st.chain++;api.combo=st.chain;st.pops.push({x:k.x,y:k.y,t:0,r:0});const pts=st.chain;api.score+=pts;
      S.pop(Math.pow(2,Math.min(st.chain,30)/14)*.8);api.burst(k.x,k.y,{c:['#fffbf0','#f5c94c'],n:6,sp:180,r:4,shape:'o'});api.float(k.x,k.y-20,'+'+pts,{size:16+Math.min(st.chain,20)*.6});
      if(st.chain===st.need){S.perfect();api.flash('#fff',.3);api.float(W/2,AY+40,'目標たっせい！',{c:'#f5c94c',size:30})}
      if(st.chain%10===0){api.shake(6);S.combo(st.chain/4)}break}}}
    st.pops=st.pops.filter(p=>p.t<GROW+HOLD+SHR);
    if(st.phase==='chain'&&st.pops.length===0){
      if(st.chain>=st.need){const bonus=st.lv*10+(st.ks.length===0?st.lv*20:0);api.score+=bonus;st.msg=st.ks.length===0?'パーフェクト！ +'+bonus:'クリア！ +'+bonus;S.fanfare();st.lv++;st.ok=true;if(st.ks.length===0){api.flash('#f5c94c',.4);api.burst(W/2,H/2,{c:['#f5c94c','#fff','#e76f51'],n:40,sp:400,shape:'star'})}}
      else{st.lives--;st.msg='ざんねん…';S.bad();api.shake(8);st.ok=false}
      st.phase='msg';st.msgT=1.3;api.combo=0}
    if(st.phase==='msg'){st.msgT-=dt;if(st.msgT<=0){if(st.lives<=0){api.end();return}this.setup()}}
  },
  overText:'おしまい！',
  draw(c,api){const st=this.st;c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.fillStyle='#f6dfb6';for(let i=0;i<12;i++)for(let j=0;j<20;j++)if((i+j)%2)c.fillRect(i*40,j*40,40,40);
    D.rrect(c,AX,AY,AW,AH,30,'#c0553f',4);D.rrect(c,AX+10,AY+10,AW-20,AH-20,24,'#8f3d2e',3);
    for(const k of st.ks)this.kernel(c,k.x,k.y,9,k.rot);
    for(const p of st.pops)if(p.r>1)this.pop(c,p.x,p.y,p.r,p.t);
    D.text(c,'ステージ '+st.lv,30,112,18,'#5b4d45','left');
    D.text(c,'のこり',W-110,112,13,'#8e8077','left');for(let i=0;i<3;i++)this.kernel(c,W-50+i*16-10,112,6,0),i>=st.lives&&(c.fillStyle='rgba(251,236,208,.8)',c.fillRect(W-50+i*16-19,100,18,24));
    const pr=Math.min(1,st.chain/st.need);D.rrect(c,AX+30,AY+AH+12,AW-60,20,10,'#fffdf8',3);if(pr>0)D.rrect(c,AX+32,AY+AH+14,(AW-64)*pr,16,8,pr>=1?'#7cb35f':'#e76f51',0);
    D.text(c,(st.chain>1?st.chain+'連鎖  ':'')+st.chain+' / '+st.need,W/2,AY+AH+22,14,'#5b4d45');
    if(st.phase==='aim'&&api.state==='play'){c.globalAlpha=.6+.4*Math.sin(api.t*5);D.text(c,'どこか1か所タップ！',W/2,AY+AH/2,24,'#fff','center',OL,6);c.globalAlpha=1}
    if(st.phase==='msg'){D.text(c,st.msg,W/2,AY+AH/2,36,st.ok?'#fff':'#f3b0a6','center',OL,9)}
  },
  __bot(api){const st=this.st;if(st.phase!=='aim')return;let best=null,bn=-1;for(const k of st.ks){let n=0;for(const q of st.ks)if(dist(k.x,k.y,q.x,q.y)<60)n++;if(n>bn){bn=n;best=k}}if(best)this.down(best.x,best.y,api)},
};
