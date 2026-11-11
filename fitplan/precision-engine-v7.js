/* FitPlan Precision V7.4 - deterministic, offline adaptive coach.
 * Training models are engineering heuristics, NOT validated biological predictions.
 * V4 is the safe baseline. V7 changes are bounded, explainable, and reversible.
 */
(function(root,factory){
 const V4=root.FitPlanPrecisionV4||(typeof require==='function'?require('./precision-engine-v4.js'):null);
 const V3=root.FitPlanPrecisionV3||(typeof require==='function'?require('./precision-engine-v3.js'):null);
 const api=factory(V4,V3);
 if(typeof module==='object'&&module.exports)module.exports=api;
 else root.FitPlanPrecisionV7=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(V4,V3){
'use strict';
const VERSION='7.4.0',DAY=86400000,WEEK=7*DAY;
const MUSCLES=['가슴','등','어깨','하체','뒤허벅지','둔근','이두','삼두','복부','종아리'];
const CREDITS={squat:{하체:1,둔근:.4},hinge:{뒤허벅지:1,둔근:.4},glutes:{둔근:1},push:{가슴:1,삼두:.35,어깨:.15},chestiso:{가슴:1},pullvertical:{등:1,이두:.35},pullhorizontal:{등:1,이두:.35},verticalpush:{어깨:1,삼두:.35},shoulderiso:{어깨:1},triceps:{삼두:1},biceps:{이두:1},calves:{종아리:1},core:{복부:1}};
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const num=(v,d=0)=>v==null||v===''?d:(Number.isFinite(+v)?+v:d);
const rnd=(v,n=2)=>Math.round(v*10**n)/10**n;
const average=a=>a.length?a.reduce((v,x)=>v+x,0)/a.length:0;
const median=a=>{if(!a.length)return 0;const v=a.slice().sort((x,y)=>x-y),k=v.length>>1;return v.length%2?v[k]:(v[k-1]+v[k])/2;};
const blank=()=>Object.fromEntries(MUSCLES.map(m=>[m,0]));
const at=(h,now)=>{const v=h?.finishedAt||h?.timestamp||h?.endTime||h?.date;const t=typeof v==='number'?v:Date.parse(v);return Number.isFinite(t)&&t>0&&t<=now? t:null;};
const valid=(s)=>s&&s.done&&!s.warmup&&s.role!=='warmup'&&!s.pain&&s.form!=='poor';
const countWork=it=>(it.sets||[]).filter(s=>!s.warmup&&s.role!=='warmup').length;
const selection=(history,catalog,now)=>{
 const idx=new Map((catalog||[]).map(e=>[e.id,e]));
 return (history||[]).map((h,i)=>({h,t:at(h,now),i})).filter(z=>z.t!==null&&now-z.t<=112*DAY).sort((a,b)=>a.t-b.t||a.i-b.i).map(z=>{
  const records=[];
  for(const it of z.h.items||[])for(const s of it.sets||[]){
   if(!valid(s))continue;
   const id=s.actualId||it.currentId||it.eid||it.id,e=idx.get(id);
   if(!e)continue;
   const reps=num(s.actualReps,-1),weight=num(s.actualWeight,0),rir=num(s.rir,NaN);
   const isHold=e.id==='plank'||e.pattern==='core',isLoad= !['body','band'].includes(e.gear)&&!['cardio','core'].includes(e.pattern);
   if(reps<=0||reps>3600||(isLoad&&weight<=0))continue;
   // e1RM is meaningful only for 3-12 reps, same exercise and equipment.
   const metric=isLoad?(reps>=3&&reps<=12&&Number.isFinite(rir)&&rir>=0&&rir<=5?weight*(1+Math.min(18,reps+rir)/30):null):reps;
   records.push({id,pattern:e.pattern,m:e.m,machine:s.machineId||it.machineId||'default',metric,
     weight,reps,rir:Number.isFinite(rir)?rir:null,target:num(s.targetReps,-1),form:s.form||'unknown',pain:!!s.pain,
     effort:num(it.effort,0)});
  }
  return {...z,records};
 });
};
function learn(input={}){
 const now=num(input.now,Date.now()),rows=selection(input.history,input.catalog,now),groups={},muscles={},fatigue=blank();
 for(const m of MUSCLES)muscles[m]={muscle:m,sessions:0,sets:0,confidence:0,trend:0,stalled:false,recoveryDays:2.5,
   recoveryConfidence:0,highFatigue:false,completion:0,meanRir:null,weeklySets:0,changeSets:0,reason:'기록이 부족하여 기본 훈련량을 유지합니다.'};
 for(const row of rows){
  const seen=new Set();
  for(const r of row.records){
   const id=r.id+'|'+r.machine;if(!groups[id])groups[id]=[];
   groups[id].push({time:row.t,...r});
   const cred=CREDITS[r.pattern]||{};
   for(const m in cred){const v=muscles[m];v.sets+=cred[m];if(row.t>=now-WEEK)v.weeklySets+=cred[m];seen.add(m);
    const quality=r.target>0&&r.reps>=r.target&&r.form!=='poor';v.completion+=quality?cred[m]:0;
    if(row.t>=now-10*DAY){const age=(now-row.t)/DAY,base=cred[m]*(1+(r.rir!==null&&r.rir<=1?.16:0));fatigue[m]+=base*Math.pow(.5,age/2.3);}
   }
  }
  for(const m of seen)muscles[m].sessions++;
 }
 const exerciseModels={};
 for(const [key,list] of Object.entries(groups)){
  const byDay=new Map();
  for(const z of list){if(!Number.isFinite(z.metric)||z.metric<=0)continue;
   const k=new Date(z.time).toISOString().slice(0,10);const prior=byDay.get(k);
   if(!prior||z.metric>prior.metric)byDay.set(k,z);
  }
  const daily=[...byDay.values()].sort((a,b)=>a.time-b.time).slice(-16),n=daily.length;
  const span=n>1?(daily[n-1].time-daily[0].time)/DAY:0;
  const k=Math.min(4,Math.floor(n/2)),first=k?median(daily.slice(0,k).map(a=>a.metric)):0,last=k?median(daily.slice(-k).map(a=>a.metric)):0;
  const raw=first>0?(last/first-1):0;
  const weekly=span>=14?clamp(Math.pow(Math.max(.5,1+raw),7/span)-1,-.05,.05):0;
  const confidence=clamp((n-2)/7,0,1)*clamp(span/28,0,1);
  const rir=list.map(a=>a.rir).filter(x=>x!==null),recent=list.slice(-12);
  exerciseModels[key]={id:daily[0]?.id||list[0]?.id,machine:list[0].machine,samples:list.length,days:n,spanDays:rnd(span),
   confidence:rnd(confidence),weeklyTrend:rnd(weekly,4),recentMetric:rnd(last),
   completion:rnd(average(recent.map(a=>a.target>0&&a.reps>=a.target?1:0))),
   lastRir:rir.length?rir[rir.length-1]:null,
   stalled:confidence>=.5&&weekly<=.002&&recent.length>=6};
 }
 // Recovery timing is inferred only from repeated, comparable same-equipment sessions.
 for(const m of MUSCLES){
  const v=muscles[m],history=[];
  for(const [key,list] of Object.entries(groups)){
   const e=exerciseModels[key];if(e.confidence<.2)continue;
   const points=list.filter(x=>Number.isFinite(x.metric)&&x.metric>0).sort((a,b)=>a.time-b.time);
   for(let i=1;i<points.length;i++){const gap=(points[i].time-points[i-1].time)/DAY;
    if(gap<.5||gap>8)continue;
    const change=points[i].metric/points[i-1].metric-1;
    if(Number.isFinite(change)&&Math.abs(change)<.25)history.push({gap,stable:change>=-.04});
   }
  }
  const stable=history.filter(h=>h.stable).map(h=>h.gap);
  v.recoveryDays=history.length>=5&&stable.length>=3?rnd(clamp(median(stable),1.5,4),1):2.5;
  v.recoveryConfidence=rnd(clamp((history.length-4)/12,0,.8));
  const own=Object.values(exerciseModels).filter(e=>{
   const cat=(input.catalog||[]).find(z=>z.id===e.id);return cat?.m===m;
  });
  v.trend=rnd(average(own.filter(e=>e.confidence>=.3).map(e=>e.weeklyTrend)),4);
  v.confidence=rnd(clamp((v.sessions-2)/10,0,1)*clamp(own.reduce((n,e)=>n+e.confidence,0)/Math.max(1,own.length),0,1));
  v.stalled=own.some(x=>x.stalled)&&v.sessions>=6;
  v.completion=v.sets?rnd(v.completion/v.sets,2):0;
  const recent=rows.filter(z=>z.t>=now-14*DAY).filter(z=>z.records.some(r=>r.m===m||Object.keys(CREDITS[r.pattern]||{}).includes(m)));
  const fatigueFlags=recent.filter(z=>num(z.h.feedback?.difficulty,5)>=8||num(z.h.feedback?.soreness,2)>=4||!!z.h.feedback?.pain).length;
  v.highFatigue=fatigueFlags>=2&&recent.length>=3||fatigue[m]>=6;
  v.fatigue=rnd(fatigue[m]);
  const eligible=v.confidence>=.45&&v.sessions>=6&&!v.highFatigue;
  // One working set up or down PER MUSCLE per 7-day horizon, no automatic runaway volume.
  v.changeSets=v.highFatigue&&v.fatigue>=4?-1:eligible&&v.stalled&&v.completion>=.82?1:eligible&&v.completion<.65?-1:0;
  v.reason=v.highFatigue?'누적 피로가 높아 추가 운동량을 제한합니다.':!eligible?'비교할 만한 기록이 충분하지 않아 기본 훈련량을 유지합니다.':
   v.changeSets>0?'회복 상태가 양호하고 동일 중량에서 장기 정체가 확인되어 주간 1세트 증가를 시험합니다.':
   v.changeSets<0?'최근 목표 달성률이 낮아 주간 세트량 감소를 시험합니다.':'현재 운동량을 유지하며 다음 기록을 평가합니다.';
 }
 const samples=rows.filter(z=>z.records.length).length;
 return {version:VERSION,samples,confidence:rnd(clamp((samples-3)/12,0,1)),muscles,exercises:exerciseModels,
   dataWindowDays:112,source:'completed-working-sets',unvalidated:true};
}
function fatiguePenalty(items,model,profile){let p=0;for(const it of items||[]){const m=model.muscles[it.muscle];if(!m)continue;const c=countWork(it);const excess=Math.max(0,m.fatigue-2);p+=c*excess*(m.highFatigue?.9:.35);if(profile?.focus?.includes(it.muscle))p*=.98;}return rnd(p);}
function adjustDay(base,input,model){
 const adjusted={...base,items:base.items.map(it=>({...it,sets:(it.sets||[]).map(s=>({...s}))}))};
 let changes=[],used=new Set(),minEstimate=0;
 const pain=!!input.readiness?.pain,poor= input.readiness?.energy<=2||input.readiness?.sleep<=2||input.readiness?.soreness>=4;
 for(const it of adjusted.items){
  const m=model.muscles[it.muscle],working=it.sets.filter(s=>!s.warmup),n=working.length;
  if(!m||n<2)continue;
  let delta=0;
  if(poor||pain||m.highFatigue&&m.fatigue>=4){delta=n>=3?-1:0;}
  else if(m.confidence>=.45&&m.changeSets!==0&&!used.has(it.muscle)){
   delta=m.changeSets>0&&n<5&&adjusted.estimatedMinutes+3<=input.minutes?1:m.changeSets<0&&n>=3?-1:0;
  }
  if(delta===-1){const last=it.sets.findLastIndex(s=>!s.warmup);if(last>=0){it.sets.splice(last,1);used.add(it.muscle);changes.push({exercise:it.id,muscle:it.muscle,sets:-1,reason:m.reason});minEstimate-=3;}}
  else if(delta===1){const w=working[working.length-1];if(w){it.sets.push({...w,role:'working'});used.add(it.muscle);changes.push({exercise:it.id,muscle:it.muscle,sets:1,reason:m.reason});minEstimate+=3;}}
 }
 adjusted.estimatedSeconds=Math.max(0,base.estimatedSeconds+minEstimate*60);
 adjusted.estimatedMinutes=Math.ceil(adjusted.estimatedSeconds/60);
 adjusted.unusedMinutes=rnd(Math.max(0,num(input.minutes,base.minutes)-adjusted.estimatedSeconds/60),1);
 adjusted.v7Changes=changes;
 return adjusted;
}
function availableSlots(now,days,availableWeekdays,horizon=14){
 const out=[];for(let n=0;n<horizon;n++){
  const date=new Date(now+n*DAY),day=date.getDay();
  if(availableWeekdays.length?availableWeekdays.includes(day):true)out.push({day,offset:n,date:date.toISOString().slice(0,10),time:now+n*DAY});
 }
 if(availableWeekdays.length)return out;
 // If the user did not specify weekdays, spread sessions across each 7-day week.
 const indices=[];for(let w=0;w<Math.ceil(horizon/7);w++)for(let j=0;j<days;j++)indices.push(w*7+Math.floor(j*7/days));
 return out.filter(x=>indices.includes(x.offset));
}
function rollingHorizon(input,model,base){
 const p=V3.normalizeProfile(input.profile),now=num(input.context?.now,Date.now());
 const chosen=Array.isArray(input.availableWeekdays)?input.availableWeekdays:[];
 const allowed=[...new Set(chosen.map(Number).filter(v=>Number.isInteger(v)&&v>=0&&v<=6))];
 const slots=availableSlots(now,p.days,allowed,14).slice(0,Math.min(12,2*p.days));
 const split=V3.SPLITS.find(x=>x.id===base.split),patterns=split?.days||[];
 const options=[];
 for(let i=0;i<slots.length;i++){
  const slot=slots[i],alternatives=[];
  // Keep the selected split stable while evaluating its upcoming day templates.
  for(let j=0;j<Math.min(3,patterns.length);j++){
   const index=num(input.sessionIndex,0)+i+j;
   const day=patterns[index%patterns.length];
   const muscles=new Set();for(const pat of day.patterns)for(const m in CREDITS[pat]||{})if(CREDITS[pat][m]>=.35)muscles.add(m);
   const quality=[...muscles].reduce((sum,m)=>{const x=model.muscles[m];return sum+1.5*(num(base.weeklyTarget?.[m],0)>num(base.weeklyDone?.[m],0)?1:0)-.18*x.fatigue;},0);
   alternatives.push({dayIndex:index%patterns.length,sequenceIndex:index,name:day.name,muscles:[...muscles],quality});
  }
  options.push({slot,alternatives});
 }
 // Bounded beam search over 14 days, scoring balance, recovery, repetition and adherence.
 let beam=[{score:0,choices:[],last:{},counts:blank(),streak:0}];
 for(const entry of options){const next=[];
  for(const b of beam)for(const c of entry.alternatives){
   let gain=c.quality;
   for(const m of c.muscles){const gap=entry.slot.offset-(b.last[m]??-10);
    if(gap<1)gain-=4.5;else if(gap<2)gain-=2.5;else if(gap<model.muscles[m].recoveryDays)gain-=1.3;
    gain+=1.2/(1+b.counts[m]);
   }
   // Rotation is preferred: small reward for the natural planned next day.
   if(c.sequenceIndex===num(input.sessionIndex,0)+b.choices.length)gain+=2;
   const last={...b.last},counts={...b.counts};for(const m of c.muscles){last[m]=entry.slot.offset;counts[m]++;}
   next.push({score:b.score+gain,choices:[...b.choices,{date:entry.slot.date,weekday:entry.slot.day,
     dayName:c.name,muscles:c.muscles,sessionIndex:c.sequenceIndex,score:rnd(gain)}],last,counts});
  }
  beam=next.sort((a,b)=>b.score-a.score||JSON.stringify(a.choices).localeCompare(JSON.stringify(b.choices))).slice(0,8);
 }
 const winner=beam[0]||{score:0,choices:[]};
 return {weeks:2,score:rnd(winner.score),slots:winner.choices,availableWeekdays:allowed,assumedSchedule:!allowed.length,
   explanation:allowed.length?'설정한 운동 가능 요일에서 다음 2주 분할·회복 간격을 비교했습니다.':'운동 가능 요일을 지정하지 않아 주간 운동 횟수를 가능한 한 균등하게 배치했습니다.',
   candidateBeamWidth:8,optimization:'bounded-beam-search',noGuarantee:true};
}
function compare(base,adapted,model,input){
 const baseSets=base.items.reduce((n,it)=>n+countWork(it),0),newSets=adapted.items.reduce((n,it)=>n+countWork(it),0);
 const overlap=(new Set(base.items.map(it=>it.id))).size;
 const confidence=model.confidence;
 return {baseline:'precision-v4',candidate:VERSION,recordCount:model.samples,confidence,baseSets,newSets,
   deltaSets:newSets-baseSets,baseMinutes:base.estimatedMinutes,newMinutes:adapted.estimatedMinutes,
   bounded:Math.abs(newSets-baseSets)<=Math.max(2,base.items.length),
   // No invented claim of better strength gains. These are operational proxy metrics.
   proxies:{feasible:adapted.estimatedSeconds<=num(input.minutes,base.minutes)*60+1,
     completedExerciseCoverage:overlap===adapted.items.length,
     fatiguePenaltyBefore:fatiguePenalty(base.items,model,input.profile),
     fatiguePenaltyAfter:fatiguePenalty(adapted.items,model,input.profile)},
   scientificallyValidated:false,causalImprovementEstablished:false};
}
function planDay(input={}){
 const base=V4.planDay(input),model=learn(input),gated=!!input.readiness?.pain&&!input.readiness?.painArea;
 let out=base;
 if(!gated&&base.items.length)out=adjustDay(base,input,model);
 const rolling=rollingHorizon(input,model,base),comparison=compare(base,out,model,input);
 const safety={...out.safety,flags:[...(out.safety?.flags||[])]};
 if(!comparison.proxies.feasible){out=base;comparison.reverted=true;comparison.reason='예상 운동 시간이 제한을 초과하여 원래 계획으로 복구했습니다.';}
 if(gated){out=base;safety.stop=true;}
 out={...out,safety,version:VERSION,schema:'precision-v7',v7:{model,rolling,comparison,changes:out.v7Changes||[],
   fallback:'V4 baseline',explanation:'훈련량은 완료 기록의 신뢰도를 검토한 뒤 제한된 범위에서만 조절합니다. 생리학적 최적 처방으로 검증된 결과가 아닙니다.'}};
 out.optimizer={...out.optimizer,engine:VERSION,baseline:'V4',clinicallyValidated:false,
   v7Confidence:model.confidence,v7DeltaSets:comparison.deltaSets,rollingHorizonDays:14};
 out.explanation+=' V7: '+out.v7.explanation+' '+rolling.explanation;
 return out;
}
function planProgram(input={}){
 const baseline=V4.planProgram(input),today=planDay({...input,minutes:input.minutes||input.profile?.duration||60}),now=num(input.context?.now,Date.now());
 const program={...baseline,version:VERSION,schema:'precision-v7-program',rolling:today.v7.rolling,
   learning:{confidence:today.v7.model.confidence,sessions:today.v7.model.samples,cohort:'individual-records-only'},
   comparison:today.v7.comparison};
 // Near-term specific calendar slots are projections and NOT pre-committed weights.
 for(const slot of program.rolling.slots){const w=Math.floor((Date.parse(slot.date)-now)/WEEK);
  if(w>=0&&w<program.calendar.length){const week=program.calendar[w];week.v7Slots=week.v7Slots||[];
   week.v7Slots.push({date:slot.date,dayName:slot.dayName,muscles:slot.muscles});}
 }
 return program;
}
function audit(input={}){
 const history=input.history||[],n=Math.min(history.length,24),out=[];
 // Temporal holdout: each historical session is evaluated only with earlier data.
 for(let i=Math.max(0,history.length-n);i<history.length;i++){
  const session=history[i],previous=history.slice(0,i),now=at(session,Date.now());if(!now)continue;
  const mod=learn({...input,history:previous,now:now-1});
  const actual=(session.items||[]).flatMap(it=>(it.sets||[]).filter(s=>valid(s)));
  const prescribed=(session.items||[]).flatMap(it=>(it.sets||[]).filter(s=>!s.warmup));
  if(!prescribed.length)continue;
  const completed=actual.length/prescribed.length;
  const pain=!!session.feedback?.pain||actual.some(s=>s.pain);
  const overexertion=num(session.feedback?.difficulty,5)>=9;
  out.push({date:new Date(now).toISOString().slice(0,10),trainedAt:now,priorRecords:mod.samples,
   completion:rnd(completed),pain,overexertion,confidence:mod.confidence,
   v7CounterfactualAvailable:false});
 }
 const rate=f=>rnd(average(out.map(f)),3);
 return {schema:'precision-v7-audit',records:out.length,holdout:out,
   observed:{completion:rate(x=>x.completion),painReports:rate(x=>x.pain?1:0),veryHardSessions:rate(x=>x.overexertion?1:0)},
   // Historical V4 sessions cannot establish counterfactual V7 improvements.
   conclusion:'과거 V4 기록은 운영 지표만 검증합니다. V7 효과를 평가하려면 실제 V7 계획과 비교 데이터가 필요합니다.',
   validatedSuperior:false,protocol:'rolling-origin chronological holdout, no future-data leakage'};
}
function validatePlan(plan){const v=V4.validatePlan(plan);const issues=[...v.issues];
 if(plan.v7?.comparison?.proxies?.feasible===false)issues.push('time-exceeded');
 if(plan.items.some(it=>countWork(it)>6))issues.push('excessive-sets');
 if(plan.safety?.stop&&plan.items.length)issues.push('safety-stop-not-enforced');
 return {ok:issues.length===0,issues};
}
return {...V4,VERSION,learn,rollingHorizon,planDay,planProgram,audit,compare,validatePlan,
 modelDescription:'Deterministic offline learning with low-confidence gates; not medical or validated optimization'};
});