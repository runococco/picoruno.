/* めくってペア：神経衰弱。絵柄はかんたんなマスコット。 */
const ART=[['maru','#f2a5b5'],['star','#f4d66d'],['cloud','#a9d6e6'],['heart','#f08a8a'],['kaku','#9cc86a'],['drop','#7fb2e0'],['moon','#f2c84b'],['mame','#c49ae0'],['ghost','#fbf7f0'],['kinoko','#e2645a']];
const GAME={...META,sprites:['icon','card','mark'],unit:'ペア',time:90,hudUnit:true,comboHud:false,fullBleed:true,
  bgm:{bpm:104,root:62,scale:'major',prog:[1,4,2,5],seed:44,lead:'triangle',drums:'pop',density:.5},
  ranks:[[0,'ど忘れ'],[4,'おぼえ見習い'],[8,'なかなかの記憶力'],[14,'ペアの達人'],[20,'記憶の天才'],[28,'ぜったい忘れない']],
  shareText:(v,f)=>`めくってペアで ${f}ペア そろえた！`,
  icon(c,x,y,s){this.card(c,x-s*.22,y,s*.36,s*.5,false,0,-.1);this.card(c,x+s*.2,y,s*.36,s*.5,true,0,.1)},
  mark(c,x,y,r,k){const[sh,col]=ART[k];
    if(sh==='maru')D.circle(c,x,y,r,col);else if(sh==='star')D.star(c,x,y,r*1.15,col,3,0,5,.55);else if(sh==='cloud')D.path(c,c=>{c.arc(x-r*.5,y+r*.15,r*.55,Math.PI*.5,Math.PI*1.5);c.arc(x,y-r*.3,r*.6,Math.PI*1.1,Math.PI*1.9);c.arc(x+r*.5,y+r*.1,r*.55,Math.PI*1.5,Math.PI*.5);c.closePath()},col);
    else if(sh==='heart')D.path(c,c=>{c.moveTo(x,y+r*.9);c.bezierCurveTo(x-r*1.4,y,x-r*.7,y-r*1.1,x,y-r*.45);c.bezierCurveTo(x+r*.7,y-r*1.1,x+r*1.4,y,x,y+r*.9)},col);
    else if(sh==='kaku')D.rrect(c,x-r*.9,y-r*.9,r*1.8,r*1.8,r*.3,col);else if(sh==='drop')D.path(c,c=>{c.moveTo(x,y-r*1.1);c.quadraticCurveTo(x+r,y,x+r*.85,y+r*.3);c.arc(x,y+r*.3,r*.85,0,Math.PI);c.quadraticCurveTo(x-r,y,x,y-r*1.1)},col);
    else if(sh==='moon')D.path(c,c=>{c.arc(x,y,r,-Math.PI*.35,Math.PI*1.35);c.arc(x+r*.45,y-r*.4,r*.75,Math.PI*1.1,-Math.PI*.05,true);c.closePath()},col);
    else if(sh==='mame')D.ellipse(c,x,y,r*.75,r,col);else if(sh==='ghost')D.path(c,c=>{c.arc(x,y-r*.1,r*.85,Math.PI,0);c.lineTo(x+r*.85,y+r*.8);for(let k=0;k<3;k++){const x0=x+r*.85-k*r*.57;c.quadraticCurveTo(x0-r*.14,y+r*.55,x0-r*.28,y+r*.8);c.quadraticCurveTo(x0-r*.42,y+r*1.05,x0-r*.57,y+r*.8)}c.closePath()},col);
    else{D.rrect(c,x-r*.4,y,r*.8,r*.85,r*.3,'#fbf2e4');D.path(c,c=>{c.moveTo(x-r,y+r*.1);c.quadraticCurveTo(x-r,y-r,x,y-r);c.quadraticCurveTo(x+r,y-r,x+r,y+r*.1);c.closePath()},col)}
    D.face(c,x,y+(sh==='kinoko'?r*.4:sh==='drop'?r*.3:r*.05),r*(sh==='kinoko'?.6:.85))},
  card(c,x,y,w,h,open,k,rot=0,flip=1){c.save();c.translate(x,y);c.rotate(rot);c.scale(Math.abs(flip),1);
    if(open){D.rrect(c,-w/2,-h/2,w,h,w*.15,'#fffdf8');this.mark(c,0,0,w*.3,k)}else{D.rrect(c,-w/2,-h/2,w,h,w*.15,'#6fa35a');D.rrect(c,-w*.36,-h*.4,w*.72,h*.8,w*.1,'#8fbf6a',2.5);D.circle(c,0,0,w*.12,'#fffdf8',2)}c.restore()},
  reset(api){this.st={lv:0,cards:[],open:[],lock:0,t:0};this.deal();api.score=0},
  deal(){const st=this.st;const pairs=Math.min(10,4+st.lv*1),cols=pairs<=6?3:4,n=pairs*2,rows=Math.ceil(n/cols);const ks=[];for(let i=0;i<pairs;i++){const k=(i+st.lv*2)%ART.length;ks.push(k,k)}
    for(let i=ks.length-1;i>0;i--){const j=rndi(0,i);[ks[i],ks[j]]=[ks[j],ks[i]]}
    const cw=Math.min(100,(W-40)/cols-10),ch=cw*1.3;const ox=(W-cols*(cw+10))/2+cw/2+5,oy=170+((H-230)-rows*(ch+10))/2+ch/2;
    st.cards=ks.map((k,i)=>({k,x:ox+(i%cols)*(cw+10),y:oy+Math.floor(i/cols)*(ch+10),w:cw,h:ch,open:false,done:false,flip:1,tf:1}));st.open=[];st.lock=0},
  down(x,y,api){const st=this.st;if(st.lock>0)return;const cd=st.cards.find(q=>!q.open&&!q.done&&Math.abs(x-q.x)<q.w/2&&Math.abs(y-q.y)<q.h/2);if(!cd)return;
    cd.open=true;cd.tf=-1;S.tap(1.2);st.open.push(cd);
    if(st.open.length===2){const[a,b]=st.open;st.lock=a.k===b.k?.5:.8;st.match=a.k===b.k}},
  update(dt,api){const st=this.st;st.t+=dt;for(const q of st.cards){q.flip+=(q.tf-q.flip)*Math.min(1,dt*12);if(q.tf<0&&q.flip<0.05){q.tf=1;q.flip=1}}
    if(st.lock>0){st.lock-=dt;if(st.lock<=0){const[a,b]=st.open;if(st.match){a.done=b.done=true;api.add(1);api.combo++;S.coin(1+Math.min(api.combo,8)*.05);api.burst(a.x,a.y,{c:[ART[a.k][1],'#fff'],n:8,sp:120,shape:'star'});api.burst(b.x,b.y,{c:[ART[a.k][1],'#fff'],n:8,sp:120,shape:'star'});
          if(st.cards.every(q=>q.done)){st.lv++;api.timeLeft+=10;S.fanfare();api.flash('#fff',.4);api.float(W/2,140,'ぜんぶそろった！ +10秒',{size:28,c:'#f3c84b'});this.deal()}}
        else{a.open=b.open=false;a.tf=b.tf=-1;api.combo=0;S.tap(.6)}st.open=[]}}},
  draw(c,api){const st=this.st;c.fillStyle='#e5f0e4';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#d9e8d6';for(let y=api.top;y<api.bottom;y+=50)for(let x=(y/50)%2*25;x<W;x+=50)c.fillRect(x,y,25,25);
    for(const q of st.cards){if(q.done){c.globalAlpha=.45;this.card(c,q.x,q.y,q.w,q.h,true,q.k,0,1);c.globalAlpha=1;continue}const showOpen=q.open?(q.tf<0?q.flip<.5:true):(q.tf<0?q.flip>=.5:false);const f=q.tf<0?Math.abs(q.flip*2-1):1;this.card(c,q.x,q.y,q.w,q.h,showOpen,q.k,0,Math.max(.05,f))}},
  __bot(api){const st=this.st;if(st.lock>0)return;st.mem=st.mem||{};for(const q of st.cards)if(q.open)st.mem[q.k]=(st.mem[q.k]||new Set()).add(q);
    if(st.open.length===1){const a=st.open[0];const m=[...(st.mem[a.k]||[])].find(q=>q!==a&&!q.done&&!q.open);const t=m||st.cards.find(q=>!q.open&&!q.done);if(t)this.down(t.x,t.y,api);return}
    const t=pick(st.cards.filter(q=>!q.open&&!q.done));if(t)this.down(t.x,t.y,api)},
};
