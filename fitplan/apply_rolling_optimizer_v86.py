#!/usr/bin/env python3
"""Integrate V8.6 rolling quality optimizer after V8.5 fatigue removal.
The existing state schema is unchanged; only optional per-session metadata is added.
"""
from pathlib import Path
base=Path('fitplan/native/app/src/main/assets')
engine=base/'precision-engine-v86.js'
engine.write_bytes(Path('fitplan/precision-engine-v86.js').read_bytes())
html=base/'index.html';h=html.read_text('utf8')
old='<script src="precision-engine-v75.js"></script>'
assert old in h
h=h.replace(old,old+'<script src="precision-engine-v86.js"></script>',1)
assert h.index('precision-engine-v75.js')<h.index('precision-engine-v86.js')<h.index('app.js')
html.write_text(h,'utf8')
p=base/'app.js';s=p.read_text('utf8')
old='FitPlanPrecisionV75?.planDay(plannerInput)'
assert old in s
s=s.replace(old,'FitPlanPrecisionV86?.planDay(plannerInput)',1)
old='FitPlanPrecisionV75?.planProgram(programInput)'
assert old in s
s=s.replace(old,'FitPlanPrecisionV86?.planProgram(programInput)',1)
old='v75:result.v75,optimizer:'
assert old in s
s=s.replace(old,'v75:result.v75,v86:result.v86,optimizer:',1)
# Keep analysis compatible; all recorded set rows and calibration are unchanged.
s=s.replace('precision:()=>FitPlanPrecisionV75,','precision:()=>FitPlanPrecisionV86,',1)
p.write_text(s,'utf8')
print('V8.6 rolling-period optimizer integrated without state migration')
