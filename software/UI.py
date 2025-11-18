import tkinter as tk
from tkinter import Frame, Label, Text, Scrollbar

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
        self.q1_label.pack(fill="both", expand=True)

        # ==== Q2: Top-Right ====
        self.q2_frame = Frame(self.root, bg="#252526", bd=2, relief="groove")
        self.q2_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.q2_label = Label(self.q2_frame, text="Q2: Detection Stats", bg="#252526", fg="white")
        self.q2_label.pack(fill="both", expand=True)

        # ==== Q3: Bottom-Left ====
        self.q3_frame = Frame(self.root, bg="#1e1e1e", bd=2, relief="groove")
        self.q3_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.q3_label = Label(self.q3_frame, text="Q3: Logs", bg="#1e1e1e", fg="lime")
        self.q3_label.pack(fill="both", expand=True)

        # ==== Q4: Bottom-Right ====
        self.q4_frame = Frame(self.root, bg="#252526", bd=2, relief="groove")
        self.q4_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.q4_label = Label(self.q4_frame, text="Q4: Counters / FPS", bg="#252526", fg="lime")
        self.q4_label.pack(fill="both", expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = FourQuadrantApp(root)
    root.mainloop()
