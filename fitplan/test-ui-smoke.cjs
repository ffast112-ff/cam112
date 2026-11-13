/* Verify actual post-patch FitPlan DOM, not just JS syntax.
 * npm install --no-save jsdom@26 before running.
 */
const fs=require('fs'),path=require('path'),assert=require('assert');
const {JSDOM,VirtualConsole}=require('jsdom');
const assets=path.resolve(__dirname,'native/app/src/main/assets');
const index=fs.readFileSync(path.join(assets,'index.html'),'utf8');
const html=index.replace(/<script[^>]*src="[^"]+"[^>]*><\/script>/g,'');
const errors=[],consoleShim=new VirtualConsole();
consoleShim.on('jsdomError',e=>errors.push(String(e)));
consoleShim.on('error',e=>errors.push(String(e)));
const dom=new JSDOM(html,{url:'https://fitplan-local.test/',runScripts:'dangerously',pretendToBeVisual:true,virtualConsole:consoleShim});
const win=dom.window;
win.fetch=async()=>({ok:false,status:503,json:async()=>({})});
win.FitPlanNative={
  getAppVersion:()=> '1.9.16',saveSnapshot:()=>{},loadSnapshot:()=>'',cancelTimer:()=>{},
  scheduleTimer:()=>{},syncSchedule:()=>{},downloadUpdate:()=>{}
};
win.localStorage.setItem('fitplan_autocoach_01',JSON.stringify({
  schema:19,onboard:true,profile:{sex:'male',goal:'hypertrophy',days:3,duration:60,place:'gym',height:178,weight:96,focus:['등'],restrictions:[]},
  settings:{alert:'off',githubRepo:'ffast112-ff/cam112'},history:[],sessionIndex:0,machines:{},cycleReports:[]
}));
const scripts=Array.from(index.matchAll(/<script[^>]*src="([^"]+)"[^>]*><\/script>/g)).map(m=>m[1]);
for(const src of scripts){try{win.eval(fs.readFileSync(path.join(assets,src),'utf8')+'\n//# sourceURL='+src);}catch(e){throw new Error('Script '+src+' failed: '+e.stack);}}
assert(win.Fit,'FitPlan actions not registered');
for(const view of ['home','work','history','state','schedule']){
  try{win.Fit.go(view);}catch(e){throw new Error(view+': '+e.stack);}
  const text=win.document.querySelector('#app')?.textContent||'';
  assert(!text.includes('화면을 불러오지 못했습니다'),view+' crashed while rendering');
  assert(text.length>30,view+' produced blank UI');
  const nav=win.document.querySelector('.tabbar');
  assert(nav&&nav.querySelectorAll('button').length===4,'Bottom navigation not rendered for '+view);
  assert(win.document.querySelectorAll('svg.fp-art').length===0,'Broken external svg icon still used');
  const icons=[...win.document.querySelectorAll('img.fp-art')];
  assert(icons.length>=5,'Missing navigation images: '+view);
  for(const im of icons){
    assert(im.getAttribute('src').startsWith('data:image/svg+xml;base64,'),'Icon not self-contained');
    const svg=Buffer.from(im.src.split(',')[1],'base64').toString('utf8');
    assert(svg.includes('<svg')&&svg.includes('viewBox'),'Invalid icon SVG');
  }
  if(view==='schedule'){
    assert(win.document.querySelectorAll('.fp-day').length===42,'Calendar cells !=42');
    const before=win.document.querySelector('.fp-calendar-head strong').textContent;
    win.Fit.moveCalendar(1);
    assert(win.document.querySelector('.fp-calendar-head strong').textContent!==before,'Month navigation broken');
    win.Fit.todayCalendar();
    win.Fit.selectCalendar('2026-11-13');
    win.Fit.markCalendar('planned');
    assert(win.FitEngine.state().settings.scheduleOverrides['2026-11-13']==='planned','Manual schedule not saved');
  }
  process.stdout.write('PASS '+view+' '+text.length+' chars '+icons.length+' icons\n');
}
// Regression: projected days are not hard-coded Tue/Thu/Sat; actual exercise details display.
win.Fit.trainingWeekday(-1);
assert.deepStrictEqual(Array.from(win.FitEngine.state().settings.trainingWeekdays||[]),[],'No fixed weekday constraint');
const today=new Date(),local=[today.getFullYear(),String(today.getMonth()+1).padStart(2,'0'),String(today.getDate()).padStart(2,'0')].join('-');
win.FitEngine.state().history.push({
  schema:19,finishedAt:Date.now(),splitName:'테스트 하체',
  items:[{currentId:'test-exercise',sets:[{done:true,warmup:false,role:'work',actualWeight:90,actualReps:12}]}]
});
win.Fit.go('schedule');win.Fit.selectCalendar(local);
assert(win.document.querySelector('#app').textContent.includes('테스트 하체'),'Completed workout split missing on calendar');
assert(win.document.querySelector('#app').textContent.includes('1세트'),'Completed exercise count missing on calendar');
const detailIcons=win.document.querySelectorAll('img.fp-art.tiny-art').length;
assert(detailIcons>0,'Decorative detailed menu images were not rendered');
console.log('PASS history date details and image-based secondary icons',detailIcons);


win.Fit.go('home');
const homeText=win.document.querySelector('#app').textContent;
assert(homeText.includes('운동 시작')||homeText.includes('운동 이어하기'),'Homepage needs a single primary workout action');
assert(!homeText.includes('주간 운동 추세'),'Duplicate homepage trend should be removed');
win.Fit.go('state');
assert(win.document.querySelector('.fp-v8-stats'),'Condensed three-metric analytics missing');
const mainTabs=[...win.document.querySelectorAll('.tabbar button')].map(b=>b.textContent.trim());
assert.deepEqual(mainTabs,['홈','운동','일정','분석']);
win.fitplanBack();
assert(win.document.querySelector('#app').textContent.includes('이번 주'),'Android back must return to prior homepage');
win.Fit.go('ready');
const rng=win.document.querySelector('input[type="range"]');
assert(rng&&rng.style.getPropertyValue('--fp-pct').trim(),'Visible slider percent must follow selected time');
win.Fit.go('schedule');
const future=new Date(Date.now()+8*86400000);
const futureDay=[future.getFullYear(),String(future.getMonth()+1).padStart(2,'0'),String(future.getDate()).padStart(2,'0')].join('-');
win.Fit.selectCalendar(futureDay); // Future date, never the already-completed test session.
const buttons=win.document.querySelector('.fp-calendar-actions');
assert(buttons&&buttons.querySelectorAll('button').length===3,'Calendar must keep three actions in fixed row');
const legend=win.document.querySelector('.fp-calendar-legend');
assert(legend,'Calendar should retain status legend');
console.log('PASS V8: four tabs, single home action, prior-screen back, slider sync, fixed calendar actions');

// V8.1: onboarding alignment is scoped, Settings has a single weekday source,
// and calendar exercise names are actionable without altering training records.
win.Fit.go('setup');
assert(win.document.querySelector('.choices .choice'), 'Goal/physique choice cards missing');
assert(win.document.querySelectorAll('.field .chip').length>=6,'Focus chips missing');
win.Fit.go('settings');
const settingsText=win.document.querySelector('#app').textContent;
assert(!settingsText.includes('V7 적응형 훈련 일정'),'Duplicate weekday configuration remains in settings');
assert(!settingsText.includes('한국어 음성 안내'),'Removed voice coach still shown');
assert(!settingsText.includes('헬스장 기구 기록'),'Removed equipment registry still shown');
assert(!settingsText.includes('사진 촬영·기구 선택 안내'),'Experimental machine-camera entry still shown');
win.Fit.go('schedule');
assert(!win.document.querySelector('#app').textContent.includes('홈 화면 위젯'),'Widget instructions must not occupy schedule');
const days=[...win.document.querySelectorAll('button[onclick*="Fit.trainingWeekday("]')];
assert.equal(days.length,8,'Seven weekday chips and one automatic reset must remain in schedule');
win.Fit.selectCalendar('2026-11-13');
const exerciseLink=win.document.querySelector('.fp-v81-exercise');
if(exerciseLink){
 assert(exerciseLink.getAttribute('onclick').includes('Fit.guideByName'),'Calendar exercise must open detailed guide');
 exerciseLink.click();
 assert(win.document.querySelector('.modal'),'Exercise explanation modal must be accessible');
 win.Fit.closeModal();
}
console.log('PASS V8.1 setup, weekday layout, streamlined settings and workout details');


win.Fit.go('ready');
const v82Range=win.document.querySelector('input[type="range"][min="30"][max="120"]');
assert(v82Range,'Time range missing');
assert(typeof win.fpSyncTimeThumb==='function','Thumb alignment routine missing');
win.fpSyncTimeThumb();
assert(v82Range.style.getPropertyValue('--fp-thumb-fill'),'Pixel-correct range endpoint not calculated');
const appJS=fs.readFileSync(path.join(assets,'app.js'),'utf8');
assert(appJS.includes('const targetLabel=targetNumber>0?'),'Safe target label missing');
assert(appJS.includes('esc(targetLabel)'),'Target display is not protected from undefined');
const playerStyle=fs.readFileSync(path.join(assets,'style.css'),'utf8');
assert(playerStyle.includes('.player-page:has(.streamlined-player) .mint-ring'),'Compact player styles missing');
assert(playerStyle.includes('overflow:hidden'),'Player viewport clipping policy missing');
assert(playerStyle.includes('.player-page .player-close'),'Header icon centering missing');
console.log('PASS V8.2 time slider, safe target labels, compact player and centered buttons');


// Production-critical end-to-end action: buttons must actually start a plan,
// not merely render HTML.  A no-op is a blocking release regression.
win.Fit.go('ready');

const planBtns=[...win.document.querySelectorAll('#app button')].filter(b=>/운동 계획 만들기|운동 계획 생성|루틴 생성|운동 생성|운동 시작/.test(b.textContent));
assert(planBtns.length>0,'No workout generation button in preparation');
const generateBtn=planBtns.find(b=>/운동 계획 만들기|운동 계획 생성|루틴 생성|운동 생성/.test(b.textContent))||planBtns[0];
const beforeClick=win.FitEngine.state().active;
try{generateBtn.click();}catch(err){throw Error('Workout creation action threw: '+err.stack);}
const afterClick=win.FitEngine.state().active;
assert(afterClick&&afterClick.items&&afterClick.items.length>0,
 'Workout generation was no-op; button='+generateBtn.textContent+
 '; before='+Boolean(beforeClick)+'; errors='+errors.join(' | '));
assert(afterClick.v86&&afterClick.v86.schema==='rolling-v86',
 'Real workout button did not run the new multi-session optimizer');
assert(afterClick.v86.lookahead>=2||afterClick.v86.reason,
 'Rolling optimizer did not produce a quality result');
console.log('PASS critical E2E: workout creation button generated '+afterClick.items.length+' exercises');

const sourceApp=fs.readFileSync(path.join(assets,'app.js'),'utf8');
for(const term of ['function createPlan(', 'function finishSetup(', 'function completeSetup(', 'function resetProfile(', 'function profileSave(', 'function readyView(', 'function setupView(', '프로필 다시 설정', 'function startWorkout(']){
 const idx=sourceApp.indexOf(term);
 if(idx>=0)console.log('PROFILE CODE '+term+' '+sourceApp.slice(Math.max(0,idx-150),idx+2600));
}
const profileVariations=[
 {goal:'hypertrophy',days:2,duration:60,place:'gym',level:3},
 {goal:'strength',days:2,duration:30,place:'home',level:0},
 {goal:'fitness',days:5,duration:120,place:'gym',level:1},
 {goal:'fatloss',days:3,duration:45,place:'home',level:2}
];
const signatures=[];
for(const variation of profileVariations){
 const state=win.FitEngine.state();
 state.profile={...state.profile,...variation};
 state.active=null;
 state.planMemory=null;
 state.sessionIndex=0;
 win.Fit.go('ready');
 const btn=[...win.document.querySelectorAll('#app button')].find(b=>/운동 계획 만들기|운동 계획 생성/.test(b.textContent));
 assert(btn,'Missing plan generation button for '+JSON.stringify(variation));
 btn.click();
 const active=win.FitEngine.state().active;
 assert(active?.items?.length>0,'Profile '+JSON.stringify(variation)+' produced no routine');
 const sig=JSON.stringify({items:active.items.map(x=>({id:x.currentId||x.id,sets:x.sets?.map(z=>[z.targetReps,z.targetRIR,z.targetWeight])})),split:active.splitName,time:active.timeLimit});
 signatures.push(sig);
 console.log('PROFILE GENERATION:',JSON.stringify({variation,split:active.splitName,time:active.timeLimit,
   items:active.items.map(x=>({name:x.currentId||x.id,sets:x.sets?.length,reps:x.sets?.[0]?.targetReps}))}));
}
assert(new Set(signatures).size>=3,'Profile changes are not producing distinct exercise plans');
console.log('PASS profile variants generate distinct plans');


assert(!errors.some(x=>/FitPlan render error|Uncaught/i.test(x)),errors.join('\n'));
const css=fs.readFileSync(path.join(assets,'style.css'),'utf8');
assert(!css.includes('}\\n.fp-art'),'CSS contains escaped newline');
console.log('FitPlan DOM smoke passed');
dom.window.close();
