#!/usr/bin/env python3
"""V8 compact UI. Applied last, preserves workout records, engine and data schema."""
from pathlib import Path
p=Path('fitplan/native/app/src/main/assets/app.js');s=p.read_text('utf8')
def change(a,b):
 global s
 assert a in s,'V8 missing anchor: '+a[:100]
 s=s.replace(a,b,1)
def setfunc(a,b,new):
 global s
 i=s.index('function '+a+'(');j=s.index('function '+b+'(',i)
 s=s[:i]+new+'\n'+s[j:]
home=r"""
function homeView(){
 const p=state.profile,active=state.active,h=state.history||[];
 const slots=[...fpProjected().values()],next=slots[0];
 const split=splitProgram().days;
 const name=active?.splitName||next?.dayName||split[state.sessionIndex%split.length][0];
 const wk=new Date(),offset=(wk.getDay()+6)%7;
 wk.setHours(0,0,0,0);wk.setDate(wk.getDate()-offset);
 const completed=h.filter(x=>sessionTime(x)>=wk.getTime()&&mainCount(x)>0);
 const n=Math.max(1,num(p.days,3)),pct=Math.round(Math.min(100,completed.length/n*100));
 let html=head()+'<div class="card hero fp-v76-hero fp-v8-main">'+
  '<div class="fp-v76-head">'+(active?'진행 중인 운동':'다음 운동')+
  (next?.date?'<span class="fp-v76-small">'+next.date+'</span>':'')+'</div>'+
  '<h1>'+esc(name)+'</h1><div class="fp-v8-info">'+fpIcon('clock','tiny-art')+
  (active?.timeLimit||p.duration)+'분 · '+(active?.items?.length||'맞춤')+'종목</div>'+
  '<button class="btn primary full" onclick="Fit.go(&quot;'+(active?'work':'ready')+'&quot;)">'+
  (active?'운동 이어하기':'운동 시작')+'</button></div>'+
  '<div class="card fp-v8-week"><div class="fp-v76-head">이번 주 <strong>'+completed.length+' / '+n+'회</strong></div>'+
  '<div class="fp-v76-progress"><i style="width:'+pct+'%"></i></div>'+
  '<div class="fp-v8-actions"><span>'+(completed.length?completed.length+'회 완료':'첫 운동을 시작해 보세요')+'</span>'+
  '<button class="btn secondary small" onclick="Fit.go(&quot;schedule&quot;)">일정 보기</button></div></div>';
 if(h.length&&mainCount(h[h.length-1]))html+='<div class="fp-v8-recent"><span>최근 운동</span><strong>'+
   esc(h[h.length-1].splitName||'운동')+'</strong><button class="btn tiny secondary" onclick="Fit.go(&quot;state&quot;)">성과</button></div>';
 return html;
}
"""
setfunc('homeView','readyView',home)
change("['home','home','홈'],['work','work','운동'],['history','history','기록'],['state','analytics','분석'],['schedule','schedule','일정']",
       "['home','home','홈'],['work','work','운동'],['schedule','schedule','일정'],['state','analytics','분석']")
change('function go(v){view=v;modal=null;render();window.scrollTo(0,0);}',
"""const fpScreenHistory=[];
function go(v){
 if(v!==view&&view!=='setup'&&fpScreenHistory[fpScreenHistory.length-1]!==view){
  fpScreenHistory.push(view);if(fpScreenHistory.length>24)fpScreenHistory.shift();
 }
 view=v;modal=null;render();window.scrollTo(0,0);
}""")
start=s.index('function fitplanBack(){')
end=s.index('function installFitplanAndroidBack(){',start)
s=s[:start]+"""function fitplanBack(){
 if(modal){modal=null;render();return;}
 if(view==='setup'&&setupPage>0){setupBack();return;}
 if(view==='player'&&state.player){view='work';save();render();return;}
 if(view==='calibration'){view='work';save();render();return;}
 while(fpScreenHistory.length){
  const v=fpScreenHistory.pop();
  if(v&&v!==view&&v!=='setup'){view=v;render();window.scrollTo(0,0);return;}
 }
 if(view!=='home'){view=state.onboard?'home':'setup';render();return;}
 toast('홈 화면입니다');
}
"""+s[end:]
# Analysis: exactly three meaningful metrics and comparison within the SAME exercise.
analysis=r"""
function stateView(){
 const completed=(state.history||[]).filter(h=>mainCount(h)>0);
 if(!completed.length)return head()+'<h1>분석</h1><div class="card fp-v8-empty">'+
  fpIcon('analytics')+'<h2>첫 운동부터 분석을 시작합니다</h2>'+
  '<button class="btn primary full mt12" onclick="Fit.go(&quot;ready&quot;)">운동 시작</button></div>';
 const start=Date.now()-28*86400000,rec=completed.filter(x=>sessionTime(x)>=start);
 const pct=Math.round(Math.min(100,rec.length/(Math.max(1,num(state.profile.days,3))*4)*100));
 const sets=rec.reduce((n,h)=>n+mainCount(h),0);
 const groups=new Map();
 for(const h of completed)for(const [id,v] of Object.entries(sessionStrengths(h))){
  if(!groups.has(id))groups.set(id,[]);
  groups.get(id).push({d:dateLabel(h),v});
 }
 const best=[...groups.entries()].filter(x=>x[1].length>=2).sort((a,b)=>b[1].length-a[1].length)[0];
 const points=best?best[1].slice(-8):[],name=best?exercise(best[0])?.n||'근력 변화':'근력 변화';
 const delta=points.length>1&&points[0].v>0?Math.round((points.at(-1).v/points[0].v-1)*100):null;
 return head()+'<h1>분석</h1><div class="fp-v8-stats">'+
  '<div class="card"><span>'+fpIcon('check','tiny-art')+'지속성</span><strong>'+pct+'%</strong></div>'+
  '<div class="card"><span>'+fpIcon('weight','tiny-art')+'본세트</span><strong>'+sets+'</strong></div>'+
  '<div class="card"><span>'+fpIcon('trend','tiny-art')+'운동</span><strong>'+rec.length+'회</strong></div></div>'+
  '<div class="card"><div class="fp-v76-head">'+esc(name)+
  (delta===null?'<span class="fp-v76-small">비교 기록 부족</span>':'<strong class="accent">'+(delta>0?'+':'')+delta+'%</strong>')+'</div>'+
  (points.length>1?svgGraph(points,name+' 근력 추세','kg'):
    '<div class="empty">같은 운동을 2회 완료하면 변화가 나타납니다.</div>')+'</div>'+
  '<div class="fp-v8-links">'+
  '<button class="btn secondary" onclick="Fit.go(&quot;history&quot;)">'+fpIcon('history','tiny-art')+'전체 기록</button>'+
  '<button class="btn secondary" onclick="Fit.coachInsights()">'+fpIcon('analytics','tiny-art')+'상세 분석</button></div>';
}
"""
setfunc('stateView','v7StateInsights',analysis)
idx=s.index('function historyView(){')
s=s[:idx]+"function coachInsights(){modal={type:'coachInsights'};render();}\n"+s[idx:]
idx=s.index("else if(modal.type==='backup'){")
s=s[:idx]+"""else if(modal.type==='coachInsights'){content='<h2>코치 분석</h2>'+detailedStateView().replace(head(),'');}
 """+s[idx:]
change("window.Fit={", "window.Fit={coachInsights,")
s=s.replace('<p class="sub">오프라인 저장 · 완료한 세트만 다음 운동 처방에 활용</p>','',1)
# Calendar controls remain on one row and precede exercises.
change("(records.length?completed:status==='planned'?expected:'<p class=\"fp-v76-muted\">이 날짜에 기록된 운동이 없습니다.</p>')+controls+'</div>'",
       "controls+(records.length?completed:status==='planned'?expected:'<p class=\"fp-v76-muted\">이 날짜에 기록된 운동이 없습니다.</p>')+'</div>'")
# Schedule edit feedback lists changed future assignments; preserve completed records.
old="state.settings.scheduleOverrides=o;save();render();"
new="""const before=[...fpProjected()].map(([d,slot])=>d+':'+slot.dayName);
 state.settings.scheduleOverrides=o;fpPlanCache=null;save();render();
 const after=[...fpProjected()].map(([d,slot])=>d+':'+slot.dayName);
 const changed=after.filter(x=>!before.includes(x)).length;
 toast(changed?'후속 운동 '+changed+'개 재배치':'일정 변경 완료');"""
change(old,new)
# Alignment of slider with shown minutes; monochrome green track no split blue segments.
change('oninput="Fit.liveMinutes(this.value)" onchange="Fit.setMinutes(this.value)"',
 'style="--fp-pct:__D__{(todayMinutes-30)/90*100}%" oninput="Fit.liveMinutes(this.value);this.style.setProperty(&quot;--fp-pct&quot;,((Number(this.value)-30)/90*100)+&quot;%&quot;)" onchange="Fit.setMinutes(this.value)"')
# Functional voice/time signal sound with a short five-second pre-cue and clear end.
change('const tones=finalAlarm?[{at:0,d:.20,f:980},{at:.25,d:.20,f:1180},{at:.51,d:.36,f:1380}]:',
 'const tones=finalAlarm?[{at:0,d:.12,f:880},{at:.20,d:.12,f:880},{at:.40,d:.12,f:880},{at:.60,d:.68,f:660}]:')
change('const volume=finalAlarm?.26:shortCue?.075:.11;','const volume=finalAlarm?.23:shortCue?.065:.11;')
# Remove redundant label paragraphs (safety explanations untouched).
s=s.replace('<span class="fp-v76-small">개인 맞춤형 운동 코치</span>','',1)
s=s.replace('<p class="sub">기본 시간은 __D__{p.duration}분이지만 오늘만 변경할 수 있어요.</p>','',1)
s=s.replace('오늘의 조건 입력</div><h1>오늘은 얼마나<br>운동할 수 있나요?</h1>',
            '운동 준비</div><h1>오늘의 운동 설정</h1>',1)
# Reuse brand art; V7.7 graphical icons remain intact.
s=s.replace('__D__','$')
p.write_text(s,'utf8')
css=Path('fitplan/native/app/src/main/assets/style.css')
css.write_text(css.read_text('utf8')+"""
/* V8: focused main screens, consistent controls, high-density no duplicate cards */
.fp-head{padding:16px 0 12px}.fp-v8-main{margin-top:5px!important}
.fp-v8-main h1{margin:8px 0 12px!important}
.fp-v8-info{display:flex;align-items:center;color:#b7cbbd;font-size:14px;margin:0 0 16px}
.fp-v8-week .fp-v76-head{margin-bottom:11px}
.fp-v8-actions,.fp-v8-recent{display:flex;justify-content:space-between;align-items:center;gap:9px;margin-top:12px;font-size:13px}
.fp-v8-recent{padding:12px 7px}.fp-v8-recent>span{color:#aac0b5}.fp-v8-recent strong{flex:1}
.fp-v8-stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:14px}
.fp-v8-stats>.card{margin:0;padding:13px 7px;border-radius:18px;text-align:center}
.fp-v8-stats>.card span{display:flex;align-items:center;justify-content:center;gap:3px;color:#b6cbbd;font-size:11px}
.fp-v8-stats>.card strong{display:block;font-size:23px;margin-top:7px}
.fp-v8-links{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin:15px 0}
.fp-v8-links button{min-height:52px}
.fp-v8-empty{text-align:center;padding:25px}.fp-v8-empty .fp-art{width:51px;height:51px;display:block;margin:auto}
.fp-calendar-actions{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}
.fp-calendar-actions button{min-width:0;padding:11px 1px;font-size:13px;white-space:nowrap}
button{touch-action:manipulation}
:where(button,input):focus-visible{outline:2px solid #7cff9c;outline-offset:2px}
input[type=range]{appearance:none;-webkit-appearance:none;width:100%;height:9px;border-radius:99px;border:0;background:linear-gradient(to right,#3cec70 0%,#3cec70 var(--fp-pct,33%),#384d46 var(--fp-pct,33%),#384d46 100%);margin:22px 0}
input[type=range]::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:23px;height:23px;background:#70ff90;border:3px solid #deffe7;border-radius:50%;box-shadow:0 0 0 4px #18412c}
.mint-arc{stroke-linecap:butt;transition:stroke-dasharray .16s linear}
@media(max-width:390px){.fp-v8-stats>.card span{font-size:10px}.fp-v8-stats>.card strong{font-size:19px}}
""",'utf8')
print('FitPlan V8 compact interface and back navigation installed')
