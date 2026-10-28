/* ぽんぽこリズム：2レーンの音ゲー。譜面はBGMと同じテンポで生成。時刻は AudioContext 基準。 */
const HITY=520,SPD=430,LX=[W*.28,W*.72],BPM=118,BEAT=60/BPM,BARS=16;
const GAME={...META,sprites:['icon','drum','note'],unit:'点',
  bgm:{bpm:BPM,root:62,scale:'major',prog:[1,5,6,4],seed:101,lead:'triangle',drums:'pop',density:.6},
  ranks:[[0,'たいこデビュー'],[3000,'お祭り好き'],[7000,'リズム名人'],[11000,'ぽんぽこ師匠'],[15000,'たいこの達人'],[18500,'フルコンボの神']],
  shareText:(v,f)=>`ぽんぽこリズムで ${f}点！`,
  icon(c,x,y,s){this.drum(c,x-s*.2,y+s*.1,s*.24,0,'#d9644f');this.drum(c,x+s*.22,y-s*.05,s*.2,0,'#5fa0c4');this.note(c,x+s*.05,y-s*.33,s*.08,0)},
  drum(c,x,y,r,hit,col){const sq=hit*.12;D.ellipse(c,x,y+r*.45,r*1.05,r*.55,col,Math.max(2,r*.07));c.fillStyle=col;c.fillRect(x-r*1.05,y,r*2.1,r*.45);c.lineWidth=Math.max(2,r*.07);c.strokeStyle=OL;c.beginPath();c.moveTo(x-r*1.05,y);c.lineTo(x-r*1.05,y+r*.45);c.moveTo(x+r*1.05,y);c.lineTo(x+r*1.05,y+r*.45);c.stroke();
    D.ellipse(c,x,y,r*(1.05+sq),r*(.5-sq),'#fbf1df',Math.max(2,r*.07));D.face(c,x,y+r*.6,r*.9,hit>.5?'o':'smile')},
  note(c,x,y,r,lane){D.circle(c,x,y,r,lane?'#5fa0c4':'#d9644f',Math.max(2,r*.16));D.circle(c,x,y,r*.55,'#fbf1df',Math.max(1.5,r*.1))},
  reset(api){const notes=[];let s=7;const r=()=>(s=(s*16807)%2147483647)/2147483647;
    for(let b=1;b<BARS;b++){const lvl=Math.min(1,b/12),den=.35+lvl*.45;for(let k=0;k<8;k++){const onBeat=k%2===0;if(r()<(onBeat?den+.2:den*.55)){const lane=r()<.5?0:1;notes.push({t:(b*4+k/2)*BEAT,lane,j:null})}}}
    // 同時押しを少しだけ
    for(const n of notes)if(r()<.06)notes.push({t:n.t,lane:1-n.lane,j:null});
    notes.sort((a,b)=>a.t-b.t);
    this.st={notes,t0:null,now:-1,hit:[0,0],judge:'',jT:0,jC:'#fff',perf:0,good:0,miss:0,end:(BARS*4+2)*BEAT,maxCombo:0};api.score=0},
  now(){const ac=AU.ctx;return this.st.t0!==null&&ac?ac.currentTime-this.st.t0-(ac.outputLatency||.03):this.st.now},
  tap(lane,api){const st=this.st,t=this.now();st.hit[lane]=1;S.tone(lane?320:200,.12,{type:'sine',v:.45,to:lane?160:90});
    let best=null,bd=.16;for(const n of st.notes){if(n.j||n.lane!==lane)continue;const d=Math.abs(n.t-t);if(d<bd){bd=d;best=n}if(n.t-t>.2)break}
    if(!best)return;const x=LX[lane];
    if(bd<.055){best.j='p';st.perf++;api.combo++;api.score+=Math.round(100*(1+Math.min(api.combo,100)/50));this.show('パーフェクト','#f3c84b');api.burst(x,HITY,{c:['#f3c84b','#fff'],n:10,sp:220,shape:'star',r:4});api.ring(x,HITY,{c:'#f3c84b',r:60})}
    else{best.j='g';st.good++;api.combo++;api.score+=Math.round(50*(1+Math.min(api.combo,100)/50));this.show('グッド','#fff');api.burst(x,HITY,{c:['#fff'],n:6,sp:160,r:4})}
    st.maxCombo=Math.max(st.maxCombo,api.combo);if(api.combo>0&&api.combo%25===0){S.combo(api.combo/10);api.float(W/2,250,api.combo+' コンボ！',{size:34,c:'#f3c84b'});api.flash('#fff',.2)}},
  show(t,c){const st=this.st;st.judge=t;st.jC=c;st.jT=.5},
  down(x,y,api){this.tap(x<W/2?0:1,api)},
  key(k,api){const l={f:0,d:0,ArrowLeft:0,j:1,k:1,ArrowRight:1}[k];if(l!==undefined)this.tap(l,api)},
  update(dt,api){const st=this.st;if(st.t0===null){st.t0=AU.t0||((AU.ctx&&AU.ctx.currentTime)||0);if(!AU.ctx)st.t0=null}
    if(!AU.ctx)st.now+=dt;const t=this.now();
    for(const n of st.notes){if(!n.j&&t-n.t>.16){n.j='m';st.miss++;api.combo=0;this.show('ミス','#cfd8e8')}}
    st.hit[0]=Math.max(0,st.hit[0]-dt*6);st.hit[1]=Math.max(0,st.hit[1]-dt*6);st.jT=Math.max(0,st.jT-dt);
    if(t>st.end){if(st.miss===0){api.score+=5000;api.float(W/2,300,'フルコンボ！ +5000',{size:34,c:'#f3c84b',life:1.4});S.fanfare()}api.end()}},
  overText:'おわり！',
  draw(c,api){const st=this.st,t=this.now();c.fillStyle=this.bg;c.fillRect(0,0,W,H);
    // 背景：ちょうちん
    for(const l of[0,1]){D.rrect(c,LX[l]-50,0,100,H,0,l?'rgba(95,160,196,.13)':'rgba(217,100,79,.13)',0)}
    c.lineWidth=4;c.strokeStyle=OL;c.beginPath();c.moveTo(20,HITY);c.lineTo(W-20,HITY);c.stroke();
    for(const l of[0,1])D.circle(c,LX[l],HITY,30,null,4);
    for(const n of st.notes){if(n.j==='p'||n.j==='g')continue;const y=HITY-(n.t-t)*SPD;if(y<-40||y>H+40)continue;c.globalAlpha=n.j==='m'?.35:1;this.note(c,LX[n.lane],y,26,n.lane);c.globalAlpha=1}
    for(const l of[0,1])this.drum(c,LX[l],HITY+92,54,st.hit[l],l?'#5fa0c4':'#d9644f');
    if(st.jT>0){c.save();c.translate(W/2,HITY-110);const s=1+st.jT*.4;c.scale(s,s);c.globalAlpha=Math.min(1,st.jT*4);D.text(c,st.judge,0,0,30,st.jC,'center',OL,7);c.restore();c.globalAlpha=1}
    const pr=clamp(t/st.end,0,1);D.rrect(c,40,H-24,W-80,8,4,'#fffdf8',2);if(pr>0)D.rrect(c,41,H-23,(W-82)*pr,6,3,this.accent,0);
  },
  __bot(api){const st=this.st,t=this.now();for(const n of st.notes){if(n.j)continue;if(n.t-t>.03)break;if(Math.abs(n.t-t)<.04&&Math.random()<.95)this.tap(n.lane,api)}},
};
