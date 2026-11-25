# Jitter audit: reads a per-frame dump of rig-part positions ({"parts": {name: [[cx,cy,cz,tx,ty,tz],...]}, "cam": [[name,x,y,z,qw,qx,qy,qz],...]})
# (tools/soccer2/checks/soccer_demo.lua writes it; rows are Heartbeat frames, assumed 60 per second) and reports 1-frame POPS, direction REVERSALS and ABRUPT STOPS outside camera cuts.
# Gate: pops/stops should only appear on deliberate impact frames.
import json, math, collections, sys
d = json.load(open(sys.argv[1]))
cam = d["cam"]
cuts = {i for i in range(1, len(cam)) if cam[i][0] != cam[i-1][0]}
def sub(a,b): return [x-y for x,y in zip(a,b)]
def n(v): return math.sqrt(sum(x*x for x in v))
pops = []; revs = collections.Counter(); stops = []
for k, arr in d["parts"].items():
    P = [r[3:6] for r in arr]  # tip point
    V = [sub(P[i], P[i-1]) for i in range(1, len(P))]
    S = [n(v) for v in V]
    for i in range(2, len(S)-2):
        f = i+1
        if f in cuts or f-1 in cuts or f+1 in cuts: continue
        nb = sorted([S[i-2], S[i-1], S[i+1], S[i+2]])
        med = (nb[1]+nb[2])/2
        if S[i] > 0.05 and S[i] > 3.5*max(med, 0.01):
            pops.append((f, k, round(S[i],3), round(med,3)))
        # reversal: velocity flips direction at speed
        if S[i] > 0.02 and S[i-1] > 0.02:
            c = sum(a*b for a,b in zip(V[i], V[i-1]))/(S[i]*S[i-1])
            if c < -0.3: revs[(f//30)*30] += 1
        # abrupt stop (speed collapses >85% in one frame from fast)
        if S[i-1] > 0.12 and S[i] < 0.15*S[i-1]:
            stops.append((f, k, round(S[i-1],3)))
print("cuts at frames:", sorted(cuts))
print("\nSINGLE-FRAME POPS (speed spike vs neighbours):", len(pops))
byf = collections.defaultdict(list)
for f,k,s,m in pops: byf[f].append(f"{k}({s}/{m})")
for f in sorted(byf): print(f"  f{f} t={f/60:.2f}s:", ", ".join(byf[f][:6]), "..." if len(byf[f])>6 else "")
print("\nDIRECTION REVERSALS at speed, per 0.5 s window:")
for w in sorted(revs): print(f"  t={w/60:.1f}s: {revs[w]}")
print("\nABRUPT STOPS (fast->~0 in 1 frame):", len(stops))
bys = collections.defaultdict(list)
for f,k,s in stops: bys[f].append(k)
for f in sorted(bys): print(f"  f{f} t={f/60:.2f}s: {len(bys[f])} parts e.g. {bys[f][:3]}")
# camera jitter: angular velocity reversals
def qang(a,b):
    dot = abs(sum(x*y for x,y in zip(a,b))); return 2*math.degrees(math.acos(min(1,dot)))
cv=[]
for i in range(1,len(cam)):
    if i in cuts: cv.append(None); continue
    cv.append((n(sub(cam[i][1:4],cam[i-1][1:4])), qang(cam[i][4:],cam[i-1][4:])))
cr = collections.Counter()
for i in range(1,len(cv)-1):
    if None in (cv[i],cv[i-1],cv[i+1]): continue
    a,b,c = cv[i-1][1],cv[i][1],cv[i+1][1]
    if b > 0.4 and b > 2.5*max(a,c,0.05): cr[(i//30)*30]+=1
print("\nCAMERA rotation spikes per 0.5 s:", dict(sorted(cr.items())))
