/* ぴょんぴょんなわとび：なわの角度が足もとを通る瞬間にジャンプ中かを判定。 */
const CX=W/2,GY=520;
const GAME={...META,sprites:['icon','kuma'],unit:'回',hudUnit:true,fullBleed:true,
  bgm:{bpm:120,root:64,scale:'major',prog:[1,4,5,1],seed:71,lead:'square',drums:'four',density:.55},
  ranks:[[0,'ひっかかり'],[10,'なわとび見習い'],[30,'ぴょんぴょん上手'],[60,'なわとびの達人'],[100,'二重とびマスター'],[150,'伝説のとび手']],
  shareText:(v,f)=>`ぴょんぴょんなわとびで ${f}回 とべた！`,
  icon(c,x,y,s){c.lineWidth=4;c.strokeStyle=OL;c.beginPath();c.arc(x,y,s*.46,Math.PI*.15,Math.PI*.85);c.stroke();this.kuma(c,x,y-s*.05,s*.3,0)},
  kuma(c,x,y,s,jump){const sq=jump>0?1-jump*.15:1;c.save();c.translate(x,y);c.scale(1/sq,sq);
    D.ellipse(c,-s*.55,-s*.55,s*.22,s*.22,'#c9a070');D.ellipse(c,s*.55,-s*.55,s*.22,s*.22,'#c9a070');
    D.rrect(c,-s*.65,-s*.65,s*1.3,s*1.4,s*.5,'#c9a070');D.ellipse(c,0,s*.2,s*.28,s*.2,'#f1dcc0');D.face(c,0,-s*.05,s*1.05,jump>0?'o':'smile');
    D.ellipse(c,-s*.3,s*.78,s*.22,s*.12,'#a67c52');D.ellipse(c,s*.3,s*.78,s*.22,s*.12,'#a67c52');c.restore()},
  reset(api){this.st={a:0,spd:2.6,jy:0,jv:0,n:0,miss:0,dbl:false,nextDbl:0,passed:false,t:0,rope:'#9cc86a',mood:'smile',ft:0};api.score=0},
  down(x,y,api){const st=this.st;if(st.jy===0&&st.miss<3){st.jv=-(st.dbl?640:560);S.boing(.9+Math.min(st.n,40)*.01);st.jumped=true}},
  update(dt,api){const st=this.st;st.t+=dt;st.ft-=dt;if(st.miss>=3){st.endT=(st.endT||0)+dt;if(st.endT>.9)api.end();return}
    st.a+=st.spd*dt;if(st.a>=Math.PI*2){st.a-=Math.PI*2;st.passed=false;
      if(st.dbl){st.dbl=false;st.rope='#9cc86a'}else{st.nextDbl--;if(st.nextDbl<=0&&st.n>5){st.dbl=true;st.rope='#e2645a';st.nextDbl=Math.round(rnd(3,7));S.tick()}}}
    st.jv+=1500*dt;st.jy+=st.jv*dt;if(st.jy>0){st.jy=0;st.jv=0}
    // rope at feet when angle in window around PI/2 (bottom)
    const bottom=Math.PI/2;const d=Math.abs(st.a-bottom);
    if(!st.passed&&st.a>=bottom-.06){st.passed=true;const h=-st.jy;const need=st.dbl?42:26;
      if(h>need){st.n+=st.dbl?2:1;api.score=st.n;api.combo=st.n;st.spd=Math.min(7.5,2.6+st.n*.06+(st.dbl?.4:0));
        const pts=st.dbl?2:1;api.float(CX,GY-180,'+'+pts,{size:st.dbl?30:22,c:st.dbl?'#e2645a':'#5b4d45'});if(st.dbl)api.burst(CX,GY-40,{c:['#e2645a','#f2c84b'],n:10,sp:180});
        S.pop(1+Math.min(st.n,30)*.02);if(st.n%10===0){S.fanfare();api.float(CX,250,st.n+'回！',{size:36,c:'#9cc86a'});api.flash('#fff',.25)}}
      else{st.miss++;st.mood='hurt';st.ft=.8;api.shake(8);S.thud();api.burst(CX,GY,{c:['#5b4d45','#fff'],n:8,sp:140});api.float(CX,GY-150,st.miss>=3?'ひっかかった…':'あぶない！',{size:26,c:'#e2645a'});api.combo=0;st.spd=Math.max(2.6,st.spd-.8);st.dbl=false;st.rope='#9cc86a';
        if(st.miss>=3){st.a=bottom}}}
    if(st.ft<=0)st.mood='smile'},
  draw(c,api){const st=this.st;c.fillStyle='#eaf3e0';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#cfe4b5';c.fillRect(0,GY+20,W,api.bottom-GY);c.fillStyle='#b8d69c';c.fillRect(0,GY+20,W,6);
    for(let i=0;i<3;i++)D.ellipse(c,(i*160+st.t*12)%(W+120)-60,120+i*60,44,14,'#fff',0);
    const r=190,ky=GY-10+st.jy;const a=st.a;const ry=Math.sin(a)*r,rx=Math.cos(a)*.35;
    // rope behind when going up (sin<0)
    const rope=()=>{c.lineWidth=5;c.strokeStyle=OL;c.beginPath();c.moveTo(CX-120,GY-150);c.quadraticCurveTo(CX+rx*40,GY-10+ry*1.05,CX+120,GY-150);c.stroke();c.lineWidth=2.5;c.strokeStyle=st.rope;c.stroke();
      D.rrect(c,CX-132,GY-178,22,40,8,'#f2c84b');D.rrect(c,CX+110,GY-178,22,40,8,'#f2c84b')};
    if(Math.sin(a)<0)rope();
    if(st.jy<0)D.ellipse(c,CX,GY+8,60+st.jy*.1,12,'rgba(90,77,69,.15)',0);
    this.kuma(c,CX,ky-60,46,st.jy<0?1:0,st.mood);
    if(Math.sin(a)>=0)rope();
    if(api.state==='play'&&st.n===0&&st.miss===0)D.text(c,'なわが足もとに来たらタップ！',CX,260,20,'#5b4d45');
    for(let i=0;i<3;i++)D.circle(c,W/2-30+i*30,150,9,i<3-st.miss?'#e2645a':'#e7e2d8',2.5);
    if(st.dbl)D.text(c,'二重とび！',CX,210,24,'#e2645a','center','#fff',5)},
  kuma(c,x,y,s,jump,mood='smile'){const sq=jump>0?1.12:1;c.save();c.translate(x,y);c.scale(1/sq,sq);
    D.ellipse(c,-s*.55,-s*.55,s*.22,s*.22,'#c9a070');D.ellipse(c,s*.55,-s*.55,s*.22,s*.22,'#c9a070');
    D.rrect(c,-s*.65,-s*.65,s*1.3,s*1.4,s*.5,'#c9a070');D.ellipse(c,0,s*.2,s*.28,s*.2,'#f1dcc0');D.face(c,0,-s*.05,s*1.05,mood==='hurt'?'hurt':jump>0?'o':'smile');
    D.ellipse(c,-s*.3,s*.78,s*.22,s*.12,'#a67c52');D.ellipse(c,s*.3,s*.78,s*.22,s*.12,'#a67c52');c.restore()},
  __bot(api){const st=this.st;const bottom=Math.PI/2;const d=bottom-.06-st.a;if(d>0&&d<st.spd*.12&&st.jy===0)this.down(0,0,api)},
};
