import pandas as pd
import streamlit as st
import requests
from io import BytesIO

# Direct download URL for the Drive file
ANJ_URL = "https://docs.google.com/spreadsheets/d/1-2Kkd2xk0xXcO5DMG0-RXpZ_EgdVQk9l/export?format=xlsx"

# Column names
COMPETITION_COL = "Nom commun"
RESTRICTION_COL = "Restrictions"
PHASES_COL = "Phases"
COUNTRY_COL = "Pays"
GENRE_COL = "Genre"
DISCIPLINE_COL = "Discipline"


@st.cache_data
def load_anj_data(url: str, sport_name: str) -> pd.DataFrame:
    """
    Loads the ANJ file, extracts the source from line 1 of the specific tab,
    and cleans the data.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = BytesIO(response.content)

        # 1. EXTRACT DYNAMIC SOURCE (Cell A1)
        df_meta = pd.read_excel(content, engine='openpyxl', sheet_name=sport_name, nrows=1, header=None)
        source_val = df_meta.iloc[0, 0] if not df_meta.empty else "ANJ Regulatory List"

        content.seek(0)

        # 2. LOAD FULL DATA
        df = pd.read_excel(content, engine='openpyxl', sheet_name=sport_name, header=None)

        # Setting headers (Excel line 5 = index 4)
        df.columns = df.iloc[4]
        df = df.iloc[5:].reset_index(drop=True)

        # List of columns to propagate (ffill)
        propagation_cols = ['Sport', 'Discipline', 'Pays', 'Club/Nation', 'Nom générique', 'Genre']
        cols_to_fill = [col for col in propagation_cols if col in df.columns]
        df[cols_to_fill] = df[cols_to_fill].ffill(axis=0)

        # Cleaning
        df = df[df[COMPETITION_COL].notna()]

        # Store metadata
        df.attrs['source_ref'] = source_val
        df.attrs['sport_name'] = sport_name

        return df
    except Exception as e:
        st.error(f"Error loading {sport_name} data: {e}")
        return pd.DataFrame()


def decide_fr_sport(comp_name: str, df: pd.DataFrame, genre: str = None, discipline: str = None):
    """
    Queries the DataFrame and handles specific logic, including mapping UI Singles to File Simple.
    """
    try:
        # 1. Filtrage par nom
        mask = df[COMPETITION_COL].str.lower() == comp_name.lower()

        # 2. Filtrage par Genre (si fourni)
        if genre:
            mask = mask & (df[GENRE_COL].str.lower() == genre.lower())

        # 3. Filtrage par Discipline (Singles/Doubles)
        if discipline:
            # Mapping anglais UI -> français Excel
            search_discipline = "Simple" if discipline == "Singles" else "Double"
            mask = mask & (df[DISCIPLINE_COL].str.lower() == search_discipline.lower())

        row = df[mask].iloc[0]
        restrictions_value = row[RESTRICTION_COL]
        phases_value = row[PHASES_COL]

        # --- SPECIFIC FIFA RANKING MODIFICATION ---
        if str(restrictions_value).strip() == "Classement FIFA **":
            restrictions_code = "Classement FIFA **"
            phases_code = "** FIFA category A international friendly matches, between two teams both ranked in the top fifty of the FIFA rankings, in force 30 days before the date of the match concerned."
        else:
            is_restrictions_none = pd.isna(restrictions_value) or str(restrictions_value).strip().lower() == 'aucune'
            is_phases_none = pd.isna(phases_value) or str(phases_value).strip().lower() == 'aucune'
            restrictions_code = "NONE" if is_restrictions_none else str(restrictions_value)
            phases_code = "ALL" if is_phases_none else str(phases_value)
            if phases_code != "ALL":
                restrictions_code = "LIMITED_PHASES"

        return {
            "allowed": True,
            "competition": comp_name,
            "restrictions": restrictions_code,
            "phases": phases_code,
            "source": df.attrs.get('source_ref', "ANJ Source"),
            "country": str(row[COUNTRY_COL]) if not pd.isna(row[COUNTRY_COL]) else "International",
            "sport": str(row['Sport']) if 'Sport' in row.index else df.attrs.get('sport_name'),
            "genre": str(row[GENRE_COL]) if GENRE_COL in row.index else "N/A",
            "discipline": discipline  # Return the English term used in the UI
        }
    except (IndexError, KeyError):
        return {"allowed": False, "competition": comp_name, "source": df.attrs.get('source_ref', "ANJ Source")}