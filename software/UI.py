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
import os
import numpy as np
import customtkinter as ctk

class FourQuadrantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ForgeCam - 4 Quadrant Layout")
        self.root.geometry("1200x700")
        self.root.configure(bg="#1e1e1e")

        # ==== 2x2 grid configuration ====
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)

        # ==== Q1: Top-Left (Camera) ====
        self.q1_frame = Frame(self.root, bg="#1e1e1e", bd=2, relief="groove")
        self.q1_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.q1_frame.grid_propagate(False)

        self.q1_label = Label(self.q1_frame, bg="#1e1e1e")
        self.q1_label.place(x=0, y=0, relwidth=1, relheight=1)

        # ==== OpenCV & YOLO Setup ====
        self.cap = cv2.VideoCapture(0)
        self.model = YOLO("best.pt")

        # Detection flags
        self.detection_on = True
        self.show_boxes = True

        # ==== Q2: Top-Right (Cumulative Counts) ====
        self.q2_frame = Frame(self.root, bg="#252526", bd=2, relief="groove")
        self.q2_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.q2_text = Text(self.q2_frame, bg="#252526", fg="white", wrap="none")
        self.q2_text.pack(side="left", fill="both", expand=True)
        scrollbar_q2 = Scrollbar(self.q2_frame, command=self.q2_text.yview)
        scrollbar_q2.pack(side="right", fill="y")
        self.q2_text.config(yscrollcommand=scrollbar_q2.set)

        # ==== Q3: Bottom-Left (Logs) ====
        self.q3_frame = Frame(self.root, bg="#1e1e1e", bd=2, relief="groove")
        self.q3_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.q3_text = Text(self.q3_frame, bg="#1e1e1e", fg="lime", wrap="none")
        self.q3_text.pack(side="left", fill="both", expand=True)
        scrollbar_q3 = Scrollbar(self.q3_frame, command=self.q3_text.yview)
        scrollbar_q3.pack(side="right", fill="y")
        self.q3_text.config(yscrollcommand=scrollbar_q3.set)

        # ==== Q4: Bottom-Right (Stats & Controls) ====
        self.q4_frame = Frame(self.root, bg="#252526", bd=2, relief="groove")
        self.q4_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        for i in range(9):
            self.q4_frame.rowconfigure(i, weight=1)
        self.q4_frame.columnconfigure(0, weight=1)

        # Labels
        self.q4_label_stats = Label(self.q4_frame, text="Statistics:", bg="#252526", fg="red")
        self.q4_label_stats.grid(row=0, column=0, sticky="w", padx=5)
        self.q4_label_fps = Label(self.q4_frame, text="FPS:", bg="#252526", fg="lime")
        self.q4_label_fps.grid(row=1, column=0, sticky="w", padx=5)
        self.q4_label_objects = Label(self.q4_frame, text="Total Objects Detected:", bg="#252526", fg="lime")
        self.q4_label_objects.grid(row=2, column=0, sticky="w", padx=5)
        self.q4_label_frequent = Label(self.q4_frame, text="Most Frequent Object:", bg="#252526", fg="lime")
        self.q4_label_frequent.grid(row=3, column=0, sticky="w", padx=5)

        # ---- CustomTkinter button style ----
        btn_kwargs = {"width": 180, "height": 35, "corner_radius": 15, "font": ("Arial", 12)}

        self.q4_clear_history_button = ctk.CTkButton(self.q4_frame, text="Clear Logs", command=self.clear_logs,
                                                     fg_color="#3498db", hover_color="#2980b9", **btn_kwargs)
        self.q4_clear_history_button.grid(row=4, column=0, sticky="ew", padx=5, pady=2)

        self.q4_toggle_detection_button = ctk.CTkButton(self.q4_frame, text="Toggle Detection", command=self.toggle_detection,
                                                        fg_color="#3498db", hover_color="#2980b9", **btn_kwargs)
        self.q4_toggle_detection_button.grid(row=5, column=0, sticky="ew", padx=5, pady=2)

        self.q4_toggle_boxes_button = ctk.CTkButton(self.q4_frame, text="Toggle Boxes", command=self.toggle_boxes,
                                                    fg_color="#3498db", hover_color="#2980b9", **btn_kwargs)
        self.q4_toggle_boxes_button.grid(row=6, column=0, sticky="ew", padx=5, pady=2)

        self.q4_screenshot_button = ctk.CTkButton(self.q4_frame, text="Screenshot", command=self.take_screenshot,
                                                  fg_color="#3498db", hover_color="#2980b9", **btn_kwargs)
        self.q4_screenshot_button.grid(row=7, column=0, sticky="ew", padx=5, pady=2)

        # Quit button with different color using copy of btn_kwargs
        quit_btn_kwargs = btn_kwargs.copy()
        quit_btn_kwargs["fg_color"] = "#e74c3c"
        quit_btn_kwargs["hover_color"] = "#c0392b"
        self.q4_quit_button = ctk.CTkButton(self.q4_frame, text="Quit", command=self.on_closing, **quit_btn_kwargs)
        self.q4_quit_button.grid(row=8, column=0, sticky="ew", padx=5, pady=2)

        # ==== MQTT Setup ====
        self.BROKER = "broker.emqx.io"
        self.PORT = 1883
        self.TOPIC = "security/alert"
        self.mqtt_client = mqtt.Client(client_id="ForgeCamPublisher")
        self.mqtt_client.connect(self.BROKER, self.PORT)
        self.mqtt_client.loop_start()

        # Data
        self.total_counts = defaultdict(int)
        self.last_person_alert = 0
        self.alert_interval = 5

        # Ensure screenshots folder exists
        os.makedirs("screenshots", exist_ok=True)

        # Start updating
        self.update_frame()

    # --- Q4 button methods ---
    def clear_logs(self):
        self.q3_text.delete(1.0, END)

    def toggle_detection(self):
        self.detection_on = not self.detection_on

    def toggle_boxes(self):
        self.show_boxes = not self.show_boxes

    def take_screenshot(self):
        ret, frame = self.cap.read()
        if ret:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"screenshots/screenshot_{timestamp}.png"
            cv2.imwrite(path, frame)
            print(f"Screenshot saved: {path}")

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
            display_frame = frame.copy()

            if self.detection_on:
                results = self.model(frame)
                if self.show_boxes:
                    display_frame = results[0].plot()
                # Update counts and logs
                for result in results:
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        name = self.model.names[cls_id]
                        self.total_counts[name] += 1
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        self.q3_text.insert(END, f"[{timestamp}] Detected: {name} ({conf:.2f})\n")
                        self.q3_text.see(END)
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

            # ==== Update Q4 statistics ====
            total_objects = sum(self.total_counts.values())
            if self.total_counts:
                most_frequent = max(self.total_counts, key=self.total_counts.get)
            else:
                most_frequent = "N/A"
            self.q4_label_objects.config(text=f"Total Objects Detected: {total_objects}")
            self.q4_label_frequent.config(text=f"Most Frequent Object: {most_frequent}")

            # ==== Resize camera feed to fixed Q1 quadrant ====
            q_width, q_height = self.q1_frame.winfo_width(), self.q1_frame.winfo_height()
            if q_width > 10 and q_height > 10:
                h, w, _ = display_frame.shape
                scale = min(q_width / w, q_height / h)
                new_w = max(1, int(w * scale))
                new_h = max(1, int(h * scale))
                resized = cv2.resize(display_frame, (new_w, new_h))

                canvas = np.zeros((q_height, q_width, 3), dtype=np.uint8)
                top = (q_height - new_h) // 2
                left = (q_width - new_w) // 2
                canvas[top:top+new_h, left:left+new_w] = resized

                frame_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.q1_label.config(image=imgtk)
                self.q1_label.imgtk = imgtk

            # Update FPS
            fps = 1.0 / (time.time() - start_time)
            self.q4_label_fps.config(text=f"FPS: {fps:.2f}")

        self.root.after(30, self.update_frame)

    # --- Closing ---
    def on_closing(self):
        self.cap.release()
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        self.root.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root = tk.Tk()
    app = FourQuadrantApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
