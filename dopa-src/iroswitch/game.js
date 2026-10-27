/* いろいろくぐり：Color Switch 系。輪（回転）とバー（横スライド）、虹玉で色替え。 */
const COLS=['#e2645a','#f3c84b','#5fb4c4','#9a83c9'],BXX=W/2,BRAD=13,GAPY=360;
const GAME={...META,unit:'点',
  bgm:{bpm:128,root:62,scale:'minor',prog:[6,4,1,5],seed:21,lead:'square',drums:'four',density:.6},
  ranks:[[0,'色迷子'],[5,'色見習い'],[12,'カラフル跳び'],[22,'虹のぼり'],[35,'色の支配者'],[55,'レインボーの化身']],
  shareText:(v,f)=>`いろいろくぐりで ${f}点！`,
  icon(c,x,y,s){this.ring(c,x,y,s*.38,s*.07,.4);this.ball(c,x,y+s*.05,s*.12,3)},
  ring(c,x,y,r,th,rot){for(let i=0;i<4;i++){c.lineWidth=th+5;c.strokeStyle=OL;c.lineCap='butt';c.beginPath();c.arc(x,y,r,rot+i*Math.PI/2,rot+(i+1)*Math.PI/2);c.stroke();c.lineWidth=th;c.strokeStyle=COLS[i];c.beginPath();c.arc(x,y,r,rot+i*Math.PI/2+.012,rot+(i+1)*Math.PI/2-.012);c.stroke()}},
  ball(c,x,y,r,ci){D.circle(c,x,y,r,COLS[ci],Math.max(2,r*.2));D.face(c,x,y+r*.1,r*1.2,'smile')},
  reset(api){this.st={y:560,vy:0,ci:0,cam:0,obs:[],nextY:330,started:false,dead:false};for(let i=0;i<4;i++)this.addObs();api.score=0},
  addObs(){const st=this.st,n=st.obs.length,lvl=Math.floor(n/2);const y=st.nextY;st.nextY-=GAPY;
    const type=n<2?'ring':pick(['ring','ring','bar','double']);
    st.obs.push({y,type,rot:rnd(6),sp:(1.4+Math.min(lvl,14)*.1)*(Math.random()<.5?1:-1),r:type==='double'?110:95,off:rnd(W),bsp:(110+lvl*8)*(Math.random()<.5?1:-1),star:true,sw:true})},
  flap(api){const st=this.st;st.started=true;st.vy=-440;S.tone(500+st.ci*80,.08,{type:'triangle',v:.2,to:900})},
  down(x,y,api){this.flap(api)},key(k,api){if(k===' '||k==='ArrowUp')this.flap(api)},
  segAt(o,by){// ボールの位置での色
    if(o.type==='bar'){const x=((BXX-o.off)%W+W)%W;return Math.floor(x/(W/4))}
    const ang=(by<o.y?-Math.PI/2:Math.PI/2)-o.rot;const a=((ang%(Math.PI*2))+Math.PI*2)%(Math.PI*2);return Math.floor(a/(Math.PI/2))%4},
  hitTest(o,by){if(o.type==='bar')return Math.abs(by-o.y)<9+BRAD;
    const rs=o.type==='double'?[o.r,o.r-40]:[o.r];for(const r of rs)if(Math.abs(Math.abs(by-o.y)-r)<9+BRAD-2)return true;return false},
  update(dt,api){const st=this.st;
    if(st.started){st.vy=Math.min(700,st.vy+1350*dt);st.y+=st.vy*dt}
    st.cam=Math.min(st.cam,st.y-430);
    for(const o of st.obs){o.rot+=o.sp*dt;o.off+=o.bsp*dt;
      if(o.star&&Math.abs(st.y-o.y)<BRAD+14){o.star=false;api.score++;S.coin(1+api.score*.01);api.burst(BXX,o.y-st.cam,{c:['#fff','#f3c84b'],n:10,sp:200,shape:'star',r:4});api.float(BXX+50,o.y-st.cam,'+1',{size:22})}
      const sy=o.y-GAPY/2;if(o.sw&&Math.abs(st.y-sy)<BRAD+14){o.sw=false;let n;do n=rndi(0,3);while(n===st.ci);st.ci=n;S.perfect(1.1);api.ring(BXX,sy-st.cam,{c:COLS[n],r:60});api.flash(COLS[n],.15)}
      if(this.hitTest(o,st.y)){const seg=this.segAt(o,st.y);// 内側の輪は左右反転なので、真上・真下の色は外側と同じ式で求まる
        if(seg!==st.ci)return this.die(api)}}
    if(st.obs[st.obs.length-1].y>st.cam-200)this.addObs();
    st.obs=st.obs.filter(o=>o.y-st.cam<H+200);
    if(st.y-st.cam>H+20&&st.started)this.die(api)},
  die(api){const st=this.st;if(st.dead)return;st.dead=true;S.boom();api.shake(14);api.flash('#fff',.5);api.burst(BXX,st.y-st.cam,{c:COLS,n:40,sp:420,r:6});api.end()},
  overText:'ぶつかった！',
  draw(c,api){const st=this.st;c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.fillStyle='rgba(255,255,255,.05)';for(let i=0;i<12;i++){const y=((i*90-st.cam*.3)%H+H)%H;c.fillRect(0,y,W,40)}
    c.save();c.translate(0,-st.cam);
    for(const o of st.obs){
      if(o.type==='bar'){for(let k=-1;k<5;k++){const x=((o.off%W)+W)%W+k*W/4-W;for(let m=0;m<2;m++){const xx=x+m*W;D.rrect(c,xx+1,o.y-9,W/4-2,18,6,COLS[((k%4)+4)%4],3)}}}
      else{this.ring(c,BXX,o.y,o.r,18,o.rot);if(o.type==='double'){c.save();c.translate(BXX,o.y);c.scale(-1,1);this.ring(c,0,0,o.r-40,14,o.rot);c.restore()}}
      if(o.star)D.star(c,BXX,o.y,14,'#fffdf8',3,api.t);
      if(o.sw){const sy=o.y-GAPY/2;for(let i=0;i<4;i++){c.fillStyle=COLS[i];c.beginPath();c.moveTo(BXX,sy);c.arc(BXX,sy,13,i*Math.PI/2+api.t*3,(i+1)*Math.PI/2+api.t*3);c.fill()}c.lineWidth=3;c.strokeStyle=OL;c.beginPath();c.arc(BXX,sy,13,0,7);c.stroke()}}
    if(!st.dead)this.ball(c,BXX,st.y,BRAD,st.ci);
    c.restore();
    if(!st.started&&api.state==='play')D.text(c,'タップでスタート',W/2,640,22,'#fff','center',OL,6);
  },
  __bot(api){const st=this.st;if(!st.started){this.flap(api);return}
    const o=st.obs.find(o=>o.y<st.y+20);if(!o){if(st.vy>0)this.flap(api);return}
    const near=Math.abs(st.y-o.y)-o.r;const nextSeg=this.segAt(o,st.y-80);if(st.vy>200||(o.y>st.y-o.r-70&&st.vy>0)||(st.y-st.cam>520))this.flap(api)},
};
