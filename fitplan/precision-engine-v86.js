/* FitPlan V8.6 — bounded rolling-program optimizer.
 * Objective: distribute the user's finite training time and real performed weekly
 * stimulus over a block of sessions while keeping a familiar main movement.
 * NO subjective fatigue, sleep, soreness, inferred recovery, or pseudo-physiology.
 * Every change is deterministic, reversible, equipment/pain filtered, time bounded.
 */
(function(root,factory){
 const V75=root.FitPlanPrecisionV75||(typeof require==='function'?require('./precision-engine-v75.js'):null);
 const V4=root.FitPlanPrecisionV4||(typeof require==='function'?require('./precision-engine-v4.js'):null);
 const V3=root.FitPlanPrecisionV3||(typeof require==='function'?require('./precision-engine-v3.js'):null);
 const api=factory(V75,V4,V3);
 if(typeof module==='object'&&module.exports)module.exports=api;
 else root.FitPlanPrecisionV86=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(V75,V4,V3){
'use strict';
if(!V75||!V4||!V3)throw Error('FitPlan V8.6 requires V3, V4 and V7.5');
const VERSION='8.6.0';
const C={
 squat:{하체:1,둔근:.4},
 hinge:{뒤허벅지:1,둔근:.5},
 glutes:{둔근:1,뒤허벅지:.25},
 push:{가슴:1,삼두:.35,어깨:.15},
 chestiso:{가슴:1},
 pullvertical:{등:1,이두:.35},
 pullhorizontal:{등:1,이두:.35,어깨:.2},
 verticalpush:{어깨:1,삼두:.35},
 shoulderiso:{어깨:1},
 triceps:{삼두:1},
 biceps:{이두:1},
 calves:{종아리:1},
 core:{복부:1}
};
const MAJOR=['하체','가슴','등','뒤허벅지','어깨'];
const SUP=['둔근','이두','삼두','복부','종아리'];
const ALL=[...MAJOR,...SUP],DAY=86400000;
const n=(v,d=0)=>v===null||v===undefined||v===''?d:Number.isFinite(+v)?+v:d;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const round=(v,d=2)=>Math.round(v*10**d)/10**d;
const work=it=>(it.sets||[]).filter(s=>!s.warmup&&s.role!=='warmup');
const copyItem=it=>({...it,sets:(it.sets||[]).map(s=>({...s}))});
const mFor=it=>C[it.pattern]||{};
const eq=(a,b)=>a.map(it=>it.id).join('|')===b.map(it=>it.id).join('|');
function allowed(it,input,index){
 const cat=(input.catalog||[]).find(e=>e.id===it.id);
 if(!cat)return false;
 const r=index===0?input.readiness||{}:{pain:false};
 try{return V3.allowedExercise(cat,input.profile,r);}catch(e){return false;}
}
function estimate(it){
 const count=work(it).length;
 const reps=n(work(it)[0]?.targetReps,10);
 const seconds=clamp(n(it.rest,75),30,240);
 return count*(seconds+clamp(reps,4,30)*2.7+17)+38;
}
function credit(plans){
 const credits=Object.fromEntries(ALL.map(m=>[m,0]));
 const patterns={},exerciseCount={};
 for(const p of plans)for(const it of p.items){
  exerciseCount[it.id]=(exerciseCount[it.id]||0)+1;
  patterns[it.pattern]=(patterns[it.pattern]||0)+1;
  const count=work(it).length;
  for(const [m,v] of Object.entries(mFor(it)))credits[m]=(credits[m]||0)+count*v;
 }
 return {credits,patterns,exerciseCount};
}
function target(input,count){
 const p=input.profile||{},minutes=clamp(n(input.minutes,p.duration||60),30,120),days=clamp(n(p.days,3),2,6);
 // Practical effort budget, not a claim that every muscle needs a fixed 16 sets.
 // Multiply by block length; a training block covers ~count/days weeks.
 const fraction=count/Math.max(2,days);
 const base=clamp(2.5*days*Math.pow(minutes/60,.55),3,12)*fraction;
 const major=Object.fromEntries(MAJOR.map(m=>[m,round(base*(m==='어깨'?.7:m==='뒤허벅지'?.75:1))]));
 const support=Object.fromEntries(SUP.map(m=>[m,round(base*(m==='둔근'?.55:.32))]));
 const special=(p.focus||[]).filter(x=>MAJOR.includes(x));
 if(special.length>0&&special.length<=2)for(const m of special)major[m]=round(major[m]*1.15);
 return {...major,...support};
}
function score(plans,input,options={}){
 const {credits,patterns,exerciseCount}=credit(plans),goals=target(input,plans.length);
 const goal=(input.profile||{}).goal||'hypertrophy';
 let value=0;
 // Diminishing returns: reduce deficits, but don't reward excessive extra sets.
 for(const m of ALL){
  const got=n(credits[m]),want=Math.max(1,goals[m]),ratio=got/want;
  const importance=MAJOR.includes(m)?(goal==='hypertrophy'?2.5:2.0):.65;
  value+=importance*(Math.min(ratio,1)*4.2+Math.min(Math.max(0,ratio-1),.3)*.65);
  if(got<=.01&&MAJOR.includes(m))value-=2.4;
 }
 const a=(name)=>n(patterns[name],0);
 const has=(list)=>list.some(x=>a(x));
 const blockSessions=plans.length;
 const patternRewards=[
  [['pullhorizontal'],2.5],
  [['pullvertical'],1.3],
  [['hinge','glutes'],2.3],
  [['verticalpush','shoulderiso'],2.0]
 ];
 if(blockSessions>=3)for(const [list,weight] of patternRewards){
  if(has(list))value+=weight;
 }
 if(n(input.minutes,input.profile?.duration||60)>=75&&has(['core']))value+=.5;
 // Stable repeatable main movements for tracking progression, but avoid
 // all sessions consisting of exactly the same four exercises.
 for(const count of Object.values(exerciseCount)){
  if(count===2||count===3)value+=.19;
  if(count>Math.max(3,Math.ceil(blockSessions*.75)))value-=(count-3)*.14;
 }
 for(const p of plans){
  if(p.estimatedSeconds>n(input.minutes,input.profile?.duration||60)*60+1)value-=1000;
  const it=p.items,ids=new Set(it.map(x=>x.id));
  if(ids.size!==it.length)value-=1000;
  if(it.length&&work(it[0]).length===0)value-=5;
 }
 value-=n(options.changes)*.7; // Small, explicit stability cost
 return round(value,4);
}
function block(input,base){
 const p=input.profile||{},days=clamp(n(p.days,3),2,6),len=Math.min(6,Math.max(4,days*2));
 const idx=n(input.sessionIndex,0);
 const out=[base];
 for(let i=1;i<len;i++){
  let future;
  try{
   future=V4.planDay({...input,sessionIndex:idx+i,readiness:{pain:false}});
  }catch(e){break;}
  if(!future?.items?.length)break;
  out.push(future);
 }
 return out;
}
function criticalPatterns(it,input){
 const p=input.profile||{};
 if(p.days>2||n(input.minutes,p.duration||60)<45)return true;
 const patterns=new Set(it.map(x=>x.pattern));
 return patterns.has('push')&&
  (patterns.has('pullvertical')||patterns.has('pullhorizontal'))&&
  it.some(x=>['squat','hinge','glutes'].includes(x.pattern));
}
function optimization(input,initial){
 if(!initial?.items?.length||initial.safety?.stop||
   input.readiness?.pain||input.readiness?.formConcern)
   return {today:initial,changed:false,reason:'통증 및 안전 제한 또는 운동 없음',candidates:0};
 const plans=block(input,initial);
 if(plans.length<2)return {today:initial,changed:false,reason:'연속 운동일 예측 정보 부족',candidates:0};
 const catalog=input.catalog||[];
 const allDonors=[];
 for(const p of plans)for(const it of p.items){
  if(!allDonors.some(z=>z.id===it.id))allDonors.push(it);
 }
 const p=input.profile||{},minutes=n(input.minutes,p.duration||60);
 const locked=initial.split==='full'&&minutes>=45?3:Math.min(2,initial.items.length);
 const baselineScore=score(plans,input),updated=plans.map(x=>({...x,items:x.items.map(copyItem)}));
 let changes=0,candidates=0;
 // Local search over at most 6 projected sessions and 2 elective positions.
 // Keep the first lower/push/pull anchors and exact split-day sequence.
 for(let pass=0;pass<2;pass++){
  let best=null,bestGain=.05;
  for(let i=0;i<updated.length;i++){
   const cur=updated[i],limit=i===0?locked:cur.split==='full'&&minutes>=45?3:Math.min(2,cur.items.length);
   for(let pos=limit;pos<cur.items.length;pos++){
    const old=cur.items[pos];
    const oldSecs=estimate(old);
    for(const donor of allDonors){
     if(donor.id===old.id||cur.items.some((it,j)=>j!==pos&&it.id===donor.id))continue;
     if(!allowed(donor,input,i))continue;
     // Never smuggle a restricted pattern through an upper/lower split.
     if(cur.split!=='full'){
      const oldLower=['squat','hinge','glutes','calves'].includes(old.pattern);
      const newLower=['squat','hinge','glutes','calves'].includes(donor.pattern);
      if(oldLower!==newLower)continue;
     }
     const estimated=cur.estimatedSeconds-oldSecs+estimate(donor);
     if(estimated>minutes*60+1||estimated<0)continue;
     const trial=cur.items.slice();trial[pos]=copyItem(donor);
     if(!criticalPatterns(trial,input))continue;
     // Avoid a replacement whose warm-up/working-set mix is incompatible with
     // the existing slot. All weights are still calibrated on the actual device.
     const version=updated.map((z,j)=>j===i?{...cur,items:trial,estimatedSeconds:estimated}:z);
     const next=score(version,input,{changes:changes+1});
     candidates++;
     const prev=score(updated,input,{changes});
     const gain=next-prev;
     if(gain>bestGain){bestGain=gain;best={i,pos,donor,estimated};}
    }
   }
  }
  if(!best)break;
  const row=updated[best.i];
  row.items[best.pos]=copyItem(best.donor);
  row.estimatedSeconds=best.estimated;
  row.estimatedMinutes=Math.ceil(best.estimated/60);
  changes++;
 }
 const after=score(updated,input,{changes});
 const today=updated[0],changeToday=!eq(initial.items,today.items);
 // The best program can improve only future sessions; that information remains
 // informative but does not claim to have pre-committed anything to the calendar.
 return {today:changeToday?today:initial,changed:changeToday,changes,
  initialScore:baselineScore,optimizedScore:after,candidates,lookahead:plans.length,
  weeklyTargets:target(input,plans.length),before:credit(plans).credits,
  after:credit(updated).credits,
  future:updated.map((x,i)=>({sessionIndex:n(input.sessionIndex,0)+i,
    split:x.split,ids:x.items.map(it=>it.id)})),
  reason:changes?'주요 동작을 유지하면서 연속 운동일의 보조운동 균형 조정':'기존 운동 구성 유지'};
}
function planDay(input={}){
 const baseline=V75.planDay(input);
 const result=optimization(input,baseline);
 // Require a strict positive score gain, never change a blocked or infeasible plan.
 const today=result.today;
 const safe= result.changed&&V75.evaluate(input,today).ok &&
  today.estimatedSeconds<=n(input.minutes,input.profile?.duration||60)*60+1;
 const output=safe?today:baseline;
 return {...output,version:VERSION,
  v86:{schema:'rolling-v86',changed:!!safe,changes:result.changes||0,
   lookahead:result.lookahead||0,candidates:result.candidates||0,
   baselineScore:result.initialScore??null,optimizedScore:result.optimizedScore??null,
   weeklyTargets:result.weeklyTargets||null,
   projectedCredits:result.after||null,
   future:result.future||[],reason:result.reason||'기존 처방 유지',
   comparisonIsHeuristic:true,physiologicalValidityClaimed:false}};
}
function planProgram(input={}){
 const program=V75.planProgram(input);
 const today=planDay(input);
 return {...program,version:VERSION,
  v86:today.v86,qualityPolicy:'상세 주간 자극은 완료된 수행 기록을 기준으로 재계산'};
}
return {...V75,VERSION,planDay,planProgram,score,optimization,
 modelDescription:'Deterministic time- and equipment-bounded rolling exercise distribution; intensity from V7.5, no fatigue scores.'};
});
