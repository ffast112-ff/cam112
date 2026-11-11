#!/usr/bin/env python3
from pathlib import Path
import re
root=Path('fitplan/native/app/src/main/assets')
def read(n):return (root/n).read_text('utf8')
def write(n,s):(root/n).write_text(s,'utf8')
def replace(s,a,b):
 assert a in s,'Missing anchor '+a[:75]
 return s.replace(a,b,1)
def reg(s,a,b):
 out,n=re.subn(a,b,s,flags=re.S)
 assert n,'Missing pattern '+a[:75]
 return out
# V3: eliminate subjective readiness and fatigue learning.
s=read('precision-engine-v3.js')
s=reg(s,r'function normalizeReadiness\(r=\{\}\) \{ return \{energy:.*?formConcern:!!r\.formConcern\}; \}',
 'function normalizeReadiness(r={}) {return {pain:!!r.pain,painArea:r.painArea||null,formConcern:!!r.formConcern};}')
s=reg(s,r'function recoveryRisk\(r\) \{return .*?;\}','function safetyRisk(r){return !!r.pain;}')
s=s.replace('recoveryRisk(', 'safetyRisk(')
s=reg(s,r"\s*else if\(safetyRisk\(r\)\)\{action='recovery';.*?\}",'')
s=s.replace('if(safetyRisk(r))v*=.78;','').replace('if(z.highFatigue)x*=.8;','')
s=s.replace('if(z.stalled&&z.recoveryAdequate)x*=1.08;', 'if(z.stalled&&z.samples>=6)x*=1.04;')
s=s.replace('highFatigue:false,','').replace('recoveryAdequate:false,','')
s=s.replace("soreness:numFeedback(h.session,'soreness'),",'')
s=reg(s,r'\s*const recent=rows\.slice\(-3\),pain=recent\.some\(x=>x\.pain\),fatigue=.*?b\.recoveryAdequate=.*?;','')
s=s.replace('const risk=response[e.m]?.highFatigue?-5:0;', 'const risk=0;')
s=s.replace('if(response[e.m]?.highFatigue||analysis.setsAdjustment<0)return 2;',
            'if(analysis.setsAdjustment<0)return 2;')
s=s.replace('회복 상태와 자세를 다시 확인합니다.','반복 수행과 자세를 다시 확인합니다.')
s=s.replace('시간·회복·수행 이력','시간·수행 이력')
s=s.replace('실제 수행 기록과 회복 상태에 따라','실제 수행 기록에 따라')
s=s.replace('현재 컨디션이 좋지 않아 증량보다 회복을 우선합니다.','통증에 따른 안전 제한을 우선합니다.')
write('precision-engine-v3.js',s)
# V4: no inferred muscle fatigue and no effect in score or sets.
s=read('precision-engine-v4.js')
s=reg(s,r'const pressure=read=>.*?;','const pressure=read=>!!read.pain;')
s=reg(s,r'function recentFatigue\(history,catalog,now\)\{.*?\n\}','')
s=reg(s,r'\s*for\(const m in credit\)score\+=credit\[m\]\*Math\.max\(0,ctx\.fatigue\.fatigue\[m\]-2\.5\)\*\.65\*working\(z\);','')
s=s.replace('plateau?.stalled&&plateau?.recoveryAdequate?.4:1.1','plateau?.stalled?.5:1.1')
s=s.replace('ctx.response?.[e.m]?.stalled&&ctx.response?.[e.m]?.recoveryAdequate?1:4','ctx.response?.[e.m]?.stalled?1:4')
s=s.replace('        fatigue=ctx.fatigue.fatigue[e.m]*.16;','')
s=s.replace('return familiar+simple+deficit+variety-fatigue-N(e.level)*.28;','return familiar+simple+deficit+variety-N(e.level)*.28;')
s=s.replace('const count=working(it),fatigue=R(ctx.fatigue.fatigue[it.muscle],1),','const count=working(it),')
s=s.replace(' · 최근 피로 참고값 ',' · 기록 기반 조정 ')
s=s.replace('focus=focusSet(p),fatigue=recentFatigue(history,catalog,now),pace=','focus=focusSet(p),pace=')
s=s.replace('focus,fatigue,pace,oldExercises','focus,pace,oldExercises')
s=reg(s,r'\s*fatigue:Object\.fromEntries\(MUSCLES\.map\(m=>\[m,R\(c\.fatigue\.fatigue\[m\],1\)\]\)\),','')
s=s.replace('changePolicy:\'한 번의 피로 변화로 루틴을 바꾸지 않으며, 회복이 충분한 장기 정체 또는 목표 변화에서 재평가\'',
            'changePolicy:\'장기적인 수행 기록과 목표 변화에 따라 루틴을 재평가\'')
s=s.replace('현재 피로·통증 정보 때문에 증량보다 회복을 우선합니다.','통증에 대한 안전 제한을 우선합니다.')
s=s.replace("성과 점검·재설계':'점진적 발전·회복 조절'","성과 점검·재설계':'점진적 발전'")
s=s.replace('const response=c.response,heavy=Object.values(response).some(x=>x.highFatigue);','')
s=s.replace("guidance:heavy?'피로 누적이 확인되면 세트 수를 줄이고 회복을 확보합니다.':","guidance:")
s=s.replace('목표 반복 달성률과 회복을 확인해','목표 반복 달성률을 확인해')
write('precision-engine-v4.js',s)
# V5 recovery scoring retired; calibration and training intensity retained.
s=read('precision-engine-v5.js')
s=reg(s,r'\s*function recoveryGuide\(history,readiness\)\{.*?\n \}','')
s=s.replace('exerciseQuality,recoveryGuide,stepsFor','exerciseQuality,stepsFor')
write('precision-engine-v5.js',s)
# V7: intensity based volume, no subjective readiness or derived fatigue/recovery scores.
s=read('precision-engine-v7.js')
s=s.replace('groups={},muscles={},fatigue=blank();','groups={},muscles={};')
s=s.replace('recoveryDays:2.5,\n    recoveryConfidence:0,highFatigue:false,','')
s=reg(s,r'\s*if\(row\.t>=now-10\*DAY\)\{const age=.*?fatigue\[m\]\+=.*?;\}','')
s=reg(s,r'\s*const v=muscles\[m\],history=\[\];.*?v\.recoveryConfidence=rnd\(clamp\(\(history\.length-4\)/12,0,\.8\)\);','\n   const v=muscles[m];')
s=reg(s,r'\s*const recent=rows\.filter\(z=>z\.t>=now-14\*DAY\).*?v\.fatigue=rnd\(fatigue\[m\]\);','')
s=s.replace('const eligible=v.confidence>=.45&&v.sessions>=6&&!v.highFatigue;','const eligible=v.confidence>=.45&&v.sessions>=6;')
s=s.replace('v.changeSets=v.highFatigue&&v.fatigue>=4?-1:eligible&&','v.changeSets=eligible&&')
s=s.replace("v.reason=v.highFatigue?'누적 피로가 높아 추가 운동량을 제한합니다.':!eligible?",'v.reason=!eligible?')
s=reg(s,r'function fatiguePenalty\(items,model,profile\)\{.*?\}\nfunction adjustDay','function adjustDay')
s=s.replace('const pain=!!input.readiness?.pain,poor= input.readiness?.energy<=2||input.readiness?.sleep<=2||input.readiness?.soreness>=4;','const pain=!!input.readiness?.pain;')
s=s.replace('const recovery=poor||m.highFatigue&&m.fatigue>=4;','').replace('it.v7LoadFactor=recovery?.95:1;','it.v7LoadFactor=1;')
s=s.replace('recovery?4:2','2').replace('if(poor||pain||m.highFatigue&&m.fatigue>=4)','if(pain)')
s=s.replace('else if(gap<x.recoveryDays)gain-=1;','').replace('gain-=.1*x.fatigue;','')
s=reg(s,r'\s*fatiguePenaltyBefore:fatiguePenalty\(base.items,model,input.profile\),\s*fatiguePenaltyAfter:fatiguePenalty\(adapted.items,model,input.profile\)','completedSetDelta:newSets-baseSets')
write('precision-engine-v7.js',s)
s=read('precision-engine-v75.js').replace('개인 학습과 피로 지표는 실제 생리학적 최적화가 아닌 보수적 경험칙입니다.','중량·반복·RIR 기록을 사용하는 보수적 처방입니다.')
write('precision-engine-v75.js',s)
s=read('fitplan-advanced.js')
s=reg(s,r' function excessiveFatigue\(history\)\{.*?\n \}','')
s=s.replace('machineDecision,excessiveFatigue,pace','machineDecision,pace')
s=s.replace("x.highFatigue?'피로 관리 우선':x.stalled&&x.recoveryAdequate?","x.stalled?")
write('fitplan-advanced.js',s)
s=read('fitplan-timer-v6.js').replace('if(number(readiness.energy,3)<=2||number(readiness.soreness,2)>=4)result+=15;','').replace('changedExercise=false,readiness={}','changedExercise=false')
write('fitplan-timer-v6.js',s)
# UI: remove day readiness and post-workout soreness while keeping pain and intensity.
s=read('app.js')
s=s.replace('readiness={energy:3,soreness:2,sleep:3,pain:false}','readiness={pain:false,painArea:null}')
s=s.replace('feedback={weight:state.profile.weight,difficulty:5,pain:false,soreness:2,note:\'\'}',
            'feedback={weight:state.profile.weight,difficulty:5,pain:false,note:\'\'}')
s=s.replace('feedback={weight:currentWeight(),difficulty:5,pain:false,soreness:2,note:\'\'}',
            'feedback={weight:currentWeight(),difficulty:5,pain:false,note:\'\'}')
a='<div class="card"><div class="field"><label>오늘 에너지 상태</label>'
b='<div class="tile"><div class="txt"><strong>운동에 영향을 주는 통증'
assert a in s and b in s
i=s.index(a);j=s.index(b,i);s=s[:i]+'<div class="card">'+s[j:]
s=s.replace("readiness[k]=k==='pain'?!!v:k==='painArea'?String(v):num(v,3);","if(k!=='pain'&&k!=='painArea')return;readiness[k]=k==='pain'?!!v:String(v);")
s=s.replace('if(readiness.energy<=2||readiness.soreness>=4)base+=20;','')
s=s.replace("['weight','difficulty','soreness'].includes(k)?num(v)","['weight','difficulty'].includes(k)?num(v)")
s=s.replace("k==='difficulty'||k==='soreness'||k==='pain'","k==='difficulty'||k==='pain'")
a='<div class="field"><label>운동 후 근육 피로도</label>'
b='<div class="tile"><div class="txt"><strong>운동 중 통증이 있었나요?'
assert a in s and b in s
i=s.index(a);j=s.index(b,i);s=s[:i]+s[j:]
s=s.replace('const rec=FitPlanPrecisionV5.recoveryGuide(state.history,s.readiness||readiness);','')
# Do not reference removed rec inside V5 card.
s=re.sub(r"\$\{esc\(rec\.reason\)\} · ",'',s)
s=s.replace(',fatigue=FitPlanAdvanced.excessiveFatigue(state.history)','')
s=re.sub(r'<p class="sub mt8">회복 평가: \$\{esc\(fatigue\.reason\)\}</p>','',s)
s=s.replace('운동 효율·회복 분석','운동 수행 분석')
s=s.replace('몸의 피로가 충분히 줄었는지 확인하고 진행하세요.','운동 간 휴식시간을 확인하세요.')
s=s.replace("const cause=pain>0||hard>=Math.max(2,Math.ceil(workouts.length*.4))?'recovery':","const cause=pain>0?'safety':")
s=s.replace("recovery:'최근 통증이나 높은 피로 기록이 있어 다음 주기는 회복을 우선합니다.'",
            "safety:'최근 통증 기록이 있어 안전 조건을 확인합니다.'")
write('app.js',s)
# Hard guard: no branches based on fatigue inputs, no rendered soreness/sleep questions.
for n in ['precision-engine-v3.js','precision-engine-v4.js','precision-engine-v5.js','precision-engine-v7.js','precision-engine-v75.js','fitplan-advanced.js','fitplan-timer-v6.js']:
 bad=re.findall(r'\.(?:energy|sleep|soreness)|highFatigue|fatiguePenalty|recoveryGuide|excessiveFatigue',read(n))
 assert not bad,(n,bad)
assert '오늘 에너지 상태' not in read('app.js')
assert '운동 후 근육 피로도' not in read('app.js')
print('Fatigue, sleep and soreness inputs and algorithm effects removed; strength intensity and pain remain')
