/* ぴったりケーキカット：回転するナイフ角度を止めて切る。等分からのずれで採点。 */
const CX=W/2,CY=400,R=140;
const TOP=[['#f2a5c0','いちご'],['#c9a070','チョコ'],['#9cc86a','まっちゃ'],['#f2c84b','レモン'],['#c49ae0','ぶどう']];
const GAME={...META,sprites:['icon','cake'],unit:'点',fullBleed:true,
  bgm:{bpm:100,root:65,scale:'major',prog:[1,6,2,5],seed:48,lead:'triangle',drums:'light',density:.45},
  ranks:[[0,'ガタガタ'],[300,'カット見習い'],[600,'ケーキ屋さん'],[900,'等分マスター'],[1200,'パティシエ'],[1500,'伝説のナイフ']],
  shareText:(v,f)=>`ぴったりケーキカットで ${f}点！`,
  icon(c,x,y,s){this.cake(c,x,y,s*.45,'#f2a5c0',[0,Math.PI*2/3,Math.PI*4/3],0);c.save();c.translate(x+s*.1,y-s*.1);c.rotate(-.6);D.rrect(c,-s*.04,-s*.5,s*.08,s*.4,s*.03,'#b9c3cc',2);D.rrect(c,-s*.05,-s*.12,s*.1,s*.16,s*.03,'#5b4d45',0);c.restore()},
  cake(c,x,y,r,col,cuts,ang){D.ellipse(c,x,y+r*.18,r*1.08,r*.45,'#fbf7f0',2.5);D.ellipse(c,x,y+r*.12,r,r*.4,'#e8d8bd',0);D.circle(c,x,y,r,col);
    for(let i=0;i<8;i++){const a=i*Math.PI/4+.3;D.circle(c,x+Math.cos(a)*r*.72,y+Math.sin(a)*r*.72,r*.07,'#fbf7f0',2)}
    c.lineWidth=3;c.strokeStyle=OL;for(const a of cuts){c.beginPath();c.moveTo(x,y);c.lineTo(x+Math.cos(a)*r,y+Math.sin(a)*r);c.stroke()}
    D.circle(c,x,y,r*.18,'#e2645a',2.5)},
  reset(api){this.st={round:0,cuts:[],need:3,ang:-Math.PI/2,spd:2.2,wait:0,top:TOP[0],t:0,fin:false};api.score=0;this.next()},
  next(){const st=this.st;st.round++;st.cuts=[];st.need=pick(st.round<4?[2,3,4]:st.round<7?[3,4,5,6]:[5,6,7,8]);st.top=TOP[(st.round-1)%TOP.length];st.ang=rnd(0,Math.PI*2);st.spd=1.8+st.round*.22;st.dir=Math.random()<.5?1:-1;st.wait=0},
  down(x,y,api){const st=this.st;if(st.wait>0||st.fin)return;const a=st.ang;st.cuts.push(a);S.swish();api.burst(CX+Math.cos(a)*R,CY+Math.sin(a)*R,{c:['#fff',st.top[0]],n:6,sp:120,r:3});
    if(st.cuts.length>=st.need){this.judge(api)}},
  judge(api){const st=this.st;const cs=st.cuts.slice().sort((a,b)=>a-b);const ideal=Math.PI*2/st.need;let err=0;
    for(let i=0;i<cs.length;i++){const d=((i<cs.length-1?cs[i+1]:cs[0]+Math.PI*2)-cs[i]);err+=Math.abs(d-ideal)}
    const avg=err/cs.length*180/Math.PI;let pts,txt;if(avg<3){pts=150;txt='ぴったり！'}else if(avg<8){pts=110;txt='きれい！'}else if(avg<16){pts=70;txt='まあまあ'}else if(avg<30){pts=30;txt='ガタガタ'}else{pts=0;txt='ぐちゃぐちゃ…'}
    if(pts>=110){api.combo++;pts+=Math.min(api.combo,5)*10}else api.combo=0;api.add(pts);
    api.float(CX,CY-180,txt+(pts?' +'+pts:''),{size:pts>=150?34:26,c:pts>=110?'#e8899a':'#5b4d45',vy:-15,life:1.1});if(pts>=150){S.perfect();api.flash('#fff',.3);api.burst(CX,CY,{c:['#f2a5c0','#f2c84b','#fff'],n:18,sp:240,shape:'s'})}else if(pts>=110)S.good();else if(pts)S.coin();else S.bad();
    st.wait=1.3;st.spread=0},
  update(dt,api){const st=this.st;st.t+=dt;if(st.wait>0){st.wait-=dt;st.spread=Math.min(14,(st.spread||0)+dt*40);if(st.wait<=0){if(st.round>=10){st.fin=true;api.end()}else this.next()}return}
    st.ang+=st.spd*st.dir*dt},
  draw(c,api){const st=this.st;c.fillStyle='#fbeef0';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#f3dde2';for(let y=api.top-((st.t*20)%40);y<api.bottom;y+=40)c.fillRect(0,y,W,2);
    D.rrect(c,CX-110,CY-280,220,56,28,'#fff',3);D.text(c,st.need+'人でわけて！',CX,CY-242,26,'#5b4d45');D.text(c,st.round+'/10 '+st.top[1],CX,CY-300,16,'#5b4d45');
    // cake with spread pieces after judge
    if(st.wait>0&&st.cuts.length){const cs=st.cuts.slice().sort((a,b)=>a-b);c.save();for(let i=0;i<cs.length;i++){const a0=cs[i],a1=i<cs.length-1?cs[i+1]:cs[0]+Math.PI*2;const m=(a0+a1)/2;const ox=Math.cos(m)*st.spread,oy=Math.sin(m)*st.spread;
        c.beginPath();c.moveTo(CX+ox,CY+oy);c.arc(CX+ox,CY+oy,R,a0,a1);c.closePath();c.fillStyle=st.top[0];c.fill();c.lineWidth=3;c.strokeStyle=OL;c.stroke()}c.restore()}
    else this.cake(c,CX,CY,R,st.top[0],st.cuts,st.ang);
    if(st.wait<=0){const a=st.ang;c.save();c.translate(CX+Math.cos(a)*(R+40),CY+Math.sin(a)*(R+40));c.rotate(a+Math.PI/2);D.rrect(c,-7,-5,14,48,5,'#b9c3cc',2.5);D.rrect(c,-9,38,18,26,6,'#5b4d45',0);c.restore();
      c.setLineDash([6,8]);c.lineWidth=2;c.strokeStyle='#e8899a';c.beginPath();c.moveTo(CX,CY);c.lineTo(CX+Math.cos(a)*R,CY+Math.sin(a)*R);c.stroke();c.setLineDash([])}
    if(api.state==='play'&&st.round===1&&st.cuts.length===0)D.text(c,'タップで切る！',CX,CY+200,22,'#5b4d45');
    for(let i=0;i<st.need;i++)D.circle(c,CX-(st.need-1)*12+i*24,CY+210,8,i<st.cuts.length?'#e8899a':'#fff',2.5)},
  __bot(api){const st=this.st;if(st.wait>0||st.fin)return;const ideal=Math.PI*2/st.need;if(st.cuts.length===0){if(Math.random()<.3)this.down(0,0,api);return}
    const want=st.cuts[st.cuts.length-1]+ideal*st.dir;let d=((st.ang-want)%(Math.PI*2)+Math.PI*3)%(Math.PI*2)-Math.PI;if(Math.abs(d)<st.spd*.05)this.down(0,0,api)},
};
