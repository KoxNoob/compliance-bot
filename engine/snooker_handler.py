import pandas as pd
from engine.matcher import get_matches_multiples
from engine.anj_loader import decide_fr_sport

def handle_snooker_search(user_prompt, df_anj):
    """Recherche Snooker en utilisant le Matcher global avec un pré-nettoyage"""
    query = user_prompt.lower().strip()

    # On garde ton mapping malin pour aider le matcher
    mapping = {
        "world snooker tour": "wst",
        "world championship": "championnat du monde",
        "masters": "masters"
    }
    for eng, fr in mapping.items():
        query = query.replace(eng, fr)

    # On appelle ton matcher global (threshold à 65 comme demandé)
    return get_matches_multiples(query, df_anj, threshold=65)

def decide_snooker(comp_name: str, df: pd.DataFrame):
    """
    Logique de décision pour le Snooker.
    On appelle la fonction centrale 'decide_fr_sport' sans genre.
    """
    # On appelle la fonction universelle que tu as dans anj_loader
    # Elle gérera déjà les restrictions, les phases et la source
    return decide_fr_sport(comp_name, df)