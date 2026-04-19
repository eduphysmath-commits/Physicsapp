import streamlit as st
import requests
import streamlit.components.v1 as components
import json
import google.generativeai as genai

# --- 1. ПАРАМЕТРЛЕР ---
URL = "https://bjqoazdkiyhrdrfkkgaz.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJqcW9hemRraXlocmRyZmtrZ2F6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk3NTM4NjIsImV4cCI6MjA4NTMyOTg2Mn0.0t4S6fa9CmYa6WBdDvkVr4V4H91wLx9xLYtcEdriX4I"
TABLE_NAME = "pisa_light_kz"

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")

st.set_page_config(page_title="PISA: Мұхит түбіндегі жарық", layout="wide", page_icon="🌊")

if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'last_result' not in st.session_state:
    st.session_state.last_result = None

# --- 2. СТИЛЬ ---
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
    .result-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        margin: 15px 0;
        border-top: 5px solid #0288d1;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. GEMINI AI БАҒАЛАУШЫ (ҚАТАЛ СТИЛЬ) ---
def evaluate_with_gemini(answers):
    """Gemini API арқылы 3 сұрақты бір промптпен тексереді"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""Сен физика пәнінің қатал, бірақ әділ сарапшы мұғалімісің.
Сенің міндетің — 8-сынып оқушысының PISA форматындағы "Мұхит түбіндегі жарық (оптикалық талшық)" тақырыбына берген 3 жауабын тексеру.

═══════════════════════════════════════════
📌 1-СҰРАҚ (Максимум 1 балл) — Көп таңдаулы
═══════════════════════════════════════════
Сұрақ: "Оптикалық талшықтың ішінде жарық сыртқа шашырап кетпей, тек іште қалуы үшін қандай басты шарт орындалуы керек?"
Дұрыс жауап кілті: **В** (Түсу бұрышы шекті бұрыштан үлкен болуы керек)

Бағалау критерийлері:
- 1 балл: Жауап "В" немесе "B" болса
- 0 балл: Басқа жауап (А, С, D)

Оқушының жауабы: {answers.get('q1', '(жауап жоқ)')}

═══════════════════════════════════════════
📌 2-СҰРАҚ (Максимум 2 балл) — Талдау
═══════════════════════════════════════════
Сұрақ: "Оптикалық кабельді қатты майыстырғанда интернет неге үзіледі?"
Дұрыс жауап кілті: Жарықтың түсу бұрышы кішірейіп, шекті бұрыштан аз болып қалады. Толық іштей шағылу орындалмай, жарық сыртқа шығып кетеді.

Бағалау критерийлері:
- 2 балл: "Түсу бұрышы", "шекті бұрыш" терминдерін қолданып, толық логикалық тізбек құрса.
- 1 балл: Логикасы дұрыс, бірақ физикалық терминдері жеткіліксіз болса.
- 0 балл: Жауап қате немесе тақырыпқа сай емес.

Оқушының жауабы: {answers.get('q2', '(жауап жоқ)')}

═══════════════════════════════════════════
📌 3-СҰРАҚ (Максимум 2 балл) — Сыни бағалау
═══════════════════════════════════════════
Сұрақ: "Ішкі өзегі су (n=1.33), сыртқы қабықшасы шыны (n=1.5) болатын оптикалық талшық жұмыс істей ме?"
Дұрыс жауап кілті: ЖОҚ, жұмыс істемейді. Толық іштей шағылу үшін жарық тығыздығы көп ортадан аз ортаға өтуі керек (n1 > n2). Мұнда керісінше: ішкі n=1.33 < сыртқы n=1.5. Сондықтан жарық судан шыныға сынып өтіп, сыртқа шашырайды.

Бағалау критерийлері:
- 2 балл: "Жоқ" деп жауап беріп, n1 > n2 шартын немесе "тығыздығы көп ортадан аз ортаға" ережесін нақты түсіндірсе.
- 1 балл: "Жоқ, себебі судың тығыздығы аз" деп жалпылама айтса, ережені толық ашпаса.
- 0 балл: "Иә жұмыс істейді" деп жазса немесе мүлдем қате негіздеме берсе.

Оқушының жауабы: {answers.get('q3', '(жауап жоқ)')}

═══════════════════════════════════════════
⚠️ ТАПСЫРМА:
Әр сұраққа әділ балл қой. Жалпы максимум — 5 балл.
Қатал, бірақ мотивация беретін қазақ тіліндегі кері байланыс жаз.

Нәтижені ТЕК ҚАНА мынадай JSON форматында қайтар (ешқандай қосымша мәтінсіз, ```json белгілерінсіз):
{{
  "q1_score": (0 немесе 1),
  "q2_score": (0, 1 немесе 2),
  "q3_score": (0, 1 немесе 2),
  "total_score": (жалпы балл, 0-5),
  "q1_feedback": "1-сұрақ бойынша қысқаша түсінік (1-2 сөйлем)",
  "q2_feedback": "2-сұрақ бойынша қысқаша түсінік (2-3 сөйлем, қате болса дұрысын көрсет)",
  "q3_feedback": "3-сұрақ бойынша қысқаша түсінік (2-3 сөйлем, қате болса дұрысын көрсет)",
  "general_feedback": "Оқушыға жалпы мотивация беретін қысқа қорытынды (1-2 сөйлем)"
}}"""

        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
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
            "q1_feedback": "AI қатесі",
            "q2_feedback": "AI қатесі",
            "q3_feedback": "AI қатесі",
            "general_feedback": f"⚠️ AI талдау қатесі: {str(e)}. Мұғалім қолмен тексереді."
        }

def send_data(payload):
    headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    try:
        return requests.post(f"{URL}/rest/v1/{TABLE_NAME}", json=payload, headers=headers, timeout=10)
    except Exception as e:
        return None

# --- 4. НЕГІЗГІ БЕТ ---
st.markdown("<h1 class='main-title'>🌊 PISA ТАПСЫРМАСЫ: «МҰХИТ ТҮБІНДЕГІ ЖАРЫҚ»</h1>", unsafe_allow_html=True)

# ========== НӘТИЖЕ КӨРІНЕТІН БЕТ ==========
if st.session_state.submitted and st.session_state.last_result:
    result = st.session_state.last_result
    total = result.get('total_score', 0)
    
    st.balloons()
    
    st.markdown("<div class='result-card'>", unsafe_allow_html=True)
    st.markdown("## 🎉 Жауаптарың тексерілді!")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("📊 Жиналған балл", f"{total} / 5")
        
        if total >= 5:
            st.success("🌟 Өте жақсы!")
        elif total >= 4:
            st.success("👍 Жақсы!")
        elif total >= 3:
            st.info("📘 Қанағаттанарлық")
        elif total >= 2:
            st.warning("📖 Орташа, қайталау керек")
        else:
            st.error("⚠️ Тақырыпты қайта оқу керек")
    
    with col2:
        st.markdown("### 💬 Жалпы кері байланыс:")
        st.info(result.get('general_feedback', ''))
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("### 📝 Әр сұрақ бойынша талдау:")
    
    # 1-сұрақ
    q1_score = result.get('q1_score', 0)
    with st.expander(f"📌 1-сұрақ: {q1_score}/1 балл", expanded=True):
        if q1_score == 1:
            st.success(f"✅ {result.get('q1_feedback', '')}")
        else:
            st.error(f"❌ {result.get('q1_feedback', '')}")
    
    # 2-сұрақ
    q2_score = result.get('q2_score', 0)
    with st.expander(f"📌 2-сұрақ: {q2_score}/2 балл", expanded=True):
        if q2_score == 2:
            st.success(f"✅ {result.get('q2_feedback', '')}")
        elif q2_score == 1:
            st.warning(f"⚠️ {result.get('q2_feedback', '')}")
        else:
            st.error(f"❌ {result.get('q2_feedback', '')}")
    
    # 3-сұрақ
    q3_score = result.get('q3_score', 0)
    with st.expander(f"📌 3-сұрақ: {q3_score}/2 балл", expanded=True):
        if q3_score == 2:
            st.success(f"✅ {result.get('q3_feedback', '')}")
        elif q3_score == 1:
            st.warning(f"⚠️ {result.get('q3_feedback', '')}")
        else:
            st.error(f"❌ {result.get('q3_feedback', '')}")
    
    st.markdown("---")
    if st.button("🔄 Қайта бастау", use_container_width=True):
        st.session_state.submitted = False
        st.session_state.last_result = None
        st.rerun()

# ========== ТАПСЫРМА БЕТІ ==========
else:
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
                    st.error("❌ 2-сұраққа толық жауап жазыңыз (кем дегенде 10 әріп)!")
                elif not q3 or len(q3.strip()) < 10:
                    st.error("❌ 3-сұраққа толық жауап жазыңыз (кем дегенде 10 әріп)!")
                else:
                    with st.spinner("🤖 AI-сарапшы жауаптарыңызды мұқият тексеруде... 15 секунд күте тұрыңыз..."):
                        student_answers = {
                            "q1": q1,
                            "q2": q2,
                            "q3": q3
                        }
                        
                        evaluation = evaluate_with_gemini(student_answers)
                        
                        # Нәтижені session-ге сақтау (бірден көрсету үшін)
                        st.session_state.last_result = evaluation
                        
                        all_answers = {
                            "lang": "kz",
                            "questions": student_answers,
                            "scores": {
                                "q1": evaluation.get("q1_score", 0),
                                "q2": evaluation.get("q2_score", 0),
                                "q3": evaluation.get("q3_score", 0)
                            }
                        }
                        
                        full_feedback = f"""📊 ЖАЛПЫ БАЛЛ: {evaluation.get('total_score', 0)}/5

💬 {evaluation.get('general_feedback', '')}

─────────────────
📌 1-сұрақ ({evaluation.get('q1_score', 0)}/1): {evaluation.get('q1_feedback', '')}

📌 2-сұрақ ({evaluation.get('q2_score', 0)}/2): {evaluation.get('q2_feedback', '')}

📌 3-сұрақ ({evaluation.get('q3_score', 0)}/2): {evaluation.get('q3_feedback', '')}"""
                        
                        payload = {
                            "student_name": name,
                            "student_class": s_class,
                            "answers": all_answers,
                            "status": "checked",
                            "score": evaluation.get("total_score", 0),
                            "ai_feedback": full_feedback
                        }
                        
                        # Supabase-ке жіберу (қате болса да нәтижені көрсетеміз)
                        send_data(payload)
                        st.session_state.submitted = True
                        st.rerun()

# --- 5. НӘТИЖЕНІ ІЗДЕУ ---
st.markdown("---")
st.markdown("### 🔎 Бұрынғы нәтижелерді іздеу")
search_query = st.text_input("Есімді жазыңыз (Мысалы: Асқаров):", key="search_input")

if search_query:
    s_headers = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
    try:
        res = requests.get(
            f"{URL}/rest/v1/{TABLE_NAME}?student_name=ilike.*{search_query}*&select=*&order=id.desc",
            headers=s_headers,
            timeout=10
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
                                
                                if 'scores' in data.get('answers', {}):
                                    scores = data['answers']['scores']
                                    st.caption(f"1-сұрақ: {scores.get('q1', 0)}/1")
                                    st.caption(f"2-сұрақ: {scores.get('q2', 0)}/2")
                                    st.caption(f"3-сұрақ: {scores.get('q3', 0)}/2")
                            
                            with col_fb:
                                with st.expander("📝 AI сарапшының толық талдауы", expanded=True):
                                    st.write(data.get('ai_feedback', 'Талдау жасалуда...'))
                        st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.info("🔍 Бұл есіммен жұмыс табылмады.")
    except Exception as e:
        st.warning(f"⚠️ Іздеу уақытша қолжетімсіз.")
