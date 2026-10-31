/* ほしくずシューター：縦シューティング。自動連射、星でパワーアップ、30秒ごとにボス。 */
const GAME={...META,sprites:['icon','ufo','enemy','boss'],unit:'点',fullBleed:true,
  bgm:{bpm:150,root:57,scale:'minor',prog:[1,6,7,5],seed:61,lead:'square',drums:'four',density:.66},
  ranks:[[0,'見習いパイロット'],[1000,'星くずハンター'],[3000,'ぎんがのエース'],[6000,'流星の騎士'],[10000,'うちゅう最強'],[16000,'伝説のUFO']],
  shareText:(v,f)=>`ほしくずシューターで ${f}点！`,
  icon(c,x,y,s){this.enemy(c,x+s*.24,y-s*.28,s*.17,1);this.ufo(c,x-s*.06,y+s*.16,s*.75);c.fillStyle='#f4d66d';for(let i=0;i<3;i++){c.beginPath();c.ellipse(x-s*.06+(i-1)*s*.12,y-s*.3-i%2*s*.08,s*.03,s*.07,0,0,7);c.fill()}},
  ufo(c,x,y,s){const k=s/60;D.group(c,()=>{D.ellipse(c,x,y-6*k,16*k,16*k,'#bfe3ee');D.ellipse(c,x,y+4*k,30*k,11*k,'#f2a5c0')});D.face(c,x,y-7*k,16*k);
    c.fillStyle='#f4d66d';for(const i of[-1,0,1]){c.beginPath();c.arc(x+i*14*k,y+5*k,2.5*k,0,7);c.fill()}},
  enemy(c,x,y,r,k,hurt){const col=['#a7a3ad','#c9a0e0','#8fbfd6'][k%3];D.path(c,c=>{c.arc(x-r*.45,y+r*.15,r*.55,Math.PI*.5,Math.PI*1.5);c.arc(x,y-r*.3,r*.6,Math.PI*1.1,Math.PI*1.9);c.arc(x+r*.5,y+r*.1,r*.55,Math.PI*1.5,Math.PI*.5);c.closePath()},hurt?'#fff':col);D.face(c,x,y+r*.05,r*.9,k===1?'angry':'flat')},
  boss(c,x,y,s,hurt){D.group(c,()=>{for(let i=0;i<6;i++){const a=i/6*Math.PI*2;D.circle(c,x+Math.cos(a)*s*.62,y+Math.sin(a)*s*.42,s*.36,hurt?'#fff':'#7d6aa8')}D.ellipse(c,x,y,s*.8,s*.55,hurt?'#fff':'#9b88c8')});D.face(c,x,y,s*.9,'angry')},
  reset(api){this.st={x:W/2,y:600,tx:W/2,ty:600,b:[],e:[],eb:[],items:[],pw:1,hp:3,inv:0,fire:0,spawn:1,t:0,boss:null,bossN:0,nextBoss:30,stars:[],kx:0,ky:0};
    for(let i=0;i<50;i++)this.st.stars.push([rnd(W),rnd(-100,H+100),rnd(.3,1)]);api.score=0},
  down(x,y){this.st.drag={x,y,sx:this.st.tx,sy:this.st.ty}},
  move(x,y){const d=this.st.drag;if(!d)return;this.st.tx=clamp(d.sx+(x-d.x)*1.2,24,W-24);this.st.ty=clamp(d.sy+(y-d.y)*1.2,160,H-30)},
  up(){this.st.drag=null},keyRepeat:true,
  key(k){const st=this.st;if(k==='ArrowLeft')st.kx=-1;if(k==='ArrowRight')st.kx=1;if(k==='ArrowUp')st.ky=-1;if(k==='ArrowDown')st.ky=1},keyUp(k){const st=this.st;if(k==='ArrowLeft'||k==='ArrowRight')st.kx=0;if(k==='ArrowUp'||k==='ArrowDown')st.ky=0},
  hurt(api){const st=this.st;if(st.inv>0)return;st.hp--;st.inv=1.6;st.pw=Math.max(1,st.pw-1);S.bad();api.shake(10);api.flash('#e2645a',.35);if(st.hp<=0){S.boom();api.burst(st.x,st.y,{c:['#f2a5c0','#bfe3ee','#fff'],n:30,sp:300});api.end()}},
  update(dt,api){const st=this.st;st.t+=dt;st.inv-=dt;
    if(st.kx||st.ky){st.tx=clamp(st.tx+st.kx*360*dt,24,W-24);st.ty=clamp(st.ty+st.ky*360*dt,160,H-30)}
    st.x+=(st.tx-st.x)*Math.min(1,dt*18);st.y+=(st.ty-st.y)*Math.min(1,dt*18);
    for(const s of st.stars){s[1]+=(60+s[2]*160)*dt;if(s[1]>H+100){s[1]=-100;s[0]=rnd(W)}}
    st.fire-=dt;if(st.fire<=0){st.fire=.11;const n=Math.min(st.pw,5),spr=.13;for(let i=0;i<n;i++){const a=-Math.PI/2+(i-(n-1)/2)*spr;st.b.push({x:st.x,y:st.y-26,vx:Math.cos(a)*720,vy:Math.sin(a)*720})}S.tone(1200,.03,{v:.04,type:'square'})}
    for(let i=st.b.length-1;i>=0;i--){const b=st.b[i];b.x+=b.vx*dt;b.y+=b.vy*dt;if(b.y<-20||b.x<-20||b.x>W+20)st.b.splice(i,1)}
    // 出現
    if(!st.boss){st.spawn-=dt;if(st.spawn<=0){const lv=Math.min(1,st.t/90);st.spawn=rnd(.45,.9)-lv*.25;const k=rndi(0,2),x=rnd(40,W-40);
        const n=Math.random()<.3?4:1;for(let i=0;i<n;i++)st.e.push({x:n>1?60+i*100:x,y:-30-(n>1?i*30:0),r:k===2?30:24,k,hp:k===2?4+Math.floor(lv*4):2+Math.floor(lv*3),vy:rnd(90,140)+lv*60,t:rnd(7),hit:0,shot:rnd(1,3)})}
      if(st.t>=st.nextBoss&&!st.e.length){st.bossN++;st.boss={x:W/2,y:-100,hp:120+st.bossN*90,max:120+st.bossN*90,t:0,hit:0,shot:1};S.zap(.5);api.float(W/2,300,'ボスあらわる！',{size:36,c:'#e2645a',life:1.4})}}
    else{const B=st.boss;B.t+=dt;B.y+=(160-B.y)*Math.min(1,dt*2);B.x=W/2+Math.sin(B.t*.9)*120;B.hit-=dt;B.shot-=dt;
      if(B.shot<=0&&B.y>120){B.shot=Math.max(.5,1.4-st.bossN*.15);const n=8+st.bossN*2;for(let i=0;i<n;i++){const a=i/n*Math.PI*2+B.t;st.eb.push({x:B.x,y:B.y,vx:Math.cos(a)*150,vy:Math.sin(a)*150+40})}S.zap(.7)}
      for(let i=st.b.length-1;i>=0;i--){const b=st.b[i];if(Math.abs(b.x-B.x)<70&&Math.abs(b.y-B.y)<50){st.b.splice(i,1);B.hp--;B.hit=.05;api.add(5)}}
      if(B.hp<=0){api.add(2000*st.bossN);S.boom();S.fanfare();api.shake(16);api.flash('#fff',.7);for(let i=0;i<5;i++)api.burst(B.x+rnd(-60,60),B.y+rnd(-40,40),{c:['#f4d66d','#9b88c8','#fff'],n:20,sp:340,shape:'star'});
        api.float(W/2,280,'ボスげきは！ +'+2000*st.bossN,{size:30,c:'#f3c84b',life:1.6});for(let i=0;i<3;i++)st.items.push({x:B.x+(i-1)*40,y:B.y,t:i===1?'heart':'star'});st.boss=null;st.nextBoss=st.t+30;st.eb.length=0}}
    for(let i=st.e.length-1;i>=0;i--){const e=st.e[i];e.t+=dt;e.y+=e.vy*dt;e.x+=Math.sin(e.t*2)*40*dt;e.hit-=dt;e.shot-=dt;
      if(e.k===1&&e.shot<=0&&e.y>0&&e.y<H*.6){e.shot=rnd(1.5,2.5);const a=Math.atan2(st.y-e.y,st.x-e.x);st.eb.push({x:e.x,y:e.y,vx:Math.cos(a)*200,vy:Math.sin(a)*200})}
      if(e.y>H+40){st.e.splice(i,1);continue}
      for(let j=st.b.length-1;j>=0;j--){const b=st.b[j];if(dist(b.x,b.y,e.x,e.y)<e.r){st.b.splice(j,1);e.hp--;e.hit=.05;if(e.hp<=0)break}}
      if(e.hp<=0){st.e.splice(i,1);api.combo++;st.ct=1.2;const p=100+Math.min(api.combo,50)*10;api.add(p);S.pop(1+Math.min(api.combo,20)*.03);api.burst(e.x,e.y,{c:['#fff','#c9a0e0','#bfe3ee'],n:12,sp:200});
        if(Math.random()<.14)st.items.push({x:e.x,y:e.y,t:Math.random()<.15&&st.hp<3?'heart':'star'});continue}
      if(dist(e.x,e.y,st.x,st.y)<e.r+16){e.hp=0;st.e.splice(i,1);this.hurt(api)}}
    st.ct=(st.ct||0)-dt;if(st.ct<=0)api.combo=0;
    for(let i=st.eb.length-1;i>=0;i--){const b=st.eb[i];b.x+=b.vx*dt;b.y+=b.vy*dt;if(b.y>H+20||b.y<-40||b.x<-20||b.x>W+20){st.eb.splice(i,1);continue}if(dist(b.x,b.y,st.x,st.y)<12){st.eb.splice(i,1);this.hurt(api)}}
    for(let i=st.items.length-1;i>=0;i--){const it=st.items[i];it.y+=110*dt;if(it.y>H+30){st.items.splice(i,1);continue}if(dist(it.x,it.y,st.x,st.y)<34){st.items.splice(i,1);
        if(it.t==='star'){st.pw++;S.perfect();api.float(clamp(st.x,90,W-90),st.y-50,st.pw>5?'+500':'パワーアップ！',{size:24,c:'#f3c84b'});if(st.pw>5)api.add(500)}else{st.hp=Math.min(3,st.hp+1);S.good();api.float(clamp(st.x,90,W-90),st.y-50,'ハート+1',{size:24,c:'#f2a5c0'})}}}},
  drawHud(c,api){D.text(c,api.score.toLocaleString(),W/2,48,32,'#fff','center',OL,8);const st=this.st;
    for(let i=0;i<3;i++){c.globalAlpha=i<st.hp?1:.25;D.path(c,c=>{const x=24+i*30,y=96;c.moveTo(x,y+8);c.bezierCurveTo(x-14,y-2,x-6,y-12,x,y-4);c.bezierCurveTo(x+6,y-12,x+14,y-2,x,y+8)},'#f2a5c0',2.5);c.globalAlpha=1}
    if(this.st.boss){const B=this.st.boss;D.rrect(c,90,82,240,14,7,'#fffdf8',2.5);D.rrect(c,91,83,238*Math.max(0,B.hp/B.max),12,6,'#e2645a',0)}
    if(api.combo>=2){D.text(c,api.combo+' COMBO',W-70,96,18,'#f4d66d','center',OL,5)}},
  draw(c,api){const st=this.st;c.fillStyle='#2f2b45';c.fillRect(0,api.top,W,api.bottom-api.top);
    for(const s of st.stars){c.globalAlpha=s[2];c.fillStyle='#e9e2f6';c.fillRect(s[0],s[1],2,2+s[2]*6)}c.globalAlpha=1;
    for(const it of st.items){if(it.t==='star')D.star(c,it.x,it.y,15,'#f4d66d',3,st.t*3);else D.path(c,c=>{const x=it.x,y=it.y;c.moveTo(x,y+10);c.bezierCurveTo(x-18,y-2,x-8,y-15,x,y-5);c.bezierCurveTo(x+8,y-15,x+18,y-2,x,y+10)},'#f2a5c0',3)}
    for(const e of st.e)this.enemy(c,e.x,e.y,e.r,e.k,e.hit>0);
    if(st.boss)this.boss(c,st.boss.x,st.boss.y,90,st.boss.hit>0);
    c.fillStyle='#f4d66d';for(const b of st.b){c.beginPath();c.ellipse(b.x,b.y,3.5,9,Math.atan2(b.vy,b.vx)+Math.PI/2,0,7);c.fill()}
    for(const b of st.eb){D.circle(c,b.x,b.y,6,'#f08a8a',2)}
    if(st.inv<=0||Math.floor(st.inv*12)%2)this.ufo(c,st.x,st.y,74)},
  __bot(api){const st=this.st;let tx=st.x;const tgt=st.boss||st.e.filter(e=>e.y>0).sort((a,b)=>b.y-a.y)[0];if(tgt)tx=tgt.x;
    const it=st.items[0];if(it)tx=it.x;let ty=600;for(const b of st.eb)if(Math.abs(b.y-st.y)<80&&Math.abs(b.x-st.x)<30)tx+=(b.x<st.x?60:-60);
    for(const e of st.e)if(Math.abs(e.y-st.y)<100&&Math.abs(e.x-st.x)<50)tx+=e.x<st.x?70:-70;st.tx=clamp(tx,24,W-24);st.ty=ty},
};
