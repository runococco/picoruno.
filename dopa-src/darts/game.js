/* ゆらゆらダーツ：リサージュで動く照準をタップで止める。 */
const TX=W/2,TY=380,TR=150,N=10;
const GAME={...META,sprites:['icon','board','dart'],unit:'点',fullBleed:true,comboHud:false,
  bgm:{bpm:112,root:57,scale:'minor',prog:[1,6,3,7],seed:66,lead:'triangle',drums:'pop',density:.5},
  ranks:[[0,'はずれ'],[100,'ダーツ初心者'],[200,'なかなか'],[300,'ダーツ上手'],[400,'ブルハンター'],[480,'ダーツの神']],
  shareText:(v,f)=>`ゆらゆらダーツで ${f}点！`,
  icon(c,x,y,s){this.board(c,x,y,s*.42);this.dart(c,x+s*.08,y-s*.06,s*.28,.6)},
  board(c,x,y,r){const cols=['#fbf7f0','#e2645a','#fbf7f0','#7fb2e0','#f2c84b'];for(let i=0;i<5;i++)D.circle(c,x,y,r*(1-i*.2),cols[i],3);D.circle(c,x,y,r*.08,'#e2645a',2)},
  dart(c,x,y,s,a){c.save();c.translate(x,y);c.rotate(a);D.rrect(c,-s*.05,-s*.5,s*.1,s*.5,s*.04,'#b9c3cc');D.rrect(c,-s*.1,-s*.05,s*.2,s*.45,s*.06,'#7d6aa8');D.poly(c,[[-s*.1,s*.4],[-s*.25,s*.6],[0,s*.5],[s*.25,s*.6],[s*.1,s*.4]],'#f2a5c0',2.5);c.restore()},
  reset(api){this.st={n:0,t:0,ax:TX,ay:TY,darts:[],wait:0,res:[]};api.score=0},
  down(x,y,api){const st=this.st;if(st.wait>0||st.n>=N)return;const d=dist(st.ax,st.ay,TX,TY)/TR;let pts=0,msg='';
    if(d<.08){pts=50;msg='ブル！！'}else if(d<.2){pts=40;msg='あと少し！'}else if(d<.4){pts=30;msg='ナイス'}else if(d<.6){pts=20;msg=''}else if(d<.8){pts=10;msg=''}else if(d<1){pts=5;msg=''}else{pts=0;msg='はずれ…'}
    st.darts.push({x:st.ax,y:st.ay,a:rnd(-.3,.3)});st.n++;st.wait=.7;st.res.push(pts);api.add(pts);
    S.noise(.06,{v:.4,f:2000});S.thud();api.shake(pts===50?8:3);
    if(pts===50){S.fanfare();api.flash('#fff6c8',.5);api.burst(st.ax,st.ay,{c:['#f4d66d','#e2645a','#fff'],n:24,shape:'star',sp:280})}else if(pts>=30)S.good();else if(!pts)S.bad();
    api.float(st.ax,st.ay-60,(msg?msg+' ':'')+'+'+pts,{size:pts>=40?30:22,c:pts>=40?'#f3c84b':'#fff'})},
  key(k,api){if(k===' ')this.down(0,0,api)},
  update(dt,api){const st=this.st;st.t+=dt;st.wait-=dt;const sp=1+st.n*.22;st.ax=TX+Math.sin(st.t*1.7*sp)*TR*.95;st.ay=TY+Math.sin(st.t*2.3*sp+1)*TR*.95;
    if(st.n>=N){st.endT=(st.endT||0)+dt;if(st.endT>1.2)api.end()}},
  drawHud(c,api){const st=this.st;D.rrect(c,70,20,280,56,28,'#fffdf8',3.5);D.text(c,api.score+'点　'+st.n+'/'+N+'本',W/2,48,22,'#5b4d45')},
  draw(c,api){const st=this.st;c.fillStyle='#e8e4ee';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#ddd7e6';for(let y=api.top;y<api.bottom;y+=60)c.fillRect(0,y,W,30);
    D.rrect(c,TX-TR-30,TY-TR-30,TR*2+60,TR*2+60,30,'#8a6a52',4);this.board(c,TX,TY,TR);
    for(const d of st.darts)this.dart(c,d.x,d.y,60,d.a);
    if(st.n<N&&api.state==='play'){c.lineWidth=3;c.strokeStyle='#5b4d45';c.beginPath();c.arc(st.ax,st.ay,18,0,7);c.stroke();c.beginPath();c.moveTo(st.ax-28,st.ay);c.lineTo(st.ax-10,st.ay);c.moveTo(st.ax+10,st.ay);c.lineTo(st.ax+28,st.ay);c.moveTo(st.ax,st.ay-28);c.lineTo(st.ax,st.ay-10);c.moveTo(st.ax,st.ay+10);c.lineTo(st.ax,st.ay+28);c.stroke()}
    let x=W/2-(N-1)*16;st.res.forEach((r,i)=>D.text(c,r,x+i*32,600,16,r>=40?'#e2645a':'#5b4d45','center','#fffdf8',4));
    if(api.t<3&&api.state==='play')D.text(c,'照準がまんなかに来たらタップ',W/2,650,16,'#5b4d45','center','#fffdf8',5)},
  __bot(api){const st=this.st;if(dist(st.ax,st.ay,TX,TY)<30)this.down(0,0,api)},
};
