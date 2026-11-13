#!/usr/bin/env python3
"""FitPlan V8.7 — profile changes correctly invalidate unstarted plans and calendar
forecasts. Started workouts and historical/machine calibration data are preserved.
Must run after V8.6 integration and legacy UI patches.
"""
from pathlib import Path
p=Path('fitplan/native/app/src/main/assets/app.js')
s=p.read_text('utf8')
def replace(old,new):
 global s
 assert old in s, 'V8.7 missing source anchor '+old[:100]
 s=s.replace(old,new,1)
marker="function setupNext(){"
assert marker in s
helpers=r"""
// V8.7: a persisted exercise plan belongs to the profile which created it.
function fpProfileSignature(profile=state.profile){
 const p=profile||{};
 return JSON.stringify({
  goal:p.goal||'',physique:p.physique||'',level:Number(p.level)||0,
  days:Number(p.days)||0,duration:Number(p.duration)||0,place:p.place||'',
  focus:[...(p.focus||[])].map(String).sort(),
  restrictions:[...(p.restrictions||[])].map(String).sort(),
  height:Number(p.height)||0,weight:Number(p.weight)||0,sex:p.sex||''
 });
}
function fpActiveHasProgress(active){
 if(!active)return false;
 if((active.items||[]).some(it=>(it.sets||[]).some(z=>z.done)))return true;
 for(const kind of ['pre','post','warmup','cooldown','preStretch','postStretch']){
  if((active[kind]||[]).some(z=>z.done))return true;
 }
 return !!(active.startedAt||active.startTime||active.started||active.elapsedSeconds>0);
}
function fpProfileInvalidateCache(){
 // Changing profile must never reuse an old calendar fingerprint.
 fpPlanCache=null;fpPlanCacheKey='';
}
function fpHandleProfileChange(before){
 if(before===fpProfileSignature())return;
 fpProfileInvalidateCache();
 state.planMemory=null;
 if(!state.active)return;
 if(fpActiveHasProgress(state.active)){
  state.active.profileChangedDuringWorkout=true;
  return;
 }
 state.active=null; // An unstarted plan is a disposable preview, not workout history.
}
function fpEnsureCurrentPlan(){
 const plan=state.active;
 if(!plan)return;
 const stored=plan.profileSignature;
 const legacy=state.planMemory?.profileKey;
 const actual=FitPlanPrecisionV4.profileKey(state.profile);
 const stale=(stored&&stored!==fpProfileSignature())||
  (!stored&&legacy&&legacy!==actual);
 if(!stale)return;
 if(fpActiveHasProgress(plan)){plan.profileChangedDuringWorkout=true;return;}
 state.active=null;state.planMemory=null;fpProfileInvalidateCache();save();
}
"""
s=s.replace(marker,helpers+"\n"+marker,1)
replace("function setupFinish(){if(num(state.profile.height)<100||num(state.profile.weight)<20){toast('신체 정보를 확인하세요');return;}state.onboard=true;state.active=null;refreshCycle();todayMinutes=state.profile.duration;save();go('home');toast('맞춤 운동 프로그램 준비 완료');}",
"""function setupFinish(){if(num(state.profile.height)<100||num(state.profile.weight)<20){toast('신체 정보를 확인하세요');return;}
 state.onboard=true;fpEnsureCurrentPlan();refreshCycle();todayMinutes=state.profile.duration;
 const kept=!!state.active?.profileChangedDuringWorkout;
 save();go('home');
 toast(kept?'진행 중인 운동은 유지됩니다. 다음 운동부터 새 프로필을 적용합니다.':'새 프로필에 맞춰 운동 계획을 갱신했습니다.');}""")
replace("function changeProfile(k,v){state.profile[k]=v;save();render();}",
"""function changeProfile(k,v){const before=fpProfileSignature();state.profile[k]=v;
 fpHandleProfileChange(before);save();render();}""")
replace("function numProfile(k,v){let n=num(v);if(k==='height')n=clamp(n,100,240);if(k==='weight')n=clamp(n,20,300);state.profile[k]=n;if(k==='duration')todayMinutes=n;save();render();}",
"""function numProfile(k,v){const before=fpProfileSignature();let n=num(v);
 if(k==='height')n=clamp(n,100,240);if(k==='weight')n=clamp(n,20,300);
 state.profile[k]=n;if(k==='duration')todayMinutes=n;
 fpHandleProfileChange(before);save();render();}""")
replace("function toggleProfile(k,v){const a=state.profile[k]||[];state.profile[k]=a.includes(v)?a.filter(x=>x!==v):a.concat(v);save();render();}",
"""function toggleProfile(k,v){const before=fpProfileSignature();const a=state.profile[k]||[];
 state.profile[k]=a.includes(v)?a.filter(x=>x!==v):a.concat(v);
 fpHandleProfileChange(before);save();render();}""")
replace("function homeView(){\n const p=state.profile,active=state.active,h=state.history||[];",
        "function homeView(){\n fpEnsureCurrentPlan();\n const p=state.profile,active=state.active,h=state.history||[];")
replace("function createPlan(){if(state.active){go('work');return;}",
        "function createPlan(){fpEnsureCurrentPlan();if(state.active){go('work');return;}")
replace("state.active=plan;replanRemaining=30;save();go('work');toast('운동 계획이 준비됐어요');}",
        "plan.profileSignature=fpProfileSignature();state.active=plan;replanRemaining=30;save();go('work');toast('운동 계획이 준비됐어요');}")
# Schedule preview must use the same plan engine and a fingerprint that changes
# with all prescription-relevant profile parameters.
replace("days:state.profile.days,weekdays:fpDays(),overrides,splitNames,planMemory:state.planMemory?.split||''",
        "days:state.profile.days,profile:fpProfileSignature(),weekdays:fpDays(),overrides,splitNames,planMemory:state.planMemory?.split||''")
# Separate matches for calendar program forecast and calendar daily details.
assert s.count('FitPlanPrecisionV75.planProgram({')>=1
s=s.replace('FitPlanPrecisionV75.planProgram({','FitPlanPrecisionV86.planProgram({',1)
assert s.count('FitPlanPrecisionV75.planDay({')>=1
s=s.replace('FitPlanPrecisionV75.planDay({','FitPlanPrecisionV86.planDay({',1)
# Existing settings' narration no longer mentions excluded fatigue/recovery inputs.
s=s.replace('목표·수준·회복·시간을 반영합니다.', '목표·수준·실제 수행 기록·시간을 반영합니다.')
s=s.replace('1~4분할의 운동량·빈도·시간·중복 피로를 동시에 비교했습니다.',
            '1~4분할의 운동량·빈도·시간·운동 패턴을 비교했습니다.')
p.write_text(s,'utf8')
print('V8.7 profile-specific active plan and schedule preview synchronization installed')
