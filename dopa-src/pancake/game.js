/* ホットケーキタワー：Stack 系。はみ出しは切り落とし、ピタッ（±5）なら幅そのまま、3連続で幅回復。 */
const PH=24,BASEY=640,CX=W/2;
const COLS=['#e9b366','#e3a656','#efbf74','#dc9c4c'];
const GAME={...META,unit:'段',hudUnit:true,
  bgm:{bpm:126,root:65,scale:'major',prog:[1,5,4,5],seed:5,lead:'square',drums:'four'},
  ranks:[[0,'ひとくちサイズ'],[10,'朝ごはん'],[20,'カフェの看板'],[35,'ホットケーキ職人'],[50,'天までとどくタワー'],[75,'ホットケーキの神']],
  shareText:(v,f)=>`ホットケーキを ${f}段 つみあげた！`,
  icon(c,x,y,s){D.ellipse(c,x,y+s*.36,s*.42,s*.08,'#fffdf8',s*.02);
    for(let i=0;i<4;i++)this.cake(c,x-s*.32+(i%2)*s*.02,y+s*.26-i*s*.13,s*.64,s*.13,i);
    D.rrect(c,x-s*.09,y-s*.33,s*.18,s*.11,s*.02,'#f8e08e',s*.018);D.face(c,x,y+s*.2,s*.34,'smile')},
  cake(c,x,y,w,h,i,face){D.rrect(c,x,y,w,h,h*.5,COLS[i%4],Math.max(2,h*.13));if(face)D.face(c,x+w/2,y+h*.45,Math.min(h*2.2,w*.5),face)},
  reset(api){this.st={L:[{x:CX-90,w:180}],cur:null,cam:0,camT:0,fall:[],perfect:0,dir:1,speed:190,syrup:0,dropAnim:0};this.spawn();api.score=0},
  spawn(){const st=this.st,top=st.L[st.L.length-1],n=st.L.length;st.dir=n%2?1:-1;
    st.speed=Math.min(470,190+n*7);st.cur={x:st.dir>0?-top.w:W,w:top.w}},
  yOf(i){return BASEY-PH*(i+1)},
  down(x,y,api){this.place(api)},key(k,api){if(k===' '||k==='Enter')this.place(api)},
  place(api){const st=this.st;if(!st.cur)return;const top=st.L[st.L.length-1],c=st.cur;
    const l=Math.max(c.x,top.x),r=Math.min(c.x+c.w,top.x+top.w),y=this.yOf(st.L.length);
    if(r-l<=0){st.fall.push({x:c.x,y,w:c.w,vy:0,vx:st.dir*80,rot:0,vr:st.dir*2,i:st.L.length});st.cur=null;api.shake(10);S.bad();api.end();return}
    if(Math.abs(c.x-top.x)<=5){st.perfect++;api.combo=st.perfect;let w=top.w;
      if(st.perfect>=3&&w<180){w=Math.min(180,w+14);api.float(W/2,y-50,'ひろがった！',{c:'#f8e08e',size:24})}
      st.L.push({x:top.x-(w-top.w)/2,w});S.perfect(1+Math.min(st.perfect,12)*.06);api.ring(CX,y+PH/2-st.cam,{c:'#fff',r:150});api.float(top.x+top.w/2,y-20-st.cam,st.perfect>1?'ピタッ×'+st.perfect:'ピタッ！',{c:'#fff',size:28});
      api.burst(top.x+top.w/2,y-st.cam+PH/2,{c:['#fff','#f8e08e'],n:16,sp:260,shape:'star',r:5});api.flash('#fff',.2)}
    else{st.perfect=0;api.combo=0;
      const cut=c.x<top.x?{x:c.x,w:top.x-c.x}:{x:r,w:c.x+c.w-r};
      st.fall.push({x:cut.x,y,w:cut.w,vy:-60,vx:(c.x<top.x?-1:1)*90,rot:0,vr:(c.x<top.x?-1:1)*3,i:st.L.length});
      st.L.push({x:l,w:r-l});S.thud();S.pop(.7+Math.random()*.2);api.shake(3)}
    api.score=st.L.length-1;st.dropAnim=1;
    if(api.score%10===0){api.float(W/2,250,api.score+'段！',{size:40,c:'#fff'});S.fanfare()}
    st.camT=Math.max(0,(st.L.length-12)*PH);this.spawn()},
  update(dt,api){const st=this.st;
    if(st.cur){st.cur.x+=st.dir*st.speed*dt;const top=st.L[st.L.length-1];
      if(st.dir>0&&st.cur.x>W){st.dir=-1}else if(st.dir<0&&st.cur.x+st.cur.w<0){st.dir=1}}
    st.cam=lerp(st.cam,st.camT,1-Math.pow(.002,dt));st.dropAnim=Math.max(0,st.dropAnim-dt*5);
    this.fallUpd(dt)},
  fallUpd(dt){const st=this.st;for(const f of st.fall){f.vy+=1400*dt;f.y+=f.vy*dt;f.x+=f.vx*dt;f.rot+=f.vr*dt}st.fall=st.fall.filter(f=>f.y-st.cam<H+200)},
  overUpdate(dt){this.fallUpd(dt)},
  draw(c,api){const st=this.st;
    const g=c.createLinearGradient(0,0,0,H);g.addColorStop(0,'#cfe6f2');g.addColorStop(1,this.bg);c.fillStyle=g;c.fillRect(0,0,W,H);
    // 高くなると空の雲
    c.save();c.translate(0,st.cam*.3%400);c.globalAlpha=.8;for(let i=-1;i<3;i++){D.ellipse(c,80+(i*150)%300,120+i*200,46,18,'#fff',0);D.ellipse(c,330,40+i*200,36,14,'#fff',0)}c.restore();
    c.save();c.translate(0,st.cam);
    D.ellipse(c,CX,BASEY+8,140,18,'#fffdf8',4);D.rrect(c,-10,BASEY+18,W+20,200,0,'#d9b98f',4);
    st.L.forEach((p,i)=>{if(i===0){this.cake(c,p.x,BASEY-PH,p.w,PH,0);return}
      const sq=i===st.L.length-1?st.dropAnim*.25:0;this.cake(c,p.x-sq*10,this.yOf(i)+sq*PH*.3,p.w+sq*20,PH*(1-sq*.3),i)});
    const top=st.L[st.L.length-1],ty=this.yOf(st.L.length-1);
    if(st.L.length>1&&api.state!=='play'){D.rrect(c,top.x+top.w/2-14,ty-8,28,10,3,'#f8e08e',2.5)}
    for(const f of st.fall){c.save();c.translate(f.x+f.w/2,f.y+PH/2);c.rotate(f.rot);this.cake(c,-f.w/2,-PH/2,f.w,PH,f.i);c.restore()}
    if(st.cur){const y=this.yOf(st.L.length);c.globalAlpha=.25;c.fillStyle=OL;c.fillRect(top.x,y+PH,top.w,4);c.globalAlpha=1;this.cake(c,st.cur.x,y,st.cur.w,PH,st.L.length,'smile')}
    c.restore();
  },
  __bot(api){const st=this.st;if(st.cur){const top=st.L[st.L.length-1];if(Math.abs(st.cur.x-top.x)<(Math.random()<.5?6:30))this.place(api)}},
};
