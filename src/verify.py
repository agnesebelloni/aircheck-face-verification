import numpy as np
import torch
from PIL import Image

from .config import ENROLL_DIR, DEFAULT_THRESHOLD, SPHEREFACE_WEIGHTS, DLIB_5_LANDMARKS
from .sphereface_model import SphereFaceEmbedder
from .preprocess import DlibAligner


def _cosine(a, b): #compute cosine similarity between two face embeddings
    a = a / (a.norm() + 1e-12)
    b = b / (b.norm() + 1e-12)
    return float(torch.dot(a, b))


def verify(user_id, image_path, threshold=DEFAULT_THRESHOLD):
    #load the biometric template associated with the enrolled guest
    template_path = ENROLL_DIR / f"{user_id}.npz"

    #verification cannot be performed if no enrollment exists
    if not template_path.exists():
        return {
            "accepted": False,
            "reason": "no_template",
            "score": None,
            "threshold": threshold
        }

    #load the enrolled biometric template
    template = torch.from_numpy(np.load(template_path)["template"]).float()
    
    #initialize face embedding extraction and face alignment modules
    embedder = SphereFaceEmbedder(SPHEREFACE_WEIGHTS)
    aligner = DlibAligner(DLIB_5_LANDMARKS)

    #load the selfie captured during the check-in process
    img = Image.open(image_path).convert("RGB")

    #detect and align the face before verification
    face = aligner.preprocess_pil(img)

    if face is None: #verification fails if no face is detected
        return {
            "accepted": False,
            "reason": "no_face",
            "score": None,
            "threshold": threshold
        }
    
    #extract the embedding from the live selfie
    emb = embedder.embed(face).float()

    #compare the live selfie with the enrolled template
    score = _cosine(emb, template)

    #final decision: accept if similarity exceeds the calibrated threshold
    return {
        "accepted": score >= threshold,
        "reason": "ok",
        "score": score,
        "threshold": threshold
    }
