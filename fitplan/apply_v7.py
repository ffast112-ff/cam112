from pathlib import Path
base=Path('fitplan/native/app/src/main/assets')
p=base/'app.js'
s=p.read_text(encoding='utf8')
old='const result=FitPlanPrecisionV4.planDay({profile:state.profile,readiness:rdy,catalog:CATALOG,'
new='const result=FitPlanPrecisionV7.planDay({profile:state.profile,readiness:rdy,catalog:CATALOG,'
assert old in s;s=s.replace(old,new,1)
old='history:state.history,sessionIndex:state.sessionIndex,minutes,context:{planMemory:state.planMemory,pace:FitPlanAdvanced.pace(state.history).factor}});'
new='history:state.history,sessionIndex:state.sessionIndex,minutes,availableWeekdays:state.settings.trainingWeekdays||[],context:{planMemory:state.planMemory,pace:FitPlanAdvanced.pace(state.history).factor}});'
assert old in s;s=s.replace(old,new,1)
# V7 runtime failure must not interrupt an active training session.
needle="const result=FitPlanPrecisionV7.planDay({profile:state.profile,readiness:rdy,catalog:CATALOG,"
assert needle in s
s=s.replace(needle,"const plannerInput={profile:state.profile,readiness:rdy,catalog:CATALOG,",1)
needle="history:state.history,sessionIndex:state.sessionIndex,minutes,availableWeekdays:state.settings.trainingWeekdays||[],context:{planMemory:state.planMemory,pace:FitPlanAdvanced.pace(state.history).factor}});"
assert needle in s
s=s.replace(needle,"""history:state.history,sessionIndex:state.sessionIndex,minutes,availableWeekdays:state.settings.trainingWeekdays||[],context:{planMemory:state.planMemory,pace:FitPlanAdvanced.pace(state.history).factor}};
 let result;
 try{result=window.FitPlanPrecisionV7?.planDay(plannerInput)||FitPlanPrecisionV4.planDay(plannerInput);}
 catch(error){console.warn('V7 fallback to V4',error);result=FitPlanPrecisionV4.planDay(plannerInput);}""",1)
# Keep V4 machine-specific load decisions and add V7's bounded recovery-day reduction.
old='const adjusted=load?(knownLoad===null?0:Math.max(unit,roundTo(knownLoad*(z.role===\'warmup\'?.5:z.role===\'backoff\'?.9:1),unit))):initial;'
new='const adjusted=load?(knownLoad===null?0:Math.max(unit,roundTo(knownLoad*(z.role===\'warmup\'?.5:z.role===\'backoff\'?.9:1)*(it.v7LoadFactor||1),unit))):initial;'
assert old in s;s=s.replace(old,new,1)
old='targetWeight:adjusted,targetReps:z.targetReps,'
new='targetWeight:adjusted,targetReps:z.targetReps,targetRIR:z.targetRIR,'
assert old in s;s=s.replace(old,new,1)
old='return {schema:46,engineVersion:result.version||\'4.0\',optimizer:result.optimizer,'
new='return {schema:46,engineVersion:result.version||\'4.0\',v7:result.v7,optimizer:result.optimizer,'
assert old in s;s=s.replace(old,new,1)
old='const program=FitPlanPrecisionV4.planProgram({profile:state.profile,catalog:CATALOG,history:state.history,readiness,weeks:num(state.settings.programWeeks,8),sessionIndex:state.sessionIndex,context:{planMemory:state.planMemory}});'
new='const program=FitPlanPrecisionV7.planProgram({profile:state.profile,catalog:CATALOG,history:state.history,readiness,weeks:num(state.settings.programWeeks,8),sessionIndex:state.sessionIndex,availableWeekdays:state.settings.trainingWeekdays||[],context:{planMemory:state.planMemory}});'
assert old in s;s=s.replace(old,new,1)
old='return `<div class="card precision-v4-card"><div class="row"><strong>V4 루틴 처방 근거</strong>'
new='return `<div class="card precision-v4-card"><div class="row"><strong>V7.4 적응형 코치 · V4 기본 엔진</strong>'
assert old in s;s=s.replace(old,new,1)
# Also make long-range preview fault-tolerant for older saved histories.
needle="const program=FitPlanPrecisionV7.planProgram({profile:state.profile,catalog:CATALOG,history:state.history,readiness,weeks:num(state.settings.programWeeks,8),sessionIndex:state.sessionIndex,availableWeekdays:state.settings.trainingWeekdays||[],context:{planMemory:state.planMemory}});"
assert needle in s
s=s.replace(needle,"""const programInput={profile:state.profile,catalog:CATALOG,history:state.history,readiness,weeks:num(state.settings.programWeeks,8),sessionIndex:state.sessionIndex,availableWeekdays:state.settings.trainingWeekdays||[],context:{planMemory:state.planMemory}};
 let program;
 try{program=window.FitPlanPrecisionV7?.planProgram(programInput)||FitPlanPrecisionV4.planProgram(programInput);}
 catch(error){console.warn('V7 program fallback',error);program=FitPlanPrecisionV4.planProgram(programInput);}""",1)
# Embed v7 summary in optimizer card without removing preexisting V4 comparisons
needle='<p class="sub mt8">${esc(review.reason||\'운동 분할과 오늘의 운동량을 함께 계산했습니다.\')}</p>'
assert needle in s
s=s.replace(needle,needle+'''\n  ${s.v7?`<div class="subhead"><strong>개인별 학습</strong><p class="sub">분석한 운동 ${s.v7.model.samples}회 · 신뢰도 ${Math.round(s.v7.model.confidence*100)}% · 기존 V4 대비 세트 변경 ${s.v7.comparison.deltaSets>0?'+':''}${s.v7.comparison.deltaSets} · 2주 예정 ${s.v7.rolling.slots.length}회</p><p class="sub">${esc(s.v7.changes.map(x=>x.muscle+' '+(x.sets>0?'+':'')+x.sets+'세트: '+x.reason).join(' / ')||'기록이 충분하지 않거나 현재 구성에 문제가 없어 기존 운동량을 유지합니다.')}</p><details class="v4-details"><summary>향후 2주 훈련 배치 보기</summary>${s.v7.rolling.slots.map(z=>`<p class="sub">${esc(z.date)} · ${esc(z.dayName)} (${esc(z.muscles.join(' · '))})</p>`).join('')}</details></div>`:''}''',1)
# Schedule UI, only 1 optional group and no new permissions.
needle=' <div class="sectionhead"><h2>음성 코치 · 장기 계획</h2></div>'
assert needle in s
add=''' <div class="sectionhead"><h2>V7 적응형 훈련 일정</h2></div><div class="card"><strong>운동 가능한 요일</strong><p class="sub">요일을 선택하지 않으면 주 ${p.days}일을 균등하게 분산합니다. 선택한 요일은 장기 계획의 우선 배치에 사용됩니다.</p><div class="chips mt8">${['일','월','화','수','목','금','토'].map((day,i)=>`<button class="chip ${(state.settings.trainingWeekdays||[]).includes(i)?'selected':''}" onclick="Fit.trainingWeekday(${i})">${day}</button>`).join('')}</div><button class="btn secondary full mt12" onclick="Fit.trainingWeekday(-1)">요일 지정 해제 · 균등 배치</button></div>\n'''
s=s.replace(needle,add+needle,1)
needle='${p.calendar.map(w=>`<details class="v4-details"'
assert needle in s
s=s.replace(needle,'''${p.rolling?`<div class="subhead"><strong>V7 · 향후 2주 실제 가능일 기반 배치</strong><p class="sub">${esc(p.rolling.explanation)}</p>${p.rolling.slots.map(s=>`<div class="row mt8"><span>${esc(s.date)}</span><strong>${esc(s.dayName)}</strong></div>`).join('')}</div>`:''}\n '''+needle,1)
needle='${cycleWidget()}${advancedStateInsights()}${extendedStateInsights()}${v5MuscleQuality()}'
assert needle in s
s=s.replace(needle,'${cycleWidget()}${v7StateInsights()}${advancedStateInsights()}${extendedStateInsights()}${v5MuscleQuality()}',1)
needle='<div class="tiny muted mt8">휴식 ${it.rest}초</div></div>`;}'
assert needle in s
s=s.replace(needle,"<div class=\"tiny muted mt8\">휴식 ${it.rest}초 · 목표 RIR ${it.sets.find(z=>!z.warmup)?.targetRIR??2}회</div></div>`;}",1)
# Preserve bounded adjustment audit, not redundant entire 2-week forecast per session.
needle='s.feedback=deep(feedback);s.bodyweight=s.feedback.weight;s.difficulty=s.feedback.difficulty;'
assert needle in s
s=s.replace(needle,needle+"""
 if(s.v7){const v=s.v7;s.v7={changes:(v.changes||[]).map(x=>({muscle:x.muscle,sets:x.sets})).slice(0,12),confidence:v.model?.confidence||0,comparison:{baseSets:v.comparison?.baseSets||0,newSets:v.comparison?.newSets||0,deltaSets:v.comparison?.deltaSets||0}};}""",1)
needle='function historyView(){'
assert needle in s
add='''function v7StateInsights(){
 try{
  const model=FitPlanPrecisionV7.learn({history:state.history,catalog:CATALOG,profile:state.profile});
  const audit=FitPlanPrecisionV7.audit({history:state.history,catalog:CATALOG,profile:state.profile});
  const muscles=Object.values(model.muscles).filter(x=>x.sessions>0).sort((a,b)=>b.sessions-a.sessions).slice(0,6);
  return `<div class="sectionhead"><h2>V7.4 · 개인 적응형 분석</h2></div><div class="card"><div class="grid2"><div class="stat"><div class="tiny muted">성과 학습 신뢰도</div><strong>${Math.round(model.confidence*100)}%</strong></div><div class="stat"><div class="tiny muted">누적 분석 운동</div><strong>${model.samples}회</strong></div></div>${muscles.map(x=>`<div class="subhead"><strong>${esc(x.muscle)}</strong><p class="sub">${x.sessions}회 · 피로 지표 ${x.fatigue} · ${esc(x.reason)}</p></div>`).join('')}<div class="subhead"><strong>시간 순서 기반 기록 검증</strong><p class="sub">기록 ${audit.records}회 · 수행률 ${Math.round(audit.observed.completion*100)}% · 통증 보고 ${Math.round(audit.observed.painReports*100)}%</p><p class="tiny muted">과거 V4 기록만으로 V7이 더 효과적이라고 증명할 수는 없습니다. 실제 운동 성과를 계속 비교합니다.</p></div></div>`;
 }catch(e){console.warn('V7 state view',e);return '';}
}
'''
s=s.replace(needle,add+needle,1)
needle='window.Fit={'
assert needle in s
s=s.replace(needle,'''function trainingWeekday(day){
 let days=Array.isArray(state.settings.trainingWeekdays)?state.settings.trainingWeekdays.slice():[];
 if(day<0)days=[];else days=days.includes(day)?days.filter(x=>x!==day):[...days,day].sort();
 state.settings.trainingWeekdays=days;save();render();
}
window.Fit={trainingWeekday,''',1)
needle='precision:()=>FitPlanPrecisionV4,precisionV5:'
assert needle in s;s=s.replace(needle,'precision:()=>FitPlanPrecisionV7,precisionV4:()=>FitPlanPrecisionV4,precisionV5:',1)
p.write_text(s,encoding='utf8')
p=base/'index.html';s=p.read_text(encoding='utf8')
needle='<script src="precision-engine-v5.js"></script>'
assert needle in s;s=s.replace(needle,needle+'<script src="precision-engine-v7.js"></script>',1)
p.write_text(s,encoding='utf8')
print('V7.4 integrated: day plan, program, weekdays, coach dashboard, baseline comparisons')