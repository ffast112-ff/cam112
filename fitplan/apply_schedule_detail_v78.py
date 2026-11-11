#!/usr/bin/env python3
"""FitPlan V7.8 safe UI extension after V7.7 asset patch."""
from pathlib import Path
p=Path('fitplan/native/app/src/main/assets/app.js');s=p.read_text('utf8')
a=s.index('function fpDays(){'); b=s.index('function moveCalendar(n){',a)
replacement=r"""
function fpDays(){
 const a=state.settings.trainingWeekdays;
 return Array.isArray(a)?[...new Set(a.map(Number).filter(x=>Number.isInteger(x)&&x>=0&&x<7))].sort():[];
}
function fpDone(){
 const done=new Set();
 for(const h of state.history||[]){
  if(mainCount(h)<1)continue;
  const t=sessionTime(h),d=t>0?new Date(t):null;
  if(d&&!isNaN(d.getTime()))done.add(fpDate(d));
  else if(/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(h.date||''))done.add(h.date);
 }return done;
}
let fpPlanCache=null,fpPlanCacheKey='';
function fpProjected(){
 const key=[fpDate(new Date()),state.history?.length||0,state.sessionIndex||0,
  state.profile.days,fpDays().join(','),state.planMemory?.split||''].join('|');
 if(fpPlanCache&&fpPlanCacheKey===key)return fpPlanCache;
 const plans=new Map();
 try{
  const prog=FitPlanPrecisionV75.planProgram({
   profile:state.profile,catalog:CATALOG,history:state.history,
   sessionIndex:state.sessionIndex,weeks:4,availableWeekdays:fpDays(),
   readiness:{energy:3,soreness:2,sleep:3,pain:false},
   context:{planMemory:state.planMemory,pace:FitPlanAdvanced.pace(state.history).factor,now:Date.now()}
  });
  for(const slot of prog?.rolling?.slots||[])if(/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(slot.date))plans.set(slot.date,slot);
 }catch(e){console.warn('Calendar projection failed',e);}
 fpPlanCacheKey=key;fpPlanCache=plans;return plans;
}
function fpStatus(d,done,plan){
 const date=fpDate(d);
 if(done.has(date))return 'done';
 const override=state.settings.scheduleOverrides?.[date];
 if(override==='planned'||override==='rest')return override;
 if(date<fpDate(new Date()))return 'rest';
 return plan.has(date)?'planned':'rest';
}
function fpRecords(date){
 return (state.history||[]).filter(h=>{
  const t=sessionTime(h);return mainCount(h)>0&&t>0&&fpDate(new Date(t))===date;
 });
}
function fpPrediction(slot){
 if(!slot)return null;
 let exercises=[];
 try{
  const day=FitPlanPrecisionV75.planDay({
   profile:state.profile,catalog:CATALOG,history:state.history,
   sessionIndex:slot.sessionIndex,minutes:state.profile.duration,
   availableWeekdays:fpDays(),readiness:{energy:3,soreness:2,sleep:3,pain:false},
   context:{planMemory:state.planMemory,pace:FitPlanAdvanced.pace(state.history).factor,now:Date.now()}
  });
  exercises=(day?.items||[]).map(it=>exercise(it.id)?.n||it.name||'운동').slice(0,12);
 }catch(e){console.warn('Exercise preview failed',e);}
 if(!exercises.length){
  const patterns=splitProgram().days.find(x=>x[0]===slot.dayName)?.[1]||[];
  exercises=patterns.map(x=>PATTERN_NAME[x]||x);
 }
 return {name:slot.dayName||'운동 예정',exercises};
}
function scheduleView(){
 const year=fpCalendarMonth.getFullYear(),m=fpCalendarMonth.getMonth(),
  start=new Date(year,m,1).getDay(),done=fpDone(),plans=fpProjected(),today=fpDate(new Date());
 if(!fpSelectedDate)fpSelectedDate=today;
 const days=Array.from({length:42},(_,i)=>{
  const d=new Date(year,m,1-start+i),date=fpDate(d),type=fpStatus(d,done,plans);
  return '<button class="fp-day '+type+(d.getMonth()!==m?' outside':'')+
   (date===today?' today':'')+(date===fpSelectedDate?' selected':'')+
   '" onclick="Fit.selectCalendar(&quot;'+date+'&quot;)">'+d.getDate()+'</button>';
 }).join('');
 const selected=new Date(fpSelectedDate+'T12:00:00'),status=fpStatus(selected,done,plans),
  records=fpRecords(fpSelectedDate),preview=status==='planned'?fpPrediction(plans.get(fpSelectedDate)):null;
 const stats={done:0,planned:0,rest:0};
 for(let day=1;day<=new Date(year,m+1,0).getDate();day++)stats[fpStatus(new Date(year,m,day),done,plans)]++;
 const completed=records.map(h=>{
  const items=(h.items||[]).map(it=>{
   const sets=(it.sets||[]).filter(z=>z.done&&!z.warmup&&z.role!=='warmup');
   if(!sets.length)return '';
   const e=exercise(it.currentId||it.eid||it.id),w=Math.max(0,...sets.map(x=>num(x.actualWeight)));
   return '<div class="fp-v76-row"><span>'+esc(e?.n||'운동')+
    '</span><strong>'+sets.length+'세트'+(w>0?' · '+formatWeight(w)+'kg':'')+'</strong></div>';
  }).filter(Boolean).join('');
  return '<div class="subhead"><strong>'+esc(h.splitName||'완료한 운동')+'</strong>'+items+'</div>';
 }).join('');
 const expected=preview?'<div class="subhead"><strong>'+esc(preview.name)+
   '</strong><p class="fp-v76-muted">예상 종목입니다. 실제 종목·중량·세트는 운동 당일 재계산합니다.</p>'+
   preview.exercises.map(x=>'<div class="fp-v76-row"><span>'+esc(x)+'</span></div>').join('')+'</div>':
   '<p class="fp-v76-muted">아직 구체적인 종목이 확정되지 않았습니다. 운동 가능일을 지정하면 계획을 재계산합니다.</p>';
 const controls=status==='done'?'':'<div class="fp-calendar-actions"><button class="btn secondary" onclick="Fit.markCalendar(&quot;planned&quot;)">운동 예정</button>'+
  '<button class="btn secondary" onclick="Fit.markCalendar(&quot;rest&quot;)">휴식</button>'+
  '<button class="btn outline" onclick="Fit.markCalendar(&quot;auto&quot;)">자동</button></div>';
 return head()+'<div class="fp-v76-head">'+fpIcon('schedule')+' 운동 일정</div>'+
  '<div class="card"><div class="fp-calendar-head"><button onclick="Fit.moveCalendar(-1)">'+fpIcon('back')+'</button><strong>'+year+'년 '+(m+1)+'월</strong><button onclick="Fit.moveCalendar(1)">'+fpIcon('next')+'</button></div>'+
  '<div class="fp-calendar-grid fp-weekdays">'+['일','월','화','수','목','금','토'].map(x=>'<span>'+x+'</span>').join('')+'</div>'+
  '<div class="fp-calendar-grid">'+days+'</div><div class="fp-calendar-legend"><span>● 완료</span><span>○ 예정</span><span>– 미정·휴식</span></div></div>'+
  '<div class="card"><div class="fp-v76-head">'+fpIcon('calendar_today')+' '+fpSelectedDate+' · '+(status==='done'?'운동 완료':status==='planned'?'운동 예정':'미정·휴식')+'</div>'+
  (records.length?completed:status==='planned'?expected:'<p class="fp-v76-muted">이 날짜에 기록된 운동이 없습니다.</p>')+controls+'</div>'+
  '<div class="card"><div class="fp-v76-head">'+fpIcon('analytics')+' 이번 달 현황</div><div class="fp-v76-ministats"><div>완료<span class="value">'+stats.done+'일</span></div><div>예정<span class="value">'+stats.planned+'일</span></div><div>미정·휴식<span class="value">'+stats.rest+'일</span></div></div></div>'+
  '<div class="card"><div class="fp-v76-head">'+fpIcon('schedule')+' 운동 가능한 요일</div>'+
  '<p class="fp-v76-muted">요일을 지정하지 않으면 향후 2주를 V7.5가 자동 최적화합니다.</p>'+
  '<div class="chips mt12">'+['일','월','화','수','목','금','토'].map((d,i)=>
   '<button class="chip '+(fpDays().includes(i)?'selected':'')+'" onclick="Fit.trainingWeekday('+i+')">'+d+'</button>').join('')+'</div>'+
  '<button class="btn secondary full mt12" onclick="Fit.trainingWeekday(-1)">요일 제한 해제 · 자동 최적화</button></div>'+
  '<div class="card"><div class="fp-v76-head">'+fpIcon('schedule')+' 홈 화면 위젯</div>'+
  '<p class="fp-v76-muted">홈 화면 길게 누르기 → 위젯 → FitPlan 일정</p>'+
  '<button class="btn secondary" onclick="Fit.todayCalendar()">오늘로 이동</button></div>';
}
"""
s=s[:a]+replacement+s[b:]
old="window.FitPlanNative.syncSchedule(JSON.stringify({done:[...fpDone()],weekdays:fpDays(),overrides:state.settings.scheduleOverrides||{}}))"
assert old in s
s=s.replace(old,"window.FitPlanNative.syncSchedule(JSON.stringify({done:[...fpDone()],plannedDates:[...fpProjected().keys()],weekdays:fpDays(),overrides:state.settings.scheduleOverrides||{}}))",1)
old="state.settings.trainingWeekdays=days;save();render();"
assert old in s
s=s.replace(old,"state.settings.trainingWeekdays=days;fpPlanCache=null;save();render();",1)
# Provide image icons for headers and controls without destructive source substitutions.
idx=s.index('function nav(){')
extra=r"""
const FP_DECOR={'▶':'play','▷':'play','▥':'analytics','▦':'schedule','▰':'work',
 '▣':'schedule','◷':'clock','◉':'check','✓':'check','↻':'recovery','↺':'recovery',
 '◎':'target','◴':'timer','⚙':'settings','✕':'remove','⊕':'add'};
function fpEnhanceIcons(root){
 const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT),pending=[];
 let n;
 while((n=walker.nextNode())){
  if(!n.parentElement?.closest('button,.fp-v76-head,.fp-v76-row,.sectionhead,.eyebrow,.pill,.tile,.callout,.subhead'))continue;
  const m=n.nodeValue.match(/^(\\s*)([▶▷▥▦▰▣◷◉✓↻↺◎◴⚙✕⊕])(?=\\s|$)/);
  if(m)pending.push([n,m[1],m[2]]);
 }
 for(const [node,space,mark] of pending){
  const holder=document.createElement('span');
  holder.innerHTML=fpIcon(FP_DECOR[mark],'tiny-art');
  node.parentNode.insertBefore(holder,node);
  node.nodeValue=space+node.nodeValue.slice(space.length+mark.length);
 }
}
"""
extra=extra.replace('\\\\s','\\s')
s=s[:idx]+extra+s[idx:]
needle="if(view==='player'||view==='calibration')syncAwake();"
assert needle in s
s=s.replace(needle,"fpEnhanceIcons(e);\n "+needle,1)
p.write_text(s,'utf8')
css=Path('fitplan/native/app/src/main/assets/style.css')
css.write_text(css.read_text('utf8')+'\n.fp-art.tiny-art{width:18px;height:18px;margin-right:4px}.fp-v76-row span{overflow-wrap:anywhere}.fp-calendar-actions button{min-height:44px}\n','utf8')
print('FitPlan V7.8 adaptive schedule details and detail icon pass applied')
