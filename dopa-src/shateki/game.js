/* コルクしゃてき：棚の景品をコルクで押して落とす。景品は矩形で奥行きを持ち、押されてずれる。 */
const SH=[300,430,560],SHL=50,SHR=370,N=12;
const PR=[{n:'あめ',w:26,h:26,c:'#f2a5b5',pt:10,d:10},{n:'おかし',w:40,h:30,c:'#9cc86a',pt:20,d:30},{n:'くまぬい',w:46,h:46,c:'#e3b47a',pt:40,d:60},{n:'おおきなぬい',w:60,h:60,c:'#a9d6e6',pt:80,d:120},{n:'金のぬい',w:40,h:46,c:'#f2c84b',pt:200,d:50,gold:true}];
const GAME={...META,sprites:['icon','prize','gun'],unit:'点',fullBleed:true,comboHud:false,
  bgm:{bpm:118,root:62,scale:'major',prog:[1,5,6,4],seed:38,lead:'square',drums:'pop',density:.55},
  ranks:[[0,'はずれ'],[100,'しゃてき初心者'],[250,'なかなかの腕'],[450,'しゃてき名人'],[700,'屋台のこわいお客'],[1000,'伝説のガンマン']],
  shareText:(v,f)=>`コルクしゃてきで ${f}点！`,
  icon(c,x,y,s){D.rrect(c,x-s*.45,y+s*.1,s*.9,s*.08,4,'#b98450');this.prize(c,x-s*.2,y+s*.1,{w:s*.3,h:s*.3,c:'#e3b47a',gold:false},0);this.prize(c,x+s*.18,y+s*.1,{w:s*.22,h:s*.22,c:'#f2a5b5',gold:false},0);D.circle(c,x+s*.05,y-s*.25,s*.08,'#c9a274')},
  prize(c,x,y,p,tilt){c.save();c.translate(x,y);c.rotate(tilt);const w=p.w,h=p.h;
    if(p.c==='#e3b47a'||p.c==='#a9d6e6'||p.gold){const col=p.gold?'#f2c84b':p.c;D.circle(c,-w*.3,-h*.95,w*.17,col);D.circle(c,w*.3,-h*.95,w*.17,col);D.ellipse(c,0,-h*.6,w*.5,h*.4,col);D.rrect(c,-w*.45,-h*.35,w*.9,h*.35,w*.2,col);D.face(c,0,-h*.55,w*.6,p.gold?'o':'smile')}
    else{D.rrect(c,-w/2,-h,w,h,w*.25,p.c);D.face(c,0,-h*.5,w*.7)}c.restore()},
  gun(c,x,y,s,kick){D.rrect(c,x-s*.12,y-s*.1+kick,s*.24,s*.55,s*.06,'#9a6a4e');D.rrect(c,x-s*.09,y-s*.55+kick,s*.18,s*.5,s*.05,'#c98a5b');D.circle(c,x,y-s*.55+kick,s*.08,'#4b3e37',2.5)},
  reset(api){const st=this.st={p:[],n:N,corks:[],t:0,kick:0,wait:0,fall:[]};
    SH.forEach((y,r)=>{let x=SHL+30;while(x<SHR-30){const k=r===0?pick([2,3,4,3]):r===1?pick([1,2,1,4]):pick([0,0,1,0]);const P=PR[k];if(x+P.w>SHR-10)break;st.p.push({x:x+P.w/2,y,k,hp:P.d,off:0,sh:r,tilt:0,vx:0});x+=P.w+rnd(14,30)}});api.score=0},
  down(x,y,api){const st=this.st;if(st.n<=0||st.wait>0)return;st.n--;st.wait=.25;st.kick=1;const jit=rnd(-14,14),jy=rnd(-10,10);
    st.corks.push({x:W/2,y:H-100,tx:x+jit,ty:y+jy,t:0});S.noise(.08,{v:.5,f:2500});S.tone(200,.1,{type:'square',v:.2,to:80});api.shake(3)},
  key(k,api){if(k===' ')this.down(W/2,SH[1],api)},
  update(dt,api){const st=this.st;st.t+=dt;st.kick=Math.max(0,st.kick-dt*6);st.wait-=dt;
    for(let i=st.corks.length-1;i>=0;i--){const k=st.corks[i];k.t+=dt*4;if(k.t>=1){st.corks.splice(i,1);this.hit(k.tx,k.ty,api)}}
    for(const p of st.p){p.off+=p.vx*dt;p.vx*=Math.pow(.05,dt);p.tilt+=(p.vx*.002-p.tilt)*Math.min(1,dt*6);const P=PR[p.k];const sy=SH[p.sh];
      if(!p.falling&&p.hp<=0){p.falling=true;p.vy=0;S.perfect();const pts=P.pt;api.add(pts);api.float(p.x+p.off,sy-P.h-20,'+'+pts,{size:P.gold?32:24,c:P.gold?'#f3c84b':'#fff'});if(P.gold){api.flash('#fff6c8',.5);S.fanfare();api.burst(p.x,sy-30,{c:['#f4d66d','#fff'],n:24,shape:'star',sp:300})}}
      if(p.falling){p.vy=(p.vy||0)+1200*dt;p.fy=(p.fy||0)+p.vy*dt;p.tilt+=dt*4}}
    for(let i=st.p.length-1;i>=0;i--)if(st.p[i].fy>500){st.p.splice(i,1);S.thud()}
    if(st.n<=0&&!st.corks.length){st.endT=(st.endT||0)+dt;if(st.endT>1.5)api.end()}},
  hit(x,y,api){const st=this.st;let best=null,bd=1e9;for(const p of st.p){if(p.falling)continue;const P=PR[p.k],px=p.x+p.off,sy=SH[p.sh];if(x>px-P.w/2-4&&x<px+P.w/2+4&&y>sy-P.h-6&&y<sy+4){const d=Math.abs(x-px);if(d<bd){bd=d;best=p}}}
    if(!best){S.tap(.4);api.burst(x,y,{c:'#c9a274',n:4,sp:80,r:3});return}
    const P=PR[best.k];best.hp-=30+rnd(0,12);best.vx+=(x<best.x+best.off?1:-1)*0+rnd(-1,1)*60;S.thud();S.tone(600,.06,{type:'square',v:.15});api.burst(x,y,{c:['#fff','#c9a274'],n:6,sp:120,r:3});api.ring(x,y,{c:'#fff',r:30});
    if(best.hp>0){api.float(x,y-30,'ぐらっ',{size:18})}},
  drawHud(c,api){const st=this.st;D.rrect(c,70,20,280,56,28,'#fffdf8',3.5);D.text(c,api.score+'点　のこり'+st.n+'発',W/2,48,22,'#5b4d45')},
  draw(c,api){const st=this.st;c.fillStyle='#f3e4d4';c.fillRect(0,api.top,W,api.bottom-api.top);
    c.fillStyle='#e8d2bc';for(let x=0;x<W;x+=40)c.fillRect(x,api.top,20,api.bottom-api.top);
    D.rrect(c,SHL-24,100,SHR-SHL+48,520,20,'#c9637f',4);c.fillStyle='#f9eef2';c.fillRect(SHL,120,SHR-SHL,480);
    for(const y of SH){D.rrect(c,SHL-6,y,SHR-SHL+12,16,6,'#b98450',3.5)}
    for(const p of st.p){const P=PR[p.k];this.prize(c,p.x+p.off,SH[p.sh]+(p.fy||0),P,p.tilt)}
    for(const k of st.corks){const t=k.t,x=lerp(W/2,k.tx,t),y=lerp(H-100,k.ty,t)-Math.sin(t*Math.PI)*40;D.circle(c,x,y,10*(1-t*.5),'#c9a274',2.5)}
    this.gun(c,W/2,H-60,90,st.kick*10);
    if(api.t<3&&api.state==='play')D.text(c,'けいひんをタップしてねらう',W/2,660,16,'#5b4d45','center','#fffdf8',5)},
  __bot(api){const st=this.st;const p=st.p.filter(q=>!q.falling)[0];if(p)this.down(p.x+p.off,SH[p.sh]-PR[p.k].h/2,api)},
};
