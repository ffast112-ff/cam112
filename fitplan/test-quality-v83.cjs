/* FitPlan V8.3 quality regression matrix: 3,680 generated routines, baseline + adaptive. */
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const assets=path.resolve(__dirname,'native/app/src/main/assets');
const V3=require(path.join(assets,'precision-engine-v3.js'));
const V4=require(path.join(assets,'precision-engine-v4.js'));
const V75=require(path.join(assets,'precision-engine-v75.js'));
const c={};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'tmp_extract/catalog.js'),'utf8')+'\nthis.cat=CATALOG',c);
const catalog=c.cat;
assert(catalog.length>=25,'Full equipment catalog expected');
const goals=['strength','hypertrophy','fatloss','fitness'],times=[30,45,60,90,120],
 days=[2,3,4,5,6],levels=[0,1,2,3],places=['gym','home'];
const readNorm={energy:3,sleep:3,soreness:2,pain:false};
const readFatigue={energy:1,sleep:2,soreness:4,pain:false};
const readPain={energy:3,sleep:3,soreness:2,pain:true,painArea:'어깨'};
const readUnknown={energy:3,sleep:3,soreness:2,pain:true,painArea:null};
const rows=[],faults=[];
function check(p,r,index=0,adaptive=false){
 const input={profile:p,catalog,readiness:r,history:[],sessionIndex:index,minutes:p.duration,context:{now:Date.now()}};
 let result;
 try{result=(adaptive?V75:V4).planDay(input);}
 catch(err){faults.push({type:'exception',error:String(err),profile:p});return;}
 const patterns=result.items.map(x=>x.pattern);
 const sets=result.items.map(x=>(x.sets||[]).filter(y=>!y.warmup&&y.role!=='warmup').length);
 const missing=['push','pull','lower'].filter(group=>!patterns.some(x=>group==='push'?x==='push':group==='pull'?['pullvertical','pullhorizontal'].includes(x):['squat','hinge','glutes'].includes(x)));
 const invalid=result.items.filter(x=>!V3.allowedExercise(catalog.find(e=>e.id===x.id),p,r));
 const row={goal:p.goal,level:p.level,days:p.days,minutes:p.duration,place:p.place,
   readiness:r.pain?'pain':r.energy<3?'fatigue':'normal',restriction:p.restrictions.join(','),
   split:result.split,exerciseCount:result.items.length,sets:sets.reduce((a,b)=>a+b,0),
   maxSet:Math.max(0,...sets),time:result.estimatedMinutes,missing:missing.join(','),
   blocked:invalid.map(x=>x.id).join(','),stopped:!!result.safety?.stop,adaptive};
 rows.push(row);
 const err=(type)=>faults.push({type,row});
 if(result.estimatedSeconds>p.duration*60+1)err('over-time');
 if(invalid.length)err('contraindicated-exercise');
 if(r.pain&&!r.painArea&&(!result.safety?.stop||result.items.length))err('unsafe-unknown-pain');
 if(!adaptive&&p.duration<=60&&sets.some(n=>n>3))err('set-overconcentration');
 if(adaptive&&p.duration<=60&&sets.some(n=>n>4))err('adaptive-set-overconcentration');
 if(p.days===2&&p.duration>=45&&!r.pain&&r.energy>2&&!p.restrictions.length){
   if(result.split!=='full')err('low-frequency-wrong-split');
   if(missing.length)err('low-frequency-missing-major-pattern');
 }
 if(adaptive&&result.v75?.qualityVerified===false)err('unverified-quality-fallback');
}
let n=0;
for(const goal of goals)for(const duration of times)for(const d of days)
for(const level of levels)for(const place of places){
 const p={goal,physique:'balanced',level,days:d,duration,place,
   focus:['가슴','등','어깨','팔','하체'],restrictions:[]};
 check(p,readNorm,0);n++;
}
for(const d of [2,3,4])for(const duration of [30,45,60,90])
for(const goal of goals)for(const level of [0,3])for(const place of places)
for(const restrictions of [[],['어깨'],['허리'],['무릎'],['어깨','무릎']]){
 const p={goal,physique:'balanced',level,days:d,duration,place,focus:['등','하체'],restrictions};
 check(p,readFatigue,1);check(p,readPain,2);check(p,readUnknown,0);
}
assert.equal(rows.length,3680,'Expected 3,680 base scenario outcomes');
for(const goal of goals)for(const duration of [45,60,90])
for(const level of [0,1,3])for(const place of places){
 const p={goal,physique:'balanced',level,days:2,duration,place,
   focus:['가슴','등','어깨','팔','하체'],restrictions:[]};
 check(p,readNorm,0,true);check(p,readNorm,1,true);
}
const summary={baseline:3680,adaptive:rows.length-3680,
 criticalFailures:faults.length,invalid:p=>p};
delete summary.invalid;
fs.writeFileSync(path.join(__dirname,'quality-v83-results.json'),
 JSON.stringify({summary,issues:faults.slice(0,100),rows},null,2));
console.log('FITPLAN V8.3 SCENARIO REPORT',JSON.stringify(summary));
if(faults.length){
 console.error('QUALITY VIOLATIONS',JSON.stringify(faults.slice(0,12),null,2));
 process.exitCode=1;
}
