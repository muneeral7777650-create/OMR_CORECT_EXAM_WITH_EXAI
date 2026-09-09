# 📝 نظام التصحيح الآلي للاختبارات (OMR Grader & AI Explainer)

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green.svg)](https://opencv.org/)
[![RTL Arabic](https://img.shields.io/badge/Arabic-RTL%20Supported-purple.svg)](#)

نظام هندسي متكامل للتصحيح الآلي لأوراق الإجابة المظللة (**OMR - Optical Mark Recognition**) مدعوم بخوارزميات **الرؤية الحاسوبية (Computer Vision)** للكشف التلقائي عن حواف الورقة وتعديل المنظور، مع **محرك شرح وتحليل تربوي ذكي** لتوجيه الطلاب وتوضيح المفاهيم التي تتطلب مراجعة.

يدعم المشروع واجهتين متكاملتين:
1. **واجهة ويب تفاعلية حديثة بـ Streamlit** جاهزة للنشر السحابي، مع دعم كامل للغة العربية واتجاه اليمين لليسار (RTL).
2. **واجهة سطح مكتب (Desktop GUI)** مبنية بـ Tkinter مع معالجة وتشكيل متقدم للخط العربي ثنائي الاتجاه.

---

## ✨ المميزات الرئيسية (Key Features)

- **اكتشاف وتصحيح المنظور (4-Point Perspective Transform):** تعديل ميلان الورقة واقتصاصها تلقائياً بدقة هندسية عالية (1400×1000 بكسل).
- **العتبة التكيفية (Adaptive Otsu Thresholding):** قراءة دقيقة للفقرات المظللة مع عزل الظلال والإضاءة غير المتساوية.
- **التظليل البصري المقارن (Visual Inspection Studio):** رسم دوائر خضراء على الإجابات النموذجية، ودوائر حمراء على مواضع خطأ الطالب مع دائرة خضراء موازية لموضع الإجابة الصحيحة.
- **الشرح والتحليل التربوي الذكي:** تشخيص فوري لنقاط الضعف الأكاديمية وتقديم نصائح مخصصة لكل سؤال خاطئ.
- **نماذج تجريبية جاهزة بنقرة واحدة (1-Click Demo):** إمكانية تجربة النظام على Streamlit Cloud مباشرة دون الحاجة لرفع ملفات مسبقاً.
- **تصدير التقارير:** إمكانية تنزيل سجل النتائج لجميع الأسئلة الـ 40 بصيغة CSV أو ملف تقرير نصي TXT.

---

## 📁 هيكلية المشروع (Project Structure)

```text
omr_corect_exam/
├── streamlit_app.py        # التطبيق الرئيسي لواجهة الويب عبر Streamlit
├── app.py                  # نقطة دخول بديلة لتشغيل Streamlit
├── main.py                 # نقطة الدخول لتشغيل واجهة سطح المكتب (Tkinter)
├── gui.py                  # واجهة سطح المكتب مع دعم تشكيل الخط العربي
├── omr.py                  # خط معالجة واستخراج إجابات OMR والمقارنة
├── image_processing.py     # خوارزميات الرؤية الحاسوبية وتصحيح المنظور
├── exam_explainer.py       # محرك التحليل التربوي وتوليد الشروحات الذكية
├── requirements.txt        # متطلبات الحزم للمشروع وStreamlit Cloud
├── packages.txt            # مكتبات نظام لينكس المطلوبة على السحابة
├── .streamlit/
│   └── config.toml         # إعدادات المظهر والسمة الداكنة لـ Streamlit
├── .gitignore              # استبعاد الملفات المؤقتة وبيئة العمل
├── true.jpeg               # ورقة الإجابة النموذجية المرجعية
├── WhatsApp Image ...jpeg  # نماذج أوراق إجابة لطلاب بنسب مختلفة
└── README.md               # التوثيق الشامل للمشروع
```

---

## 🚀 التشغيل المحلي (Local Quickstart)

### 1. تثبيت المتطلبات:
تأكد من وجود Python 3.10+ ثم قم بتثبيت الحزم:
```bash
pip install -r requirements.txt
```

### 2. تشغيل واجهة الويب (Streamlit):
```bash
streamlit run streamlit_app.py
```
> أو يمكنك استخدام: `streamlit run app.py`

سيفتح المتصفح تلقائياً على الرابط: `http://localhost:8501`.

### 3. تشغيل واجهة سطح المكتب (Desktop Tkinter):
```bash
python main.py
```

---

## ☁️ خطوات النشر على Streamlit Community Cloud

تم تجهيز هذا المشروع ليكون قابلاً للنشر على منصة **Streamlit Cloud** مجاناً في دقيقة واحدة:

1. **ارفع المشروع إلى GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: OMR Grader with RTL Arabic and Streamlit App"
   git branch -M main
   git remote add origin https://github.com/USERNAME/REPO_NAME.git
   git push -u origin main
   ```

2. **توجه إلى موقع Streamlit Cloud:**
   - افتح [share.streamlit.io](https://share.streamlit.io) وسجل الدخول بحساب GitHub الخاص بك.

3. **أنشئ تطبيقاً جديداً (New App):**
   - **Repository:** اختر مستودعك.
   - **Branch:** `main`.
   - **Main file path:** `streamlit_app.py` (أو `app.py`).

4. **اضغط على "Deploy!":**
   - سيتولى Streamlit Cloud تثبيت الحزم المحددة في `requirements.txt` و `packages.txt` وتشغيل التطبيق فوراً برابط عام يمكنك مشاركته مع أي شخص!

---

## 🛠️ تفاصيل المعالجة الهندسية للخط العربي (Arabic RTL Handling)

- **في واجهة Streamlit:** تم تضمين دعم اتجاه الكتابة من اليمين لليسار (`dir="rtl"`) مع خط `Cairo` المتوافق، مستفيدين من محركات المتصفح الحديثة التي تدعم Unicode BiDi تلقائياً.
- **في واجهة Tkinter:** تم تضمين مكتبتي `arabic_reshaper` و `python-bidi` مع دالة التفاف أسطر مسبقة (`textwrap`) لضمان ربط الحروف العربية وعدم ظهورها مجزأة أو معكوسة في مربعات النصوص المكتبية.

---

## 📄 الترخيص (License)
هذا المشروع مفتوح المصدر ومتاح للاستخدام الأكاديمي والتعليمي.
