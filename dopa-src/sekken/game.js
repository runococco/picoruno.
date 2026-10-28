/* せっけんザリザリ：スクラッチ式にセルを削る。層ごとに色、中にお宝。30秒。 */
const SX=70,SY=200,CS=10,NC=28,NR=36,BR=22;
const PALS=[['#f6c6cf','#f9e0a8','#cbe6b8','#bfe0ef','#d9cdef'],['#cfe6e3','#a9d6cf','#f6efcf'],['#f2d1a8','#e9b68c','#fbe7c8'],['#d9cdef','#f3c6dc','#fbe0ec','#c8e1f2'],['#fff1c9','#ffd9a8','#f7b9a3','#e996a0']];
const SHAPES=['rect','round','heart','rect','oval'];
const TREAS=['star','heart','gem','duck','coin'];
const GAME={...META,sprites:['icon','treasure'],time:30,unit:'個',hudUnit:true,comboHud:false,
  bgm:{bpm:96,root:65,scale:'major',prog:[1,6,4,5],seed:15,lead:'triangle',drums:'pop',density:.45,stab:false},
  ranks:[[0,'あわあわ初心者'],[2,'せっけん好き'],[4,'ザリザリ職人'],[6,'けずりの達人'],[8,'せっけん彫刻家'],[11,'人間かんな']],
  shareText:(v,f)=>`せっけんザリザリで ${f}個 けずった！`,
  icon(c,x,y,s){D.rrect(c,x-s*.32,y-s*.22,s*.64,s*.44,s*.1,'#f6c6cf',s*.02);c.save();c.beginPath();c.rect(x-s*.32,y-s*.22,s*.64,s*.44);c.clip();c.fillStyle='#f9e0a8';c.fillRect(x-s*.32,y-s*.05,s*.64,s*.1);c.fillStyle='#bfe0ef';c.fillRect(x-s*.32,y+s*.08,s*.64,s*.15);c.restore();D.rrect(c,x-s*.32,y-s*.22,s*.64,s*.44,s*.1,null,s*.02);D.face(c,x,y-s*.08,s*.3,'smile');
    for(let i=0;i<4;i++)this.curl(c,x-s*.3+i*s*.18,y-s*.34-(i%2)*s*.08,s*.05,PALS[0][i],i)},
  curl(c,x,y,r,col,rot){c.save();c.translate(x,y);c.rotate(rot);c.lineWidth=r*.9;c.strokeStyle=OL;c.lineCap='round';c.beginPath();c.arc(0,0,r,0,Math.PI*1.5);c.stroke();c.lineWidth=r*.5;c.strokeStyle=col;c.stroke();c.restore()},
  inShape(sh,i,j){const u=(i+.5)/NC*2-1,v=(j+.5)/NR*2-1;
    if(sh==='round')return u*u+v*v*.7<.9;if(sh==='oval')return u*u*.8+v*v<.95;
    if(sh==='heart'){const x=u*1.2,y=-v*1.25+.25;return Math.pow(x*x+y*y-1,3)-x*x*y*y*y<0}
    return true},
  newSoap(){const st=this.st;const k=st.n%5,sh=SHAPES[(st.n+rndi(0,4))%5],pal=pick(PALS);st.n++;st.sh=sh;st.pal=pal;st.treas=TREAS[(st.n-1)%TREAS.length];st.cells=new Uint8Array(NC*NR);st.total=0;st.left=0;st.slide=1;st.cleared=false;
    st.stripe=rndi(0,2);
    for(let j=0;j<NR;j++)for(let i=0;i<NC;i++){if(this.inShape(sh,i,j)){st.cells[j*NC+i]=1;st.total++}}st.left=st.total},
  colAt(i,j){const st=this.st,p=st.pal,n=p.length;if(st.stripe===0)return p[Math.floor(j/NR*n)];if(st.stripe===1){return p[Math.floor((i+j)/(NC+NR)*n*2)%n]}const d=Math.hypot(i-NC/2,(j-NR/2)*.8);return p[Math.floor(d/4)%n]},
  reset(api){this.st={n:0,px:0,py:0,down:false,curls:[],snd:0,count:0};this.newSoap();api.score=0},
  shave(x,y,api){const st=this.st;if(st.slide>.05||st.cleared)return;let n=0;
    const i0=Math.floor((x-SX-BR)/CS),i1=Math.floor((x-SX+BR)/CS),j0=Math.floor((y-SY-BR)/CS),j1=Math.floor((y-SY+BR)/CS);
    for(let j=Math.max(0,j0);j<=Math.min(NR-1,j1);j++)for(let i=Math.max(0,i0);i<=Math.min(NC-1,i1);i++){const k=j*NC+i;if(!st.cells[k])continue;const cx=SX+(i+.5)*CS,cy=SY+(j+.5)*CS;if(dist(cx,cy,x,y)>BR)continue;
      st.cells[k]=0;st.left--;n++;if(Math.random()<.25)st.curls.push({x:cx,y:cy,vx:rnd(-120,120),vy:rnd(-260,-80),r:rnd(5,9),c:this.colAt(i,j),rot:rnd(6),vr:rnd(-10,10),life:rnd(.8,1.4)})}
    if(n){st.count+=n;st.snd+=n;if(st.snd>6){st.snd=0;S.noise(.05,{v:.25,f:rnd(2500,4500),q:1.5});S.noise(.03,{v:.15,f:7000,type:'highpass',at:.02})}}
    if(!st.cleared&&st.left<=st.total*.03){st.cleared=true;api.score++;S.fanfare();api.flash('#fff',.5);api.burst(SX+NC*CS/2,SY+NR*CS/2,{c:[...st.pal,'#fff','#f3c84b'],n:40,sp:420,shape:'star',r:6});api.float(W/2,SY+NR*CS/2-60,'おたからゲット！',{size:32});
      setTimeout(()=>{if(api.state==='play')this.newSoap()},900)}},
  down(x,y,api){const st=this.st;st.down=true;st.px=x;st.py=y;this.shave(x,y,api)},
  move(x,y,api){const st=this.st;if(!st.down)return;const d=dist(st.px,st.py,x,y),n=Math.ceil(d/6);for(let k=1;k<=n;k++)this.shave(lerp(st.px,x,k/n),lerp(st.py,y,k/n),api);st.px=x;st.py=y},
  up(){this.st.down=false},
  update(dt,api){const st=this.st;st.slide=Math.max(0,st.slide-dt*4);
    for(const q of st.curls){q.vy+=900*dt;q.x+=q.vx*dt;q.y+=q.vy*dt;q.rot+=q.vr*dt;q.life-=dt;if(q.y>H-80){q.y=H-80;q.vy=0;q.vx*=.8;q.vr=0}}
    st.curls=st.curls.filter(q=>q.life>0||q.y>=H-81).slice(-260)},
  treasure(c,x,y,t){if(t==='star')D.star(c,x,y,40,'#f3c84b',4);else if(t==='heart')D.path(c,c=>{c.moveTo(x,y+32);c.bezierCurveTo(x-60,y-8,x-24,y-48,x,y-18);c.bezierCurveTo(x+24,y-48,x+60,y-8,x,y+32)},'#e98fa6',4);
    else if(t==='gem')D.poly(c,[[x-30,y-14],[x-14,y-32],[x+14,y-32],[x+30,y-14],[x,y+30]],'#8fd0e0',4);else if(t==='duck'){D.ellipse(c,x,y+10,34,22,'#f6d86a',4);D.circle(c,x+16,y-16,18,'#f6d86a',4);D.poly(c,[[x+30,y-16],[x+44,y-12],[x+30,y-8]],'#f0a050',3)}
    else D.circle(c,x,y,34,'#f3c84b',4);D.face(c,x+(t==='duck'?16:0),y+(t==='duck'?-16:0),t==='duck'?22:34,'smile')},
  draw(c,api){const st=this.st;c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.fillStyle='#e6d9e8';for(let i=0;i<9;i++)for(let j=0;j<16;j++)if((i+j)%2)c.fillRect(i*48,j*48,48,48);
    D.rrect(c,-20,H-80,W+40,120,0,'#cfd8dc',4);
    D.ellipse(c,W/2,SY+NR*CS+30,170,26,'#b9c7cc',4);
    c.save();c.translate(st.slide*W,0);
    this.treasure(c,SX+NC*CS/2,SY+NR*CS/2,st.treas);
    for(let j=0;j<NR;j++)for(let i=0;i<NC;i++)if(st.cells[j*NC+i]){c.fillStyle=this.colAt(i,j);c.fillRect(SX+i*CS,SY+j*CS,CS+.6,CS+.6)}
    // 輪郭：残っているセルの外周
    c.strokeStyle=OL;c.lineWidth=3;c.beginPath();
    for(let j=0;j<NR;j++)for(let i=0;i<NC;i++){if(!st.cells[j*NC+i])continue;const x=SX+i*CS,y=SY+j*CS;
      if(i===0||!st.cells[j*NC+i-1]){c.moveTo(x,y);c.lineTo(x,y+CS)}if(i===NC-1||!st.cells[j*NC+i+1]){c.moveTo(x+CS,y);c.lineTo(x+CS,y+CS)}
      if(j===0||!st.cells[(j-1)*NC+i]){c.moveTo(x,y);c.lineTo(x+CS,y)}if(j===NR-1||!st.cells[(j+1)*NC+i]){c.moveTo(x,y+CS);c.lineTo(x+CS,y+CS)}}
    c.stroke();
    if(st.left>st.total*.7)D.face(c,SX+NC*CS/2,SY+NR*CS*.3,60,'smile');
    c.restore();
    for(const q of st.curls)this.curl(c,q.x,q.y,q.r,q.c,q.rot);
    const pr=1-st.left/st.total;D.text(c,'けずった',W/2,150,13,'#8e8077');D.rrect(c,90,162,W-180,12,6,'#fffdf8',3);if(pr>0)D.rrect(c,92,164,(W-184)*Math.min(1,pr/.97),8,4,this.accent,0);
  },
  __bot(api){const st=this.st;const y=SY+rnd(0,NR*CS);this.down(SX-20,y,api);for(let k=0;k<6;k++)this.move(SX+k*60,y+rnd(-20,20),api);this.up()},
};
