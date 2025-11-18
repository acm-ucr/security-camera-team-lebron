import cv2
import tkinter as tk
from tkinter import Label, Button, Frame, Text, Scrollbar, END
from PIL import Image, ImageTk
from ultralytics import YOLO
import datetime

class WebcamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ForgeCam - Object Detection Security")
        self.root.geometry("1200x700")
        self.root.configure(bg="#1e1e1e")

        # Configure grid (2 columns)
        self.root.columnconfigure(0, weight=3)  # Left side (video)
        self.root.columnconfigure(1, weight=1)  # Right side (notifications)
        self.root.rowconfigure(0, weight=1)

        # YOLO model
        self.model = YOLO("yolov8n.pt") # need to re update with the trained model

        # Webcam
        self.video_source = 0
        self.vid = cv2.VideoCapture(self.video_source)

        # ==== LEFT SIDE (Video Feed) ====
        self.video_frame = Frame(self.root, bg="#1e1e1e")
        self.video_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.label = Label(self.video_frame, bg="#1e1e1e")
        self.label.pack(fill="both", expand=True)

        self.capture_button = Button(
            self.video_frame,
            text="Capture Image",
            command=self.capture_image,
            bg="#2e2e2e",
            fg="white",
            font=("Helvetica", 12),
            relief="flat"
        )
        self.capture_button.pack(pady=10)

        # ==== RIGHT SIDE (Notifications) ====
        self.right_frame = Frame(self.root, bg="#252526")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(0,10), pady=10)

        self.log_label = Label(
            self.right_frame,
            text="Detected Objects",
            bg="#252526",
            fg="white",
            font=("Helvetica", 14, "bold")
        )
        self.log_label.pack(pady=10)

        # Scrollable text box
        self.text_box = Text(
            self.right_frame,
            bg="#1e1e1e",
            fg="lime",
            font=("Courier", 11),
            height=30,
            width=35
        )
        self.text_box.pack(padx=10, pady=10, fill="both", expand=True)

        self.scrollbar = Scrollbar(self.text_box)
        self.text_box.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

        # Start video loop
        self.update_frame()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_frame(self):
        ret, frame = self.vid.read()
        if ret:
            results = self.model(frame, verbose=False)
            annotated_frame = results[0].plot()

            # Log detections
            for box in results[0].boxes:
                cls = self.model.names[int(box.cls)]
                conf = float(box.conf)
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                self.log_detection(cls, conf, timestamp)

            annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(annotated_frame))
            self.label.config(image=self.photo)

        self.root.after(30, self.update_frame)

    def log_detection(self, cls, conf, timestamp):
        message = f"[{timestamp}] Detected: {cls} ({conf:.2f})\n"
        self.text_box.insert(END, message)
        self.text_box.see(END)

    def capture_image(self):
        ret, frame = self.vid.read()
        if ret:
            filename = datetime.datetime.now().strftime("capture_%Y%m%d_%H%M%S.jpg")
            cv2.imwrite(filename, frame)
            self.log_detection("CAPTURE", 1.0, datetime.datetime.now().strftime("%H:%M:%S"))
            print(f"Image saved as {filename}")

    def on_closing(self):
        self.vid.release()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = WebcamApp(root)
    root.mainloop()
