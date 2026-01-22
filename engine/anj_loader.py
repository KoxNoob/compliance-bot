import pandas as pd
import streamlit as st

ANJ_URL = "https://docs.google.com/spreadsheets/d/1vN4_qEFr7b3XmC1v88j4U6v2-M5hS3p6/edit#gid=0"


@st.cache_data(ttl=3600)
def load_anj_data(url, sheet_name):
    try:
        file_id = url.split('/')[-2]
        csv_url = f"https://docs.google.com/spreadsheets/d/{file_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

        # 1. Scan pour trouver l'index de la ligne d'en-tête
        df_scan = pd.read_csv(csv_url, header=None, nrows=20)
        found_row_index = None
        for i, row in df_scan.iterrows():
            # Recherche plus large pour éviter les problèmes de casse ou d'espaces
            line_str = " ".join(row.astype(str)).lower()
            if "nom commun" in line_str:
                found_row_index = i
                break

        skip_n = found_row_index if found_row_index is not None else 0

        # 2. Chargement réel
        df = pd.read_csv(csv_url, skiprows=skip_n)

        # 3. Nettoyage immédiat des noms de colonnes
        df.columns = [str(c).split('$')[0].strip().replace('\n', ' ') for c in df.columns]

        # 4. NETTOYAGE CRUCIAL DES DONNÉES
        # On supprime les lignes où 'Nom commun' est vide ou contient le nom de la colonne lui-même
        if "Nom commun" in df.columns:
            # Enlève les lignes vides
            df = df.dropna(subset=["Nom commun"])
            # Enlève les lignes de texte parasites (ex: si le scan a pris une ligne de titre)
            df = df[df["Nom commun"].astype(str).lower() != "nom commun"]
            # Nettoyage des espaces blancs dans les données
            df["Nom commun"] = df["Nom commun"].astype(str).strip()

        df.attrs['source_ref'] = f"ANJ List - {sheet_name}"
        return df
    except Exception:
        return pd.DataFrame()


def decide_for_sport(comp_name: str, df: pd.DataFrame, sport_name: str):
    try:
        # On s'assure que la recherche est insensible à la casse et aux espaces
        df_clean = df.copy()
        df_clean['match_col'] = df_clean['Nom commun'].astype(str).strip()

        mask = df_clean['match_col'] == comp_name.strip()
        if not mask.any():
            return {"allowed": False, "competition": comp_name, "reason": "Non trouvé dans la liste"}

        row = df_clean[mask].iloc[0]

        # Récupération avec valeurs par défaut
        res = str(row.get('Restrictions', 'Aucune'))
        pha = str(row.get('Phases', 'Toutes'))
        cou = str(row.get('Pays', 'International'))
        gen = str(row.get('Genre', 'Open'))

        # Logique de blocage spécifique
        allowed = True
        low_name = comp_name.lower()
        if "q-school" in low_name:
            allowed = False
        if "exhibition" in low_name:
            allowed = False

        return {
            "allowed": allowed,
            "competition": comp_name,
            "restrictions": res if pd.notna(res) and res.lower() != "nan" else "Aucune",
            "phases": pha if pd.notna(pha) and pha.lower() != "nan" else "Toutes",
            "country": cou if pd.notna(cou) and cou.lower() != "nan" else "N/A",
            "genre": gen if pd.notna(gen) and gen.lower() != "nan" else "N/A",
            "sport": sport_name,
            "source": df.attrs.get('source_ref', "ANJ List")
        }
    except Exception as e:
        return {"allowed": False, "competition": comp_name, "error": str(e)}


# Constantes de compatibilité
COMPETITION_COL = "Nom commun"
GENRE_COL = "Genre"
RESTRICTION_COL = "Restrictions"
PHASES_COL = "Phases"
COUNTRY_COL = "Pays"
DISCIPLINE_COL = "Discipline"