#!/usr/bin/env python3
"""Original synthesized two-stage radio-clock-like signals; no third-party recordings."""
from pathlib import Path
import wave,math,struct
dest=Path('fitplan/native/app/src/main/res/raw')
dest.mkdir(parents=True,exist_ok=True)
SAMPLE_RATE=22050
def synth(name,events):
 duration=max(t+d for t,d,frequency,amp in events)+.08
 count=math.ceil(duration*SAMPLE_RATE)
 buf=[0.0]*count
 for start,duration,freq,volume in events:
  onset=int(start*SAMPLE_RATE)
  length=int(duration*SAMPLE_RATE)
  for k in range(length):
   t=k/SAMPLE_RATE
   fade=min(1,t/.014,(duration-t)/.042)
   if fade<=0:continue
   ix=onset+k
   buf[ix]+=volume*fade*(.83*math.sin(2*math.pi*freq*t)+.17*math.sin(2*math.pi*2*freq*t))
 pcm=b''.join(struct.pack('<h',max(-32767,min(32767,int(x*32700)))) for x in buf)
 with wave.open(str(dest/(name+'.wav')),'wb') as out:
  out.setnchannels(1);out.setsampwidth(2);out.setframerate(SAMPLE_RATE);out.writeframes(pcm)
synth('fitplan_pretone',[(0,.10,880,.14)])
synth('fitplan_endtone',[(0,.12,880,.24),(.20,.12,880,.24),(.40,.12,880,.24),(.60,.68,660,.35)])
print('Original FitPlan countdown + completion WAV assets generated')
