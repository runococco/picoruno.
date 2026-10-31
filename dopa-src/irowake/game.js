/* いろわけジュース：ウォーターソート。上の色が同じか空のびんにだけ注げる。 */
const CAP=4,JUICE=['#e46a6a','#8fc46a','#9b7cc6','#f2a24a','#f2d25a','#6fb2d9','#f2a5c0','#9a6a4e','#6fc9b0'];
const GAME={...META,sprites:['icon','bottle'],unit:'問',time:90,hudUnit:true,comboHud:false,
  bgm:{bpm:112,root:60,scale:'major',prog:[1,5,6,4],seed:55,lead:'triangle',drums:'pop',density:.5},
  ranks:[[0,'まぜまぜ'],[2,'ジュース係'],[4,'いろわけ上手'],[7,'色のソムリエ'],[10,'ジュース職人'],[14,'いろわけの神']],
  shareText:(v,f)=>`いろわけジュースで ${f}問 とけた！`,
  icon(c,x,y,s){this.bottle(c,x-s*.22,y+s*.05,s*.3,[0,0,1,1],0,false);this.bottle(c,x+s*.22,y+s*.05,s*.3,[5,5,5,5],0,true)},
  // 底から順に色番号の配列
  bottle(c,x,y,h,cols,lift=0,done=false,sel=false){const w=h*.27,top=y-h/2-lift,lw=Math.max(2.5,h*.03);c.save();
    const shape=c=>{c.moveTo(x-w/2,top+h*.08);c.lineTo(x-w/2,top+h-w/2);c.arc(x,top+h-w/2,w/2,Math.PI,0,true);c.lineTo(x+w/2,top+h*.08)};
    D.path(c,c=>{shape(c);c.closePath()},'#fbfdfd',lw);
    c.save();c.beginPath();shape(c);c.closePath();c.clip();const lh=(h*.88)/CAP;
    cols.forEach((k,i)=>{c.fillStyle=JUICE[k];c.fillRect(x-w/2,top+h-(i+1)*lh,w,lh+.5)});c.restore();
    D.path(c,c=>{shape(c)},null,lw);
    if(done){D.rrect(c,x-w*.4,top-h*.06,w*.8,h*.12,h*.03,'#c99a6a',lw);D.face(c,x,top+h-lh*1.8,w*.8)}
    if(sel){D.poly(c,[[x-8,top-26],[x+8,top-26],[x,top-14]],'#f3c84b',2.5)}
    c.restore()},
  newLevel(api){const st=this.st;st.lv++;const nc=Math.min(3+Math.floor(st.lv/2),9),pool=[];
    for(let k=0;k<nc;k++)for(let i=0;i<CAP;i++)pool.push(k);
    let b;do{for(let i=pool.length-1;i>0;i--){const j=rndi(0,i);[pool[i],pool[j]]=[pool[j],pool[i]]}b=[];for(let k=0;k<nc;k++)b.push(pool.slice(k*CAP,k*CAP+CAP))}while(b.some(t=>t.every(v=>v===t[0])));
    b.push([],[]);st.b=b;st.sel=-1;st.pour=null;st.extra=false;st.hist=[];st.lay=this.layout(b.length)},
  layout(n){const row=n<=6?1:2,per=Math.ceil(n/row),out=[];const h=n<=6?200:165;
    for(let i=0;i<n;i++){const r=Math.floor(i/per),k=i%per,cnt=r===row-1?n-per*(row-1):per,gap=Math.min(76,(W-30)/cnt);out.push({x:W/2+(k-(cnt-1)/2)*gap,y:row===1?400:300+r*240,h})}return out},
  reset(api){this.st={lv:0,b:[],sel:-1,pour:null,lay:[],clearT:0,shake:{}};this.newLevel(api);api.score=0},
  top(t){return t.length?t[t.length-1]:-1},
  canPour(a,b){const A=this.st.b[a],B=this.st.b[b];if(a===b||!A.length||B.length>=CAP)return false;return!B.length||this.top(B)===this.top(A)},
  isDone(t){return t.length===CAP&&t.every(v=>v===t[0])},
  hit(x,y){const st=this.st;for(let i=0;i<st.lay.length;i++){const L=st.lay[i];if(Math.abs(x-L.x)<Math.min(38,(W-30)/st.lay.length*.55+10)&&Math.abs(y-L.y)<L.h*.6)return i}
    // ボタン
    if(y>H-90&&y<H-30){if(x>40&&x<200)return'undo';if(x>220&&x<380)return'extra'}return-1},
  down(x,y,api){const st=this.st;if(st.pour||st.clearT>0)return;const i=this.hit(x,y);
    if(i==='undo'){if(st.hist.length){st.b=st.hist.pop();st.sel=-1;S.whoosh()}return}
    if(i==='extra'){if(!st.extra){st.extra=true;st.b.push([]);st.lay=this.layout(st.b.length);api.timeLeft=Math.max(1,api.timeLeft-5);api.float(W/2,H-110,'びん+1（-5秒）',{size:20});S.good()}return}
    if(i<0){st.sel=-1;return}
    if(st.sel<0){if(st.b[i].length&&!this.isDone(st.b[i])){st.sel=i;S.tap()}else S.tap(.6);return}
    if(i===st.sel){st.sel=-1;S.tap(.8);return}
    if(this.canPour(st.sel,i)){this.pour(st.sel,i,api)}else{st.shake[i]=.3;S.bad();if(st.b[i].length&&!this.isDone(st.b[i])){st.sel=i}}},
  pour(a,b,api){const st=this.st;st.hist.push(st.b.map(t=>t.slice()));if(st.hist.length>20)st.hist.shift();
    const A=st.b[a],B=st.b[b],k=this.top(A);let n=0;while(A.length&&this.top(A)===k&&B.length<CAP){A.pop();n++}
    st.pour={a,b,k,n,t:0,dst:B.length,src:A.length};st.sel=-1;
    for(let i=0;i<n;i++)S.tone(380+i*90,.09,{type:'sine',v:.2,at:.18+i*.08,to:520+i*90})},
  update(dt,api){const st=this.st;for(const k in st.shake)st.shake[k]=Math.max(0,st.shake[k]-dt);
    if(st.pour){const p=st.pour;p.t+=dt;if(p.t>.25+p.n*.09){const B=st.b[p.b];for(let i=0;i<p.n;i++)B.push(p.k);st.pour=null;
        if(this.isDone(B)){const L=st.lay[p.b];S.coin(1.2);api.burst(L.x,L.y-L.h/2,{c:[JUICE[p.k],'#fff'],n:16,sp:200,shape:'star'});api.ring(L.x,L.y,{c:JUICE[p.k],r:70});api.combo++}
        if(st.b.every(t=>!t.length||this.isDone(t))){st.clearT=1.1;api.add(1);api.timeLeft+=15;S.fanfare();api.flash('#fff',.4);api.float(W/2,200,'クリア！ +15秒',{size:34,c:'#f3c84b',life:1.1});
          for(let i=0;i<4;i++)api.burst(rnd(60,W-60),rnd(250,500),{c:JUICE,n:14,sp:260,shape:'star'})}}}
    if(st.clearT>0){st.clearT-=dt;if(st.clearT<=0){this.newLevel(api)}}},
  draw(c,api){const st=this.st;c.fillStyle='#e4eef0';c.fillRect(0,0,W,H);
    c.fillStyle='#d3e3e6';for(let i=0;i<8;i++)c.fillRect(0,170+i*80,W,40);
    const rows=[...new Set(st.lay.map(L=>L.y))];for(const ry of rows)D.rrect(c,14,ry+st.lay[0].h/2-6,W-28,20,9,'#c9a77e',3);
    D.text(c,'Lv.'+st.lv,W/2,130,22,'#5b4d45');
    st.b.forEach((t,i)=>{const L=st.lay[i];if(!L)return;let x=L.x,y=L.y,lift=i===st.sel?28:0,cols=t;
      if(st.shake[i])x+=Math.sin(st.shake[i]*60)*5;
      const p=st.pour;if(p&&i===p.a){const L2=st.lay[p.b],k=Math.min(1,p.t/.18);x=lerp(L.x,L2.x-34,k);y=lerp(L.y,L2.y-L.h*.55,k);
        c.save();c.translate(x,y);c.rotate(k*1.1);this.bottle(c,0,0,L.h,cols,0);c.restore();
        if(k>=1){c.fillStyle=JUICE[p.k];c.fillRect(L2.x-6,L2.y-L.h*.85,8,L.h*.6)}return}
      if(p&&i===p.b){const k=clamp((p.t-.18)/(p.n*.09),0,1);cols=t.slice();const m=Math.floor(k*p.n);for(let j=0;j<m;j++)cols.push(p.k)}
      this.bottle(c,x,y,L.h,cols,lift,this.isDone(t),i===st.sel)});
    D.rrect(c,40,H-90,160,52,26,st.hist.length?'#fffdf8':'#e9e2d9',3);D.text(c,'ひとつもどす',120,H-64,17,st.hist.length?'#5b4d45':'#b0a59b');
    D.rrect(c,220,H-90,160,52,26,st.extra?'#e9e2d9':'#fffdf8',3);D.text(c,st.extra?'つかった':'びん+1',300,H-64,17,st.extra?'#b0a59b':'#5b4d45');
  },
  __bot(api){const st=this.st;if(st.pour||st.clearT>0)return;const n=st.b.length;let mv=null;
    for(let a=0;a<n&&!mv;a++)for(let b=0;b<n;b++){if(!this.canPour(a,b)||this.isDone(st.b[a]))continue;const A=st.b[a];if(!st.b[b].length&&A.every(v=>v===A[0]))continue;if(st.b[b].length){mv=[a,b];break}}
    if(!mv)for(let a=0;a<n&&!mv;a++)for(let b=0;b<n;b++){if(this.canPour(a,b)&&!this.isDone(st.b[a])&&!(st.b[a].every(v=>v===st.b[a][0])&&!st.b[b].length)){mv=[a,b];break}}
    if(!mv&&!st.extra){this.down(300,H-64,api);return}
    if(!mv||Math.random()<.1){if(st.hist.length)this.down(120,H-64,api);return}
    this.pour(mv[0],mv[1],api)},
};
