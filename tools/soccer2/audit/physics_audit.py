# Physics audit on the same per-frame dump as jitter_audit.py (parts rows: cx,cy,cz, footx,footy,footz, lowest_z, fixed-point xyz):
# planted-foot SKATING, parts BELOW FLOOR, AIRBORNE arcs vs gravity, BALANCE (torso over feet), fastest root travel.
import json, math, collections, sys
d = json.load(open(sys.argv[1]))
P = d["parts"]; N = len(P["H:Torso"]); FPS = 60
cams = d["cam"]; cuts = {i for i in range(1,len(cams)) if cams[i][0]!=cams[i-1][0]}
# visible range for V starts ~698
def vis(tag, f): return tag=="H" or f>=700
print("== FOOT SLIDE (leg tip within 0.35 of floor, horizontal speed while 'planted')")
for tag in "HV":
    slide = collections.defaultdict(float); cnt = collections.Counter()
    for leg in ("Right Leg","Left Leg"):
        A = P[f"{tag}:{leg}"]
        for f in range(1,N):
            if not vis(tag,f) or f in cuts: continue
            z = A[f][6]
            if z < 0.25:
                hs = math.hypot(A[f][3]-A[f-1][3], A[f][4]-A[f-1][4])*FPS
                slide[f//60]+=hs; cnt[f//60]+=1
    for s in sorted(slide):
        avg = slide[s]/cnt[s]
        if avg > 1.0: print(f"  {tag} t={s}s avg planted-foot slide {avg:.1f} studs/s over {cnt[s]} foot-frames")
print("== SKATING: per frame, the SLOWER of the two grounded feet (that one should be planted, ~0 st/s)")
for tag in "HV":
    R=P[f"{tag}:Right Leg"]; L=P[f"{tag}:Left Leg"]; acc=collections.defaultdict(list)
    for f in range(1,N):
        if not vis(tag,f) or f in cuts: continue
        sp=[]
        for A in (R,L):
            if A[f][6] < 0.12: sp.append(math.hypot(A[f][3]-A[f-1][3],A[f][4]-A[f-1][4])*FPS)
        if sp: acc[f//60].append(min(sp))
    for s_ in sorted(acc):
        m=sum(acc[s_])/len(acc[s_])
        if m>0.4: print(f"  {tag} t={s_}s planted foot skates {m:.2f} st/s ({len(acc[s_])} frames)")
print("== BELOW FLOOR (any part tip z < -0.15)")
for k,A in P.items():
    tag=k[0]; bad=[f for f in range(N) if vis(tag,f) and A[f][6] < -0.3]
    if bad: print(f"  {k}: {len(bad)} frames, t={bad[0]/60:.2f}-{bad[-1]/60:.2f}s, min z {min(A[f][6] for f in bad):.2f}")
print("== AIRBORNE ARCS (both feet > 0.6 above floor): vertical accel of torso vs gravity")
for tag in "HV":
    T = P[f"{tag}:Torso"]; R=P[f"{tag}:Right Leg"]; L=P[f"{tag}:Left Leg"]
    air = [f for f in range(N) if vis(tag,f) and R[f][6]>0.5 and L[f][6]>0.5]
    # group
    segs=[]; 
    for f in air:
        if segs and f==segs[-1][-1]+1: segs[-1].append(f)
        else: segs.append([f])
    for sg in segs:
        if len(sg)<8: continue
        z=[T[f][2] for f in sg]
        acc=[(z[i+1]-2*z[i]+z[i-1])*FPS*FPS for i in range(1,len(z)-1)]
        vz=[(z[i+1]-z[i])*FPS for i in range(len(z)-1)]
        print(f"  {tag} {sg[0]/60:.2f}-{sg[-1]/60:.2f}s ({len(sg)}f): z {min(z):.1f}..{max(z):.1f}, vz {min(vz):.1f}..{max(vz):.1f} st/s, accel median {sorted(acc)[len(acc)//2]:.0f}, min {min(acc):.0f} max {max(acc):.0f} st/s2")
print("== BALANCE: grounded frames where torso center is outside the feet support (horiz dist from feet midpoint > 1.6)")
for tag in "HV":
    T=P[f"{tag}:Torso"]; R=P[f"{tag}:Right Leg"]; L=P[f"{tag}:Left Leg"]; bad=collections.Counter()
    for f in range(N):
        if not vis(tag,f): continue
        if min(R[f][6],L[f][6])<0.3:
            mx=(R[f][3]+L[f][3])/2; my=(R[f][4]+L[f][4])/2
            if math.hypot(T[f][0]-mx,T[f][1]-my)>1.6: bad[f//30]+=1
    for w in sorted(bad): print(f"  {tag} t={w/2:.1f}s: {bad[w]} frames off-balance")
print("== SPEED PROFILE of root travel (horizontal), peaks")
for tag in "HV":
    T=P[f"{tag}:Torso"]; sp=[math.hypot(T[f][0]-T[f-1][0],T[f][1]-T[f-1][1])*FPS if f not in cuts and vis(tag,f) and vis(tag,f-1) else 0 for f in range(1,N)]
    top=sorted(range(len(sp)),key=lambda i:-sp[i])[:6]
    print(f"  {tag} fastest: "+", ".join(f"{(i+1)/60:.2f}s {sp[i]:.0f}st/s" for i in sorted(top)))
