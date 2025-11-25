import tkinter as tk
from tkinter import Frame, Label
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO
from datetime import datetime
from collections import defaultdict

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

        # ==== OpenCV Setup ====
        self.cap = cv2.VideoCapture(0)
        self.model = YOLO("best.pt")

        # ==== Q2: Top-Right (Cumulative Counts) ====
        self.q2_frame = Frame(self.root, bg="#252526", bd=2, relief="groove")
        self.q2_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.q2_frame.grid_propagate(False)

        # Scrollable Text widget to show cumulative counts
        self.q2_text = Text(self.q2_frame, bg="#252526", fg="white", wrap="none")
        self.q2_text.pack(side="left", fill="both", expand=True)
        scrollbar_q2 = Scrollbar(self.q2_frame, command=self.q2_text.yview)
        scrollbar_q2.pack(side="right", fill="y")
        self.q2_text.config(yscrollcommand=scrollbar_q2.set)

        # Store cumulative counts
        self.total_counts = defaultdict(int)

        # Q3 Frame
        self.q3_frame = Frame(self.root, bg="#1e1e1e", bd=2, relief="groove")
        self.q3_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.q3_frame.grid_propagate(False)
        self.q3_text = Text(self.q3_frame, bg="#1e1e1e", fg="lime", wrap="none")
        self.q3_text.pack(side="left", fill="both", expand=True)
        scrollbar_q3 = Scrollbar(self.q3_frame, command=self.q3_text.yview)
        scrollbar_q3.pack(side="right", fill="y")
        self.q3_text.config(yscrollcommand=scrollbar_q3.set)

        # ==== Q4: Bottom-Right ====
        self.q4_frame = Frame(self.root, bg="#252526", bd=2, relief="groove")
        self.q4_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.q4_frame.grid_propagate(False)
        for i in range(8):
            self.q4_frame.rowconfigure(i, weight=1)
        self.q4_frame.columnconfigure(0, weight=1)
        self.q4_label_stats = Label(self.q4_frame, text="Statistics:", bg="#252526", fg="red")
        self.q4_label_stats.grid(row=0, column=0, sticky="w")
        self.q4_label_fps = Label(self.q4_frame, text="FPS:", bg="#252526", fg="lime")
        self.q4_label_fps.grid(row=1, column=0, sticky="w")
        self.q4_label_objects = Label(self.q4_frame, text="Total Objects Detected:", bg="#252526", fg="lime")
        self.q4_label_objects.grid(row=2, column=0, sticky="w")
        self.q4_label_frequent = Label(self.q4_frame, text="Most Frequent Object:", bg="#252526", fg="lime")
        self.q4_label_frequent.grid(row=3, column=0, sticky="w")
        self.q4_clear_history_button = tk.Button(self.q4_frame, text="Clear History")
        self.q4_clear_history_button.grid(row=4, column=0, sticky="ew", pady=2)
        self.q4_toggle_detection_button = tk.Button(self.q4_frame, text="Toggle Detection")
        self.q4_toggle_detection_button.grid(row=5, column=0, sticky="ew", pady=2)
        self.q4_toggle_boxes_button = tk.Button(self.q4_frame, text="Toggle Boxes")
        self.q4_toggle_boxes_button.grid(row=6, column=0, sticky="ew", pady=2)
        self.q4_screenshot_button = tk.Button(self.q4_frame, text="Screenshot")
        self.q4_screenshot_button.grid(row=7, column=0, sticky="ew", pady=2)

        # Start updating frames
        self.update_frame()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:

            # Run YOLO
            results = self.model(frame)
            annotated_frame = results[0].plot()

            # Update cumulative counts
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    name = self.model.names[cls_id]
                    self.total_counts[name] += 1  # increment total detections

            # Update Q2 Text widget
            self.q2_text.delete(1.0, END)
            for obj_name, count in self.total_counts.items():
                self.q2_text.insert(END, f"{obj_name}: {count}\n")
            self.q2_text.see(END)

            # Optionally, log to Q3
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    name = self.model.names[cls_id]
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    log_msg = f"[{timestamp}] Detected: {name} ({conf:.2f})\n"
                    self.q3_text.insert(END, log_msg)
                    self.q3_text.see(END)

            # Resize Q1 camera feed
            q_width  = self.q1_frame.winfo_width()
            q_height = self.q1_frame.winfo_height()
            if q_width > 10 and q_height > 10:
                annotated_frame = cv2.resize(annotated_frame, (q_width, q_height))

            frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.q1_label.config(image=imgtk)
            self.q1_label.imgtk = imgtk

        self.root.after(100, self.update_frame)  # update every 100ms


    def on_closing(self):
        self.cap.release()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = FourQuadrantApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
