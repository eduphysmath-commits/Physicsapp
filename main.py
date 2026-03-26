import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image
import time

# --- 1. ПАРАМЕТРЛЕР ---
URL = "https://eytvntwumnptjddlsarg.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV5dHZudHd1bW5wdGpkZGxzYXJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk4ODgzNzgsImV4cCI6MjA4NTQ2NDM3OH0.zBn48hYdDVvuzE3ZBg86L8_-XNl7ikCGA4lK7yUJW20"

headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

st.set_page_config(page_title="Нәтижелер тақтасы", layout="wide", page_icon="📊")

# --- 2. СТИЛЬ (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .student-card { padding: 10px; border-radius: 5px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. БАЗАМЕН ЖҰМЫС ФУНКЦИЯЛАРЫ ---
def get_exams():
    res = requests.get(f"{URL}/rest/v1/exams?order=id.desc&select=*", headers=headers)
    return res.json() if res.status_code == 200 else []

def get_submissions_by_exam(exam_id):
    res = requests.get(f"{URL}/rest/v1/submissions?exam_id=eq.{exam_id}&order=created_at.desc&select=*", headers=headers)
    return res.json() if res.status_code == 200 else []

def update_submission_score(sub_id, new_score, teacher_feedback):
    payload = {"score": new_score, "ai_feedback": teacher_feedback, "status": "done"}
    res = requests.patch(f"{URL}/rest/v1/submissions?id=eq.{sub_id}", json=payload, headers=headers)
    return res.status_code in [200, 204]

# --- 4. НЕГІЗГІ ИНТЕРФЕЙС ---
st.title("📊 Мұғалім кабинеті: Нәтижелер тақтасы")
st.write("Бұл парақшада тек оқушылардың тапсырған жұмыстарын көріп, бағалауға болады.")
st.write("---")

exams_list = get_exams()

if exams_list:
    exam_options = {exam['title']: exam['id'] for exam in exams_list}
    selected_exam_result = st.selectbox("Қай ТЖБ-ның нәтижесін көргіңіз келеді?", list(exam_options.keys()))
    res_exam_id = exam_options[selected_exam_result]
    
    st.info(f"**Оқушыларға жіберілетін сілтеме (көшіріп алу үшін):**\n`https://sizdin-sayt.streamlit.app/?exam_id={res_exam_id}`")
    
    submissions = get_submissions_by_exam(res_exam_id)
    
    if submissions:
        for sub in submissions:
            if sub['status'] == 'cheated':
                status_emoji = "🚫"
            elif sub['status'] == 'done':
                status_emoji = "✅"
            else:
                status_emoji = "⏳"
                
            with st.expander(f"{status_emoji} {sub['student_name']} ({sub['student_class']}) - Қазіргі балл: {sub.get('score', 0)}"):
                st.write(f"**Пин-код:** {sub.get('pin_code')}")
                
                if sub['status'] == 'cheated':
                    st.error("🚫 БҰЛ ОҚУШЫ АНТИ-ЧИТ ЖҮЙЕСІНЕ ТҮСТІ! Емтихан кезінде басқа терезеге өтіп кеткен.")
                
                st.write("**📝 Оқушының жауаптары:**")
                answers_data = sub.get('answers', {})
                
                # Базадан келген жауап JSON (dict) форматында болса ғана оқимыз
                if isinstance(answers_data, dict):
                    # 1. Текст түріндегі жауаптар
                    if 'questions' in answers_data:
                        for k, v in answers_data.get('questions', {}).items():
                            st.markdown(f"- **{k}-сұрақ:** {v}")
                    
                    # 2. Тікелей URL сілтеме 
                    if answers_data.get('image_url'):
                        st.write("**📸 Жүктелген сурет (URL):**")
                        st.image(answers_data['image_url'], width=500)
                    
                    # 3. Ескі форматтағы Base64 суреттер
                    images = answers_data.get('images_base64', [])
                    if images:
                        st.write("**📸 Жүктелген/Түсірілген суреттер:**")
                        for img_b64 in images:
                            try:
                                st.image(Image.open(BytesIO(base64.b64decode(img_b64))), width=500)
                            except Exception:
                                st.error("Суретті ашу мүмкін болмады немесе форматы қате.")
                
                st.write("---")
                st.markdown("**✍️ Бағалау және Кері байланыс**")
                col_score, col_btn = st.columns([3, 1])
                
                with col_score:
                    new_score = st.number_input("Қорытынды балл:", value=sub.get('score', 0), key=f"score_update_{sub['id']}")
                    new_feedback = st.text_area("Мұғалімнің пікірі:", value=sub.get('ai_feedback', ''), key=f"feedback_update_{sub['id']}")
                
                with col_btn:
                    st.write("") 
                    st.write("")
                    if st.button("Бағаны бекіту ✅", key=f"btn_update_{sub['id']}", use_container_width=True):
                        if update_submission_score(sub['id'], new_score, new_feedback):
                            st.success("Сақталды!")
                            time.sleep(1) 
                            st.rerun()
    else:
        st.info("Бұл ТЖБ бойынша әзірге ешқандай оқушы жұмыс тапсырған жоқ.")
else:
    st.warning("⚠️ Базада ешқандай ТЖБ табылған жоқ. Алдымен 'exams' кестесіне ТЖБ тақырыптарын қосыңыз.")