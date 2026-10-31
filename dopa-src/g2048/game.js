/* ぎゅっと2048：4x4 のスライド合体。大きい数ほど色が濃くなり、128 以上は顔がつく。 */
const N=4,BS=376,BX=(W-BS)/2,BY=250,GAP=10,CS=(BS-GAP*(N+1))/N;
const TC={2:'#fbf2e4',4:'#f7e3c6',8:'#f6c08a',16:'#f2a46e',32:'#f08a6a',64:'#e8705a',128:'#f2d36b',256:'#ecc95a',512:'#9cc86a',1024:'#7fb2e0',2048:'#c49ae0',4096:'#e0789a'};
const GAME={...META,sprites:['icon','tile'],unit:'点',fullBleed:true,comboHud:false,
  bgm:{bpm:110,root:60,scale:'major',prog:[1,6,4,5],seed:20,lead:'triangle',drums:'pop',density:.5},
  ranks:[[0,'ちいさな2'],[1000,'64のかべ'],[3000,'256まで来た'],[7000,'512の使い手'],[15000,'1024の達人'],[25000,'2048マスター']],
  shareText:(v,f,)=>`ぎゅっと2048で ${f}点！`,
  icon(c,x,y,s){const t=s*.3;this.tile(c,x-t*.55,y-t*.55,t,8);this.tile(c,x+t*.55,y-t*.55,t,8);this.tile(c,x,y+t*.6,t*1.2,128)},
  tile(c,x,y,s,v,sc=1){const w=Math.max(2,s*sc);D.rrect(c,x-w/2,y-w/2,w,w,w*.18,TC[v]||'#5b4d45',Math.max(2.5,w*.05));
    const fs=w*(v<100?.42:v<1000?.34:.27);if(v>=128){D.face(c,x,y+w*.18,w*.45);D.text(c,v,x,y-w*.12,fs*.85,v>=1024?'#fffdf8':'#5b4d45')}else D.text(c,v,x,y,fs,v>=8?'#fffdf8':'#5b4d45','center',v>=8?OL:null,4)},
  cell(r,c){return[BX+GAP+c*(CS+GAP)+CS/2,BY+GAP+r*(CS+GAP)+CS/2]},
  reset(api){this.st={g:[],anim:0,best:2,won:false,id:0};for(let r=0;r<N;r++)this.st.g.push(new Array(N).fill(null));this.add();this.add();api.score=0},
  add(){const st=this.st,e=[];for(let r=0;r<N;r++)for(let c=0;c<N;c++)if(!st.g[r][c])e.push([r,c]);if(!e.length)return;const[r,c]=pick(e);st.g[r][c]={v:Math.random()<.9?2:4,id:st.id++,fr:r,fc:c,born:0,pop:0}},
  go(d,api){const st=this.st;if(st.anim>0)return;const dr={U:-1,D:1,L:0,R:0}[d],dc={L:-1,R:1,U:0,D:0}[d];let moved=false,gain=0,merges=0,maxNew=0;
    for(let r=0;r<N;r++)for(let c=0;c<N;c++)if(st.g[r][c]){st.g[r][c].fr=r;st.g[r][c].fc=c;st.g[r][c].merged=false;st.g[r][c].pop=0;st.g[r][c].born=1}
    const order=[...Array(N).keys()];const rs=dr>0?order.slice().reverse():order,cs=dc>0?order.slice().reverse():order;st.ghost=[];
    for(const r of rs)for(const c of cs){const t=st.g[r][c];if(!t)continue;let nr=r,nc=c;
      while(true){const tr=nr+dr,tc=nc+dc;if(tr<0||tr>=N||tc<0||tc>=N)break;const o=st.g[tr][tc];if(!o){nr=tr;nc=tc;continue}
        if(o.v===t.v&&!o.merged){st.g[r][c]=null;o.v*=2;o.merged=true;o.pop=1;st.ghost.push({v:t.v,fr:r,fc:c,tr,tc});gain+=o.v;merges++;maxNew=Math.max(maxNew,o.v);moved=true;nr=null}break}
      if(nr===null)continue;if(nr!==r||nc!==c){st.g[nr][nc]=t;st.g[r][c]=null;moved=true}}
    if(!moved){S.tap(.5);return}
    st.anim=.12;S.swish();api.add(gain);
    if(merges){api.combo=merges;setTimeout(()=>{S.pop(1+Math.log2(maxNew)*.04);if(merges>=2)S.combo(merges*3)},110);
      if(maxNew>st.best){st.best=maxNew;if(maxNew>=128){setTimeout(()=>{S.perfect();api.flash('#fff',.35);api.float(W/2,170,maxNew+' できた！',{size:32,c:'#f3c84b'})},120)}}
      if(maxNew>=2048&&!st.won){st.won=true;setTimeout(()=>{S.fanfare();for(let i=0;i<6;i++)api.burst(rnd(60,W-60),rnd(250,600),{c:['#c49ae0','#f4d66d','#fff'],n:20,shape:'star',sp:300})},150)}}
    st.pending=true},
  down(x,y){this.st.sw={x,y,used:false}},
  move(x,y,api){const s=this.st.sw;if(!s||s.used)return;const dx=x-s.x,dy=y-s.y;if(Math.hypot(dx,dy)<24)return;s.used=true;this.go(Math.abs(dx)>Math.abs(dy)?(dx>0?'R':'L'):(dy>0?'D':'U'),api)},
  up(){this.st.sw=null},
  key(k,api){const m={ArrowLeft:'L',ArrowRight:'R',ArrowUp:'U',ArrowDown:'D'}[k];if(m)this.go(m,api)},
  canMove(){const g=this.st.g;for(let r=0;r<N;r++)for(let c=0;c<N;c++){if(!g[r][c])return true;if(c<N-1&&g[r][c+1]&&g[r][c+1].v===g[r][c].v)return true;if(r<N-1&&g[r+1][c]&&g[r+1][c].v===g[r][c].v)return true}return false},
  update(dt,api){const st=this.st;if(st.anim>0){st.anim-=dt;if(st.anim<=0){st.ghost=[];if(st.pending){st.pending=false;this.add();for(const row of st.g)for(const t of row)if(t){t.fr=null}if(!this.canMove()){S.bad();api.end()}}}}
    for(const row of st.g)for(const t of row)if(t){t.born=Math.min(1,t.born+dt*7);if(st.anim<=0)t.pop=Math.max(0,t.pop-dt*5)}},
  overText:'うごけない！',
  drawHud(c,api){D.rrect(c,90,20,240,56,28,'#fffdf8',3.5);D.text(c,api.score.toLocaleString()+'点',W/2,48,26,'#5b4d45');const st=this.st;D.text(c,'さいこう：'+st.best,W/2,104,17,'#8e8077','center','#fffdf8',4)},
  draw(c,api){const st=this.st;c.fillStyle='#f5ead9';c.fillRect(0,api.top,W,api.bottom-api.top);D.rrect(c,BX,BY,BS,BS,22,'#cbb59a',4);
    for(let r=0;r<N;r++)for(let cc=0;cc<N;cc++){const[x,y]=this.cell(r,cc);D.rrect(c,x-CS/2,y-CS/2,CS,CS,CS*.18,'#dccab2',0)}
    const k=st.anim>0?1-st.anim/.12:1;
    for(const g of st.ghost||[]){const[x0,y0]=this.cell(g.fr,g.fc),[x1,y1]=this.cell(g.tr,g.tc);this.tile(c,lerp(x0,x1,k),lerp(y0,y1,k),CS,g.v)}
    for(let r=0;r<N;r++)for(let cc=0;cc<N;cc++){const t=st.g[r][cc];if(!t)continue;let[x,y]=this.cell(r,cc);if(st.anim>0&&t.fr!=null){const[x0,y0]=this.cell(t.fr,t.fc);x=lerp(x0,x,k);y=lerp(y0,y,k)}
      const sc=(t.born<1?ease.outBack(t.born):1)*(1+(st.anim>0?0:t.pop*.15));this.tile(c,x,y,CS,st.anim>0&&t.merged?t.v/2:t.v,sc)}
    D.text(c,'スワイプでうごかす',W/2,BY+BS+40,16,'#a58f78')},
  __bot(api){const st=this.st;if(st.anim>0)return;const prefs=['D','L','R','U'];for(const d of prefs){const before=JSON.stringify(st.g.map(r=>r.map(t=>t&&t.v)));this.go(d,api);if(st.anim>0)return}},
};
