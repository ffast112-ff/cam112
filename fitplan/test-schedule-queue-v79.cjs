const assert=require('node:assert/strict');
const Q=require('./schedule-queue-v79.js');
const baseDates=['2026-11-16','2026-11-18','2026-11-20','2026-11-23','2026-11-25','2026-11-27'];
const baseSlots=baseDates.map((date,i)=>({date,sessionIndex:i,dayName:['전신 A','전신 B','전신 C'][i%3]}));
const splits=['전신 A','전신 B','전신 C'];
const m=a=>Array.from(a,([d,slot])=>[d,slot.dayName]);
const opts={baseSlots,splitNames:splits,today:'2026-11-17',completedDates:['2026-11-16'],sessionIndex:1};
const normal=Q.assign(opts);
assert.deepEqual(m(normal),[
  ['2026-11-18','전신 B'],['2026-11-20','전신 C'],['2026-11-23','전신 A'],
  ['2026-11-25','전신 B'],['2026-11-27','전신 C']
]);
// 1st week Wednesday missed -> Friday must be B, next Monday C, not C/A.
const missed=Q.assign({...opts,overrides:{'2026-11-18':'rest'}});
assert.deepEqual(m(missed),[
  ['2026-11-20','전신 B'],['2026-11-23','전신 C'],
  ['2026-11-25','전신 A'],['2026-11-27','전신 B']
]);
// After Wednesday is marked rest, Thursday added -> Thursday B, Friday C, Monday A.
const inserted=Q.assign({...opts,overrides:{'2026-11-18':'rest','2026-11-19':'planned'}});
assert.deepEqual(m(inserted),[
  ['2026-11-19','전신 B'],['2026-11-20','전신 C'],['2026-11-23','전신 A'],
  ['2026-11-25','전신 B'],['2026-11-27','전신 C']
]);
// Actually completing Thursday consumes B, and it is immutable thereafter.
const doneThursday=Q.assign({...opts,today:'2026-11-20',sessionIndex:2,
  completedDates:['2026-11-16','2026-11-19'],
  overrides:{'2026-11-18':'rest','2026-11-19':'planned'}});
assert.equal(doneThursday.get('2026-11-20').dayName,'전신 C');
assert.equal(doneThursday.get('2026-11-23').dayName,'전신 A');
assert.equal(doneThursday.has('2026-11-19'),false);
// Override a calendar slot, add a different date, then revert to automatic.
const reverted=Q.assign({...opts,overrides:{'2026-11-18':'rest','2026-11-19':'auto'}});
assert.equal(reverted.get('2026-11-20').dayName,'전신 B');
assert.equal(reverted.has('2026-11-19'),false);
assert.equal(Q.assign({...opts,overrides:{'2026-11-16':'planned'}}).has('2026-11-16'),false);
assert.deepEqual(m(Q.assign({...opts,baseSlots:[]})),[]);
console.log('PASS sequence queue: missed / inserted / completed / restored dates preserve A→B→C');
