/* かんたおしストライク：横から見た缶タワー。缶は矩形の簡易物理（円で近似）で崩れる。 */
const FL=560,R=5,BALLX=90,BALLY=600;
const GAME={...META,sprites:['icon','can','ball'],unit:'個',hudUnit:true,fullBleed:true,comboHud:false,
  bgm:{bpm:124,root:60,scale:'major',prog:[1,5,4,5],seed:84,lead:'square',drums:'four',density:.55},
  ranks:[[0,'ことん'],[8,'かんたおし見習い'],[16,'ガラガラ上手'],[25,'ストライカー'],[32,'かんたおし名人'],[38,'屋台のこわい人']],
  shareText:(v,f)=>`かんたおしストライクで ${f}個 たおした！`,
  icon(c,x,y,s){[[0,1],[-1,2],[1,2],[-.5,3],[.5,3]].forEach(([dx,row])=>this.can(c,x+dx*s*.2+s*.1,y+s*.42-row*s*.2,s*.18,0,0));D.circle(c,x-s*.34,y+s*.25,s*.1,'#e2645a')},
  can(c,x,y,s,rot,k){c.save();c.translate(x,y);c.rotate(rot);const col=['#f08a8a','#7fb2e0','#9cc86a','#f2c84b'][k%4];D.rrect(c,-s*.42,-s*.5,s*.84,s,s*.12,col);c.fillStyle='#fbf7f0';c.fillRect(-s*.42,-s*.2,s*.84,s*.4);c.strokeStyle=OL;c.lineWidth=2.5;c.strokeRect(-s*.42,-s*.2,s*.84,s*.4);D.face(c,0,0,s*.6);c.restore()},
  reset(api){this.st={round:0,balls:3,cans:[],b:null,wait:0,t:0,rdown:0,res:[]};this.build();api.score=0},
  build(){const st=this.st;st.cans=[];const cx=300;const rows=[4,3,2,1];let y=FL-20;rows.forEach((n,ri)=>{for(let i=0;i<n;i++)st.cans.push({x:cx+(i-(n-1)/2)*42,y,vx:0,vy:0,rot:0,vr:0,k:ri+i,down:false,out:false});y-=42});st.rdown=0;st.balls=3},
  down(x,y){if(this.st.b||this.st.wait>0)return;this.st.sw={x,y,t:performance.now()}},
  up(x,y,api){const st=this.st,s=st.sw;st.sw=null;if(!s||st.b||st.wait>0||st.balls<=0)return;const dx=x-s.x,dy=y-s.y;if(Math.hypot(dx,dy)<30)return;const dt=Math.max(50,performance.now()-s.t);const v=clamp(Math.hypot(dx,dy)/dt*1000,400,1500);this.throwB(Math.atan2(dy,dx),v,api)},
  throwB(a,v,api){const st=this.st;st.b={x:BALLX,y:BALLY,vx:Math.cos(a)*v,vy:Math.sin(a)*v,t:0};st.balls--;S.whoosh()},
  key(k,api){if(k===' ')this.throwB(-.35,1000,api)},
  update(dt,api){const st=this.st;st.t+=dt;if(st.wait>0){st.wait-=dt;if(st.wait<=0){st.round++;if(st.round>=5){api.end();return}this.build()}return}
    const b=st.b;const sub=4,h=dt/sub;
    for(let s=0;s<sub;s++){if(b){b.vy+=900*h;b.x+=b.vx*h;b.y+=b.vy*h;b.t+=h;if(b.y>FL-12){b.y=FL-12;b.vy*=-.3;b.vx*=.8}}
      for(const cn of st.cans){if(cn.out)continue;cn.vy+=900*h;cn.x+=cn.vx*h;cn.y+=cn.vy*h;cn.rot+=cn.vr*h;cn.vx*=1-.5*h;cn.vr*=1-.8*h;
        if(cn.y>FL-21){cn.y=FL-21;cn.vy*=-.2;cn.vx*=.7;if(Math.abs(cn.rot)>.3)cn.down=true}
        if(cn.x<-30||cn.x>W+30)cn.out=true;
        if(b){const d=dist(cn.x,cn.y,b.x,b.y);if(d<34){const nx=(cn.x-b.x)/d,ny=(cn.y-b.y)/d;const rv=(b.vx-cn.vx)*nx+(b.vy-cn.vy)*ny;if(rv>0){cn.vx+=nx*rv*.9;cn.vy+=ny*rv*.9-100;cn.vr+=rnd(-8,8);b.vx-=nx*rv*.3;b.vy-=ny*rv*.3;S.tone(900,.05,{type:'square',v:.15});S.noise(.05,{v:.4,f:3500});api.shake(3)}}}}
      for(let i=0;i<st.cans.length;i++)for(let j=i+1;j<st.cans.length;j++){const a=st.cans[i],c2=st.cans[j];if(a.out||c2.out)continue;const dx=c2.x-a.x,dy=c2.y-a.y,d=Math.hypot(dx,dy);if(d<40&&d>0){const nx=dx/d,ny=dy/d,o=(40-d)/2;a.x-=nx*o;a.y-=ny*o;c2.x+=nx*o;c2.y+=ny*o;const rv=(a.vx-c2.vx)*nx+(a.vy-c2.vy)*ny;if(rv>0){a.vx-=nx*rv*.5;a.vy-=ny*rv*.5;c2.vx+=nx*rv*.5;c2.vy+=ny*rv*.5;if(rv>60){a.vr+=rnd(-4,4);c2.vr+=rnd(-4,4);S.tone(700,.04,{type:'square',v:.08})}}}}}
    if(b&&(b.t>3||b.x>W+30)){st.b=null}
    let n=0;for(const cn of st.cans)if(cn.out||cn.down||cn.y>FL-30)n++;
    if(n>st.rdown){const g=n-st.rdown;st.rdown=n;api.add(g);api.float(300,400,'+'+g,{size:26});S.coin()}
    if(!b&&(st.balls<=0||n>=10)&&st.cans.every(cn=>Math.hypot(cn.vx,cn.vy)<20||cn.out)){st.wait=1.4;if(n>=10&&st.balls===2){api.add(10);S.fanfare();api.flash('#fff',.5);api.float(W/2,300,'ストライク！ +10',{size:40,c:'#f3c84b'})}else if(n>=10){S.perfect();api.float(W/2,300,'ぜんぶたおした！',{size:32,c:'#f3c84b'})}else S.good()}},
  drawHud(c,api){const st=this.st;D.rrect(c,70,20,280,56,28,'#fffdf8',3.5);D.text(c,api.score+'個　R'+(st.round+1)+'/5　ボール'+st.balls,W/2,48,20,'#5b4d45')},
  draw(c,api){const st=this.st;c.fillStyle='#e9eef4';c.fillRect(0,api.top,W,api.bottom-api.top);c.fillStyle='#dbe3ec';for(let x=0;x<W;x+=50)c.fillRect(x,api.top,25,api.bottom-api.top);
    D.rrect(c,-10,FL,W+20,api.bottom-FL+10,0,'#c9a274',4);D.rrect(c,220,FL-4,160,14,6,'#b98450',3);
    for(const cn of st.cans)if(!cn.out)this.can(c,cn.x,cn.y,42,cn.rot,cn.k);
    if(st.b)D.circle(c,st.b.x,st.b.y,12,'#e2645a');else if(st.balls>0&&st.wait<=0){D.circle(c,BALLX,BALLY,12,'#e2645a');if(api.t<3&&api.state==='play')D.text(c,'かんへスワイプしてなげる →',W/2,660,16,'#5b4d45','center','#fffdf8',5)}
    for(let i=0;i<st.balls;i++)D.circle(c,40+i*24,BALLY+40,8,'#e2645a',2)},
  __bot(api){const st=this.st;if(st.b||st.wait>0||st.balls<=0)return;const up=st.cans.filter(c=>!c.down&&!c.out);const t=up.length?up[rndi(0,up.length-1)]:null;if(!t)return;this.throwB(Math.atan2(t.y-80-BALLY,t.x-BALLX),rnd(800,1200),api)},
};
