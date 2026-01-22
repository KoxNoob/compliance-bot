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
def load_anj_data(url, sheet_name):
    try:
        file_id = url.split('/')[-2]
        csv_url = f"https://docs.google.com/spreadsheets/d/{file_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

        # 1. On lit les 20 premières lignes pour scanner l'en-tête
        df_scan = pd.read_csv(csv_url, header=None, nrows=20)

        found_row_index = None
        for i, row in df_scan.iterrows():
            # On cherche "Nom commun" dans n'importe quelle cellule de la ligne
            if row.astype(str).str.contains("Nom commun", case=False).any():
                found_row_index = i
                break

        if found_row_index is None:
            st.error(f"⚠️ Impossible de trouver 'Nom commun' dans l'onglet {sheet_name}")
            return pd.DataFrame()

        # LOG DE LA LIGNE DÉTECTÉE
        # L'index 0 de pandas correspond à la Ligne 1 d'Excel
        excel_line = found_row_index + 1
        st.toast(f"ℹ️ {sheet_name}: Headers detected at Excel line {excel_line}")

        # 2. On recharge le DF à partir de la ligne détectée
        df = pd.read_csv(csv_url, skiprows=found_row_index)

        # 3. Nettoyage des colonnes
        df.columns = [str(c).split('$')[0].strip().replace('\n', ' ') for c in df.columns]

        # 4. Nettoyage des lignes vides
        df = df.dropna(how='all', subset=[df.columns[0]]) if len(df) > 0 else df

        df.attrs['source_ref'] = "ANJ Regulatory List"
        return df

    except Exception as e:
        st.error(f"Error loading {sheet_name}: {e}")
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