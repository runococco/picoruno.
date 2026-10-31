/* ぐるぐるソフトクリーム：クリーム段を積む。各段の中心オフセットの合計が傾きになる。 */
const CONEX=W/2,CONEY=600,SEG=14;
const GAME={...META,sprites:['icon','cone','cream'],unit:'点',fullBleed:true,comboHud:false,
  bgm:{bpm:120,root:64,scale:'major',prog:[1,6,4,5],seed:17,lead:'square',drums:'pop',density:.55},
  ranks:[[0,'ポタッ'],[150,'ソフト見習い'],[400,'ぐるぐる上手'],[800,'ソフト職人'],[1400,'タワーの達人'],[2200,'ソフトクリームの神']],
  shareText:(v,f)=>`ぐるぐるソフトクリームで ${f}点！`,
  icon(c,x,y,s){this.cone(c,x,y+s*.45,s*.55);for(let i=0;i<4;i++)this.cream(c,x+(i%2?s*.03:-s*.03),y+s*.1-i*s*.12,s*.26-i*s*.03,'#fffaf0')},
  cone(c,x,y,s){D.poly(c,[[x-s*.42,y-s*.75],[x+s*.42,y-s*.75],[x,y]],'#e3b47a');c.strokeStyle='#c98a5b';c.lineWidth=2;for(let i=1;i<4;i++){c.beginPath();c.moveTo(x-s*.42+i*s*.2,y-s*.75);c.lineTo(x-s*.05+i*s*.03,y-s*.12);c.stroke()}},
  cream(c,x,y,r,col){D.ellipse(c,x,y,r,r*.62,col,3)},
  reset(api){this.st={segs:[],pouring:false,cur:0,tx:CONEX,ox:0,tilt:0,vt:0,fall:0,order:rndi(8,14),col:pick(['#fffaf0','#f7c9d4','#d5a97a','#bcd99c']),done:0,scoreT:0};api.score=0},
  down(x,y){const st=this.st;if(st.fall)return;st.pouring=true;st.tx=x;S.noise(.3,{v:.12,f:900,type:'lowpass'})},
  move(x){this.st.tx=x},up(){this.st.pouring=false},
  key(k,api){const st=this.st;if(k===' ')this.down(st.tx,0);if(k==='ArrowLeft')st.tx-=12;if(k==='ArrowRight')st.tx+=12},keyUp(k){if(k===' ')this.up()},keyRepeat:true,
  update(dt,api){const st=this.st;if(st.fall){st.fall+=dt;st.tilt+=st.vt*dt;st.vt+=6*dt*Math.sign(st.tilt||1);if(st.fall>1.2)api.end();return}
    st.ox+=(clamp(st.tx-CONEX,-60,60)-st.ox)*Math.min(1,dt*8);
    if(st.pouring){st.cur+=dt*4;if(st.cur>=1){st.cur=0;const n=st.segs.length;st.segs.push({off:st.ox*.5+rnd(-3,3),r:Math.max(14,34-n*1.2)});S.tone(400+n*30,.06,{type:'sine',v:.12});api.add(10);
        if(n+1===st.order){api.add(100);S.perfect();api.flash('#fff',.3);api.float(CONEX,200,'注文どおり！ +100',{size:28,c:'#f3c84b'})}}}
    // 傾き：各段のオフセットの加重和
    let m=0;st.segs.forEach((s,i)=>m+=s.off*(i+1));const n=st.segs.length;const lean=n?m/(n*n*8):0;st.vt+=(lean*2.5-st.tilt*3)*dt;st.vt*=1-dt*2;st.tilt+=st.vt*dt;
    if(Math.abs(st.tilt)>.5&&n>2){st.fall=.01;st.pouring=false;S.bad();S.boom();api.shake(10);api.float(CONEX,300,'ぐしゃっ…',{size:36,c:'#fff'});
      const bonus=n*5;api.add(bonus)}
    if(!st.pouring&&n>0){st.scoreT+=dt}else st.scoreT=0;
    if(n>=40){api.add(500);S.fanfare();api.end()}},
  drawHud(c,api){const st=this.st;D.rrect(c,70,20,280,56,28,'#fffdf8',3.5);D.text(c,api.score+'点　注文 '+st.order+'段　いま'+st.segs.length+'段',W/2,48,19,'#5b4d45');
    const k=clamp(st.tilt/.5,-1,1);D.rrect(c,110,86,200,12,6,'#fffdf8',2.5);c.fillStyle=Math.abs(k)>.7?'#e2645a':'#9cc86a';c.fillRect(k<0?210+100*k:210,87,Math.abs(100*k),10);c.fillStyle=OL;c.fillRect(209,84,2,16)},
  draw(c,api){const st=this.st;c.fillStyle='#fbe8ee';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#f6dde5';for(let i=0;i<14;i++)c.fillRect(0,api.top+i*60,W,20);
    D.rrect(c,20,CONEY+20,W-40,80,20,'#e0789a',4);D.text(c,'注文：'+st.order+'段',W/2,CONEY+60,22,'#fffdf8','center',OL,5);
    // ノズル
    D.rrect(c,st.tx-24,100,48,50,10,'#b9c3cc');D.rrect(c,st.tx-10,150,20,18,4,'#8a8392');
    if(st.pouring){const k=st.cur;D.ellipse(c,st.tx,170+k*30,12,8+k*6,st.col)}
    c.save();c.translate(CONEX,CONEY);c.rotate(st.tilt);this.cone(c,0,0,120);
    st.segs.forEach((s,i)=>{const y=-92-i*SEG,x=s.off*.5;this.cream(c,x,y,s.r,st.col)});
    if(st.segs.length){const t=st.segs[st.segs.length-1];D.ellipse(c,t.off*.5,-92-(st.segs.length-1)*SEG-8,t.r*.6,t.r*.45,st.col);D.face(c,t.off*.5,-92-(st.segs.length-1)*SEG-6,t.r)}
    c.restore();
    if(api.t<3&&api.state==='play')D.text(c,'おしてクリームを出す・左右でバランス',W/2,230,16,'#5b4d45','center','#fffdf8',5)},
  __bot(api){const st=this.st;if(st.fall)return;if(!st.pouring)this.down(CONEX,0);st.tx=CONEX-st.tilt*300+rnd(-10,10);if(st.segs.length>=st.order+rndi(0,6))this.up()},
};
