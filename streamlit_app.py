import io
import os
import cv2
import pandas as pd
import streamlit as st
from PIL import Image

from omr import grade_exam
from exam_explainer import TRUE_FALSE_LABELS, MCQ_LABELS, QUESTION_TOPICS

# ==========================================
# Page Configuration
# ==========================================
st.set_page_config(
    page_title="نظام التصحيح الآلي للاختبارات | OMR Grader",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# Custom RTL Styling (Arabic First UI)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

    html, body, [class*="css"], .stMarkdown, .stText, div, p, span, h1, h2, h3, h4, h5, h6, button, input {
        font-family: 'Cairo', 'Segoe UI', Tahoma, sans-serif !important;
    }

    /* RTL Container & Main Layout */
    .rtl-content {
        direction: rtl;
        text-align: right;
    }

    /* Hero Header */
    .hero-container {
        background: linear-gradient(135deg, #1E1E2E 0%, #2A2B3D 100%);
        border: 1px solid #3B4252;
        border-radius: 16px;
        padding: 24px 30px;
        margin-bottom: 25px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
        direction: rtl;
        text-align: right;
    }

    .hero-title {
        color: #89B4FA;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .hero-subtitle {
        color: #A6ADC8;
        font-size: 1.05rem;
        line-height: 1.6;
    }

    /* KPI Metric Cards */
    .metric-card {
        background-color: #2A2B3D;
        border-radius: 14px;
        padding: 18px 20px;
        border: 1px solid #3E4256;
        text-align: center;
        box-shadow: 0 4px 14px rgba(0,0,0,0.15);
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-card .metric-val {
        font-size: 2rem;
        font-weight: 800;
        margin: 5px 0;
    }
    .metric-card .metric-lbl {
        color: #A6ADC8;
        font-size: 0.95rem;
        font-weight: 600;
    }

    /* Status Badge */
    .status-badge-pass {
        background: rgba(166, 227, 161, 0.15);
        color: #A6E3A1;
        border: 1px solid #A6E3A1;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }
    .status-badge-fail {
        background: rgba(243, 139, 168, 0.15);
        color: #F38BA8;
        border: 1px solid #F38BA8;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 700;
        display: inline-block;
    }

    /* AI Analysis Callout */
    .ai-box {
        background: linear-gradient(135deg, rgba(137, 180, 250, 0.08) 0%, rgba(166, 227, 161, 0.08) 100%);
        border: 1px solid #89B4FA;
        border-radius: 14px;
        padding: 20px 24px;
        margin: 20px 0;
        direction: rtl;
        text-align: right;
    }
    .ai-box-title {
        color: #89B4FA;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .ai-box-text {
        color: #CDD6F4;
        font-size: 1.05rem;
        line-height: 1.8;
    }

    /* Mistake Card */
    .mistake-item {
        background-color: #242638;
        border-right: 4px solid #F38BA8;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
        direction: rtl;
        text-align: right;
    }

    /* RTL Table fixes */
    div[data-testid="stTable"] table, div[data-testid="stDataFrame"] {
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# Pre-packaged Sample Data (for 1-click demo)
# ==========================================
SAMPLE_KEY_PATH = "true.jpeg"

DEMO_STUDENTS = {
    "طالب 1 (درجة كاملة 100% - ممتاز جدًا)": "WhatsApp Image 2026-07-08 at 10.23.18 PM.jpeg",
    "طالب 2 (درجة 92.50% - 3 أخطاء فقط)": "WhatsApp Image 2026-07-08 at 9.36.59 PM.jpeg",
    "طالب 3 (درجة 62.50% - 15 خطأ)": "WhatsApp Image 2026-07-08 at 10.26.08 PM.jpeg",
}


def main():
    # --- Header Banner ---
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">📝 نظام التصحيح الآلي الهندسي للاختبارات (OMR)</div>
        <div class="hero-subtitle">
            منظومة متطورة تجمع بين <b>الرؤية الحاسوبية (Computer Vision)</b> لتصحيح المنظور واكتشاف الفقرات المظللة، 
            و<b>محرك التحليل التربوي الذكي</b> لتقديم تغذية راجعة مفصلة وشرح لكل خطأ يقع فيه الطالب.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ==========================================
    # Sidebar: Input Sources & Options
    # ==========================================
    with st.sidebar:
        st.markdown('<div class="rtl-content"><h3>⚙️ خيارات الإدخال والتصحيح</h3></div>', unsafe_allow_html=True)

        input_mode = st.radio(
            "اختر مصدر الأوراق:",
            ["نماذج تجريبية جاهزة (بنقرة واحدة)", "رفع صور مخصصة من جهازك"],
            index=0
        )

        key_source = None
        student_source = None

        if input_mode == "نماذج تجريبية جاهزة (بنقرة واحدة)":
            st.info("💡 تم تضمين نماذج أوراق OMR حقيقية لتجربة النظام مباشرة دون الحاجة لرفع ملفات.")
            selected_student_label = st.selectbox(
                "اختر نموذج ورقة الطالب للاختبار:",
                list(DEMO_STUDENTS.keys()),
                index=1
            )
            key_source = SAMPLE_KEY_PATH
            student_source = DEMO_STUDENTS[selected_student_label]

            st.caption(f"ورقة الإجابة النموذجية: `{SAMPLE_KEY_PATH}`")
            st.caption(f"ورقة الطالب المختارة: `{student_source}`")

        else:
            st.markdown('<div class="rtl-content"><p><b>1. ورقة الإجابة النموذجية (Answer Key)</b></p></div>', unsafe_allow_html=True)
            key_file = st.file_uploader(
                "رفع ورقة النموذج",
                type=["jpg", "jpeg", "png", "bmp"],
                key="key_uploader"
            )
            st.markdown('<div class="rtl-content"><p><b>2. ورقة إجابة الطالب (Student Sheet)</b></p></div>', unsafe_allow_html=True)
            student_file = st.file_uploader(
                "رفع ورقة الطالب",
                type=["jpg", "jpeg", "png", "bmp"],
                key="student_uploader"
            )

            if key_file is not None:
                key_source = key_file
            if student_file is not None:
                student_source = student_file

        pass_threshold = st.slider(
            "نسبة النجاح الدنيا (%)",
            min_value=40,
            max_value=90,
            value=50,
            step=5
        )

        st.markdown("---")
        btn_start = st.button("🚀 ابدأ التصحيح الآلي", type="primary", use_container_width=True)

        st.markdown("""
        <div class="rtl-content" style="font-size: 0.85rem; color: #A6ADC8; margin-top: 20px;">
            <b>مميزات النظام:</b><br>
            • كشف تلقائي للحواف وتعديل المنظور 4-Point Transform<br>
            • تصفية الضوضاء وثنائية Otsu التكيفية<br>
            • تظليل بصري ثنائي للدوائر (أخضر/أحمر)<br>
            • دعم كامل للغة العربية والاتجاه من اليمين لليسار RTL
        </div>
        """, unsafe_allow_html=True)

    # ==========================================
    # Main Execution & Results
    # ==========================================
    # Run automatically on first load with demo, or when button clicked
    should_run = btn_start or ("last_result" in st.session_state and input_mode == "نماذج تجريبية جاهزة (بنقرة واحدة)")

    if btn_start or ("last_result" not in st.session_state and key_source and student_source):
        if key_source is None or student_source is None:
            st.warning("⚠️ يرجى اختيار أو رفع ورقة النموذج وورقة الطالب أولاً للمتابعة.")
            return

        with st.spinner("⏳ جاري تشغيل خط المعالجة الهندسية واكتشاف الفقرات..."):
            try:
                result = grade_exam(key_source, student_source)
                st.session_state["last_result"] = result
            except Exception as e:
                st.error(f"❌ حدث خطأ أثناء معالجة الصور: {str(e)}")
                return

    if "last_result" in st.session_state:
        result = st.session_state["last_result"]
        render_results(result, pass_threshold)


def render_results(result, pass_threshold):
    percentage = result.get("percentage", 0.0)
    is_pass = percentage >= pass_threshold
    status_label = "ناجح (PASS)" if is_pass else "راسب (FAIL)"
    badge_class = "status-badge-pass" if is_pass else "status-badge-fail"

    # 1. Top KPI Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">📋 مجموع الأسئلة</div>
            <div class="metric-val" style="color: #89B4FA;">{result.get('total', 40)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">✅ الإجابات الصحيحة</div>
            <div class="metric-val" style="color: #A6E3A1;">{result.get('correct', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">❌ الإجابات الخاطئة</div>
            <div class="metric-val" style="color: #F38BA8;">{result.get('wrong', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">📈 النسبة المئوية</div>
            <div class="metric-val" style="color: #F9E2AF;">{percentage:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-lbl">🎯 نتيجة التقييم</div>
            <div style="margin-top: 10px;"><span class="{badge_class}">{status_label}</span></div>
        </div>
        """, unsafe_allow_html=True)

    # 2. AI Analysis & Summary Card
    if "ai_summary" in result:
        st.markdown(f"""
        <div class="ai-box">
            <div class="ai-box-title">🧠 التحليل الذكي للأداء الأكاديمي</div>
            <div class="ai-box-text">{result['ai_summary']}</div>
        </div>
        """, unsafe_allow_html=True)

    # 3. Computer Vision Studio (Visual Tabs)
    st.markdown('<div class="rtl-content"><h3>🔬 معمل الفحص البصري والهندسي</h3></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "👁️ التظليل والتحليل البصري (Visualized Highlights)",
        "📐 تصحيح المنظور واستخراج الورقة (Warped Sheets)",
        "🖼️ الصور الأصلية المدخلة (Original Images)"
    ])

    with tab1:
        st.markdown('<div class="rtl-content"><p>يتم رسم <b>دوائر خضراء</b> على الإجابات الصحيحة، و<b>دوائر حمراء</b> على مواضع خطأ الطالب مع دائرة خضراء موازية توضح موضع الإجابة النموذجية.</p></div>', unsafe_allow_html=True)
        col_k, col_s = st.columns(2)
        with col_k:
            st.markdown('<div class="rtl-content"><b>ورقة النموذج المظللة (Correct Answer Key)</b></div>', unsafe_allow_html=True)
            if "key_visualized" in result:
                st.image(cv2.cvtColor(result["key_visualized"], cv2.COLOR_BGR2RGB), use_container_width=True)
        with col_s:
            st.markdown('<div class="rtl-content"><b>ورقة الطالب المظللة والمقارنة (Student Sheet)</b></div>', unsafe_allow_html=True)
            if "student_visualized" in result:
                st.image(cv2.cvtColor(result["student_visualized"], cv2.COLOR_BGR2RGB), use_container_width=True)

    with tab2:
        st.markdown('<div class="rtl-content"><p>نتيجة خوارزمية <b>Four-Point Perspective Transform</b> بعد اكتشاف حواف الورقة الأربعة وقصها بحجم موحد (1400x1000 بكسل).</p></div>', unsafe_allow_html=True)
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.markdown('<div class="rtl-content"><b>نموذج الإجابة بعد تصحيح المنظور</b></div>', unsafe_allow_html=True)
            if "key_warped" in result:
                st.image(cv2.cvtColor(result["key_warped"], cv2.COLOR_BGR2RGB), use_container_width=True)
        with col_w2:
            st.markdown('<div class="rtl-content"><b>ورقة الطالب بعد تصحيح المنظور</b></div>', unsafe_allow_html=True)
            if "student_warped" in result:
                st.image(cv2.cvtColor(result["student_warped"], cv2.COLOR_BGR2RGB), use_container_width=True)

    with tab3:
        st.markdown('<div class="rtl-content"><p>الصور الخام قبل دخولها في خوارزميات Canny Edge Detection ومعالجة المنظور.</p></div>', unsafe_allow_html=True)
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown('<div class="rtl-content"><b>الصورة الخام للنموذج</b></div>', unsafe_allow_html=True)
            if "key_image" in result:
                st.image(cv2.cvtColor(result["key_image"], cv2.COLOR_BGR2RGB), use_container_width=True)
        with col_r2:
            st.markdown('<div class="rtl-content"><b>الصورة الخام لورقة الطالب</b></div>', unsafe_allow_html=True)
            if "student_image" in result:
                st.image(cv2.cvtColor(result["student_image"], cv2.COLOR_BGR2RGB), use_container_width=True)

    # 4. Detailed Mistakes & Explanations
    st.markdown("---")
    st.markdown('<div class="rtl-content"><h3>📋 تفاصيل الأخطاء والشرح التربوي الموجه</h3></div>', unsafe_allow_html=True)

    mistakes = result.get("mistakes", [])
    if len(mistakes) == 0:
        st.success("🎉 ما شاء الله! الطالب لم يرتكب أي خطأ، جميع الإجابات مطابقة للنموذج 100%.")
    else:
        st.markdown(f'<div class="rtl-content"><p>تم رصد <b>{len(mistakes)}</b> أخطاء، موضح أدناه التحليل المفصل لكل سؤال والتوجيه المناسب:</p></div>', unsafe_allow_html=True)

        for item in mistakes:
            q_num = item.get("question")
            correct_val = item.get("correct")
            student_val = item.get("student")
            topic = item.get("topic", "الفهم العام")
            explanation = item.get("explanation", "")

            # Formatted labels
            if 1 <= q_num <= 10:
                q_type = "صح / خطأ"
                c_lbl = TRUE_FALSE_LABELS.get(correct_val, str(correct_val))
                s_lbl = TRUE_FALSE_LABELS.get(student_val, str(student_val))
            else:
                q_type = "اختيار من متعدد"
                c_lbl = MCQ_LABELS.get(correct_val, str(correct_val))
                s_lbl = MCQ_LABELS.get(student_val, str(student_val))

            st.markdown(f"""
            <div class="mistake-item">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-weight: 700; color: #89B4FA; font-size: 1.1rem;">السؤال رقم {q_num} ({q_type})</span>
                    <span style="background: #313244; padding: 2px 10px; border-radius: 12px; font-size: 0.85rem; color: #CDD6F4;">المفهوم: {topic}</span>
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="color: #F38BA8; font-weight: 600;">إجابة الطالب: {s_lbl}</span> &nbsp;|&nbsp; 
                    <span style="color: #A6E3A1; font-weight: 600;">الإجابة الصحيحة: {c_lbl}</span>
                </div>
                <div style="color: #A6ADC8; font-size: 0.95rem; line-height: 1.6;">
                    💡 {explanation}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # 5. Full Questions Grid Table
    st.markdown("---")
    st.markdown('<div class="rtl-content"><h3>📊 سجل الإجابات لجميع الأسئلة الـ 40</h3></div>', unsafe_allow_html=True)

    key_answers = result.get("key_answers", {})
    student_answers = result.get("student_answers", {})

    records = []
    for q in range(1, 41):
        k_ans = key_answers.get(q, "-")
        s_ans = student_answers.get(q, "-")

        if 1 <= q <= 10:
            k_lbl = TRUE_FALSE_LABELS.get(k_ans, str(k_ans))
            s_lbl = TRUE_FALSE_LABELS.get(s_ans, str(s_ans))
            category = "صح/خطأ (1-10)"
        else:
            k_lbl = MCQ_LABELS.get(k_ans, str(k_ans))
            s_lbl = MCQ_LABELS.get(s_ans, str(s_ans))
            category = "اختيار من متعدد (11-30)" if q <= 30 else "اختيار من متعدد (31-40)"

        is_corr = (k_ans == s_ans)
        records.append({
            "رقم السؤال": q,
            "القسم": category,
            "إجابة الطالب": s_lbl,
            "الإجابة النموذجية": k_lbl,
            "الحالة": "✅ صحيح" if is_corr else "❌ خطأ",
            "الموضوع المعرفي": QUESTION_TOPICS.get(q, "الفهم العام")
        })

    df_records = pd.DataFrame(records)
    st.dataframe(df_records, use_container_width=True, hide_index=True)

    # 6. Export Options
    st.markdown("---")
    st.markdown('<div class="rtl-content"><h3>📥 تصدير تقرير النتائج</h3></div>', unsafe_allow_html=True)

    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        csv_data = df_records.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📄 تحميل جدول النتائج كملف CSV",
            data=csv_data,
            file_name=f"exam_results_{result.get('percentage', 0):.1f}pct.csv",
            mime="text/csv",
            use_container_width=True
        )

    with exp_col2:
        summary_text = (
            f"تقرير نتائج الاختبار الآلي\n"
            f"=================================\n"
            f"مجموع الأسئلة: {result.get('total', 40)}\n"
            f"الإجابات الصحيحة: {result.get('correct', 0)}\n"
            f"الإجابات الخاطئة: {result.get('wrong', 0)}\n"
            f"النسبة المئوية: {percentage:.2f}%\n"
            f"التقييم: {status_label}\n\n"
            f"التحليل الذكي:\n{result.get('ai_summary', '')}\n\n"
            f"تفاصيل الأخطاء:\n"
        )
        for m in mistakes:
            summary_text += f"- سؤال {m.get('question')}: {m.get('explanation')}\n"

        st.download_button(
            label="📝 تحميل التقرير التحليلي كملف نصي TXT",
            data=summary_text.encode('utf-8-sig'),
            file_name=f"exam_report_{result.get('percentage', 0):.1f}pct.txt",
            mime="text/plain",
            use_container_width=True
        )


if __name__ == "__main__":
    main()
