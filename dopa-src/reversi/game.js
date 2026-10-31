/* ぱたぱたリバーシ：6x6。スコアは勝利数。相手は3段階（ランダム→多く取る→角を優先）。 */
const N=6,BS=360,BX=(W-BS)/2,BY=200,CS=BS/N;
const GAME={...META,sprites:['icon','disc'],unit:'勝',hudUnit:true,fullBleed:true,comboHud:false,
  bgm:{bpm:100,root:60,scale:'major',prog:[1,6,2,5],seed:29,lead:'triangle',drums:'pop',density:.45},
  ranks:[[0,'ぱたぱた見習い'],[1,'1勝！'],[2,'リバーシ上手'],[3,'3人ぬき'],[5,'リバーシ名人'],[8,'ぱたぱたの神']],
  shareText:(v,f)=>`ぱたぱたリバーシで ${f}勝！`,
  icon(c,x,y,s){const g=s*.22;D.rrect(c,x-g*2,y-g*2,g*4,g*4,g*.3,'#7fa874',4);[[0,0,1],[1,0,1],[2,0,2],[0,1,2],[1,1,1],[2,1,1],[1,2,2],[2,2,2]].forEach(([i,j,k])=>this.disc(c,x-g*1.5+i*g,y-g*1.5+j*g,g*.4,k,1))},
  disc(c,x,y,r,k,flip){c.save();c.translate(x,y);c.scale(Math.max(.08,Math.abs(flip)),1);D.circle(c,0,0,r,k===1?'#f2a5c0':'#5b5560');if(k===1)D.face(c,0,r*.05,r*1.1);else{c.fillStyle='#8a8392';c.beginPath();c.arc(-r*.3,0,r*.12,0,7);c.arc(r*.3,0,r*.12,0,7);c.fill()}c.restore()},
  reset(api){this.st={lv:0,wins:0};this.newGame();api.score=0},
  newGame(){const st=this.st;st.b=[];for(let r=0;r<N;r++)st.b.push(new Array(N).fill(0));st.b[2][2]=2;st.b[3][3]=2;st.b[2][3]=1;st.b[3][2]=1;st.turn=1;st.flip={};st.wait=0;st.over=0;st.pass=0},
  flips(b,r,c,k){if(b[r][c])return[];const out=[];for(const[dr,dc]of[[-1,0],[1,0],[0,-1],[0,1],[-1,-1],[-1,1],[1,-1],[1,1]]){let rr=r+dr,cc=c+dc,line=[];while(rr>=0&&cc>=0&&rr<N&&cc<N&&b[rr][cc]===3-k){line.push([rr,cc]);rr+=dr;cc+=dc}if(line.length&&rr>=0&&cc>=0&&rr<N&&cc<N&&b[rr][cc]===k)out.push(...line)}return out},
  moves(k){const st=this.st,out=[];for(let r=0;r<N;r++)for(let c=0;c<N;c++){const f=this.flips(st.b,r,c,k);if(f.length)out.push({r,c,f})}return out},
  place(m,k,api){const st=this.st;st.b[m.r][m.c]=k;m.f.forEach(([r,c],i)=>{st.b[r][c]=k;st.flip[r+','+c]=.3+i*.06});S.thud();for(let i=0;i<m.f.length;i++)S.tone(500+i*70,.07,{type:'triangle',v:.14,at:.08+i*.07});
    if(k===1&&m.f.length>=4){api.float(BX+(m.c+.5)*CS,BY+(m.r+.5)*CS-30,m.f.length+'枚！',{size:24,c:'#f3c84b'})}
    st.turn=3-k;st.wait=.5+m.f.length*.06;if(!this.moves(st.turn).length){if(!this.moves(k).length){this.finish(api)}else{st.turn=k;api.float(W/2,BY-40,(st.turn===1?'相手':'あなた')+'はパス',{size:20})}}},
  finish(api){const st=this.st;st.over=1.8;let me=0,cp=0;for(const row of st.b)for(const v of row){if(v===1)me++;if(v===2)cp++}st.resMe=me;st.resCp=cp;
    if(me>cp){st.wins++;api.score=st.wins;st.lv=Math.min(2,st.lv+1);S.fanfare();api.flash('#fff',.4);api.float(W/2,BY+BS/2,'かち！ '+me+'-'+cp,{size:40,c:'#f3c84b',life:1.6});for(let i=0;i<4;i++)api.burst(rnd(60,W-60),rnd(250,550),{c:['#f2a5c0','#fff','#f4d66d'],n:16,shape:'star'})}
    else{S.bad();api.float(W/2,BY+BS/2,(me===cp?'ひきわけ ':'まけ… ')+me+'-'+cp,{size:36,life:1.6});st.lost=me<cp}},
  down(x,y,api){const st=this.st;if(st.turn!==1||st.wait>0||st.over)return;const c=Math.floor((x-BX)/CS),r=Math.floor((y-BY)/CS);if(r<0||c<0||r>=N||c>=N)return;const f=this.flips(st.b,r,c,1);if(!f.length){S.tap(.5);return}this.place({r,c,f},1,api)},
  cpu(api){const st=this.st;const ms=this.moves(2);if(!ms.length)return;let m;if(st.lv===0)m=pick(ms);else{const corner=ms.filter(q=>(q.r===0||q.r===N-1)&&(q.c===0||q.c===N-1));if(st.lv===2&&corner.length)m=pick(corner);else{ms.sort((a,b)=>b.f.length-a.f.length);m=ms[0]}}this.place(m,2,api)},
  update(dt,api){const st=this.st;for(const k in st.flip)st.flip[k]=Math.max(0,st.flip[k]-dt);if(st.over){st.over-=dt;if(st.over<=0){if(st.lost){api.end();return}this.newGame()}return}
    if(st.wait>0){st.wait-=dt;if(st.wait<=0&&st.turn===2)this.cpu(api)}},
  drawHud(c,api){const st=this.st;let me=0,cp=0;for(const row of st.b)for(const v of row){if(v===1)me++;if(v===2)cp++}D.rrect(c,60,20,300,56,28,'#fffdf8',3.5);this.disc(c,100,48,14,1,1);D.text(c,String(me),135,48,24,'#5b4d45');D.text(c,['よわい','ふつう','つよい'][st.lv]+'　'+st.wins+'勝',W/2+10,48,17,'#5b4d45');D.text(c,String(cp),290,48,24,'#5b4d45');this.disc(c,325,48,14,2,1)},
  draw(c,api){const st=this.st;c.fillStyle='#e4efd8';c.fillRect(0,api.top,W,api.bottom-api.top);D.rrect(c,BX-10,BY-10,BS+20,BS+20,16,'#7fa874',4);
    for(let r=0;r<N;r++)for(let cc=0;cc<N;cc++){c.fillStyle=(r+cc)%2?'#8fbf84':'#86b57b';c.fillRect(BX+cc*CS,BY+r*CS,CS,CS)}
    c.strokeStyle='#5f8a56';c.lineWidth=2;for(let i=0;i<=N;i++){c.beginPath();c.moveTo(BX+i*CS,BY);c.lineTo(BX+i*CS,BY+BS);c.moveTo(BX,BY+i*CS);c.lineTo(BX+BS,BY+i*CS);c.stroke()}
    if(st.turn===1&&!st.wait&&!st.over)for(const m of this.moves(1)){c.globalAlpha=.5;D.circle(c,BX+(m.c+.5)*CS,BY+(m.r+.5)*CS,7,'#fffdf8',2);c.globalAlpha=1}
    for(let r=0;r<N;r++)for(let cc=0;cc<N;cc++){const v=st.b[r][cc];if(!v)continue;const f=st.flip[r+','+cc]||0;let fl=1,k=v;if(f>0){fl=Math.cos(Math.min(1,f/.3)*Math.PI);if(f>.15)k=3-v}this.disc(c,BX+(cc+.5)*CS,BY+(r+.5)*CS,CS*.4,k,fl)}
    D.text(c,st.over?'':st.turn===1?'あなたの番':'相手が考え中…',W/2,BY+BS+40,20,'#5b4d45')},
  __bot(api){const st=this.st;if(st.turn!==1||st.wait>0||st.over)return;const ms=this.moves(1);if(ms.length){ms.sort((a,b)=>b.f.length-a.f.length);this.place(ms[0],1,api)}},
};
