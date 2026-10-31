/* ぴったりジュース：長押しで水位上昇。目標線との差で採点。 */
const N=10,CX=W/2,CB=600;
const JU=[['#f2a24a','オレンジ'],['#e2645a','いちご'],['#9cc86a','メロン'],['#c49ae0','ぶどう'],['#7fb2e0','ソーダ']];
const GAME={...META,sprites:['icon'],unit:'点',fullBleed:true,
  bgm:{bpm:96,root:65,scale:'major',prog:[1,4,2,5],seed:21,lead:'triangle',drums:'light',density:.4},
  ranks:[[0,'こぼしっぱなし'],[300,'そそぎ見習い'],[600,'なかなかの手つき'],[900,'ぴったりの達人'],[1200,'ジュース屋さん'],[1450,'伝説のそそぎ手']],
  shareText:(v,f)=>`ぴったりジュースで ${f}点！`,
  icon(c,x,y,s){this.cup(c,x,y+s*.1,s*.3,s*.5,.6,'#f2a24a',.7);D.rrect(c,x-s*.1,y-s*.5,s*.2,s*.14,s*.04,'#b9c3cc',2.5)},
  cup(c,x,y,hw,h,lv,col,line){const top=y-h;c.save();c.beginPath();c.moveTo(x-hw,top);c.lineTo(x+hw,top);c.lineTo(x+hw*.85,y);c.lineTo(x-hw*.85,y);c.closePath();c.clip();
    if(lv>0){c.fillStyle=col;c.fillRect(x-hw,y-h*lv,hw*2,h*lv)}c.restore();
    D.path(c,c=>{c.moveTo(x-hw,top);c.lineTo(x+hw,top);c.lineTo(x+hw*.85,y);c.lineTo(x-hw*.85,y);c.closePath()},'rgba(255,255,255,.25)',3.5);
    if(line!==undefined){const ly=y-h*line;c.setLineDash([5,5]);c.lineWidth=3;c.strokeStyle='#5b4d45';c.beginPath();c.moveTo(x-hw-14,ly);c.lineTo(x+hw+14,ly);c.stroke();c.setLineDash([]);D.poly(c,[[x+hw+16,ly-8],[x+hw+16,ly+8],[x+hw+28,ly]],'#e2645a',2)}},
  reset(api){this.st={n:0,lv:0,hold:false,wait:0,t:0,res:[]};api.score=0;this.next()},
  next(){const st=this.st;st.n++;st.lv=0;st.hold=false;st.wait=0;st.done=false;st.hw=rnd(45,80);st.h=rnd(150,260);st.line=rnd(.45,.9);st.j=JU[(st.n-1)%JU.length];st.rate=rnd(.35,.6)+st.n*.03},
  down(){const st=this.st;if(st.done||st.wait>0)return;st.hold=true;S.noise(.3,{v:.15,f:1500})},
  up(x,y,api){const st=this.st;if(!st.hold)return;st.hold=false;this.judge(api)},
  judge(api){const st=this.st;if(st.done)return;st.done=true;const d=Math.abs(st.lv-st.line)*st.h;let pts,txt;
    if(st.lv>=1){pts=0;txt='こぼれた…';api.combo=0;S.bad();api.shake(6);api.burst(CX,CB-st.h,{c:[st.j[0]],n:12,sp:160,r:4})}
    else if(d<3){pts=150;txt='ぴったり！';}else if(d<8){pts=120;txt='すごい！'}else if(d<20){pts=80;txt='いいね'}else if(d<45){pts=40;txt='まあまあ'}else{pts=10;txt='ずれてる…'}
    if(pts>=120){api.combo++;pts+=Math.min(api.combo,5)*10}else if(pts)api.combo=0;api.add(pts);st.res.push(pts);
    api.float(CX,325,txt+(pts?' +'+pts:''),{size:pts>=150?34:26,c:pts>=120?'#f2a24a':'#5b4d45',vy:-30});if(pts>=150){S.perfect();api.flash('#fff',.3);api.burst(CX,CB-st.h*st.line,{c:[st.j[0],'#f2c84b','#fff'],n:16,sp:220,shape:'s'})}else if(pts>=120)S.good();else if(pts)S.coin();
    st.wait=1.3},
  update(dt,api){const st=this.st;st.t+=dt;if(st.wait>0){st.wait-=dt;if(st.wait<=0){if(st.n>=N)api.end();else this.next()}return}
    if(st.hold&&!st.done){st.lv+=st.rate*dt*(200/st.h);if(st.lv>=1){st.lv=1.02;this.judge(api)}}},
  draw(c,api){const st=this.st;c.fillStyle='#fff4e0';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#f6e3c4';c.fillRect(0,CB+10,W,api.bottom-CB-10);
    D.rrect(c,CX-90,250,180,44,22,'#fff',3);D.text(c,st.j[1]+'ジュース',CX,280,20,'#5b4d45');
    // tap
    D.rrect(c,CX-14,250-60,28,30,8,'#b9c3cc',3);D.rrect(c,CX-6,250-32,12,30,4,'#b9c3cc',2.5);
    if(st.hold&&!st.done){c.fillStyle=st.j[0];c.fillRect(CX-5,250,10,CB-st.h*st.lv-250);c.strokeStyle=OL;c.lineWidth=2;c.strokeRect(CX-5,250,10,CB-st.h*st.lv-250)}
    this.cup(c,CX,CB,st.hw,st.h,Math.min(st.lv,1),st.j[0],st.line);
    if(st.lv>=1){for(let i=0;i<4;i++)D.ellipse(c,CX+(i-1.5)*40,CB+6,18,6,st.j[0],2)}
    D.text(c,st.n+'/'+N,CX,110,18,'#5b4d45');
    for(let i=0;i<N;i++)D.circle(c,CX-(N-1)*11+i*22,150,7,i<st.res.length?(st.res[i]>=120?'#f2a24a':st.res[i]?'#fff':'#5b5560'):'#fff',2.5);
    if(api.state==='play'&&st.n===1&&!st.hold&&st.lv===0)D.text(c,'おしてそそぐ！線でぴたっ',CX,CB+60,20,'#5b4d45')},
  __bot(api){const st=this.st;if(st.done||st.wait>0)return;if(!st.hold)this.down();else if(st.lv>=st.line-.005)this.up(0,0,api)},
};
