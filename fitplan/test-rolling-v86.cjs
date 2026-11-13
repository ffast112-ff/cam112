/* FitPlan V8.6: cross-session optimization, not a single 60-minute special case.
 * Check actual V86 plan production across goals, frequency, time, venue, level,
 * including safety, past data immutability, subjective fatigue isolation.
 */
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const assets=path.resolve(__dirname,'native/app/src/main/assets');
const V3=require(path.join(assets,'precision-engine-v3.js'));
const V4=require(path.join(assets,'precision-engine-v4.js'));
const V75=require(path.join(assets,'precision-engine-v75.js'));
const V86=require(path.join(assets,'precision-engine-v86.js'));
const ns={};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'tmp_extract/catalog.js'),'utf8')+'\nthis.catalog=CATALOG;',ns);
const catalog=ns.catalog;
const NOW=Date.parse('2026-11-13T12:00:00Z');
const goals=['strength','hypertrophy','fatloss','fitness'];
const times=[30,45,60,90,120],days=[2,3,4,6],venues=['gym','home'],levels=[0,3];
const variations=[];
let cases=0,changed=0,positive=0,blocked=0,mismatched=0,empty=0;
function input(profile,sessionIndex=0,readiness={pain:false},history=[]){
 return {profile,readiness,history,catalog,sessionIndex,
  minutes:profile.duration,context:{now:NOW},availableWeekdays:[]};
}
function signature(p){return JSON.stringify({
 ids:p.items.map(it=>it.id),sets:p.items.map(it=>it.sets.map(x=>
  [x.targetReps,x.targetWeight,x.targetRIR,x.role,x.warmup])),
  split:p.split,seconds:p.estimatedSeconds
});}
for(const goal of goals)for(const duration of times)for(const day of days)
for(const place of venues)for(const level of levels){
 const profile={goal,duration,days:day,place,level,physique:'balanced',
  focus:['가슴','등','어깨','팔','하체'],restrictions:[]};
 const inp=input(profile);
 const before=JSON.stringify(inp);
 const base=V75.planDay(inp);
 const current=V86.planDay(inp);
 assert.equal(JSON.stringify(inp),before,'V86 mutated profile, history, or config');
 assert(current.items&&current.v86,'V86 result is missing optimizer metadata');
 assert.equal(current.split,base.split,'Unexpected split change');
 assert.equal(current.safety?.stop,base.safety?.stop,'Safety stop changed');
 assert(current.estimatedSeconds<=duration*60+1,'Time budget exceeded');
 assert(V75.evaluate(inp,current).ok,'V7.5 structural quality gate failed');
 assert(current.items.every(it=>V3.allowedExercise(catalog.find(x=>x.id===it.id),profile,{pain:false})),
   'Disallowed exercise introduced by optimizer');
 assert.equal(new Set(current.items.map(x=>x.id)).size,current.items.length,'Duplicate movement');
 if(day===2&&duration>=45){
  const pats=current.items.map(x=>x.pattern);
  assert(pats.includes('push')&&pats.some(x=>x.startsWith('pull'))&&
    pats.some(x=>['squat','hinge','glutes'].includes(x)),
    'Low-frequency full-body major pattern missing');
 }
 if(current.v86.changed){
  changed++;
  assert.notEqual(signature(current),signature(base),'Changed is false-positive');
  assert(current.v86.optimizedScore>current.v86.baselineScore,'Optimizer did not improve proxy objective');
  assert.equal(current.items.slice(0,3).map(x=>x.id).join('|'),
   base.items.slice(0,3).map(x=>x.id).join('|'),
   'Primary movements should remain stable');
 }else if(current.v86.changes>0){
  // Future substitutions are not silently saved; they are only forecasts.
  assert.equal(signature(current),signature(base),"Uncommitted future plan changed today\'s result");
 }
 cases++;
 if(current.v86.lookahead>1)positive++;
 if(current.v86.changes)variations.push({goal,duration,day,place,level,
  changed:current.v86.changed,improvement:current.v86.optimizedScore-current.v86.baselineScore,
  baseline:base.items.map(x=>x.id),optimized:current.items.map(x=>x.id)});
}
const coreProfile={goal:'hypertrophy',days:2,duration:60,level:3,
 place:'gym',physique:'balanced',focus:['등','가슴','어깨','하체'],restrictions:[]};
const baseInput=input(coreProfile);
const first=V86.planDay(baseInput);
for(const r of [
 {pain:false,energy:1,sleep:1,soreness:5},
 {pain:false,energy:5,sleep:5,soreness:1},
 {pain:false}
]){
 assert.equal(signature(V86.planDay(input(coreProfile,0,r))),signature(first),
  'Subjective fatigue data affected the new rolling optimizer');
}
for(const painArea of [null,'어깨','허리','무릎']){
 const r={pain:true,painArea};
 const plan=V86.planDay(input(coreProfile,0,r));
 const baseline=V75.planDay(input(coreProfile,0,r));
 assert.equal(signature(plan),signature(baseline),
  'Pain-safe baseline should be passed through unchanged');
 assert.equal(!!plan.safety?.stop,!!baseline.safety?.stop,'Pain safety modified');
 blocked++;
}
const history=[{finishedAt:NOW-3*86400000,items:[{id:'leg_press',sets:[{
 done:true,actualWeight:120,actualReps:10,targetReps:10,rir:2,warmup:false
 }]}],feedback:{pain:false,difficulty:5,soreness:5},readiness:{sleep:2,energy:2,soreness:5}}];
const clean=JSON.parse(JSON.stringify(history));
delete clean[0].feedback.soreness;clean[0].readiness={pain:false};
assert.equal(signature(V86.planDay(input(coreProfile,1,{pain:false},history))),
 signature(V86.planDay(input(coreProfile,1,{pain:false},clean))),
 'Legacy fatigue history affected workout');
const report={cases,lookaheadApplied:positive,changed,blocked,
 examples:variations.slice(0,12),scientificValidation:false};
console.log('V8.6 CROSS SESSION RESULTS '+JSON.stringify(report));
assert.equal(cases,320,'Expected full cross-profile matrix');
assert(positive>=250,'Planning horizon not applied to enough scenarios');
assert(changed>0,'No profile improved — optimizer may be ineffective');
fs.writeFileSync(path.join(__dirname,'quality-v86-report.json'),JSON.stringify(report,null,2));
console.log('PASS cross-profile and multi-session optimization checks');
