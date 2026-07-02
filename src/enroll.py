import numpy as np
from PIL import Image

from .config import ENROLL_DIR, SPHEREFACE_WEIGHTS, DLIB_5_LANDMARKS
from .sphereface_model import SphereFaceEmbedder
from .preprocess import DlibAligner


def enroll(user_id, image_paths):
    #initialize the face embedding model (SphereFace) and the face alignment module (Dlib)
    embedder = SphereFaceEmbedder(SPHEREFACE_WEIGHTS)
    aligner = DlibAligner(DLIB_5_LANDMARKS)

    embeddings = []
    #list used to store facial embeddings extracted from the enrollment identity photos

    for path in image_paths:
        img = Image.open(path).convert("RGB")
        face = aligner.preprocess_pil(img) #detect and align the face before feature extraction

        if face is None:
            continue

        emb = embedder.embed(face).float() #extract the facial embedding representing the identity
        emb = emb / (emb.norm() + 1e-12) #normalize the embedding to improve cosine similarity comparison
        embeddings.append(emb.numpy())

    if len(embeddings) == 0: #enrollment fails if no valid face was detected
        raise ValueError("No faces detected during enrollment.")

    #create the biometric template by averaging the embeddings
    template = np.mean(np.stack(embeddings, axis=0), axis=0)
    template = template / (np.linalg.norm(template) + 1e-12) #normalize final template

    #store the biometric template associated with the booking/user ID
    out = ENROLL_DIR / f"{user_id}.npz"
    np.savez_compressed(out, template=template)

    return out
