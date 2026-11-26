# diet_app.py  (version 9)  - run with:  streamlit run diet_app.py
# 5 pages: Home, Add Food, My Day, Progress, Profile. Invite-code lock first.
import csv
import json
import os
import time
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

APP_NAME = "MuscleUp"   # <- change the app name here (one place only)
LOGO_FILE = "logo.png"  # put logo.png in the same folder as this file

st.set_page_config(page_title=APP_NAME, page_icon="💪", layout="centered")

# ------------------------------------------------------------- splash screen
if "splash_done" not in st.session_state:
    st.session_state.splash_done = False

if not st.session_state.splash_done:
    st.markdown(
        "<style>.block-container{padding-top:18vh;}</style>",
        unsafe_allow_html=True,
    )
    splash = st.empty()
    with splash.container():
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), LOGO_FILE)
        shown = False
        try:
            if os.path.exists(logo_path):
                left, mid, right = st.columns([1, 2, 1])
                mid.image(logo_path, use_container_width=True)
                shown = True
        except Exception:
            shown = False
        if not shown:
            st.markdown(
                "<div style='text-align:center;font-size:110px;line-height:1.1'>💪</div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            "<div style='text-align:center;font-size:40px;font-weight:800'>%s</div>" % APP_NAME,
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='text-align:center;color:gray;margin-top:10px'>Loading...</div>",
            unsafe_allow_html=True,
        )
    time.sleep(2.7)
    splash.empty()
    st.session_state.splash_done = True

# ---------------------------------------------------------------- invite lock
DEFAULT_CODES = ["FITNESS123"]


def get_codes():
    codes = list(DEFAULT_CODES)
    try:
        extra = st.secrets["invite_codes"]
        if isinstance(extra, str):
            extra = [extra]
        codes += [str(c) for c in extra]
    except Exception:
        pass
    return [c.strip().upper() for c in codes if str(c).strip()]


if "unlocked" not in st.session_state:
    st.session_state.unlocked = False

def read_key_param():
    try:
        v = st.query_params.get("key", "")
        if isinstance(v, (list, tuple)):
            v = v[0] if v else ""
        return str(v).strip().upper()
    except Exception:
        return ""


def write_key_param(code):
    try:
        st.query_params["key"] = code
    except Exception:
        pass  # old Streamlit: just remember for this session


if not st.session_state.unlocked:
    saved_key = read_key_param()
    if saved_key and saved_key in get_codes():
        st.session_state.unlocked = True

if not st.session_state.unlocked:
    st.title("🔒 " + APP_NAME)
    st.write("This app is invite only. Type your invite code.")
    code = st.text_input("Invite code", type="password")
    if st.button("Open the app", use_container_width=True):
        if code.strip().upper() in get_codes():
            st.session_state.unlocked = True
            write_key_param(code.strip().upper())
            st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()
        else:
            st.error("Wrong code. Ask your friend for the right code.")
    st.stop()

# ------------------------------------------------------------- food database
# name | kcal per 100g | protein per 100g | units (unit=grams) | aliases
FOOD_TEXT = """
Egg boiled|155|13|piece=50|egg,eggs,boiled egg,anda
Egg white|52|11|piece=33|egg whites
Omelette (1 egg)|154|11|piece=60|omelet,omlette
Egg bhurji|190|12|plate=150,cup=120|anda bhurji,scrambled egg
Egg curry|130|8|bowl=200,cup=200|anda curry
Chicken breast cooked|165|31|piece=120,plate=150|chicken breast,chicken
Chicken curry|150|14|bowl=200,cup=200,plate=250|chicken gravy
Chicken fry|250|22|piece=80,plate=150|fried chicken
Tandoori chicken|190|25|piece=120,plate=200|chicken tandoori
Chicken tikka|180|24|piece=30,plate=150|tikka
Grilled chicken|165|27|piece=100,plate=150|
Chicken leg piece|215|24|piece=100|chicken leg
Chicken 65|260|20|plate=150,piece=25|
Chicken biryani|180|9|plate=300,cup=180|biryani,chicken biriyani
Egg biryani|170|7|plate=300,cup=180|
Veg biryani|150|3.5|plate=300,cup=180|vegetable biryani
Mutton biryani|200|10|plate=300,cup=180|
Mutton curry|190|16|bowl=200,cup=200|mutton
Fish fry|230|20|piece=80,plate=150|fish
Fish curry|140|15|bowl=200,cup=200|
Prawns curry|120|14|bowl=200|prawn,shrimp
Rice cooked|130|2.7|plate=250,cup=160,bowl=200|white rice,rice,anna,annam
Brown rice cooked|112|2.3|plate=250,cup=160|
Curd rice|120|3.5|plate=250,cup=200|mosaranna,thayir sadam
Lemon rice|160|3|plate=250,cup=200|chitranna
Tomato rice|150|3|plate=250,cup=200|tomato bath
Bisibele bath|140|4|plate=250,cup=200|bisi bele bath
Vangi bath|160|3|plate=250,cup=200|
Pulao|150|3|plate=250,cup=180|pulav,pulaov
Jeera rice|150|3|plate=250,cup=180|
Fried rice veg|165|4|plate=300,cup=180|fried rice
Egg fried rice|180|6|plate=300,cup=180|
Chicken fried rice|185|8|plate=300,cup=180|
Khichdi|120|4|plate=250,bowl=200|
Pongal|140|4|plate=250,cup=200|ven pongal
Roti|297|9|piece=40|chapati,chapathi,phulka
Chapati with oil|330|8|piece=45|
Paratha plain|300|7|piece=80|
Aloo paratha|260|6|piece=110|
Paneer paratha|280|9|piece=110|
Naan|290|9|piece=90|
Butter naan|330|9|piece=100|
Puri|350|7|piece=30|poori
Bhatura|330|8|piece=80|
Dosa plain|168|4|piece=100|dose,dosai
Masala dosa|190|4|piece=180|
Egg dosa|190|8|piece=130|
Rava dosa|180|4|piece=100|
Set dosa|170|4|piece=60|
Neer dosa|130|2.5|piece=50|
Idli|130|4|piece=40|idly
Vada medu|260|8|piece=50|vade,medu vada
Upma|130|3|plate=200,cup=200|uppittu
Poha|130|3|plate=200,cup=180|avalakki
Uttapam|180|5|piece=120|
Ragi mudde|118|2.5|piece=150,ball=150|ragi ball,ragi balls,ragi
Ragi dosa|150|3.5|piece=90|
Ragi roti|180|4|piece=60|
Jowar roti|190|5|piece=50|jolada rotti
Akki roti|200|4|piece=70|
Dal cooked|110|7|bowl=200,cup=200,plate=250|dal tadka,toor dal,dhal,sambar dal
Dal fry|130|7|bowl=200,cup=200|
Moong dal cooked|105|7|bowl=200,cup=200|
Rajma curry|120|6|bowl=200,cup=200|rajma
Chole|140|7|bowl=200,cup=200|chana masala,chickpea curry
Sambar|60|3|bowl=200,cup=200|saaru
Rasam|30|1|bowl=200,cup=200|
Palak dal|100|6|bowl=200|
Sprouts|110|9|bowl=100,cup=100|moong sprouts
Boiled chana|164|9|cup=160,bowl=100|chickpeas,kala chana
Soya chunks cooked|135|16|cup=100,bowl=100|soya chunks,meal maker
Tofu|76|8|piece=100|
Paneer|265|18|piece=25,plate=100|cottage cheese
Paneer butter masala|200|9|bowl=200,cup=200|
Palak paneer|150|8|bowl=200|
Paneer tikka|230|14|piece=25,plate=150|
Paneer bhurji|240|14|plate=150|
Curd|60|3.5|cup=200,bowl=150|yogurt,dahi,mosaru
Greek yogurt|59|10|cup=170|
Buttermilk|40|2|glass=250,cup=250|chaas,majjige
Lassi sweet|100|3|glass=250|
Milk full fat|62|3.2|glass=250,cup=250|milk,haalu
Milk toned|58|3.1|glass=250,cup=250|
Milk skimmed|35|3.4|glass=250|
Cheese slice|300|20|piece=20|cheese
Butter|717|1|piece=10,tsp=5|
Ghee|900|0|tsp=5,spoon=5|
Whey protein|400|80|scoop=30|protein powder,whey,protein shake
Peanut butter|590|25|tbsp=16,spoon=16|
Banana|89|1.1|piece=120|kela,baale hannu
Apple|52|0.3|piece=180|
Orange|47|0.9|piece=130|
Mango|60|0.8|piece=200,cup=165|
Papaya|43|0.5|cup=145,bowl=150|
Watermelon|30|0.6|cup=150,piece=200|
Grapes|69|0.7|cup=150|
Pomegranate|83|1.7|piece=200,cup=170|
Guava|68|2.6|piece=150|
Pineapple|50|0.5|cup=165|
Muskmelon|34|0.8|cup=160|
Chikoo|83|0.4|piece=100|sapota
Pear|57|0.4|piece=180|
Kiwi|61|1.1|piece=75|
Dates|277|1.8|piece=8|khajur
Raisins|299|3|spoon=10|
Coconut fresh|354|3.3|piece=45|
Almonds|579|21|piece=1.2,spoon=10|badam
Cashew|553|18|piece=1.5|
Peanuts roasted|585|26|spoon=10,cup=146|groundnut,shenga
Walnuts|654|15|piece=5|
Pistachio|562|20|piece=0.8|
Sunflower seeds|584|21|spoon=10|
Chia seeds|486|17|spoon=12|
Oats cooked|71|2.5|bowl=250,cup=240|oats porridge
Oats dry|389|17|cup=80,spoon=10|
Cornflakes|357|7|cup=30,bowl=40|
Muesli|360|10|cup=50|
Bread white|265|9|piece=25,slice=25|
Bread brown|250|10|piece=28,slice=28|
Bread omelette|200|9|plate=150|
Sandwich veg|200|6|piece=150|
Sandwich grilled cheese|290|11|piece=150|
Peanut butter sandwich|300|11|piece=100|
Potato boiled|87|1.9|piece=100|aloo
Sweet potato|86|1.6|piece=130|
Aloo sabzi|120|2|bowl=200,cup=200|aloo curry
Aloo gobi|110|3|bowl=200|
Bhindi fry|110|2.5|bowl=150|ladies finger
Brinjal curry|100|2|bowl=200|baingan
Cabbage curry|70|2|bowl=150|
Beans palya|80|3|bowl=150|beans
Carrot|41|0.9|piece=70|
Cucumber|15|0.7|piece=200|
Tomato|18|0.9|piece=100|
Onion|40|1.1|piece=100|
Spinach cooked|23|3|cup=180|palak
Broccoli|34|2.8|cup=90|
Cauliflower|25|1.9|cup=100|
Green peas|81|5|cup=145|
Corn boiled|96|3.4|piece=150,cup=145|sweet corn
Mixed veg curry|90|3|bowl=200|
Mushroom curry|90|4|bowl=200|
Salad|25|1|plate=150,bowl=150|
Samosa|262|4|piece=60|
Kachori|350|6|piece=60|
Pakoda|300|6|plate=100,piece=20|bajji,bhajji
Vada pav|290|6|piece=120|
Pav bhaji|170|4|plate=300|
Pani puri|200|3|piece=20,plate=120|golgappa
Bhel puri|160|4|plate=150|
Sev puri|220|4|plate=150|
Dahi puri|180|4|plate=150|
Maggi noodles|430|9|packet=70,plate=250|noodles,maggie
Chowmein|160|4|plate=300|
Hakka noodles|165|4|plate=300|
Momos veg|160|5|piece=25,plate=150|
Momos chicken|190|9|piece=25,plate=150|
Spring roll|250|5|piece=80|
Gobi manchurian|200|4|plate=200|
Paneer roll|250|9|piece=180|
Chicken roll|240|11|piece=180|kathi roll
Egg roll|230|9|piece=170|
Burger veg|250|8|piece=160|
Burger chicken|260|14|piece=180|
Pizza slice|266|11|piece=110|pizza
French fries|312|3.4|plate=120,packet=100|fries
Chips|536|7|packet=30|lays,potato chips
Kurkure|520|6|packet=30|
Biscuits|450|7|piece=10,packet=60|
Marie biscuit|430|7|piece=7|
Cream biscuit|480|5|piece=12|
Rusk|407|10|piece=11|
Chocolate|540|7|piece=20,bar=40|
Dairy Milk bar|535|7|piece=25|
Ice cream|207|3.5|scoop=70,cup=100|
Gulab jamun|330|5|piece=40|
Jalebi|380|3|piece=30|
Rasgulla|186|4|piece=50|
Laddu|400|6|piece=40|
Mysore pak|500|6|piece=40|
Kheer|130|3.5|bowl=150,cup=150|payasam
Halwa|300|3|bowl=100|
Cake slice|370|5|piece=80|
Sugar|387|0|tsp=4,spoon=4|
Jaggery|383|0.4|piece=10|bella
Honey|304|0.3|tsp=7,spoon=7|
Tea with milk sugar|45|1.2|cup=150|chai,tea
Coffee with milk sugar|50|1.5|cup=150|coffee
Black coffee|2|0.1|cup=150|
Green tea|1|0|cup=150|
Cold coffee|80|2.5|glass=250|
Cola|42|0|glass=250,bottle=600,can=330|coke,pepsi,thums up
Fruit juice|50|0.5|glass=250|
Sugarcane juice|60|0.2|glass=250|
Coconut water|19|0.7|glass=250|tender coconut
Lemon juice sweet|45|0.1|glass=250|nimbu pani
Banana shake|90|3|glass=300|
Mango shake|95|2.5|glass=300|
Energy drink|45|0|can=250|
Beer|43|0.5|glass=330,bottle=650|
Tuna canned|116|26|piece=100|
Chicken sausage|200|14|piece=40|
Chicken keema|220|18|bowl=150|
Mutton keema|240|20|bowl=150|
Chicken soup|40|3|bowl=250|
Tomato soup|45|1|bowl=250|
Sweet corn soup|60|2|bowl=250|
Rice flakes chivda|450|8|bowl=50|
Murmura|380|7|cup=15,bowl=30|puffed rice
Makhana|347|10|cup=30,bowl=30|fox nuts
Khakhra|400|12|piece=20|
Thepla|290|8|piece=45|
Dhokla|160|6|piece=40|
Chicken shawarma|230|13|piece=200|shawarma
Appam|130|2|piece=60|
Puttu|150|3|piece=120|
Fish biryani|170|9|plate=300|
Kebab chicken|200|18|piece=40|seekh kebab
Curd with sugar|110|3.5|cup=200|
"""


def load_foods():
    foods = {}
    for line in FOOD_TEXT.strip().splitlines():
        parts = line.split("|")
        if len(parts) < 4:
            continue
        name = parts[0].strip()
        units = {}
        for u in parts[3].split(","):
            if "=" in u:
                k, v = u.split("=")
                units[k.strip()] = float(v)
        aliases = []
        if len(parts) > 4:
            aliases = [a.strip().lower() for a in parts[4].split(",") if a.strip()]
        foods[name] = {
            "kcal": float(parts[1]),
            "protein": float(parts[2]),
            "units": units,
            "aliases": aliases,
        }
    return foods


FOODS = load_foods()

# --------------------------------------------------------------- saving data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_FILE = os.path.join(BASE_DIR, "diet_profile.json")
LOG_FILE = os.path.join(BASE_DIR, "diet_log.csv")
WEIGHT_FILE = os.path.join(BASE_DIR, "diet_weights.csv")
LOG_COLS = ["id", "date", "time", "food", "qty", "unit", "kcal", "protein"]

DEFAULT_PROFILE = {
    "age": 19,
    "gender": "Male",
    "height": 170,
    "weight": 60.0,
    "activity": "Moderate (exercise 3-5 days)",
    "goal": "Build muscle",
}
ACTIVITY = {
    "Low (little exercise)": 1.2,
    "Light (exercise 1-3 days)": 1.375,
    "Moderate (exercise 3-5 days)": 1.55,
    "High (exercise 6-7 days)": 1.725,
}
GOALS = {"Lose fat": -400, "Stay same": 0, "Build muscle": 300}
GOAL_PROTEIN = {"Lose fat": 1.8, "Stay same": 1.4, "Build muscle": 2.0}

if "save_ok" not in st.session_state:
    st.session_state.save_ok = True


def load_profile():
    prof = dict(DEFAULT_PROFILE)
    try:
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                prof.update(json.load(f))
    except Exception:
        pass
    if prof["activity"] not in ACTIVITY:
        prof["activity"] = DEFAULT_PROFILE["activity"]
    if prof["goal"] not in GOALS:
        prof["goal"] = DEFAULT_PROFILE["goal"]
    return prof


def save_profile(prof):
    try:
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(prof, f)
    except Exception:
        st.session_state.save_ok = False


def load_log():
    rows = []
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    try:
                        r["id"] = int(r["id"])
                        r["qty"] = float(r["qty"])
                        r["kcal"] = float(r["kcal"])
                        r["protein"] = float(r["protein"])
                        rows.append(r)
                    except Exception:
                        pass
    except Exception:
        pass
    return rows


def save_log(rows):
    try:
        with open(LOG_FILE, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=LOG_COLS, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
    except Exception:
        st.session_state.save_ok = False


def load_weights():
    rows = []
    try:
        if os.path.exists(WEIGHT_FILE):
            with open(WEIGHT_FILE, "r", encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    try:
                        rows.append({"date": r["date"], "weight": float(r["weight"])})
                    except Exception:
                        pass
    except Exception:
        pass
    return rows


def save_weights(rows):
    try:
        with open(WEIGHT_FILE, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["date", "weight"])
            w.writeheader()
            for r in rows:
                w.writerow(r)
    except Exception:
        st.session_state.save_ok = False


if "weights" not in st.session_state:
    st.session_state.weights = load_weights()
if "profile" not in st.session_state:
    st.session_state.profile = load_profile()
if "log" not in st.session_state:
    st.session_state.log = load_log()
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ------------------------------------------------------------------- numbers


def calc(prof):
    h, w, a = float(prof["height"]), float(prof["weight"]), int(prof["age"])
    bmi = w / ((h / 100.0) ** 2) if h > 0 else 0.0
    base = 10 * w + 6.25 * h - 5 * a
    bmr = base + 5 if prof["gender"] == "Male" else base - 161
    tdee = bmr * ACTIVITY[prof["activity"]]
    target = max(1200.0, tdee + GOALS[prof["goal"]])
    protein = w * GOAL_PROTEIN[prof["goal"]]
    return bmi, bmr, tdee, target, protein


def bmi_label(b):
    if b < 18.5:
        return "Underweight"
    if b < 25:
        return "Normal"
    if b < 30:
        return "Overweight"
    return "Obese"


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def today_rows():
    t = today_str()
    return [r for r in st.session_state.log if r["date"] == t]


def go(page):
    st.session_state.page = page


# ----------------------------------------------------------------- nav bar
PAGES = [
    ("Home", "🏠 Home"),
    ("Add Food", "➕ Add"),
    ("My Day", "📋 Day"),
    ("Progress", "📈 Progress"),
    ("Profile", "👤 Profile"),
]
cols = st.columns(5)
for i, (key, label) in enumerate(PAGES):
    cols[i].button(
        label,
        key="nav_" + key,
        on_click=go,
        args=(key,),
        use_container_width=True,
        type="primary" if st.session_state.page == key else "secondary",
    )
st.divider()

if not st.session_state.save_ok:
    st.warning(
        "Could not save to a file here. Your data stays only while this page is open."
    )

prof = st.session_state.profile
bmi, bmr, tdee, target, ptarget = calc(prof)
rows = today_rows()
eaten = sum(r["kcal"] for r in rows)
peaten = sum(r["protein"] for r in rows)

page = st.session_state.page

# -------------------------------------------------------------------- HOME
if page == "Home":
    st.title("🏠 Home")
    st.caption("Today: " + datetime.now().strftime("%d %B %Y"))
    remaining = target - eaten
    c1, c2 = st.columns(2)
    c1.metric("🔥 Calories eaten", "%d" % round(eaten), "of %d" % round(target), delta_color="off")
    c2.metric("⚡ Calories left", "%d" % round(remaining) if remaining >= 0 else "0")
    st.progress(min(1.0, eaten / target if target else 0.0))
    if remaining < 0:
        st.error("You are %d calories over today's target." % round(-remaining))
    c3, c4 = st.columns(2)
    c3.metric("💪 Protein eaten", "%d g" % round(peaten), "of %d g" % round(ptarget), delta_color="off")
    c4.metric("⚖️ BMI", "%.1f" % bmi, bmi_label(bmi), delta_color="off")
    st.progress(min(1.0, peaten / ptarget if ptarget else 0.0))
    if peaten < ptarget:
        st.info("Protein left: %d g" % round(ptarget - peaten))
    else:
        st.success("Protein target done! 🎉")
    st.write("")
    st.button("➕ Add food now", on_click=go, args=("Add Food",), use_container_width=True)

# --------------------------------------------------------------- ADD FOOD
elif page == "Add Food":
    st.title("➕ Add Food")
    q = st.text_input("Type the food name (example: dosa, egg, ragi)").strip().lower()
    names = sorted(FOODS.keys())
    if q:
        hits = [n for n in names if q in n.lower() or any(q in a for a in FOODS[n]["aliases"])]
        words = q.split()
        if not hits and words:
            hits = [n for n in names if any(w in n.lower() or any(w in a for a in FOODS[n]["aliases"]) for w in words)]
    else:
        hits = names
    if not hits:
        st.warning("Food not found. Try another word.")
    else:
        food_name = st.selectbox("Choose food (%d found)" % len(hits), hits)
        food = FOODS[food_name]
        own_units = list(food["units"].keys())
        ordered = own_units + ["grams", "ml"]
        c1, c2 = st.columns(2)
        unit = c1.selectbox("Unit", ordered)
        is_weight = unit in ("grams", "ml")
        default_qty = 100.0 if is_weight else 1.0
        qty = c2.number_input("How many?", min_value=0.0, max_value=5000.0, value=default_qty, step=0.5)
        grams = qty if is_weight else qty * food["units"][unit]
        kcal = grams * food["kcal"] / 100.0
        prot = grams * food["protein"] / 100.0
        st.subheader("%d calories, %.1f g protein" % (round(kcal), prot))
        if unit == "ml":
            st.caption("About %d ml (counted like %d grams)" % (round(qty), round(grams)))
        else:
            st.caption("About %d grams in total" % round(grams))
        if st.button("✅ Add to my day", use_container_width=True):
            if qty <= 0:
                st.error("Quantity must be more than 0.")
            else:
                new_id = max([r["id"] for r in st.session_state.log] + [0]) + 1
                st.session_state.log.append(
                    {
                        "id": new_id,
                        "date": today_str(),
                        "time": datetime.now().strftime("%H:%M"),
                        "food": food_name,
                        "qty": qty,
                        "unit": unit,
                        "kcal": round(kcal, 1),
                        "protein": round(prot, 1),
                    }
                )
                save_log(st.session_state.log)
                st.success("Added: %s" % food_name)
    st.write("")
    st.caption("Today so far: %d calories, %d g protein" % (round(eaten), round(peaten)))

# ----------------------------------------------------------------- MY DAY
elif page == "My Day":
    st.title("📋 My Day")
    if not rows:
        st.info("You have not added any food today.")
        st.button("➕ Add food", on_click=go, args=("Add Food",), use_container_width=True)
    else:
        df = pd.DataFrame(
            [
                {
                    "Time": r["time"],
                    "Food": r["food"],
                    "Amount": "%g %s" % (r["qty"], r["unit"]),
                    "Calories": round(r["kcal"]),
                    "Protein (g)": round(r["protein"], 1),
                }
                for r in rows
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.metric("Total calories", "%d" % round(eaten), "target %d" % round(target), delta_color="off")
        st.metric("Total protein", "%d g" % round(peaten), "target %d g" % round(ptarget), delta_color="off")
        st.divider()
        st.subheader("Remove food")
        if st.button("↩️ Undo last item", use_container_width=True):
            last_id = rows[-1]["id"]
            st.session_state.log = [r for r in st.session_state.log if r["id"] != last_id]
            save_log(st.session_state.log)
            st.success("Removed the last item.")
            st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()
        labels = {r["id"]: "%s  %s  (%s %g %s, %d cal)" % (r["time"], r["food"], "", r["qty"], r["unit"], round(r["kcal"])) for r in rows}
        pick = st.selectbox("Or choose one to delete", list(labels.keys()), format_func=lambda i: labels[i])
        if st.button("🗑️ Delete this item", use_container_width=True):
            st.session_state.log = [r for r in st.session_state.log if r["id"] != pick]
            save_log(st.session_state.log)
            st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()
        with st.expander("Clear the whole day"):
            if st.button("Delete everything from today", use_container_width=True):
                t = today_str()
                st.session_state.log = [r for r in st.session_state.log if r["date"] != t]
                save_log(st.session_state.log)
                st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()

# --------------------------------------------------------------- PROGRESS
elif page == "Progress":
    st.title("📈 Progress")
    # one row per day from the whole log
    daily = {}
    for r in st.session_state.log:
        d = daily.setdefault(r["date"], {"kcal": 0.0, "protein": 0.0})
        d["kcal"] += r["kcal"]
        d["protein"] += r["protein"]
    all_days = pd.DataFrame(
        [{"Date": k, "Calories": round(v["kcal"]), "Protein (g)": round(v["protein"], 1)} for k, v in sorted(daily.items())]
    )
    st.subheader("Today")
    c1, c2 = st.columns(2)
    c1.metric("Calories", "%d" % round(eaten), "target %d" % round(target), delta_color="off")
    c2.metric("Protein", "%d g" % round(peaten), "target %d g" % round(ptarget), delta_color="off")

    def last_days(n):
        # last n days including today, missing days = 0
        out = []
        today = datetime.now().date()
        for i in range(n - 1, -1, -1):
            day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            v = daily.get(day, {"kcal": 0.0, "protein": 0.0})
            out.append({"Date": day[5:], "Calories": round(v["kcal"]), "Protein (g)": round(v["protein"], 1), "_has": day in daily})
        return pd.DataFrame(out)

    wk = last_days(7)
    st.subheader("Last 7 days")
    if all_days.empty:
        st.info("No food saved yet. Add food and come back.")
    else:
        st.bar_chart(wk.set_index("Date")[["Calories"]])
        st.bar_chart(wk.set_index("Date")[["Protein (g)"]])
        used = wk[wk["_has"]]
        if len(used) > 0:
            avg_k = used["Calories"].mean()
            avg_p = used["Protein (g)"].mean()
            a1, a2 = st.columns(2)
            a1.metric("Average calories", "%d" % round(avg_k), "on %d days with food" % len(used), delta_color="off")
            a2.metric("Average protein", "%d g" % round(avg_p))
        # streak: days in a row (ending today or yesterday) with food logged
        streak = 0
        day = datetime.now().date()
        if day.strftime("%Y-%m-%d") not in daily:
            day = day - timedelta(days=1)
        while day.strftime("%Y-%m-%d") in daily and streak < 3650:
            streak += 1
            day = day - timedelta(days=1)
        st.metric("🔥 Logging streak", "%d day%s" % (streak, "" if streak == 1 else "s"))
        hit = sum(1 for k, v in daily.items() if v["protein"] >= ptarget)
        st.caption("Days you reached your protein target: %d" % hit)

        st.subheader("Last 30 days")
        mo = last_days(30)
        st.line_chart(mo.set_index("Date")[["Calories"]])
        st.line_chart(mo.set_index("Date")[["Protein (g)"]])

        st.subheader("Past days")
        st.dataframe(all_days.iloc[::-1].reset_index(drop=True), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("⚖️ Body weight")
    w1, w2 = st.columns(2)
    wdate = w1.date_input("Date", value=datetime.now().date())
    wval = w2.number_input("Weight (kg)", min_value=25.0, max_value=250.0, value=float(prof["weight"]), step=0.1)
    if st.button("💾 Save weight", use_container_width=True):
        key = wdate.strftime("%Y-%m-%d")
        rows_w = [r for r in st.session_state.weights if r["date"] != key]
        rows_w.append({"date": key, "weight": round(float(wval), 1)})
        rows_w.sort(key=lambda r: r["date"])
        st.session_state.weights = rows_w
        save_weights(rows_w)
        st.success("Weight saved for %s" % key)
    ws = sorted(st.session_state.weights, key=lambda r: r["date"])
    if not ws:
        st.info("No weight saved yet. Add your weight above.")
    else:
        first, lastw = ws[0], ws[-1]
        diff = lastw["weight"] - first["weight"]
        m1, m2 = st.columns(2)
        m1.metric("Latest weight", "%.1f kg" % lastw["weight"], lastw["date"], delta_color="off")
        m2.metric("Change since first", "%+.1f kg" % diff, "first: %.1f kg" % first["weight"], delta_color="off")
        if len(ws) >= 2:
            wdf = pd.DataFrame(ws)
            wdf["date"] = pd.to_datetime(wdf["date"])
            st.line_chart(wdf.set_index("date")[["weight"]])
        else:
            st.caption("Add one more weight on another day to see the line chart.")
        with st.expander("All weights"):
            st.dataframe(pd.DataFrame(ws[::-1]), use_container_width=True, hide_index=True)
        if st.button("↩️ Delete latest weight", use_container_width=True):
            st.session_state.weights = ws[:-1]
            save_weights(st.session_state.weights)
            st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()

# ---------------------------------------------------------------- PROFILE
else:
    st.title("👤 Profile")
    c1, c2 = st.columns(2)
    age = c1.number_input("Age (years)", min_value=10, max_value=90, value=int(prof["age"]), step=1)
    gender = c2.selectbox("Gender", ["Male", "Female"], index=0 if prof["gender"] == "Male" else 1)
    c3, c4 = st.columns(2)
    height = c3.number_input("Height (cm)", min_value=100, max_value=230, value=int(prof["height"]), step=1)
    weight = c4.number_input("Weight (kg)", min_value=25.0, max_value=250.0, value=float(prof["weight"]), step=0.5)
    act_list = list(ACTIVITY.keys())
    activity = st.selectbox("How active are you?", act_list, index=act_list.index(prof["activity"]))
    goal_list = list(GOALS.keys())
    goal = st.selectbox("Your goal", goal_list, index=goal_list.index(prof["goal"]))
    if st.button("💾 Save profile", use_container_width=True):
        st.session_state.profile = {
            "age": int(age),
            "gender": gender,
            "height": int(height),
            "weight": float(weight),
            "activity": activity,
            "goal": goal,
        }
        save_profile(st.session_state.profile)
        st.success("Saved!")
        st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()
    st.divider()
    st.subheader("Your numbers")
    c5, c6 = st.columns(2)
    c5.metric("⚖️ BMI", "%.1f" % bmi, bmi_label(bmi), delta_color="off")
    c6.metric("🔥 BMR", "%d cal" % round(bmr))
    c7, c8 = st.columns(2)
    c7.metric("🎯 Daily calories", "%d" % round(target))
    c8.metric("💪 Daily protein", "%d g" % round(ptarget))
    st.caption("BMR = calories your body burns at rest. Daily calories = BMR x activity, then goal added or removed. These are estimates.")
