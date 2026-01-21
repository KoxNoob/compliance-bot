import pandas as pd
from engine.anj_loader import COMPETITION_COL, GENRE_COL, RESTRICTION_COL, PHASES_COL, COUNTRY_COL


def handle_golf_search(user_prompt, df_anj):
    """Recherche Golf avec priorité aux noms exacts"""
    query = user_prompt.lower().strip()

    # Mapping universel pour les JO
    mapping = {
        "olympic games": "jeux olympiques",
        "olympic": "jeux olympiques",
        "jo": "jeux olympiques"
    }
    for eng, fr in mapping.items():
        query = query.replace(eng, fr)

    matches = []
    for idx, row in df_anj.iterrows():
        file_name_orig = str(row[COMPETITION_COL])
        file_name_clean = file_name_orig.lower().strip()

        # 1. MATCH EXACT OU CONTENU : On vérifie si la Ryder Cup ou Solheim Cup est citée
        if query == file_name_clean or query in file_name_clean:
            matches.append((file_name_orig, 100, row[GENRE_COL]))

    return list(set(matches))


def decide_golf(comp_name: str, df: pd.DataFrame, genre: str = None):
    """Logique de décision standard pour le Golf"""
    try:
        mask = (df[COMPETITION_COL] == comp_name)
        if genre:
            mask = mask & (df[GENRE_COL] == genre)

        row = df[mask].iloc[0]

        return {
            "allowed": True,
            "competition": comp_name,
            "restrictions": row[RESTRICTION_COL] if not pd.isna(row[RESTRICTION_COL]) else "NONE",
            "phases": row[PHASES_COL] if not pd.isna(row[PHASES_COL]) else "ALL",
            "source": df.attrs.get('source_ref', "ANJ Source"),
            "country": str(row[COUNTRY_COL]) if not pd.isna(row[COUNTRY_COL]) else "International",
            "sport": "Golf",
            "genre": str(row[GENRE_COL])
        }
    except:
        return {"allowed": False, "competition": comp_name}