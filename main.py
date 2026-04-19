import streamlit as st
import requests
import streamlit.components.v1 as components
import json
import google.generativeai as genai

# --- 1. ПАРАМЕТРЛЕР ---
URL = "https://bjqoazdkiyhrdrfkkgaz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJqcW9hemRraXlocmRyZmtrZ2F6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3NTM4NjIsImV4cCI6MjA4NTMyOTg2Mn0.0t4S6fa9CmYa6WBdDvkVr4V4H91wLx9xLYtcEdriX4I"
TABLE_NAME = "pisa_light_kz"  # Жаңа кесте атауы

# Gemini API кілтін st.secrets-тан алыңыз немесе осында қойыңыз
# Streamlit Cloud-та: Settings > Secrets > GEMINI_API_KEY қосыңыз
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")

st.set_page_config(page_title="PISA: Мұхит түбіндегі жарық", layout="wide", page_icon="🌊")

if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# --- 2. СТИЛЬ (Дизайн) ---
st.markdown("""
    <style>
    * { -webkit-user-select: none; user-select: none; } 
    .stApp { background: linear-gradient(135deg, #e0f7fa 0%, #e1f5fe 100%); }
    .main-title { 
        color: #01579b; 
        text-align: center; 
        font-weight: 800; 
        padding: 20px; 
        border-bottom: 3px solid #0288d1;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .intro-box {
        background: white;
        padding: 25px;
        border-radius: 12px;
        border-left: 6px solid #00acc1;
        margin: 20px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        line-height: 1.7;
    }
    .question-box { 
        background-color: white; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #0288d1; 
        margin-bottom: 15px; 
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .q-number {
        display: inline-block;
        background: #0288d1;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        margin-right: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. GEMINI AI БАҒАЛАУШЫ ---
def evaluate_with_gemini(answers):
    """Gemini API арқылы оқушының жауаптарын тексереді"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""Сен — физика пәнінің тәжірибелі мұғалімісің. PISA форматындағы "Мұхит түбіндегі жарық (оптикалық талшық)" тақырыбына оқушы жауаптарын тексер.

📚 БАҒАЛАУ КРИТЕРИЙЛЕРІ (КІЛТ):

🔹 **1-сұрақ (1 балл)** - Көп таңдаулы:
Дұрыс жауап: **В** (Түсу бұрышы шекті бұрыштан үлкен болуы керек)
Оқушы В деп жазса немесе мағынасын толық ашса — 1 балл, басқа жауап — 0 балл.

🔹 **2-сұрақ (2 балл)** - Талдау:
Толық жауап (2 балл): Кабель майысқанда жарықтың қабырғаға түсу бұрышы өзгереді. Бұрыш кішірейіп, **шекті бұрыштан аз** болады. Нәтижесінде жарық толық іштей шағылмай, **сынып сыртқа шығады**, сигнал жоғалады.
Жартылай жауап (1 балл): "Бұрыш өзгереді, жарық сыртқа шығады" деп жалпылама айтса, бірақ "шекті бұрыш" терминін қолданбаса.
0 балл: Жауап жоқ немесе мүлдем қате.

🔹 **3-сұрақ (2 балл)** - Сыни бағалау:
Толық жауап (2 балл): **ЖОҚ, жұмыс істемейді**. Толық іштей шағылу үшін жарық тығыздығы **көп ортадан аз ортаға** өтуі керек (n1 > n2). Мұнда ішкі су n=1.33 < сыртқы шыны n=1.5. Сондықтан жарық судан шыныға сынып өтіп, сыртқа шашырайды.
Жартылай жауап (1 балл): Тек "Жоқ, судың тығыздығы аз" деп жазса, ережені толық ашпаса.
0 балл: "Иә жұмыс істейді" деп жазса немесе себебін дұрыс түсіндірмесе.

📝 ОҚУШЫНЫҢ ЖАУАПТАРЫ:

**1-сұрақ:** {answers.get('q1', '(жауап жоқ)')}

**2-сұрақ:** {answers.get('q2', '(жауап жоқ)')}

**3-сұрақ:** {answers.get('q3', '(жауап жоқ)')}

⚠️ ТАПСЫРМА:
Әр сұраққа балл қой (критерийлер бойынша). Жалпы балл 5-тен. Содан кейін оқушыға қазақ тілінде достық әрі педагогикалық кері байланыс жаз. Дұрыс жерлерін мақта, қателерін жұмсақ түрде түсіндір.

ТЕК осы JSON форматында жауап қайтар (басқа мәтінсіз, ```json белгілерінсіз):
{{
  "q1_score": 0-1 саны,
  "q2_score": 0-2 саны,
  "q3_score": 0-2 саны,
  "total_score": жалпы балл (0-5),
  "feedback": "Оқушыға арналған толық кері байланыс (әр сұрақ бойынша талдау, мақтау мен ұсыныстар)"
}}"""

        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # JSON-ды тазалау
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        result = json.loads(result_text)
        return result
    except Exception as e:
        return {
            "q1_score": 0,
            "q2_score": 0,
            "q3_score": 0,
            "total_score": 0,
            "feedback": f"⚠️ AI талдау қатесі: {str(e)}. Мұғалім қолмен тексереді."
        }

def send_data(payload):
    headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    return requests.post(f"{URL}/rest/v1/{TABLE_NAME}", json=payload, headers=headers)

# --- 4. НЕГІЗГІ БЕТ ---
st.markdown("<h1 class='main-title'>🌊 PISA ТАПСЫРМАСЫ: «МҰХИТ ТҮБІНДЕГІ ЖАРЫҚ»</h1>", unsafe_allow_html=True)

if st.session_state.submitted:
    st.balloons()
    st.success("🎉 Жауаптарың сәтті қабылданды және AI арқылы тексерілді! Төмендегі іздеу бөлімінен нәтижені біле аласың.")
    if st.button("Қайта бастау 🔄"):
        st.session_state.submitted = False
        st.rerun()
else:
    # Кіріспе мәтін
    st.markdown("""
    <div class='intro-box'>
    <h3>📖 Кіріспе мәтін</h3>
    <p>Бүгінгі таңда біздің үйімізге жоғары жылдамдықты интернет мыс сымдар арқылы емес, 
    <b>оптикалық талшықтар (кабельдер)</b> арқылы келеді. Оптикалық талшық – шашымыздың қалыңдығындай 
    ғана болатын өте жіңішке мөлдір шыны немесе пластик жіп. Интернет ақпараты осы жіптің ішімен 
    жарық сәулесі түрінде мыңдаған шақырымға (тіпті мұхиттардың астымен) секундына 
    <b>300 000 км жылдамдықпен</b> тасымалданады.</p>
    
    <p>Жарық мөлдір шынының ішінен неге сыртқа шығып кетпейді? Оның сыры – кабельдің құрылысында. 
    Кабель екі қабаттан тұрады: <b>ішкі мөлдір өзек</b> (оның оптикалық тығыздығы жоғары) және 
    <b>сыртқы қабықша</b> (оның оптикалық тығыздығы төмен). Жарық сәулесі кабель ішіне белгілі бір 
    бұрышпен жіберіледі де, қабырғаға соғылып, сыртқа шыға алмай, зигзаг тәрізді іштей шағылысып 
    алға қарай жүре береді. Бұл құбылыс физикада <b>толық іштей шағылу</b> деп аталады.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.warning("⚠️ **Нұсқаулық:** Мәтінді мұқият оқып, сұрақтарға толық жауап беріңіз. Басқа терезеге өтпеңіз — анти-чит жүйесі жұмыс істеп тұр!")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("👤 Оқушының аты-жөні:", placeholder="Мысалы: Асқаров Нұрлан")
    with col2:
        s_class = st.selectbox("🏫 Сыныбыңыз:", ["8 А", "8 Б", "8 В", "8 Г", "9 А", "9 Б", "9 В"])

    if name:
        # АНТИ-ЧИТ JS
        components.html(f"""
            <script>
            let isSubmitting = false;
            document.addEventListener("visibilitychange", function() {{
                if (document.hidden && !isSubmitting) {{
                    const payload = {{
                        student_name: "{name}",
                        student_class: "{s_class}",
                        status: "cheated",
                        answers: {{ "lang": "kz" }},
                        ai_feedback: "🚫 ЖҰМЫС ЖОЙЫЛДЫ: Анти-чит жүйесі басқа бетке өткеніңізді анықтады.",
                        score: 0
                    }};
                    fetch('{URL}/rest/v1/{TABLE_NAME}', {{
                        method: 'POST',
                        headers: {{ 'apikey': '{KEY}', 'Authorization': 'Bearer {KEY}', 'Content-Type': 'application/json' }},
                        body: JSON.stringify(payload)
                    }}).then(() => {{ 
                        isSubmitting = true;
                        window.parent.location.reload(); 
                    }});
                }}
            }});
            </script>
        """, height=0)

        with st.form("pisa_light_exam"):
            
            st.markdown("### 📝 СҰРАҚТАР:")

            # 1-сұрақ
            st.markdown("""
            <div class='question-box'>
            <span class='q-number'>1</span><b>Ақпаратты табу (1 балл)</b>
            <p style='margin-top:10px;'>Мәтінге және физикалық біліміңізге сүйене отырып жауап беріңіз: 
            <b>Оптикалық талшықтың ішінде жарық сыртқа шашырап кетпей, тек іште қалуы үшін қандай басты шарт орындалуы керек?</b></p>
            <p><b>А)</b> Түсу бұрышы шекті бұрыштан кіші болуы керек.<br>
            <b>В)</b> Түсу бұрышы шекті бұрыштан үлкен болуы керек.<br>
            <b>С)</b> Ішкі өзектің және сыртқы қабықшаның тығыздығы бірдей болуы керек.<br>
            <b>D)</b> Жарық тек перпендикуляр (90 градус) бағытта түсуі керек.</p>
            </div>
            """, unsafe_allow_html=True)
            q1 = st.radio(
                "Жауабыңызды таңдаңыз:",
                ["А", "В", "С", "D"],
                key="q1",
                horizontal=True,
                index=None
            )

            # 2-сұрақ
            st.markdown("""
            <div class='question-box'>
            <span class='q-number'>2</span><b>Мәселені талдау және түсіндіру (2 балл)</b>
            <p style='margin-top:10px;'>Интернет орнататын мамандарға (инженерлерге) оптикалық кабельді 
            бөлме бұрыштарынан өткізгенде оны қатты бұруға (90 градусқа майыстыруға немесе сындыруға) 
            қатаң тыйым салынады. Егер кабель қатты майысса, интернет сигналы үзіліп қалады. 
            <b>Толық іштей шағылу заңдылығына сүйене отырып, мұның физикалық себебін түсіндіріңіз.</b></p>
            </div>
            """, unsafe_allow_html=True)
            q2 = st.text_area("Сіздің жауабыңыз:", key="q2", height=130, 
                              placeholder="Физикалық ұғымдарды (бұрыш, шекті бұрыш, шағылу, сыну) қолданып түсіндіріңіз...")

            # 3-сұрақ
            st.markdown("""
            <div class='question-box'>
            <span class='q-number'>3</span><b>Сыни бағалау (2 балл)</b>
            <p style='margin-top:10px;'>Жас өнертапқыш жаңа оптикалық талшық жасап шығарғысы келді. 
            Ол кабельдің <b>ішкі өзегін</b> жасау үшін сыну көрсеткіші <b>n = 1.33</b> болатын суды пайдаланды. 
            Ал суды сыртынан қаптап тұратын <b>қабықша</b> ретінде сыну көрсеткіші <b>n = 1.5</b> болатын шыны 
            түтікті қолданды. <b>Өнертапқыштың бұл моделі оптикалық талшық ретінде жұмыс істей ала ма? 
            Неліктен? Жауабыңызды негіздеңіз.</b></p>
            </div>
            """, unsafe_allow_html=True)
            q3 = st.text_area("Сіздің жауабыңыз:", key="q3", height=150,
                              placeholder="Иә/Жоқ деп жауап беріп, физикалық заңдылықпен негіздеңіз...")

            submit_btn = st.form_submit_button("📤 ЖҰМЫСТЫ ТАПСЫРУ ✅", use_container_width=True)

            if submit_btn:
                if not name or len(name) < 3:
                    st.error("❌ Аты-жөніңізді дұрыс жазыңыз!")
                elif q1 is None:
                    st.error("❌ 1-сұраққа жауап таңдаңыз!")
                elif not q2 or len(q2.strip()) < 10:
                    st.error("❌ 2-сұраққа толық жауап жазыңыз!")
                elif not q3 or len(q3.strip()) < 10:
                    st.error("❌ 3-сұраққа толық жауап жазыңыз!")
                else:
                    with st.spinner("🤖 AI жауаптарыңызды тексеруде... Күте тұрыңыз..."):
                        student_answers = {
                            "q1": q1,
                            "q2": q2,
                            "q3": q3
                        }
                        
                        # Gemini арқылы бағалау
                        evaluation = evaluate_with_gemini(student_answers)
                        
                        all_answers = {
                            "lang": "kz",
                            "questions": student_answers,
                            "scores": {
                                "q1": evaluation.get("q1_score", 0),
                                "q2": evaluation.get("q2_score", 0),
                                "q3": evaluation.get("q3_score", 0)
                            }
                        }
                        
                        payload = {
                            "student_name": name,
                            "student_class": s_class,
                            "answers": all_answers,
                            "status": "checked",
                            "score": evaluation.get("total_score", 0),
                            "ai_feedback": evaluation.get("feedback", "Талдау жасалмады.")
                        }
                        
                        resp = send_data(payload)
                        if resp.status_code in [200, 201, 204]:
                            st.session_state.submitted = True
                            st.rerun()
                        else:
                            st.error(f"⚠️ Қате: {resp.text}")

# --- 5. НӘТИЖЕНІ ІЗДЕУ ---
st.markdown("---")
st.markdown("### 🔎 Нәтижеңді тексер")
search_query = st.text_input("Есіміңді жаз (Мысалы: Асқаров):", key="search_input")

if search_query:
    s_headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
    res = requests.get(
        f"{URL}/rest/v1/{TABLE_NAME}?student_name=ilike.*{search_query}*&select=*&order=id.desc",
        headers=s_headers
    )
    
    if res.status_code == 200:
        results = res.json()
        if len(results) > 0:
            for data in results:
                with st.container():
                    st.markdown(f"#### 👤 {data['student_name']} ({data['student_class']})")
                    
                    if data['status'] == 'cheated':
                        st.error("🚫 Жұмыс жойылды: Анти-чит жүйесі іске қосылған.")
                    elif data['status'] == 'pending':
                        st.warning("⏳ Тексерілуде... Күте тұрыңыз.")
                    else:
                        col_score, col_fb = st.columns([1, 3])
                        with col_score:
                            score = data.get('score', 0)
                            st.metric("Жиналған балл", f"{score} / 5")
                            
                            # Балл бойынша баға
                            if score >= 5:
                                st.success("🌟 Өте жақсы!")
                            elif score >= 4:
                                st.info("👍 Жақсы")
                            elif score >= 3:
                                st.info("📘 Қанағаттанарлық")
                            else:
                                st.warning("📖 Қайталау керек")
                            
                            # Жеке сұрақтар бойынша балл
                            if 'scores' in data.get('answers', {}):
                                scores = data['answers']['scores']
                                st.caption(f"1-сұрақ: {scores.get('q1', 0)}/1")
                                st.caption(f"2-сұрақ: {scores.get('q2', 0)}/2")
                                st.caption(f"3-сұрақ: {scores.get('q3', 0)}/2")
                        
                        with col_fb:
                            with st.expander("📝 AI мұғалімнің толық талдауы", expanded=True):
                                st.write(data.get('ai_feedback', 'Талдау жасалуда...'))
                    st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("🔍 Бұл есіммен жұмыс табылмады.")
