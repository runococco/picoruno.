/* おはじきはじき：円形物理。自分の玉で相手玉を円外へ。 */
const CX=W/2,CY=400,CR=175,N=8;
const COLS=['#e2645a','#f2c84b','#7fb2e0','#9cc86a','#f2a5c0','#c49ae0'];
const GAME={...META,sprites:['icon','piece'],unit:'点',fullBleed:true,
  bgm:{bpm:104,root:62,scale:'major',prog:[1,3,4,5],seed:88,lead:'triangle',drums:'light',density:.45},
  ranks:[[0,'コロコロ'],[300,'おはじき見習い'],[600,'はじき上手'],[900,'おはじきの達人'],[1300,'円の支配者'],[1700,'伝説のおはじき']],
  shareText:(v,f)=>`おはじきはじきで ${f}点！`,
  icon(c,x,y,s){D.circle(c,x,y,s*.46,'#fbf7f0');this.piece(c,x-s*.15,y+s*.1,s*.14,'#fff');this.piece(c,x+s*.15,y-s*.12,s*.12,'#e2645a');this.piece(c,x+s*.22,y+s*.2,s*.11,'#7fb2e0');this.piece(c,x-s*.1,y-s*.25,s*.11,'#f2c84b')},
  piece(c,x,y,r,col){D.circle(c,x,y,r,col);if(col!=='#fff')D.circle(c,x,y,r*.38,col,2.5)},
  reset(api){this.st={n:0,p:[],me:null,moving:false,sw:null,t:0,round:0,outN:0};api.score=0;this.setup()},
  setup(){const st=this.st;st.round++;st.p=[];const cnt=6+Math.min(st.round,4);for(let i=0;i<cnt;i++){let x,y,ok=0;for(let k=0;k<40&&!ok;k++){const a=rnd(0,Math.PI*2),d=rnd(0,CR-50);x=CX+Math.cos(a)*d;y=CY-30+Math.sin(a)*d*.75;ok=st.p.every(q=>dist(x,y,q.x,q.y)>40)}st.p.push({x,y,vx:0,vy:0,r:18,c:COLS[i%6],out:false})}
    st.me={x:CX,y:CY+130,vx:0,vy:0,r:20,c:'#fff',out:false};st.p.push(st.me)},
  down(x,y){const st=this.st;if(st.moving||st.n>=N)return;st.sw={x,y,t:performance.now()}},
  up(x,y,api){const st=this.st,s=st.sw;st.sw=null;if(!s||st.moving||st.n>=N)return;const dx=x-s.x,dy=y-s.y;if(Math.hypot(dx,dy)<20)return;const dt=Math.max(50,performance.now()-s.t);const v=clamp(Math.hypot(dx,dy)/dt*1000,300,1100);
    st.me.vx=dx/Math.hypot(dx,dy)*v;st.me.vy=dy/Math.hypot(dx,dy)*v;st.moving=true;st.n++;st.outN=0;S.clink();S.whoosh()},
  update(dt,api){const st=this.st;st.t+=dt;if(!st.moving)return;let any=false;const ps=st.p.filter(q=>!q.out);
    for(const q of ps){q.x+=q.vx*dt;q.y+=q.vy*dt;const f=Math.pow(.25,dt);q.vx*=f;q.vy*=f;if(Math.hypot(q.vx,q.vy)<8){q.vx=0;q.vy=0}else any=true;
      const d=dist(q.x,q.y,CX,CY)/1;const ex=(q.x-CX)/CR,ey=(q.y-CY)/(CR*.75);if(ex*ex+ey*ey>1.05){q.out=true;if(q===st.me){api.add(-50);api.float(q.x,q.y-30,'-50',{size:22,c:'#e2645a'});S.bad();api.combo=0}else{st.outN++;const pts=50*st.outN;api.add(pts);api.float(q.x,q.y-30,'+'+pts,{size:20+st.outN*4,c:'#c49ae0'});S.coin(1+st.outN*.1);api.burst(q.x,q.y,{c:[q.c,'#fff'],n:8,sp:150,r:3})}}}
    for(let i=0;i<ps.length;i++)for(let j=i+1;j<ps.length;j++){const a=ps[i],b=ps[j];if(a.out||b.out)continue;const dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy),m=a.r+b.r;if(d<m&&d>0){const nx=dx/d,ny=dy/d;const ov=(m-d)/2;a.x-=nx*ov;a.y-=ny*ov;b.x+=nx*ov;b.y+=ny*ov;const rv=(a.vx-b.vx)*nx+(a.vy-b.vy)*ny;if(rv>0){a.vx-=rv*nx;a.vy-=rv*ny;b.vx+=rv*nx;b.vy+=rv*ny;if(rv>60)S.clink(.7+Math.min(rv,600)/900)}}}
    if(!any){st.moving=false;if(st.outN>=3){api.combo++;S.perfect();api.float(CX,200,st.outN+'こ同時！',{size:30,c:'#c49ae0'});api.flash('#fff',.25)}
      const left=st.p.filter(q=>!q.out&&q!==st.me).length;if(st.me.out){st.me.out=false;st.me.x=CX;st.me.y=CY+130;st.me.vx=st.me.vy=0}
      if(left===0){api.add(200);api.float(CX,250,'全部出た！+200',{size:28,c:'#c49ae0'});S.fanfare();this.setup()}
      if(st.n>=N){st.endT=0;st.fin=true}}
    if(st.fin){st.endT+=dt;if(st.endT>.8)api.end()}},
  draw(c,api){const st=this.st;c.fillStyle='#f3ecf6';c.fillRect(0,api.top,W,api.bottom-api.top);
    D.ellipse(c,CX,CY+12,CR+12,(CR+12)*.75,'#d9cfe3',0);D.ellipse(c,CX,CY,CR,CR*.75,'#fbf7f0',4);c.setLineDash([6,8]);c.lineWidth=2;c.strokeStyle='#c49ae0';c.beginPath();c.ellipse(CX,CY,CR-14,(CR-14)*.75,0,0,Math.PI*2);c.stroke();c.setLineDash([]);
    const ps=st.p.filter(q=>!q.out).sort((a,b)=>a.y-b.y);for(const q of ps){D.ellipse(c,q.x,q.y+q.r*.7,q.r*.9,q.r*.35,'rgba(90,77,69,.12)',0);this.piece(c,q.x,q.y,q.r,q.c)}
    if(st.sw&&!st.moving){c.lineWidth=3;c.strokeStyle='#c49ae0';c.setLineDash([5,6]);c.beginPath();c.moveTo(st.me.x,st.me.y);c.lineTo(st.me.x+(api.px-st.sw.x||0),st.me.y+(api.py-st.sw.y||0));c.stroke();c.setLineDash([])}
    for(let i=0;i<N;i++)D.circle(c,W/2-(N-1)*12+i*24,150,8,i<st.n?'#c49ae0':'#fff',2.5);
    if(api.state==='play'&&st.n===0)D.text(c,'スワイプではじく！',CX,620,22,'#5b4d45')},
  __bot(api){const st=this.st;if(st.moving||st.n>=N||st.fin)return;const tg=st.p.find(q=>!q.out&&q!==st.me);if(!tg)return;const dx=tg.x-st.me.x,dy=tg.y-st.me.y;const d=Math.hypot(dx,dy);st.me.vx=dx/d*800;st.me.vy=dy/d*800;st.moving=true;st.n++;st.outN=0;S.clink()},
};
