/* たこ焼きにつまようじ：Knife Hit 系。回転パターンはステージごとに変化。 */
const CX=W/2,CY=270,R=82,PL=78,TH=0.17;
const GAME={...META,unit:'本',hudUnit:true,
  bgm:{bpm:136,root:62,scale:'minor',prog:[1,7,6,5],seed:88,lead:'square',drums:'four'},
  ranks:[[0,'つまようじ見習い'],[15,'屋台の手伝い'],[35,'たこ焼き屋さん'],[60,'くるくる職人'],[90,'つまようじの名手'],[130,'大阪の伝説']],
  shareText:(v,f)=>`たこ焼きにつまようじ ${f}本 さした！`,
  icon(c,x,y,s){this.tako(c,x,y+s*.05,s*.32,0,1);[[-.6,1],[.4,1],[2.2,1]].forEach(([a])=>this.pick(c,x+Math.cos(a-Math.PI/2)*s*.32,y+s*.05+Math.sin(a-Math.PI/2)*s*.32,a,s*.3))},
  tako(c,x,y,r,rot,face){c.save();c.translate(x,y);c.rotate(rot);D.circle(c,0,0,r,'#e7a35c',Math.max(2,r*.05));
    D.path(c,c=>{c.moveTo(-r*.85,-r*.3);c.bezierCurveTo(-r*.6,-r*1.05,r*.6,-r*1.05,r*.85,-r*.3);c.bezierCurveTo(r*.6,-r*.05,r*.2,-r*.25,0,-r*.1);c.bezierCurveTo(-r*.3,-r*.25,-r*.6,0,-r*.85,-r*.3)},'#8a4a2c',0);
    c.strokeStyle='#fffbf0';c.lineWidth=r*.06;c.lineCap='round';c.beginPath();for(let i=0;i<6;i++){c.lineTo(-r*.55+i*r*.22,-r*.58+(i%2)*r*.22)}c.stroke();
    c.fillStyle='#6fa457';for(let i=0;i<9;i++){const a=i*2.4,d=r*(.2+((i*37)%10)/14);c.fillRect(Math.cos(a)*d*.8-2,-r*.45+Math.sin(a)*d*.25-2,4,4)}
    c.restore();if(face)D.face(c,x,y+r*.3,r*.75,face===1?'smile':face)},
  pick(c,x,y,a,len=PL){c.save();c.translate(x,y);c.rotate(a);D.rrect(c,-3,0,6,len,3,'#f1d7a6',2.5);c.fillStyle='#d7b77e';c.fillRect(-2,len*.72,4,3);c.restore()},
  reset(api){this.st={stage:0,rot:0,vel:0,picks:[],bonus:[],fly:null,left:0,need:0,drop:[],clearT:0,t:0,shards:[]};this.nextStage(api);api.score=0},
  nextStage(api){const st=this.st;st.stage++;st.need=Math.min(14,5+st.stage);st.left=st.need;st.picks=[];st.bonus=[];st.t=0;st.clearT=0;st.mode=st.stage%5===0?'boss':pick(['const','wave','rev','jerk']);if(st.stage<3)st.mode='const';
    st.base=(1.6+st.stage*.12)*(Math.random()<.5?1:-1);
    const pre=Math.min(st.stage-1,5);for(let i=0;i<pre;i++)st.picks.push({a:i/pre*Math.PI*2+rnd(.3),pre:true});
    for(let i=0;i<(st.stage>1?rndi(1,2):0);i++){let a;do a=rnd(Math.PI*2);while(st.picks.some(p=>Math.abs(this.ad(p.a,a))<.35));st.bonus.push({a})}},
  ad(a,b){let d=(a-b)%(Math.PI*2);if(d>Math.PI)d-=Math.PI*2;if(d<-Math.PI)d+=Math.PI*2;return d},
  throw_(api){const st=this.st;if(st.fly||st.clearT>0||st.left<=0)return;st.fly={y:H-120};st.left--;S.whoosh()},
  down(x,y,api){this.throw_(api)},key(k,api){if(k===' '||k==='Enter')this.throw_(api)},
  update(dt,api){const st=this.st;st.t+=dt;
    const m=st.mode,b=st.base;st.vel=m==='const'?b:m==='wave'?b*(.4+1.2*Math.abs(Math.sin(st.t*1.2))):m==='rev'?b*Math.sign(Math.sin(st.t*.9)+.3)*1.2:m==='jerk'?b*(Math.sin(st.t*2.5)>0?1.8:.3):b*1.3*Math.sin(st.t*.8)*1.6+b*.3;
    st.rot+=st.vel*dt;
    if(st.clearT>0){st.clearT-=dt;for(const s of st.shards){s.vy+=1200*dt;s.x+=s.vx*dt;s.y+=s.vy*dt;s.r+=s.vr*dt}if(st.clearT<=0){st.shards=[];this.nextStage(api)}return}
    if(st.fly){st.fly.y-=2600*dt;if(st.fly.y<=CY+R){const la=Math.PI/2-st.rot;st.fly=null;
      const hit=st.picks.find(p=>Math.abs(this.ad(p.a,la))<TH);
      if(hit){S.zap();S.bad();api.shake(14);api.flash('#e2645a',.35);st.drop.push({x:CX,y:CY+R,vx:rnd(-200,200),vy:-300,r:0,vr:rnd(-12,12)});api.end();return}
      st.picks.push({a:la,t:0});api.score++;S.thud();S.tick();api.shake(4);api.hitstop(30);api.burst(CX,CY+R,{c:['#e7a35c','#8a4a2c'],n:8,sp:180,r:3});st.kick=.12;
      const bi=st.bonus.findIndex(q=>Math.abs(this.ad(q.a,la))<.25);if(bi>=0){st.bonus.splice(bi,1);api.score+=3;S.coin();api.float(CX,CY+R+40,'かつおぶし +3',{c:'#f3c84b',size:24});api.burst(CX,CY+R,{c:['#f2d9a0','#d9a86a'],n:16,sp:260,shape:'s'})}
      if(st.left<=0){st.clearT=1.1;S.fanfare();api.flash('#fff',.5);api.shake(10);api.float(CX,CY,'クリア！',{size:42,life:1});
        for(let i=0;i<10;i++){const a=i/10*Math.PI*2;st.shards.push({x:CX,y:CY,vx:Math.cos(a)*rnd(150,400),vy:Math.sin(a)*rnd(150,400)-200,r:a,vr:rnd(-8,8),a})}
        for(const p of st.picks){const wa=p.a+st.rot;st.drop.push({x:CX+Math.cos(wa)*R,y:CY+Math.sin(wa)*R,vx:Math.cos(wa)*300,vy:Math.sin(wa)*300-200,r:wa-Math.PI/2,vr:rnd(-10,10)})}}}}
    st.kick=Math.max(0,(st.kick||0)-dt);
    for(const d of st.drop){d.vy+=1500*dt;d.x+=d.vx*dt;d.y+=d.vy*dt;d.r+=d.vr*dt}st.drop=st.drop.filter(d=>d.y<H+100)},
  overUpdate(dt){const st=this.st;for(const d of st.drop){d.vy+=1500*dt;d.x+=d.vx*dt;d.y+=d.vy*dt;d.r+=d.vr*dt}},
  draw(c,api){const st=this.st;c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.fillStyle='#efd2ad';for(let i=0;i<6;i++){c.beginPath();c.arc(CX,CY,140+i*90,0,7);c.lineWidth=30;c.strokeStyle='#efd2ad';c.stroke()}
    D.rrect(c,-20,H-80,W+40,120,0,'#c9894f',4);
    const ky=CY-(st.kick||0)*40;
    if(st.clearT>0){for(const s of st.shards){c.save();c.translate(s.x,s.y);c.rotate(s.r);D.path(c,c=>{c.moveTo(0,0);c.arc(0,0,R*.6,0,.63);c.closePath()},'#e7a35c',3);c.restore()}}
    else{for(const p of st.picks){const wa=p.a+st.rot;this.pick(c,CX+Math.cos(wa)*(R-14),ky+Math.sin(wa)*(R-14),wa-Math.PI/2)}
      for(const q of st.bonus){const wa=q.a+st.rot,x=CX+Math.cos(wa)*(R+14),y=ky+Math.sin(wa)*(R+14);c.save();c.translate(x,y);c.rotate(wa+Math.PI/2);D.poly(c,[[-14,-6],[12,-10],[15,6],[-10,9]],'#f2d9a0',2.5);c.restore()}
      this.tako(c,CX,ky,R,st.rot,api.state==='over'?'sad':st.stage%5===0?'angry':'smile')}
    for(const d of st.drop){c.save();c.translate(d.x,d.y);c.rotate(d.r);this.pick(c,0,-PL/2,0);c.restore()}
    if(st.fly)this.pick(c,CX,st.fly.y,0);
    else if(api.state==='play'&&st.left>0&&st.clearT<=0)this.pick(c,CX,H-120,0);
    // 残り本数
    for(let i=0;i<st.need;i++){const x=24,y=H-110-i*26;c.globalAlpha=i<st.left?1:.25;this.pick(c,x,y,-Math.PI/2,30);c.globalAlpha=1}
    D.text(c,st.stage%5===0?'ボス たこ焼き':'たこ焼き '+st.stage+'こめ',CX,CY+R+70,20,'#7a6658');
  },
  __bot(api){const st=this.st;if(st.fly)return;const la=Math.PI/2-st.rot;if(!st.picks.some(p=>Math.abs(this.ad(p.a,la))<.4)||Math.random()<.02)this.throw_(api)},
};
