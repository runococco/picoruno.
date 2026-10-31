/* ぱくぱくホール：穴を動かして小さいものから飲み込む（Hole.io 系）。のむほど穴が育つ。 */
const WW=1100,WH=1700;
const KIND=[
  {n:'あめ',r:9,p:1,c:'#f2a5b5'},{n:'クッキー',r:13,p:2,c:'#dcae78'},{n:'マカロン',r:17,p:3,c:'#a9d6c6'},{n:'ドーナツ',r:22,p:5,c:'#f0c27a'},
  {n:'カップケーキ',r:29,p:8,c:'#f7c9d4'},{n:'プリン',r:37,p:12,c:'#f4d66d'},{n:'ケーキ',r:50,p:20,c:'#fffaf0'},{n:'おかしの家',r:68,p:35,c:'#e9b98d'},{n:'ケーキの塔',r:92,p:60,c:'#f3d3df'}];
const GAME={...META,sprites:['icon','item'],unit:'点',time:60,fullBleed:true,
  bgm:{bpm:124,root:57,scale:'major',prog:[1,6,4,5],seed:41,lead:'square',drums:'pop',density:.6},
  ranks:[[0,'ちいさな穴'],[300,'おなかペコペコ'],[800,'くいしんぼう'],[1500,'町のおそうじ係'],[2500,'おかしの町のぬし'],[4000,'ブラックホール級']],
  shareText:(v,f)=>`ぱくぱくホールで ${f}点 のみこんだ！`,
  icon(c,x,y,s){D.ellipse(c,x,y+s*.15,s*.42,s*.24,'#4b3e37');this.item(c,x-s*.05,y-s*.02,s*.2,4,.4);this.item(c,x+s*.28,y-s*.28,s*.1,0,0);this.item(c,x-s*.32,y-s*.3,s*.13,3,0)},
  // k=種類 t=アニメ角度
  item(c,x,y,r,k,rot=0){c.save();c.translate(x,y);c.rotate(rot);const lw=Math.max(2,r*.12),K=KIND[k];
    if(k===0){D.circle(c,0,0,r,K.c,lw);D.poly(c,[[-r,0],[-r*1.7,-r*.6],[-r*1.7,r*.6]],K.c,lw);D.poly(c,[[r,0],[r*1.7,-r*.6],[r*1.7,r*.6]],K.c,lw)}
    else if(k===1){D.circle(c,0,0,r,K.c,lw);c.fillStyle='#8a5a3c';for(const[a,b]of[[-.4,-.3],[.35,-.1],[-.1,.4],[.3,.45]]){c.beginPath();c.arc(a*r,b*r,r*.13,0,7);c.fill()}}
    else if(k===2){D.ellipse(c,0,-r*.35,r,r*.45,K.c,lw);D.rrect(c,-r*.8,-r*.12,r*1.6,r*.28,r*.14,'#fffaf0',lw*.7);D.ellipse(c,0,r*.38,r,r*.45,K.c,lw)}
    else if(k===3){D.circle(c,0,0,r,K.c,lw);D.path(c,c=>{c.arc(0,0,r*.8,Math.PI*1.05,Math.PI*1.95);c.arc(0,0,r*.45,Math.PI*1.95,Math.PI*1.05,true);c.closePath()},'#f2a5b5',0);D.circle(c,0,0,r*.32,'#efe4d2',lw)}
    else if(k===4){D.poly(c,[[-r*.75,0],[r*.75,0],[r*.55,r*.9],[-r*.55,r*.9]],'#a9c7e6',lw);D.ellipse(c,0,-r*.1,r*.9,r*.6,K.c,lw);D.circle(c,0,-r*.75,r*.22,'#e2645a',lw*.8);D.face(c,0,r*.42,r*.7)}
    else if(k===5){D.poly(c,[[-r*.6,-r*.55],[r*.6,-r*.55],[r*.95,r*.7],[-r*.95,r*.7]],K.c,lw);D.path(c,c=>{c.moveTo(-r*.6,-r*.55);c.lineTo(r*.6,-r*.55);c.lineTo(r*.66,-r*.25);c.quadraticCurveTo(0,-r*.05,-r*.66,-r*.25);c.closePath()},'#9a6243',lw*.8);D.face(c,0,r*.25,r*.8)}
    else if(k===6){D.rrect(c,-r*.9,-r*.3,r*1.8,r*1,r*.15,K.c,lw);D.rrect(c,-r*.9,-r*.55,r*1.8,r*.32,r*.15,'#f2a5b5',lw);for(let i=-1;i<=1;i++)D.circle(c,i*r*.55,-r*.7,r*.17,'#e2645a',lw*.7);D.face(c,0,r*.25,r*.8)}
    else if(k===7){D.rrect(c,-r*.8,-r*.2,r*1.6,r*1,r*.1,K.c,lw);D.poly(c,[[-r,-r*.15],[0,-r*.95],[r,-r*.15]],'#c7746a',lw);D.rrect(c,-r*.2,r*.35,r*.4,r*.45,r*.15,'#8a5a3c',lw*.8);D.rrect(c,r*.35,0,r*.3,r*.28,r*.06,'#f4d66d',lw*.7);D.face(c,-r*.35,r*.1,r*.5)}
    else{for(let i=0;i<3;i++){const w=r*(1-i*.28),yy=r*.55-i*r*.5;D.rrect(c,-w,yy-r*.3,w*2,r*.5,r*.12,i%2?'#f2a5b5':K.c,lw)}D.star(c,0,-r*1.05,r*.3,'#f4d66d',lw*.8);D.face(c,0,r*.42,r*.7)}
    c.restore()},
  spawn(k,x,y){const st=this.st,K=KIND[k];for(let t=0;t<30;t++){const px=x??rnd(K.r+20,WW-K.r-20),py=y??rnd(K.r+20,WH-K.r-20);
      if(dist(px,py,st.hx,st.hy)<st.r+K.r+40&&x===undefined)continue;
      if(st.o.some(o=>dist(o.x,o.y,px,py)<o.r+K.r+4)&&t<29)continue;st.o.push({x:px,y:py,r:K.r,k,rot:rnd(-.3,.3),fall:-1});return}},
  reset(api){this.__P=api;this.st={o:[],hx:WW/2,hy:WH/2,r:24,rt:24,tx:WW/2,ty:WH/2,drag:null,cam:{x:WW/2,y:WH/2,z:1.4},chainT:0,eaten:0};
    const cnt=[70,55,40,30,22,16,10,7,3];cnt.forEach((n,k)=>{for(let i=0;i<n;i++)this.spawn(k)});api.score=0},
  down(x,y,api){this.st.drag={x,y,hx:this.st.tx,hy:this.st.ty}},
  move(x,y){const st=this.st;if(!st.drag)return;const z=st.cam.z;st.tx=clamp(st.drag.hx+(x-st.drag.x)/z*1.25,30,WW-30);st.ty=clamp(st.drag.hy+(y-st.drag.y)/z*1.25,30,WH-30)},
  up(){this.st.drag=null},
  key(k){const st=this.st,d=40;if(k==='ArrowLeft')st.tx-=d;if(k==='ArrowRight')st.tx+=d;if(k==='ArrowUp')st.ty-=d;if(k==='ArrowDown')st.ty+=d;st.tx=clamp(st.tx,30,WW-30);st.ty=clamp(st.ty,30,WH-30)},keyRepeat:true,
  update(dt,api){const st=this.st;
    const sp=Math.min(1,dt*9);st.hx+=(st.tx-st.hx)*sp;st.hy+=(st.ty-st.hy)*sp;
    st.r+=(st.rt-st.r)*Math.min(1,dt*5);st.chainT-=dt;if(st.chainT<=0)api.combo=0;
    const z=clamp(1.5*28/(st.r+4),.42,1.4);st.cam.z+=(z-st.cam.z)*Math.min(1,dt*2);
    st.cam.x+=(st.hx-st.cam.x)*Math.min(1,dt*6);st.cam.y+=(st.hy-st.cam.y)*Math.min(1,dt*6);
    for(let i=st.o.length-1;i>=0;i--){const o=st.o[i];
      if(o.fall>=0){o.fall+=dt*2.8;o.x+=(st.hx-o.x)*Math.min(1,dt*8);o.y+=(st.hy-o.y)*Math.min(1,dt*8);o.rot+=dt*8;
        if(o.fall>=1){st.o.splice(i,1);const K=KIND[o.k];api.combo++;st.chainT=.7;const mul=1+Math.min(api.combo,20)*.1,pts=Math.round(K.p*mul);api.add(pts);
          st.rt+=K.r*K.r/(st.rt*7.5);st.eaten++;
          const [sx,sy]=this.toScr(st.hx,st.hy);if(o.k>=3||api.combo%10===0)api.float(sx,sy-st.r*st.cam.z-14,'+'+pts,{size:o.k>=5?30:20,c:o.k>=6?'#f3c84b':'#fff'});
          if(o.k>=6){S.perfect();api.shake(7);api.flash('#fff',.3);api.burst(sx,sy,{c:['#f3c84b','#fff','#f2a5b5'],n:20,shape:'star',sp:280})}else S.combo(api.combo);
          if(o.k>=4)api.ring(sx,sy,{c:'#fff',r:st.r*st.cam.z*1.6});
          this.spawn(Math.min(o.k,rndi(0,8)))}continue}
      const d=dist(o.x,o.y,st.hx,st.hy);
      if(o.r<st.r*.92&&d<st.r-o.r*.25){o.fall=0;S.pop(1.4-o.k*.08)}
      else if(o.r>=st.r*.92&&d<st.r+o.r*.6&&d>1){// 大きすぎるものはちょっとゆれる
        o.rot=Math.sin(api.t*30)*.08}}
  },
  toScr(x,y){const c=this.st.cam;return[(x-c.x)*c.z+W/2,(y-c.y)*c.z+H/2+60]},
  draw(c,api){const st=this.st,cam=st.cam;c.fillStyle='#d9c7aa';c.fillRect(0,api.top,W,api.bottom-api.top);
    c.save();c.translate(W/2,H/2+60);c.scale(cam.z,cam.z);c.translate(-cam.x,-cam.y);
    c.fillStyle='#efe4d2';c.fillRect(0,0,WW,WH);
    c.fillStyle='#e6d6bd';for(let gx=0;gx<WW;gx+=110)for(let gy=0;gy<WH;gy+=110)if(((gx+gy)/110)%2===0)c.fillRect(gx,gy,110,110);
    c.lineWidth=8;c.strokeStyle=OL;c.strokeRect(0,0,WW,WH);
    // 穴
    D.circle(c,st.hx,st.hy,st.r+4,'#7d6aa8',4);D.circle(c,st.hx,st.hy,st.r,'#3f342e',0);
    c.save();c.beginPath();c.arc(st.hx,st.hy,st.r,0,7);c.clip();
    for(const o of st.o)if(o.fall>=0){const s=1-o.fall*.85;c.globalAlpha=1-o.fall*.5;this.item(c,o.x,o.y+o.fall*o.r*.6,o.r*s,o.k,o.rot)}c.globalAlpha=1;c.restore();
    const vx0=cam.x-W/2/cam.z-100,vx1=cam.x+W/2/cam.z+100,vy0=cam.y-(H/2+60-GAME.__P.top)/cam.z-100,vy1=cam.y+(GAME.__P.bottom-H/2-60)/cam.z+100;
    const vis=st.o.filter(o=>o.fall<0&&o.x>vx0&&o.x<vx1&&o.y>vy0&&o.y<vy1).sort((a,b)=>a.y-b.y);
    for(const o of vis){c.globalAlpha=.18;D.ellipse(c,o.x,o.y+o.r*.8,o.r*.9,o.r*.25,'#5b4d45',0);c.globalAlpha=1;this.item(c,o.x,o.y,o.r,o.k,o.rot)}
    c.restore();
    // 次に食べられるサイズ
    const nx=KIND.find(K=>K.r>=st.r*.92);if(nx&&api.state==='play'){D.rrect(c,14,H-56,190,40,20,'#fffdf8',3);D.text(c,'つぎ：'+nx.n,109,H-36,16,'#5b4d45')}
  },
  __bot(api){const st=this.st;let best=null,bd=1e9;for(const o of st.o){if(o.fall>=0||o.r>=st.r*.92)continue;const d=dist(o.x,o.y,st.hx,st.hy)-o.r*3;if(d<bd){bd=d;best=o}}
    if(best){st.tx=best.x;st.ty=best.y}},
};
