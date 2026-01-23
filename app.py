import streamlit as st
import pandas as pd
from engine.anj_loader import load_anj_data, ANJ_URL
from engine.football_handler import handle_football_search, decide_football
from engine.badminton_handler import handle_badminton_search, decide_badminton
from engine.golf_handler import handle_golf_search, decide_golf
from engine.templates import TEMPLATES, get_emoji, localize_value
from engine.snooker_handler import handle_snooker_search, decide_snooker

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Compliance ChatBot", layout="wide")


def reset_selection_state():
    st.session_state.awaiting_choice = False
    st.session_state.options = []


# --- 2. SIDEBAR ---
with st.sidebar:
    try:
        st.image("compliance logo.png", width=180)
    except:
        try:
            st.image("compliance logo.jpg", width=180)
        except:
            st.title("🌐 GIG")

    st.subheader("Compliance Center")
    st.divider()
    page = st.radio("Go to:", ["🏠 Home", "💬 Compliance ChatBot", "📂 Source Files"])
    st.divider()

    if page == "💬 Compliance ChatBot":
        if st.button("🗑️ Clear Question History", width='stretch'):
            st.session_state.chat_history = []
            st.session_state.awaiting_choice = False
            st.session_state.options = []
            st.rerun()

# --- 3. SESSION STATE ---
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'awaiting_choice' not in st.session_state: st.session_state.awaiting_choice = False
if 'options' not in st.session_state: st.session_state.options = []


# --- 4. LOGIC FUNCTIONS ---
def display_final_decision(comp_name, df, lang, sport, genre=None, discipline=None):
    if sport == "Football":
        data = decide_football(comp_name, df, genre=genre)
    elif sport == "Badminton":
        data = decide_badminton(comp_name, df, genre=genre, discipline=discipline)
    elif sport == "Golf":
        data = decide_golf(comp_name, df, genre=genre)
    elif sport == "Snooker":
        data = decide_snooker(comp_name, df)

    # Sécurité si la compétition n'a pas été trouvée (évite le KeyError)
    if not data.get('allowed') and 'restrictions' not in data:
        msg = TEMPLATES[lang]["not_found"].format(source=df.attrs.get('source_ref', "ANJ List"))
        st.session_state.chat_history.append(("assistant", msg))
        st.rerun()
        return

    data['restrictions'] = localize_value(data['restrictions'], lang, 'restrictions')
    data['phases'] = localize_value(data['phases'], lang, 'phases')
    data['emoji'] = get_emoji(data.get('country', 'International'))

    g_map = {"Homme": "Men", "Femme": "Women", "Mixte": "Mixed", "N/A": "Open/Mixed"}
    data['genre_en'] = g_map.get(data.get('genre'), "Open/Mixed")
    data['discipline_en'] = discipline if discipline else "N/A"

    response = TEMPLATES[lang]["allowed"].format(**data)
    st.session_state.chat_history.append(("assistant", response))
    st.rerun()


# --- 5. PAGE CONTENT ---
if page == "🏠 Home":
    st.title("🤖 Compliance ChatBot")
    st.subheader("Welcome to your Compliance Assistant.")
    df_home = load_anj_data(ANJ_URL, "Football")
    DYNAMIC_SOURCE = df_home.attrs.get('source_ref', "ANJ Regulatory List")

    st.markdown(f"""
    This tool allows you to instantly check if a competition is authorized by the ANJ.

    **Current Regulatory Source:** {DYNAMIC_SOURCE}

    ---
    **How to use:**
    1. Navigate to the **Compliance ChatBot** page.
    2. Ask about a specific competition.
    3. Get instant regulatory feedback.
    """)

elif page == "💬 Compliance ChatBot":
    st.title("💬 Compliance Q&A")
    selected_sport = st.selectbox("Choose a sport:", ["Football", "Badminton", "Golf", "Snooker"],
                                  on_change=reset_selection_state)

    selected_discipline = None
    if selected_sport == "Badminton":
        selected_discipline = st.radio("Choose Discipline:", ["Singles", "Doubles"], horizontal=True)

    # Aiguillage vers l'onglet Billard pour le Snooker
    target_sheet = "Billard" if selected_sport == "Snooker" else selected_sport
    df_anj = load_anj_data(ANJ_URL, target_sheet)
    DYNAMIC_SOURCE = df_anj.attrs.get('source_ref', "ANJ Regulatory List")

    for role, message in st.session_state.chat_history:
        st.chat_message(role).markdown(message)

    user_prompt = st.chat_input(f"Your question about {selected_sport}...")

    if user_prompt and not st.session_state.awaiting_choice:
        st.session_state.chat_history.append(("user", user_prompt))

        # 1. RECHERCHE
        if selected_sport == "Football":
            matches = handle_football_search(user_prompt, df_anj)
        elif selected_sport == "Badminton":
            matches = handle_badminton_search(user_prompt, df_anj, selected_discipline)
        elif selected_sport == "Golf":
            matches = handle_golf_search(user_prompt, df_anj)
        elif selected_sport == "Snooker":
            matches = handle_snooker_search(user_prompt, df_anj)

        # 2. LOGIQUE DE ROUTAGE
        # Match unique et précis (Score >= 90)
        if len(matches) == 1 and matches[0][1] >= 90 and selected_sport in ["Football", "Golf", "Snooker"]:
            display_final_decision(matches[0][0], df_anj, "en", selected_sport, genre=matches[0][2])

        # Cas spécifique SNOOKER : Message pédagogique direct au lieu de boutons compliqués
        elif selected_sport == "Snooker":
            msg = (
                "🔍 **Information:** For Snooker, only professional tournaments belonging to the **World Snooker Tour (WST)** are authorized.\n\n"
                "This includes major events like the World Championship, The Masters, and the UK Championship."
            )
            st.session_state.chat_history.append(("assistant", msg))
            st.rerun()

        elif len(matches) > 0:
            st.session_state.awaiting_choice = True
            st.session_state.options = matches

            # Cas spécifique Evian / Golf
            if selected_sport == "Golf" and any("evian" in str(m[0]).lower() for m in matches):
                msg = "Is this a **Men's** or **Women's** tournament?\n\n💡 *Note: **Evian Championship** is a Women's major.*"
                st.session_state.chat_history.append(("assistant", msg))
            st.rerun()

        elif selected_sport == "Golf":
            st.session_state.awaiting_choice = True
            st.session_state.options = [("Men's Tournament", 0, "Homme"), ("Women's Tournament", 0, "Femme")]
            msg = "Is this a **Men's** or **Women's** tournament?\n\n💡 *Note: **LPGA Tour** (Women), **PGA/DP World/LIV** (Men).*"
            st.session_state.chat_history.append(("assistant", msg))
            st.rerun()

        else:
            msg = TEMPLATES["en"]["not_found"].format(source=DYNAMIC_SOURCE)
            st.session_state.chat_history.append(("assistant", msg))
            st.rerun()

    if st.session_state.awaiting_choice:
        with st.chat_message("assistant"):
            st.info("Please select an option:")

            for i, opt in enumerate(st.session_state.options):
                g_map = {"Homme": "Men", "Femme": "Women", "Mixte": "Mixed", "N/A": "Open"}
                gender_display = g_map.get(opt[2], opt[2])
                label = f"{opt[0]} ({gender_display})" if opt[1] != 0 else opt[0]

                if st.button(label, key=f"btn_{selected_sport}_{i}_{opt[2]}", width='stretch'):
                    st.session_state.awaiting_choice = False

                    if opt[1] == 0 or "Tournament" in str(opt[0]):
                        genre_label = "Women" if opt[2] == "Femme" else "Men"
                        if opt[2] == "Femme":
                            circuit_txt = "**LPGA Tour**"
                            warning_txt = ""
                        else:
                            circuit_txt = "**PGA Tour**, **DP World Tour**, or **LIV International Golf Series**"
                            warning_txt = "\n\n⚠️ **Important:** Do not confuse the *PGA Tour* (Authorized) with the *PGA Tour Champions* (Not Authorized)."

                        resp = f"For **{genre_label}** golf, the authorized circuits are: {circuit_txt}.{warning_txt}"
                        st.session_state.chat_history.append(("assistant", resp))
                    else:
                        display_final_decision(opt[0], df_anj, "en", selected_sport, genre=opt[2],
                                               discipline=selected_discipline)

                    st.session_state.options = []
                    st.rerun()

elif page == "📂 Source Files":
    st.title("📂 Files and Data")
    preview_sport = st.selectbox("Preview data for:", ["Football", "Badminton", "Golf", "Snooker"])

    # Aiguillage correct pour l'aperçu du Snooker
    target_preview = "Billard" if preview_sport == "Snooker" else preview_sport
    df_preview = load_anj_data(ANJ_URL, target_preview)

    st.info(f"Regulatory document: **{df_preview.attrs.get('source_ref')}**")
    st.link_button("🔗 Open ANJ File (Google Drive)", ANJ_URL)
    st.dataframe(df_preview, width='stretch')