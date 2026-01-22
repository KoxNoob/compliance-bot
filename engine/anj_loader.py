import pandas as pd
import streamlit as st

ANJ_URL = "https://docs.google.com/spreadsheets/d/1vN4_qEFr7b3XmC1v88j4U6v2-M5hS3p6/edit#gid=0"


def load_anj_data(url, sheet_name):
    try:
        file_id = url.split('/')[-2]
        csv_url = f"https://docs.google.com/spreadsheets/d/{file_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

        # --- LOGIQUE PAR SPORT (Ce qui marchait avant) ---
        if sheet_name == "Billard":  # Pour le Snooker
            skip_n = 3  # Ligne 4 Excel
        elif sheet_name in ["Football", "Badminton"]:
            skip_n = 4  # Ligne 5 Excel
        else:
            skip_n = 4  # Par défaut pour Golf et les autres

        df = pd.read_csv(csv_url, skiprows=skip_n)

        # Nettoyage des colonnes
        df.columns = [str(c).split('$')[0].strip().replace('\n', ' ') for c in df.columns]

        # Nettoyage des données : on enlève les lignes vides
        if "Nom commun" in df.columns:
            df = df.dropna(subset=["Nom commun"])
            df["Nom commun"] = df["Nom commun"].astype(str).str.strip()

        df.attrs['source_ref'] = f"ANJ Regulatory List"
        return df
    except Exception as e:
        return pd.DataFrame()


def decide_for_sport(comp_name: str, df: pd.DataFrame, sport_name: str):
    """
    Tranche selon le sport : gère le Genre pour le Foot/Bad,
    et l'ignore pour le Snooker.
    """
    try:
        # Nettoyage pour la recherche
        comp_name_clean = comp_name.strip()
        mask = df['Nom commun'].astype(str).str.strip() == comp_name_clean

        if not mask.any():
            return {"allowed": False, "competition": comp_name}

        row = df[mask].iloc[0]

        # Récupération des données communes
        res = str(row.get('Restrictions', 'Aucune'))
        pha = str(row.get('Phases', 'Toutes'))
        cou = str(row.get('Pays', 'N/A'))

        # LOGIQUE PARTICULIÈRE : Genre ou pas Genre
        if sport_name.lower() == "snooker":
            gen = "N/A (Non applicable)"
        else:
            gen = str(row.get('Genre', 'Tous'))

        # Blocage auto pour certains termes
        is_allowed = True
        if "q-school" in comp_name.lower(): is_allowed = False

        return {
            "allowed": is_allowed,
            "competition": comp_name,
            "restrictions": res if res != "nan" else "Aucune",
            "phases": pha if pha != "nan" else "Toutes",
            "country": cou if cou != "nan" else "N/A",
            "genre": gen if gen != "nan" else "N/A",
            "sport": sport_name,
            "source": df.attrs.get('source_ref', "ANJ List")
        }
    except:
        return {"allowed": False, "competition": comp_name}


# Constantes pour les handlers
COMPETITION_COL = "Nom commun"
GENRE_COL = "Genre"
RESTRICTION_COL = "Restrictions"
PHASES_COL = "Phases"
COUNTRY_COL = "Pays"
DISCIPLINE_COL = "Discipline"