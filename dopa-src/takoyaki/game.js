/* たこやきくるん：各穴に焼き進行度。きつね色の窓でタップ。 */
const PL=[];for(let r=0;r<3;r++)for(let q=0;q<3;q++)PL.push({x:100+q*110,y:330+r*110});
const GAME={...META,sprites:['icon','tako'],unit:'点',time:60,fullBleed:true,
  bgm:{bpm:132,root:62,scale:'major',prog:[1,6,4,5],seed:77,lead:'square',drums:'light',density:.55},
  ranks:[[0,'まっくろ'],[400,'たこやき見習い'],[900,'くるん上手'],[1500,'たこやきの達人'],[2200,'屋台の主'],[3000,'伝説のたこやき']],
  shareText:(v,f)=>`たこやきくるんで ${f}点！`,
  icon(c,x,y,s){D.rrect(c,x-s*.46,y-s*.3,s*.92,s*.7,s*.1,'#5b5560');for(let i=0;i<3;i++)this.tako(c,x-s*.28+i*s*.28,y+s*.05,s*.12,i===1?.55:i?1:.2)},
  tako(c,x,y,r,k){const col=k<.3?'#f6e3c0':k<.6?'#f2c27a':k<.85?'#d99a52':'#5b4d45';D.circle(c,x,y,r,col);if(k>=.6){D.ellipse(c,x,y-r*.1,r*.55,r*.3,'#8a6a48',2);D.ellipse(c,x-r*.2,y+r*.3,r*.2,r*.1,'#fbf7f0',0);D.ellipse(c,x+r*.25,y-r*.5,r*.18,r*.1,'#8ab850',0)}},
  reset(api){this.st={p:PL.map(()=>null),t:0,spawn:0,done:0};api.score=0},
  down(x,y,api){const st=this.st;for(let i=0;i<9;i++){const p=st.p[i],h=PL[i];if(!p||p.gone)continue;if(dist(x,y,h.x,h.y)<50){const k=p.k;let pts,txt;
      if(k<.6){pts=0;txt='まだ生…';api.combo=0;S.bad()}else if(k<.85){const g=1-(k-.6)/.25;pts=50+Math.round(g*50);api.combo++;pts+=Math.min(api.combo,10)*5;txt=g>.6?'ぴったり！':'くるん';S.pop(1.1);S.good()}else{pts=0;txt='こげた…';api.combo=0;S.bad()}
      api.add(pts);p.gone=true;p.goneT=0;p.flip=1;st.done++;api.float(h.x,h.y-60,txt+(pts?' +'+pts:''),{size:pts>=90?24:18,c:pts?'#c9743e':'#5b4d45'});if(pts>=90){api.burst(h.x,h.y,{c:['#f2c84b','#fff'],n:8,sp:150,r:3})}
      if(api.combo&&api.combo%10===0){S.fanfare();api.float(W/2,220,api.combo+'コンボ！',{size:30,c:'#c9743e'})}return}}S.tap(.3)},
  update(dt,api){const st=this.st;st.t+=dt;const lv=Math.min(1,st.t/60);st.spawn-=dt;if(st.spawn<=0){st.spawn=rnd(.5,1)-lv*.35;const free=[];st.p.forEach((p,i)=>{if(!p)free.push(i)});if(free.length){st.p[pick(free)]={k:0,sp:rnd(.18,.3)+lv*.12}}}
    for(let i=0;i<9;i++){const p=st.p[i];if(!p)continue;if(p.gone){p.goneT+=dt;if(p.goneT>.35)st.p[i]=null;continue}p.k+=p.sp*dt;if(p.k>1.1){st.p[i]=null;api.combo=0;api.float(PL[i].x,PL[i].y-50,'まっくろ…',{size:16,c:'#5b4d45'});S.noise(.1,{v:.2,f:800})}}},
  draw(c,api){const st=this.st;c.fillStyle='#f6e7d2';c.fillRect(0,api.top,W,api.bottom-api.top);D.rrect(c,40,260,W-80,360,20,'#5b5560',4);D.rrect(c,30,250,W-60,20,8,'#8a8392',3);
    for(let i=0;i<9;i++){const h=PL[i];D.circle(c,h.x,h.y,42,'#3e3a48',0);const p=st.p[i];if(p){if(p.gone){const s=1+Math.sin(p.goneT/.35*Math.PI)*.4;this.tako(c,h.x,h.y-p.goneT*120,34*s,Math.min(p.k,.84))}else{this.tako(c,h.x,h.y,34,p.k)}}}
    for(let i=0;i<9;i++){const p=st.p[i];if(p&&!p.gone&&p.k>=.6&&p.k<.85){const h=PL[i];c.lineWidth=3;c.strokeStyle='#f2c84b';c.beginPath();c.arc(h.x,h.y,46,0,Math.PI*2);c.stroke()}}
    if(api.state==='play'&&st.t<3)D.text(c,'きつね色になったらタップ！',W/2,220,20,'#5b4d45')},
  __bot(api){const st=this.st;for(let i=0;i<9;i++){const p=st.p[i];if(p&&!p.gone&&p.k>=.62&&p.k<.8){this.down(PL[i].x,PL[i].y,api);return}}},
};
