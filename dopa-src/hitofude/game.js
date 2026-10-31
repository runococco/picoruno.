/* ひとふでがき：グリッド上のハミルトン路。生成は蛇行経路＋ランダム切り抜きで必ず解ける。 */
const GAME={...META,sprites:['icon'],unit:'問',time:90,hudUnit:true,fullBleed:true,comboHud:false,
  bgm:{bpm:96,root:62,scale:'major',prog:[1,6,4,5],seed:46,lead:'triangle',drums:'pop',density:.45},
  ranks:[[0,'線がきれた'],[2,'ひとふで見習い'],[4,'なぞり上手'],[7,'ひとふでの達人'],[10,'線の魔術師'],[14,'ひとふでの神']],
  shareText:(v,f)=>`ひとふでがきで ${f}問 とけた！`,
  icon(c,x,y,s){const g=s*.22;c.lineCap='round';c.lineJoin='round';c.lineWidth=g*.5;c.strokeStyle=OL;const P=[[0,0],[1,0],[2,0],[2,1],[1,1],[0,1],[0,2],[1,2],[2,2]];c.beginPath();P.forEach(([i,j],k)=>k?c.lineTo(x-g+i*g,y-g+j*g):c.moveTo(x-g+i*g,y-g+j*g));c.stroke();c.lineWidth=g*.32;c.strokeStyle='#e2645a';c.stroke();D.circle(c,x-g,y-g,g*.28,'#f2c84b',3)},
  gen(){const st=this.st;const n=Math.min(6,3+Math.floor(st.lv/2)),m=Math.min(7,4+Math.floor(st.lv/2));
    // 蛇行で全マスの経路を作り、端から何マスか削る
    let path=[];for(let r=0;r<m;r++){for(let i=0;i<n;i++){const c=r%2?n-1-i:i;path.push([r,c])}}
    if(Math.random()<.5)path=path.map(([r,c])=>[c,r]);
    const cut=rndi(0,Math.floor(path.length*.3));path=path.slice(cut);if(Math.random()<.5)path.reverse();
    const cells=new Set(path.map(p=>p.join(',')));st.cells=cells;st.start=path[0];const rs=path.map(p=>p[0]),cs=path.map(p=>p[1]);st.r0=Math.min(...rs);st.r1=Math.max(...rs);st.c0=Math.min(...cs);st.c1=Math.max(...cs);
    const rows=st.r1-st.r0+1,cols=st.c1-st.c0+1;st.cs=Math.min(78,(W-60)/cols,(H-280)/rows);st.ox=(W-st.cs*cols)/2;st.oy=170+((H-260)-st.cs*rows)/2;st.line=[];st.drag=false;st.clearT=0},
  reset(api){this.st={lv:0};this.gen();api.score=0},
  pos(r,c){const st=this.st;return[st.ox+(c-st.c0+.5)*st.cs,st.oy+(r-st.r0+.5)*st.cs]},
  cellAt(x,y){const st=this.st;const c=Math.floor((x-st.ox)/st.cs)+st.c0,r=Math.floor((y-st.oy)/st.cs)+st.r0;return st.cells.has(r+','+c)?[r,c]:null},
  down(x,y,api){const st=this.st;if(st.clearT>0)return;const cl=this.cellAt(x,y);if(cl&&cl[0]===st.start[0]&&cl[1]===st.start[1]){st.line=[cl];st.drag=true;S.tap()}else{st.line=[]}},
  move(x,y,api){const st=this.st;if(!st.drag||st.clearT>0)return;const cl=this.cellAt(x,y);if(!cl)return;const last=st.line[st.line.length-1];if(cl[0]===last[0]&&cl[1]===last[1])return;
    if(Math.abs(cl[0]-last[0])+Math.abs(cl[1]-last[1])!==1)return;
    if(st.line.length>1){const prev=st.line[st.line.length-2];if(prev[0]===cl[0]&&prev[1]===cl[1]){st.line.pop();S.tap(.6);return}}
    if(st.line.some(p=>p[0]===cl[0]&&p[1]===cl[1]))return;st.line.push(cl);S.tone(400+st.line.length*40,.05,{type:'sine',v:.12});
    if(st.line.length===st.cells.size){st.clearT=1;st.drag=false;api.add(1);api.timeLeft+=10;S.fanfare();api.flash('#fff',.3);api.float(W/2,140,'クリア！ +10秒',{size:28,c:'#f3c84b'});const[px,py]=this.pos(cl[0],cl[1]);api.burst(px,py,{c:['#e2645a','#f4d66d','#fff'],n:18,shape:'star',sp:220})}},
  up(){const st=this.st;if(st.drag&&st.clearT<=0){st.drag=false;if(st.line.length>1){S.bad();st.line=[]}}},
  update(dt,api){const st=this.st;if(st.clearT>0){st.clearT-=dt;if(st.clearT<=0){st.lv++;this.gen()}}},
  draw(c,api){const st=this.st;c.fillStyle='#f3eadb';c.fillRect(0,api.top,W,api.bottom-api.top);D.text(c,'Lv.'+(st.lv+1),W/2,130,20,'#5b4d45');
    for(const k of st.cells){const[r,cc]=k.split(',').map(Number);const[x,y]=this.pos(r,cc);D.rrect(c,x-st.cs/2+3,y-st.cs/2+3,st.cs-6,st.cs-6,10,'#fffdf8',3);}
    if(st.line.length){c.lineCap='round';c.lineJoin='round';c.lineWidth=st.cs*.4;c.strokeStyle=OL;c.beginPath();st.line.forEach((p,i)=>{const[x,y]=this.pos(p[0],p[1]);i?c.lineTo(x,y):c.moveTo(x,y)});c.stroke();c.lineWidth=st.cs*.28;c.strokeStyle=st.clearT>0?'#f4d66d':'#e2645a';c.stroke()}
    const[sx,sy]=this.pos(st.start[0],st.start[1]);D.circle(c,sx,sy,st.cs*.2,'#f2c84b',3);if(!st.line.length)D.text(c,'ここから',sx,sy-st.cs*.45,13,'#5b4d45');
    if(st.line.length){const[lx,ly]=this.pos(...st.line[st.line.length-1]);D.circle(c,lx,ly,st.cs*.16,'#fbf7f0',3)}},
  __bot(api){const st=this.st;if(st.clearT>0)return;if(!st.drag){const[x,y]=this.pos(...st.start);this.down(x,y,api);return}
    const last=st.line[st.line.length-1];const nb=[[1,0],[-1,0],[0,1],[0,-1]].map(([a,b])=>[last[0]+a,last[1]+b]).filter(p=>st.cells.has(p.join(','))&&!st.line.some(q=>q[0]===p[0]&&q[1]===p[1]));
    if(!nb.length){st.drag=false;st.line=[];return}const p=pick(nb);const[x,y]=this.pos(p[0],p[1]);this.move(x,y,api)},
};
