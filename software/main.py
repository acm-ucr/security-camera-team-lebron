import cv2
from ultralytics import YOLO

# --- 1. Load your trained YOLOv8 model ---
model = YOLO("100ephoch.pt")  # change this to your model's .pt file

# --- 2. Open webcam (0 = default camera) ---
cap = cv2.VideoCapture(0)

# Optional: set resolution
cap.set(3, 1280)
cap.set(4, 720)

print("Press 'q' to quit...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # --- 3. Run YOLOv8 inference on each frame ---
    results = model(frame)

    # --- 4. Display annotated results ---
    annotated_frame = results[0].plot()  # draw bounding boxes
    cv2.imshow("YOLOv8 Webcam Detection", annotated_frame)

    # --- 5. Exit on 'q' key ---
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- 6. Cleanup ---
cap.release()
cv2.destroyAllWindows()
