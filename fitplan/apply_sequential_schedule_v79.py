#!/usr/bin/env python3
"""Integrate the sequential FitPlan workout queue without changing training engine or layout."""
from pathlib import Path
src=Path('fitplan/native/app/src/main/assets')
app=src/'app.js'
s=app.read_text(encoding='utf-8')
index=src/'index.html'
html=index.read_text(encoding='utf-8')
queue=Path('fitplan/schedule-queue-v79.js')
assert queue.exists()
(src/'schedule-queue-v79.js').write_bytes(queue.read_bytes())
# The queue must execute before app.js. The existing V7.5 bundle remains unmodified.
assert '<script src="app.js"></script>' in html, "App entrypoint missing"
html=html.replace('<script src="app.js"></script>','<script src="schedule-queue-v79.js"></script><script src="app.js"></script>',1)
index.write_text(html,encoding='utf-8')
start=s.index('function fpProjected(){')
end=s.index('function fpStatus(',start)
new=r"""
function fpProjected(){
 const overrides=state.settings.scheduleOverrides||{};
 const splitNames=splitProgram().days.map(day=>day[0]);
 const fingerprint=JSON.stringify({
   date:fpDate(new Date()),sessionIndex:state.sessionIndex,history:state.history?.map(h=>[h.finishedAt,h.timestamp,h.date,h.splitName]),
   days:state.profile.days,weekdays:fpDays(),overrides,splitNames,planMemory:state.planMemory?.split||''
 });
 if(fpPlanCache&&fpPlanCacheKey===fingerprint)return fpPlanCache;
 let baseSlots=[];
 try{
  const prog=FitPlanPrecisionV75.planProgram({
   profile:state.profile,catalog:CATALOG,history:state.history,
   sessionIndex:state.sessionIndex,weeks:4,availableWeekdays:fpDays(),
   readiness:{energy:3,soreness:2,sleep:3,pain:false},
   context:{planMemory:state.planMemory,pace:FitPlanAdvanced.pace(state.history).factor,now:Date.now()}
  });
  baseSlots=prog?.rolling?.slots||[];
 }catch(e){console.warn('Calendar base projection failed',e);}
 // Source of truth: candidate dates + actual completed sessionIndex.
 // A skipped day never consumes a split. Adding a day moves every subsequent split forward.
 const plans=FitPlanScheduleQueue.assign({
  baseSlots,overrides,completedDates:fpDone(),
  sessionIndex:state.sessionIndex,splitNames,today:fpDate(new Date())
 });
 fpPlanCacheKey=fingerprint;fpPlanCache=plans;return plans;
}
"""
s=s[:start]+new+s[end:]
# Keep future workout assignment in a single queue; no alternate calculation based on Map length.
fallback="""preview=status==='planned'?fpPrediction(plans.get(fpSelectedDate)||{
   sessionIndex:state.sessionIndex+[...plans.keys()].filter(x=>x<fpSelectedDate).length,
   dayName:splitProgram().days[(state.sessionIndex+[...plans.keys()].filter(x=>x<fpSelectedDate).length)%splitProgram().days.length][0]
  }):null;"""
if fallback not in s:
    raise RuntimeError('Calendar preview fallback changed; refusing unsafe patch')
s=s.replace(fallback,"preview=status==='planned'?fpPrediction(plans.get(fpSelectedDate)):null;",1)
# fpStatus accepts a manual override for a date outside rolling horizon; it must not fabricate a split.
# UI clearly states that older manually planned dates outside the near-term horizon lack an assigned session.
app.write_text(s,encoding='utf-8')
print('FitPlan V7.9 schedule queue integrated')
