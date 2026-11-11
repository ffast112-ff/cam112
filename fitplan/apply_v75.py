#!/usr/bin/env python3
"""Apply FitPlan V7.5 on top of the tested V7.4 native build. No secrets."""
from pathlib import Path
import re
from PIL import Image, ImageDraw

base=Path("fitplan/native/app/src/main/assets")
app=base/"app.js"
s=app.read_text(encoding="utf-8")
def change(old,new,required=True):
    global s
    if old not in s:
        if required: raise RuntimeError("V7.5 anchor missing: "+old[:100])
        return
    s=s.replace(old,new,1)

s,n=re.subn(r"const APP_VERSION='[^']+';","const APP_VERSION='1.9.11';",s,count=1)
if n==0:
    assert 'const APP_VERSION=(()=>{' in s, 'Native version marker missing'
change("FitPlanPrecisionV7?.planDay(plannerInput)","FitPlanPrecisionV75?.planDay(plannerInput)")
change("FitPlanPrecisionV7?.planProgram(programInput)","FitPlanPrecisionV75?.planProgram(programInput)")
change("const model=FitPlanPrecisionV7.learn(","const model=FitPlanPrecisionV75.learn(")
change("const audit=FitPlanPrecisionV7.audit(","const audit=FitPlanPrecisionV75.audit(")
change("precision:()=>FitPlanPrecisionV7,","precision:()=>FitPlanPrecisionV75,")
change("V7.4 적응형 코치 · V4 기본 엔진","V7.5 적응형 코치 · V4 보호 엔진")
change("V7.4 · 개인 적응형 분석","V7.5 · 개인 적응형 분석")
change("v7:result.v7,optimizer:","v7:result.v7,v75:result.v75,optimizer:")

# Only use equipment-specific history. Do not replace the existing calibration safety gate.
old="const knownLoad=load?.weight!==null&&load?.weight!==undefined?load.weight:(calibrated?.status==='ready'?calibrated.weight:null);"
new=old+"""
     const learned=knownLoad!==null&&knownLoad!==undefined?FitPlanPrecisionV75.nextWorkout({history:state.history},it.id,machine?.machineId||'default',unit):null;
     const correctedLoad=learned?.weight!=null&&learned.confidence>=.4?learned.weight:knownLoad;"""
change(old,new)
old="const adjusted=load?(knownLoad===null?0:Math.max(unit,roundTo(knownLoad*(z.role==='warmup'?.5:z.role==='backoff'?.9:1)*(it.v7LoadFactor||1),unit))):initial;"
new="const adjusted=load?(correctedLoad===null?0:Math.max(unit,roundTo(correctedLoad*(z.role==='warmup'?.5:z.role==='backoff'?.9:1)*(it.v7LoadFactor||1),unit))):initial;"
change(old,new)

# Safe, bounded same-session adjustments. Never increase if pain or form is poor.
start=s.index("function adjustFollowing(it,idx){")
end=s.index("function checkSet(index,j)",start)
s=s[:start]+"""function adjustFollowing(it,idx){
 const completed=it.sets[idx],e=exercise(it.currentId);
 if(!completed||!e||completed.warmup||!completed.done)return;
 const next=it.sets.slice(idx+1).find(z=>!z.done&&!z.warmup);
 const rec=FitPlanAdvanced.machineRecord(state,e),v=rec.variants.find(x=>x.id===it.machineId)||rec.variants[0];
 const step=v?.increment||2.5;
 const proposal=FitPlanPrecisionV75.nextSet({weight:completed.actualWeight,reps:completed.actualReps,
  targetReps:completed.targetReps,rir:completed.rir,pain:completed.pain,form:completed.form,increment:step});
 if(completed.requiresCalibration&&num(completed.actualWeight)>0){
  completed.targetWeight=completed.actualWeight;completed.requiresCalibration=false;
  it.sets.filter(z=>!z.done&&z.requiresCalibration).forEach(z=>{z.targetWeight=proposal.weight;z.actualWeight=proposal.weight;z.requiresCalibration=false;});
  it.reason='최초 시험 수행 반영: '+proposal.reason;
  return;
 }
 if(proposal.hold){it.reason=proposal.reason;it.halted=!!completed.pain;return;}
 if(!next)return;
 if(proposal.weight!==next.targetWeight){next.targetWeight=proposal.weight;next.actualWeight=proposal.weight;}
 it.reason=proposal.reason;
}
""" + s[end:]

# Reduce typing: one tap to rate the last completed work set. Existing number inputs remain.
change("function editSet(index,j,k,value)", """function quickLastRir(index,value){
 const it=state.active?.items?.[index];if(!it)return;
 const last=[...it.sets].reverse().find(z=>z.done&&!z.warmup);
 if(!last){toast('먼저 세트를 완료해 주세요');return;}
 last.rir=clamp(num(value),0,6);save();render();toast('RIR '+last.rir+' 기록');
}
function skipMovement(index){
 const it=state.active?.items?.[index];if(!it)return;
 it.skipped=true;it.sets=it.sets.filter(z=>z.done);save();render();
 toast('해당 운동의 남은 세트를 제외했습니다. 다른 운동으로 교체할 수 있습니다.');
}
function editSet(index,j,k,value)""")
change("window.Fit={trainingWeekday,","window.Fit={quickLastRir,skipMovement,trainingWeekday,")

# Add compact buttons, keep detailed set-by-set table and substitution action.
btn='<button class="btn tiny secondary mt8" onclick="Fit.skipMovement(\x24{index})">남은 세트 건너뛰기</button>'
old='<div class="tiny muted mt8">휴식 \x24{it.rest}초 · 목표 RIR'
change(old,btn+old)
# Compact RIR one-tap alternatives for the most recently completed work set.
old="</td></tr>"+chr(96)+";}).join('')}</tbody></table>"
buttons='<div class="row mt8">' + '\x24{[0,1,2,3,4].map(x=>'+chr(96)+'<button class="btn tiny secondary" onclick="Fit.quickLastRir(\x24{index},\x24{x})">RIR \x24{x}</button>'+chr(96)+").join('')}</div>"
change(old,old+buttons)

# Display plateau warning without additional questions or charts.
old='\x24{s.v7?'+chr(96)+'<div class="subhead"><strong>개인별 학습</strong>'
new='\x24{s.v75?.alerts?.length?'+chr(96)+'<div class="callout">\x24{s.v75.alerts.map(a=>esc(a.message)).join(" · ")}</div>'+chr(96)+":''}"+old
change(old,new)
# More meaningful observed score alongside legacy audit.
change("기록 \x24{audit.records}회 · 수행률", "기록 \x24{audit.records}회 · 목표 달성률 \x24{audit.v75?.targetAchievement==null?'자료 부족':Math.round(audit.v75.targetAchievement*100)+'%'} · 수행률")

app.write_text(s,encoding="utf-8")
html=base/"index.html"
h=html.read_text(encoding="utf-8")
assert '<script src="precision-engine-v7.js"></script>' in h
h=h.replace('<script src="precision-engine-v7.js"></script>',
 '<script src="precision-engine-v7.js"></script><script src="precision-engine-v75.js"></script>',1)
html.write_text(h,encoding="utf-8")
(base/"precision-engine-v75.js").write_bytes(Path("fitplan/precision-engine-v75.js").read_bytes())

# Fix false-positive exercise coverage comparator in V7.4 proxy score.
engine=base/"precision-engine-v7.js"
v=engine.read_text(encoding="utf-8")
old="const overlap=(new Set(base.items.map(it=>it.id))).size;"
assert old in v
v=v.replace(old,"const overlap=base.items.length===adapted.items.length&&base.items.every(it=>adapted.items.some(x=>x.id===it.id));",1)
assert "completedExerciseCoverage:overlap===adapted.items.length," in v
v=v.replace("completedExerciseCoverage:overlap===adapted.items.length,","completedExerciseCoverage:overlap,",1)
engine.write_text(v,encoding="utf-8")

# Android launcher icon: weight + rising progress bars, matching FitPlan branding.
size=512
im=Image.new("RGB",(size,size),(11,18,22));d=ImageDraw.Draw(im)
d.rounded_rectangle((13,13,499,499),radius=100,fill=(15,24,28),outline=(48,69,72),width=4)
green=(55,220,112)
for i,hgt in enumerate((30,62,96,142)):
 x=135+79*i
 d.rounded_rectangle((x,402-hgt,x+48,405),radius=8,fill=green)
d.line([(90,364),(164,315),(245,282),(325,236),(398,179)],fill=green,width=17,joint="curve")
d.polygon([(397,176),(356,182),(398,136),(429,202)],fill=green)
d.line([(118,178),(383,145)],fill="white",width=24)
for x,y0,y1,w in ((78,166,224,24),(136,135,263,42),(358,105,235,42),(425,145,213,26)):
 d.rounded_rectangle((x-w//2,y0,x+w//2,y1),radius=12,fill="white")
res=Path("fitplan/native/app/src/main/res/drawable")
res.mkdir(parents=True,exist_ok=True)
im.save(res/"fitplan_icon.png")
manifest=Path("fitplan/native/app/src/main/AndroidManifest.xml")
m=manifest.read_text(encoding="utf-8")
assert '<application android:label="FitPlan"' in m
m=m.replace('<application android:label="FitPlan"', '<application android:label="FitPlan" android:icon="@drawable/fitplan_icon"',1)
manifest.write_text(m,encoding="utf-8")
print("FitPlan V7.5 app, model, and Android icon patched")
