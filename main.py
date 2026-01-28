import flet as ft
import requests

# --- БАЗАМЕН БАЙЛАНЫС ---
SUPABASE_URL = "https://iuqdbdvmbewaedgydaah.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1cWRiZHZtYmV3YWVkZ3lkYWFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkzMjE5ODgsImV4cCI6MjA4NDg5Nzk4OH0.a_PPVZWcA3qOfT4cNaXNE_a3xuSv0CHyrY8LbTgjWww" 

def send_to_db(data):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    try:
        res = requests.post(f"{SUPABASE_URL}/rest/v1/physics_scores", json=data, headers=headers)
        return res.status_code
    except:
        return 500

def main(page: ft.Page):
    page.title = "Физика Порталы"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = "adaptive"
    page.window_width = 400
    page.window_height = 700

    # Оқушы мәліметтері
    name_input = ft.TextField(label="Аты-жөніңіз")
    class_select = ft.Dropdown(
        label="Сыныбыңыз",
        options=[ft.dropdown.Option("9 А"), ft.dropdown.Option("9 Б"), ft.dropdown.Option("9 В")]
    )
    pin_input = ft.TextField(label="PIN код", password=True, can_reveal_password=True)

    test_container = ft.Column(visible=False)
    q1 = ft.RadioGroup(content=ft.Column([
        ft.Radio(value="v = s/t", label="v = s/t"),
        ft.Radio(value="v = m/g", label="v = m/g"),
        ft.Radio(value="v = a*t", label="v = a*t")
    ]))
    q3 = ft.TextField(label="Еркін түсу үдеуі (g) нешеге тең?")

    def on_submit(e):
        payload = {
            "student_name": name_input.value,
            "student_class": class_select.value,
            "test_name": "BJB_1_Kinematika",
            "answers": {"q1": q1.value, "q3": q3.value},
            "status": "pending"
        }
        status = send_to_db(payload)
        if status in [200, 201]:
            page.clean()
            page.add(ft.Text("🎉 Жұмыс қабылданды!", size=30, weight="bold", color="green"))
            page.add(ft.Text("Нәтижені кейін көре аласыз."))
            page.update()

    def check_pin(e):
        if pin_input.value == "1111":
            test_container.visible = True
            login_card.visible = False
            page.update()
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Қате PIN!"))
            page.snack_bar.open = True
            page.update()

    login_card = ft.Column([
        ft.Text("🪐 Физика: Кіру", size=30, weight="bold"),
        name_input, class_select, pin_input,
        ft.ElevatedButton("Тестті ашу", on_click=check_pin)
    ])

    test_container.controls = [
        ft.Text("БЖБ №1: Кинематика", size=22, weight="bold"),
        ft.Text("1. Жылдамдықтың формуласы:"), q1,
        ft.Text("2. Еркін түсу үдеуі:"), q3,
        ft.ElevatedButton("Жіберу", on_click=on_submit, bgcolor="blue", color="white")
    ]

    page.add(login_card, test_container)

ft.app(target=main)