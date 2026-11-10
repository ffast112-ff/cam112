"""Precision V6: exercise-wide first-load and skill-specific calibration.
External statistics are population 1RM references, not individual prescriptions.
Only manually verified 95/100 kg male anchors are used as numerical benchmarks.
Unverified or mismatched variants are NOT silently converted.
"""
from pathlib import Path
p=Path('fitplan/native/app/src/main/assets/precision-engine-v5.js')
s=p.read_text(encoding='utf8')
marker=" return {VERSION,calKey,usesLoad,standardOneRM,startingLoad,calibrationStatus,begin,evaluateTrial,"
assert marker in s, 'V5 API marker changed'
addition=r"""
 // V6 catalog for the COMPLETE 31-exercise inventory; one explicit policy per ID.
 // Male anchors [Beginner,Novice,Intermediate,Advanced] at bodyweights 95,100kg.
 // Source: individual Strength Level standards (checked 2026-11-11).
 // The numeric entries below are strictly limited to sources verified directly.
 const CATALOG_V6={
  leg_press:{category:'direct',unit:'plates_total',url:'https://strengthlevel.com/strength-standards/sled-leg-press/kg',male:{95:[135,194,268,353],100:[144,205,280,366]}},
  goblet_squat:{category:'direct',unit:'one_dumbbell',url:'https://strengthlevel.com/strength-standards/goblet-squat/kg',male:{95:[18,30,46,65],100:[19,31,47,66]}},
  body_squat:{category:'reps',unit:'repetitions',url:'https://strengthlevel.com/strength-standards/bodyweight-squat'},
  split_squat:{category:'conditional',unit:'repetitions',reason:'현재 앱의 맨몸 스플릿 스쿼트는 덤벨 스플릿 스쿼트 통계를 환산할 수 없습니다.'},
  chest_press:{category:'direct',unit:'machine_stack',url:'https://strengthlevel.com/strength-standards/chest-press/kg'},
  db_press:{category:'direct',unit:'one_dumbbell',url:'https://strengthlevel.com/strength-standards/dumbbell-bench-press/kg',male:{95:[24,34,46,61],100:[25,36,48,63]}},
  bench_press:{category:'direct',unit:'barbell_includes_bar',url:'https://strengthlevel.com/strength-standards/bench-press/kg',male:{95:[69,90,115,143],100:[73,95,120,149]}},
  pushup:{category:'reps',unit:'repetitions',url:'https://strengthlevel.com/strength-standards/push-ups'},
  cable_fly:{category:'direct',unit:'cable_stack',url:'https://strengthlevel.com/strength-standards/cable-fly'},
  lat_pulldown:{category:'direct',unit:'machine_stack',url:'https://strengthlevel.com/strength-standards/lat-pulldown/kg'},
  assisted_pullup:{category:'conditional',unit:'assistance_kg',reason:'어시스트 머신은 숫자가 클수록 쉬워짐. 일반 풀업 1RM 통계로 역산 금지.'},
  pullup:{category:'reps',unit:'repetitions',url:'https://strengthlevel.com/strength-standards/pull-ups'},
  seated_row:{category:'direct',unit:'machine_stack',url:'https://strengthlevel.com/strength-standards/seated-cable-row/kg',reason:'시티드 로우 머신과 케이블 로우가 다르면 직접 환산하지 않음.'},
  db_row:{category:'direct',unit:'one_dumbbell',url:'https://strengthlevel.com/strength-standards/dumbbell-row/kg',male:{95:[24,36,51,68],100:[26,38,53,70]}},
  band_row:{category:'reps',unit:'band_grade',reason:'밴드별 장력·신장률이 달라 kg 표를 사용하지 않음.'},
  rld_machine:{category:'conditional',unit:'machine_stack',url:'https://strengthlevel.com/strength-standards/seated-leg-curl',reason:'레그컬은 앉은형/누운형을 구분하고 같은 기구 기록 우선.'},
  db_rdl:{category:'direct',unit:'one_dumbbell',url:'https://strengthlevel.com/strength-standards/dumbbell-romanian-deadlift/kg'},
  glute_bridge:{category:'reps',unit:'repetitions',url:'https://strengthlevel.com/strength-standards/glute-bridge'},
  hip_thrust:{category:'conditional',unit:'machine_stack',url:'https://strengthlevel.com/strength-standards/hip-thrust',reason:'바벨 힙 쓰러스트 통계를 힙 쓰러스트 머신의 kg로 변환 금지.'},
  shoulder_press:{category:'direct',unit:'machine_stack',url:'https://strengthlevel.com/strength-standards/machine-shoulder-press',reason:'바벨 오버헤드 프레스와 구분해야 함.'},
  db_shoulder:{category:'direct',unit:'one_dumbbell',url:'https://strengthlevel.com/strength-standards/dumbbell-shoulder-press/kg'},
  lateral_raise:{category:'direct',unit:'one_dumbbell',url:'https://strengthlevel.com/strength-standards/dumbbell-lateral-raise/kg'},
  face_pull:{category:'direct',unit:'cable_stack',url:'https://strengthlevel.com/strength-standards/face-pull'},
  triceps_push:{category:'direct',unit:'cable_stack',url:'https://strengthlevel.com/strength-standards/tricep-pushdown/kg'},
  triceps_db:{category:'direct',unit:'one_dumbbell',url:'https://strengthlevel.com/strength-standards/dumbbell-tricep-kickback'},
  biceps_curl:{category:'direct',unit:'one_dumbbell',url:'https://strengthlevel.com/strength-standards/dumbbell-curl/kg',male:{95:[10,16,25,35],100:[11,17,26,36]}},
  cable_curl:{category:'direct',unit:'cable_stack',url:'https://strengthlevel.com/strength-standards/cable-bicep-curl'},
  calf_raise:{category:'conditional',unit:'body_reps',reason:'현재 앱은 맨몸 스탠딩 카프레이즈. 머신 카프레이즈 kg 기준 사용 금지.'},
  plank:{category:'time',unit:'seconds',url:'https://strengthlevel.com/strength-standards/plank'},
  dead_bug:{category:'reps',unit:'repetitions',reason:'좌우 반복과 자세 유지로 평가; 1RM 없음.'},
  walking:{category:'cardio',unit:'minutes_speed_incline',reason:'시간·속도·경사·자각강도로 평가; kg 1RM 없음.'}
 };
 const originalStartingLoad=startingLoad;
 startingLoad=function(profile,e,increment,minimum){
   const d=CATALOG_V6[e&&e.id];
   if(!d)throw Error('Unknown exercise in V6 catalog: '+(e&&e.id));
   if(!usesLoad(e)||d.category==='reps'||d.category==='time'||d.category==='cardio'){
     return {...originalStartingLoad(profile,e,increment,minimum),category:d.category,unit:d.unit,
       benchmarkUrl:d.url||null,source:'non-load-assessment',
       note:d.reason||'이 종목은 체중·반복횟수·유지시간·난이도를 기준으로 평가합니다. 임의의 kg 1RM을 제시하지 않습니다.'};
   }
   const fallback=originalStartingLoad(profile,e,increment,minimum);
   const step=clamp(N(increment,e.gear==='dumbbell'?1:2.5),.25,25);
   const floor=Math.max(step,N(minimum,step));
   const bw=N(profile?.weight,NaN),lv=clamp(N(profile?.level,0),0,3);
   // A population standard is eligible only when the same movement, load unit,
   // sex AND supported bodyweight data are available.
   const anchors=d.male&&profile?.sex==='male'&&bw>=95&&bw<=100?d.male:null;
   if(anchors){
     const oneRM=anchors[95][lv]+(anchors[100][lv]-anchors[95][lv])*(bw-95)/5;
     // A first *exploration* set, rather than 8RM. First-time technical familiarity
     // is unknown; novice/intermediate statistical rankings do not prove proficiency.
     const factor=lv===0?.40:lv===1?.42:.38;
     let trial=oneRM*factor;
     if(e.id==='leg_press')trial=Math.min(trial,80); // Unfamiliar sled: start around 50–80kg ADDED plates, not a fixed 20kg.
     if(e.kind==='isolation')trial=Math.min(trial,oneRM*.40);
     const rounded=Math.max(floor,Math.floor(trial/step)*step);
     const isSled=e.id==='leg_press';
     return {...fallback,weight:rounded,source:'verified-population-1rm-trial',
       category:d.category,unit:d.unit,benchmark1RM:oneRM,benchmarkUrl:d.url,confidence:'low',
       note:(isSled?'45도 원판형: 표시 중량은 양쪽에 추가한 원판 합계이고, 썰매 자체 저항은 별도입니다. 빈 썰매를 안전하게 확인하세요. ':'')+
       '공개된 성별·체중별 1RM 통계를 바탕으로 산출한 첫 탐색 후보 '+rounded+'kg입니다. 숙련도 통계는 실제 첫 사용 능력을 보장하지 않습니다. 가벼운 준비 세트 후 RIR·자세·통증으로 보정하세요.'};
   }
   // Existing V5 verified numeric standard (lat, chest and seated row) retains its
   // matching-source logic. Machine variation always makes it low confidence.
   if(fallback.source==='strength-level'){
     return {...fallback,category:d.category,unit:d.unit,confidence:'low',
       note:fallback.note+' 개인 운동 기록이 생기면 통계보다 그 기록을 우선합니다.'};
   }
   // Source link exists, but NO validated numeric table for this exact load variant.
   // Deliberately do not fabricate a strength standard or proxy another exercise.
   return {...fallback,category:d.category,unit:d.unit,confidence:'very-low',
     source:d.category==='conditional'?'variant-specific-calibration':'catalog-link-without-numeric-anchor',
     benchmarkUrl:d.url||null,
     note:(d.reason?d.reason+' ':'')+
       '종목별 공개 통계를 참고할 수 있지만 현재 사용자 조건에 검증된 수치표가 없어 기존의 낮은 신뢰도 탐색 후보를 사용합니다. 목표 중량이 아니라 첫 시험 후보입니다. 개인 기록·기구 표시 단위·실제 RIR을 우선하세요.'};
 };
"""
s=s.replace(marker,addition+'\n'+marker,1)
s=s.replace("return {VERSION,calKey,usesLoad,standardOneRM,startingLoad,calibrationStatus,begin,evaluateTrial,",
            "return {VERSION,calKey,usesLoad,standardOneRM,startingLoad,CATALOG_V6,calibrationStatus,begin,evaluateTrial,",1)
p.write_text(s,encoding='utf8')
print('V6 catalog mapped',31,'exercises; sourced numeric anchors only when verified')
