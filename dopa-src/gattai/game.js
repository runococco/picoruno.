/* もちもちがったい：同じ段階のおもちが触れると合体（スイカ系）。円の物理を自前で解く。 */
const L=26,Rt=394,BOT=680,TOP=150,LINE=196;
const TIERS=[
  {r:15,c:'#fffaf0',n:'しらたま'},{r:20,c:'#f7c9d4',n:'さくら'},{r:26,c:'#bcd99c',n:'よもぎ'},{r:33,c:'#ecd08f',n:'きなこ'},
  {r:41,c:'#f2b183',n:'みたらし'},{r:50,c:'#cbb6e2',n:'いもあん'},{r:60,c:'#9fd2d9',n:'ソーダもち'},{r:71,c:'#f4d66d',n:'たまご'},
  {r:83,c:'#ea9292',n:'いちごだいふく'},{r:96,c:'#b4a08a',n:'くさだんご'},{r:110,c:'#fffdf8',n:'かがみもち'}];
const PTS=[1,3,6,10,15,21,28,36,45,55,100];
const GAME={...META,unit:'点',
  bgm:{bpm:118,root:60,scale:'major',prog:[1,4,5,1],seed:27,lead:'triangle',drums:'pop',density:.55},
  ranks:[[0,'もち初心者'],[300,'もちつき見習い'],[800,'もちもち名人'],[1500,'おもちの達人'],[2500,'かがみもちの使い手'],[4000,'もちもち神']],
  shareText:(v,f)=>`もちもちがったいで ${f}点！`,
  icon(c,x,y,s){this.mochi(c,x,y+s*.1,s*.38,8);this.mochi(c,x-s*.33,y-s*.26,s*.12,1);this.mochi(c,x+s*.3,y-s*.3,s*.16,3)},
  mochi(c,x,y,r,t,sq=0,rot=0){
    const T=TIERS[t];c.save();c.translate(x,y);c.rotate(rot*.15);
    const lw=Math.max(2,r*.09);
    if(t===10){D.ellipse(c,0,r*.25,r,r*.62,'#fffdf8',lw);D.ellipse(c,0,-r*.3,r*.78,r*.5,'#fffdf8',lw);D.circle(c,0,-r*.82,r*.24,'#f2a24a',lw);D.path(c,c=>{c.moveTo(0,-r*1.05);c.quadraticCurveTo(r*.2,-r*1.25,r*.35,-r*1.1)},null,lw);D.face(c,0,r*.25,r*.9,'smile')}
    else{D.ellipse(c,0,0,r*(1.04+sq),r*(.96-sq),T.c,lw);
      if(t===4){c.save();c.globalAlpha=.6;D.ellipse(c,0,-r*.35,r*.7,r*.3,'#c77a3e',0);c.restore()}
      if(t===8){D.path(c,c=>{c.moveTo(-r*.25,-r*.9);c.lineTo(0,-r*1.15);c.lineTo(r*.25,-r*.9)},'#9cc58a',lw*.7)}
      D.face(c,0,r*.08,r*1.1,t%3===2?'o':'smile')}
    c.restore();
  },
  reset(api){this.st={b:[],x:W/2,cur:rndi(0,2),next:rndi(0,3),cd:0,overT:0,chainT:0,chain:0,maxT:0,id:0,aiming:false};api.score=0},
  drop(api){const st=this.st;if(st.cd>0)return;const r=TIERS[st.cur].r;
    st.b.push({id:st.id++,x:clamp(st.x,L+r,Rt-r),y:TOP-10,vx:0,vy:60,t:st.cur,age:0,sq:0,rot:0});
    st.cur=st.next;st.next=rndi(0,Math.min(4,Math.max(2,st.maxT-1)));st.cd=.45;S.whoosh()},
  down(x,y,api){this.st.x=x;this.st.aiming=true},
  move(x,y){this.st.x=x},
  up(x,y,api){if(this.st.aiming){this.st.x=x;this.drop(api);this.st.aiming=false}},
  key(k,api){if(k==='ArrowLeft')this.st.x-=24;else if(k==='ArrowRight')this.st.x+=24;else if(k===' ')this.drop(api);this.st.x=clamp(this.st.x,L,Rt)},
  keyRepeat:true,
  merge(a,b,api){const st=this.st,t=a.t+1;a.dead=b.dead=true;
    st.chain=st.chainT>0?st.chain+1:1;st.chainT=1;api.combo=st.chain;
    const x=(a.x+b.x)/2,y=(a.y+b.y)/2;
    let pts=PTS[Math.min(t,10)]*(st.chain>1?st.chain:1);
    if(t>10){pts=200;api.burst(x,y,{c:['#f2a24a','#fff','#f7c9d4'],n:60,sp:500,shape:'star',r:7});api.flash('#fff',.8);api.shake(20);S.fanfare();api.float(x,y,'かがみもち×2 消滅！',{size:28})}
    else{const nb={id:st.id++,x,y,vx:(a.vx+b.vx)/2,vy:(a.vy+b.vy)/2-40,t,age:.5,sq:.18,rot:0};st.b.push(nb);st.maxT=Math.max(st.maxT,t);
      api.burst(x,y,{c:[TIERS[t].c,'#fff'],n:8+t*3,sp:150+t*25,r:4+t*.4,shape:'o'});api.ring(x,y,{c:'#fff',r:TIERS[t].r*1.8});
      S.pop(1.4-t*.08);if(st.chain>1)S.combo(st.chain*2);
      if(t>=6){api.shake(4+t);api.flash('#fff',.25);api.float(x,y-TIERS[t].r-10,TIERS[t].n+'！',{size:24+t})}
      if(t===10)S.perfect()}
    api.score+=pts;if(st.chain>1)api.float(x,y,st.chain+'連鎖 +'+pts,{c:'#f3c84b',size:22})},
  update(dt,api){const st=this.st,B=st.b;st.cd=Math.max(0,st.cd-dt);st.chainT-=dt;if(st.chainT<=0)api.combo=0;
    const sub=4,h=dt/sub;
    for(let s=0;s<sub;s++){
      for(const b of B){b.vy+=1500*h;b.x+=b.vx*h;b.y+=b.vy*h;b.vx*=.999;b.rot+=b.vx*h*.02}
      for(let it=0;it<2;it++){
        for(let i=0;i<B.length;i++){const a=B[i];if(a.dead)continue;for(let j=i+1;j<B.length;j++){const b=B[j];if(b.dead)continue;
          const ra=TIERS[a.t].r,rb=TIERS[b.t].r,dx=b.x-a.x,dy=b.y-a.y,d2=dx*dx+dy*dy,rr=ra+rb;if(d2>=rr*rr)continue;
          if(a.t===b.t){this.merge(a,b,api);break}
          const d=Math.sqrt(d2)||.01,nx=dx/d,ny=dy/d,ov=rr-d,ma=ra*ra,mb=rb*rb,k=ov/(ma+mb);
          a.x-=nx*k*mb;a.y-=ny*k*mb;b.x+=nx*k*ma;b.y+=ny*k*ma;
          const rv=(b.vx-a.vx)*nx+(b.vy-a.vy)*ny;if(rv<0){const imp=-(1.15)*rv/(1/ma+1/mb);a.vx-=imp*nx/ma;a.vy-=imp*ny/ma;b.vx+=imp*nx/mb;b.vy+=imp*ny/mb;
            const tx=-ny,ty=nx,tv=(b.vx-a.vx)*tx+(b.vy-a.vy)*ty,f=tv*.08;a.vx+=tx*f;a.vy+=ty*f;b.vx-=tx*f;b.vy-=ty*f;
            if(-rv>260&&a.age>.3)a.sq=Math.min(.15,-rv/4000)}}}
        for(const b of B){const r=TIERS[b.t].r;if(b.x<L+r){b.x=L+r;b.vx=Math.abs(b.vx)*.2}if(b.x>Rt-r){b.x=Rt-r;b.vx=-Math.abs(b.vx)*.2}
          if(b.y>BOT-r){if(b.vy>300){b.sq=Math.min(.15,b.vy/4000)}b.y=BOT-r;b.vy=-Math.abs(b.vy)*.15;b.vx*=.92}}
      }
      for(let i=B.length-1;i>=0;i--)if(B[i].dead)B.splice(i,1);
    }
    let danger=false;for(const b of B){b.age+=dt;b.sq*=Math.pow(.02,dt);if(b.age>1.2&&b.y-TIERS[b.t].r<LINE&&Math.abs(b.vy)<120)danger=true}
    st.overT=danger?st.overT+dt:Math.max(0,st.overT-dt*2);
    if(st.overT>2){api.shake(10);S.bad();api.end()}
  },
  overText:'あふれた！',
  draw(c,api){const st=this.st;
    c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    c.fillStyle='#ead9bd';for(let i=0;i<8;i++)c.fillRect(0,i*90+((api.t*0)%90),W,45);
    D.rrect(c,L-8,TOP-30,Rt-L+16,BOT-TOP+38,18,'#fdf6ea',4);
    const dz=st.overT>0;c.setLineDash([10,8]);c.lineWidth=3;c.strokeStyle=dz&&Math.sin(api.t*20)>0?'#e2645a':'rgba(226,100,90,.5)';c.beginPath();c.moveTo(L,LINE);c.lineTo(Rt,LINE);c.stroke();c.setLineDash([]);
    if(api.state==='play'||api.state==='count'){const r=TIERS[st.cur].r,x=clamp(st.x,L+r,Rt-r);
      c.globalAlpha=.25;c.fillStyle=OL;c.fillRect(x-1.5,TOP,3,BOT-TOP);c.globalAlpha=st.cd>0?.4:1;this.mochi(c,x,TOP-10,r,st.cur);c.globalAlpha=1}
    for(const b of st.b)this.mochi(c,b.x,b.y,TIERS[b.t].r,b.t,b.sq,b.rot);
    D.text(c,'つぎ',W-48,108,14,'#7a6658');this.mochi(c,W-48,134,14,st.next);
    // しんか表
    for(let i=0;i<11;i++){const x=40+i*34.5;this.mochi(c,x,702,6+i*.9,i);}
  },
  __bot(api){const st=this.st;st.x=rnd(L+20,Rt-20);this.drop(api)},
};
