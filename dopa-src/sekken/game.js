/* せっけんザリザリ：なぞった所がまず表面だけ削れて（すじ跡）、もう一度で削り取れる。削りカスはくるくるのリボン。中にお宝。30秒。 */
const CS=7,NC=40,NR=51,SX=(W-NC*CS)/2,SY=200,BR=22;
const PALS=[['#f6c6cf','#f9e0a8','#cbe6b8','#bfe0ef','#d9cdef'],['#cfe6e3','#a9d6cf','#f6efcf'],['#f2d1a8','#e9b68c','#fbe7c8'],['#d9cdef','#f3c6dc','#fbe0ec','#c8e1f2'],['#fff1c9','#ffd9a8','#f7b9a3','#e996a0']];
const SHAPES=['rect','round','heart','rect','oval'];
const TREAS=['star','heart','gem','duck','coin'];
const GAME={...META,sprites:['icon','treasure'],time:30,unit:'個',hudUnit:true,comboHud:false,
  bgm:{bpm:96,root:65,scale:'major',prog:[1,6,4,5],seed:15,lead:'triangle',drums:'pop',density:.45,stab:false},
  ranks:[[0,'あわあわ初心者'],[2,'せっけん好き'],[4,'ザリザリ職人'],[6,'けずりの達人'],[8,'せっけん彫刻家'],[11,'人間かんな']],
  shareText:(v,f)=>`せっけんザリザリで ${f}個 けずった！`,
  icon(c,x,y,s){D.rrect(c,x-s*.32,y-s*.22,s*.64,s*.44,s*.1,'#f6c6cf',s*.02);c.save();c.beginPath();c.rect(x-s*.32,y-s*.22,s*.64,s*.44);c.clip();c.fillStyle='#f9e0a8';c.fillRect(x-s*.32,y-s*.05,s*.64,s*.1);c.fillStyle='#bfe0ef';c.fillRect(x-s*.32,y+s*.08,s*.64,s*.15);c.restore();D.rrect(c,x-s*.32,y-s*.22,s*.64,s*.44,s*.1,null,s*.02);D.face(c,x,y-s*.08,s*.3,'smile');
    for(let i=0;i<4;i++)this.curl(c,x-s*.3+i*s*.18,y-s*.34-(i%2)*s*.08,s*.05,PALS[0][i],i)},
  // 削りカス：うすいリボンがくるくるねじれたもの（横から見たらせん）
  curl(c,x,y,r,col,rot){c.save();c.translate(x,y);c.rotate(rot);c.lineCap='round';c.lineJoin='round';
    const L=r*2.6,pts=[];for(let k=0;k<=40;k++){const t=k/40,a=t*Math.PI*2*Math.max(1.5,r/4);pts.push([-L/2+t*L+Math.sin(a)*r*.45,-Math.cos(a)*r*.55])}
    const path=()=>{c.beginPath();pts.forEach((p,i)=>i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]))};
    path();c.lineWidth=Math.max(3,r*.32)+3;c.strokeStyle=OL;c.stroke();path();c.lineWidth=Math.max(3,r*.32);c.strokeStyle=col;c.stroke();c.restore()},
  // せっけんの形（なめらかな輪郭）
  shapePath(c,sh){const w=NC*CS,h=NR*CS,cx=w/2,cy=h/2;c.beginPath();
    if(sh==='round')c.ellipse(cx,cy,w*.49,h*.49,0,0,7);else if(sh==='oval')c.ellipse(cx,cy,w*.5,h*.44,0,0,7);
    else if(sh==='heart'){c.moveTo(cx,h*.98);c.bezierCurveTo(-w*.05,h*.62,-w*.02,h*.05,cx,h*.3);c.bezierCurveTo(w*1.02,h*.05,w*1.05,h*.62,cx,h*.98)}
    else c.roundRect(0,0,w,h,26)},
  layers(){const k=2,PAD=10,w=(NC*CS+PAD*2)*k,h=(NR*CS+PAD*2)*k;
    if(!this.cv){this.cv={};for(const n of['top','inner','tmp']){const e=document.createElement('canvas');e.width=w;e.height=h;this.cv[n]=e}}
    return{k,PAD}},
  paintSoap(){const st=this.st,{k,PAD}=this.layers();
    for(const n of['top','inner']){const e=this.cv[n].getContext('2d');e.setTransform(1,0,0,1,0,0);e.clearRect(0,0,9999,9999);e.setTransform(k,0,0,k,PAD*k,PAD*k);
      e.save();this.shapePath(e,st.sh);e.clip();const q=CS/3.5;for(let y=0;y<NR*CS;y+=q)for(let x=0;x<NC*CS;x+=q){e.fillStyle=this.colAt(x/CS,y/CS);e.fillRect(x-.3,y-.3,q+.6,q+.6)}
      if(n==='inner'){e.fillStyle='rgba(255,255,255,.45)';e.fillRect(-PAD,-PAD,NC*CS+PAD*2,NR*CS+PAD*2)}e.restore()}},
  // 見た目を削る：表面は太く、中は細く。中にはなぞった向きのすじを残す
  carve(x0,y0,x1,y1){const{k,PAD}=this.layers(),lx0=x0-SX,ly0=y0-SY,lx1=x1-SX,ly1=y1-SY;
    const inn=this.cv.inner.getContext('2d'),top=this.cv.top.getContext('2d');
    const l=Math.hypot(lx1-lx0,ly1-ly0);if(l>.5){const nx=-(ly1-ly0)/l,ny=(lx1-lx0)/l;inn.save();inn.globalCompositeOperation='source-atop';inn.lineCap='round';inn.lineWidth=1.6;
      for(const o of[-17,-11,-5,1,7,13,19]){inn.strokeStyle=Math.abs(o)%2?'rgba(91,77,69,.10)':'rgba(255,255,255,.5)';inn.beginPath();inn.moveTo(lx0+nx*o,ly0+ny*o);inn.lineTo(lx1+nx*o,ly1+ny*o);inn.stroke()}inn.restore()}
    for(const[e,wd]of[[top,BR*2],[inn,BR*1.1]]){e.save();e.globalCompositeOperation='destination-out';e.lineCap='round';e.lineWidth=wd;e.beginPath();e.moveTo(lx0,ly0);e.lineTo(lx1+.01,ly1);e.stroke();e.restore()}},
  inShape(sh,i,j){const u=(i+.5)/NC*2-1,v=(j+.5)/NR*2-1;
    if(sh==='round')return u*u/(.98*.98)+v*v/(.98*.98)<1;if(sh==='oval')return u*u+v*v/(.88*.88)<1;
    if(sh==='heart'){const x=u*1.2,y=-v*1.25+.25;return Math.pow(x*x+y*y-1,3)-x*x*y*y*y<0}
    return true},
  newSoap(){const st=this.st;const k=st.n%5,sh=SHAPES[(st.n+rndi(0,4))%5],pal=pick(PALS);st.n++;st.sh=sh;st.pal=pal;st.treas=TREAS[(st.n-1)%TREAS.length];st.cells=new Uint8Array(NC*NR);st.grooves=[];st.total=0;st.left=0;st.slide=1;st.cleared=false;
    st.stripe=rndi(0,2);
    for(let j=0;j<NR;j++)for(let i=0;i<NC;i++){if(this.inShape(sh,i,j)){st.cells[j*NC+i]=2;st.total++}}st.left=st.total;this.paintSoap()},
  colAt(i,j){const st=this.st,p=st.pal,n=p.length;if(st.stripe===0)return p[Math.floor(j/NR*n)];if(st.stripe===1){return p[Math.floor((i+j)/(NC+NR)*n*2)%n]}const d=Math.hypot(i-NC/2,(j-NR/2)*.8);return p[Math.floor(d/5.7)%n]},
  reset(api){this.st={n:0,px:0,py:0,down:false,curls:[],snd:0,count:0,peel:null,touch:0,speed:0};this.newSoap();api.score=0},
  shave(x,y,api,px,py){const st=this.st;if(st.slide>.05||st.cleared)return;let n=0;this.carve(px??x,py??y,x,y);
    const i0=Math.floor((x-SX-BR)/CS),i1=Math.floor((x-SX+BR)/CS),j0=Math.floor((y-SY-BR)/CS),j1=Math.floor((y-SY+BR)/CS);
    for(let j=Math.max(0,j0);j<=Math.min(NR-1,j1);j++)for(let i=Math.max(0,i0);i<=Math.min(NC-1,i1);i++){const k=j*NC+i;if(!st.cells[k])continue;const cx=SX+(i+.5)*CS,cy=SY+(j+.5)*CS;if(dist(cx,cy,x,y)>BR)continue;
      const dd=dist(cx,cy,x,y);st.cells[k]=Math.max(0,st.cells[k]-(dd<BR*.55?2:1));st.touch++;if(st.cells[k])continue;st.left--;n++;if(!st.peel)st.peel={c:this.colAt(i,j),len:0,rot:rnd(6)};st.peel.len+=.18}
    if(st.peel){st.peel.x=x;st.peel.y=y-6;if(st.peel.len>9)this.dropPeel()}
    if(n)st.count+=n;
    if(!st.cleared&&st.left<=st.total*.03){st.cleared=true;api.score++;S.fanfare();api.flash('#fff',.5);api.burst(SX+NC*CS/2,SY+NR*CS/2,{c:[...st.pal,'#fff','#f3c84b'],n:40,sp:420,shape:'star',r:6});api.float(W/2,SY+NR*CS/2-60,'おたからゲット！',{size:32});
      setTimeout(()=>{if(api.state==='play')this.newSoap()},900)}},
  dropPeel(){const st=this.st,q=st.peel;if(!q)return;st.peel=null;if(q.len<1.2)return;
    st.curls.push({x:q.x,y:q.y,vx:rnd(-140,140),vy:rnd(-300,-120),r:4+q.len*.75,c:q.c,rot:q.rot,vr:rnd(-8,8),life:rnd(1,1.6)})},
  // ASMRの削り音：ずっと鳴っているノイズの音量を、削った量となぞる速さで上下させる＋ときどき細かいパリッ
  scrapeInit(){const ac=AU.ctx;if(!ac||this.sc||!AU.nbuf)return;const mk=(type,f,q)=>{const src=ac.createBufferSource();src.buffer=AU.nbuf;src.loop=true;const fl=ac.createBiquadFilter();fl.type=type;fl.frequency.value=f;fl.Q.value=q;const g=ac.createGain();g.gain.value=0;src.connect(fl);fl.connect(g);g.connect(AU.sfx);src.start(0,Math.random());return{fl,g}};
    this.sc={body:mk('bandpass',1600,.8),air:mk('highpass',5200,.5)}},
  scrape(dt){const st=this.st,ac=AU.ctx;if(!ac)return;this.scrapeInit();if(!this.sc)return;
    const amt=Math.min(1,st.touch/14),sp=Math.min(1,st.speed/900),t=ac.currentTime;st.touch=0;
    this.sc.body.g.gain.setTargetAtTime(amt*(.32+sp*.25),t,.03);this.sc.air.g.gain.setTargetAtTime(amt*(.12+sp*.18),t,.03);
    this.sc.body.fl.frequency.setTargetAtTime(1200+sp*1600+rnd(-200,200),t,.05);
    if(amt>0&&Math.random()<amt*.9)S.noise(.006,{v:rnd(.08,.22)*amt,f:rnd(3500,9000),type:'highpass',a:.0003});
    if(amt>.3&&Math.random()<.15)S.noise(.02,{v:.1,f:rnd(700,1300),q:3})},
  down(x,y,api){const st=this.st;st.down=true;st.px=x;st.py=y;this.shave(x,y,api)},
  move(x,y,api){const st=this.st;if(!st.down)return;const d=dist(st.px,st.py,x,y),n=Math.ceil(d/6);st.speed=Math.max(st.speed,d*60);for(let k=1;k<=n;k++)this.shave(lerp(st.px,x,k/n),lerp(st.py,y,k/n),api,lerp(st.px,x,(k-1)/n),lerp(st.py,y,(k-1)/n));st.px=x;st.py=y},
  up(){this.st.down=false;this.dropPeel()},
  update(dt,api){const st=this.st;st.slide=Math.max(0,st.slide-dt*4);st.speed*=Math.pow(.02,dt);this.scrape(dt);
    for(const q of st.curls){q.vy+=900*dt;q.x+=q.vx*dt;q.y+=q.vy*dt;q.rot+=q.vr*dt;q.life-=dt;if(q.y>H-80){if(q.vy>200)S.noise(.035,{v:.05,f:rnd(1500,2500),q:1.2});q.y=H-80;q.vy=0;q.vx*=.8;q.vr=0}}
    st.curls=st.curls.filter(q=>q.life>0||q.y>=H-81).slice(-160);if(st.peel)st.peel.rot+=dt*2},
  treasure(c,x,y,t){if(t==='star')D.star(c,x,y,40,'#f3c84b',4);else if(t==='heart')D.path(c,c=>{c.moveTo(x,y+32);c.bezierCurveTo(x-60,y-8,x-24,y-48,x,y-18);c.bezierCurveTo(x+24,y-48,x+60,y-8,x,y+32)},'#e98fa6',4);
    else if(t==='gem')D.poly(c,[[x-30,y-14],[x-14,y-32],[x+14,y-32],[x+30,y-14],[x,y+30]],'#8fd0e0',4);else if(t==='duck'){D.ellipse(c,x,y+10,34,22,'#f6d86a',4);D.circle(c,x+16,y-16,18,'#f6d86a',4);D.poly(c,[[x+30,y-16],[x+44,y-12],[x+30,y-8]],'#f0a050',3)}
    else D.circle(c,x,y,34,'#f3c84b',4);D.face(c,x+(t==='duck'?16:0),y+(t==='duck'?-16:0),t==='duck'?22:34,'smile')},
  draw(c,api){const st=this.st;c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.fillStyle='#e6d9e8';for(let i=0;i<9;i++)for(let j=0;j<16;j++)if((i+j)%2)c.fillRect(i*48,j*48,48,48);
    D.rrect(c,-20,H-80,W+40,120,0,'#cfd8dc',4);
    D.ellipse(c,W/2,SY+NR*CS+30,170,26,'#b9c7cc',4);
    c.save();c.translate(st.slide*W,0);
    this.treasure(c,SX+NC*CS/2,SY+NR*CS/2,st.treas);
    // せっけん：中の層（ふち付き）→ 表面の層（段差のふち）
    {const{k,PAD}=this.layers(),tc=this.cv.tmp.getContext('2d'),ox=SX-PAD,oy=SY-PAD,w=NC*CS+PAD*2,h=NR*CS+PAD*2;
      const ink=(src,col)=>{tc.globalCompositeOperation='source-over';tc.clearRect(0,0,9999,9999);tc.drawImage(src,0,0);tc.globalCompositeOperation='source-in';tc.fillStyle=col;tc.fillRect(0,0,9999,9999);tc.globalCompositeOperation='source-over';return this.cv.tmp};
      const ring=(src,col,d)=>{const im=ink(src,col);for(let a=0;a<8;a++)c.drawImage(im,ox+Math.cos(a*Math.PI/4)*d,oy+Math.sin(a*Math.PI/4)*d,w,h)};
      ring(this.cv.inner,OL,3);c.drawImage(this.cv.inner,ox,oy,w,h);
      c.globalAlpha=.45;ring(this.cv.top,OL,1.6);c.globalAlpha=1;c.drawImage(this.cv.top,ox,oy,w,h)}
    if(st.left>st.total*.7)D.face(c,SX+NC*CS/2,SY+NR*CS*.3,60,'smile');
    c.restore();
    for(const q of st.curls)this.curl(c,q.x,q.y,q.r,q.c,q.rot);
    if(st.peel&&st.peel.len>1.2)this.curl(c,st.peel.x,st.peel.y,4+st.peel.len*.75,st.peel.c,st.peel.rot);
    const pr=1-st.left/st.total;D.text(c,'けずった',W/2,150,13,'#8e8077');D.rrect(c,90,162,W-180,12,6,'#fffdf8',3);if(pr>0)D.rrect(c,92,164,(W-184)*Math.min(1,pr/.97),8,4,this.accent,0);
  },
  __bot(api){const st=this.st;const y=SY+rnd(0,NR*CS);this.down(SX-20,y,api);for(let k=0;k<6;k++)this.move(SX+k*60,y+rnd(-20,20),api);this.up()},
};
