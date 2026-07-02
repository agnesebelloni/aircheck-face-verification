
#Flask tools:
#Flask: creates the web application
#request: reads form data, uploaded files, and JSON data
#jsonify: sends JSON responses to the frontend
#render_template_string: renders HTML stored as Python strings
#redirect/url_for: redirects the user after actions such as booking creation

from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from pathlib import Path
from PIL import Image
import base64 #used to decode webcam images sent as base64 string
import io #used to handle image data in memory
import secrets #uised to generate secure random booking tokens
import qrcode #used to generate QR codes for the check-in link

#enroll() creates the biometric template from the identity photo
#verify() compares the live selfie with the stored template
from src.enroll import enroll
from src.verify import verify

app = Flask(__name__) #initializes the Flask application
#creates an in-memory structure used to store booking information

BOOKINGS = {}



#HTML page shown to the host
#it contains: the booking form, identity photo upload, QR code display after booking creation
HOME_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>AirCheck</title>
<style>
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f6f7fb;
}
.container {
    max-width: 1100px;
    margin: 35px auto;
    background: white;
    padding: 35px;
    border-radius: 24px;
    box-shadow: 0 12px 35px rgba(0,0,0,0.10);
}
h1 {
    color: #ff385c;
    font-size: 46px;
    margin-bottom: 0;
}
.subtitle {
    color: #555;
    margin-top: 5px;
    font-size: 18px;
}
.grid {
    display: grid;
    grid-template-columns: 1.1fr 0.9fr;
    gap: 28px;
}
.card {
    margin-top: 25px;
    padding: 25px;
    border-radius: 18px;
    border: 1px solid #eee;
}
input, button {
    width: 100%;
    padding: 13px;
    margin: 8px 0;
    border-radius: 12px;
    border: 1px solid #ccc;
    font-size: 16px;
    box-sizing: border-box;
}
input[type="file"] {
    background: #fafafa;
}
button {
    background: #ff385c;
    color: white;
    border: none;
    font-weight: bold;
    cursor: pointer;
}
button:hover {
    background: #e03150;
}
.success {
    background: #eafff1;
    border: 1px solid #b7efc5;
}
.qr {
    text-align: center;
}
.badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: #ffe8ee;
    color: #ff385c;
    font-weight: bold;
    font-size: 13px;
}
.note {
    color: #666;
    font-size: 14px;
}
@media (max-width: 850px) {
    .grid {
        grid-template-columns: 1fr;
    }
}
</style>
</head>

<body>
<div class="container">
    <span class="badge">Smart short-rental access</span>
    <h1>AirCheck</h1>
    <p class="subtitle">AI-based smart check-in for short-term rentals</p>

    <div class="grid">
        <div class="card">
            <h2>1. Simulated Airbnb booking</h2>
            <p>Register the guest and upload an initial identity photo. This image is used to create the face template for later check-in verification.</p>

            <form method="POST" action="/create_booking" enctype="multipart/form-data">
                <input name="guest_name" placeholder="Guest name" required>
                <input name="property_name" placeholder="Property name" value="Milan Smart Apartment" required>
                <input name="checkin_date" type="date" required>

                <h3>Identity photo</h3>
                <input type="file" name="identity_photo" accept="image/*" required>
                <p class="note">Upload a clear frontal photo of the guest. The system stores only the biometric template.</p>

                <button type="submit">Create booking and generate QR code</button>
            </form>
        </div>

        {% if has_booking %}
        <div class="card success">
            <h2>2. Booking created</h2>
            <p><b>Booking ID:</b> {{ booking_id }}</p>
            <p><b>Guest:</b> {{ guest_name }}</p>
            <p><b>Property:</b> {{ property_name }}</p>
            <p><b>Check-in date:</b> {{ checkin_date }}</p>

            <div class="qr">
                <h3>Scan this QR code to check in</h3>
                <img src="data:image/png;base64,{{ qr_code }}" width="270">
                <p class="note">The guest scans this QR code from the phone at arrival.</p>
            </div>
        </div>
        {% else %}
        <div class="card">
            <h2>Workflow</h2>
            <p><b>Step 1:</b> Host creates booking and uploads identity photo.</p>
            <p><b>Step 2:</b> System generates a QR code for the booking.</p>
            <p><b>Step 3:</b> Guest scans QR at check-in.</p>
            <p><b>Step 4:</b> Guest takes live selfie.</p>
            <p><b>Step 5:</b> System verifies identity and returns access code.</p>
        </div>
        {% endif %}
    </div>
</div>
</body>
</html>
"""

#HTML page shown to the guest after scanning the QR code
#this page: opens the smartphone camera, captures a live selfie, sends it to the backend API for verification, displays Access Granted / Access Denied
CHECKIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>AirCheck Check-in</title>
<style>
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f6f7fb;
}
.container {
    max-width: 760px;
    margin: 35px auto;
    background: white;
    padding: 32px;
    border-radius: 24px;
    box-shadow: 0 12px 35px rgba(0,0,0,0.10);
    text-align: center;
}
h1 {
    color: #ff385c;
}
button {
    padding: 14px 22px;
    margin: 8px;
    border-radius: 12px;
    border: none;
    background: #ff385c;
    color: white;
    font-weight: bold;
    cursor: pointer;
}
button:hover {
    background: #e03150;
}
video {
    width: 100%;
    max-width: 420px;
    border-radius: 18px;
    border: 2px solid #eee;
}
.info {
    background: #fafafa;
    padding: 15px;
    border-radius: 14px;
    margin: 15px 0;
}
.result {
    margin-top: 25px;
    padding: 22px;
    border-radius: 16px;
    font-size: 18px;
}
.granted {
    background: #eafff1;
    color: #087a32;
}
.denied {
    background: #ffecec;
    color: #a40000;
}
.code {
    font-size: 38px;
    font-weight: bold;
    letter-spacing: 6px;
    background: white;
    color: #087a32;
    padding: 12px;
    border-radius: 12px;
    display: inline-block;
    margin-top: 8px;
}
</style>
</head>

<body>
<div class="container">
    <h1>AirCheck Check-in</h1>

    <div class="info">
        <p><b>Booking ID:</b> {{ booking_id }}</p>
        <p><b>Guest:</b> {{ guest_name }}</p>
        <p><b>Property:</b> {{ property_name }}</p>
    </div>

    <p>Take a live selfie to verify your identity and complete the check-in.</p>

    <button onclick="startCamera()">Start camera</button>
    <button onclick="captureCheckin()">Take check-in selfie</button>

    <br><br>

    <video id="video" autoplay playsinline></video>
    <canvas id="canvas" width="420" height="315" style="display:none;"></canvas>

    <div id="result"></div>
</div>

<script>
async function startCamera() {
    const video = document.getElementById("video");
    const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" },
        audio: false
    });
    video.srcObject = stream;
}

async function captureCheckin() {
    const video = document.getElementById("video");
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");
    const resultBox = document.getElementById("result");

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const image = canvas.toDataURL("image/jpeg", 0.92);

    resultBox.innerHTML = "<p>Verifying identity...</p>";

    const response = await fetch("/api/verify/{{ token }}", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({image: image})
    });

    const data = await response.json();

    if (data.accepted) {
        resultBox.innerHTML = `
        <div class="result granted">
            <h2>✅ Check-in completed successfully</h2>
            <p>Identity verified.</p>
            <p>Your keybox / door code is:</p>
            <div class="code">4931</div>
        </div>`;
    } else {
        resultBox.innerHTML = `
        <div class="result denied">
            <h2>❌ Check-in failed</h2>
            <p>Identity verification did not succeed.</p>
            <p>Reason: ${data.reason}</p>
            <p>Please contact the host.</p>
        </div>`;
    }
}
</script>
</body>
</html>
"""

#converts a base64 image sent by JavaScript into a PIL image
def dataurl_to_image(data_url):
    _, encoded = data_url.split(",", 1)
    img_bytes = base64.b64decode(encoded)
    return Image.open(io.BytesIO(img_bytes)).convert("RGB")


#creates a QR code from a URL and returns it as a base64 PNG
def make_qr_base64(url):
    qr = qrcode.make(url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

#shows the booking form
#if a booking was just created, it also shows the generated QR code
@app.route("/")
def home():
    last = getattr(app, "last_booking", None)

    if last:
        return render_template_string(HOME_PAGE, has_booking=True, **last)

    return render_template_string(HOME_PAGE, has_booking=False)



#route used by the host to create a new booking
#it receives: guest name, property name, check-in date, identity photo
@app.post("/create_booking") 
def create_booking():
    guest_name = request.form["guest_name"]
    property_name = request.form["property_name"]
    checkin_date = request.form["checkin_date"]

    identity_file = request.files["identity_photo"] #read the uploaded identity photo

    token = secrets.token_urlsafe(10) #generate a secure random token used inside the QR link
    booking_id = f"BK_{token[:6]}" #create a readable booking ID

    initial_path = Path("/tmp") / f"identity_{booking_id}.jpg"
    identity_file.save(initial_path)

    #enrollment phase: the identity photo is converted into a biometric template
    #using face detection, alignment, SphereFace embedding extraction.
    try:
        enroll(booking_id, [initial_path])
    except Exception as e:
        return f"Enrollment failed: {e}", 400

    #create the check-in URL that will be encoded in the QR code
    checkin_url = f"https://{request.host}/checkin/{token}"
    qr_code = make_qr_base64(checkin_url) #generate QR code as base64 image

    BOOKINGS[token] = {
        "booking_id": booking_id,
        "guest_name": guest_name,
        "property_name": property_name,
        "checkin_date": checkin_date
    }

    #store last booking to display it on the home page
    app.last_booking = {
        "booking_id": booking_id,
        "guest_name": guest_name,
        "property_name": property_name,
        "checkin_date": checkin_date,
        "qr_code": qr_code
    }

    return redirect(url_for("home")) #redirect back to the home page, now showing the QR code


#this is the page opened after the guest scanned the QR code
@app.route("/checkin/<token>")
def checkin(token):
    if token not in BOOKINGS:
        return "Invalid booking token", 404
    
    booking = BOOKINGS[token]

    #render the guest page with booking information
    return render_template_string(
        CHECKIN_PAGE,
        token=token,
        booking_id=booking["booking_id"],
        guest_name=booking["guest_name"],
        property_name=booking["property_name"]
    )

#API endpoint called by JavaScript after the live selfie is captured
@app.post("/api/verify/<token>")
def api_verify(token):
    if token not in BOOKINGS: #check that the booking exists
        return jsonify({"accepted": False, "reason": "invalid_token"}), 404

    booking = BOOKINGS[token]
    booking_id = booking["booking_id"]

    image = dataurl_to_image(request.json["image"]) #convert webcam base64 image to PIL image
    verify_path = Path("/tmp") / f"verify_{booking_id}.jpg"
    image.save(verify_path)

    result = verify(booking_id, verify_path) #compares the live selfie embedding with the stored enrollment template

    return jsonify(result)


#start the Flask development server
if __name__ == "__main__":
    print("AIRCHECK SERVER RUNNING ON PORT 5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
