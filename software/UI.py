import tkinter as tk
from tkinter import Frame, Label, Text, Scrollbar, END
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO
from datetime import datetime
from collections import defaultdict
import paho.mqtt.client as mqtt
import json
import time

class FourQuadrantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ForgeCam - 4 Quadrant Layout")
        self.root.geometry("1200x700")
        self.root.configure(bg="#1e1e1e")

        # Configure 2x2 grid equally
        self.root.rowconfigure(0, weight=1, minsize=350)
        self.root.rowconfigure(1, weight=1, minsize=350)
        self.root.columnconfigure(0, weight=1, minsize=600)
        self.root.columnconfigure(1, weight=1, minsize=600)

        # ==== Q1: Top-Left (Camera) ====
        self.q1_frame = Frame(self.root, bg="#1e1e1e", bd=2, relief="groove")
        self.q1_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.q1_frame.grid_propagate(False)
        self.q1_frame.rowconfigure(0, weight=1)
        self.q1_frame.columnconfigure(0, weight=1)
        self.q1_label = Label(self.q1_frame, bg="#1e1e1e")
        self.q1_label.grid(row=0, column=0, sticky="nsew")

        # ==== OpenCV & YOLO Setup ====
        self.cap = cv2.VideoCapture(0)
        self.model = YOLO("best.pt")

        # ==== Q2: Top-Right (Cumulative Counts) ====
        self.q2_frame = Frame(self.root, bg="#252526", bd=2, relief="groove")
        self.q2_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.q2_frame.grid_propagate(False)
        self.q2_text = Text(self.q2_frame, bg="#252526", fg="white", wrap="none")
        self.q2_text.pack(side="left", fill="both", expand=True)
        scrollbar_q2 = Scrollbar(self.q2_frame, command=self.q2_text.yview)
        scrollbar_q2.pack(side="right", fill="y")
        self.q2_text.config(yscrollcommand=scrollbar_q2.set)

        # ==== Q3: Bottom-Left (Logs) ====
        self.q3_frame = Frame(self.root, bg="#1e1e1e", bd=2, relief="groove")
        self.q3_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.q3_frame.grid_propagate(False)
        self.q3_text = Text(self.q3_frame, bg="#1e1e1e", fg="lime", wrap="none")
        self.q3_text.pack(side="left", fill="both", expand=True)
        scrollbar_q3 = Scrollbar(self.q3_frame, command=self.q3_text.yview)
        scrollbar_q3.pack(side="right", fill="y")
        self.q3_text.config(yscrollcommand=scrollbar_q3.set)

        # ==== Q4: Bottom-Right (Stats & Controls) ====
        self.q4_frame = Frame(self.root, bg="#252526", bd=2, relief="groove")
        self.q4_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # Configure Q4 rows & column
        for i in range(9):
            if i < 4:
                self.q4_frame.rowconfigure(i, weight=0, minsize=25)
            else:
                self.q4_frame.rowconfigure(i, weight=1, minsize=35)
        self.q4_frame.columnconfigure(0, weight=1)

        # --- Labels ---
        self.q4_label_stats = Label(self.q4_frame, text="Statistics:", bg="#252526", fg="red")
        self.q4_label_stats.grid(row=0, column=0, sticky="w", padx=5)
        self.q4_label_fps = Label(self.q4_frame, text="FPS:", bg="#252526", fg="lime")
        self.q4_label_fps.grid(row=1, column=0, sticky="w", padx=5)
        self.q4_label_objects = Label(self.q4_frame, text="Total Objects Detected:", bg="#252526", fg="lime")
        self.q4_label_objects.grid(row=2, column=0, sticky="w", padx=5)
        self.q4_label_frequent = Label(self.q4_frame, text="Most Frequent Object:", bg="#252526", fg="lime")
        self.q4_label_frequent.grid(row=3, column=0, sticky="w", padx=5)

        # --- Buttons ---
        self.q4_clear_history_button = tk.Button(self.q4_frame, text="Clear History")
        self.q4_clear_history_button.grid(row=4, column=0, sticky="ew", padx=5, pady=2)
        self.q4_toggle_detection_button = tk.Button(self.q4_frame, text="Toggle Detection")
        self.q4_toggle_detection_button.grid(row=5, column=0, sticky="ew", padx=5, pady=2)
        self.q4_toggle_boxes_button = tk.Button(self.q4_frame, text="Toggle Boxes")
        self.q4_toggle_boxes_button.grid(row=6, column=0, sticky="ew", padx=5, pady=2)
        self.q4_screenshot_button = tk.Button(self.q4_frame, text="Screenshot")
        self.q4_screenshot_button.grid(row=7, column=0, sticky="ew", padx=5, pady=2)
        self.q4_quit_button = tk.Button(self.q4_frame, text="Quit", command=self.on_closing)
        self.q4_quit_button.grid(row=8, column=0, sticky="ew", padx=5, pady=2)

        # ==== MQTT Setup ====
        self.BROKER = "broker.emqx.io"
        self.PORT = 1883
        self.TOPIC = "security/alert"
        self.mqtt_client = mqtt.Client(client_id="ForgeCamPublisher")
        self.mqtt_client.connect(self.BROKER, self.PORT)
        self.mqtt_client.loop_start()

        # Store counts
        self.total_counts = defaultdict(int)
        self.last_person_alert = 0
        self.alert_interval = 5  # seconds

        # Start updating frames
        self.update_frame()

    # --- MQTT alert ---
    def send_mqtt_alert(self, obj_name, confidence):
        message = {
            "object": obj_name,
            "confidence": confidence,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.mqtt_client.publish(self.TOPIC, json.dumps(message))
        print(f"MQTT alert sent: {message}")

    # --- Update camera frames ---
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            start_time = time.time()

            results = self.model(frame)
            annotated_frame = results[0].plot()

            # Update counts and logs
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    name = self.model.names[cls_id]
                    self.total_counts[name] += 1

                    # Log to Q3
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    self.q3_text.insert(END, f"[{timestamp}] Detected: {name} ({conf:.2f})\n")
                    self.q3_text.see(END)

                    # MQTT alert for person
                    if name.lower() == "person":
                        now = time.time()
                        if now - self.last_person_alert > self.alert_interval:
                            self.send_mqtt_alert(name, conf)
                            self.last_person_alert = now

            # Update Q2 cumulative counts
            self.q2_text.delete(1.0, END)
            for obj_name, count in self.total_counts.items():
                self.q2_text.insert(END, f"{obj_name}: {count}\n")
            self.q2_text.see(END)

            # Resize camera feed
            q_width, q_height = self.q1_frame.winfo_width(), self.q1_frame.winfo_height()
            if q_width > 10 and q_height > 10:
                annotated_frame = cv2.resize(annotated_frame, (q_width, q_height))
            frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.q1_label.config(image=imgtk)
            self.q1_label.imgtk = imgtk

            # Update FPS
            fps = 1.0 / (time.time() - start_time)
            self.q4_label_fps.config(text=f"FPS: {fps:.2f}")

        self.root.after(100, self.update_frame)

    # --- Closing ---
    def on_closing(self):
        self.cap.release()
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = FourQuadrantApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
