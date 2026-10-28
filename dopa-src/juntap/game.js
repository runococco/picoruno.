/* 1から25タッチ：シュルテ表のタイムアタック。ミスは+1秒。むずかしいモードは1〜49（7×7）。 */
let N=5,TS=68,GAP=6,GX=(W-(N*TS+(N-1)*GAP))/2,GY=220;
function setGrid(n){N=n;TS=n===5?68:49;GAP=n===5?6:5;GX=(W-(N*TS+(N-1)*GAP))/2;GY=n===5?220:200}
const PAL=['#f4c6c2','#f6dd9c','#c7e3b6','#bcdcec','#d9cdef','#f6d2b0'];
const GAME={...META,sprites:['icon'],unit:'秒',hudUnit:true,lowerIsBetter:true,comboHud:false,
  fmt:v=>v.toFixed(2),validScore:v=>v>0,
  bgm:{bpm:150,root:64,scale:'minor',prog:[1,4,5,1],seed:9,lead:'square',drums:'four',density:.7},
  modes:[{id:'n',label:'スタート（1〜25）',short:'ふつう'},{id:'hard',label:'むずかしい（1〜49）',short:'むずかしい'}],
  ranks:[[999,'のんびりさん'],[30,'ふつうの人'],[22,'すばやい人'],[16,'数字ハンター'],[12,'動体視力おばけ'],[9,'脳がバグってる']],
  ranksFor(m){return m==='hard'?[[999,'のんびりさん'],[90,'ふつうの人'],[70,'すばやい人'],[55,'数字ハンター'],[42,'動体視力おばけ'],[32,'脳がバグってる']]:this.ranks},
  shareText:(v,f,m)=>m==='hard'?`1から49まで ${f}秒 でタッチ！（むずかしい）`:`1から25まで ${f}秒 でタッチ！`,
  icon(c,x,y,s){const t=s*.27;[[1,-1,-1],[2,1,-1],[3,-1,1],[4,1,1]].forEach(([n,i,j],k)=>{D.rrect(c,x+i*t*.56-t/2,y+j*t*.56-t/2,t,t,t*.25,PAL[k],s*.02);D.text(c,n,x+i*t*.56,y+j*t*.56+2,t*.55,'#5b4d45')})},
  reset(api){setGrid(api.mode==='hard'?7:5);const M=N*N,nums=[...Array(M)].map((_,i)=>i+1).sort(()=>Math.random()-.5);
    this.st={tiles:nums.map((n,i)=>({n,i:i%N,j:Math.floor(i/N),c:pick(PAL),done:false,dt:0,shake:0})),next:1,pen:0,done:false,M};api.score=0},
  down(x,y,api){const st=this.st;if(st.done)return;
    const i=Math.floor((x-GX)/(TS+GAP)),j=Math.floor((y-GY)/(TS+GAP));if(i<0||j<0||i>=N||j>=N)return;
    const t=st.tiles.find(q=>q.i===i&&q.j===j);if(!t||t.done)return;
    const cx=GX+i*(TS+GAP)+TS/2,cy=GY+j*(TS+GAP)+TS/2;
    if(t.n===st.next){t.done=true;st.next++;api.combo++;S.pop(1+st.next*.03);S.good(1+st.next*.04);api.burst(cx,cy,{c:[t.c,'#fff'],n:10,sp:200,shape:'star',r:4});api.ring(cx,cy,{c:'#fff',r:50});
      if(st.next>st.M){st.done=true;S.fanfare();api.flash('#fff',.6);api.burst(W/2,H/2,{c:PAL,n:60,sp:500,shape:'star',r:6});setTimeout(()=>api.end(),300)}}
    else{st.pen+=1;t.shake=.3;api.combo=0;S.bad();api.shake(6);api.float(cx,cy-30,'+1秒',{c:'#e2645a',size:26})}},
  update(dt,api){const st=this.st;if(!st.done)api.score=api.t+st.pen;for(const t of st.tiles){if(t.done)t.dt+=dt;t.shake=Math.max(0,t.shake-dt)}},
  overText:'クリア！',
  draw(c,api){const st=this.st;c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.globalAlpha=.4;for(let i=0;i<10;i++)D.text(c,(i*7)%25+1,(i*83)%W,(i*131)%H,40,'#fff');c.globalAlpha=1;
    D.rrect(c,GX-14,GY-14,N*TS+(N-1)*GAP+28,N*TS+(N-1)*GAP+28,22,'#fffdf8',4);
    for(const t of st.tiles){let x=GX+t.i*(TS+GAP),y=GY+t.j*(TS+GAP);if(t.shake>0)x+=Math.sin(t.shake*80)*5;
      if(t.done){const k=Math.min(1,t.dt/.25);if(k<1){c.save();c.translate(x+TS/2,y+TS/2);c.scale(1+k*.3,1+k*.3);c.globalAlpha=1-k;D.rrect(c,-TS/2,-TS/2,TS,TS,16,t.c,3.5);c.restore();c.globalAlpha=1}
        D.rrect(c,x+4,y+4,TS-8,TS-8,TS*.2,'#f1ede5',0);c.globalAlpha=.3;D.text(c,t.n,x+TS/2,y+TS/2+2,TS*.42,'#b9ada4');c.globalAlpha=1;continue}
      D.rrect(c,x,y+4,TS,TS,TS*.23,'rgba(91,77,69,.25)',0);D.rrect(c,x,y,TS,TS,TS*.23,t.c,N===5?3.5:3);D.text(c,t.n,x+TS/2,y+TS/2+2,N===5?34:26,'#5b4d45')}
    if(st.next<=st.M&&api.state!=='title'){D.text(c,'つぎは',W/2-40,GY+N*(TS+GAP)+52,18,'#8e8077');D.text(c,st.next,W/2+30,GY+N*(TS+GAP)+50,42,'#8a7cc8','center',OL,7)}
  },
  __bot(api){const st=this.st;if(Math.random()<.1){this.down(GX+5,GY+5,api);return}const t=st.tiles.find(q=>q.n===st.next);if(t)this.down(GX+t.i*(TS+GAP)+20,GY+t.j*(TS+GAP)+20,api)},
};
