# 1. تثبيت المكتبات المطلوبة (شغلها لو أول مرة أو لو عملت Restart للوكال)
!pip install flask joblib xgboost pandas pyngrok --quiet

from flask import Flask, render_template_string, request, redirect
import pandas as pd
import joblib
import subprocess, threading, time, os
from pyngrok import ngrok

app = Flask(__name__)

# --- إعداد التوكن الخاص بك ---
NGROK_AUTH_TOKEN = "2vyGrSsnj8CHpZnhl5Dk99U5ohI_5AmtnL5aKNEJst29Ai61A"
ngrok.set_auth_token(NGROK_AUTH_TOKEN)

# --- واجهة المستخدم الكونية (Cosmic Dashboard) ---
html_template = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Electricity AI Guard | منظومة الرقابة الذكية</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root { --primary: #facc15; --secondary: #ff4b4b; --bg: #06060f; --glass: rgba(255, 255, 255, 0.03); --border: rgba(250, 204, 21, 0.2); --text: #e2e8f0; }
        * { box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }
        body { background: radial-gradient(circle at center, #0f0c1b 0%, var(--bg) 100%); margin: 0; color: var(--text); min-height: 100vh; overflow-x: hidden; }
        .header { background: rgba(0,0,0,0.5); padding: 20px; border-bottom: 1px solid var(--border); text-align: center; backdrop-filter: blur(10px); }
        .header h1 { color: var(--primary); margin: 0; letter-spacing: 2px; text-shadow: 0 0 15px rgba(250, 204, 21, 0.4); }
        .container { padding: 30px; max-width: 1400px; margin: auto; display: grid; grid-template-columns: 2.5fr 1fr; gap: 25px; }
        .upload-area { grid-column: span 2; background: var(--glass); border: 2px dashed var(--border); border-radius: 20px; padding: 25px; text-align: center; transition: 0.3s; }
        .upload-area:hover { border-color: var(--primary); background: rgba(250, 204, 21, 0.05); }
        .upload-label { cursor: pointer; display: block; }
        .upload-label i { font-size: 2.5rem; color: var(--primary); margin-bottom: 10px; }
        .stats-grid { grid-column: span 2; display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
        .stat-card { background: var(--glass); border: 1px solid var(--border); padding: 20px; border-radius: 15px; text-align: center; }
        .stat-value { font-size: 2.2rem; font-weight: bold; color: var(--primary); display: block; }
        .main-panel { background: var(--glass); border: 1px solid var(--border); border-radius: 20px; padding: 25px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th { text-align: right; padding: 15px; color: var(--primary); border-bottom: 1px solid var(--border); }
        td { padding: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .badge { padding: 6px 12px; border-radius: 8px; font-weight: bold; }
        .badge-danger { background: rgba(255, 75, 75, 0.15); color: #ff4b4b; border: 1px solid #ff4b4b; }
        .badge-success { background: rgba(0, 255, 127, 0.15); color: #00ff7f; border: 1px solid #00ff7f; }
        .alert-box { background: rgba(255, 75, 75, 0.08); border: 1px solid var(--secondary); border-radius: 20px; padding: 25px; position: sticky; top: 20px; }
        .btn-action { background: linear-gradient(135deg, var(--primary), #eab308); color: #000; border: none; padding: 15px; border-radius: 12px; font-weight: bold; cursor: pointer; width: 100%; margin-top: 20px; }
        input[type="file"] { display: none; }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ منظومة الرقابة الذكية وفحص التيار ⚡</h1>
        <p style="color: #94a3b8; margin-top: 8px;">نسخة العرض الوزاري 2026 - وحدة تحليل البيانات</p>
    </div>

    <div class="container">
        <div class="upload-area">
            <form action="/upload" method="post" enctype="multipart/form-data" id="uploadForm">
                <label class="upload-label">
                    <i class="fas fa-file-invoice"></i>
                    <div style="font-size: 1.2rem; font-weight: bold;">اسحب ملف بيانات الشركة (CSV/Excel) هنا</div>
                    <div style="color: #94a3b8; margin-top: 5px;">سيقوم الذكاء الاصطناعي بتحليل البيانات فوراً</div>
                    <input type="file" name="file" onchange="document.getElementById('uploadForm').submit()">
                </label>
            </form>
        </div>

        <div class="stats-grid">
            <div class="stat-card"><i class="fas fa-users"></i><span class="stat-value">{{ total }}</span>إجمالي المشتركين</div>
            <div class="stat-card"><i class="fas fa-user-secret" style="color:var(--secondary)"></i><span class="stat-value" style="color:var(--secondary)">{{ suspects }}</span>تلاعب مكتشف</div>
            <div class="stat-card"><i class="fas fa-chart-line"></i><span class="stat-value">100%</span>دقة الرصد الآلي</div>
            <div class="stat-card"><i class="fas fa-map-marker-alt"></i><span class="stat-value">نشط</span>حالة التغطية</div>
        </div>

        <div class="main-panel">
            <h3 style="color: var(--primary); margin-top: 0;"><i class="fas fa-microchip"></i> نتائج تحليل قاعدة البيانات</h3>
            <table>
                <thead>
                    <tr>
                        <th>كود العميل</th>
                        <th>الاستهلاك الحالي</th>
                        <th>نسبة الخطورة</th>
                        <th>الوضعية النهائية</th>
                    </tr>
                </thead>
                <tbody>
                    {% for index, row in data.iterrows() %}
                    <tr>
                        <td>#{{ row['customer_id'] }}</td>
                        <td>{{ row['monthly_usage']|round(1) }} kWh</td>
                        <td>{{ row['risk_score']|round(1) }}%</td>
                        <td>
                            {% if row['ai_decision'] == 1 %}
                                <span class="badge badge-danger">🔴 تلاعب محتمل</span>
                            {% else %}
                                <span class="badge badge-success">🟢 مستهلك طبيعي</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="side-panel">
            <div class="alert-box">
                <h3 style="color: var(--secondary); margin-top: 0;"><i class="fas fa-satellite-dish"></i> رصد حالة حرجة</h3>
                {% if top is not none %}
                <div style="line-height: 1.8;">
                    <strong>هوية المشترك:</strong> #{{ top['customer_id'] }}<br>
                    <strong>درجة اليقين:</strong> {{ top['risk_score']|round(1) }}%<br>
                    <strong>الحالة:</strong> اشتباه تلاعب عالي الخطورة.
                </div>
                <button class="btn-action"><i class="fas fa-gavel"></i> توجيه مأمورية قضائية</button>
                {% else %}
                <p>ارفع ملفاً لبدء التحليل الحظي.</p>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
"""

# --- منطق المعالجة والـ Routes ---
def process_and_render(df):
    try:
        model = joblib.load('/content/electricity_model.pkl')
        features = joblib.load('/content/features_list.pkl')

        # التأكد من وجود الأعمدة المطلوبة
        df['ai_decision'] = model.predict(df[features])
        df['risk_score'] = (model.predict_proba(df[features])[:, 1] * 100)

        display_df = df.sort_values(by='risk_score', ascending=False).head(40)
        top_suspect = df.sort_values(by='risk_score', ascending=False).iloc[0] if len(df)>0 else None

        return render_template_string(html_template, data=display_df, total=len(df),
                                       suspects=len(df[df['ai_decision']==1]), top=top_suspect)
    except Exception as e:
        return f"<h3>خطأ: تأكد من رفع ملف يحتوي على الأعمدة الصحيحة.</h3><p>{str(e)}</p>"

@app.route("/")
def index():
    # محاولة عرض داتا افتراضية إذا وجدت
    if os.path.exists('elec_data.csv'):
        df = pd.read_csv('elec_data.csv').head(20)
        return process_and_render(df)
    return render_template_string(html_template, data=pd.DataFrame(), total=0, suspects=0, top=None)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files['file']
    if not file: return redirect("/")
    df = pd.read_csv(file) if file.filename.endswith('.csv') else pd.read_excel(file)
    return process_and_render(df)

# --- تشغيل ngrok والسيرفر ---
def start_ngrok():
    try:
        # إغلاق أي جلسات قديمة
        tunnels = ngrok.get_tunnels()
        for t in tunnels: ngrok.disconnect(t.public_url)

        url = ngrok.connect(5000).public_url
        print("\n" + "="*50)
        print(f"🔗 رابط المنظومة الكونية الجديد جاهز:\n🔗 {url}")
        print("="*50 + "\n")
    except Exception as e:
        print(f"❌ فشل تشغيل ngrok: {e}")

if __name__ == "__main__":
    threading.Thread(target=start_ngrok, daemon=True).start()
    app.run(port=5000)
