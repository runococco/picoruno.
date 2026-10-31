/* ぴょんぴょん川わたり：横に流れる葉っぱの列を1列ずつジャンプ。 */
const RH=90,FY=560;
const GAME={...META,sprites:['icon','frog','leaf'],unit:'列',hudUnit:true,fullBleed:true,
  bgm:{bpm:118,root:62,scale:'major',prog:[1,4,1,5],seed:19,lead:'square',drums:'light',density:.5},
  ranks:[[0,'ぽちゃん'],[5,'かえる見習い'],[15,'ぴょんぴょん上手'],[30,'川わたりの達人'],[50,'向こう岸の主'],[80,'伝説のかえる']],
  shareText:(v,f)=>`ぴょんぴょん川わたりで ${f}列 わたった！`,
  icon(c,x,y,s){this.leaf(c,x-s*.2,y+s*.25,s*.3,0);this.leaf(c,x+s*.25,y-s*.2,s*.26,1);this.frog(c,x-s*.2,y+s*.08,s*.26,0)},
  leaf(c,x,y,r,k){D.ellipse(c,x,y,r,r*.55,k?'#86b85e':'#9cc86a');c.lineWidth=2;c.strokeStyle=OL;c.beginPath();c.moveTo(x-r*.8,y);c.lineTo(x+r*.8,y);c.stroke()},
  frog(c,x,y,s,jump){c.save();c.translate(x,y);const sq=jump?1.15:1;c.scale(1/sq,sq);D.ellipse(c,-s*.8,s*.55,s*.32,s*.2,'#7fb24e',2.5);D.ellipse(c,s*.8,s*.55,s*.32,s*.2,'#7fb24e',2.5);
    D.ellipse(c,0,s*.15,s*.95,s*.75,'#8ec25c');D.circle(c,-s*.5,-s*.45,s*.3,'#8ec25c');D.circle(c,s*.5,-s*.45,s*.3,'#8ec25c');D.face(c,0,-s*.2,s*1.6,jump?'o':'smile');c.restore()},
  reset(api){this.st={rows:[],row:0,x:W/2,fx:W/2,jump:0,jy:0,dead:false,scroll:0,on:null,idle:0,t:0,endT:0};api.score=0;for(let i=0;i<10;i++)this.addRow(i)},
  addRow(i){const st=this.st;const lv=Math.min(1,i/60);const spd=(40+rnd(0,40)+lv*110)*(i%2?1:-1);const gap0=rnd(190,280)-lv*50;const n=Math.max(2,Math.round((W+300)/gap0)),gap=(W+300)/n;const r=Math.max(32,50-lv*14);const leaves=[];for(let j=0;j<n;j++)leaves.push({x:-150+j*gap+rnd(-15,15),r});st.rows[i]={spd,leaves,i,k:i%2}},
  down(x,y,api){const st=this.st;if(st.dead||st.jump>0)return;st.jump=.3;st.fromX=st.fx;st.row++;S.boing(1+Math.min(st.row,40)*.01);api.burst(st.fx,FY+20,{c:['#cfe7ee','#fff'],n:5,sp:90,r:3});st.idle=0},
  update(dt,api){const st=this.st;st.t+=dt;if(st.dead){st.endT+=dt;if(st.endT>1)api.end();return}
    for(const r of st.rows)if(r)for(const l of r.leaves){l.x+=r.spd*dt;if(r.spd>0&&l.x>W+150)l.x-=W+300;if(r.spd<0&&l.x<-150)l.x+=W+300}
    if(st.row>0&&!st.jump){st.idle+=dt;const lim=Math.max(1.6,3.2-st.row*.03);if(st.idle>lim){this.die(api,'流された…')}}
    // scroll target: current row at FY
    const target=st.row*RH;st.scroll+=(target-st.scroll)*8*dt;
    if(st.jump>0){st.jump-=dt;st.jy=Math.sin((1-st.jump/.3)*Math.PI)*60;
      if(st.jump<=0){st.jump=0;st.jy=0;const r=st.rows[st.row];if(!st.rows[st.row+8])for(let i=st.rows.length;i<=st.row+8;i++)this.addRow(i);
        const l=r.leaves.find(l=>Math.abs(l.x-st.fx)<l.r*.85);if(l){st.on=l;st.onRow=r;api.score=st.row;api.combo=st.row;S.pop(1+Math.min(st.row,30)*.015);api.float(st.fx,FY-70,'+1',{size:20,c:'#5b4d45'});
          if(st.row%10===0){S.fanfare();api.float(W/2,250,st.row+'列！',{size:34,c:'#9cc86a'});api.flash('#fff',.25)}}
        else this.die(api,'ぽちゃん…')}}
    else if(st.on){st.fx=st.on.x;if(st.fx<-20||st.fx>W+20)this.die(api,'流された…')}
  },
  die(api,txt){const st=this.st;st.dead=true;S.bad();S.noise(.15,{v:.5,f:1200});api.shake(8);api.burst(st.fx,FY,{c:['#9ccfe0','#fff'],n:14,sp:200,r:5});api.float(W/2,300,txt,{size:30,c:'#5b4d45'});api.combo=0},
  draw(c,api){const st=this.st;c.fillStyle='#cfe7ee';c.fillRect(0,api.top,W,api.bottom-api.top);
    const off=st.scroll-st.row*RH;
    for(let i=Math.max(0,st.row-3);i<=st.row+7;i++){const r=st.rows[i];if(!r)continue;const y=FY-(i-st.row)*RH-off;if(y<api.top-60||y>api.bottom+60)continue;
      if(i===0){c.fillStyle='#b8d69c';c.fillRect(0,y-10,W,api.bottom-y+60);c.fillStyle='#a6c98a';c.fillRect(0,y-10,W,8)}
      c.fillStyle='rgba(255,255,255,.45)';for(let x=((i*53-st.t*r.spd*.3)%160+160)%160-80;x<W;x+=160)D.rrect(c,x,y+34,60,4,2,'rgba(255,255,255,.5)',0);
      for(const l of r.leaves)if(l.x>-80&&l.x<W+80)this.leaf(c,l.x,y,l.r,r.k)}
    const fy=FY-st.jy-off*0;if(st.jump>0)D.ellipse(c,st.fx,FY+20,30-st.jy*.2,10,'rgba(90,77,69,.15)',0);
    if(!st.dead||st.endT<.3)this.frog(c,st.fx,fy-18,22,st.jump>0);
    if(api.state==='play'&&st.row===0)D.text(c,'タップでジャンプ！',W/2,FY-120,22,'#5b4d45');
    if(st.row>0&&!st.dead){const lim=Math.max(1.6,3.2-st.row*.03);const k=1-st.idle/lim;D.rrect(c,W/2-60,150,120,10,5,'#fff',2);if(k>0)D.rrect(c,W/2-58,152,116*k,6,3,k<.35?'#e2645a':'#9cc86a',0)}},
  __bot(api){const st=this.st;if(st.dead||st.jump>0)return;const r=st.rows[st.row+1];if(!r)return;const l=r.leaves.find(l=>Math.abs(l.x+r.spd*.3-st.fx)<l.r*.5);if(l)this.down(0,0,api)},
};
