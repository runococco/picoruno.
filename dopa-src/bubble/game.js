/* あわあわバブル：六角配置のバブルシューター。3つ以上でわれ、つながってないあわは落ちる。顔はつけない（細かい顔がならぶのをさける）。 */
const COLS=['#f08a8a','#f2c84b','#8fc46a','#7fb2e0','#c49ae0','#f2a5c0'],R=19,NC=10,X0=W/2-NC*R+R/2-R/2,SY=170,RH=R*Math.sqrt(3),LINE=590,SX=W/2,SYY=640;
const GAME={...META,sprites:['icon','bub','shooter'],unit:'点',fullBleed:true,
  bgm:{bpm:120,root:60,scale:'major',prog:[1,6,4,5],seed:76,lead:'triangle',drums:'pop',density:.55},
  ranks:[[0,'あわ見習い'],[1000,'パチパチ係'],[3000,'あわあわ上手'],[6000,'バブル職人'],[10000,'あわの魔術師'],[16000,'バブルの神']],
  shareText:(v,f)=>`あわあわバブルで ${f}点！`,
  icon(c,x,y,s){const r=s*.12;[[0,0,0],[1,0,1],[2,0,0],[.5,1,2],[1.5,1,0]].forEach(([i,j,k])=>this.bub(c,x-r*1.6+i*r*2,y-r*1.4+j*r*1.75,r,k));this.shooter(c,x,y+s*.3,s*.35,-Math.PI/2,1)},
  bub(c,x,y,r,k){D.circle(c,x,y,r,COLS[k],Math.max(2,r*.13))},
  shooter(c,x,y,s,a,k){c.save();c.translate(x,y);c.rotate(a+Math.PI/2);D.rrect(c,-s*.12,-s*.9,s*.24,s*.6,s*.08,'#b9c3cc');c.restore();D.circle(c,x,y,s*.38,'#f4e6d4');D.face(c,x,y+s*.12,s*.4)},
  pos(r,c){const st=this.st;const odd=(r+st.par)%2;return[X0+c*R*2+(odd?R:0)+R,SY+r*RH+st.drop]},
  cols(r){return(r+this.st.par)%2?NC-1:NC},
  reset(api){const st=this.st={g:[],par:0,drop:0,cur:rndi(0,3),next:rndi(0,3),aim:-Math.PI/2,aiming:false,shot:null,fall:[],pops:[],shots:0,nc:4};
    for(let r=0;r<6;r++){st.g.push([]);for(let c=0;c<this.cols(r);c++)st.g[r].push(rndi(0,3))}api.score=0},
  colorsLeft(){const s=new Set();for(const row of this.st.g)for(const v of row)if(v>=0)s.add(v);return[...s]},
  down(x,y){this.st.aiming=true;this.aimAt(x,y)},move(x,y){if(this.st.aiming)this.aimAt(x,y)},
  up(x,y,api){if(!this.st.aiming)return;this.st.aiming=false;this.aimAt(x,y);this.fire(api)},
  aimAt(x,y){this.st.aim=clamp(Math.atan2(Math.min(y,SYY-20)-SYY,x-SX),-Math.PI+.18,-.18)},
  key(k,api){const st=this.st;if(k==='ArrowLeft')st.aim=Math.max(-Math.PI+.18,st.aim-.06);if(k==='ArrowRight')st.aim=Math.min(-.18,st.aim+.06);if(k===' ')this.fire(api)},keyRepeat:true,
  fire(api){const st=this.st;if(st.shot)return;st.shot={x:SX,y:SYY,vx:Math.cos(st.aim)*900,vy:Math.sin(st.aim)*900,k:st.cur};st.cur=st.next;const cl=this.colorsLeft();st.next=cl.length?pick(cl):rndi(0,st.nc-1);S.whoosh()},
  cell(r,c){const g=this.st.g;return g[r]&&c>=0&&c<g[r].length?g[r][c]:-2},
  nb(r,c){const odd=(r+this.st.par)%2;const d=odd?[[0,-1],[0,1],[-1,0],[-1,1],[1,0],[1,1]]:[[0,-1],[0,1],[-1,-1],[-1,0],[1,-1],[1,0]];return d.map(([dr,dc])=>[r+dr,c+dc])},
  snap(x,y){const st=this.st;let best=null,bd=1e9;for(let r=0;r<st.g.length+1;r++){for(let c=0;c<(r<st.g.length?st.g[r].length:this.cols(r));c++){if(r<st.g.length&&st.g[r][c]>=0)continue;const[px,py]=this.pos(r,c);const d=dist(px,py,x,y);if(d<bd){bd=d;best=[r,c]}}}return best},
  place(r,c,k,api){const st=this.st;while(st.g.length<=r){const nr=st.g.length;st.g.push(new Array(this.cols(nr)).fill(-1))}st.g[r][c]=k;
    // 同じ色のかたまり
    const seen=new Set([r+','+c]),q=[[r,c]],grp=[];while(q.length){const[a,b]=q.pop();grp.push([a,b]);for(const[nr,nc]of this.nb(a,b))if(this.cell(nr,nc)===k&&!seen.has(nr+','+nc)){seen.add(nr+','+nc);q.push([nr,nc])}}
    if(grp.length>=3){for(const[a,b]of grp){const[px,py]=this.pos(a,b);st.pops.push({x:px,y:py,k,t:-grp.indexOf([a,b])*0});st.g[a][b]=-1;api.burst(px,py,{c:[COLS[k],'#fff'],n:6,sp:150,r:4})}
      api.combo++;const pts=grp.length*10*api.combo;api.add(pts);S.pop(1.2);for(let i=1;i<Math.min(grp.length,8);i++)S.tone(700+i*120,.06,{type:'sine',v:.15,at:i*.04});
      // 天井とつながってないものを落とす
      const ok=new Set(),q2=[];st.g[0].forEach((v,cc)=>{if(v>=0){ok.add('0,'+cc);q2.push([0,cc])}});while(q2.length){const[a,b]=q2.pop();for(const[nr,nc]of this.nb(a,b))if(this.cell(nr,nc)>=0&&!ok.has(nr+','+nc)){ok.add(nr+','+nc);q2.push([nr,nc])}}
      let nf=0;st.g.forEach((row,a)=>row.forEach((v,b)=>{if(v>=0&&!ok.has(a+','+b)){const[px,py]=this.pos(a,b);st.fall.push({x:px,y:py,vx:rnd(-60,60),vy:rnd(-150,0),k:v});row[b]=-1;nf++}}));
      if(nf){const b=nf*nf*20;api.add(b);setTimeout(()=>S.coin(1.2),150);api.float(W/2,330,nf+'こ落下！ +'+b,{size:Math.min(40,22+nf*2),c:'#f3c84b'});if(nf>=5){api.shake(8);api.flash('#fff',.3);S.perfect()}}
      api.float(this.pos(r,c)[0],this.pos(r,c)[1]-20,'+'+pts,{size:22})}
    else{api.combo=0;S.thud()}
    while(st.g.length&&st.g[st.g.length-1].every(v=>v<0))st.g.pop();
    if(!st.g.length||st.g.every(row=>row.every(v=>v<0))){api.add(3000);S.fanfare();api.float(W/2,280,'ぜんぶ消した！ +3000',{size:30,c:'#f3c84b',life:1.6});st.nc=Math.min(6,st.nc+1);this.addRows(5)}
    st.shots++;if(st.shots%5===0)this.addRows(1);
    for(let a=0;a<st.g.length;a++)if(st.g[a].some(v=>v>=0)&&this.pos(a,0)[1]+R>LINE){api.end();S.bad();return}},
  addRows(n){const st=this.st;for(let i=0;i<n;i++){st.par^=1;st.g.unshift(new Array(this.cols(0)).fill(0).map(()=>rndi(0,st.nc-1)));st.drop=-RH}S.thud()},
  update(dt,api){const st=this.st;st.drop=Math.min(0,st.drop+dt*RH*5);
    const s=st.shot;if(s){const steps=4;for(let i=0;i<steps;i++){s.x+=s.vx*dt/steps;s.y+=s.vy*dt/steps;if(s.x<X0+R){s.x=X0+R;s.vx*=-1;S.tap(.7)}if(s.x>X0+NC*R*2-R){s.x=X0+NC*R*2-R;s.vx*=-1;S.tap(.7)}
        let hit=s.y<=SY+st.drop;if(!hit)for(let r=0;r<st.g.length&&!hit;r++)for(let c=0;c<st.g[r].length;c++){if(st.g[r][c]<0)continue;const[px,py]=this.pos(r,c);if(dist(px,py,s.x,s.y)<R*1.75){hit=true;break}}
        if(hit){const sp=this.snap(s.x,s.y);st.shot=null;if(sp)this.place(sp[0],sp[1],s.k,api);break}}}
    for(let i=st.fall.length-1;i>=0;i--){const f=st.fall[i];f.vy+=1400*dt;f.x+=f.vx*dt;f.y+=f.vy*dt;if(f.y>H+40)st.fall.splice(i,1)}
    for(let i=st.pops.length-1;i>=0;i--){st.pops[i].t+=dt;if(st.pops[i].t>.2)st.pops.splice(i,1)}},
  draw(c,api){const st=this.st;c.fillStyle='#dbe5f1';c.fillRect(0,api.top,W,api.bottom-api.top);D.rrect(c,X0-6,SY-R-10,NC*R*2+12,LINE-SY+R+40,16,'#eef3f9',4);
    c.setLineDash([8,8]);c.strokeStyle='#e2645a';c.lineWidth=2;c.beginPath();c.moveTo(X0,LINE);c.lineTo(X0+NC*R*2,LINE);c.stroke();c.setLineDash([]);
    st.g.forEach((row,r)=>row.forEach((v,cc)=>{if(v>=0){const[px,py]=this.pos(r,cc);this.bub(c,px,py,R-1,v)}}));
    for(const p of st.pops){const k=p.t/.2;c.globalAlpha=1-k;this.bub(c,p.x,p.y,R*(1+k*.6),p.k);c.globalAlpha=1}
    for(const f of st.fall)this.bub(c,f.x,f.y,R-1,f.k);
    // ガイド線（1回反射まで）
    if(!st.shot){c.fillStyle='rgba(91,77,69,.35)';let x=SX,y=SYY,vx=Math.cos(st.aim),vy=Math.sin(st.aim);for(let i=0;i<34;i++){x+=vx*16;y+=vy*16;if(x<X0+R||x>X0+NC*R*2-R)vx*=-1;if(y<SY+st.drop)break;if(i>2){c.beginPath();c.arc(x,y,3,0,7);c.fill()}}}
    if(st.shot)this.bub(c,st.shot.x,st.shot.y,R-1,st.shot.k);
    this.shooter(c,SX,SYY+28,90,st.aim);if(!st.shot)this.bub(c,SX,SYY,R-1,st.cur);
    D.text(c,'つぎ',SX+92,SYY+6,14,'#8e8077');this.bub(c,SX+92,SYY+34,R*.75,st.next);
    D.text(c,'あと'+(5-st.shots%5)+'発で',70,SYY+22,14,'#8e8077');D.text(c,'天井がさがる',70,SYY+42,14,'#8e8077')},
  __bot(api){const st=this.st;if(st.shot)return;let best=null,bs=-1;
    for(let i=0;i<40;i++){const a=-Math.PI+.2+i*(Math.PI-.4)/39;let x=SX,y=SYY,vx=Math.cos(a)*8,vy=Math.sin(a)*8,hit=null;for(let s=0;s<200&&!hit;s++){x+=vx;y+=vy;if(x<X0+R||x>X0+NC*R*2-R)vx*=-1;if(y<SY)hit=[x,y];for(let r=0;r<st.g.length&&!hit;r++)for(let cc=0;cc<st.g[r].length;cc++)if(st.g[r][cc]>=0){const[px,py]=this.pos(r,cc);if(dist(px,py,x,y)<R*1.75){hit=[x,y];break}}}
      if(!hit)continue;const sp=this.snap(hit[0],hit[1]);if(!sp)continue;let n=0;for(const[nr,nc]of this.nb(sp[0],sp[1]))if(this.cell(nr,nc)===st.cur)n++;const sc=n+Math.random()*.5;if(sc>bs){bs=sc;best=a}}
    st.aim=best??-Math.PI/2;this.fire(api)},
};
