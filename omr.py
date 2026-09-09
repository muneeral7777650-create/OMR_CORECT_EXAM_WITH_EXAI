import os
import cv2
import numpy as np

from exam_explainer import enrich_result_with_ai
from image_processing import (
    load_image,
    preprocess_sheet
)

TOTAL_QUESTIONS = 40

# الألوان المحددة للتمييز البصري (BGR format)
COLOR_GREEN = (0, 255, 0) # إجابة صحيحة أو نموذجية
COLOR_RED = (0, 0, 255)   # خطأ الطالب

# ==========================================
# Count Filled Pixels
# ==========================================
def bubble_score(roi):

    if roi.size == 0:
        return 0

    return cv2.countNonZero(roi)

# ==========================================
# Extract Answers
# ==========================================
def extract_answers(thresh):

    answers = {}

    height, width = thresh.shape

    radius = 18

    # --------------------------------------
    # TRUE / FALSE (1 - 10)
    # --------------------------------------

    tf_true_x = int(width * 0.18)
    tf_false_x = int(width * 0.25)

    tf_start_y = int(height * 0.13)
    tf_gap_y = int(height * 0.043)

    for q in range(1, 11):

        y = tf_start_y + ((q - 1) * tf_gap_y)

        true_roi = thresh[
            y-radius:y+radius,
            tf_true_x-radius:tf_true_x+radius
        ]

        false_roi = thresh[
            y-radius:y+radius,
            tf_false_x-radius:tf_false_x+radius
        ]

        scores = [
            bubble_score(true_roi),
            bubble_score(false_roi)
        ]

        answer = np.argmax(scores) + 1

        answers[q] = answer

    # --------------------------------------
    # MCQ 11 - 30
    # --------------------------------------

    mcq1_start_x = int(width * 0.37)

    option_gap = 55

    mcq1_start_y = int(height * 0.13)
    mcq1_gap_y = int(height * 0.041)

    for q in range(11, 31):

        row = q - 11

        y = mcq1_start_y + row * mcq1_gap_y

        scores = []

        for option in range(4):

            x = mcq1_start_x + (option * option_gap)

            roi = thresh[
                y-radius:y+radius,
                x-radius:x+radius
            ]

            scores.append(
                bubble_score(roi)
            )

        answers[q] = np.argmax(scores) + 1

    # --------------------------------------
    # MCQ 31 - 40
    # --------------------------------------

    mcq2_start_x = int(width * 0.67)

    for q in range(31, 41):

        row = q - 31

        y = mcq1_start_y + row * mcq1_gap_y

        scores = []

        for option in range(4):

            x = mcq2_start_x + (option * option_gap)

            roi = thresh[
                y-radius:y+radius,
                x-radius:x+radius
            ]

            scores.append(
                bubble_score(roi)
            )

        answers[q] = np.argmax(scores) + 1

    return answers

# ==========================================
# Compare Answers
# ==========================================
def compare_answers(
        key_answers,
        student_answers):

    correct = 0

    mistakes = []

    for q in range(1, TOTAL_QUESTIONS + 1):

        key = key_answers[q]

        student = student_answers[q]

        if key == student:

            correct += 1

        else:

            mistakes.append(
                {
                    "question": q,
                    "correct": key,
                    "student": student
                }
            )

    wrong = TOTAL_QUESTIONS - correct

    percentage = (
        correct / TOTAL_QUESTIONS
    ) * 100

    return {
        "total": TOTAL_QUESTIONS,
        "correct": correct,
        "wrong": wrong,
        "score": f"{correct}/{TOTAL_QUESTIONS}",
        "percentage": percentage,
        "mistakes": mistakes
    }

# ==========================================
# Visualize Answers (Added)
# ==========================================
def visualize_answers(warped_image, sheet_answers, key_answers=None, is_key=False):
    """
    تقوم هذه الدالة برسم التمييز البصري (Highligts) على الصورة المصححة.
    """
    height, width = warped_image.shape[:2]
    radius_draw = 15 # نصف قطر رسم الدائرة

    # تم عزل منطق التكرار هنا ليطابق دالة extract_answers تماماً لضمان دقة الإحداثيات

    # --------------------------------------
    # TRUE / FALSE (1 - 10)
    # --------------------------------------
    tf_true_x = int(width * 0.18)
    tf_false_x = int(width * 0.25)
    tf_start_y = int(height * 0.13)
    tf_gap_y = int(height * 0.043)
    tf_x_coords = [tf_true_x, tf_false_x]

    for q in range(1, 11):
        y = tf_start_y + ((q - 1) * tf_gap_y)
        # الفقرة التي تم اختيارها (إندكس)
        ans_idx = sheet_answers[q] - 1 

        if is_key:
            # لوحة النموذج: تمييز النموذج بأخضر
            center = (tf_x_coords[ans_idx], y)
            cv2.circle(warped_image, center, radius_draw, COLOR_GREEN, 3)
        else:
            # لوحة الطالب: مقارنة مع النموذج
            key_ans_idx = key_answers[q] - 1 # الفقرة النموذجية الصحيحة

            if ans_idx == key_ans_idx:
                # إجابة الطالب صحيحة: رسم دائرة خضراء
                center = (tf_x_coords[ans_idx], y)
                cv2.circle(warped_image, center, radius_draw, COLOR_GREEN, 3)
            else:
                # إجابة الطالب خاطئة: رسم دائرة حمراء على موضع الطالب
                center_student = (tf_x_coords[ans_idx], y)
                cv2.circle(warped_image, center_student, radius_draw, COLOR_RED, 3)
                # رسم دائرة خضراء في الموضع النموذجي لتوضيح المقارنة
                center_key = (tf_x_coords[key_ans_idx], y)
                cv2.circle(warped_image, center_key, radius_draw, COLOR_GREEN, 3)

    # --------------------------------------
    # MCQ 11 - 30
    # --------------------------------------
    mcq1_start_x = int(width * 0.37)
    option_gap = 55
    mcq1_start_y = int(height * 0.13)
    mcq1_gap_y = int(height * 0.041)

    for q in range(11, 31):
        row = q - 11
        y = mcq1_start_y + row * mcq1_gap_y
        ans_idx = sheet_answers[q] - 1 # الخيار المختار (0-3)

        if is_key:
            # لوحة النموذج
            x = mcq1_start_x + (ans_idx * option_gap)
            center = (x, y)
            cv2.circle(warped_image, center, radius_draw, COLOR_GREEN, 3)
        else:
            # لوحة الطالب
            key_ans_idx = key_answers[q] - 1
            
            if ans_idx == key_ans_idx:
                # الطالب صح
                x = mcq1_start_x + (ans_idx * option_gap)
                center = (x, y)
                cv2.circle(warped_image, center, radius_draw, COLOR_GREEN, 3)
            else:
                # الطالب خطأ: أحمر على موضع الطالب، أخضر على موضع النموذج
                x_student = mcq1_start_x + (ans_idx * option_gap)
                center_student = (x_student, y)
                cv2.circle(warped_image, center_student, radius_draw, COLOR_RED, 3)
                # توضيح الإجابة الصحيحة من النموذج
                x_key = mcq1_start_x + (key_ans_idx * option_gap)
                center_key = (x_key, y)
                cv2.circle(warped_image, center_key, radius_draw, COLOR_GREEN, 3)

    # --------------------------------------
    # MCQ 31 - 40
    # --------------------------------------
    mcq2_start_x = int(width * 0.67)

    for q in range(31, 41):
        row = q - 31
        y = mcq1_start_y + row * mcq1_gap_y
        ans_idx = sheet_answers[q] - 1

        if is_key:
            # لوحة النموذج
            x = mcq2_start_x + (ans_idx * option_gap)
            center = (x, y)
            cv2.circle(warped_image, center, radius_draw, COLOR_GREEN, 3)
        else:
            # لوحة الطالب
            key_ans_idx = key_answers[q] - 1
            
            if ans_idx == key_ans_idx:
                x = mcq2_start_x + (ans_idx * option_gap)
                center = (x, y)
                cv2.circle(warped_image, center, radius_draw, COLOR_GREEN, 3)
            else:
                # خطأ: تمييز الطالب، توضيح النموذج
                x_student = mcq2_start_x + (ans_idx * option_gap)
                center_student = (x_student, y)
                cv2.circle(warped_image, center_student, radius_draw, COLOR_RED, 3)
                # توضيح النموذج الصحيح
                x_key = mcq2_start_x + (key_ans_idx * option_gap)
                center_key = (x_key, y)
                cv2.circle(warped_image, center_key, radius_draw, COLOR_GREEN, 3)

    return warped_image

# ==========================================
# Save Processed Images
# ==========================================
def save_processed_images(
        key_sheet,
        student_sheet):
    """تحفظ الصور المصححة الأساسية قبل التلوين البصري."""
    os.makedirs("results", exist_ok=True)
    cv2.imwrite(
        "results/key_warped.jpg",
        key_sheet
    )

    cv2.imwrite(
        "results/student_warped.jpg",
        student_sheet
    )

# ==========================================
# Save Visualized Images (Added)
# ==========================================
def save_visualized_images(key_sheet_viz, student_sheet_viz):
    """تحفظ الصور المصححة والمظللة الجديدة بشكل منفصل."""
    os.makedirs("results", exist_ok=True)
    cv2.imwrite("results/key_visualized.jpg", key_sheet_viz)
    cv2.imwrite("results/student_visualized.jpg", student_sheet_viz)

# ==========================================
# Main Grading Function (Modified)
# ==========================================
def grade_exam(
        answer_key_path,
        student_sheet_path):

    # Load Images
    key_image = load_image(
        answer_key_path
    )

    student_image = load_image(
        student_sheet_path
    )

    # Preprocess (get base warped images and thresholds)
    key_sheet, key_thresh = preprocess_sheet(
        key_image
    )

    student_sheet, student_thresh = preprocess_sheet(
        student_image
    )

    # حفظ الصور المصححة الأساسية (للمرجعية، ليست للعرض المظلل)
    save_processed_images(
        key_sheet,
        student_sheet
    )

    # Extract Answers
    key_answers = extract_answers(
        key_thresh
    )

    student_answers = extract_answers(
        student_thresh
    )

    # ==========================================
    # Visualization (Engineering Logic Start)
    # ==========================================
    # إنشاء نسخ هندسية من الصور المصححة قبل الرسم عليها، لتجنب تعديل الصور الأساسية
    key_sheet_viz = key_sheet.copy()
    student_sheet_viz = student_sheet.copy()

    # تظليل ورقة النموذج: الدوائر النموذجية (خضراء)
    key_sheet_viz = visualize_answers(key_sheet_viz, key_answers, is_key=True)

    # تظليل ورقة الطالب: الدوائر الصحيحة والخاطئة والمقارنة
    student_sheet_viz = visualize_answers(student_sheet_viz, student_answers, key_answers=key_answers, is_key=False)

    # حفظ الصور المظللة الجديدة
    save_visualized_images(key_sheet_viz, student_sheet_viz)

    # Compare
    result = compare_answers(
        key_answers,
        student_answers
    )

    result = enrich_result_with_ai(result)

    # تخزين مصفوفات الصور الأصلية والمعدلة والمظللة للاستخدام المباشر في واجهة Streamlit
    result["key_image"] = key_image
    result["student_image"] = student_image
    result["key_warped"] = key_sheet
    result["student_warped"] = student_sheet
    result["key_visualized"] = key_sheet_viz
    result["student_visualized"] = student_sheet_viz
    result["key_answers"] = key_answers
    result["student_answers"] = student_answers

    return result