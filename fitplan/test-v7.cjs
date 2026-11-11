const assert=require('node:assert/strict');
const DAY=86400000;
const V7=require('./native/app/src/main/assets/precision-engine-v7.js');
const ids=['leg_press','goblet_squat','body_squat','split_squat','chest_press','db_press','bench_press','pushup','cable_fly','lat_pulldown','assisted_pullup','pullup','seated_row','db_row','band_row','rld_machine','db_rdl','glute_bridge','hip_thrust','shoulder_press','db_shoulder','lateral_raise','face_pull','triceps_push','triceps_db','biceps_curl','cable_curl','calf_raise','plank','dead_bug','walking'];
const pat=['squat','squat','squat','squat','push','push','push','push','chestiso','pullvertical','pullvertical','pullvertical','pullhorizontal','pullhorizontal','pullhorizontal','hinge','hinge','glutes','glutes','verticalpush','verticalpush','shoulderiso','shoulderiso','triceps','triceps','biceps','biceps','calves','core','core','cardio'];
const muscles=['하체','하체','하체','하체','가슴','가슴','가슴','가슴','가슴','등','등','등','등','등','등','뒤허벅지','뒤허벅지','둔근','둔근','어깨','어깨','어깨','어깨','삼두','삼두','이두','이두','종아리','복부','복부','유산소'];
const catalog=ids.map((id,i)=>({id,n:id,m:muscles[i],pattern:pat[i],gear:['body_squat','split_squat','pushup','pullup','glute_bridge','calf_raise','plank','dead_bug'].includes(id)?'body':id.startsWith('db_')||id==='goblet_squat'||id==='biceps_curl'||id==='lateral_raise'||id==='triceps_db'?'dumbbell':'machine',kind:pat[i].includes('iso')?'isolation':'compound',level:0}));
const p={sex:'male',weight:96,level:1,goal:'hypertrophy',days:3,duration:60,place:'gym',physique:'balanced',focus:['등'],restrictions:[]};
const input={profile:p,readiness:{energy:4,sleep:4,soreness:2,pain:false},catalog,history:[],sessionIndex:0,minutes:60,context:{now:Date.now()}};
const today=V7.planDay(input);
console.log('today',today.schema,today.items.map(i=>i.id),today.v7.rolling.slots.length,today.v7.comparison);
assert(today.items.length);assert(V7.validatePlan(today).ok);assert(today.v7.model.confidence===0);assert(today.v7.changes.length===0);assert(today.v7.rolling.slots.length===6);
const wed=V7.planDay({...input,availableWeekdays:[1,3,6]});assert(wed.v7.rolling.slots.every(s=>[1,3,6].includes(s.weekday)));
const sessionTime=Date.now()-70*DAY;
const history=Array.from({length:20},(_,k)=>({finishedAt:sessionTime+k*3*DAY,feedback:{difficulty:k<15?5:8,soreness:2,pain:false},items:[{eid:'chest_press',currentId:'chest_press',machineId:'alpha',pattern:'push',sets:Array.from({length:4},()=>({done:true,warmup:false,actualId:'chest_press',machineId:'alpha',actualWeight:40+k*.5,actualReps:9,targetReps:8,rir:3,form:'good',pain:false}))}]}));
const model=V7.learn({...input,history});console.log('learnt',model.samples,model.muscles['가슴'],model.exercises['chest_press|alpha']);assert(model.samples===20);assert(model.exercises['chest_press|alpha'].days===16);assert(model.muscles['가슴'].sessions===20);
const audit=V7.audit({...input,history});assert(audit.records<=24&&audit.records>0);assert(audit.validatedSuperior===false);
const prog=V7.planProgram({...input,history,weeks:8});assert(prog.calendar.length===8);assert(prog.rolling.slots.length===6);
const stop=V7.planDay({...input,readiness:{pain:true,energy:2,soreness:5,sleep:1}});assert(stop.safety.stop);assert(stop.items.length===0);
const imm=V7.planDay({...input,history});assert(imm.items.length);assert(V7.validatePlan(imm).ok);
console.log('PASS V7 tests');
// Regression: forecast day labels must never skip session indices in the live V4 rotation.
const rot=V7.planDay({...input,availableWeekdays:[0,1,2,3,4,5,6]});
const all=rot.v7.rolling.slots;
assert(all.length===p.days*2);
assert(all.every((z,i)=>z.sessionIndex===input.sessionIndex+i));
assert(all.every((z,i)=>z.date>=new Date(input.context.now).toISOString().slice(0,10)));
assert(all.every((z,i)=>i===0||z.offset>all[i-1].offset));
// Additional recovery stress alters only session targets, never the stored calibration.
const tired=V7.planDay({...input,readiness:{energy:2,soreness:4,sleep:2,pain:false}});
assert(tired.items.every(it=>it.v7LoadFactor===.95||it.sets.filter(s=>!s.warmup).length<2));
assert(tired.items.flatMap(it=>it.sets).filter(s=>!s.warmup).every(s=>s.targetRIR>=4));
// Maturity: stable RIR and 20 repeated sessions can justify only a bounded single set.
const stableHistory=Array.from({length:22},(_,k)=>({finishedAt:Date.now()-(66-k*3)*DAY,
 feedback:{difficulty:5,soreness:2,pain:false},items:[{eid:'chest_press',currentId:'chest_press',machineId:'alpha',pattern:'push',sets:
 Array.from({length:3},()=>({done:true,warmup:false,actualId:'chest_press',machineId:'alpha',actualWeight:50,actualReps:10,targetReps:9,rir:3,form:'good',pain:false}))}]}));
const matured=V7.learn({...input,history:stableHistory});
assert(matured.muscles['가슴'].confidence>=.45);
assert(matured.muscles['가슴'].stalled);
const q=V7.planDay({...input,history:stableHistory,minutes:90});
assert(q.v7.changes.filter(x=>x.muscle==='가슴'&&x.sets>0).length<=1);
// Existing increase in last 7 days is counted against the weekly budget.
const recentlyAdjusted=stableHistory.slice();recentlyAdjusted[recentlyAdjusted.length-1]={...recentlyAdjusted.at(-1),
 v7:{changes:[{muscle:'가슴',sets:1}]}};
const next=V7.planDay({...input,history:recentlyAdjusted,minutes:90});
assert(!next.v7.changes.some(x=>x.muscle==='가슴'&&x.sets>0));
// Observational V4/V7 audit reports actual recorded denominators, not a false win claim.
const mixed=[...stableHistory,{...stableHistory.at(-1),finishedAt:Date.now()-DAY,engineVersion:'7.4.0'}];
const observed=V7.audit({...input,history:mixed});
assert(observed.byEngine.V7.sessions===1);
assert(observed.byEngine.V4_or_legacy.sessions===22);
assert(!observed.validatedSuperior);
console.log('PASS V7 expanded safety, schedule consistency, weekly budget and observational audit tests');