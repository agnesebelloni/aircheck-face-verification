from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"
ENROLL_DIR = DATA_DIR / "enrollments"

ENROLL_DIR.mkdir(parents=True, exist_ok=True)

SPHEREFACE_WEIGHTS = ASSETS_DIR / "sphere20a_20171020.pth"
DLIB_5_LANDMARKS = ASSETS_DIR / "shape_predictor_5_face_landmarks.dat"

DEFAULT_THRESHOLD = 0.52
