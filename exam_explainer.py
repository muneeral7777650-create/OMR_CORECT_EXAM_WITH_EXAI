"""نظام شرح ذكي للنتائج بعد التصحيح."""

QUESTION_TOPICS = {
    1: "الفهم العام للمعلومة الصحيحة",
    2: "التقييم المنطقي للعبارة",
    3: "المعرفة الأساسية",
    4: "فهم النص والبيان",
    5: "استيعاب الفكرة الرئيسية",
    6: "الاستدلال المنطقي",
    7: "المقارنة بين البدائل",
    8: "التحليل البنيوي",
    9: "التطبيق العملي للمفهوم",
    10: "التقييم النهائي للعبارة",
    11: "التفكير التحليلي",
    12: "تحليل الاختيارات",
    13: "الفهم المعرفي",
    14: "استنتاج الإجابة الصحيحة",
    15: "التمييز بين الخيارات",
    16: "التطبيق العملي",
    17: "الفهم المفاهيمي",
    18: "التذكر والاسترجاع",
    19: "الاستنتاج المنطقي",
    20: "تقييم البدائل",
    21: "الفهم الدقيق",
    22: "الربط بين المفاهيم",
    23: "الاستدلال العلمي",
    24: "التحليل المقارن",
    25: "الحكم على الأفضلية",
    26: "التطبيق على الحالة",
    27: "الحل المنطقي",
    28: "الفحص الدقيق للخيارات",
    29: "الاستنتاج الصحيح",
    30: "التقويم النهائي",
    31: "الاستيعاب المتقدم",
    32: "التحليل المنطقي",
    33: "الفهم العميق",
    34: "تحديد الإجابة الأقرب",
    35: "التفكير النقدي",
    36: "الاستدلال المقارن",
    37: "الاستجلاء المفاهيمي",
    38: "الفحص الدقيق",
    39: "التطبيق على السيناريو",
    40: "التقييم النهائي للمستوى",
}

TRUE_FALSE_LABELS = {
    1: "صح",
    2: "خطأ",
}

MCQ_LABELS = {
    1: "A",
    2: "B",
    3: "C",
    4: "D",
}


def _get_option_label(question_number, option_value):
    if 1 <= question_number <= 10:
        return TRUE_FALSE_LABELS.get(option_value, str(option_value))
    return MCQ_LABELS.get(option_value, str(option_value))


def _get_question_group(question_number):
    if 1 <= question_number <= 10:
        return "صح/خطأ"
    if 11 <= question_number <= 30:
        return "اختيار من متعدد (1)"
    return "اختيار من متعدد (2)"


def build_question_explanation(question_number, correct_answer, student_answer):
    """يُنشئ شرحًا عربيًا لكل سؤال خاطئ."""
    topic = QUESTION_TOPICS.get(question_number, "الفهم العام للسؤال")
    question_group = _get_question_group(question_number)

    correct_label = _get_option_label(question_number, correct_answer)
    student_label = _get_option_label(question_number, student_answer)

    return (
        f"السؤال {question_number} ({question_group}): "
        f"إجابة الطالب كانت ({student_label}) بينما الإجابة الصحيحة هي ({correct_label}). "
        f"يشير ذلك إلى الحاجة لدعم مفهوم '{topic}'. "
        f"يُنصح بمراجعة هذا الدرس بدقة قبل الاختبار القادم."
    )


def generate_exam_summary(result):
    """يُنشئ ملخصًا ذكيًا للنتيجة العامة."""
    percentage = result.get("percentage", 0)
    wrong = result.get("wrong", 0)
    correct = result.get("correct", 0)
    total = result.get("total", 0)

    if percentage >= 85:
        level = "مستوى ممتاز جدًا 🌟"
        advice = "أداء متفوق ورائع، واصل بهذا الأداء المتميز مع مراجعة النقاط البسيطة المتبقية."
    elif percentage >= 70:
        level = "مستوى جيد جدًا 👍"
        advice = "أداء قوي وناجح، وتوجد بعض المفاهيم التي تتطلب مراجعة سريعة لرفع الكفاءة."
    elif percentage >= 50:
        level = "مستوى متوسط (ناجح) ⚠️"
        advice = "اجتزت الاختبار ولكن ينصح بشدة بمراجعة الأسئلة الخاطئة وشروحاتها بعناية."
    else:
        level = "مستوى يحتاج إلى تركيز ودراسة مكثفة ❌"
        advice = "لم يتم اجتياز الاختبار. يُنصح بإعادة مراجعة المنهج والمفاهيم الأساسية ثم إعادة الاختبار."

    return (
        f"ملخص تحليلي: حصل الطالب على {correct} إجابة صحيحة من أصل {total}، "
        f"بنسبة نجاح {percentage:.2f}%. "
        f"التقييم العام: {level}. "
        f"عدد الأخطاء: {wrong}. {advice}"
    )


def enrich_result_with_ai(result):
    """يضيف شرحًا لكل خطأ وملخصًا عامًا إلى النتيجة."""
    mistakes = result.get("mistakes", [])

    explained_mistakes = []
    for item in mistakes:
        q_num = item.get("question")
        if q_num is None:
            explained_mistakes.append(item)
            continue

        explanation = build_question_explanation(
            q_num,
            item.get("correct"),
            item.get("student")
        )

        explained_item = dict(item)
        explained_item["topic"] = QUESTION_TOPICS.get(q_num, "الفهم العام")
        explained_item["explanation"] = explanation
        explained_mistakes.append(explained_item)

    result["mistakes"] = explained_mistakes
    result["ai_summary"] = generate_exam_summary(result)
    return result
