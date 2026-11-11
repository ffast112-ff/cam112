#!/usr/bin/env python3
"""Generate a readable, anti-aliased neon FitPlan launcher icon from vector primitives."""
from PIL import Image,ImageDraw,ImageFilter
from pathlib import Path
S=768
im=Image.new('RGBA',(S,S),(0,0,0,0))
pixels=im.load()
for y in range(S):
 for x in range(S):
  r=((x-S*.5)**2+(y-S*.5)**2)**.5/S
  t=max(0,min(1,(x+y)/(2*S)))
  pixels[x,y]=(int(8+7*t),int(19+11*t),int(25+9*t),255)
d=ImageDraw.Draw(im,'RGBA')
d.rounded_rectangle((15,15,753,753),radius=170,outline=(96,146,130,180),width=5)
d.rounded_rectangle((26,26,742,742),radius=165,outline=(35,75,60,180),width=3)
# Ambient green glow behind a bold centered barbell.
glow=Image.new('RGBA',(S,S),(0,0,0,0))
g=ImageDraw.Draw(glow,'RGBA')
g.ellipse((162,158,610,585),fill=(33,255,111,115))
glow=glow.filter(ImageFilter.GaussianBlur(85))
im=Image.alpha_composite(im,glow)
d=ImageDraw.Draw(im,'RGBA')
green=(63,251,112,255)
soft=(188,255,202,255)
# Single strongly legible equipment mark, symmetric and no confusing tiny lines.
d.rounded_rectangle((148,364,620,405),radius=21,fill=(207,255,219,255))
d.rounded_rectangle((121,287,185,481),radius=19,fill=green)
d.rounded_rectangle((194,248,274,519),radius=23,fill=green)
d.rounded_rectangle((494,248,574,519),radius=23,fill=green)
d.rounded_rectangle((583,287,647,481),radius=19,fill=green)
# Bright upper-left edge lighting and visible dark shadow.
for box in [(206,259,218,498),(506,259,518,498),(132,298,140,470),(594,298,602,470)]:
 d.rounded_rectangle(box,radius=5,fill=(212,255,214,165))
d.line((288,376,480,376),fill=(245,255,248,250),width=7)
# Small integrated upward growth indicator, subordinate to dumbbell.
for i,h in enumerate([29,47,65]):
 x=337+49*i
 d.rounded_rectangle((x,635-h,x+23,636),radius=8,fill=(63,251,112,215))
# Final resized antialias.
result=im.convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
folder=Path('fitplan/native/app/src/main/res/drawable')
folder.mkdir(parents=True,exist_ok=True)
result.save(folder/'fitplan_icon.png',optimize=True)
print('FitPlan polished original barbell launcher icon generated')
