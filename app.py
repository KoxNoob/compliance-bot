import streamlit as st
import pandas as pd
from engine.anj_loader import load_anj_data, ANJ_URL
from engine.football_handler import handle_football_search, decide_football
from engine.badminton_handler import handle_badminton_search, decide_badminton
from engine.golf_handler import handle_golf_search, decide_golf
from engine.templates import TEMPLATES, get_emoji, localize_value

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Compliance ChatBot", layout="wide")


def reset_selection_state():
    st.session_state.awaiting_choice = False
    st.session_state.options = []


# --- 2. SIDEBAR (NAVIGATION MENU) ---
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

    data['restrictions'] = localize_value(data['restrictions'], lang, 'restrictions')
    data['phases'] = localize_value(data['phases'], lang, 'phases')
    data['emoji'] = get_emoji(data.get('country', 'International'))

    gender_map = {"Homme": "Men", "Femme": "Women", "Mixte": "Mixed"}
    data['genre_en'] = gender_map.get(data.get('genre'), data.get('genre', "N/A"))
    data['discipline_en'] = discipline if discipline else "N/A"

    response = TEMPLATES[lang]["allowed"].format(**data)
    st.session_state.chat_history.append(("assistant", response))
    st.rerun()


# --- 5. PAGE CONTENT ---
if page == "🏠 Home":
    st.title("🤖 Compliance ChatBot")
    st.subheader("Welcome to your Compliance Assistant.")

    # On utilise Football par défaut pour la source dynamique en Home
    df_anj_home = load_anj_data(ANJ_URL, "Football")
    DYNAMIC_SOURCE = df_anj_home.attrs.get('source_ref', "ANJ Regulatory List")

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

    selected_sport = st.selectbox("Choose a sport:", ["Football", "Badminton", "Golf"], on_change=reset_selection_state)

    selected_discipline = None
    if selected_sport == "Badminton":
        selected_discipline = st.radio("Choose Discipline:", ["Singles", "Doubles"], horizontal=True)

    df_anj = load_anj_data(ANJ_URL, selected_sport)
    DYNAMIC_SOURCE = df_anj.attrs.get('source_ref', "ANJ Regulatory List")

    for role, message in st.session_state.chat_history:
        st.chat_message(role).markdown(message)

    user_prompt = st.chat_input(f"Your question about {selected_sport}...")

    if user_prompt and not st.session_state.awaiting_choice:
        st.session_state.chat_history.append(("user", user_prompt))

        if selected_sport == "Football":
            matches = handle_football_search(user_prompt, df_anj)
        elif selected_sport == "Badminton":
            matches = handle_badminton_search(user_prompt, df_anj, selected_discipline)
        elif selected_sport == "Golf":
            matches = handle_golf_search(user_prompt, df_anj)

        # --- LOGIQUE DE SORTIE GOLF ---
        if selected_sport == "Golf":
            if len(matches) == 1:
                # MATCH UNIQUE (ex: Ryder Cup) -> Réponse directe
                display_final_decision(matches[0][0], df_anj, "en", "Golf", genre=matches[0][2])
            elif len(matches) > 1:
                # DOUBLON (ex: JO) -> Demander précision
                st.session_state.awaiting_choice = True
                st.session_state.options = matches
                st.rerun()
            else:
                # AUCUN MATCH (ex: Evian) -> DÉCLENCHEMENT DE L'AIDE PAR GENRE
                st.session_state.awaiting_choice = True
                # On crée des options fictives pour Homme/Femme pour forcer le choix pédagogique
                st.session_state.options = [("Men's Tournament", 0, "Homme"), ("Women's Tournament", 0, "Femme")]

                msg = (
                    "Competition not recognized in the direct list. However, it might be allowed if it belongs to a major circuit.\n\n"
                    "Is this a **Men's** or **Women's** tournament?\n\n"
                    "💡 *Note: **LPGA Tour** is authorized for women. **PGA Tour**, **DP World Tour**, and **LIV International Golf Series** are authorized for men.*"
                )
                st.chat_message("assistant").markdown(msg)
                st.session_state.chat_history.append(("assistant", msg))
                st.rerun()

        # --- LOGIQUE STANDARD (FOOT/BAD) ---
        else:
            if len(matches) > 1:
                st.session_state.awaiting_choice = True
                st.session_state.options = matches
                st.rerun()
            elif len(matches) == 1:
                display_final_decision(matches[0][0], df_anj, "en", selected_sport, genre=matches[0][2],
                                       discipline=selected_discipline)
            else:
                msg = TEMPLATES["en"]["not_found"].format(source=DYNAMIC_SOURCE)
                st.session_state.chat_history.append(("assistant", msg))
                st.rerun()

        # --- GESTION DES BOUTONS DE CHOIX ---
    if st.session_state.awaiting_choice:
        with st.chat_message("assistant"):
            st.info("Please select an option:")
            for opt in st.session_state.options:
                label = opt[0]  # Nom de la comp ou "Men's Tournament"
                if st.button(label, key=f"btn_{label}_{opt[2]}", width='stretch'):
                    st.session_state.awaiting_choice = False

                    if opt[1] == 0:  # C'est un choix de circuit (Evian case)
                        circuit_msg = (
                                          f"For **{opt[2]}** golf, the authorized circuits are: "
                                          "**LPGA Tour**" if opt[
                                                                 2] == "Femme" else "**PGA Tour, DP World Tour, and LIV International Golf Series**."
                                      ) + ""
                        st.session_state.chat_history.append(("assistant", circuit_msg))
                        st.rerun()
                    else:
                        # C'est un match réel (JO ou autre)
                        display_final_decision(opt[0], df_anj, "en", selected_sport, genre=opt[2],
                                               discipline=selected_discipline)

    if st.session_state.awaiting_choice:
        with st.chat_message("assistant"):
            if selected_sport != "Golf":
                st.info("Multiple competitions found. Please specify:")

            for opt in st.session_state.options:
                g_map = {"Homme": "Men", "Femme": "Women", "Mixte": "Mixed"}
                g_en = g_map.get(opt[2], opt[2])

                if selected_sport == "Badminton":
                    label = f"{opt[0]} ({selected_discipline} - {g_en})"
                else:
                    label = f"{opt[0]} ({g_en})"

                if st.button(label, key=f"btn_{opt[0]}_{opt[2]}_{selected_sport}", width='stretch'):
                    st.session_state.awaiting_choice = False
                    st.session_state.options = []
                    display_final_decision(opt[0], df_anj, "en", selected_sport, genre=opt[2],
                                           discipline=selected_discipline)

            st.markdown("---")
            label_none = TEMPLATES["en"].get("none_of_above", "None of these options")
            if st.button(f"🚫 {label_none}", key="btn_none_of_above", width='stretch'):
                st.session_state.awaiting_choice = False
                st.session_state.options = []
                msg = TEMPLATES["en"]["not_found"].format(source=DYNAMIC_SOURCE)
                st.session_state.chat_history.append(("assistant", msg))
                st.rerun()

elif page == "📂 Source Files":
    preview_sport = st.selectbox("Preview data for:", ["Football", "Badminton", "Golf"], key="preview_sport")
    df_preview = load_anj_data(ANJ_URL, preview_sport)
    st.title("📂 Files and Data")
    st.info(f"Regulatory document: **{df_preview.attrs.get('source_ref')}**")
    st.link_button("🔗 Open ANJ File (Google Drive)", ANJ_URL)
    st.dataframe(df_preview, width='stretch')