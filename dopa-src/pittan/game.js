/* ぴったんブロック：Block Blast/1010 系。8x8、3ピース、列消し、コンボ。 */
const N=8,CS=44,BX=(W-N*CS)/2,BY=150,TRAYY=600,SLOTS=[78,210,342],TS=.5;
const SHP=[[[0,0]],[[0,0],[1,0]],[[0,0],[0,1]],[[0,0],[1,0],[2,0]],[[0,0],[0,1],[0,2]],[[0,0],[1,0],[2,0],[3,0]],[[0,0],[0,1],[0,2],[0,3]],
  [[0,0],[1,0],[0,1],[1,1]],[[0,0],[1,0],[2,0],[0,1],[1,1],[2,1],[0,2],[1,2],[2,2]],[[0,0],[0,1],[1,1]],[[1,0],[0,1],[1,1]],[[0,0],[1,0],[0,1]],[[0,0],[1,0],[1,1]],
  [[0,0],[0,1],[0,2],[1,2],[2,2]],[[0,0],[1,0],[2,0],[2,1],[2,2]],[[0,0],[1,0],[2,0],[1,1]],[[1,0],[0,1],[1,1],[2,1]],[[0,0],[0,1],[1,1],[1,2]],[[1,0],[2,0],[0,1],[1,1]],
  [[0,0],[1,0],[2,0],[3,0],[4,0]],[[0,0],[0,1],[0,2],[0,3],[0,4]],[[0,0],[1,0],[0,1],[1,1],[0,2],[1,2]]];
const PC=['#e98f8f','#f3c84b','#8fcf8a','#7fc6d8','#a99ae0','#f2a97a'];
const GAME={...META,unit:'点',
  bgm:{bpm:116,root:64,scale:'major',prog:[1,5,6,4],seed:44,lead:'triangle',drums:'pop',density:.55},
  ranks:[[0,'つみき見習い'],[300,'ぴったん好き'],[1000,'ならべ上手'],[2500,'消し職人'],[5000,'ブロックの鬼'],[9000,'ぴったん神']],
  shareText:(v,f)=>`ぴったんブロックで ${f}点！`,
  icon(c,x,y,s){const k=s*.16;[[0,0,0],[1,0,0],[2,0,0],[0,1,3],[1,1,4],[2,1,2],[1,2,1]].forEach(([i,j,ci])=>this.cell(c,x+(i-1.5)*k,y+(j-1.5)*k,k,PC[ci]));D.face(c,x,y-k*.5+k*.5,k*1.1,'smile')},
  cell(c,x,y,s,col){D.rrect(c,x+1,y+1,s-2,s-2,s*.22,col,Math.max(2,s*.07))},
  reset(api){this.st={b:Array(N*N).fill(null),tray:[],drag:null,pop:[],combo:0,since:0,moves:0,shakeCell:0};this.fill();api.score=0},
  fill(){const st=this.st;st.tray=[0,1,2].map(i=>{const s=SHP[rndi(0,SHP.length-1)];return{s,c:pick(PC),slot:i,w:Math.max(...s.map(p=>p[0]))+1,h:Math.max(...s.map(p=>p[1]))+1}})},
  fits(s,ox,oy){const st=this.st;for(const[i,j]of s){const x=ox+i,y=oy+j;if(x<0||y<0||x>=N||y>=N||st.b[y*N+x])return false}return true},
  canAny(p){for(let y=0;y<N;y++)for(let x=0;x<N;x++)if(this.fits(p.s,x,y))return true;return false},
  pieceAt(x,y){const st=this.st;for(const p of st.tray){const cx=SLOTS[p.slot];if(Math.abs(x-cx)<66&&Math.abs(y-TRAYY)<70)return p}return null},
  down(x,y,api){const p=this.pieceAt(x,y);if(!p)return;this.st.drag={p,x,y};S.tap(1.2)},
  move(x,y){const d=this.st.drag;if(d){d.x=x;d.y=y}},
  target(d){const p=d.p,gx=d.x-p.w*CS/2,gy=d.y-90-p.h*CS/2;return[Math.round((gx-BX)/CS),Math.round((gy-BY)/CS)]},
  up(x,y,api){const st=this.st,d=st.drag;if(!d)return;st.drag=null;const[ox,oy]=this.target(d);
    if(!this.fits(d.p.s,ox,oy)){S.tone(300,.08,{type:'triangle',v:.15});return}
    for(const[i,j]of d.p.s)st.b[(oy+j)*N+ox+i]=d.p.c;api.score+=d.p.s.length;S.thud();S.pop(1.3);api.shake(2);
    st.tray=st.tray.filter(q=>q!==d.p);
    // 列判定
    const rows=[],cols=[];for(let k=0;k<N;k++){let r=true,cc=true;for(let m=0;m<N;m++){if(!st.b[k*N+m])r=false;if(!st.b[m*N+k])cc=false}if(r)rows.push(k);if(cc)cols.push(k)}
    const lines=rows.length+cols.length;
    if(lines){st.combo=st.since<=2&&st.moves>0?st.combo+1:1;st.since=0;api.combo=st.combo;const set=new Set();rows.forEach(r=>{for(let m=0;m<N;m++)set.add(r*N+m)});cols.forEach(cc=>{for(let m=0;m<N;m++)set.add(m*N+cc)});
      let pts=lines*lines*10*Math.max(1,st.combo);api.score+=pts;
      set.forEach(k=>{const x=BX+(k%N+.5)*CS,y=BY+(Math.floor(k/N)+.5)*CS;st.pop.push({x,y,c:st.b[k],t:0,d:(Math.abs(k%N-ox)+Math.abs(Math.floor(k/N)-oy))*.02});st.b[k]=null});
      setTimeout(()=>{S.perfect(1+Math.min(st.combo,10)*.05);for(let i=0;i<Math.min(lines,4);i++)S.pop(1.5+i*.2)},0);
      api.flash('#fff',.2+lines*.08);api.shake(4+lines*3);
      const msg=lines>=4?'すごすぎ！':lines===3?'すごい！':lines===2?'ダブル！':'いいね！';
      api.float(W/2,BY-30,msg+' +'+pts,{size:26+lines*4,c:lines>=3?'#f3c84b':'#fff'});if(st.combo>1)api.float(W/2,BY+N*CS/2,st.combo+' コンボ！',{size:40,c:'#f3c84b',life:1});
      if(st.b.every(v=>!v)){api.score+=300;api.float(W/2,BY+N*CS/2+50,'ぜんけし！ +300',{size:36,c:'#7fc6d8',life:1.2});S.fanfare();api.flash('#7fc6d8',.4)}}
    else{st.since++;if(st.since>2){st.combo=0;api.combo=0}}
    st.moves++;
    if(!st.tray.length)this.fill();
    if(!st.tray.some(p=>this.canAny(p))){st.over=true;setTimeout(()=>{S.bad();api.end()},500)}},
  update(dt){const st=this.st;for(const p of st.pop)p.t+=dt;st.pop=st.pop.filter(p=>p.t<p.d+.35)},
  overText:'おけない！',
  draw(c,api){const st=this.st;c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.fillStyle='#dfe6f0';for(let i=0;i<20;i++){c.beginPath();c.arc((i*71)%W,(i*137)%H,20+(i%3)*10,0,7);c.fill()}
    D.rrect(c,BX-10,BY-10,N*CS+20,N*CS+20,18,'#5a6378',4);
    for(let y=0;y<N;y++)for(let x=0;x<N;x++){const v=st.b[y*N+x];if(v)this.cell(c,BX+x*CS,BY+y*CS,CS,v);else{c.fillStyle='#4a5266';c.fillRect(BX+x*CS+3,BY+y*CS+3,CS-6,CS-6)}}
    // プレビュー＆消える予告
    const d=st.drag;if(d){const[ox,oy]=this.target(d);if(this.fits(d.p.s,ox,oy)){c.globalAlpha=.45;for(const[i,j]of d.p.s)this.cell(c,BX+(ox+i)*CS,BY+(oy+j)*CS,CS,d.p.c);c.globalAlpha=1;
      const tmp=st.b.slice();for(const[i,j]of d.p.s)tmp[(oy+j)*N+ox+i]=1;c.fillStyle='rgba(255,255,255,.35)';
      for(let k=0;k<N;k++){let r=true,cc=true;for(let m=0;m<N;m++){if(!tmp[k*N+m])r=false;if(!tmp[m*N+k])cc=false}if(r)c.fillRect(BX,BY+k*CS,N*CS,CS);if(cc)c.fillRect(BX+k*CS,BY,CS,N*CS)}}}
    for(const p of st.pop){const k=Math.max(0,p.t-p.d)/.35;if(k<=0){this.cell(c,p.x-CS/2,p.y-CS/2,CS,p.c);continue}const s=CS*(1+k*.5);c.globalAlpha=1-k;this.cell(c,p.x-s/2,p.y-s/2,s,p.c);c.globalAlpha=1}
    // トレイ
    D.rrect(c,20,TRAYY-70,W-40,140,22,'rgba(255,255,255,.6)',3);
    for(const p of st.tray){if(d&&d.p===p)continue;const s=CS*TS,cx=SLOTS[p.slot],ok=this.canAny(p);c.globalAlpha=ok?1:.35;for(const[i,j]of p.s)this.cell(c,cx-p.w*s/2+i*s,TRAYY-p.h*s/2+j*s,s,p.c);c.globalAlpha=1}
    if(d){const p=d.p,gx=d.x-p.w*CS/2,gy=d.y-90-p.h*CS/2;for(const[i,j]of p.s)this.cell(c,gx+i*CS,gy+j*CS,CS,p.c);D.face(c,gx+p.s[0][0]*CS+CS/2,gy+p.s[0][1]*CS+CS/2,CS*.7,'o')}
  },
  __bot(api){const st=this.st;if(st.over)return;for(const p of st.tray){for(let y=0;y<N;y++)for(let x=0;x<N;x++)if(this.fits(p.s,x,y)){const cx=SLOTS[p.slot];this.down(cx,TRAYY,api);const tx=BX+x*CS+p.w*CS/2,ty=BY+y*CS+p.h*CS/2+90;this.move(tx,ty);this.up(tx,ty,api);return}}},
};
