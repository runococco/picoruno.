/* あまい？しょっぱい？：左右ふりわけ。食べものはすべて図形で描く。 */
const CX=W/2,CY=330;
const FOODS=[
  ['ケーキ',0],['ドーナツ',0],['プリン',0],['ソフトクリーム',0],['キャンディ',0],['チョコ',0],['マカロン',0],['ホットケーキ',0],
  ['ポテチ',1],['せんべい',1],['ソーセージ',1],['うめぼし',1],['フライドポテト',1],['えだまめ',1],['ハンバーガー',1],['しおラーメン',1]];
const GAME={...META,time:30,unit:'点',
  bgm:{bpm:150,root:65,scale:'major',prog:[1,4,5,4],seed:33,lead:'square',drums:'four',density:.65},
  ranks:[[0,'まだおなかすいてない'],[30,'つまみぐい'],[70,'食いしんぼう'],[120,'ふりわけ名人'],[180,'味覚のプロ'],[250,'ベロが光速']],
  shareText:(v,f)=>`あまい？しょっぱい？で ${f}点！`,
  icon(c,x,y,s){this.food(c,0,x-s*.2,y,s*.5);this.food(c,8,x+s*.22,y+s*.04,s*.45)},
  food(c,i,x,y,s){c.save();c.translate(x,y);const k=s/100,lw=Math.max(2,3.5*k);
    const P=(fn,f)=>D.path(c,fn,f,lw);
    switch(i){
    case 0:P(c=>{c.moveTo(-45*k,30*k);c.lineTo(45*k,30*k);c.lineTo(45*k,-10*k);c.lineTo(-45*k,-30*k);c.closePath()},'#fff8ec');c.fillStyle='#f6b6c4';c.fillRect(-43*k,5*k,86*k,8*k);D.circle(c,-10*k,-34*k,12*k,'#e2645a',lw);break;
    case 1:D.circle(c,0,0,42*k,'#d9a066',lw);P(c=>{for(let a=0;a<12;a++){const t=a/12*Math.PI*2,r=(a%2?30:36)*k;c.lineTo(Math.cos(t)*r,Math.sin(t)*r-2*k)}c.closePath()},'#f3b0c3');D.circle(c,0,-2*k,12*k,'#fbefe6',lw);break;
    case 2:P(c=>{c.moveTo(-30*k,-20*k);c.lineTo(30*k,-20*k);c.lineTo(42*k,30*k);c.lineTo(-42*k,30*k);c.closePath()},'#f6d77a');P(c=>{c.moveTo(-30*k,-20*k);c.lineTo(30*k,-20*k);c.lineTo(33*k,-8*k);c.lineTo(-33*k,-8*k);c.closePath()},'#9a5a32');D.ellipse(c,0,32*k,52*k,8*k,'#fff',lw);break;
    case 3:P(c=>{c.moveTo(-24*k,0);c.lineTo(24*k,0);c.lineTo(0,50*k);c.closePath()},'#e8b770');D.ellipse(c,0,-8*k,30*k,16*k,'#fff8ec',lw);D.ellipse(c,0,-24*k,22*k,13*k,'#fff8ec',lw);P(c=>{c.moveTo(-8*k,-34*k);c.quadraticCurveTo(0,-52*k,6*k,-46*k)},'#fff8ec');break;
    case 4:P(c=>{c.moveTo(-34*k,0);c.lineTo(-55*k,-16*k);c.lineTo(-55*k,16*k);c.closePath();c.moveTo(34*k,0);c.lineTo(55*k,-16*k);c.lineTo(55*k,16*k);c.closePath()},'#f3c84b');D.circle(c,0,0,34*k,'#e98fa6',lw);break;
    case 5:D.rrect(c,-40*k,-30*k,80*k,60*k,6*k,'#8a5a3c',lw);c.strokeStyle='#6f4630';c.lineWidth=lw*.7;c.beginPath();c.moveTo(0,-28*k);c.lineTo(0,28*k);c.moveTo(-38*k,0);c.lineTo(38*k,0);c.stroke();break;
    case 6:D.ellipse(c,0,-16*k,40*k,16*k,'#bfe3c9',lw);D.rrect(c,-36*k,-6*k,72*k,12*k,6*k,'#fff8ec',lw);D.ellipse(c,0,16*k,40*k,16*k,'#bfe3c9',lw);break;
    case 7:for(let n=2;n>=0;n--)D.rrect(c,-44*k,-18*k+n*14*k,88*k,18*k,9*k,'#e3a656',lw);D.rrect(c,-10*k,-28*k,20*k,10*k,3*k,'#f8e08e',lw);break;
    case 8:P(c=>{for(let a=0;a<=20;a++){const t=a/20*Math.PI*2,r=(38+(a%2?3:-3))*k;c.lineTo(Math.cos(t)*r*1.1,Math.sin(t)*r*.8)}c.closePath()},'#f6d77a');break;
    case 9:D.circle(c,0,0,40*k,'#c98f55',lw);D.rrect(c,-40*k,-10*k,80*k,20*k,2*k,'#3f5a3c',0);c.lineWidth=lw;c.strokeStyle=OL;c.beginPath();c.arc(0,0,40*k,0,7);c.stroke();break;
    case 10:D.rrect(c,-50*k,-17*k,100*k,34*k,17*k,'#d9785a',lw);c.strokeStyle=OL;c.lineWidth=lw*.7;for(const sx of[-34,34]){c.beginPath();c.moveTo(sx*k-6*k,-10*k);c.lineTo(sx*k+6*k,-2*k);c.stroke()}break;
    case 11:D.circle(c,0,0,36*k,'#d84a4a',lw);P(c=>{c.moveTo(-4*k,-36*k);c.quadraticCurveTo(4*k,-50*k,14*k,-48*k)},'#7cb35f');break;
    case 12:for(let n=-2;n<=2;n++)D.rrect(c,n*12*k-5*k,-45*k+Math.abs(n)*6*k,10*k,40*k,3*k,'#f3cf6a',lw*.8);P(c=>{c.moveTo(-36*k,-15*k);c.lineTo(36*k,-15*k);c.lineTo(28*k,40*k);c.lineTo(-28*k,40*k);c.closePath()},'#e2645a');break;
    case 13:P(c=>{c.moveTo(-50*k,0);c.bezierCurveTo(-40*k,-30*k,40*k,-30*k,50*k,0);c.bezierCurveTo(40*k,24*k,-40*k,24*k,-50*k,0)},'#8fc56c');for(const bx of[-24,0,24])D.circle(c,bx*k,-2*k,10*k,'#b5dc8f',lw*.7);break;
    case 14:D.path(c,c=>{c.moveTo(-44*k,-6*k);c.bezierCurveTo(-44*k,-48*k,44*k,-48*k,44*k,-6*k);c.closePath()},'#e3a656',lw);D.rrect(c,-48*k,-6*k,96*k,12*k,6*k,'#8fc56c',lw);D.rrect(c,-46*k,4*k,92*k,14*k,7*k,'#8a5a3c',lw);D.rrect(c,-44*k,16*k,88*k,18*k,8*k,'#e3a656',lw);break;
    case 15:D.path(c,c=>{c.moveTo(-50*k,-6*k);c.lineTo(50*k,-6*k);c.bezierCurveTo(48*k,40*k,-48*k,40*k,-50*k,-6*k)},'#fff8ec',lw);D.ellipse(c,0,-6*k,50*k,10*k,'#f3e3b4',lw);c.strokeStyle='#e8c46a';c.lineWidth=lw*.8;for(let n=-2;n<=2;n++){c.beginPath();c.moveTo(n*12*k-10*k,-8*k);c.quadraticCurveTo(n*12*k,-4*k,n*12*k+10*k,-8*k);c.stroke()}D.circle(c,18*k,-8*k,8*k,'#f2c7d3',lw*.6);break;
    }
    const fy=[6,26,12,-10,0,0,-14,-2,0,8,0,4,14,10,8,12][i];D.face(c,0,fy*k,s*.42,'smile');c.restore()},
  reset(api){this.st={cur:null,fly:[],px:null,py:null,feverT:0,cnt:0,last:-1};this.next();api.score=0},
  next(){const st=this.st;let i;do i=rndi(0,FOODS.length-1);while(i===st.last);st.last=i;st.cur={i,t:0}},
  sort(dir,api){const st=this.st;if(!st.cur||st.cur.t<.06)return;const f=FOODS[st.cur.i],ok=(dir===0&&f[1]===0)||(dir===1&&f[1]===1);
    st.fly.push({i:st.cur.i,x:CX,y:CY,vx:dir?620:-620,vy:-300,t:0,ok});
    if(ok){api.combo++;const p=1+Math.floor(api.combo/10)+(st.feverT>0?2:0);api.score+=p;S.pop(1+Math.min(api.combo,30)*.03);S.good(1+Math.min(api.combo,30)*.02);api.float(dir?W-90:90,500,'+'+p,{size:24,c:dir?'#7fb6d8':'#f3a6bd'});
      if(api.combo%20===0){st.feverT=5;api.fever=true;api.bgmRate=1.2;S.fanfare();api.flash('#fff',.4);api.float(CX,200,'フィーバー！',{size:40,c:'#f3c84b'})}}
    else{api.combo=0;api.timeLeft=Math.max(0,api.timeLeft-2);S.bad();api.shake(10);api.flash('#e2645a',.25);api.float(CX,CY-90,f[0]+'は'+(f[1]?'しょっぱい':'あまい')+'！ -2秒',{size:22,c:'#e2645a',life:1.1})}
    this.next()},
  down(x,y){this.st.px=x;this.st.py=y},
  up(x,y,api){const st=this.st;if(st.px===null)return;const dx=x-st.px;st.px=null;if(Math.abs(dx)>25)this.sort(dx>0?1:0,api);else this.sort(x>W/2?1:0,api)},
  key(k,api){if(k==='ArrowLeft'||k==='a'||k==='f')this.sort(0,api);if(k==='ArrowRight'||k==='d'||k==='j')this.sort(1,api)},
  update(dt,api){const st=this.st;if(st.cur)st.cur.t+=dt;
    if(st.feverT>0){st.feverT-=dt;if(st.feverT<=0){api.fever=false;api.bgmRate=1}}
    for(const f of st.fly){f.t+=dt;f.vy+=1500*dt;f.x+=f.vx*dt;f.y+=f.vy*dt}st.fly=st.fly.filter(f=>f.t<.5)},
  draw(c,api){const st=this.st;c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.fillStyle='#f9e1d3';c.fillRect(0,0,W/2,H);c.fillStyle='#e3eef4';c.fillRect(W/2,0,W/2,H);
    D.rrect(c,24,540,150,120,26,'#f3a6bd',4);D.text(c,'あまい',99,600,28,'#fff','center',OL,6);D.text(c,'←',99,560,22,'#fff','center',OL,5);
    D.rrect(c,W-174,540,150,120,26,'#7fb6d8',4);D.text(c,'しょっぱい',W-99,600,24,'#fff','center',OL,6);D.text(c,'→',W-99,560,22,'#fff','center',OL,5);
    if(st.cur){const s=ease.outBack(Math.min(1,st.cur.t*6));D.circle(c,CX,CY,100*s+1,'#fffdf8',4);this.food(c,st.cur.i,CX,CY,130*s+1);D.text(c,FOODS[st.cur.i][0],CX,CY+130,22,'#4a3428')}
    for(const f of st.fly){c.globalAlpha=1-f.t*2;this.food(c,f.i,f.x,f.y,90*(1-f.t));c.globalAlpha=1}
  },
  __bot(api){const st=this.st;if(st.cur&&st.cur.t>.25){const f=FOODS[st.cur.i];this.sort(Math.random()<.9?f[1]:1-f[1],api)}},
};
