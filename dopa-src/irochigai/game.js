/* ひとりだけ色ちがい：Kuku Kube 系。レベルでマス数↑・色差↓。ミス-3秒。 */
const AREA=360,AX=(W-AREA)/2,AY=200;
const GAME={...META,time:40,unit:'問',hudUnit:true,comboHud:false,
  bgm:{bpm:124,root:60,scale:'major',prog:[4,5,3,6],seed:58,lead:'triangle',drums:'pop',density:.55},
  ranks:[[0,'色ってむずかしい'],[10,'ふつうの目'],[18,'いい目してる'],[26,'色のソムリエ'],[34,'ほぼカメラ'],[42,'色ちがい検出AI']],
  shareText:(v,f)=>`ひとりだけ色ちがい、40秒で ${f}問 正解！`,
  icon(c,x,y,s){const r=s*.15;for(let i=0;i<3;i++)for(let j=0;j<3;j++){const px=x+(i-1)*r*2.3,py=y+(j-1)*r*2.3;D.circle(c,px,py,r,i===2&&j===0?'#e7a2bc':'#ecb6ca',s*.018);D.face(c,px,py+r*.1,r*1.2,i===2&&j===0?'o':'smile')}},
  reset(api){this.st={lv:0,miss:0,anim:0,wrongT:0};this.next(api);api.score=0},
  next(api){const st=this.st,lv=st.lv,n=Math.min(8,2+Math.floor((lv+1)/2.2));
    const h=rnd(360),s=rnd(40,62),l=rnd(62,74),d=Math.max(2.2,16-lv*.45)*(Math.random()<.5?-1:1);
    st.n=n;st.odd=rndi(0,n*n-1);st.c1=`hsl(${h},${s}%,${l}%)`;st.c2=`hsl(${h},${s}%,${l+d}%)`;st.anim=0},
  down(x,y,api){const st=this.st,cs=AREA/st.n,i=Math.floor((x-AX)/cs),j=Math.floor((y-AY)/cs);if(i<0||j<0||i>=st.n||j>=st.n)return;
    const k=j*st.n+i,cx=AX+(i+.5)*cs,cy=AY+(j+.5)*cs;
    if(k===st.odd){st.lv++;api.score=st.lv;S.coin(1+Math.min(st.lv,30)*.03);api.burst(cx,cy,{c:[st.c2,'#fff'],n:14,sp:240,shape:'star',r:5});api.ring(cx,cy,{c:'#fff',r:cs});api.float(cx,cy-cs*.6,'いた！',{size:24});if(st.lv%10===0){S.fanfare();api.flash('#fff',.4);api.float(W/2,150,st.lv+'問とっぱ！',{size:30})}this.next(api)}
    else{api.timeLeft=Math.max(0,api.timeLeft-3);S.bad();api.shake(8);st.wrongT=.4;st.wi=k;api.float(cx,cy-20,'-3秒',{c:'#e2645a',size:26})}},
  update(dt){const st=this.st;st.anim=Math.min(1,st.anim+dt*5);st.wrongT=Math.max(0,st.wrongT-dt)},
  overUpdate(dt){this.st.reveal=(this.st.reveal||0)+dt},
  draw(c,api){const st=this.st;c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.fillStyle='#ebe3d6';for(let i=-2;i<14;i++){c.save();c.translate(i*50,0);c.rotate(.3);c.fillRect(0,-50,20,H+100);c.restore()}
    D.rrect(c,AX-14,AY-14,AREA+28,AREA+28,26,'#fffdf8',4);
    const cs=AREA/st.n,r=cs*.4*ease.outBack(st.anim);
    for(let j=0;j<st.n;j++)for(let i=0;i<st.n;i++){const k=j*st.n+i,cx=AX+(i+.5)*cs,cy=AY+(j+.5)*cs;let ox=0;if(st.wrongT>0&&k===st.wi)ox=Math.sin(st.wrongT*60)*4;
      D.circle(c,cx+ox,cy,r,k===st.odd?st.c2:st.c1,Math.max(2,cs*.05));D.face(c,cx+ox,cy+r*.1,r*1.15,st.wrongT>0&&k===st.wi?'sad':'smile');
      if(api.state==='over'&&k===st.odd){c.lineWidth=4;c.strokeStyle='#e2645a';c.beginPath();c.arc(cx,cy,r+8,0,7);c.stroke()}}
    D.text(c,'レベル '+(st.lv+1),W/2,AY+AREA+50,20,'#7a6658');
  },
  __bot(api){const st=this.st;if(Math.random()<.5)return;const k=Math.random()<.9?st.odd:rndi(0,st.n*st.n-1),cs=AREA/st.n;this.down(AX+(k%st.n+.5)*cs,AY+(Math.floor(k/st.n)+.5)*cs,api)},
};
