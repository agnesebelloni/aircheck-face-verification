from pathlib import Path
import time #to measure how long each verification takes
import numpy as np

from src.enroll import enroll
from src.verify import verify

#final decision threshold used by AirCheck
#if cosine similarity >= 0.52, the identity is accepted
#this threshold was selected after calibration
THRESHOLD = 0.52
USER_ID = "eval_guest" #identifier used for the enrolled identity during evaluation

GUEST_DIR = Path("eval_data/guest")
IMPOSTOR_DIR = Path("eval_data/impostors")

VALID_EXT = {".jpg", ".jpeg", ".png"}

def image_files(folder): 
#utility function to collect valid image files from a folder
    return sorted([
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in VALID_EXT
    ])

guest_images = image_files(GUEST_DIR) #load all valid guest images
impostor_images = image_files(IMPOSTOR_DIR) #load all valid impostors images

print("Guest images:", len(guest_images))
print("Impostor images:", len(impostor_images))

#at least two guest images are required: one for enrollment and one for genuine testing
if len(guest_images) < 2:
    raise ValueError("Need at least 2 guest images.")

if len(impostor_images) < 1:
    raise ValueError("Need at least 1 impostor image.")

#first guest image = enrollment / identity photo
enrollment_image = guest_images[0]
genuine_tests = guest_images[1:]

print("\nEnrollment image:")
print(" -", enrollment_image)

print("\nCreating enrollment template...")
enroll(USER_ID, [enrollment_image]) #face detection -> face alignment -> SphereFace embedding -> template storage

results = []

#genuine attempts: same person
for img in genuine_tests:
    start = time.time()
    res = verify(USER_ID, img, threshold=THRESHOLD)
    elapsed = time.time() - start

    results.append({
        "image": img.name,
        "true_label": 1,
        "type": "genuine",
        "accepted": bool(res["accepted"]),
        "score": res["score"],
        "reason": res["reason"],
        "time": elapsed
    })

# Impostor attempts: different people
for img in impostor_images:
    start = time.time()
    res = verify(USER_ID, img, threshold=THRESHOLD)
    elapsed = time.time() - start

    results.append({
        "image": img.name,
        "true_label": 0,
        "type": "impostor",
        "accepted": bool(res["accepted"]),
        "score": res["score"],
        "reason": res["reason"],
        "time": elapsed
    })



#convert true labels into a NumPy array
#y_true = 1 means genuine user
#y_true = 0 means impostor
y_true = np.array([r["true_label"] for r in results])


#convert system decisions into predictions
#y_pred = 1 means accepted
#y_pred = 0 means rejected
y_pred = np.array([1 if r["accepted"] else 0 for r in results])

#compute confusion matrix components
TP = int(((y_true == 1) & (y_pred == 1)).sum())
FN = int(((y_true == 1) & (y_pred == 0)).sum())
FP = int(((y_true == 0) & (y_pred == 1)).sum())
TN = int(((y_true == 0) & (y_pred == 0)).sum())

#evaluation metrics
accuracy = (TP + TN) / len(results)
far = FP / (FP + TN) if (FP + TN) > 0 else 0.0
frr = FN / (TP + FN) if (TP + FN) > 0 else 0.0
avg_time = float(np.mean([r["time"] for r in results]))

genuine_scores = [r["score"] for r in results if r["type"] == "genuine" and r["score"] is not None]
impostor_scores = [r["score"] for r in results if r["type"] == "impostor" and r["score"] is not None]

#print final results
print("\n================ AirCheck Evaluation ================")
print(f"Threshold: {THRESHOLD}")
print(f"Enrollment image: {enrollment_image.name}")
print(f"Total test attempts: {len(results)}")
print(f"Genuine attempts: {len(genuine_tests)}")
print(f"Impostor attempts: {len(impostor_images)}")
print("-----------------------------------------------------")
print(f"Accuracy: {accuracy:.3f}")
print(f"FAR (False Accept Rate): {far:.3f}")
print(f"FRR (False Reject Rate): {frr:.3f}")
print(f"Average verification time: {avg_time:.3f} s")

if genuine_scores:
    print(f"Mean genuine score: {np.mean(genuine_scores):.3f}")
if impostor_scores:
    print(f"Mean impostor score: {np.mean(impostor_scores):.3f}")

print("\nConfusion Matrix")
print("                 Pred Accepted   Pred Rejected")
print(f"True Guest       {TP:13d}   {FN:13d}")
print(f"Impostor         {FP:13d}   {TN:13d}")

print("\nDetailed scores")
for r in results:
    score_str = "None" if r["score"] is None else f"{r['score']:.3f}"
    decision = "ACCEPT" if r["accepted"] else "REJECT"
    print(f"{r['type']:8s} | {r['image']:30s} | score={score_str:>6s} | {decision:6s} | reason={r['reason']} | time={r['time']:.3f}s")

print("\n=====================================================")
