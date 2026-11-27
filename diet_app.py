# diet_app.py  (version 15)  - run with:  streamlit run diet_app.py
# 6 pages: Home, Add Food, My Day, Progress, Workout, Profile. 
import csv
import json
import os
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

TZ_HOURS = 5.5  # India time (IST). The cloud server runs on UTC, so we shift it.


def now_local():
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=TZ_HOURS)


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

# ------------------------------------------------------------ exercise list
# name | type (S = sets/reps/weight, C = cardio minutes) | aliases
EXERCISE_TEXT = """
Push-ups|S|pushup,pushups,push ups
Incline push-ups|S|
Diamond push-ups|S|
Pull-ups|S|pullup,pullups,pull ups,chin up
Chin-ups|S|chinup
Bench press|S|chest press,flat bench
Incline bench press|S|incline press
Dumbbell bench press|S|db press
Dumbbell fly|S|chest fly,fly
Cable crossover|S|cable fly
Chest dips|S|dips
Overhead shoulder press|S|shoulder press,military press,ohp
Dumbbell shoulder press|S|db shoulder press
Lateral raise|S|side raise
Front raise|S|
Rear delt fly|S|reverse fly
Shrugs|S|
Bicep curl|S|bicep curls,curls,dumbbell curl
Hammer curl|S|
Barbell curl|S|
Tricep pushdown|S|tricep,triceps
Skull crusher|S|
Overhead tricep extension|S|tricep extension
Tricep dips|S|bench dips
Lat pulldown|S|pulldown
Barbell row|S|bent over row,row
Seated cable row|S|cable row
Dumbbell row|S|one arm row
T-bar row|S|
Deadlift|S|
Romanian deadlift|S|rdl
Squats|S|squat,bodyweight squat
Barbell squat|S|back squat
Goblet squat|S|
Front squat|S|
Leg press|S|
Lunges|S|lunge,walking lunge
Bulgarian split squat|S|split squat
Leg extension|S|
Leg curl|S|hamstring curl
Hip thrust|S|glute bridge
Calf raise|S|calves
Plank|S|plank seconds
Crunches|S|crunch,sit ups,situps
Leg raises|S|
Russian twist|S|
Mountain climbers|S|
Burpees|S|
Running|C|run,jogging,jog
Walking|C|walk
Cycling|C|cycle,bicycle
Skipping rope|C|skipping,jump rope
Swimming|C|swim
Treadmill|C|
Stair climbing|C|stairs
HIIT|C|
Yoga|C|
"""


def load_exercises():
    ex = {}
    for line in EXERCISE_TEXT.strip().splitlines():
        p = line.split("|")
        if len(p) < 2:
            continue
        al = []
        if len(p) > 2:
            al = [a.strip().lower() for a in p[2].split(",") if a.strip()]
        ex[p[0].strip()] = {"cardio": p[1].strip() == "C", "aliases": al}
    return ex


EXERCISES = load_exercises()

# Day plans: weekday (0 = Monday ... 6 = Sunday) -> (title, [(exercise, sets, reps or minutes)])
# Cardio exercises use sets = 1 and the number is MINUTES. Plank number is SECONDS.
PLAN_DAYS = {
    "Build muscle": {
        0: ("Push", [("Bench press", 4, 8), ("Incline bench press", 3, 10), ("Overhead shoulder press", 3, 10), ("Lateral raise", 3, 12), ("Tricep pushdown", 3, 12), ("Push-ups", 2, 15)]),
        1: ("Pull", [("Lat pulldown", 4, 10), ("Barbell row", 4, 8), ("Seated cable row", 3, 10), ("Rear delt fly", 3, 12), ("Bicep curl", 3, 12), ("Hammer curl", 3, 12)]),
        2: ("Legs", [("Barbell squat", 4, 8), ("Leg press", 3, 12), ("Romanian deadlift", 3, 10), ("Leg curl", 3, 12), ("Calf raise", 4, 15), ("Plank", 3, 30)]),
        3: ("Push 2", [("Dumbbell bench press", 4, 10), ("Dumbbell shoulder press", 3, 10), ("Dumbbell fly", 3, 12), ("Front raise", 3, 12), ("Skull crusher", 3, 10), ("Chest dips", 3, 10)]),
        4: ("Pull 2", [("Pull-ups", 4, 8), ("Dumbbell row", 3, 10), ("T-bar row", 3, 10), ("Shrugs", 3, 12), ("Barbell curl", 3, 10), ("Hammer curl", 3, 12)]),
        5: ("Legs and abs", [("Goblet squat", 3, 12), ("Lunges", 3, 12), ("Hip thrust", 3, 12), ("Leg extension", 3, 12), ("Crunches", 3, 20), ("Leg raises", 3, 15), ("Plank", 3, 40)]),
        6: ("Rest day", []),
    },
    "Lose fat": {
        0: ("Full body", [("Squats", 3, 15), ("Push-ups", 3, 12), ("Dumbbell row", 3, 12), ("Lunges", 3, 12), ("Plank", 3, 30), ("Skipping rope", 1, 10)]),
        1: ("Cardio and abs", [("Running", 1, 30), ("Mountain climbers", 3, 20), ("Crunches", 3, 20), ("Leg raises", 3, 15)]),
        2: ("Full body", [("Goblet squat", 3, 15), ("Dumbbell shoulder press", 3, 12), ("Lat pulldown", 3, 12), ("Hip thrust", 3, 15), ("Russian twist", 3, 20), ("Cycling", 1, 15)]),
        3: ("Cardio and abs", [("Cycling", 1, 30), ("Burpees", 3, 10), ("Crunches", 3, 20), ("Plank", 3, 40), ("Leg raises", 3, 15)]),
        4: ("Full body", [("Romanian deadlift", 3, 12), ("Dumbbell bench press", 3, 12), ("Seated cable row", 3, 12), ("Bicep curl", 3, 12), ("Tricep pushdown", 3, 12), ("Skipping rope", 1, 10)]),
        5: ("Long cardio", [("Running", 1, 40), ("Walking", 1, 10), ("Mountain climbers", 3, 20), ("Plank", 3, 30)]),
        6: ("Rest day", []),
    },
    "Stay same": {
        0: ("Upper body", [("Push-ups", 3, 12), ("Dumbbell row", 3, 10), ("Dumbbell shoulder press", 3, 10), ("Lat pulldown", 3, 10), ("Bicep curl", 3, 12), ("Tricep pushdown", 3, 12)]),
        1: ("Lower body", [("Squats", 3, 12), ("Lunges", 3, 12), ("Leg press", 3, 12), ("Leg curl", 3, 12), ("Calf raise", 3, 15)]),
        2: ("Cardio and abs", [("Running", 1, 30), ("Crunches", 3, 20), ("Plank", 3, 30), ("Leg raises", 3, 12)]),
        3: ("Upper body", [("Bench press", 3, 10), ("Pull-ups", 3, 8), ("Overhead shoulder press", 3, 10), ("Seated cable row", 3, 10), ("Hammer curl", 3, 12), ("Skull crusher", 3, 10)]),
        4: ("Lower body and abs", [("Deadlift", 3, 8), ("Goblet squat", 3, 12), ("Hip thrust", 3, 12), ("Plank", 3, 40), ("Crunches", 3, 20)]),
        5: ("Cardio or sport", [("Cycling", 1, 30), ("Walking", 1, 15)]),
        6: ("Rest day", []),
    },
}
PLAN_TIPS = {
    "Build muscle": "Tip: Add a little weight when it feels easy. Eat enough protein and sleep 7-8 hours.",
    "Lose fat": "Tip: Keep rests short. Stay a bit under your calorie target and walk every day.",
    "Stay same": "Tip: Keep it regular. Eat at your calorie target.",
}
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
TIMED = ("Plank",)


def day_plan(goal, weekday):
    plans = PLAN_DAYS.get(goal, PLAN_DAYS["Stay same"])
    return plans.get(weekday, ("Rest day", []))


# ------------------------------------------------------------ animations
# Pictures come from the free "free-exercise-db" project on GitHub (public domain, no sign-in).
# Each exercise has 2 pictures (start and end). We flip between them to make a small animation.
IMG_BASE = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/"
GIF_IDS = {
    "Push-ups": "Pushups",
    "Incline push-ups": "Incline_Push-Up",
    "Pull-ups": "Pullups",
    "Chin-ups": "Chin-Up",
    "Bench press": "Barbell_Bench_Press_-_Medium_Grip",
    "Incline bench press": "Barbell_Incline_Bench_Press_-_Medium_Grip",
    "Dumbbell bench press": "Dumbbell_Bench_Press",
    "Dumbbell fly": "Dumbbell_Flyes",
    "Cable crossover": "Cable_Crossover",
    "Chest dips": "Dips_-_Chest_Version",
    "Overhead shoulder press": "Barbell_Shoulder_Press",
    "Dumbbell shoulder press": "Dumbbell_Shoulder_Press",
    "Lateral raise": "Side_Lateral_Raise",
    "Front raise": "Front_Dumbbell_Raise",
    "Rear delt fly": "Reverse_Flyes",
    "Shrugs": "Dumbbell_Shrug",
    "Bicep curl": "Dumbbell_Bicep_Curl",
    "Hammer curl": "Hammer_Curls",
    "Barbell curl": "Barbell_Curl",
    "Tricep pushdown": "Triceps_Pushdown",
    "Skull crusher": "EZ-Bar_Skullcrusher",
    "Overhead tricep extension": "Cable_Rope_Overhead_Triceps_Extension",
    "Tricep dips": "Bench_Dips",
    "Lat pulldown": "Wide-Grip_Lat_Pulldown",
    "Barbell row": "Bent_Over_Barbell_Row",
    "Seated cable row": "Seated_Cable_Rows",
    "Dumbbell row": "One-Arm_Dumbbell_Row",
    "T-bar row": "T-Bar_Row_with_Handle",
    "Deadlift": "Barbell_Deadlift",
    "Romanian deadlift": "Romanian_Deadlift",
    "Squats": "Bodyweight_Squat",
    "Barbell squat": "Barbell_Squat",
    "Goblet squat": "Goblet_Squat",
    "Front squat": "Front_Barbell_Squat",
    "Leg press": "Leg_Press",
    "Lunges": "Dumbbell_Lunges",
    "Bulgarian split squat": "Split_Squat_with_Dumbbells",
    "Leg extension": "Leg_Extensions",
    "Leg curl": "Lying_Leg_Curls",
    "Hip thrust": "Barbell_Hip_Thrust",
    "Calf raise": "Standing_Calf_Raises",
    "Plank": "Plank",
    "Crunches": "Crunches",
    "Leg raises": "Flat_Bench_Lying_Leg_Raise",
    "Russian twist": "Russian_Twist",
    "Mountain climbers": "Mountain_Climbers",
    "Running": "Running_Treadmill",
    "Walking": "Walking_Treadmill",
    "Cycling": "Bicycling",
    "Skipping rope": "Rope_Jumping",
    "Treadmill": "Jogging_Treadmill",
    "Stair climbing": "Stairmaster",
}

CUES = {
    "Diamond push-ups": "Hands close together under your chest, thumbs and fingers make a diamond. Lower your chest to your hands, then push up.",
    "Burpees": "Squat down, jump your feet back, do a push-up, jump your feet in, then jump up with arms overhead.",
    "Swimming": "Swim steady laps. Breathe calmly and keep a smooth rhythm.",
    "HIIT": "Go hard for 30 seconds (jumping jacks, high knees, fast feet), then rest 30 seconds. Repeat.",
    "Yoga": "Move slowly. Breathe in and out deeply. Do not force any stretch.",
}


def exercise_visual(name):
    """Show the two-picture animation, or a text cue if we have no picture."""
    gid = GIF_IDS.get(name)
    if gid:
        a = IMG_BASE + gid + "/0.jpg"
        b = IMG_BASE + gid + "/1.jpg"
        html = (
            "<style>"
            ".mu-anim{position:relative;max-width:340px;margin:0 auto 10px auto;border-radius:12px;overflow:hidden;background:#fff}"
            ".mu-anim img{width:100%;display:block}"
            ".mu-anim img.mu-b{position:absolute;top:0;left:0;opacity:0;animation:mu-flip 1.8s infinite}"
            "@keyframes mu-flip{0%,45%{opacity:0}50%,95%{opacity:1}100%{opacity:0}}"
            "</style>"
            "<div class='mu-anim'><img src='" + a + "' alt='start'><img class='mu-b' src='" + b + "' alt='end'></div>"
        )
        try:
            st.markdown(html, unsafe_allow_html=True)
            return
        except Exception:
            pass
    cue = CUES.get(name, "Keep your back straight, move slowly and breathe.")
    st.info("💡 How to: " + cue)


TIMER_HTML = """
<div id="mu" style="font-family:Arial,sans-serif;text-align:center;border-radius:14px;padding:12px;background:#1a1f2b;color:#fafafa">
  <div style="font-size:16px;font-weight:bold;margin-bottom:4px">__TITLE__</div>
  <div id="t" style="font-size:64px;font-weight:800;line-height:1.1">00:00</div>
  <div id="msg" style="min-height:22px;font-size:16px;margin:4px 0"></div>
  <div id="presets" style="margin:6px 0"></div>
  <div style="margin:6px 0">
    <input id="c" type="number" min="1" max="3600" placeholder="seconds" style="width:90px;font-size:16px;padding:6px;background:#0e1117;color:#fafafa;border:1px solid #555;border-radius:6px">
    <button id="setc" style="font-size:16px;padding:8px 12px;background:#2a3142;color:#fafafa;border:1px solid #555;border-radius:8px">Set</button>
  </div>
  <div>
    <button id="go" style="font-size:20px;padding:12px 22px;background:#22c55e;color:#06210f;border:0;border-radius:10px;font-weight:bold">▶ Start</button>
    <button id="rs" style="font-size:20px;padding:12px 16px;border:0;border-radius:10px;background:#2a3142;color:#fafafa">↺</button>
  </div>
</div>
<script>
var PRESETS = __PRESETS__;
var total = __DEFAULT__, left = total, endAt = 0, timer = null, ctx = null;
var $ = function(i){return document.getElementById(i);};
function fmt(s){var m=Math.floor(s/60), r=s%60; return (m<10?"0":"")+m+":"+(r<10?"0":"")+r;}
function show(){ $("t").textContent = fmt(left); }
function beep(f, d, when){
  try{
    var o=ctx.createOscillator(), g=ctx.createGain();
    o.frequency.value=f; o.connect(g); g.connect(ctx.destination);
    g.gain.value=0.4; o.start(ctx.currentTime+when); o.stop(ctx.currentTime+when+d);
  }catch(e){}
}
function done(){
  clearInterval(timer); timer=null; left=0; show();
  $("go").textContent="▶ Start";
  $("msg").textContent="⏰ Time is up!";
  $("mu").style.background="#7a1f1f";
  beep(880,0.25,0); beep(880,0.25,0.4); beep(1175,0.5,0.8);
  try{ if(navigator.vibrate) navigator.vibrate([300,150,300,150,600]); }catch(e){}
  setTimeout(function(){ $("mu").style.background="#1a1f2b"; }, 4000);
}
function tick(){
  left = Math.max(0, Math.round((endAt - Date.now())/1000));
  show();
  if(left<=0){ done(); }
}
function start(){
  if(!ctx){ try{ ctx = new (window.AudioContext||window.webkitAudioContext)(); }catch(e){} }
  if(ctx && ctx.resume){ try{ ctx.resume(); }catch(e){} }
  if(left<=0) left=total;
  endAt = Date.now() + left*1000;
  $("msg").textContent="";
  $("mu").style.background="#1a1f2b";
  $("go").textContent="⏸ Pause";
  clearInterval(timer); timer=setInterval(tick, 250); tick();
}
function pause(){ clearInterval(timer); timer=null; $("go").textContent="▶ Start"; }
function setTotal(n){ pause(); total=n; left=n; $("msg").textContent=""; $("mu").style.background="#1a1f2b"; show(); }
$("go").onclick=function(){ if(timer){ pause(); } else { start(); } };
$("rs").onclick=function(){ setTotal(total); };
$("setc").onclick=function(){ var v=parseInt($("c").value,10); if(v>0){ setTotal(v); } };
PRESETS.forEach(function(p){
  var b=document.createElement("button");
  b.textContent = p>=120 && p%60==0 ? (p/60)+" min" : p+" s";
  b.style.cssText="font-size:16px;padding:8px 12px;margin:3px;border-radius:8px;border:1px solid #555;background:#2a3142;color:#fafafa";
  b.onclick=function(){ setTotal(p); };
  $("presets").appendChild(b);
});
show();
</script>
"""


def timer_html(title, default_seconds, presets):
    presets = sorted(set(int(p) for p in presets if int(p) > 0))
    return (
        TIMER_HTML.replace("__TITLE__", title)
        .replace("__DEFAULT__", str(int(default_seconds)))
        .replace("__PRESETS__", json.dumps(presets))
    )


def show_timer(title, default_seconds, presets):
    """Timer runs in the browser (no page reloads). Beeps and vibrates when done."""
    html = timer_html(title, default_seconds, presets)
    try:
        if hasattr(st, "iframe"):
            st.iframe(html, height=310)
        else:
            import streamlit.components.v1 as components

            components.html(html, height=310)
    except Exception:
        st.info("Timer is not available here. Use your phone clock: %d seconds." % int(default_seconds))


# --------------------------------------------------------------- saving data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# These three paths are set for the current user right after the "Who are you?" screen.
PROFILE_FILE = ""
LOG_FILE = ""
WEIGHT_FILE = ""
WORKOUT_FILE = ""
WATER_FILE = ""
MEASURE_FILE = ""
WATER_TARGET = 8  # glasses per day
WORKOUT_COLS = ["id", "date", "time", "exercise", "sets", "reps", "weight"]
LOG_COLS = ["id", "date", "time", "food", "qty", "unit", "kcal", "protein"]

DEFAULT_PROFILE = {
    "age": 19,
    "gender": "Male",
    "height": 170,
    "weight": 60.0,
    "activity": "Moderate (exercise 3-5 days)",
    "goal": "Build muscle",
    "target_weight": 0.0,
    "start_weight": 0.0,
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


def load_workout():
    rows = []
    try:
        if os.path.exists(WORKOUT_FILE):
            with open(WORKOUT_FILE, "r", encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    try:
                        r["id"] = int(r["id"])
                        r["sets"] = int(float(r["sets"]))
                        r["reps"] = int(float(r["reps"]))
                        r["weight"] = float(r["weight"])
                        rows.append(r)
                    except Exception:
                        pass
    except Exception:
        pass
    return rows


def save_workout(rows):
    try:
        with open(WORKOUT_FILE, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=WORKOUT_COLS, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
    except Exception:
        st.session_state.save_ok = False


def load_water():
    water = {}
    try:
        if os.path.exists(WATER_FILE):
            with open(WATER_FILE, "r", encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    try:
                        water[r["date"]] = int(float(r["glasses"]))
                    except Exception:
                        pass
    except Exception:
        pass
    return water


def save_water(water):
    try:
        with open(WATER_FILE, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["date", "glasses"])
            w.writeheader()
            for k in sorted(water.keys()):
                w.writerow({"date": k, "glasses": water[k]})
    except Exception:
        st.session_state.save_ok = False


MEASURE_COLS = ["date", "chest", "waist", "arms"]


def load_measure():
    rows = []
    try:
        if os.path.exists(MEASURE_FILE):
            with open(MEASURE_FILE, "r", encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    try:
                        rows.append({"date": r["date"], "chest": float(r["chest"]), "waist": float(r["waist"]), "arms": float(r["arms"])})
                    except Exception:
                        pass
    except Exception:
        pass
    return rows


def save_measure(rows):
    try:
        with open(MEASURE_FILE, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=MEASURE_COLS)
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


# ------------------------------------------------------------ who are you?
def make_slug(name):
    out = ""
    for ch in str(name).strip().lower():
        out += ch if (ch.isascii() and ch.isalnum()) else "_"
    out = "_".join([p for p in out.split("_") if p])
    return out[:30]


def existing_users():
    users = []
    try:
        for fn in sorted(os.listdir(BASE_DIR)):
            for pre, ext in (("diet_profile_", ".json"), ("diet_log_", ".csv"), ("diet_weights_", ".csv"), ("diet_workout_", ".csv"), ("diet_water_", ".csv"), ("diet_measure_", ".csv")):
                if fn.startswith(pre) and fn.endswith(ext):
                    slug = fn[len(pre):-len(ext)]
                    if slug and slug not in users:
                        users.append(slug)
    except Exception:
        pass
    return sorted(users)


def clean_name(name):
    return " ".join(str(name).strip().split())[:30]


def read_user_param():
    try:
        v = st.query_params.get("user", "")
        if isinstance(v, (list, tuple)):
            v = v[0] if v else ""
        return clean_name(v)
    except Exception:
        return ""


def write_user_param(name):
    try:
        if name:
            st.query_params["user"] = name
        elif "user" in st.query_params:
            del st.query_params["user"]
    except Exception:
        pass  # old Streamlit: person is remembered for this session only


def choose_user(name):
    name = clean_name(name)
    if not make_slug(name):
        return False
    st.session_state.user = name
    write_user_param(name)
    return True


def switch_user():
    st.session_state.user = ""
    st.session_state.loaded_slug = ""
    st.session_state.page = "Home"
    st.session_state.guide_started = False
    st.session_state.guide_idx = 0
    write_user_param("")


if "user" not in st.session_state:
    st.session_state.user = ""
if "loaded_slug" not in st.session_state:
    st.session_state.loaded_slug = ""
if "page" not in st.session_state:
    st.session_state.page = "Home"

if not st.session_state.user:
    remembered = read_user_param()
    if remembered:
        choose_user(remembered)

if not st.session_state.user:
    st.title("👋 " + APP_NAME)
    st.write("Type your name to start.")
    typed = st.text_input("Your name")
    if st.button("Start", use_container_width=True, type="primary"):
        if choose_user(typed):
            st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()
        else:
            st.error("Please type your name (letters or numbers).")
    others = existing_users()
    if others:
        st.write("Or pick your name:")
        for slug in others[:30]:
            if st.button(slug.replace("_", " ").title(), key="pick_" + slug, use_container_width=True):
                choose_user(slug.replace("_", " "))
                st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()
    st.caption("This is only a name, not a password.")
    st.stop()

# a user is chosen: point the files at this user and load their data
slug = make_slug(st.session_state.user)
PROFILE_FILE = os.path.join(BASE_DIR, "diet_profile_%s.json" % slug)
LOG_FILE = os.path.join(BASE_DIR, "diet_log_%s.csv" % slug)
WEIGHT_FILE = os.path.join(BASE_DIR, "diet_weights_%s.csv" % slug)
WORKOUT_FILE = os.path.join(BASE_DIR, "diet_workout_%s.csv" % slug)
WATER_FILE = os.path.join(BASE_DIR, "diet_water_%s.csv" % slug)
MEASURE_FILE = os.path.join(BASE_DIR, "diet_measure_%s.csv" % slug)

if st.session_state.loaded_slug != slug:
    st.session_state.weights = load_weights()
    st.session_state.profile = load_profile()
    st.session_state.log = load_log()
    st.session_state.workout = load_workout()
    st.session_state.water = load_water()
    st.session_state.measure = load_measure()
    st.session_state.celebrated = False
    st.session_state.guide_started = False
    st.session_state.guide_idx = 0
    st.session_state.loaded_slug = slug
    st.session_state.save_ok = True
    st.session_state.page = "Home"
    # make sure this person shows up in the "pick your name" list
    if not os.path.exists(PROFILE_FILE):
        save_profile(st.session_state.profile)
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
    return now_local().strftime("%Y-%m-%d")


def today_rows():
    t = today_str()
    return [r for r in st.session_state.log if r["date"] == t]


def today_workout():
    t = today_str()
    return [r for r in st.session_state.workout if r["date"] == t]


QUOTES = [
    "Small steps every day beat big plans you never start.",
    "Your body can do it. Convince your mind.",
    "Sweat now, smile later.",
    "Do not stop when you are tired. Stop when you are done.",
    "Discipline is doing it even when you do not feel like it.",
    "One more rep. That is where change happens.",
    "Strong is not a size. It is a habit.",
    "Today's pain is tomorrow's power.",
    "You do not need to be perfect. You need to show up.",
    "Eat well, sleep well, train hard, repeat.",
    "The only bad workout is the one you skipped.",
    "Progress is slow, but it adds up. Keep going.",
    "Be stronger than your excuses.",
    "Your future self is watching. Make them proud.",
    "Consistency beats motivation. Every time.",
]


def quote_of_the_day():
    return QUOTES[now_local().timetuple().tm_yday % len(QUOTES)]


def goal_status(profile):
    """Returns (start, current, target, percent) or None if no target is set."""
    try:
        target = float(profile.get("target_weight", 0) or 0)
        current = float(profile.get("weight", 0) or 0)
        start = float(profile.get("start_weight", 0) or 0)
    except Exception:
        return None
    if target <= 0 or current <= 0:
        return None
    if start <= 0:
        start = current
    if abs(start - target) < 0.01:
        pct = 1.0 if abs(current - target) < 0.5 else 0.0
    else:
        pct = (start - current) / (start - target)
    return start, current, target, max(0.0, min(1.0, pct))


def add_water(n):
    t = today_str()
    cur = st.session_state.water.get(t, 0)
    st.session_state.water[t] = max(0, min(50, cur + n))
    save_water(st.session_state.water)


def streak_days():
    """Days in a row (ending today or yesterday) with any food or workout logged."""
    days = set(r["date"] for r in st.session_state.log) | set(r["date"] for r in st.session_state.workout)
    day = now_local().date()
    if day.strftime("%Y-%m-%d") not in days:
        day = day - timedelta(days=1)
    n = 0
    while day.strftime("%Y-%m-%d") in days and n < 3650:
        n += 1
        day = day - timedelta(days=1)
    return n


def go(page):
    st.session_state.page = page


# ----------------------------------------------------------------- nav bar
PAGES = [
    ("Home", "🏠 Home"),
    ("Add Food", "➕ Add"),
    ("My Day", "📋 Day"),
    ("Progress", "📈 Progress"),
    ("Workout", "🏋️ Workout"),
    ("Profile", "👤 Profile"),
]
cols = st.columns(6)
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
    st.write("Hello, **%s**!" % st.session_state.user)
    st.caption("Today: " + now_local().strftime("%d %B %Y"))
    st.info("💬 " + quote_of_the_day())
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
    gs = goal_status(prof)
    if gs:
        g_start, g_cur, g_tar, g_pct = gs
        st.subheader("🎯 Goal: %g kg to %g kg" % (g_cur, g_tar))
        st.progress(g_pct)
        if g_pct >= 1.0:
            st.success("Goal reached! 🏆")
        else:
            st.caption("%d%% there (started at %g kg)" % (round(g_pct * 100), g_start))
    else:
        st.caption("🎯 Set a target weight in Profile to see your goal bar.")
    sk = streak_days()
    if sk > 0:
        st.subheader("🔥 %d day streak" % sk)
    else:
        st.subheader("🔥 No streak yet")
        st.caption("Log food or a workout today to start your streak.")
    glasses = st.session_state.water.get(today_str(), 0)
    st.subheader("💧 Water: %d/%d glasses" % (glasses, WATER_TARGET))
    st.progress(min(1.0, glasses / float(WATER_TARGET)))
    w1, w2 = st.columns([3, 1])
    w1.button("💧 +1 glass", key="water_add", on_click=add_water, args=(1,), use_container_width=True)
    w2.button("−1", key="water_sub", on_click=add_water, args=(-1,), use_container_width=True)
    if glasses >= WATER_TARGET:
        st.success("Water target done! 💦")
    st.write("")
    st.button("➕ Add food now", on_click=go, args=("Add Food",), use_container_width=True)
    st.button("🔄 Not you? Switch user", key="switch_home", on_click=switch_user, use_container_width=True)

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
                        "time": now_local().strftime("%H:%M"),
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

# ---------------------------------------------------------------- WORKOUT
elif page == "Workout":
    st.title("🏋️ Workout")

    def is_cardio(name):
        return name in EXERCISES and EXERCISES[name]["cardio"]

    def reps_text(name, reps):
        if is_cardio(name):
            return "%d min" % reps
        if name in TIMED:
            return "%d sec" % reps
        return str(reps)

    def last_weight(name):
        for r in reversed(st.session_state.workout):
            if r["exercise"] == name and r["weight"] > 0:
                return float(r["weight"])
        return 0.0

    def save_entry(name, sets_n, reps_n, weight_n):
        new_id = max([r["id"] for r in st.session_state.workout] + [0]) + 1
        st.session_state.workout.append(
            {
                "id": new_id,
                "date": today_str(),
                "time": now_local().strftime("%H:%M"),
                "exercise": name,
                "sets": int(sets_n),
                "reps": int(reps_n),
                "weight": float(weight_n),
            }
        )
        save_workout(st.session_state.workout)

    def rerun_now():
        st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()

    # forget an old guided run when the day changes
    if st.session_state.get("guide_date") != today_str():
        st.session_state.guide_date = today_str()
        st.session_state.guide_started = False
        st.session_state.guide_idx = 0

    weekday = now_local().weekday()
    title, items = day_plan(prof["goal"], weekday)
    st.caption("%s, goal: %s" % (now_local().strftime("%A"), prof["goal"]))

    wrows = today_workout()

    # ---------- guided workout
    if not items:
        st.subheader("😴 Rest day")
        st.info("Today is a rest day in your plan. Walk, stretch and sleep well. You can still add an exercise below if you want.")
    else:
        total = len(items)
        idx = st.session_state.guide_idx
        if not st.session_state.guide_started:
            st.subheader("Today: %s" % title)
            for n, (nm, sn, rn) in enumerate(items, 1):
                if is_cardio(nm):
                    st.write("%d. %s - %d min" % (n, nm, rn))
                else:
                    st.write("%d. %s - %d x %s" % (n, nm, sn, reps_text(nm, rn)))
            if st.button("▶️ Start today's workout", use_container_width=True, type="primary"):
                st.session_state.celebrated = False
                st.session_state.guide_started = True
                st.session_state.guide_idx = 0
                rerun_now()
        elif idx >= total:
            st.success("🎉 Workout complete! Great job.")
            if wrows and not st.session_state.get("celebrated", False):
                st.session_state.celebrated = True
                st.balloons()
            st.subheader("What you did today")
            if not wrows:
                st.write("You skipped everything today. That is okay. Try again tomorrow.")
            for r in wrows:
                if is_cardio(r["exercise"]):
                    st.write("✅ %s - %d min" % (r["exercise"], r["reps"]))
                else:
                    wtxt = "body weight" if r["weight"] == 0 else "%g kg" % r["weight"]
                    st.write("✅ %s - %d x %s, %s" % (r["exercise"], r["sets"], reps_text(r["exercise"], r["reps"]), wtxt))
            if st.button("🔁 Start again", use_container_width=True):
                st.session_state.celebrated = False
                st.session_state.guide_started = False
                st.session_state.guide_idx = 0
                rerun_now()
        else:
            nm, tsets, treps = items[idx]
            st.subheader("Exercise %d of %d" % (idx + 1, total))
            st.progress(idx / float(total))
            st.markdown("## " + nm)
            exercise_visual(nm)
            k = "%s_%d_%s" % (today_str(), idx, slug)
            if is_cardio(nm):
                st.write("Target: **%d minutes**" % treps)
                minutes = st.number_input("Minutes you did", min_value=0, max_value=600, value=int(treps), step=1, key="g_min_" + k)
                g_sets, g_reps, g_wt = 1, int(minutes), 0.0
            else:
                st.write("Target: **%d sets x %s**" % (tsets, reps_text(nm, treps)))
                c1, c2 = st.columns(2)
                g_sets = c1.number_input("Sets you did", min_value=0, max_value=20, value=int(tsets), step=1, key="g_sets_" + k)
                g_reps = c2.number_input(
                    "Seconds in each set" if nm in TIMED else "Reps in each set",
                    min_value=0, max_value=500, value=int(treps), step=1, key="g_reps_" + k,
                )
                g_wt = st.number_input("Weight in kg (0 = body weight)", min_value=0.0, max_value=500.0, value=last_weight(nm), step=2.5, key="g_wt_" + k)
            if is_cardio(nm):
                show_timer("⏱️ Exercise timer: " + nm, treps * 60, [treps * 60, 300, 600, 1200])
            elif nm in TIMED:
                show_timer("⏱️ Hold timer: " + nm, treps, [treps, 30, 45, 60])
            else:
                show_timer("😮‍💨 Rest timer (press Start after your set)", 60, [30, 60, 90, 120])
            b1, b2 = st.columns(2)
            if b1.button("✅ Done - next", use_container_width=True, type="primary", key="g_done_" + k):
                if g_reps > 0 and g_sets > 0:
                    save_entry(nm, g_sets, g_reps, g_wt)
                st.session_state.guide_idx = idx + 1
                rerun_now()
            if b2.button("⏭️ Skip", use_container_width=True, key="g_skip_" + k):
                st.session_state.guide_idx = idx + 1
                rerun_now()
            if st.button("⏹️ Stop workout", key="g_stop_" + k, use_container_width=True):
                st.session_state.guide_idx = total
                rerun_now()

    # ---------- timer when no exercise is open
    guide_open = bool(items) and st.session_state.guide_started and st.session_state.guide_idx < len(items)
    if not guide_open:
        with st.expander("⏱️ Rest / exercise timer"):
            show_timer("⏱️ Timer", 60, [30, 60, 90, 120])

    # ---------- extra exercise (manual)
    st.divider()
    with st.expander("➕ Add extra exercise"):
        q = st.text_input("Type the exercise name (example: bench, squat, run)", key="wo_q").strip().lower()
        names = sorted(EXERCISES.keys())
        if q:
            hits = [n for n in names if q in n.lower() or any(q in a for a in EXERCISES[n]["aliases"])]
            words = q.split()
            if not hits and words:
                hits = [n for n in names if any(w in n.lower() or any(w in a for a in EXERCISES[n]["aliases"]) for w in words)]
        else:
            hits = names
        if not hits:
            st.warning("Exercise not found. Try another word.")
        else:
            ex_name = st.selectbox("Choose exercise (%d found)" % len(hits), hits, key="wo_ex")
            if is_cardio(ex_name):
                minutes = st.number_input("Minutes", min_value=1, max_value=600, value=20, step=1, key="wo_min")
                sets, reps, wt = 1, int(minutes), 0.0
            else:
                c1, c2 = st.columns(2)
                sets = c1.number_input("Sets", min_value=1, max_value=20, value=3, step=1, key="wo_sets")
                reps = c2.number_input("Reps in each set", min_value=1, max_value=500, value=10, step=1, key="wo_reps")
                wt = st.number_input("Weight in kg (0 = body weight)", min_value=0.0, max_value=500.0, value=0.0, step=2.5, key="wo_wt")
            if st.button("✅ Add to today's workout", use_container_width=True):
                save_entry(ex_name, sets, reps, wt)
                st.success("Added: %s" % ex_name)
                rerun_now()

    # ---------- today's table
    st.subheader("Today's workout log")
    wrows = today_workout()
    if not wrows:
        st.info("No exercise saved today.")
    else:
        df = pd.DataFrame(
            [
                {
                    "Exercise": r["exercise"],
                    "Sets": "-" if is_cardio(r["exercise"]) else str(r["sets"]),
                    "Reps": reps_text(r["exercise"], r["reps"]),
                    "Weight (kg)": "-" if is_cardio(r["exercise"]) else ("Body" if r["weight"] == 0 else "%g" % r["weight"]),
                }
                for r in wrows
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
        total_sets = sum(r["sets"] for r in wrows if not is_cardio(r["exercise"]))
        st.caption("%d exercises, %d sets in total" % (len(wrows), total_sets))
        if st.button("↩️ Undo last exercise", use_container_width=True):
            last_id = wrows[-1]["id"]
            st.session_state.workout = [r for r in st.session_state.workout if r["id"] != last_id]
            save_workout(st.session_state.workout)
            rerun_now()
        wlabels = {r["id"]: "%s  %s" % (r["time"], r["exercise"]) for r in wrows}
        wpick = st.selectbox("Or choose one to delete", list(wlabels.keys()), format_func=lambda i: wlabels[i], key="wo_del")
        if st.button("🗑️ Delete this exercise", use_container_width=True):
            st.session_state.workout = [r for r in st.session_state.workout if r["id"] != wpick]
            save_workout(st.session_state.workout)
            rerun_now()

    # ---------- weekly plan
    st.divider()
    st.subheader("📅 Weekly plan")
    st.caption("Plan for your goal: %s (change it in Profile)" % prof["goal"])
    for d in range(7):
        t, its = day_plan(prof["goal"], d)
        if its:
            st.write("**%s - %s:** %s" % (DAY_NAMES[d], t, ", ".join(x[0] for x in its)))
        else:
            st.write("**%s - %s**" % (DAY_NAMES[d], t))
    st.write(PLAN_TIPS.get(prof["goal"], ""))

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
        today = now_local().date()
        for i in range(n - 1, -1, -1):
            day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            v = daily.get(day, {"kcal": 0.0, "protein": 0.0})
            out.append({"Date": day[5:], "Calories": round(v["kcal"]), "Protein (g)": round(v["protein"], 1), "_has": day in daily})
        return pd.DataFrame(out)

    wk = last_days(7)
    try:
        best = {}
        for r in st.session_state.workout:
            nm_ = r["exercise"]
            if nm_ in EXERCISES and not EXERCISES[nm_]["cardio"] and r["weight"] > 0:
                if nm_ not in best or r["weight"] > best[nm_][0]:
                    best[nm_] = (r["weight"], r["date"])
        st.subheader("🏆 Personal records")
        if not best:
            st.caption("Log a workout with weight to see your best lifts here.")
        else:
            for nm_, (wt_, dt_) in sorted(best.items(), key=lambda kv: -kv[1][0]):
                st.write("**%s:** %g kg  (%s)" % (nm_, wt_, dt_))
    except Exception:
        pass
    try:
        week_days = set((now_local().date() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7))
        wo_days = set(r["date"] for r in st.session_state.workout if r["date"] in week_days)
        st.metric("🏋️ Workouts this week", "%d day%s" % (len(wo_days), "" if len(wo_days) == 1 else "s"))
    except Exception:
        pass
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
        day = now_local().date()
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
    wdate = w1.date_input("Date", value=now_local().date())
    wval = w2.number_input("Weight (kg)", min_value=25.0, max_value=250.0, value=float(prof["weight"]), step=0.1)
    if st.button("💾 Save weight", use_container_width=True):
        key = wdate.strftime("%Y-%m-%d")
        rows_w = [r for r in st.session_state.weights if r["date"] != key]
        rows_w.append({"date": key, "weight": round(float(wval), 1)})
        rows_w.sort(key=lambda r: r["date"])
        st.session_state.weights = rows_w
        save_weights(rows_w)
        if key == today_str():
            st.session_state.profile["weight"] = round(float(wval), 1)
            save_profile(st.session_state.profile)
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

    st.divider()
    st.subheader("📏 Body measurements (cm)")
    m_date = st.date_input("Measurement date", value=now_local().date(), key="m_date")
    mc1, mc2, mc3 = st.columns(3)
    m_chest = mc1.number_input("Chest", min_value=0.0, max_value=250.0, value=0.0, step=0.5, key="m_chest")
    m_waist = mc2.number_input("Waist", min_value=0.0, max_value=250.0, value=0.0, step=0.5, key="m_waist")
    m_arms = mc3.number_input("Arms", min_value=0.0, max_value=100.0, value=0.0, step=0.5, key="m_arms")
    st.caption("Leave a box at 0 if you did not measure it.")
    if st.button("💾 Save measurements", use_container_width=True):
        if m_chest <= 0 and m_waist <= 0 and m_arms <= 0:
            st.error("Type at least one measurement.")
        else:
            mk = m_date.strftime("%Y-%m-%d")
            rows_m = [r for r in st.session_state.measure if r["date"] != mk]
            rows_m.append({"date": mk, "chest": float(m_chest), "waist": float(m_waist), "arms": float(m_arms)})
            rows_m.sort(key=lambda r: r["date"])
            st.session_state.measure = rows_m
            save_measure(rows_m)
            st.success("Saved measurements for %s" % mk)
    ms = sorted(st.session_state.measure, key=lambda r: r["date"])
    if not ms:
        st.info("No measurements saved yet.")
    else:
        mm1, mm2, mm3 = st.columns(3)
        for col, key_, label in ((mm1, "chest", "Chest"), (mm2, "waist", "Waist"), (mm3, "arms", "Arms")):
            vals = [r[key_] for r in ms if r[key_] > 0]
            if vals:
                col.metric(label, "%g cm" % vals[-1], "%+.1f since first" % (vals[-1] - vals[0]), delta_color="off")
            else:
                col.metric(label, "-")
        with st.expander("All measurements"):
            st.dataframe(pd.DataFrame(ms[::-1]), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------- PROFILE
else:
    st.title("👤 Profile")
    c1, c2 = st.columns(2)
    age = c1.number_input("Age (years)", min_value=10, max_value=90, value=int(prof["age"]), step=1)
    gender = c2.selectbox("Gender", ["Male", "Female"], index=0 if prof["gender"] == "Male" else 1)
    c3, c4 = st.columns(2)
    height = c3.number_input("Height (cm)", min_value=100, max_value=230, value=int(prof["height"]), step=1)
    weight = c4.number_input("Weight (kg)", min_value=25.0, max_value=250.0, value=float(prof["weight"]), step=0.5)
    tw_default = float(prof.get("target_weight", 0) or 0)
    tweight = st.number_input("Target weight in kg (0 = no target)", min_value=0.0, max_value=250.0, value=tw_default, step=0.5)
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
            "target_weight": float(tweight),
            "start_weight": float(prof.get("start_weight", 0) or 0),
        }
        newp = st.session_state.profile
        if float(tweight) != float(prof.get("target_weight", 0) or 0) or newp["start_weight"] <= 0:
            newp["start_weight"] = float(weight)  # goal starts from the weight you have now
        if abs(float(weight) - float(prof["weight"])) > 0.001:
            todayk = today_str()
            st.session_state.weights = [r for r in st.session_state.weights if r["date"] != todayk] + [{"date": todayk, "weight": round(float(weight), 1)}]
            st.session_state.weights.sort(key=lambda r: r["date"])
            save_weights(st.session_state.weights)
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
    st.button("🔄 Not you? Switch user", key="switch_profile", on_click=switch_user, use_container_width=True)
    st.caption("BMR = calories your body burns at rest. Daily calories = BMR x activity, then goal added or removed. These are estimates.")
