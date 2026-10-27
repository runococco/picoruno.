/* ぽとぽとプリンコ：ピンに当たって落ちる。ふたごピンで分裂、金ピンで加点。15球。 */
const PR=6,BRr=9,TOPY=170,ROWS=11,SPX=36,SPY=38,SLOTY=TOPY+ROWS*SPY+20,BALLS=15;
const MULT=[10,4,2,1,.5,.2,.5,1,2,4,10],SW=W/MULT.length;
const MC={10:'#e2645a',4:'#f2a97a',2:'#f3c84b',1:'#9fd27c',.5:'#7fc6d8',.2:'#b9b3c9'};
const GAME={...META,unit:'点',
  bgm:{bpm:124,root:62,scale:'major',prog:[1,6,2,5],seed:77,lead:'square',drums:'pop',density:.55},
  ranks:[[0,'ころがりはじめ'],[1000,'ぽとぽと好き'],[2500,'カンコン名人'],[5000,'倍率ハンター'],[9000,'×10マスター'],[15000,'プリンコの神']],
  shareText:(v,f)=>`ぽとぽとプリンコで ${f}点！`,
  icon(c,x,y,s){for(let j=0;j<3;j++)for(let i=0;i<=j;i++)D.circle(c,x+(i-j/2)*s*.2,y-s*.12+j*s*.17,s*.035,j===2&&i===1?'#f3c84b':'#fffdf8',s*.015);this.ball(c,x+s*.05,y-s*.33,s*.1);D.rrect(c,x-s*.4,y+s*.32,s*.8,s*.12,s*.04,'#e2645a',s*.02);D.text(c,'×10',x,y+s*.38,s*.09,'#fff')},
  ball(c,x,y,r){D.circle(c,x,y,r,'#fffdf8',Math.max(2,r*.25));D.face(c,x,y+r*.1,r*1.3,'smile')},
  reset(api){const pegs=[];for(let j=0;j<ROWS;j++){const n=j%2?10:11;for(let i=0;i<n;i++){const x=W/2+(i-(n-1)/2)*SPX;pegs.push({x,y:TOPY+j*SPY,t:'n',flash:0})}}
    this.st={pegs,balls:[],left:BALLS,dropX:W/2,cd:0,slotFx:Array(MULT.length).fill(0),drops:0};this.special();api.score=0},
  special(){const st=this.st;for(const p of st.pegs)if(p.t!=='n'&&Math.random()<.5)p.t='n';const cand=st.pegs.filter(p=>p.t==='n'&&p.y>TOPY+SPY);
    for(let k=0;k<2;k++)pick(cand).t='split';for(let k=0;k<3;k++)pick(cand).t='gold'},
  drop(x,api){const st=this.st;if(st.left<=0||st.cd>0)return;st.left--;st.cd=.25;st.drops++;x=clamp(x,50,W-50);st.dropX=x;st.balls.push({x:x+rnd(-1,1),y:TOPY-60,vx:0,vy:0,hits:0});S.tap(.8);if(st.drops%3===0)this.special()},
  down(x,y,api){this.drop(this.st.dropX,api)},key(k,api){if(k===' '||k==='Enter')this.drop(this.st.dropX,api)},
  update(dt,api){const st=this.st;st.cd=Math.max(0,st.cd-dt);st.ph=(st.ph||0)+dt*(1.6+st.drops*.06);st.dropX=W/2+Math.sin(st.ph)*(W/2-50);for(const p of st.pegs)p.flash=Math.max(0,p.flash-dt*4);for(let i=0;i<st.slotFx.length;i++)st.slotFx[i]=Math.max(0,st.slotFx[i]-dt*2);
    const sub=3,h=dt/sub;const add=[];
    for(let s=0;s<sub;s++)for(const b of st.balls){if(b.done)continue;b.vy+=900*h;b.x+=b.vx*h;b.y+=b.vy*h;
      if(b.x<BRr){b.x=BRr;b.vx=Math.abs(b.vx)*.5}if(b.x>W-BRr){b.x=W-BRr;b.vx=-Math.abs(b.vx)*.5}
      for(const p of st.pegs){const dx=b.x-p.x,dy=b.y-p.y,d=Math.hypot(dx,dy);if(d<PR+BRr&&d>0){const nx=dx/d,ny=dy/d;b.x=p.x+nx*(PR+BRr);b.y=p.y+ny*(PR+BRr);const vn=b.vx*nx+b.vy*ny;if(vn<0){b.vx-=1.5*vn*nx;b.vy-=1.5*vn*ny;b.vx+=rnd(-25,25);
        if(p.flash<.5){S.tone(900+((p.y-TOPY)/SPY)*60,.05,{type:'triangle',v:.1});p.flash=1;b.hits++}
        if(p.t==='gold'){p.t='n';api.score+=50;S.coin(1.3);api.float(p.x,p.y-20,'+50',{size:20,c:'#f3c84b'});api.burst(p.x,p.y,{c:['#f3c84b','#fff'],n:10,sp:180,shape:'star',r:4})}
        else if(p.t==='split'){p.t='n';add.push({x:b.x,y:b.y,vx:-b.vx-60,vy:b.vy,hits:0});S.perfect(1.2);api.float(p.x,p.y-24,'ふえた！',{size:22,c:'#8fd0e0'});api.ring(p.x,p.y,{c:'#8fd0e0',r:40});api.flash('#fff',.15)}}}}
      if(b.y>SLOTY+20){b.done=true;const si=clamp(Math.floor(b.x/SW),0,MULT.length-1),m=MULT[si],pts=Math.round(100*m);api.score+=pts;st.slotFx[si]=1;
        const sx=(si+.5)*SW;api.float(sx,SLOTY-30,'+'+pts,{size:m>=4?30:20,c:m>=4?'#f3c84b':'#fff'});
        if(m>=10){S.fanfare();api.shake(12);api.flash('#f3c84b',.4);api.burst(sx,SLOTY,{c:['#e2645a','#f3c84b','#fff'],n:40,sp:420,shape:'star',r:6})}else if(m>=2){S.coin(1+m*.05);api.burst(sx,SLOTY,{c:[MC[m],'#fff'],n:12,sp:220,r:4})}else S.thud()}}
    st.balls.push(...add);st.balls=st.balls.filter(b=>!b.done);
    if(st.left<=0&&st.balls.length===0&&!st.ending){st.ending=true;setTimeout(()=>api.end(),500)}},
  overText:'おしまい！',
  draw(c,api){const st=this.st;c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.fillStyle='#e2daf0';for(let i=0;i<10;i++){c.save();c.translate(i*50,0);c.rotate(-.2);c.fillRect(0,-40,22,H+80);c.restore()}
    // 投入ゾーン
    D.rrect(c,14,TOPY-96,W-28,52,16,'rgba(255,253,248,.7)',3);
    if(api.state==='play'&&st.left>0){c.globalAlpha=st.cd>0?.4:1;this.ball(c,st.dropX,TOPY-70,BRr);c.globalAlpha=1}
    for(const p of st.pegs){const col=p.t==='gold'?'#f3c84b':p.t==='split'?'#8fd0e0':p.flash>0?'#fbe7a6':'#fffdf8';const r=PR+(p.t!=='n'?2:0)+p.flash*2;D.circle(c,p.x,p.y,r,col,2.5);if(p.t==='split'){D.circle(c,p.x-3,p.y,2,'#4a3428',0);D.circle(c,p.x+3,p.y,2,'#4a3428',0)}}
    for(let i=0;i<MULT.length;i++){const m=MULT[i],x=i*SW,fx=st.slotFx[i];D.rrect(c,x+2,SLOTY+4-fx*6,SW-4,46,8,MC[m],3);D.text(c,'×'+m,x+SW/2,SLOTY+27-fx*6,String(m).length>2?11:14,'#fff','center',OL,4)}
    for(const b of st.balls)this.ball(c,b.x,b.y,BRr);
    D.text(c,'のこり',W/2-40,SLOTY+90,16,'#7a6658');D.text(c,st.left+'球',W/2+20,SLOTY+90,26,'#4a3428');
  },
  __bot(api){if(Math.random()<.3)this.drop(this.st.dropX,api)},
};
