# AirCheck

## Project Overview

AirCheck is an AI-based smart check-in system for short-term rental properties.

The system allows a guest to:

1. Upload an identity photo during booking.
2. Receive a unique QR code.
3. Scan the QR code at check-in.
4. Take a live selfie.
5. Verify identity through face recognition.
6. Obtain an access code if verification succeeds.

---

## Technologies

- Python
- Flask
- SphereFace
- Dlib
- PyTorch
- OpenCV
- HTML/CSS
- QR Codes

---

## Project Structure

```text
aircheck_webcam/
│
├── aircheck_server.py
├── evaluate_metrics.py
├── README.md
│
├── src/
│   ├── enroll.py
│   ├── verify.py
│   ├── preprocess.py
│   ├── sphereface_model.py
│   ├── net_sphere.py
│   └── config.py
│
├── templates/
├── static/
├── assets/
└── eval_data/

Pretrained Models

The pretrained models are not included in this repository due to size constraints.

Download them from:

sphere20a_20171020.pth
https://drive.google.com/file/d/1U9puXFjWQhZeEw1IWWIUrYf_0N9jTavB/view?usp=sharing

shape_predictor_5_face_landmarks.dat
https://drive.google.com/file/d/1r4ttm7g8YxyjM6b6t3V8N9ZeD66kcMwW/view?usp=sharing

After downloading, place both files inside the `assets/` directory before running the application.