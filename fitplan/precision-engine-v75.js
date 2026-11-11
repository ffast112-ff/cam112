/* FitPlan Adaptive Coach V7.5 — offline heuristics, not medical advice. */
(function(root,factory){
 const V7=root.FitPlanPrecisionV7||(typeof require==='function'?require('./precision-engine-v7.js'):null);
 const V4=root.FitPlanPrecisionV4||(typeof require==='function'?require('./precision-engine-v4.js'):null);
 const api=factory(V7,V4);
 if(typeof module==='object'&&module.exports)module.exports=api;
 else root.FitPlanPrecisionV75=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(V7,V4){
'use strict';
if(!V7||!V4)throw Error('V7.5 depends on V7 and V4');
const N=(x,d=0)=>x==null||x===''?d:Number.isFinite(+x)?+x:d;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const id=it=>it.currentId||it.eid||it.id;
function histories(input,eid,machine){
 const out=[];
 for(const h of input.history||[])for(const it of h.items||[]){
  if(id(it)!==eid)continue;
  for(const s of it.sets||[]){
   if(!s.done||s.warmup||s.role==='warmup'||s.pain||s.form==='poor')continue;
   if((s.machineId||it.machineId||'default')!==(machine||'default'))continue;
   if(N(s.actualReps)<=0)continue;
   out.push({weight:N(s.actualWeight),reps:N(s.actualReps),target:N(s.targetReps),rir:s.rir==null?null:N(s.rir),
    time:N(h.finishedAt||h.timestamp||Date.parse(h.date))});
  }
 }
 return out.sort((a,b)=>a.time-b.time).slice(-24);
}
function plateau(input,eid,machine){
 const h=histories(input,eid,machine).filter(x=>x.weight>0&&x.reps>=3&&x.reps<=15).slice(-9);
 if(h.length<6)return {stalled:false,confidence:0,reason:'비교 가능한 기록이 부족함'};
 const metric=x=>x.weight*(1+Math.min(18,x.reps+N(x.rir,2))/30);
 const m=a=>a.map(metric).sort((a,b)=>a-b)[1];
 const early=m(h.slice(0,3)),late=m(h.slice(-3));
 const span=h[h.length-1].time-h[0].time;
 const stalled=span>=14*86400000&&late<=early*1.012;
 return {stalled,confidence:span>=21*86400000?.8:.5,delta:early>0?+(late/early-1).toFixed(3):0,
  reason:stalled?'성과 정체 가능성: 증량보다 회복 및 훈련량 점검':'기록 개선 또는 관찰기간 부족'};
}
function nextSet({weight,reps,targetReps,rir,pain=false,form='unknown',increment=2.5}){
 const step=clamp(N(increment,2.5),.5,25),w=N(weight),r=N(reps),target=Math.max(1,N(targetReps,10));
 if(!w||!r)return {weight:w,delta:0,reason:'실제 수행량을 입력해 주세요'};
 if(pain||form==='poor')return {weight:w,delta:0,hold:true,reason:'통증·자세 문제로 자동 증량 중단'};
 const effort=rir==null||rir===''?null:N(rir);
 let delta=0;
 if(r<target-2||(r<target&&effort!==null&&effort<=1))delta=-step;
 else if(r>=target&&effort!==null&&effort>=4)delta=step;
 const next=Math.max(step,Math.round((w+delta)/step)*step);
 return {weight:next,delta:next-w,reason:delta<0?'반복 목표 미달로 한 단계 감량':delta>0?'높은 여유가 확인되어 한 단계 증량':'동일 중량 유지'};
}
function nextWorkout(input,eid,machine,increment=2.5){
 const a=histories(input,eid,machine).filter(x=>x.weight>0);
 if(!a.length)return {weight:null,confidence:0,reason:'기구별 첫 측정 필요'};
 const v=a.slice(-3),last=a[a.length-1],p=plateau(input,eid,machine),step=clamp(N(increment,2.5),.5,25);
 const good=v.filter(x=>x.reps>=x.target&&x.rir!==null&&x.rir>=2).length;
 const poor=v.filter(x=>x.reps<x.target-1||(x.rir!==null&&x.rir===0)).length;
 const delta=poor>=2?-step:good>=2&&!p.stalled?step:0;
 return {weight:Math.max(step,Math.round((last.weight+delta)/step)*step),confidence:clamp(v.length/5,0,.6),
  reason:delta>0?'연속 목표 달성':delta<0?'반복 목표 미달':p.stalled?'정체기 유지':'기록 기반 중량 유지',plateau:p};
}
function evaluate(input,p){
 const errors=[],warnings=[],ids=new Set();
 for(const it of p.items||[]){
  if(ids.has(it.id))warnings.push('duplicate-exercise:'+it.id);ids.add(it.id);
  const sets=(it.sets||[]).filter(x=>!x.warmup&&x.role!=='warmup');
  if(sets.length>6)errors.push('excessive-sets:'+it.id);
  if(sets.some(x=>N(x.targetReps)<=0))errors.push('invalid-reps:'+it.id);
 }
 if(p.safety?.stop&&(p.items||[]).length)errors.push('unsafe-plan');
 if(p.v7?.comparison?.proxies?.feasible===false)warnings.push('time-fallback');
 return {ok:errors.length===0,errors,warnings};
}
function planDay(input={}){
 const out=V7.planDay(input),checks=evaluate(input,out);
 if(!checks.ok){
  const fallback=V4.planDay(input);
  return {...fallback,version:'7.5.0',v75:{fallback:true,checks,alerts:[]}};
 }
 const alerts=[];
 for(const it of out.items||[]){
  const p=plateau(input,it.id,'default');
  if(p.stalled)alerts.push({id:it.id,message:p.reason});
 }
 return {...out,version:'7.5.0',v75:{fallback:false,checks,alerts,
  note:'개인 학습과 피로 지표는 실제 생리학적 최적화가 아닌 보수적 경험칙입니다.'}};
}
function planProgram(input={}){return {...V7.planProgram(input),version:'7.5.0'};}
function audit(input={}){
 const out=V7.audit(input);let attempted=0,success=0;
 for(const h of input.history||[])for(const it of h.items||[])for(const s of it.sets||[]){
  if(!s.done||s.warmup||s.role==='warmup'||s.pain||s.form==='poor'||N(s.targetReps)<=0)continue;
  attempted++;if(N(s.actualReps)>=N(s.targetReps))success++;
 }
 return {...out,v75:{completedSets:attempted,targetAchievement:attempted?success/attempted:null,scientificallyValidated:false}};
}
return {...V7,VERSION:'7.5.0',planDay,planProgram,audit,evaluate,nextSet,nextWorkout,plateau,histories};
});
