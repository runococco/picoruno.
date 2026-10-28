/* ぷちぷちラッシュ：なぞってつぶす。1シート全部で+3秒、金でフィーバー、怒りぷちは-2秒。 */
const COLS=6,ROWS=8,GX=55,GY=188,SP=62,R=25;
const GAME={...META,sprites:['icon','mini'],comboHud:false,time:30,unit:'ぷち',hudUnit:false,
  bgm:{bpm:152,root:62,scale:'major',prog:[1,6,4,5],seed:11,lead:'square',drums:'pop'},
  ranks:[[0,'ぷちぷち見習い'],[60,'ぷちぷち好き'],[120,'ぷちぷち職人'],[180,'ぷちぷちマイスター'],[250,'エアパッキン破壊神'],[330,'ぷちぷちの化身']],
  shareText:(v,f)=>`ぷちぷちラッシュで ${f}ぷち つぶした！`,
  icon(c,x,y,s){
    const r=s*.36;D.ellipse(c,x+s*.05,y+s*.06,r*1.1,r,'#cfeaf0',s*.025);D.face(c,x+s*.05,y+s*.06,r*1.3,'smile');
    D.circle(c,x-s*.33,y-s*.3,s*.1,'#cfeaf0',s*.02);D.circle(c,x+s*.36,y-s*.32,s*.07,'#f6d87a',s*.02);D.circle(c,x-s*.36,y+s*.3,s*.06,'#cfeaf0',s*.02);
    c.save();c.globalAlpha=.9;D.text(c,'ぷち！',x+s*.28,y+s*.38,s*.13,'#fff','center',OL,s*.03);c.restore();
  },
  // 説明用の小さいぷち
  mini(c,x,y,r,col,mood){D.ellipse(c,x,y,r,r*.92,col,2.5);D.face(c,x,y+1,r*1.1,mood)},
  legend(c){const y=112;
    D.rrect(c,22,y-19,W-44,38,19,'rgba(255,255,255,.7)',2.5);
    this.mini(c,48,y,13,'#f6d87a','o');D.text(c,'フィーバー 得点2倍',128,y+1,14,'#5b4d45');
    this.mini(c,236,y,13,'#ec8d82','angry');D.text(c,'さわると -2秒',310,y+1,14,'#e2645a')},
  newSheet(api,from=0){
    const st=this.st,n=st.sheet;st.bubs=[];
    const golds=n%2===1?1:0,bads=Math.min(1+Math.floor(n/2),6);
    const cells=[];for(let j=0;j<ROWS;j++)for(let i=0;i<COLS;i++)cells.push([i,j]);
    cells.sort(()=>Math.random()-.5);
    cells.forEach(([i,j],k)=>{const type=k<golds?'gold':k<golds+bads?'bad':'n';
      st.bubs.push({i,j,x:GX+i*SP+(j%2?14:-14),y:GY+j*SP,type,popped:false,pt:0,face:type!=='n'||Math.random()<.14,wob:rnd(6),...this.crumple()})});
    st.slide=from;
  },
  // つぶれたあとのしわ：ふちの内側に、くしゃっとした膜と折れ線
  crumple(){const n=12,crum=[];for(let a=0;a<n;a++)crum.push([a/n*Math.PI*2+rnd(-.12,.12),rnd(.5,.9)]);
    const wr=[];for(let k=0;k<rndi(3,4);k++){const a=rnd(Math.PI*2),r0=rnd(.05,.3),pts=[[Math.cos(a)*r0,Math.sin(a)*r0]];let ang=a+rnd(-.6,.6),r=r0;for(let m=0;m<2;m++){r+=rnd(.2,.32);ang+=rnd(-.7,.7);pts.push([Math.cos(ang)*r,Math.sin(ang)*r])}wr.push(pts)}
    return{crum,wr,rot:rnd(6)}},
  reset(api){this.st={sheet:0,bubs:[],slide:0,lastPop:-9,feverT:0,px:null,py:null,down:false,popped:0,mad:0};this.newSheet(api,0);api.score=0},
  popAt(x,y,api){
    const st=this.st;if(st.slide>0.05)return;
    for(const b of st.bubs){if(b.popped)continue;if(dist(x,y,b.x,b.y)<R+6)this.pop(b,api)}
  },
  pop(b,api){
    const st=this.st;b.popped=true;b.pt=0;
    if(b.type==='bad'){api.combo=0;api.timeLeft=Math.max(0,api.timeLeft-2);S.bad();api.shake(12);api.flash('#e2645a',.35);api.float(b.x,b.y-20,'-2秒',{c:'#e2645a',size:30});api.burst(b.x,b.y,{c:['#e2645a','#f39a8f'],n:14,sp:260});st.mad=.4;return}
    const chain=api.t-st.lastPop<.45;st.lastPop=api.t;api.combo=chain?api.combo+1:1;
    let pts=1;if(b.type==='gold'){pts=5;st.feverT=4;api.fever=true;api.bgmRate=1.2;S.perfect();api.flash('#f6d87a',.4);api.ring(b.x,b.y,{c:'#f6d87a',r:120});api.float(b.x,b.y-30,'FEVER!',{c:'#f6d87a',size:36})}
    if(api.fever)pts*=2;
    api.score+=pts;st.popped++;
    S.puchi(rnd(.9,1.1));
    api.burst(b.x,b.y,{c:b.type==='gold'?['#f6d87a','#fff']:['#fff','#bfe4ec'],n:6,sp:160,r:4,g:300,life:.35});
    if(api.combo%10===0&&api.combo>0){api.float(W/2,140,api.combo+' COMBO!',{c:'#fff',size:30});S.combo(api.combo/5)}
    if(st.bubs.every(q=>q.popped||q.type==='bad')){
      st.sheet++;api.timeLeft+=3;api.score+=api.fever?20:10;S.fanfare();api.flash('#fff',.5);api.float(W/2,H/2,'1枚クリア！ +3秒',{size:34,c:'#fff',life:1.1});
      for(const q of st.bubs)if(!q.popped){q.popped=true;q.pt=0}
      setTimeout(()=>{if(api.state==='play')this.newSheet(api,1)},250);
    }
  },
  down(x,y,api){this.st.down=true;this.st.px=x;this.st.py=y;this.popAt(x,y,api)},
  move(x,y,api){const st=this.st;if(!st.down)return;const d=dist(st.px,st.py,x,y),n=Math.ceil(d/10);for(let k=1;k<=n;k++)this.popAt(lerp(st.px,x,k/n),lerp(st.py,y,k/n),api);st.px=x;st.py=y},
  up(){this.st.down=false},
  update(dt,api){const st=this.st;
    if(st.slide>0)st.slide=Math.max(0,st.slide-dt*4);
    if(st.feverT>0){st.feverT-=dt;if(st.feverT<=0){api.fever=false;api.bgmRate=1}}
    st.mad=Math.max(0,st.mad-dt);
    for(const b of st.bubs){b.pt+=dt;b.wob+=dt}
  },
  draw(c,api){const st=this.st;
    c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.globalAlpha=.35;for(let i=0;i<12;i++){D.circle(c,(i*97)%W,(i*173+api.t*20)%H,8+(i%3)*6,'#fff',0)}c.globalAlpha=1;
    const ox=st.slide*W*ease.out(st.slide);
    c.save();c.translate(ox,0);
    D.rrect(c,12,GY-46,W-24,ROWS*SP+28,22,'rgba(255,255,255,.55)',3.5);
    for(const b of st.bubs){
      const x=b.x,y=b.y;
      const tint=b.type==='gold'?'#f6d87a':b.type==='bad'?'#ec8d82':'#dff1f4';
      if(b.popped&&b.pt>.07){
        // ぺしゃんこ：シートの継ぎ目の輪＋くしゃっとした膜＋しわ
        c.globalAlpha=.55;D.circle(c,x,y,R,tint,0);c.globalAlpha=1;
        c.lineWidth=2;c.strokeStyle='rgba(91,77,69,.35)';c.beginPath();c.arc(x,y,R,0,7);c.stroke();
        c.save();c.translate(x,y);c.rotate(b.rot);
        c.beginPath();b.crum.forEach(([t,r],i)=>{const px=Math.cos(t)*r*R,py=Math.sin(t)*r*R;i?c.lineTo(px,py):c.moveTo(px,py)});c.closePath();
        c.fillStyle=b.type==='n'?'rgba(170,205,214,.45)':b.type==='gold'?'rgba(214,170,70,.4)':'rgba(200,110,100,.4)';c.fill();c.lineWidth=1.6;c.strokeStyle='rgba(91,77,69,.42)';c.lineJoin='round';c.stroke();
        c.lineWidth=1.4;c.strokeStyle='rgba(91,77,69,.32)';c.lineCap='round';for(const w of b.wr){c.beginPath();w.forEach(([px,py],i)=>i?c.lineTo(px*R,py*R):c.moveTo(px*R,py*R));c.stroke()}
        c.restore();continue}
      // 押されてつぶれる途中（0.07秒）
      const k=b.popped?b.pt/.07:0,wob=1+Math.sin(b.wob*3)*.03;
      c.globalAlpha=.5;D.circle(c,x,y,R+2,tint,0);c.globalAlpha=1;
      D.group(c,()=>{D.ellipse(c,x,y+k*4,R*wob*(1+k*.12),R*.92/wob*(1-k*.55),tint,3);
        if(D.mode==='fill'){c.save();c.beginPath();c.ellipse(x,y+k*4,R*wob*(1+k*.12),R*.92/wob*(1-k*.55),0,0,7);c.clip();c.fillStyle='rgba(91,77,69,.09)';c.beginPath();c.ellipse(x+R*.25,y+R*.55,R*.95,R*.6,0,0,7);c.fill();c.restore()}});
      if((b.face||b.type!=='n')&&k<.5)D.face(c,x,y+2,R*1.0,b.type==='bad'?'angry':b.type==='gold'?'o':'smile');
    }
    c.restore();
    this.legend(c);
    D.text(c,'シート '+(st.sheet+1),W/2,H-22,16,'#8e8077');
  },
};
