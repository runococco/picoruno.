/* ぷくーっとガム：長押しでふくらむ。隠し限界を超えると破裂。 */
const N=10,CX=W/2,CY=430;
const GAME={...META,sprites:['icon','gum'],unit:'点',fullBleed:true,
  bgm:{bpm:112,root:67,scale:'major',prog:[1,6,4,5],seed:99,lead:'triangle',drums:'light',density:.45},
  ranks:[[0,'パンパン'],[300,'ガム見習い'],[600,'ぷくぷく上手'],[900,'ふくらませの達人'],[1200,'ガムの神'],[1500,'伝説のぷくー']],
  shareText:(v,f)=>`ぷくーっとガムで ${f}点！`,
  icon(c,x,y,s){this.gum(c,x,y,s*.38,s*.18)},
  gum(c,x,y,r,m){D.ellipse(c,x,y+r+m*.9,m*1.3,m*.9,'#f1dcc0');D.face(c,x,y+r+m*.7,m*1.8,'o');if(r>2)D.circle(c,x,y,r,'#f2a5c0')},
  reset(api){this.st={n:0,r:0,hold:false,lim:0,wait:0,t:0,res:[],pop:0};api.score=0;this.next()},
  next(){const st=this.st;st.n++;st.r=0;st.hold=false;st.lim=rnd(70,150);st.done=false;st.pop=0;st.wait=0},
  down(){const st=this.st;if(st.done||st.wait>0)return;st.hold=true;S.noise(.4,{v:.12,f:600,type:'lowpass'})},
  up(x,y,api){const st=this.st;if(!st.hold||st.done)return;st.hold=false;st.done=true;const k=st.r/st.lim;let pts=Math.round(st.r);let txt='';if(k>.95){pts+=100;txt='ギリギリ！'}else if(k>.85){pts+=50;txt='おしい！'}else if(k>.6){txt='まずまず'}else{txt='ちいさい…'}
    if(k>.85){api.combo++;pts+=Math.min(api.combo,5)*10}else api.combo=0;api.add(pts);st.res.push(pts);
    api.float(CX,250,txt+' +'+pts,{size:k>.95?34:26,c:k>.85?'#e2645a':'#5b4d45'});if(k>.95){S.perfect();api.flash('#fff',.3);api.burst(CX,CY,{c:['#f2a5c0','#f2c84b','#fff'],n:16,sp:220,shape:'s'})}else if(k>.85)S.good();else S.coin();st.wait=1.3},
  update(dt,api){const st=this.st;st.t+=dt;if(st.wait>0){st.wait-=dt;if(st.wait<=0){if(st.n>=N)api.end();else this.next()}return}
    if(st.hold&&!st.done){st.r+=(45+st.n*3)*dt;if(st.r>=st.lim){st.done=true;st.hold=false;st.pop=1;st.res.push(0);api.combo=0;S.boom();S.noise(.1,{v:.5,f:3000});api.shake(10);api.burst(CX,CY,{c:['#f2a5c0','#fff'],n:22,sp:260,r:5});api.float(CX,250,'パンッ！0点',{size:32,c:'#e2645a'});st.wait=1.4}}},
  draw(c,api){const st=this.st;c.fillStyle='#fbe9ef';c.fillRect(0,api.top,W,api.bottom-api.top);for(let i=0;i<4;i++)D.circle(c,(i*120+st.t*6)%(W+60)-30,140+i*140,8,'#f6d6e0',0);
    if(st.pop){D.ellipse(c,CX,CY+60,70,30,'#f2a5c0',3);D.ellipse(c,CX-50,CY+30,20,14,'#f2a5c0',2.5);D.ellipse(c,CX+55,CY+40,16,12,'#f2a5c0',2.5);D.ellipse(c,CX,CY+110,30,22,'#f1dcc0');D.face(c,CX,CY+105,46,'hurt')}
    else this.gum(c,CX,CY-st.r*.3,st.r,36);
    D.text(c,st.n+'/'+N,CX,110,18,'#5b4d45');for(let i=0;i<N;i++)D.circle(c,CX-(N-1)*11+i*22,150,7,i<st.res.length?(st.res[i]?'#f2a5c0':'#5b5560'):'#fff',2.5);
    if(st.hold)D.text(c,Math.round(st.r),CX,620,36,'#5b4d45');
    if(api.state==='play'&&st.n===1&&!st.hold&&st.r===0)D.text(c,'おしてふくらませる！',CX,620,22,'#5b4d45')},
  __bot(api){const st=this.st;if(st.done||st.wait>0)return;if(!st.hold)this.down();else if(st.r>=Math.min(st.lim-5,rnd(60,140)))this.up(0,0,api)},
};
