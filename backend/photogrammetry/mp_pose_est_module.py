import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose

def extract_measurements_from_images(front_img_path, side_img_path, height_cm):
    def extract_keypoints(image_path):
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"Image not found: {image_path}")
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        with mp_pose.Pose(static_image_mode=True) as pose:
            results = pose.process(image_rgb)
            if not results.pose_landmarks:
                raise ValueError("No landmarks detected")
            return results.pose_landmarks.landmark

    front_landmarks = extract_keypoints(front_img_path)
    side_landmarks = extract_keypoints(side_img_path)

    def calculate_distance(a, b):
        return ((a.x - b.x)**2 + (a.y - b.y)**2 + (a.z - b.z)**2) ** 0.5

    measurements = {
        "shoulder_cm": calculate_distance(front_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER],
                                             front_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]),
        "torso_height": calculate_distance(front_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER],
                                           front_landmarks[mp_pose.PoseLandmark.LEFT_HIP]),
        "side_depth": calculate_distance(side_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER],
                                         side_landmarks[mp_pose.PoseLandmark.LEFT_HIP])
    }

    return measurements
