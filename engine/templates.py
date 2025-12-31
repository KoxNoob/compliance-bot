import pandas as pd

# --- CONFIGURATION DES EMOJIS ---
COUNTRY_EMOJIS = {
    "France": "🇫🇷",
    "Italie": "🇮🇹",
    "Espagne": "🇪🇸",
    "Allemagne": "🇩🇪",
    "Angleterre": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Amérique du Sud": "🌎",
    "Amérique du Nord, Centrale et Caraïbes": "🌎",
    "Amérique du Nord, Centrale": "🌎",
    "Asie": "🌏",
    "Afrique": "🌍",
    "Europe": "🇪🇺",
    "International": "🌎",
}

# --- DICTIONNAIRES DE TRADUCTION ---
PHASES_TRANSLATIONS = {
    "Tous les matchs (à l'exception du 1er tour de qualification de la voie principale)": {
        "en": "All matches (except the 1st qualifying round of the main path)",
        "es": "Todos los partidos (excepto la 1ª ronda de clasificación de la vía principal)"
    },
    "A partir du tournoi final": {
        "en": "Starting from the final tournament",
        "es": "A partir del torneo final"
    },
    "Tournoi final": {
        "en": "Final tournament",
        "es": "Torneo final"
    },
    "Demi-finales et finale": {
        "en": "Semi-finals and Final",
        "es": "Semifinales y final"
    },
    "A partir des 32ème de finale": {
        "en": "Starting from the Round of 32",
        "es": "A partir de los treintaidosavos de final"
    },
    "A partir des 32èmes de finale": {
        "en": "Starting from the Round of 32",
        "es": "A partir de los treintaidosavos de final"
    },
    "A partir des 32èmes finales (\"Third round proper\")": {
        "en": "Starting from the Round of 32 (\"Third round proper\")",
        "es": "A partir de los trenteidosavos de final (\"Third round proper\")"
    },
    "A partir des 8èmes de finales": {
        "en": "Starting from the Round of 16",
        "es": "A partir de los octavos de final"
    },
    "A partir des huitièmes de finales": {
        "en": "Starting from the Round of 16",
        "es": "A partir de los octavos de final"
    },
    "A partir des 16èmes de finale": {
        "en": "Starting from the Round of 16",
        "es": "A partir de los dieciseisavos de final"
    },
    "A partir du 3ème tour": {
        "en": "Starting from the 3rd Round",
        "es": "A partir de la 3ª ronda"
    },
    "A partir du round four": {
        "en": "Starting from the Round Four",
        "es": "A partir de la ronda quatre"
    },
    "A partir du second round": {
        "en": "Starting from the Second Round",
        "es": "A partir de la segunda ronda"
    },
    "Phase finale (A partir des demi-finales)": {
        "en": "Final phase (Starting from the semi-finals)",
        "es": "Fase final (A partir de las semifinales)"
    },
    "A partir des demi-finales": {
        "en": "Starting from the semi-finals",
        "es": "A partir de las semifinales"
    },
    "A partir des quarts de finale": {
        "en": "Starting from the Quarter-finals",
        "es": "A partir de los quarts de final"
    },
    "A partir des 1/4 de finales": {
        "en": "Starting from the Quarter-finals",
        "es": "A partir de los cuartos de final"
    },
    "A partir des 1/8 de finales": {
        "en": "Starting from the Round of 16",
        "es": "A partir de los octavos de final"
    },
    "Matchs à élimination directe du tournoi final": {
        "en": "Knockout matches of the final tournament",
        "es": "Partidos de eliminación directe del torneo final"
    },
    "Ligue A et B: phase de groupe et matchs à élimination directe": {
        "en": "League A and B: group stage and knockout matches",
        "es": "Liga A et B: fase de grupos y partidos de eliminación directe"
    },
    "Phase à élimination directe": {
        "en": "Knockout phase",
        "es": "Fase de eliminación directa"
    }
}

DEFAULT_TRANSLATIONS = {
    "NONE": {"fr": "Aucune", "en": "None", "es": "Ninguna"},
    "ALL": {"fr": "Toutes phases autorisées", "en": "All phases authorised", "es": "Todas las fases autorizadas"},
    "LIMITED_PHASES": {"fr": "Phases spécifiques autorisées", "en": "Specific phases authorised", "es": "Fases específicas autorizadas"}
}

def get_emoji(country_name):
    return COUNTRY_EMOJIS.get(country_name, "🗺️")

def localize_value(value: str, lang: str, value_type: str) -> str:
    if value in DEFAULT_TRANSLATIONS:
        return DEFAULT_TRANSLATIONS[value].get(lang, value)
    if value_type == 'phases' and value in PHASES_TRANSLATIONS:
        return PHASES_TRANSLATIONS[value].get(lang, value)
    return value

TEMPLATES = {
    "en": {
        "allowed": "\n **ANJ**\n---\n✅ **Status : Allowed**\n\n🏟️ **Sport :** {sport}\n\n{emoji} **Country :** {country}\n\n🏆 **Competition :** {competition}\n\n🏸 **Category :** {discipline_en} - {genre_en}\n\n---\n**Restrictions :** {restrictions}\n\n**Allowed phases :** {phases}\n\n📄 **Source :** {source}",
        "not_found": "\n❌ **Competition not recognised**\n\n📄 **Source :** {source}",
        "none_of_above": "None of these options",
    },
    "fr": {
        "allowed": "\n **ANJ**\n---\n✅ **Statut : Autorisé**\n\n🏟️ **Sport :** {sport}\n\n{emoji} **Pays :** {country}\n\n🏆 **Compétition :** {competition}\n\n🏸 **Catégorie :** {discipline_en} - {genre_en}\n\n---\n**Restrictions :** {restrictions}\n\n**Phases autorisées :** {phases}\n\n📄 **Source :** {source}",
        "not_found": "\n❌ **Compétition non reconnue**\n\n📄 **Source :** {source}",
        "none_of_above": "Aucune de ses propositions",
    },
    "es": {
        "allowed": "\n**ANJ**\n---\n✅ **Estado : Autorizado**\n\n🏟️ **Deporte :** {sport}\n\n{emoji} **País :** {country}\n\n🏆 **Competición :** {competition}\n\n🏸 **Categoría :** {discipline_en} - {genre_en}\n\n---\n**Restricciones :** {restrictions}\n\n**Fases autorizadas :** {phases}\n\n📄 **Fuente :** {source}",
        "not_found": "\n❌ **Competición no reconocida**\n\n📄 **Fuente :** {source}",
        "none_of_above": "Ninguna de estas options"
    }
}