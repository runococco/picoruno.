/* カリカリかたぬき：点線に沿ってゆっくりなぞる。速すぎると割れる。 */
const CX=W/2,CY=420,SHAPES=[
  {n:'まる',pts:t=>[CX+Math.cos(t)*110,CY+Math.sin(t)*110]},
  {n:'ハート',pts:t=>{const x=16*Math.pow(Math.sin(t),3),y=13*Math.cos(t)-5*Math.cos(2*t)-2*Math.cos(3*t)-Math.cos(4*t);return[CX+x*7,CY-y*7+10]}},
  {n:'ほし',pts:t=>{const k=t/(Math.PI*2)*10,i=Math.floor(k),f=k-i,a0=-Math.PI/2+i*Math.PI/5,a1=a0+Math.PI/5,r0=i%2?55:125,r1=(i+1)%2?55:125;return[lerp(CX+Math.cos(a0)*r0,CX+Math.cos(a1)*r1,f),lerp(CY+Math.sin(a0)*r0,CY+Math.sin(a1)*r1,f)]}},
  {n:'さかな',pts:t=>{const a=t;if(a<Math.PI*1.5)return[CX-20+Math.cos(a*4/3)*100,CY+Math.sin(a*4/3)*65];const f=(a-Math.PI*1.5)/(Math.PI*.5);const seq=[[CX+80,CY],[CX+140,CY-60],[CX+140,CY+60],[CX+80,CY]];const k=f*3,i=Math.min(2,Math.floor(k)),g=k-i;return[lerp(seq[i][0],seq[i+1][0],g),lerp(seq[i][1],seq[i+1][1],g)]}},
  {n:'ねこ',pts:t=>{const k=t/(Math.PI*2);const P=[[CX-100,CY+80],[CX-100,CY-30],[CX-110,CY-110],[CX-50,CY-60],[CX+50,CY-60],[CX+110,CY-110],[CX+100,CY-30],[CX+100,CY+80]];const n=P.length,kk=k*n,i=Math.floor(kk)%n,g=kk-Math.floor(kk);return[lerp(P[i][0],P[(i+1)%n][0],g),lerp(P[i][1],P[(i+1)%n][1],g)]}},
];
const NP=120;
const GAME={...META,sprites:['icon','needle'],unit:'枚',hudUnit:true,fullBleed:true,comboHud:false,
  bgm:{bpm:92,root:64,scale:'major',prog:[1,6,4,5],seed:31,lead:'triangle',drums:'none',density:.4,stab:false},
  ranks:[[0,'パキッ'],[1,'かたぬきデビュー'],[2,'そーっと上手'],[3,'かたぬき職人'],[4,'ゆびさきの魔術師'],[5,'屋台のレジェンド']],
  shareText:(v,f)=>`カリカリかたぬきで ${f}枚 ぬけた！`,
  icon(c,x,y,s){D.rrect(c,x-s*.42,y-s*.3,s*.84,s*.6,s*.06,'#f2c9a0');c.setLineDash([6,6]);c.lineWidth=3;c.strokeStyle=OL;c.beginPath();c.arc(x,y,s*.18,0,7);c.stroke();c.setLineDash([]);this.needle(c,x+s*.2,y+s*.12,s*.4)},
  needle(c,x,y,s){c.save();c.translate(x,y);c.rotate(.6);D.rrect(c,-s*.06,-s*.9,s*.12,s*.9,s*.05,'#b9c3cc');D.rrect(c,-s*.12,-s*.15,s*.24,s*.45,s*.08,'#e2645a');c.restore()},
  reset(api){this.st={lv:0,path:[],done:[],drag:null,crack:0,fails:0,win:0,lx:0,ly:0,sp:0,cleared:0};this.load();api.score=0},
  load(){const st=this.st;const S0=SHAPES[st.lv%SHAPES.length];st.path=[];for(let i=0;i<NP;i++)st.path.push(S0.pts(i/NP*Math.PI*2));st.done=new Array(NP).fill(false);st.crack=0;st.win=0;st.name=S0.n;st.hp=1},
  down(x,y){this.st.drag={};this.st.lx=x;this.st.ly=y;this.st.sp=0},
  move(x,y,api){const st=this.st;if(!st.drag||st.win||st.crack)return;const d=dist(x,y,st.lx,st.ly);st.sp=st.sp*.6+d*.4;st.lx=x;st.ly=y;
    if(st.sp>13){st.hp-=(st.sp-13)*.02;if(st.hp<=0){this.crackIt(api);return}}else st.hp=Math.min(1,st.hp+.01);
    let near=false;for(let i=0;i<NP;i++){if(!st.done[i]&&dist(x,y,st.path[i][0],st.path[i][1])<16){st.done[i]=true;near=true;S.noise(.03,{v:.25,f:rnd(3000,5000),type:'highpass'});if(Math.random()<.4)api.burst(x,y,{c:'#f2c9a0',n:2,sp:60,r:2,g:300})}}
    const n=st.done.filter(Boolean).length;if(n>=NP-2){this.winIt(api)}},
  up(){this.st.drag=null},
  crackIt(api){const st=this.st;st.crack=1;st.fails++;S.noise(.25,{v:.6,f:2000});S.bad();api.shake(10);api.float(W/2,CY,'パキッ！',{size:44,c:'#fff'});},
  winIt(api){const st=this.st;st.win=1;st.cleared++;api.score=st.cleared;S.fanfare();api.flash('#fff',.4);api.float(W/2,CY-180,st.name+'、成功！',{size:34,c:'#f3c84b'});api.burst(CX,CY,{c:['#f2c9a0','#fff','#f4d66d'],n:24,shape:'star',sp:260})},
  update(dt,api){const st=this.st;if(st.crack){st.crack+=dt;if(st.crack>1.5){if(st.fails>=3){api.end();return}this.load()}}if(st.win){st.win+=dt;if(st.win>1.6){st.lv++;this.load()}}},
  drawHud(c,api){const st=this.st;D.rrect(c,70,20,280,56,28,'#fffdf8',3.5);D.text(c,api.score+'枚　'+st.name+'　ミス'+st.fails+'/3',W/2,48,20,'#5b4d45');
    D.rrect(c,110,86,200,12,6,'#fffdf8',2.5);const k=clamp(st.hp,0,1);D.rrect(c,111,87,198*k,10,5,k<.4?'#e2645a':'#9cc86a',0)},
  draw(c,api){const st=this.st;c.fillStyle='#c98a5b';c.fillRect(0,api.top,W,api.bottom-api.top);
    const cr=st.crack?Math.min(1,st.crack*3):0;c.save();if(cr)c.translate(rnd(-2,2)*(1-cr),0);
    D.rrect(c,40,200,W-80,440,10,'#f2c9a0',4);
    c.setLineDash([5,5]);c.lineWidth=2;c.strokeStyle='#8e6a4e';c.beginPath();st.path.forEach((p,i)=>i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]));c.closePath();c.stroke();c.setLineDash([]);
    c.lineWidth=7;c.strokeStyle='#c98a5b';c.lineCap='round';for(let i=0;i<NP;i++){if(!st.done[i])continue;const a=st.path[i],b=st.path[(i+1)%NP];c.beginPath();c.moveTo(a[0],a[1]);c.lineTo(b[0],b[1]);c.stroke()}
    if(st.win){const k=Math.min(1,st.win*2);c.save();c.translate(0,-k*60);c.globalAlpha=1-k*.3;D.path(c,c=>{st.path.forEach((p,i)=>i?c.lineTo(p[0],p[1]):c.moveTo(p[0],p[1]));c.closePath()},'#f2c9a0',3);c.restore()}
    if(cr){c.lineWidth=4;c.strokeStyle=OL;c.beginPath();c.moveTo(CX-30,CY-150);c.lineTo(CX+10,CY-40);c.lineTo(CX-20,CY+30);c.lineTo(CX+30,CY+150);c.stroke()}
    c.restore();
    if(st.drag&&!st.win)this.needle(c,st.lx,st.ly,70);
    if(api.t<4&&api.state==='play')D.text(c,'点線の上を、ゆっくりなぞる',W/2,170,18,'#fffdf8','center',OL,5)},
  __bot(api){const st=this.st;if(st.win||st.crack)return;const i=st.done.findIndex(v=>!v);if(i<0)return;const p=st.path[i];if(!st.drag){this.down(p[0],p[1]);return}this.move(lerp(st.lx,p[0],.5),lerp(st.ly,p[1],.5),api)},
};
