import streamlit as st
import pandas as pd
from engine.anj_loader import load_anj_data, ANJ_URL
from engine.football_handler import handle_football_search, decide_football
from engine.badminton_handler import handle_badminton_search, decide_badminton
from engine.golf_handler import handle_golf_search, decide_golf
from engine.templates import TEMPLATES, get_emoji, localize_value

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

    data['restrictions'] = localize_value(data['restrictions'], lang, 'restrictions')
    data['phases'] = localize_value(data['phases'], lang, 'phases')
    data['emoji'] = get_emoji(data.get('country', 'International'))

    g_map = {"Homme": "Men", "Femme": "Women", "Mixte": "Mixed"}
    data['genre_en'] = g_map.get(data.get('genre'), data.get('genre', 'N/A'))
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

        # LOGIQUE DE DÉCISION
        if len(matches) == 1 and selected_sport != "Badminton":
            # Cas Ryder Cup : Réponse directe car un seul match trouvé
            display_final_decision(matches[0][0], df_anj, "en", selected_sport, genre=matches[0][2])
        elif len(matches) > 1 or (len(matches) == 1 and selected_sport == "Badminton"):
            # Cas avec plusieurs choix ou Badminton
            st.session_state.awaiting_choice = True
            st.session_state.options = matches
            st.rerun()
        elif len(matches) == 0 and selected_sport == "Golf":
            # Cas Evian : Mode pédagogique
            st.session_state.awaiting_choice = True
            st.session_state.options = [("Men's Tournament", 0, "Homme"), ("Women's Tournament", 0, "Femme")]

            msg = (
                "Competition not recognized in the direct list. However, it might be allowed if it belongs to a major circuit.\n\n"
                "Is this a **Men's** or **Women's** tournament?\n\n"
                "💡 *Note: **LPGA Tour** is authorized for women. **PGA Tour**, **DP World Tour**, and **LIV International Golf Series** are authorized for men.*"
            )
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
                # i garantit une clé unique même si les labels sont identiques
                if st.button(opt[0], key=f"btn_opt_{i}", width='stretch'):
                    st.session_state.awaiting_choice = False
                    if opt[1] == 0:  # Réponse circuit
                        circuit_txt = "LPGA Tour" if opt[
                                                         2] == "Femme" else "PGA Tour, DP World Tour, or LIV International Golf Series"
                        resp = f"For **{opt[2]}** golf, the authorized circuits are: **{circuit_txt}**."
                        st.session_state.chat_history.append(("assistant", resp))
                    else:
                        display_final_decision(opt[0], df_anj, "en", selected_sport, genre=opt[2],
                                               discipline=selected_discipline)
                    st.session_state.options = []
                    st.rerun()

elif page == "📂 Source Files":
    st.title("📂 Files and Data")
    preview_sport = st.selectbox("Preview data for:", ["Football", "Badminton", "Golf"])
    df_preview = load_anj_data(ANJ_URL, preview_sport)
    st.info(f"Regulatory document: **{df_preview.attrs.get('source_ref')}**")
    st.link_button("🔗 Open ANJ File (Google Drive)", ANJ_URL)
    st.dataframe(df_preview, width='stretch')