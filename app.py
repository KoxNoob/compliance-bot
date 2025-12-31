import streamlit as st
import pandas as pd
from engine.anj_loader import load_anj_data, ANJ_URL
from engine.football_handler import handle_football_search, decide_football
from engine.badminton_handler import handle_badminton_search, decide_badminton
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
    else:
        data = decide_badminton(comp_name, df, genre=genre, discipline=discipline)

    data['restrictions'] = localize_value(data['restrictions'], lang, 'restrictions')
    data['phases'] = localize_value(data['phases'], lang, 'phases')
    data['emoji'] = get_emoji(data.get('country', 'International'))

    # Mapping Men/Women pour l'affichage final
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

    # On charge la source pour l'affichage dynamique
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
    selected_sport = st.selectbox("Choose a sport:", ["Football", "Badminton"], on_change=reset_selection_state)

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
        else:
            matches = handle_badminton_search(user_prompt, df_anj, selected_discipline)

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

    if st.session_state.awaiting_choice:
        with st.chat_message("assistant"):
            st.info("Multiple competitions found. Please specify:")
            for opt in st.session_state.options:
                g_map = {"Homme": "Men", "Femme": "Women", "Mixte": "Mixed"}
                g_en = g_map.get(opt[2], opt[2])
                label = f"{opt[0]} ({selected_discipline + ' - ' if selected_discipline else ''}{g_en})"

                if st.button(label, key=f"btn_{opt[0]}_{opt[2]}_{selected_sport}", width='stretch'):
                    st.session_state.awaiting_choice = False
                    st.session_state.options = []
                    display_final_decision(opt[0], df_anj, "en", selected_sport, genre=opt[2],
                                           discipline=selected_discipline)

elif page == "📂 Source Files":
    st.title("📂 Files and Data")
    preview_sport = st.selectbox("Preview data for:", ["Football", "Badminton"])
    df_preview = load_anj_data(ANJ_URL, preview_sport)

    st.info(f"Regulatory document: **{df_preview.attrs.get('source_ref')}**")
    st.link_button("🔗 Open ANJ File (Google Drive)", ANJ_URL)
    st.dataframe(df_preview, width='stretch')