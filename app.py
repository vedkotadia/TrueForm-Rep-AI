import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from flask import Flask, render_template, Response, request, jsonify
import cv2
import mediapipe as mp
import numpy as np
import time
from werkzeug.utils import secure_filename

from body_part_angle import BodyPartAngle
from types_of_exercise import TypeOfExercise
from utils import score_table

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'output'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

class VideoCamera(object):
    def __init__(self, video_source=0, exercise_type="push-up"):
        self.video = cv2.VideoCapture(video_source)
        if video_source == 0:
            self.video.set(3, 800)
            self.video.set(4, 480)
        self.exercise_type = exercise_type
        self.counter = 0
        self.status = True
        self.pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def __del__(self):
        self.video.release()
        self.pose.close()

    def get_frame(self):
        success, frame = self.video.read()
        if not success:
            return None

        # Resize for consistent processing
        frame = cv2.resize(frame, (800, 480), interpolation=cv2.INTER_AREA)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False

        results = self.pose.process(frame_rgb)

        try:
            landmarks = results.pose_landmarks.landmark
            self.counter, self.status = TypeOfExercise(landmarks).calculate_exercise(
                self.exercise_type, self.counter, self.status)
        except Exception as e:
            pass

        frame = score_table(self.exercise_type, frame, self.counter, self.status)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(174, 139, 45), thickness=2, circle_radius=2),
            )

        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

def gen(camera):
    while True:
        frame = camera.get_frame()
        if frame is None:
            break
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        # small sleep to prevent overwhelming CPU
        time.sleep(0.01)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    source = request.args.get('source', '0')
    exercise = request.args.get('exercise', 'push-up')
    
    video_source = 0 if source == '0' else os.path.join(app.config['UPLOAD_FOLDER'], source)
    
    camera = VideoCamera(video_source=video_source, exercise_type=exercise)
    return Response(gen(camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'filename': filename})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
