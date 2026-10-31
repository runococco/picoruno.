/* ころころペンキ：スワイプでボールがかべまで転がり、通ったゆかを塗る。全部塗ったらクリア。 */
const PAINT=['#f08a8a','#7fc3a8','#f2b45a','#8a9de0','#e58ac0','#9cc86a','#6fbfd9','#c49ae0'];
const DIRS={L:[-1,0],R:[1,0],U:[0,-1],D:[0,1]};
const GAME={...META,sprites:['icon','ball'],unit:'面',time:60,hudUnit:true,comboHud:false,
  bgm:{bpm:128,root:62,scale:'major',prog:[1,4,6,5],seed:63,lead:'square',drums:'four',density:.55},
  ranks:[[0,'はじめてのペンキ'],[3,'ペンキ見習い'],[6,'ぬりぬり上手'],[10,'ペンキ職人'],[15,'ゆかぬり名人'],[22,'ペンキの神']],
  shareText:(v,f)=>`ころころペンキで ${f}面 ぬりつぶした！`,
  icon(c,x,y,s){const g=s*.19,P=[[0,0],[1,0],[2,0],[2,1],[2,2],[1,2]];D.rrect(c,x-g*2.1,y-g*2.1,g*4.2,g*4.2,g*.4,'#6b5d78',4);for(let i=0;i<4;i++)for(let j=0;j<4;j++){if(i===3||j===3&&i<2)continue;const pnt=P.some(q=>q[0]===i&&q[1]===j);c.fillStyle=pnt?'#f08a8a':'#fbf7f0';c.fillRect(x-g*2+i*g,y-g*2+j*g,g,g)}this.ball(c,x-g*.5,y+g*.5,g*.6,'#f08a8a')},
  ball(c,x,y,r,col){D.circle(c,x,y,r,col);D.face(c,x,y+r*.05,r*1.05)},
  gen(lv){// 掘ったマスから、ボールの止まる位置どうしのつながりで塗れるマスを決める
    const n=Math.min(6+Math.floor(lv/2),11),m=Math.min(8+Math.floor(lv/2),14);
    for(let tries=0;tries<200;tries++){
      const g=[];for(let y=0;y<m;y++)g.push(new Array(n).fill(1));
      let x=rndi(1,n-2),y=rndi(1,m-2);const sx=x,sy=y;g[y][x]=0;let last='';
      const steps=8+lv*2;for(let s=0;s<steps;s++){const ds=Object.keys(DIRS).filter(d=>d!==last);const d=pick(ds),[dx,dy]=DIRS[d];const len=rndi(2,5);
        for(let k=0;k<len;k++){const nx=x+dx,ny=y+dy;if(nx<1||ny<1||nx>n-2||ny>m-2)break;x=nx;y=ny;g[y][x]=0}last=d}
      const slide=(px,py,d)=>{const[dx,dy]=DIRS[d];const cells=[];while(g[py+dy]&&g[py+dy][px+dx]===0){px+=dx;py+=dy;cells.push(px+','+py)}return{px,py,cells}};
      const key=(a,b)=>a+','+b,seen=new Set([key(sx,sy)]),q=[[sx,sy]],paint=new Set([key(sx,sy)]),edges={};
      while(q.length){const[px,py]=q.shift();edges[key(px,py)]=[];for(const d in DIRS){const r=slide(px,py,d);if(!r.cells.length)continue;edges[key(px,py)].push(key(r.px,r.py));r.cells.forEach(cc=>paint.add(cc));const k=key(r.px,r.py);if(!seen.has(k)){seen.add(k);q.push([r.px,r.py])}}}
      // どの止まり位置からもスタートに戻れること（つまり行き止まりなし）
      const back=new Set([key(sx,sy)]);let ch=true;while(ch){ch=false;for(const k of seen)if(!back.has(k)&&edges[k].some(e=>back.has(e))){back.add(k);ch=true}}
      if(back.size!==seen.size||paint.size<Math.min(12+lv*3,n*m*.45))continue;
      for(let yy=0;yy<m;yy++)for(let xx=0;xx<n;xx++)if(g[yy][xx]===0&&!paint.has(key(xx,yy)))g[yy][xx]=1;
      return{g,n,m,sx,sy,total:paint.size}}
    return this.gen(Math.max(0,lv-1))},
  newLevel(){const st=this.st;st.lv++;const L=this.gen(st.lv);Object.assign(st,L);st.bx=L.sx;st.by=L.sy;st.px=L.sx;st.py=L.sy;st.col=PAINT[(st.lv-1)%PAINT.length];
    st.p=new Set([L.sx+','+L.sy]);st.paintT={};st.paintT[L.sx+','+L.sy]=1;st.mv=null;st.clearT=0;st.queue=null;
    st.cs=Math.min((W-40)/L.n,(H-260)/L.m);st.ox=(W-st.cs*L.n)/2;st.oy=170+((H-260)-st.cs*L.m)/2},
  reset(api){this.st={lv:0};this.newLevel();api.score=0},
  go(d,api){const st=this.st;if(st.clearT>0)return;if(st.mv){st.queue=d;return}const[dx,dy]=DIRS[d];let x=st.bx,y=st.by,path=[];
    while(st.g[y+dy]&&st.g[y+dy][x+dx]===0){x+=dx;y+=dy;path.push([x,y])}
    if(!path.length){st.bump={d,t:.15};S.tap(.5);return}
    st.mv={path,i:0,t:0,d};S.whoosh()},
  down(x,y){this.st.sw={x,y,used:false}},
  move(x,y,api){const s=this.st.sw;if(!s||s.used)return;const dx=x-s.x,dy=y-s.y;if(Math.hypot(dx,dy)<22)return;s.used=true;
    this.go(Math.abs(dx)>Math.abs(dy)?(dx>0?'R':'L'):(dy>0?'D':'U'),api)},
  up(){this.st.sw=null},
  key(k,api){const m={ArrowLeft:'L',ArrowRight:'R',ArrowUp:'U',ArrowDown:'D'}[k];if(m)this.go(m,api)},
  update(dt,api){const st=this.st;if(st.bump){st.bump.t-=dt;if(st.bump.t<=0)st.bump=null}
    if(st.mv){const mv=st.mv;mv.t+=dt*22;while(mv.t>=1&&mv.i<mv.path.length){mv.t-=1;const[x,y]=mv.path[mv.i++];st.bx=x;st.by=y;const k=x+','+y;
        if(!st.p.has(k)){st.p.add(k);st.paintT[k]=0;S.tone(500+st.p.size*9,.05,{type:'sine',v:.12});api.add(0)}}
      const nx=mv.i<mv.path.length?mv.path[mv.i]:null;st.px=nx?lerp(st.bx,nx[0],mv.t):st.bx;st.py=nx?lerp(st.by,nx[1],mv.t):st.by;
      if(mv.i>=mv.path.length){st.mv=null;st.px=st.bx;st.py=st.by;S.thud();api.shake(3);st.squash={d:mv.d,t:.18};
        const[sx,sy]=this.cell(st.bx,st.by);api.burst(sx,sy,{c:st.col,n:6,sp:120,r:4,g:0,life:.35});
        if(st.p.size>=st.total){st.clearT=1;api.add(1);api.timeLeft+=8;S.fanfare();api.flash('#fff',.35);api.float(W/2,150,'クリア！ +8秒',{size:32,c:'#f3c84b'});
          for(let i=0;i<5;i++)api.burst(rnd(60,W-60),rnd(250,600),{c:PAINT,n:12,sp:240,shape:'star'})}
        else if(st.queue){const q=st.queue;st.queue=null;this.go(q,api)}}}
    for(const k in st.paintT)st.paintT[k]=Math.min(1,st.paintT[k]+dt*6);
    if(st.squash){st.squash.t-=dt;if(st.squash.t<=0)st.squash=null}
    if(st.clearT>0){st.clearT-=dt;if(st.clearT<=0)this.newLevel()}},
  cell(x,y){const st=this.st;return[st.ox+(x+.5)*st.cs,st.oy+(y+.5)*st.cs]},
  draw(c,api){const st=this.st,cs=st.cs;c.fillStyle='#eae6f2';c.fillRect(0,0,W,H);
    D.text(c,'Lv.'+st.lv+'　'+Math.floor(st.p.size/st.total*100)+'%',W/2,128,20,'#5b4d45');
    D.rrect(c,st.ox-8,st.oy-8,cs*st.n+16,cs*st.m+16,14,'#6b5d78',4);
    for(let y=0;y<st.m;y++)for(let x=0;x<st.n;x++){const X=st.ox+x*cs,Y=st.oy+y*cs;if(st.g[y][x]){c.fillStyle='#6b5d78';c.fillRect(X-.5,Y-.5,cs+1,cs+1);continue}
      c.fillStyle='#fbf7f0';c.fillRect(X,Y,cs,cs);const k=x+','+y;if(st.p.has(k)){const t=ease.outBack(st.paintT[k]||1),r=cs*.5*Math.min(1.42,t*1.42);
        c.save();c.beginPath();c.rect(X,Y,cs,cs);c.clip();c.fillStyle=st.col;c.beginPath();c.arc(X+cs/2,Y+cs/2,r,0,7);c.fill();c.restore()}}
    c.strokeStyle='rgba(91,77,69,.12)';c.lineWidth=1;for(let y=0;y<st.m;y++)for(let x=0;x<st.n;x++)if(!st.g[y][x])c.strokeRect(st.ox+x*cs,st.oy+y*cs,cs,cs);
    const[bx,by]=this.cell(st.px,st.py);let sx=1,sy=1;if(st.squash){const k=st.squash.t/.18*.25,h=st.squash.d==='L'||st.squash.d==='R';sx=h?1-k:1+k;sy=h?1+k:1-k}
    if(st.mv){const h=st.mv.d==='L'||st.mv.d==='R';sx=h?1.15:.9;sy=h?.9:1.15}
    c.save();c.translate(bx,by);c.scale(sx,sy);this.ball(c,0,0,cs*.38,st.col);c.restore();
    if(st.clearT>0){c.globalAlpha=Math.min(.5,(1-st.clearT)*.8);c.fillStyle=st.col;c.fillRect(st.ox,st.oy,cs*st.n,cs*st.m);c.globalAlpha=1}
  },
  __bot(api){const st=this.st;if(st.mv||st.clearT>0)return;// まだ塗ってないマスが多い方向へ
    let best=null,bv=-1;for(const d in DIRS){const[dx,dy]=DIRS[d];let x=st.bx,y=st.by,v=0,len=0;while(st.g[y+dy]&&st.g[y+dy][x+dx]===0){x+=dx;y+=dy;len++;if(!st.p.has(x+','+y))v++}
      if(!len)continue;const sc=v+Math.random()*1.2;if(sc>bv){bv=sc;best=d}}if(best)this.go(best,api)},
};
