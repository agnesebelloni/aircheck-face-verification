import cv2
import dlib
import numpy as np
import torch
from PIL import Image


class DlibAligner:
    def __init__(self, predictor_path):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(str(predictor_path))

        self.ref_pts = np.float32([
            [30.2946, 51.6963],
            [65.5318, 51.5014],
            [48.0252, 71.7366],
            [33.5493, 92.3655],
            [62.7299, 92.2041]
        ])

    def preprocess_pil(self, img: Image.Image):
        rgb = np.asarray(img.convert("RGB"))

        dets = self.detector(rgb, 1)
        if len(dets) == 0:
            return None

        det = max(dets, key=lambda r: (r.right() - r.left()) * (r.bottom() - r.top()))
        shape = self.predictor(rgb, det)

        pts = np.array(
            [[shape.part(i).x, shape.part(i).y] for i in range(5)],
            dtype=np.float32
        )

        M, _ = cv2.estimateAffinePartial2D(pts, self.ref_pts, method=cv2.LMEDS)
        if M is None:
            return None

        aligned = cv2.warpAffine(rgb, M, (96, 112), borderValue=0)

        x = aligned.astype(np.float32)
        x = (x - 127.5) / 128.0
        x = np.transpose(x, (2, 0, 1))

        return torch.from_numpy(x)
