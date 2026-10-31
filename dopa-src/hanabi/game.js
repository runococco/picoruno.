/* はなび打ち上げ：長押しの長さで上昇高さが決まる。ターゲット高さとの差で採点。 */
const N=15,GY=640;
const COLS=['#e2645a','#f2c84b','#7fb2e0','#9cc86a','#f2a5c0','#c49ae0'];
const GAME={...META,sprites:['icon','tube'],unit:'点',fullBleed:true,
  bgm:{bpm:96,root:57,scale:'major',prog:[1,6,4,5],seed:27,lead:'triangle',drums:'light',density:.45},
  ranks:[[0,'しけった花火'],[400,'花火見習い'],[800,'なかなかの花火師'],[1200,'花火の達人'],[1600,'夜空の名人'],[2000,'伝説の花火師']],
  shareText:(v,f)=>`はなび打ち上げで ${f}点！`,
  icon(c,x,y,s){for(let i=0;i<8;i++){const a=i*Math.PI/4;c.lineWidth=3;c.strokeStyle=OL;c.beginPath();c.moveTo(x+Math.cos(a)*s*.12,y-s*.1+Math.sin(a)*s*.12);c.lineTo(x+Math.cos(a)*s*.42,y-s*.1+Math.sin(a)*s*.42);c.stroke();D.circle(c,x+Math.cos(a)*s*.42,y-s*.1+Math.sin(a)*s*.42,s*.07,COLS[i%6])}D.circle(c,x,y-s*.1,s*.1,'#f2c84b')},
  tube(c,x,y,s,charge){D.rrect(c,x-s*.3,y-s*.9,s*.6,s*.95,s*.12,'#8a6a48');D.rrect(c,x-s*.36,y-s*.95,s*.72,s*.2,s*.08,'#a67c52');if(charge>0)D.rrect(c,x-s*.2,y-s*.1-charge*s*.65,s*.4,charge*s*.65,s*.05,'#f2c84b',0);D.face(c,x,y-s*.45,s*.7,charge>0?'o':'smile')},
  reset(api){this.st={n:0,ch:0,hold:false,rk:null,wait:0,target:380,res:[],t:0,parts:[],sky:[]};api.score=0;for(let i=0;i<40;i++)this.st.sky.push([rnd(0,W),rnd(0,500),rnd(1,2.5)])},
  down(){const st=this.st;if(st.rk||st.wait>0||st.n>=N)return;st.hold=true;st.ch=0},
  up(x,y,api){const st=this.st;if(!st.hold)return;st.hold=false;if(st.rk||st.wait>0)return;const h=GY-80-st.ch*560;st.rk={x:W/2,y:GY-80,ty:h,col:pick(COLS),tr:[]};st.n++;S.whoosh();S.noise(.4,{v:.25,f:2500})},
  update(dt,api){const st=this.st;st.t+=dt;if(st.hold)st.ch=Math.min(1,st.ch+dt*.7);
    if(st.wait>0){st.wait-=dt;if(st.wait<=0){st.target=rnd(130,520);if(st.n>=N)api.end()}}
    const r=st.rk;if(r){r.y-=520*dt;r.x+=Math.sin(st.t*9)*12*dt;r.tr.push([r.x,r.y]);if(r.tr.length>12)r.tr.shift();
      if(r.y<=r.ty){const d=Math.abs(r.ty-st.target);let pts,txt;if(d<12){pts=150;txt='ど真ん中！'}else if(d<35){pts=110;txt='いい花火！'}else if(d<80){pts=60;txt='まあまあ'}else{pts=20;txt='ずれた…'}
        if(pts>=110){api.combo++;pts+=Math.min(api.combo,5)*10}else api.combo=0;api.add(pts);st.res.push(pts);
        const big=pts>=150;api.burst(r.x,r.ty,{c:[r.col,'#fff','#f2c84b'],n:big?36:pts>=110?26:14,sp:big?280:200,r:big?6:4,g:120,life:1.1});api.ring(r.x,r.ty,{c:r.col,r:big?140:90,life:.6,lw:5});
        if(big){S.boom();S.fanfare();api.flash('#fff',.3);api.shake(5)}else if(pts>=110){S.boom();api.shake(3)}else{S.pop(.6)}
        api.float(W/2,200,txt+' +'+pts,{size:big?34:26,c:big?'#f2c84b':'#fff'});st.rk=null;st.wait=1.3}}},
  draw(c,api){const st=this.st;c.fillStyle='#1f1d33';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#fff';for(const[x,y,r]of st.sky){c.globalAlpha=.4+.4*Math.sin(st.t*2+x);c.fillRect(x,y,r,r)}c.globalAlpha=1;
    c.fillStyle='#2e2b45';c.fillRect(0,GY-40,W,api.bottom-GY+40);D.ellipse(c,W/2,GY-30,W*.7,30,'#3a3650',0);
    // target ring
    const ty=st.target;c.setLineDash([8,8]);c.lineWidth=3;c.strokeStyle='rgba(255,255,255,.35)';c.beginPath();c.moveTo(0,ty);c.lineTo(W,ty);c.stroke();c.setLineDash([]);
    c.lineWidth=5;c.strokeStyle='#f2c84b';c.beginPath();c.ellipse(W/2,ty,70,26,0,0,Math.PI*2);c.stroke();c.lineWidth=2;c.strokeStyle='#fff';c.beginPath();c.ellipse(W/2,ty,40,14,0,0,Math.PI*2);c.stroke();
    const r=st.rk;if(r){c.lineWidth=3;c.strokeStyle='#f2c84b';c.beginPath();for(let i=0;i<r.tr.length;i++){const[x,y]=r.tr[i];i?c.lineTo(x,y):c.moveTo(x,y)}c.stroke();D.circle(c,r.x,r.y,8,r.col)}
    this.tube(c,W/2,GY-20,60,st.hold?st.ch:0);
    // charge gauge
    if(st.hold){D.rrect(c,W-50,150,20,420,10,'#fff',3);D.rrect(c,W-48,152+416*(1-st.ch),16,416*st.ch,8,'#f2c84b',0)}
    for(let i=0;i<N;i++)D.circle(c,W/2-(N-1)*11+i*22,120,7,i<st.res.length?(st.res[i]>=110?'#f2c84b':st.res[i]>=60?'#fff':'#5b5560'):'rgba(255,255,255,.2)',2);
    if(api.state==='play'&&st.n===0&&!st.hold)D.text(c,'長押しでつめて、はなす！',W/2,GY-130,20,'#fff')},
  __bot(api){const st=this.st;if(st.rk||st.wait>0||st.n>=N)return;const need=(GY-80-st.target)/560;if(!st.hold){this.down()}else if(st.ch>=need-.02)this.up(0,0,api)},
};
