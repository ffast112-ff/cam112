/* Regression: changing subjective fatigue/sleep/soreness or old stored fatigue ratings
   must NOT alter the prescription. RIR, completed reps and pain still must work. */
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const assets=path.join(__dirname,'native/app/src/main/assets');
const V3=require(path.join(assets,'precision-engine-v3.js'));
const V4=require(path.join(assets,'precision-engine-v4.js'));
const V75=require(path.join(assets,'precision-engine-v75.js'));
const ns={};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'tmp_extract/catalog.js'),'utf8')+'\nthis.catalog=CATALOG;',ns);
const catalog=ns.catalog,now=Date.now();
const variations=[
 {energy:1,sleep:1,soreness:5,pain:false},
 {energy:5,sleep:5,soreness:1,pain:false},
 {energy:2,sleep:4,soreness:3,pain:false},
 {pain:false}
];
const profiles=[
 {goal:'strength',place:'gym',days:2,duration:60,level:3,physique:'balanced',focus:['가슴','등','어깨','하체'],restrictions:[]},
 {goal:'hypertrophy',place:'gym',days:4,duration:90,level:1,physique:'balanced',focus:['하체'],restrictions:[]},
 {goal:'fitness',place:'home',days:3,duration:45,level:0,physique:'balanced',focus:['등'],restrictions:[]}
];
const shape=plan=>JSON.stringify({
 split:plan.split,ids:plan.items.map(it=>it.id),
 sets:plan.items.map(it=>(it.sets||[]).map(s=>[s.warmup,s.targetWeight,s.targetReps,s.targetRIR])),
 score:plan.score?.total,estimated:plan.estimatedSeconds
});
for(const profile of profiles)for(const engine of [V3,V4,V75]){
 let prev=null;
 for(const r of variations){
  const input={profile,catalog,readiness:r,history:[],minutes:profile.duration,sessionIndex:0,context:{now}};
  const plan=engine.planDay(input);
  const current=shape(plan);
  if(prev!==null)assert.equal(current,prev,'Subjective fatigue changed '+engine.VERSION+' '+profile.goal);
  prev=current;
 }
}
const sample={id:'leg_press',currentId:'leg_press',machineId:'default',sets:[
 {done:true,warmup:false,role:'working',actualWeight:100,actualReps:10,targetReps:10,rir:2,form:'good'}
]};
const recentHistory=[{finishedAt:now-3*86400000,feedback:{difficulty:6,soreness:5},readiness:{energy:1,sleep:1,soreness:5},items:[sample]}];
const cleaner=JSON.parse(JSON.stringify(recentHistory));
delete cleaner[0].feedback.soreness;cleaner[0].readiness={pain:false};
for(const engine of [V3,V4,V75]){
 const input={profile:profiles[0],catalog,readiness:{pain:false},minutes:60,sessionIndex:1,context:{now}};
 assert.equal(shape(engine.planDay({...input,history:recentHistory})),
              shape(engine.planDay({...input,history:cleaner})),
              'Legacy subjective fatigue history changes workout: '+engine.VERSION);
}
assert(V3.normalizeReadiness({pain:true,painArea:'어깨',sleep:2}).pain,'Pain safety lost');
assert(!Object.hasOwn(V3.normalizeReadiness({sleep:1,soreness:5,energy:1}),'sleep'),
 'Fatigue fields must not appear in normalized readiness');
const tired=V75.nextSet({weight:100,reps:10,targetReps:10,rir:4,increment:2.5});
const hard=V75.nextSet({weight:100,reps:10,targetReps:10,rir:0,increment:2.5});
assert(tired.weight>hard.weight,'RIR-based intensity decisions lost');
const app=fs.readFileSync(path.join(assets,'app.js'),'utf8');
for(const s of ['오늘 에너지 상태','근육통·피로 누적','지난밤 수면·회복 상태','운동 후 근육 피로도'])
 assert(!app.includes(s),'Fatigue question rendered: '+s);
console.log('PASS V8.5 fatigue independence, legacy data isolation, pain safety, RIR intensity');
