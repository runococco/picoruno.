/* ふんわりわなげ：スワイプ速度→飛距離。棒の位置と着地点で判定。 */
const N=10;
const GAME={...META,sprites:['icon','ring','peg'],unit:'点',fullBleed:true,
  bgm:{bpm:108,root:64,scale:'major',prog:[1,4,5,1],seed:53,lead:'triangle',drums:'light',density:.45},
  ranks:[[0,'カラカラ'],[200,'わなげ見習い'],[500,'かけ上手'],[800,'わなげの達人'],[1100,'えんにちの主'],[1400,'伝説の輪']],
  shareText:(v,f)=>`ふんわりわなげで ${f}点！`,
  icon(c,x,y,s){this.peg(c,x,y+s*.35,s*.5,'#e2645a');this.ring(c,x,y+s*.2,s*.3,.4,'#7fb2e0');this.ring(c,x-s*.3,y-s*.25,s*.22,.5,'#f2c84b')},
  peg(c,x,y,h,col){D.ellipse(c,x,y,28,10,'#d9c7a3');D.rrect(c,x-7,y-h,14,h,5,col);D.circle(c,x,y-h,9,col)},
  ring(c,x,y,r,sq,col){c.lineWidth=3;c.strokeStyle=OL;c.beginPath();c.ellipse(x,y,r,r*sq,0,0,Math.PI*2);c.stroke();c.lineWidth=r*.3;c.strokeStyle=col;c.beginPath();c.ellipse(x,y,r*.85,r*.85*sq,0,0,Math.PI*2);c.stroke();c.lineWidth=3;c.strokeStyle=OL;c.beginPath();c.ellipse(x,y,r*.7,r*.7*sq,0,0,Math.PI*2);c.stroke()},
  reset(api){this.st={n:0,pegs:[],r:null,wait:0,sw:null,t:0};api.score=0;this.layout()},
  layout(){const st=this.st;st.pegs=[];const rows=[[590,1,60,'#9cc86a'],[490,2,80,'#7fb2e0'],[390,3,110,'#e2645a'],[290,4,150,'#c49ae0']];const gi=rndi(0,9);let k=0;
    for(const[y,cnt,pts,col]of rows){const xs=cnt===1?[W/2]:cnt===2?[W/2-70,W/2+70]:cnt===3?[W/2-110,W/2,W/2+110]:[W/2-135,W/2-45,W/2+45,W/2+135];for(const x of xs){const gold=k===gi;st.pegs.push({x:x+rnd(-10,10),y,pts:gold?300:pts,col:gold?'#f2c84b':col,gold});k++}}},
  down(x,y){const st=this.st;if(st.r||st.wait>0||st.n>=N)return;st.sw={x,y,t:performance.now()}},
  up(x,y,api){const st=this.st,s=st.sw;st.sw=null;if(!s||st.r||st.wait>0)return;const dx=x-s.x,dy=y-s.y;if(dy>-25)return;const dt=Math.max(60,performance.now()-s.t);const v=clamp(-dy/dt*1000,250,1600);this.throwR(v,dx/Math.max(40,-dy),api)},
  throwR(v,drift,api){const st=this.st;st.n++;const dist=clamp(v*.3,60,420);st.r={x:W/2,y:650,sx:W/2,sy:650,ty:650-dist,tx:W/2+drift*dist*.6,k:0,col:pick(['#7fb2e0','#f2c84b','#e2645a','#9cc86a'])};S.whoosh()},
  update(dt,api){const st=this.st;st.t+=dt;if(st.wait>0){st.wait-=dt;if(st.wait<=0){st.r=null;if(st.n>=N)api.end();else if(st.n%5===0)this.layout()}return}
    const r=st.r;if(!r)return;r.k=Math.min(1,r.k+dt*1.3);const k=r.k;r.x=r.sx+(r.tx-r.sx)*k;r.y=r.sy+(r.ty-r.sy)*k;r.h=Math.sin(k*Math.PI)*140;
    if(k>=1){const p=st.pegs.find(p=>Math.abs(p.x-r.x)<22&&Math.abs(p.y-r.y)<18);let pts=0,txt='';if(p){pts=p.pts;api.combo++;pts+=Math.min(api.combo,5)*10;txt=(p.gold?'大当たり！':'カラン！')+' +'+pts;api.add(pts);r.x=p.x;r.y=p.y;S.clink();S.good();api.burst(p.x,p.y-40,{c:[p.col,'#fff'],n:12,sp:200,shape:'s'});if(p.gold){S.fanfare();api.flash('#fff6c8',.3)}}
      else{txt='はずれ…';api.combo=0;S.thud()}api.float(W/2,200,txt,{size:pts>=300?34:26,c:pts?'#f2a24a':'#5b4d45'});st.wait=1}},
  draw(c,api){const st=this.st;c.fillStyle='#fbf1dc';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#efe0bf';c.fillRect(0,250,W,api.bottom-250);c.fillStyle='#e3cfa3';for(let y=270;y<api.bottom;y+=40)c.fillRect(0,y,W,2);
    const ps=st.pegs.slice().sort((a,b)=>a.y-b.y);for(const p of ps){this.peg(c,p.x,p.y,42,p.col);D.text(c,p.pts,p.x,p.y+24,12,'#5b4d45')}
    const r=st.r;if(r){if(r.k<1){D.ellipse(c,r.x,r.y,24,10,'rgba(90,77,69,.15)',0);this.ring(c,r.x,r.y-r.h,30-r.k*6,.45,r.col)}else this.ring(c,r.x,r.y-4,26,.4,r.col)}
    else if(st.n<N)this.ring(c,W/2,650,30,.5,'#7fb2e0');
    for(let i=0;i<N;i++)D.circle(c,W/2-(N-1)*11+i*22,150,7,i<st.n?'#f2a24a':'#fff',2.5);
    if(api.state==='play'&&st.n===0)D.text(c,'上にスワイプ！',W/2,600,22,'#5b4d45')},
  __bot(api){const st=this.st;if(st.r||st.wait>0||st.n>=N)return;const p=pick(st.pegs);const dist=650-p.y;this.throwR(dist/.3,(p.x-W/2)/(dist*.6),api)},
};
