import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import os
import textwrap

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_ARABIC_SUPPORT = True
except ImportError:
    HAS_ARABIC_SUPPORT = False

from omr import grade_exam


class AutoExamGUI:

    @staticmethod
    def rtl_text(text, width=42):
        """
        تشكيل وتهيئة النصوص العربية للعرض في بيئة Tkinter (التي تفتقر لمحرك HarfBuzz تلقائي).
        يتم التفاف السطور أولاً ثم إعادة تشكيل الحروف وربطها (reshaper) ثم ترتيب اتجاه العرض (BiDi).
        """
        if text is None:
            return ""
        value = str(text).strip()
        if not value:
            return value
        if not HAS_ARABIC_SUPPORT:
            return value

        formatted_lines = []
        for paragraph in value.split("\n"):
            if not paragraph.strip():
                formatted_lines.append("")
                continue
            wrapped_lines = textwrap.wrap(paragraph, width=width)
            for line in wrapped_lines:
                reshaped = arabic_reshaper.reshape(line)
                bidi_line = get_display(reshaped)
                formatted_lines.append(bidi_line)
        return "\n".join(formatted_lines)

    def __init__(self, root):

        self.root = root

        self.root.title("نظام التصحيح الآلي - واجهة الفحص الهندسي")
        self.root.geometry("1300x850")
        
        # =========================
        # Color Palette (Dark Theme)
        # =========================
        self.bg_color = "#1E1E2E"
        self.card_bg = "#2A2B3D"
        self.text_color = "#CDD6F4"
        self.accent_blue = "#89B4FA"
        self.accent_green = "#A6E3A1"
        self.accent_red = "#F38BA8"
        
        self.root.configure(bg=self.bg_color)
        
        # متغيرات لحفظ مسارات الملفات
        self.answer_key_path = ""
        self.student_sheet_path = ""
        
        # متغيرات لحفظ الصور لتجنب حذفها من الذاكرة (Garbage Collection)
        self.photo_key = None
        self.photo_student = None

        self.create_widgets()

    def create_widgets(self):

        # =========================
        # Header
        # =========================
        header = tk.Frame(self.root, bg="#11111B", height=80)
        header.pack(fill="x")

        title = tk.Label(
            header,
            text="Automatic Exam Grading System - Engineering View",
            bg="#11111B",
            fg=self.accent_blue,
            font=("Segoe UI", 20, "bold")
        )
        title.pack(pady=(15, 5))

        # =========================
        # Main Layout (Split Pane)
        # =========================
        main_pane = tk.Frame(self.root, bg=self.bg_color)
        main_pane.pack(fill="both", expand=True, padx=20, pady=20)

        # Left Panel: Controls and Results
        left_panel = tk.Frame(main_pane, bg=self.bg_color, width=450)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False) # تثبيت العرض

        # Right Panel: Image Comparison
        right_panel = tk.Frame(main_pane, bg=self.card_bg, bd=1, relief="solid")
        right_panel.pack(side="right", fill="both", expand=True)

        # ---------------------------------------------------------
        # Left Panel Content: Inputs
        # ---------------------------------------------------------
        inputs_frame = tk.Frame(left_panel, bg=self.card_bg, bd=1, relief="solid")
        inputs_frame.pack(fill="x", pady=(0, 15))

        tk.Label(
            inputs_frame, text="📄 Answer Key Sheet",
            bg=self.card_bg, fg=self.text_color, font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.btn_key = tk.Button(
            inputs_frame, text="Select Answer Key",
            bg="#313244", fg=self.text_color, activebackground=self.accent_blue,
            relief="flat", cursor="hand2", font=("Segoe UI", 10, "bold"),
            command=self.select_answer_key
        )
        self.btn_key.pack(padx=15, pady=5, anchor="w", fill="x")

        self.lbl_key = tk.Label(
            inputs_frame, text="No file selected",
            bg=self.card_bg, fg="#6C7086", font=("Segoe UI", 9)
        )
        self.lbl_key.pack(anchor="w", padx=15, pady=(0, 15))

        # --- Student Input ---
        tk.Label(
            inputs_frame, text="👨‍🎓 Student Answer Sheet",
            bg=self.card_bg, fg=self.text_color, font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.btn_student = tk.Button(
            inputs_frame, text="Select Student Sheet",
            bg="#313244", fg=self.text_color, activebackground=self.accent_blue,
            relief="flat", cursor="hand2", font=("Segoe UI", 10, "bold"),
            command=self.select_student_sheet
        )
        self.btn_student.pack(padx=15, pady=5, anchor="w", fill="x")

        self.lbl_student = tk.Label(
            inputs_frame, text="No file selected",
            bg=self.card_bg, fg="#6C7086", font=("Segoe UI", 9)
        )
        self.lbl_student.pack(anchor="w", padx=15, pady=(0, 15))

        # --- Start Button ---
        self.btn_grade = tk.Button(
            left_panel, text="✅ START GRADING",
            bg=self.accent_green, fg="#11111B", activebackground="#87C084",
            relief="flat", cursor="hand2", font=("Segoe UI", 12, "bold"),
            pady=10, command=self.start_grading
        )
        self.btn_grade.pack(fill="x", pady=(0, 15))

        # ---------------------------------------------------------
        # Left Panel Content: Result Box (Unchanged format)
        # ---------------------------------------------------------
        result_frame = tk.Frame(left_panel, bg=self.card_bg, bd=1, relief="solid")
        result_frame.pack(fill="both", expand=True)

        tk.Label(
            result_frame, text="📊 Exam Result",
            bg=self.card_bg, fg=self.text_color, font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.result_box = ScrolledText(
            result_frame, bg="#11111B", fg=self.text_color,
            font=("Segoe UI", 10), relief="flat"
        )
        self.result_box.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        # ---------------------------------------------------------
        # Right Panel Content: Visual Verification (Warped Images)
        # ---------------------------------------------------------
        tk.Label(
            right_panel, 
            text="👁️ Edge Detection & Perspective Correction (Warped Sheets)",
            bg=self.card_bg, fg=self.accent_blue, font=("Segoe UI", 13, "bold")
        ).pack(pady=15)

        images_container = tk.Frame(right_panel, bg=self.card_bg)
        images_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Key Image display
        key_img_frame = tk.Frame(images_container, bg=self.card_bg)
        key_img_frame.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(key_img_frame, text="Correct Answer Key", bg=self.card_bg, fg=self.accent_green, font=("Segoe UI", 11, "bold")).pack()
        self.lbl_img_key = tk.Label(key_img_frame, bg="#11111B", text="[ Waiting for Image ]", fg="#6C7086")
        self.lbl_img_key.pack(fill="both", expand=True, pady=5)

        # Student Image display
        student_img_frame = tk.Frame(images_container, bg=self.card_bg)
        student_img_frame.pack(side="right", fill="both", expand=True, padx=5)
        tk.Label(student_img_frame, text="Student Sheet", bg=self.card_bg, fg=self.accent_red, font=("Segoe UI", 11, "bold")).pack()
        self.lbl_img_student = tk.Label(student_img_frame, bg="#11111B", text="[ Waiting for Image ]", fg="#6C7086")
        self.lbl_img_student.pack(fill="both", expand=True, pady=5)

        # =========================
        # Status Bar
        # =========================
        self.status = tk.Label(
            self.root, text="System Ready", bg="#11111B", fg="#A6ADC8",
            anchor="w", padx=20, font=("Segoe UI", 10)
        )
        self.status.pack(fill="x", side="bottom")

    # =====================================
    # Select Answer Key
    # =====================================
    def select_answer_key(self):
        file_path = filedialog.askopenfilename(
            title="Select Answer Key Sheet",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if file_path:
            self.answer_key_path = file_path
            self.lbl_key.config(text=os.path.basename(file_path), fg=self.accent_green)
            self.status.config(text="✓ Answer key loaded.")

    # =====================================
    # Select Student Sheet
    # =====================================
    def select_student_sheet(self):
        file_path = filedialog.askopenfilename(
            title="Select Student Answer Sheet",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if file_path:
            self.student_sheet_path = file_path
            self.lbl_student.config(text=os.path.basename(file_path), fg=self.accent_green)
            self.status.config(text="✓ Student sheet loaded.")

    # =====================================
    # Start Grading
    # =====================================
    def start_grading(self):
        if not self.answer_key_path or not self.student_sheet_path:
            messagebox.showerror("Error", "Please select both Answer Key and Student Sheet.")
            return

        # إنشاء مجلد النتائج إذا لم يكن موجوداً لتفادي الأخطاء الهندسية
        os.makedirs("results", exist_ok=True)

        self.status.config(text="Processing computer vision pipeline...")
        self.root.update()

        try:
            result = grade_exam(self.answer_key_path, self.student_sheet_path)
            
            # 1. عرض النتيجة النصية
            self.display_result(result)
            
            # 2. عرض الصور المعالجة لتوضيح عملية اكتشاف الحواف
            self.display_processed_images()

            self.status.config(text="✓ Pipeline execution completed successfully.")

        except Exception as e:
            self.status.config(text="Pipeline execution failed.")
            messagebox.showerror("Processing Error", str(e))

    # =====================================
    # Display Visual Pipeline Results
    # =====================================
    def display_processed_images(self):
        try:
            # تحميل الصور المعالجة (Warped) التي تم حفظها بواسطة omr.py
            key_img_path = "results/key_warped.jpg"
            student_img_path = "results/student_warped.jpg"

            if os.path.exists(key_img_path):
                img_k = Image.open(key_img_path)
                img_k.thumbnail((380, 550), Image.Resampling.LANCZOS)
                self.photo_key = ImageTk.PhotoImage(img_k)
                self.lbl_img_key.config(image=self.photo_key, text="")

            if os.path.exists(student_img_path):
                img_s = Image.open(student_img_path)
                img_s.thumbnail((380, 550), Image.Resampling.LANCZOS)
                self.photo_student = ImageTk.PhotoImage(img_s)
                self.lbl_img_student.config(image=self.photo_student, text="")
                
        except Exception as e:
            print(f"Error loading images for display: {e}")

    # =====================================
    # Display Results (Format preserved)
    # =====================================
    def display_result(self, result):
        self.result_box.delete(1.0, tk.END)
        self.result_box.tag_configure("rtl", justify="right", font=("Segoe UI", 10), spacing1=3, spacing3=4)
        self.result_box.tag_configure("q_num", font=("Segoe UI", 10, "bold"), foreground=self.accent_blue)
        self.result_box.configure(wrap="word")

        percentage = result["percentage"]

        if percentage >= 50:
            status = "PASS"
            icon = "✅"
        else:
            status = "FAIL"
            icon = "❌"

        self.result_box.insert(tk.END, "=========================================\n")
        self.result_box.insert(tk.END, "              EXAM RESULT\n")
        self.result_box.insert(tk.END, "=========================================\n\n")
        self.result_box.insert(tk.END, f"📋 Total Questions : {result['total']}\n\n")
        self.result_box.insert(tk.END, f"✅ Correct Answers : {result['correct']}\n\n")
        self.result_box.insert(tk.END, f"❌ Wrong Answers   : {result['wrong']}\n\n")
        self.result_box.insert(tk.END, f"🏆 Final Score     : {result['score']}\n\n")
        self.result_box.insert(tk.END, f"📈 Percentage      : {percentage:.2f}%\n\n")
        self.result_box.insert(tk.END, f"{icon} Status          : {status}\n")

        if "ai_summary" in result:
            self.result_box.insert(tk.END, "\n\n=========================================\n")
            self.result_box.insert(tk.END, "           AI EXPLANATION\n")
            self.result_box.insert(tk.END, "=========================================\n\n")
            self.result_box.insert(tk.END, self.rtl_text(result["ai_summary"]) + "\n\n", "rtl")

        if len(result["mistakes"]) > 0:
            self.result_box.insert(tk.END, "\n\n=========================================\n")
            self.result_box.insert(tk.END, "            WRONG ANSWERS\n")
            self.result_box.insert(tk.END, "=========================================\n\n")
            for item in result["mistakes"]:
                explanation = item.get("explanation", "")
                self.result_box.insert(
                    tk.END,
                    f"Question {item['question']:>2}    "
                    f"Correct: {item['correct']}    "
                    f"Student: {item['student']}\n",
                    "q_num"
                )
                if explanation:
                    self.result_box.insert(tk.END, self.rtl_text(explanation) + "\n\n", "rtl")

        # التلوين الديناميكي للنصوص داخل الصندوق ليتناسب مع النمط الداكن
        self.result_box.tag_add("title", "2.0", "2.end")
        self.result_box.tag_config("title", font=("Segoe UI", 12, "bold"), foreground=self.accent_blue)

        if percentage >= 50:
            self.result_box.tag_add("status", "14.0", "14.end")
            self.result_box.tag_config("status", foreground=self.accent_green, font=("Segoe UI", 10, "bold"))
        else:
            self.result_box.tag_add("status", "14.0", "14.end")
            self.result_box.tag_config("status", foreground=self.accent_red, font=("Segoe UI", 10, "bold"))


# =====================================
# Run Application
# =====================================
if __name__ == "__main__":
    root = tk.Tk()
    app = AutoExamGUI(root)
    root.mainloop()