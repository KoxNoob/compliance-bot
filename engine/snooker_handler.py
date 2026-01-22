import pandas as pd
from engine.anj_loader import COMPETITION_COL, RESTRICTION_COL, PHASES_COL, COUNTRY_COL


def handle_snooker_search(user_prompt, df_anj):
    """Recherche Snooker avec mapping WST et Championnat du Monde"""
    query = user_prompt.lower().strip()

    # Mapping pour faciliter la recherche
    mapping = {
        "snooker" : "billard",
        "world snooker tour": "wst",
        "world championship": "championnat du monde",
        "masters": "masters"
    }
    for eng, fr in mapping.items():
        query = query.replace(eng, fr)

    matches = []
    for idx, row in df_anj.iterrows():
        file_name_orig = str(row[COMPETITION_COL])
        file_name_clean = file_name_orig.lower().strip()

        if query in file_name_clean or file_name_clean in query:
            # Le snooker n'a pas de colonne Genre (souvent Mixte/Open)
            matches.append((file_name_orig, 100, "Mixte"))

    return list(set(matches))


def decide_snooker(comp_name: str, df: pd.DataFrame):
    """Logique de décision pour le Snooker"""
    try:
        mask = (df[COMPETITION_COL] == comp_name)
        row = df[mask].iloc[0]

        return {
            "allowed": True,
            "competition": comp_name,
            "restrictions": str(row[RESTRICTION_COL]) if not pd.isna(row[RESTRICTION_COL]) else "NONE",
            "phases": str(row[PHASES_COL]) if not pd.isna(row[PHASES_COL]) else "ALL",
            "source": df.attrs.get('source_ref', "ANJ Source"),
            "country": str(row[COUNTRY_COL]) if not pd.isna(row[COUNTRY_COL]) else "International",
            "sport": "Snooker",
            "genre": "Open"
        }
    except:
        return {"allowed": False, "competition": comp_name}