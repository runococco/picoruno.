/* ちくわブリッジ：Stick Hero 系。長押しで伸ばし、離すと倒れる。 */
const TOPY=470,HX=70;
const GAME={...META,unit:'本',hudUnit:true,
  bgm:{bpm:108,root:62,scale:'major',prog:[1,3,4,5],seed:19,lead:'triangle',drums:'pop',density:.5},
  ranks:[[0,'ちくわの穴'],[5,'ちくわ見習い'],[12,'ちくわ大工'],[22,'ちくわ建築士'],[35,'ちくわ橋の巨匠'],[50,'ちくわ大明神']],
  shareText:(v,f)=>`ちくわブリッジで ${f}本 わたった！`,
  icon(c,x,y,s){this.chikuwa(c,x-s*.42,y+s*.12,s*.84,s*.16);this.hero(c,x,y-s*.04,s*.36,0)},
  chikuwa(c,x,y,len,th=16){if(len<2)return;D.rrect(c,x,y-th/2,len,th,th/2,'#f6e6c4',3);if(len>th*1.6){c.fillStyle='#c98a4b';c.beginPath();c.roundRect?c.roundRect(x+th*.5,y-th*.3,len-th*1.1,th*.5,th*.25):c.rect(x+th*.5,y-th*.3,len-th*1.1,th*.5);c.fill()}D.ellipse(c,x+len-th*.35,y,th*.16,th*.28,'#fffaf0',2)},
  hero(c,x,y,s,walk){const lg=Math.sin(walk*18)*s*.08;c.lineWidth=Math.max(2,s*.07);c.strokeStyle=OL;c.lineCap='round';c.beginPath();c.moveTo(x-s*.15,y-s*.1);c.lineTo(x-s*.15+lg,y);c.moveTo(x+s*.15,y-s*.1);c.lineTo(x+s*.15-lg,y);c.stroke();
    D.ellipse(c,x,y-s*.42,s*.42,s*.36,'#fbf4e4',Math.max(2,s*.07));D.path(c,c=>{c.ellipse(x,y-s*.68,s*.2,s*.08,0,0,7)},'#a4c66f',Math.max(1.5,s*.05));D.face(c,x+s*.06,y-s*.42,s*.42,'smile')},
  reset(api){this.st={pil:[],cam:0,camT:0,ph:'idle',len:0,ang:0,hx:0,walk:0,fall:0,perfect:0};const st=this.st;st.pil.push({x:20,w:90});this.addP();this.addP();st.hx=st.pil[0].x+st.pil[0].w-14;api.score=0},
  addP(){const st=this.st,l=st.pil[st.pil.length-1],sc=Math.min(1,st.pil.length/30);st.pil.push({x:l.x+l.w+rnd(50,200+sc*60),w:rnd(36-sc*10,96-sc*30)})},
  down(x,y,api){const st=this.st;if(st.ph==='idle'){st.ph='grow';st.len=0;S.tap()}},
  up(x,y,api){const st=this.st;if(st.ph==='grow'){st.ph='rot';st.ang=0;S.whoosh()}},
  key(k,api){if(k===' ')this.down(0,0,api)},keyUp(k,api){if(k===' ')this.up(0,0,api)},
  update(dt,api){const st=this.st,cur=st.pil[0],nx=st.pil[1],ex=cur.x+cur.w;
    st.cam=lerp(st.cam,st.camT,1-Math.pow(.001,dt));
    if(st.ph==='grow'){st.len=Math.min(600,st.len+430*dt);if(Math.floor(st.len/30)!==Math.floor((st.len-430*dt)/30))S.tick()}
    else if(st.ph==='rot'){st.ang=Math.min(1,st.ang+dt*3.2);if(st.ang>=1){S.thud();api.shake(4);const tip=ex+st.len;st.ok=tip>=nx.x&&tip<=nx.x+nx.w;
        const mid=nx.x+nx.w/2;st.perf=st.ok&&Math.abs(tip-mid)<7;st.ph='walk';st.target=st.ok?nx.x+nx.w-14:tip+10}}
    else if(st.ph==='walk'){st.walk+=dt;st.hx=Math.min(st.target,st.hx+380*dt);if(st.hx>=st.target){
        if(st.ok){api.score++;let msg='+1';if(st.perf){api.score+=2;st.perfect++;api.combo=st.perfect;msg='ぴったり！+3';S.perfect();api.flash('#fff',.3);api.ring(nx.x+nx.w/2-st.cam,TOPY,{c:'#e2645a',r:60})}else{st.perfect=0;api.combo=0;S.coin()}
          api.float(st.hx-st.cam,TOPY-80,msg,{size:st.perf?30:24,c:st.perf?'#f3c84b':'#fff'});api.burst(st.hx-st.cam,TOPY,{c:['#fff','#f3dfb4'],n:8,sp:150,r:4});
          st.old={x:ex,len:st.len};st.pil.shift();this.addP();st.camT=st.pil[0].x+st.pil[0].w-HX-40;st.ph='idle';st.len=0;st.walk=0}
        else{st.ph='fall';st.fall=0;S.bad();api.shake(8)}}}
    else if(st.ph==='fall'){st.fall+=dt;st.ang=Math.min(2,1+st.fall*2.5);if(st.fall>.9)api.end()}},
  overUpdate(dt){const st=this.st;st.fall+=dt;st.ang=Math.min(2,1+st.fall*2.5)},
  overText:'おちた！',
  draw(c,api){const st=this.st;const g=c.createLinearGradient(0,0,0,H);g.addColorStop(0,'#f9d9b8');g.addColorStop(1,'#f6e7d8');c.fillStyle=g;c.fillRect(0,0,W,H);
    c.save();c.translate(-st.cam*.2,0);for(let i=0;i<14;i++){const x=i*140-((st.cam*.2)%140)*0;D.ellipse(c,x+40,520,120,160,'#ecc7a4',0)}c.restore();
    D.circle(c,W-90,150,50,'#fbe5a8',0);
    c.save();c.translate(-st.cam,0);
    for(const p of st.pil){D.rrect(c,p.x,TOPY,p.w,H-TOPY+40,6,'#8f6a52',3.5);D.rrect(c,p.x+p.w/2-6,TOPY,12,7,2,'#e2645a',2)}
    if(st.old){this.chikuwa(c,st.old.x,TOPY-8,st.old.len)}
    const cur=st.pil[0],ex=cur.x+cur.w;
    if(st.ph!=='idle'||st.len>0){c.save();c.translate(ex,TOPY);c.rotate(-Math.PI/2+ease.inOut(Math.min(1,st.ang))*Math.PI/2+(st.ang>1?(st.ang-1)*Math.PI/2:0));this.chikuwa(c,0,-8,st.len);c.restore()}
    const hy=st.ph==='fall'||api.state==='over'?TOPY+Math.pow(st.fall,2)*1600:TOPY;
    this.hero(c,st.hx,hy,46,st.ph==='walk'?st.walk:0);
    c.restore();
  },
  __bot(api){const st=this.st;if(st.ph==='idle'){this.down(0,0,api);const nx=st.pil[1],ex=st.pil[0].x+st.pil[0].w;st.want=nx.x+nx.w/2-ex+rnd(-12,12)}if(st.ph==='grow'&&st.len>=st.want)this.up(0,0,api)},
};
