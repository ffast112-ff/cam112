#!/usr/bin/env python3
from pathlib import Path
p=Path('fitplan/native/app/src/main/assets/app.js');s=p.read_text('utf8')
def change(a,b):
 global s
 assert a in s,'V8.2 anchor: '+a[:85]
 s=s.replace(a,b,1)
D=chr(36)
helper="""
function fpSyncTimeThumb(){
 document.querySelectorAll('input[type="range"][min="30"][max="120"]').forEach(r=>{
  const fraction=Math.max(0,Math.min(1,(Number(r.value)-30)/90));
  const center=12+Math.max(0,r.clientWidth-24)*fraction;
  r.style.setProperty('--fp-thumb-fill',center.toFixed(2)+'px');
 });
}
window.addEventListener('resize',()=>{if(view==='ready')requestAnimationFrame(fpSyncTimeThumb);});
document.addEventListener('input',e=>{
 if(e.target?.matches('input[type="range"][min="30"][max="120"]'))fpSyncTimeThumb();
});
"""
change('function readyView(){',helper+'\nfunction readyView(){')
change("if(view==='player'||view==='calibration')syncAwake();",
       "if(view==='ready')requestAnimationFrame(fpSyncTimeThumb);\n if(view==='player'||view==='calibration')syncAwake();")
change("const weightLabel=weightRequired?(cur.ref.actualWeight>0?formatWeight(cur.ref.actualWeight)+'kg':'설정 필요'):'맨몸/시간';",
"""const weightLabel=weightRequired?(cur.ref.actualWeight>0?formatWeight(cur.ref.actualWeight)+'kg':'설정 필요'):'맨몸/시간';
 const targetNumber=num(cur.ref.targetReps);
 const targetLabel=targetNumber>0?formatWeight(targetNumber)+(isTimed(e)?'초':'회'):
  (cur.kind==='stretch'?'가볍게 진행':cur.kind==='timed'?'시간 운동':'자유 운동');""")
change(D+"{cur.ref.targetReps}"+D+"{isTimed(e)?'초':'회'}</strong></div></div>",
       D+"{esc(targetLabel)}</strong></div></div>")
change('<button class="player-close" onclick="Fit.exitPlayer()">✕</button>',
       '<button class="player-close" onclick="Fit.exitPlayer()" aria-label="운동 화면 닫기">'+D+'{fpIcon("remove","fp-v82-control-icon")}</button>')
change(D+"{p.paused?'▶ 계속':'Ⅱ 일시정지'}</button>",
       D+"{p.paused?fpIcon('play','fp-v82-control-icon')+' 계속':fpIcon('pause','fp-v82-control-icon')+' 일시정지'}</button>")
change('<p class="fp-v76-muted">'+D+'{esc(phase)} · 개인 목표에 따른 진행</p>',
       '<p class="fp-v76-muted">'+D+'{esc(phase)}</p>')
p.write_text(s,'utf8')
css=Path('fitplan/native/app/src/main/assets/style.css')
css.write_text(css.read_text('utf8')+"""
/* Pixel-accurate slider fill ends exactly at physical thumb center. */
input[type=range][min="30"][max="120"]{
 appearance:none;-webkit-appearance:none;width:100%;height:12px;box-sizing:border-box;border:0;
 border-radius:999px;background:linear-gradient(to right,#29eb68 0,#29eb68 var(--fp-thumb-fill,12px),
 #3b544a var(--fp-thumb-fill,12px),#3b544a 100%)!important
}
input[type=range][min="30"][max="120"]::-webkit-slider-runnable-track{
 height:12px;border:0;background:transparent;border-radius:999px
}
input[type=range][min="30"][max="120"]::-webkit-slider-thumb{
 -webkit-appearance:none;appearance:none;width:24px;height:24px;margin-top:-6px;
 box-sizing:border-box;border:3px solid #d0ffe0;border-radius:50%;background:#66fc84;box-shadow:0 0 0 5px #183d2b
}
/* Viewport-fitted active workout; input-heavy preparation is still scrollable. */
.player-page:has(.streamlined-player){height:100dvh;overflow:hidden;display:flex;flex-direction:column}
.player-page:has(.streamlined-player) .player-head{min-height:54px;padding:8px 12px 4px;align-items:center}
.player-page:has(.streamlined-player) .player-progress{height:6px;margin:3px 14px}
.player-page:has(.streamlined-player) .timer-session-stats{padding:4px 14px;font-size:12px}
.player-page:has(.streamlined-player) .player-body{
 flex:1;min-height:0;overflow:hidden;padding:5px 10px max(5px,env(safe-area-inset-bottom));
 display:flex;align-items:center;justify-content:center
}
.player-page:has(.streamlined-player) .mint-player{
 min-height:0;width:100%;max-width:460px;gap:5px;justify-content:center
}
.player-page:has(.streamlined-player) .fp-v76-workhead{
 padding:9px 12px!important;margin:0 0 2px!important;border-radius:16px
}
.player-page:has(.streamlined-player) .fp-v76-workhead .fp-v76-head{font-size:16px;margin:0!important}
.player-page:has(.streamlined-player) .fp-v76-workhead .fp-v76-head>span{font-size:12px;white-space:nowrap}
.player-page:has(.streamlined-player) .fp-v76-workhead p{display:none}
.player-page:has(.streamlined-player) .mint-ring{
 width:min(73vw,38dvh,340px)!important;height:min(73vw,38dvh,340px)!important;
 margin:0 auto 3px!important;flex:0 1 auto;max-height:none
}
.player-page:has(.streamlined-player) .mint-ring-core{gap:4px}
.player-page:has(.streamlined-player) .fp-v76-timer-icon{font-size:23px}
.player-page:has(.streamlined-player) .mint-clock-label{font-size:clamp(13px,2.6vw,17px)}
.player-page:has(.streamlined-player) .mint-ring-clock{font-size:clamp(37px,10vw,70px)!important;letter-spacing:-2px}
.player-page:has(.streamlined-player) .fp-v76-total{font-size:11px;padding:3px 11px}
.player-page:has(.streamlined-player) .mint-target{
 width:100%;max-width:460px;padding:10px 12px;min-height:52px;
 border-radius:16px;margin:2px auto!important
}
.player-page:has(.streamlined-player) .mint-target>div{
 flex:1;min-width:0;display:flex;align-items:center;flex-direction:column;gap:4px;text-align:center
}
.player-page:has(.streamlined-player) .mint-target>div+div{border-left:1px solid #38564e}
.player-page:has(.streamlined-player) .mint-target .fp-v76-small{font-size:11px}
.player-page:has(.streamlined-player) .mint-target strong{font-size:clamp(14px,3.6vw,19px);overflow-wrap:anywhere}
.player-page:has(.streamlined-player) .btn.primary.full{min-height:53px;margin:5px 0!important;font-size:17px;border-radius:17px}
.player-page:has(.streamlined-player) .mint-rest-actions button{min-height:44px;padding:8px}
.player-page:has(.streamlined-player) .mint-controlbar{margin:0 auto;gap:8px}
.player-page:has(.streamlined-player) .mint-outline{min-height:44px;padding:8px}
.player-page .player-close,.player-page button.player-close{
 display:inline-flex!important;align-items:center!important;justify-content:center!important;
 flex:0 0 45px;width:45px!important;height:45px!important;padding:0!important;
 text-align:center;line-height:1!important;box-sizing:border-box
}
/* Button icons share a single, centered flex alignment. */
button .fp-art,button .fp-v82-control-icon{
 display:inline-block;object-fit:contain;vertical-align:middle;margin:0!important;
 width:20px;height:20px;flex:0 0 20px
}
button:has(>.fp-art),button:has(>.fp-v82-control-icon){
 display:inline-flex!important;align-items:center!important;justify-content:center!important;gap:6px
}
button .fp-art.fp-v82-control-icon{width:22px;height:22px;flex-basis:22px}
.tabbar button .fp-art.nav-icon{display:block;width:27px;height:27px;flex-basis:27px}
@media(max-height:700px){
 .player-page:has(.streamlined-player) .mint-ring{
 width:min(67vw,32dvh,255px)!important;height:min(67vw,32dvh,255px)!important
 }
 .player-page:has(.streamlined-player) .fp-v76-workhead{padding:6px 10px!important}
 .player-page:has(.streamlined-player) .mint-target{min-height:44px;padding:6px 9px}
 .player-page:has(.streamlined-player) .fp-v76-total{display:none}
}
@media(max-height:575px){
 .player-page:has(.streamlined-player) .mint-ring{
 width:min(58vw,26dvh,200px)!important;height:min(58vw,26dvh,200px)!important
 }
 .player-page:has(.streamlined-player) .fp-v76-workhead{display:none}
}
""",'utf8')
print('V8.2 slider, compact player and centered icon patch installed')
