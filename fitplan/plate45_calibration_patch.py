from pathlib import Path
v5=Path('fitplan/native/app/src/main/assets/precision-engine-v5.js')
s=v5.read_text(encoding='utf8')
old="""   const stat=standardOneRM(profile,e);
   // Around 50%"""
new="""   const stat=standardOneRM(profile,e);
   // Plate-loaded 45-degree sled: report *added plates, both sides combined*.
   // Empty-sled resistance is machine-specific and MUST NOT be assumed zero.
   if(e.id==='leg_press'){
     return {required:true,weight:20,minimum:10,step:10,targetReps:8,
       source:'plate45',benchmark1RM:null,benchmarkUrl:null,
       note:'45도 원판형: 20kg은 양쪽 원판 합계(좌우 10kg씩)이며 썰매 자체 저항은 포함되지 않습니다. 원판 없는 썰매를 통증 없이 3~5회 움직여 확인한 후 시작하세요. 경험이 있다면 원판 합계 중량을 직접 수정하고, 통증이 있으면 중단하세요.'};
   }
   // Around 50%"""
assert old in s,'v5 start marker'
s=s.replace(old,new,1)
old="""     status:'active',phase:'instructions',startedAt:Date.now(),targetReps:first.targetReps,"""
new="""     status:'active',phase:first.source==='plate45'?'sledcheck':'instructions',startedAt:Date.now(),targetReps:first.targetReps,"""
assert old in s,'phase marker'
s=s.replace(old,new,1)
old="""     next.lowEasy=Math.max(prevEasy,w);
     next.weight=candidate;"""
new="""     if(cal.first?.source==='plate45' && rir>=7 && goodReps && (!prevHard||prevHard>w)){
       candidate=Math.max(candidate,Math.min(w+20,Math.max(w+step,quantize(w*1.4))));
     }
     next.lowEasy=Math.max(prevEasy,w);
     next.weight=candidate;"""
assert old in s,'next trial marker'
s=s.replace(old,new,1)
v5.write_text(s,encoding='utf8')
p=Path('fitplan/native/app/src/main/assets/app.js')
s=p.read_text(encoding='utf8')
old="""function loadUnit(e){return e.gear==='dumbbell'?1:"""
assert old in s,'load unit marker'
s=s.replace(old,"""function loadUnit(e){if(e?.id==='leg_press')return 10;return e.gear==='dumbbell'?1:""",1)
old=""" const old=state.calibrationActive;
 if(!old||old.exerciseId"""
new=""" // Preserve the old generic-machine record rather than relabel old kg values.
 if(e.id==='leg_press'&&it.machineId==='default'){
   let plate=rec.variants.find(x=>x.id==='plate45_v1');
   if(!plate){
     plate={id:'plate45_v1',name:'45도 원판형 · 원판 합계',increment:10,minimum:10,
       resistanceMode:'plates_added',seat:'',notes:'썰매 저항 별도; 양쪽 원판 합계 기록'};
     rec.variants.push(plate);
   }
   rec.active=plate.id;it.machineId=plate.id;
   for(const set of it.sets)if(!set.done)set.machineId=plate.id;
 }
 const configured=rec.variants.find(x=>x.id===it.machineId)||v;
 const old=state.calibrationActive;
 if(!old||old.exerciseId"""
assert old in s,'begin marker'
s=s.replace(old,new,1)
old="""FitPlanPrecisionV5.begin(state.profile,e,v.id,v.increment,v.minimum),index};"""
assert old in s,'v5 begin marker'
s=s.replace(old,"""FitPlanPrecisionV5.begin(state.profile,e,configured.id,configured.increment,configured.minimum),index};""",1)
old=""" if(c.phase==='instructions'&&c.status==='active'){"""
new=""" if(c.phase==='sledcheck'&&c.status==='active'){
 body='<div class="card"><h2>45도 원판형 · 빈 썰매 안전 확인</h2><p>원판 없이 안전 스토퍼를 확인하고, 통증 없이 3~5회 천천히 움직여 보세요.</p><div class="callout">썰매 자체 저항은 기구마다 다릅니다. 이후 표시되는 20kg은 좌우 원판 합계로, 전체 저항이 아닙니다.</div><button class="btn primary full mt12" onclick="Fit.plateSledChecked()">통증 없이 확인 · 다음</button><button class="btn secondary full mt8" onclick="Fit.calibrationAbort()">중단</button></div>';
 }else if(c.phase==='instructions'&&c.status==='active'){"""
assert old in s,'instructions marker'
s=s.replace(old,new,1)
old=""" <label class="player-setup-field">실제 사용할 중량(kg)<input id="cal-weight" """
new=""" <label class="player-setup-field">실제 사용할 중량(kg) · 45도 원판형은 양쪽 추가 원판 합계<input id="cal-weight" """
assert old in s,'weight label marker'
s=s.replace(old,new,1)
old=""" <p class="tiny muted">기구에 없는 중량은 더 가벼운 단계로 설정하세요.</p>"""
new=""" <p class="tiny muted">45도 원판형은 썰매 자체 무게를 제외한 양쪽 원판 합계를 기록하세요(예: 좌우 20kg씩이면 40kg). 원판 없는 상태의 저항도 별도로 존재합니다. 익숙한 원판 중량으로 시험 후보를 수정할 수 있습니다.</p>"""
assert old in s,'input note marker'
s=s.replace(old,new,1)
old="""function calibrationResume(){"""
new="""function plateSledChecked(){
 const c=state.calibrationActive;
 if(!c||c.exerciseId!=='leg_press'||c.phase!=='sledcheck')return;
 c.phase='instructions';c.sledCheckedAt=Date.now();save();render();
}
function calibrationResume(){"""
assert old in s,'resume marker'
s=s.replace(old,new,1)
old=""" c.weight=w;c.phase='perform';"""
new=""" if(c.first?.source==='plate45'&&(w<10||Math.abs(w/10-Math.round(w/10))>.00001)){
   showPlayerWarning('기본 원판형은 양쪽 원판 합계 10kg 단위로 입력하세요. 예: 좌우 5kg씩이면 합계 10kg.');return;
 }
 c.weight=w;c.phase='perform';"""
assert old in s,'calibration start marker'
s=s.replace(old,new,1)
old="""window.Fit={githubRepo:"""
assert old in s,'Fit exports'
s=s.replace(old,"""window.Fit={plateSledChecked,githubRepo:""",1)
p.write_text(s,encoding='utf8')
print('Plate45 calibration prepared: sled check, per-side plate tracking, independent history')
