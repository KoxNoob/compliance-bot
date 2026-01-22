import pandas as pd
import streamlit as st

ANJ_URL = "https://docs.google.com/spreadsheets/d/1vN4_qEFr7b3XmC1v88j4U6v2-M5hS3p6/edit#gid=0"


@st.cache_data(ttl=3600)
def load_anj_data(url, sheet_name):
    try:
        file_id = url.split('/')[-2]
        csv_url = f"https://docs.google.com/spreadsheets/d/{file_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

        # Auto-scan pour trouver la ligne d'en-tête (Ligne 4 ou 5)
        df_scan = pd.read_csv(csv_url, header=None, nrows=20)
        found_row_index = None
        for i, row in df_scan.iterrows():
            if row.astype(str).str.contains("Nom commun", case=False).any():
                found_row_index = i
                break

        skip_n = found_row_index if found_row_index is not None else 0
        df = pd.read_csv(csv_url, skiprows=skip_n)

        # Nettoyage des colonnes
        df.columns = [str(c).split('$')[0].strip().replace('\n', ' ') for c in df.columns]

        # Nettoyage des lignes vides
        if not df.empty:
            df = df.dropna(how='all', subset=[df.columns[0]])

        df.attrs['source_ref'] = f"ANJ List - {sheet_name}"
        return df
    except Exception:
        return pd.DataFrame()


def decide_for_sport(comp_name: str, df: pd.DataFrame, sport_name: str):
    """
    Fonction de décision universelle intégrée au loader.
    Fonctionne pour Foot (avec Genre) et Snooker (sans Genre).
    """
    try:
        # Recherche de la ligne
        mask = df['Nom commun'] == comp_name
        if not mask.any():
            return {"allowed": False, "competition": comp_name, "reason": "Not found"}

        row = df[mask].iloc[0]

        # Récupération sécurisée des colonnes (car elles varient selon le sport)
        res = str(row.get('Restrictions', 'Aucune'))
        pha = str(row.get('Phases', 'Toutes'))
        cou = str(row.get('Pays', 'International'))
        gen = str(row.get('Genre', 'Open'))  # 'Open' par défaut si la colonne manque

        # Logique de blocage spécifique (ex: Q-School pour le Snooker)
        allowed = True
        if "q-school" in comp_name.lower():
            allowed = False

        return {
            "allowed": allowed,
            "competition": comp_name,
            "restrictions": res if pd.notna(res) and res != "nan" else "Aucune",
            "phases": pha if pd.notna(pha) and pha != "nan" else "Toutes",
            "country": cou if pd.notna(cou) and cou != "nan" else "N/A",
            "genre": gen if pd.notna(gen) and gen != "nan" else "N/A",
            "sport": sport_name,
            "source": df.attrs.get('source_ref', "ANJ List")
        }
    except Exception as e:
        return {"allowed": False, "competition": comp_name, "error": str(e)}


COMPETITION_COL = "Nom commun"
GENRE_COL = "Genre"
RESTRICTION_COL = "Restrictions"
PHASES_COL = "Phases"
COUNTRY_COL = "Pays"
DISCIPLINE_COL = "Discipline"