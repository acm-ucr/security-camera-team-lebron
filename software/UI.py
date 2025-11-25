import tkinter as tk
from tkinter import Frame, Label, Text, Scrollbar, END
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO
from datetime import datetime

class FourQuadrantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ForgeCam - 4 Quadrant Layout")
        self.root.geometry("1200x700")
        self.root.configure(bg="#1e1e1e")

        # Configure 2x2 grid
        self.root.rowconfigure([0, 1], weight=1)
        self.root.columnconfigure([0, 1], weight=1)

        # ==== Q1: Top-Left ====
        self.q1_frame = Frame(self.root, bg="#1e1e1e", bd=2, relief="groove")
        self.q1_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.q1_label = Label(self.q1_frame, text="Q1: Camera Feed", bg="#1e1e1e", fg="white")

        # keep the camera size fixed
        self.q1_frame.grid_propagate(False)

        self.q1_frame.rowconfigure(0, weight=1)
        self.q1_frame.columnconfigure(0, weight=1)

        self.q1_label = Label(self.q1_frame, bg="#1e1e1e")
        self.q1_label.grid(row=0, column=0, sticky="nsew")

        # ==== OpenCV Setup ====
        self.cap = cv2.VideoCapture(0)

        # store the model
        self.model = YOLO("best.pt")

        # Start updating frames
        self.update_frame()

        # ==== Q2: Top-Right ====
        self.q2_frame = Frame(self.root, bg="#252526", bd=2, relief="groove")
        self.q2_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.q2_label = Label(self.q2_frame, text="Q2: Detection Stats", bg="#252526", fg="white")
        self.q2_label.pack(fill="both", expand=True)

        # ==== Q3: Bottom-Left (Logs) ====
        self.q3_frame = Frame(self.root, bg="#1e1e1e", bd=2, relief="groove")
        self.q3_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Scrollable Text widget for logs
        self.q3_text = Text(self.q3_frame, bg="#1e1e1e", fg="lime", wrap="none")
        self.q3_text.pack(side="left", fill="both", expand=True)
        scrollbar = Scrollbar(self.q3_frame, command=self.q3_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.q3_text.config(yscrollcommand=scrollbar.set)

        # ==== Q4: Bottom-Right ====
        self.q4_frame = Frame(self.root, bg="#252526", bd=2, relief="groove")
        self.q4_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.q4_label = Label(self.q4_frame, text="Q4: Counters / FPS", bg="#252526", fg="lime")
        self.q4_label.pack(fill="both", expand=True)

    # runs the model on every frame
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Run YOLO
            results = self.model(frame)
            annotated_frame = results[0].plot()

            # Log detections in Q3
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    name = self.model.names[cls_id]
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    log_msg = f"[{timestamp}] Detected: {name} ({conf:.2f})\n"
                    self.q3_text.insert(END, log_msg)
                    self.q3_text.see(END)  # auto-scroll

            # Get dynamic quadrant size
            q_width  = self.q1_frame.winfo_width()
            q_height = self.q1_frame.winfo_height()

            # Avoid resizing to 1x1 at program start
            if q_width > 10 and q_height > 10:
                annotated_frame = cv2.resize(annotated_frame, (q_width, q_height))

            # Convert to Tkinter image
            frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            # Update label
            self.q1_label.config(image=imgtk)
            self.q1_label.imgtk = imgtk

        self.root.after(15, self.update_frame)

    def on_closing(self):
        self.cap.release()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = FourQuadrantApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
