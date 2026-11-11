#!/usr/bin/env python3
from pathlib import Path
import shutil
p=Path('fitplan/native/app/src/main/assets/app.js');s=p.read_text('utf8')
base=p.parent
shutil.copyfile('fitplan/icons-v77.svg',base/'icons-v77.svg')
D=chr(36)
def change(a,b):
 global s
 assert a in s, ('Missing UI anchor',a[:75])
 s=s.replace(a,b,1)
change("function nav(){const tabs=[['home','⌂','홈'],['work','▰','운동'],['history','▤','기록'],['state','▥','분석']];",
       "function nav(){const tabs=[['home','home','홈'],['work','work','운동'],['history','history','기록'],['state','analytics','분석'],['schedule','schedule','일정']];")
change('<span aria-hidden="true">'+D+'{ico}</span><small>'+D+'{label}</small>',D+'{fpIcon(ico,"nav-icon")}<small>'+D+'{label}</small>')
insert="""
const FP_ICONS=new Set(['home','work','history','analytics','schedule','settings','trend','check','recovery','timer','play','pause','next','back','add','remove','weight','target','rest','notification','finish','edit','clock','calendar_today','heart']);
function fpIcon(k,cls=''){return '<svg class="fp-art '+cls+'" role="img" aria-label="'+k+'"><use href="icons-v77.svg#'+(FP_ICONS.has(k)?k:'target')+'"></use></svg>';}
let fpCalendarMonth=new Date(new Date().getFullYear(),new Date().getMonth(),1);
let fpSelectedDate='';
function fpDate(d){return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');}
function fpDays(){
 let a=state.settings.trainingWeekdays;
 if(Array.isArray(a)&&a.length)return a.map(Number).filter(x=>x>=0&&x<7);
 const n=Math.min(7,Math.max(1,Math.round(num(state.profile.days,3))));
 return Array.from({length:n},(_,i)=>(1+Math.floor((i+.5)*7/n))%7);
}
function fpDone(){
 const set=new Set();
 for(const h of state.history||[]){
  if(mainCount(h)<1)continue;
  const t=sessionTime(h),d=t?new Date(t):null;
  if(d&&!isNaN(d.getTime()))set.add(fpDate(d));
  else if(/^\\\\d{4}-\\\\d{2}-\\\\d{2}$/.test(h.date||''))set.add(h.date);
 }
 return set;
}
function fpStatus(d,done){
 if(done.has(fpDate(d)))return 'done';
 const o=state.settings.scheduleOverrides?.[fpDate(d)];
 return o==='planned'||o==='rest'?o:fpDays().includes(d.getDay())?'planned':'rest';
}
function scheduleView(){
 const month=fpCalendarMonth,year=month.getFullYear(),mm=month.getMonth(),offset=new Date(year,mm,1).getDay(),done=fpDone(),today=fpDate(new Date());
 if(!fpSelectedDate)fpSelectedDate=today;
 const cells=Array.from({length:42},(_,i)=>{
  let d=new Date(year,mm,1-offset+i),day=fpDate(d),kind=fpStatus(d,done);
  return '<button class="fp-day '+kind+(d.getMonth()!==mm?' outside':'')+(day===today?' today':'')+(day===fpSelectedDate?' selected':'')+'" onclick="Fit.selectCalendar(\\''+day+'\\')">'+d.getDate()+'</button>';
 }).join('');
 const chosen=new Date(fpSelectedDate+'T12:00:00'),kind=fpStatus(chosen,done);
 let counts={done:0,planned:0,rest:0};
 for(let i=1;i<=new Date(year,mm+1,0).getDate();i++){let k=fpStatus(new Date(year,mm,i),done);counts[k]++;}
 return head()+'<div class="fp-v76-head">'+fpIcon('schedule')+' 운동 일정</div>'
 +'<div class="card"><div class="fp-calendar-head"><button onclick="Fit.moveCalendar(-1)">'+fpIcon('back')+'</button><strong>'+year+'년 '+(mm+1)+'월</strong><button onclick="Fit.moveCalendar(1)">'+fpIcon('next')+'</button></div>'
 +'<div class="fp-calendar-grid fp-weekdays">'+['일','월','화','수','목','금','토'].map(x=>'<span>'+x+'</span>').join('')+'</div>'
 +'<div class="fp-calendar-grid">'+cells+'</div><div class="fp-calendar-legend"><span>● 운동 완료</span><span>◯ 운동 예정</span><span>– 휴식</span></div></div>'
 +'<div class="card"><div class="fp-v76-head">'+fpIcon('calendar_today')+' '+fpSelectedDate+' · '+(kind==='done'?'운동 완료':kind==='planned'?'운동 예정':'휴식')+'</div>'
 +(kind==='done'?'<p class="fp-v76-muted">운동 완료 기록에서 자동으로 반영되었습니다.</p>':'<div class="fp-calendar-actions"><button class="btn secondary" onclick="Fit.markCalendar(\\'planned\\')">운동 예정</button><button class="btn secondary" onclick="Fit.markCalendar(\\'rest\\')">휴식</button><button class="btn outline" onclick="Fit.markCalendar(\\'auto\\')">자동</button></div>')+'</div>'
 +'<div class="card"><div class="fp-v76-head">'+fpIcon('analytics')+' 이번 달 현황</div><div class="fp-v76-ministats"><div>완료<span class="value">'+counts.done+'일</span></div><div>예정<span class="value">'+counts.planned+'일</span></div><div>휴식<span class="value">'+counts.rest+'일</span></div></div></div>'
 +'<div class="card"><div class="fp-v76-head">'+fpIcon('schedule')+' 홈 화면 위젯</div><p class="fp-v76-muted">휴대전화 홈 화면 길게 누르기 → 위젯 → FitPlan 일정. 크기 조절에 따라 작은 요약 또는 월간 달력을 표시합니다.</p><button class="btn secondary" onclick="Fit.todayCalendar()">오늘로 이동</button></div>';
}
function moveCalendar(n){fpCalendarMonth=new Date(fpCalendarMonth.getFullYear(),fpCalendarMonth.getMonth()+n,1);render();}
function selectCalendar(s){fpSelectedDate=s;render();}
function todayCalendar(){fpSelectedDate=fpDate(new Date());fpCalendarMonth=new Date(new Date().getFullYear(),new Date().getMonth(),1);render();}
function markCalendar(k){
 let o=state.settings.scheduleOverrides||{};
 if(k==='auto')delete o[fpSelectedDate];else o[fpSelectedDate]=k;
 state.settings.scheduleOverrides=o;save();render();
}
function syncWidget(){
 try{if(window.FitPlanNative?.syncSchedule)window.FitPlanNative.syncSchedule(JSON.stringify({done:[...fpDone()],weekdays:fpDays(),overrides:state.settings.scheduleOverrides||{}}));}
 catch(e){console.warn('Calendar widget sync unavailable',e);}
}
"""
# Revert escapes used when embedding JavaScript single-quote in HTML onclick
insert=insert.replace("\\\\'","\\'")
s=s.replace('function nav(){',insert+chr(10)+'function nav(){',1)
change(" nativeSync();\n}", " nativeSync();syncWidget();\n}")
change("else if(view==='history')page=historyView();","else if(view==='history')page=historyView();else if(view==='schedule')page=scheduleView();")
change("window.Fit={quickLastRir,","window.Fit={moveCalendar,selectCalendar,todayCalendar,markCalendar,quickLastRir,")
change('<span class="barbell-logo">━●━</span>','<span class="barbell-logo">'+D+'{fpIcon("work")}</span>')
change('aria-label="설정">⚙</button>','aria-label="설정">'+D+'{fpIcon("settings")}</button>')
# graphical images for small and large decorative UI headings, buttons, and secondary sections
for mark,k in [('▥','analytics'),('▦','schedule'),('▰','work'),('◷','clock'),('◉','check'),('✓','check'),('▶','play'),('↻','recovery'),('◎','target'),('◴','timer')]:
 for suffix in [' ','<']:
  s=s.replace('>'+mark+suffix,'>'+D+'{fpIcon("'+k+'")}'+suffix)
# status icons, title icons, and tool buttons rendered via a unified image atlas
p.write_text(s,'utf8')
css="""
.fp-art{display:inline-block;width:23px;height:23px;vertical-align:middle;margin-right:5px;filter:drop-shadow(0 0 3px #21ee7080);flex-shrink:0}
.fp-art.nav-icon{width:27px;height:27px;margin:0 0 4px}.tabbar{display:flex;justify-content:space-between}
.tabbar button{flex:1;min-width:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.barbell-logo .fp-art{width:37px;height:37px;margin:0}
.fp-calendar-head{display:flex;align-items:center;justify-content:space-between;font-size:22px;margin-bottom:18px}
.fp-calendar-head button{background:#203039;border:1px solid #4d6868;border-radius:14px;padding:8px}
.fp-calendar-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px;text-align:center}
.fp-weekdays{font-size:12px;color:#9cadb8;margin-bottom:12px}
.fp-day{aspect-ratio:1;border-radius:50%;border:1px solid transparent;background:#102127;color:#eafff2;font-size:14px;min-height:31px;padding:1px}
.fp-day.done{background:linear-gradient(145deg,#aaffb2,#11df5a);color:#031e0b;font-weight:900}
.fp-day.planned{border:2px solid #48f27b}.fp-day.rest{color:#8eabb2}
.fp-day.outside{opacity:.24}.fp-day.today{box-shadow:0 0 0 2px #d4ffe4,0 0 12px #42f986}
.fp-day.selected{outline:2px solid #93ffae;outline-offset:2px}
.fp-calendar-legend{display:flex;justify-content:space-between;gap:4px;font-size:11px;color:#bbd4c8;margin-top:18px}
.fp-calendar-actions{display:flex;flex-wrap:wrap;gap:7px;margin-top:12px}.fp-calendar-actions button{flex:1}
"""
q=base/'style.css';q.write_text(q.read_text('utf8')+'\\n'+css,'utf8')
print('FitPlan schedule and image icon atlas integrated')
