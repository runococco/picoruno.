/* くるくるパイプ：各マスは接続ビット（上1 右2 下4 左8）。タップで右回転。経路探索で左→右がつながったらクリア。 */
const ROT=v=>((v<<1)&15)|((v>>3)&1);
const GAME={...META,sprites:['icon','tile'],unit:'面',time:90,hudUnit:true,fullBleed:true,comboHud:false,
  bgm:{bpm:108,root:60,scale:'major',prog:[1,4,6,5],seed:53,lead:'triangle',drums:'pop',density:.5},
  ranks:[[0,'水もれ'],[2,'パイプ見習い'],[4,'くるくる上手'],[7,'配管の達人'],[10,'水道の神'],[14,'パイプマスター']],
  shareText:(v,f)=>`くるくるパイプで ${f}面 つなげた！`,
  icon(c,x,y,s){const g=s*.22;[[0,0,6],[1,0,10],[2,0,12],[0,1,3],[2,1,5],[0,2,2],[1,2,10],[2,2,9]].forEach(([i,j,v])=>this.tile(c,x-g+i*g,y-g+j*g,g,v,i===0||j===2))},
  tile(c,x,y,s,v,wet){D.rrect(c,x-s/2,y-s/2,s,s,s*.12,'#fbf7f0',2.5);const w=s*.3,col=wet?'#7fc3e0':'#c9bfb4';
    c.lineCap='butt';c.strokeStyle=OL;c.lineWidth=w+5;this.arms(c,x,y,s,v);c.strokeStyle=col;c.lineWidth=w;this.arms(c,x,y,s,v);D.circle(c,x,y,w*.72,col,3)},
  arms(c,x,y,s,v){c.beginPath();if(v&1){c.moveTo(x,y);c.lineTo(x,y-s/2)}if(v&2){c.moveTo(x,y);c.lineTo(x+s/2,y)}if(v&4){c.moveTo(x,y);c.lineTo(x,y+s/2)}if(v&8){c.moveTo(x,y);c.lineTo(x-s/2,y)}c.stroke()},
  gen(){const st=this.st;const n=Math.min(7,4+Math.floor(st.lv/2));const g=[];for(let r=0;r<n;r++){g.push(new Array(n).fill(0))}
    // ランダムウォークで左端の入口から右端の出口まで道を掘る
    let r=rndi(0,n-1),c=0;let path=[[r,c]];g[r][c]|=8;let guard=0;while(c<n-1&&guard++<400){const opts=[];if(c<n-1)opts.push([0,1],[0,1]);if(r>0&&!path.some(p=>p[0]===r-1&&p[1]===c))opts.push([-1,0]);if(r<n-1&&!path.some(p=>p[0]===r+1&&p[1]===c))opts.push([1,0]);const[dr,dc]=pick(opts);const nr=r+dr,nc=c+dc;
      if(path.some(p=>p[0]===nr&&p[1]===nc))continue;g[r][c]|=dr===-1?1:dr===1?4:2;g[nr][nc]|=dr===-1?4:dr===1?1:8;r=nr;c=nc;path.push([r,c])}
    g[r][c]|=2;st.exit=r;st.entry=path[0][0];
    for(let rr=0;rr<n;rr++)for(let cc=0;cc<n;cc++){if(!g[rr][cc])g[rr][cc]=pick([3,6,12,9,5,10,7,14]);const k=rndi(0,3);for(let i=0;i<k;i++)g[rr][cc]=ROT(g[rr][cc])}
    st.g=g;st.n=n;st.cs=Math.min(80,(W-50)/n);st.ox=(W-st.cs*n)/2;st.oy=170+((H-260)-st.cs*n)/2;st.wet=this.flow();if(st.wet.ok)this.gen()},
  flow(){const st=this.st,g=st.g,n=st.n;const seen=new Set();const q=[];if(g[st.entry][0]&8){q.push([st.entry,0]);seen.add(st.entry+',0')}let ok=false;
    while(q.length){const[r,c]=q.shift();const v=g[r][c];if(c===n-1&&r===st.exit&&(v&2))ok=true;const nb=[[r-1,c,1,4],[r,c+1,2,8],[r+1,c,4,1],[r,c-1,8,2]];for(const[nr,nc,bit,back]of nb){if(!(v&bit)||nr<0||nc<0||nr>=n||nc>=n)continue;if(!(g[nr][nc]&back))continue;const k=nr+','+nc;if(!seen.has(k)){seen.add(k);q.push([nr,nc])}}}
    return{seen,ok}},
  reset(api){this.st={lv:0,anim:{},clearT:0};this.gen();api.score=0},
  down(x,y,api){const st=this.st;if(st.clearT>0)return;const c=Math.floor((x-st.ox)/st.cs),r=Math.floor((y-st.oy)/st.cs);if(r<0||c<0||r>=st.n||c>=st.n)return;
    st.g[r][c]=ROT(st.g[r][c]);st.anim[r+','+c]=.18;S.tap(1.3);st.wet=this.flow();
    if(st.wet.ok){st.clearT=1.2;api.add(1);api.timeLeft+=12;S.fanfare();S.noise(.8,{v:.3,f:1200,to:600});api.flash('#fff',.3);api.float(W/2,140,'つながった！ +12秒',{size:28,c:'#f3c84b'})}else if(st.wet.seen.size>1)S.tone(500+st.wet.seen.size*40,.06,{type:'sine',v:.1})},
  update(dt,api){const st=this.st;for(const k in st.anim)st.anim[k]=Math.max(0,st.anim[k]-dt);if(st.clearT>0){st.clearT-=dt;if(st.clearT<=0){st.lv++;this.gen()}}},
  draw(c,api){const st=this.st,cs=st.cs;c.fillStyle='#e3eef5';c.fillRect(0,api.top,W,api.bottom-api.top);
    D.text(c,'Lv.'+(st.lv+1),W/2,130,20,'#5b4d45');
    D.rrect(c,st.ox-10,st.oy-10,cs*st.n+20,cs*st.n+20,16,'#6b8aa0',4);
    const ey=st.oy+(st.entry+.5)*cs,xy=st.oy+(st.exit+.5)*cs;
    D.rrect(c,st.ox-40,ey-18,36,36,8,'#7fc3e0');D.rrect(c,st.ox-34,ey-40,10,28,4,'#8a8392');
    D.rrect(c,st.ox+cs*st.n+6,xy-10,34,40,6,st.clearT>0?'#7fc3e0':'#c9a274');
    for(let r=0;r<st.n;r++)for(let cc=0;cc<st.n;cc++){const x=st.ox+(cc+.5)*cs,y=st.oy+(r+.5)*cs,a=st.anim[r+','+cc]||0;c.save();c.translate(x,y);c.rotate(-a/.18*Math.PI/2);this.tile(c,0,0,cs-4,st.g[r][cc],st.wet.seen.has(r+','+cc));c.restore()}
    if(st.clearT>0){c.globalAlpha=.3;c.fillStyle='#7fc3e0';c.fillRect(st.ox,st.oy,cs*st.n,cs*st.n);c.globalAlpha=1}},
  __bot(api){const st=this.st;if(st.clearT>0)return;// 水が届いてる最前線のとなりを回す
    const cand=[];for(const k of st.wet.seen){const[r,c]=k.split(',').map(Number);for(const[nr,nc]of[[r,c+1],[r-1,c],[r+1,c]]){if(nr>=0&&nc<st.n&&nr<st.n&&!st.wet.seen.has(nr+','+nc))cand.push([nr,nc])}}
    let best=null;for(const[r,c]of cand){const v=st.g[r][c];let vv=v;for(let i=1;i<4&&!best;i++){vv=ROT(vv);st.g[r][c]=vv;if(this.flow().seen.has(r+','+c))best=[r,c]}st.g[r][c]=v;if(best)break}
    if(!best)best=[rndi(0,st.n-1),rndi(0,st.n-1)];this.down(st.ox+(best[1]+.5)*st.cs,st.oy+(best[0]+.5)*st.cs,api)},
};
