#!/usr/bin/env python3
"""
Travel Order Resolver — Streamlit App
Run with: streamlit run app.py
"""

import os
import sys
import warnings
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))

# Speech-to-Text
try:
    from audio_recorder_streamlit import audio_recorder
    from src.nlp.speech_to_text import transcribe_audio, is_api_key_configured, validate_audio_bytes
    SPEECH_TO_TEXT_AVAILABLE = True
except ImportError:
    SPEECH_TO_TEXT_AVAILABLE = False

# ──────────────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Travel Order Resolver",
    page_icon="🚄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────────────────────
# Cached resources
# ──────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Chargement du modele baseline...")
def get_baseline():
    from src.utils.pipeline import load_nlp_model
    return load_nlp_model("baseline")

@st.cache_resource(show_spinner="Chargement de CamemBERT (peut prendre 30s)...")
def get_camembert():
    from src.utils.pipeline import load_nlp_model
    return load_nlp_model("camembert", "models/camembert-ner")

@st.cache_resource(show_spinner="Chargement du reseau ferroviaire...")
def get_graph_and_mapping():
    from src.pathfinding.graph_loader import get_or_build_graph
    from src.utils.pipeline import load_city_mapping
    mapping = load_city_mapping()
    graph   = get_or_build_graph()
    return graph, mapping

@st.cache_data
def load_split(split: str) -> pd.DataFrame:
    return pd.read_csv(f"data/processed/{split}.csv", encoding="utf-8")

@st.cache_data
def load_stations_geo() -> pd.DataFrame:
    df = pd.read_csv("data/processed/sncf/stations_clean.csv", encoding="utf-8")
    return df[["uic_code", "station_name", "city_name", "latitude", "longitude"]].dropna()


def extract(sentence: str, model, model_type: str) -> dict:
    from src.utils.pipeline import _extract
    return _extract(sentence, model, model_type)


def _display_route(cities: list, total_time: float, segments: list = None):
    h = int(total_time // 60)
    m = int(total_time % 60)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Depart",   cities[0])
    col_b.metric("Arrivee",  cities[-1])
    col_c.metric("Duree",    f"{h}h{m:02d}" if h else f"{m} min")
    st.caption(f"{len(cities)} gares  •  {len(cities) - 2} arret(s) intermediaire(s)")

    # ── Carte géographique ──────────────────────────────────────────────────
    stations_geo = load_stations_geo()
    geo_map = stations_geo.set_index("city_name")

    route_coords = []
    for city in cities:
        # Try station_name first, then city_name
        matches = stations_geo[
            stations_geo["station_name"].str.lower() == city.lower()
        ]
        if matches.empty:
            matches = stations_geo[
                stations_geo["city_name"].str.lower() == city.lower()
            ]
        if matches.empty:
            route_coords.append({"city": city, "lat": None, "lon": None})
        else:
            row = matches.iloc[0]
            route_coords.append({
                "city": city,
                "lat": float(row["latitude"]),
                "lon": float(row["longitude"]),
            })

    coords_df = pd.DataFrame(route_coords).dropna(subset=["lat", "lon"])

    if not coords_df.empty:
        fig_map = go.Figure()

        # Line connecting route stations
        fig_map.add_trace(go.Scattergeo(
            lat=coords_df["lat"].tolist(),
            lon=coords_df["lon"].tolist(),
            mode="lines",
            line=dict(width=3, color="#1E88E5"),
            name="Route",
            showlegend=False,
        ))

        # All stations (grey background dots)
        fig_map.add_trace(go.Scattergeo(
            lat=stations_geo["latitude"].tolist(),
            lon=stations_geo["longitude"].tolist(),
            mode="markers",
            marker=dict(size=3, color="#CCCCCC", opacity=0.4),
            name="Reseau SNCF",
            hoverinfo="skip",
            showlegend=True,
        ))

        # Route stops
        colors = [
            "#FF3B30" if i == 0 else (
            "#FF3B30" if i == len(coords_df) - 1 else "#1E88E5")
            for i in range(len(coords_df))
        ]
        sizes = [
            16 if i in (0, len(coords_df) - 1) else 10
            for i in range(len(coords_df))
        ]
        fig_map.add_trace(go.Scattergeo(
            lat=coords_df["lat"].tolist(),
            lon=coords_df["lon"].tolist(),
            mode="markers+text",
            marker=dict(size=sizes, color=colors, symbol="circle"),
            text=coords_df["city"].tolist(),
            textposition="top right",
            textfont=dict(size=11),
            name="Gares",
            showlegend=False,
        ))

        fig_map.update_geos(
            scope="europe",
            center=dict(
                lat=coords_df["lat"].mean(),
                lon=coords_df["lon"].mean(),
            ),
            projection_scale=6,
            showland=True, landcolor="#F5F5F5",
            showcoastlines=True, coastlinecolor="#AAAAAA",
            showcountries=True, countrycolor="#CCCCCC",
            showframe=False,
        )
        fig_map.update_layout(
            height=480,
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.7)"),
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("Coordonnees GPS introuvables pour cet itineraire.")

    # ── Liste des gares ─────────────────────────────────────────────────────
    with st.expander("Voir toutes les gares"):
        line_badges = {
            "TGV": "🚄 *TGV*",
            "IC": "🚆 *Intercites*",
            "TER": "🚈 *TER*",
            "TRAIN": "🚆",
            "CORRESP": "🚶 *Correspondance*",
        }
        for i, city in enumerate(cities):
            icon = "🔴" if i in (0, len(cities) - 1) else "🔵"
            st.markdown(f"{icon} **{city}**" if i in (0, len(cities) - 1) else f"{icon} {city}")


def get_city_suggestions(city_name: str, gazetteer, city_mapping: dict) -> list:
    """
    Get all possible matches for a city name with connection status.

    Returns:
        List of tuples: [(canonical_city_name, has_connection), ...]
    """
    from src.nlp.postprocessing import get_all_matches
    from src.utils.pipeline import map_city_to_uic

    matches = get_all_matches(city_name, gazetteer)

    suggestions = []
    for city in matches:
        uic = map_city_to_uic(city, city_mapping)
        has_connection = bool(uic)
        suggestions.append((city, has_connection))

    return suggestions


def find_route(origin: str, destination: str):
    """
    Find route between two cities.

    Returns:
        (cities, total_time, segments, err, err_type)
        - cities: list of station names along route
        - total_time: total travel time in minutes
        - segments: list of segment dicts with line_code, duration, etc.
        - err: error message string or None
        - err_type: "origin" or "destination" if error relates to a specific city, else None
    """
    from src.utils.pipeline import map_city_to_uic
    from src.pathfinding.algorithms import dijkstra, get_route_details, InvalidStationError, NoPathError
    from src.pathfinding.graph_loader import get_station_info
    from src.nlp.gazetteer import load_gazetteer, KNOWN_FOREIGN_CITIES
    from src.nlp.postprocessing import get_all_matches
    from src.nlp.preprocessing import preprocess_for_matching

    graph, mapping = get_graph_and_mapping()
    gazetteer = load_gazetteer()

    o_uic = map_city_to_uic(origin, mapping)
    d_uic = map_city_to_uic(destination, mapping)

    # Check for ambiguous short names EVEN if mapping found
    if o_uic and len(origin) <= 15:
        matches = get_all_matches(origin, gazetteer)
        if len(matches) > 1:
            return None, None, None, f"Ville '{origin}' ambigue - plusieurs correspondances possibles", "origin"

    if d_uic and len(destination) <= 10:
        matches = get_all_matches(destination, gazetteer)
        if len(matches) > 1:
            return None, None, None, f"Ville '{destination}' ambigue - plusieurs correspondances possibles", "destination"

    if not o_uic:
        norm = preprocess_for_matching(origin)
        if norm in KNOWN_FOREIGN_CITIES:
            return None, None, None, f"'{origin}' n'est pas dans le reseau SNCF. Seules les gares francaises sont supportees.", None
        return None, None, None, f"Ville '{origin}' introuvable dans le reseau SNCF", "origin"
    if not d_uic:
        norm = preprocess_for_matching(destination)
        if norm in KNOWN_FOREIGN_CITIES:
            return None, None, None, f"'{destination}' n'est pas dans le reseau SNCF. Seules les gares francaises sont supportees.", None
        return None, None, None, f"Ville '{destination}' introuvable dans le reseau SNCF", "destination"

    try:
        path, total_time = dijkstra(graph, o_uic, d_uic)
        cities = []
        for uic in path:
            info = get_station_info(graph, uic)
            cities.append(info.get("station_name", uic) if info else uic)
        segments = get_route_details(path, graph)
        return cities, total_time, segments, None, None
    except (InvalidStationError, NoPathError) as e:
        return None, None, None, str(e), None


# ──────────────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────────────

st.title("🚄 Travel Order Resolver")
st.markdown(
    "Extraction d'ordres de voyage en français avec NLP + calcul d'itineraire SNCF "
    "— projet EPITECH T-AIA-911"
)
st.divider()

# ──────────────────────────────────────────────────────────────────────────────
# Tabs
# ──────────────────────────────────────────────────────────────────────────────

tab_home, tab_data, tab_nlp, tab_route, tab_eval, tab_pipeline = st.tabs([
    "🏠 Projet",
    "📊 Donnees",
    "🔍 Extraction NLP",
    "🗺️ Itineraire",
    "📈 Evaluation",
    "📁 Pipeline CSV",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Présentation du projet
# ══════════════════════════════════════════════════════════════════════════════

with tab_home:
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Objectif")
        st.markdown(
            """
            Etant donne une phrase en français décrivant un ordre de voyage,
            extraire automatiquement la **ville de départ** et la **ville d'arrivée**,
            puis calculer l'**itineraire optimal** sur le réseau SNCF.

            **Contraintes** : fautes d'orthographe, absence de majuscules, noms composés,
            ordre inversé (destination avant origine), phrases sans intention de voyage.
            """
        )

        st.subheader("Architecture")
        st.markdown(
            """
            ```
            Phrase → Prétraitement → Extraction NLP → Mapping UIC → Dijkstra → Itinéraire
                                         ↑
                               Baseline (règles) ou CamemBERT (NER)
            ```

            | Module | Rôle |
            |---|---|
            | `src/nlp/preprocessing.py` | Normalisation (accents, tirets, casse) |
            | `src/nlp/baseline.py` | Extracteur par mots-clés français |
            | `src/nlp/transformer.py` | CamemBERT fine-tuné sur 7 000 phrases |
            | `src/pathfinding/` | Graphe NetworkX + Dijkstra sur données GTFS |
            """
        )

    with col2:
        st.subheader("Résultats clés")

        st.metric("Exact match — CamemBERT", "96.76%", "+52 pts vs baseline")
        st.metric("Exact match — Baseline", "44.48%")
        st.metric("Dataset", "10 000 phrases", "train / val / test")
        st.metric("Réseau SNCF", "2 782 gares", "11 230 connexions GTFS réelles")

        st.subheader("Exemples traites")
        examples = [
            ("j'veu alé de roquefort-les-pins @ niiice", "roquefort-les-pins", "nice"),
            ("depuis marseilles rejoindre toulouse avec marcel", "marseille", "toulouse"),
            ("Bon je vais prendre le train de Aix-en-Provence a Paris", "aix-en-provence", "paris"),
        ]
        for phrase, orig, dest in examples:
            with st.expander(f'"{phrase[:50]}..."'):
                st.markdown(f"**Origine :** {orig}  \n**Destination :** {dest}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Exploration des données
# ══════════════════════════════════════════════════════════════════════════════

with tab_data:
    st.subheader("Explorer le dataset")

    c1, c2, c3 = st.columns(3)
    with c1:
        train_df = load_split("train")
        st.metric("Train", f"{len(train_df):,} phrases")
    with c2:
        val_df = load_split("val")
        st.metric("Validation", f"{len(val_df):,} phrases")
    with c3:
        test_df = load_split("test")
        st.metric("Test", f"{len(test_df):,} phrases")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Distribution par catégorie (train)")
        cat_counts = train_df["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "count"]
        fig = px.bar(
            cat_counts, x="count", y="category", orientation="h",
            color="count", color_continuous_scale="Blues",
            labels={"count": "Phrases", "category": ""},
        )
        fig.update_layout(showlegend=False, coloraxis_showscale=False,
                          height=400, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("#### Distribution par difficulté (train)")
        diff_counts = train_df["difficulty"].value_counts().reset_index()
        diff_counts.columns = ["difficulty", "count"]
        colors = {"easy": "#4CAF50", "medium": "#FF9800", "hard": "#F44336"}
        fig2 = px.pie(
            diff_counts, values="count", names="difficulty",
            color="difficulty", color_discrete_map=colors,
        )
        fig2.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Exemples par catégorie")

    selected_split = st.selectbox("Split", ["train", "val", "test"], key="data_split")
    df_selected = load_split(selected_split)

    selected_cat = st.selectbox("Catégorie", sorted(df_selected["category"].unique()), key="data_cat")
    sample = df_selected[df_selected["category"] == selected_cat].sample(
        min(5, len(df_selected[df_selected["category"] == selected_cat])),
        random_state=42
    )[["sentenceID", "sentence", "origin", "destination", "difficulty", "is_valid"]]

    st.dataframe(sample, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Extraction NLP
# ══════════════════════════════════════════════════════════════════════════════

with tab_nlp:
    st.subheader("Tester l'extraction NLP")
    st.markdown("Entrez une phrase en français — les deux modèles sont appliqués en parallèle.")

    sentence = st.text_input(
        "Phrase",
        value="je voudrais un billet de nice pour aller a toulouse stp",
        placeholder="Ex: de paris a lyon sans escale",
    )

    if st.button("Extraire", type="primary", key="nlp_btn") and sentence.strip():
        col_base, col_camembert = st.columns(2)

        with col_base:
            st.markdown("### Baseline (règles)")
            with st.spinner("Analyse..."):
                model_b = get_baseline()
                res_b   = extract(sentence, model_b, "baseline")
            if res_b.get("valid"):
                st.success("Ordre de voyage détecté ✓")
                st.metric("Origine",      res_b.get("origin",      "—"))
                st.metric("Destination",  res_b.get("destination", "—"))
            else:
                st.error("Phrase invalide (pas un ordre de voyage)")
                st.metric("Origine",     res_b.get("origin")      or "—")
                st.metric("Destination", res_b.get("destination") or "—")

        with col_camembert:
            st.markdown("### CamemBERT (NER fine-tuné)")
            with st.spinner("Analyse..."):
                model_c = get_camembert()
                res_c   = extract(sentence, model_c, "camembert")
            if res_c.get("valid"):
                st.success("Ordre de voyage détecté ✓")
                st.metric("Origine",     res_c.get("origin",      "—"))
                st.metric("Destination", res_c.get("destination", "—"))
            else:
                st.error("Phrase invalide (pas un ordre de voyage)")
                st.metric("Origine",     res_c.get("origin")      or "—")
                st.metric("Destination", res_c.get("destination") or "—")

    st.markdown("---")
    st.markdown("#### Cas de test typiques")
    test_cases = {
        "Standard":           "Je veux aller de Paris a Lyon",
        "Faute d'orthographe": "j'veu alé de roquefort-les-pins @ niiice",
        "Sans majuscules":    "billet bordeaux marseille",
        "Ordre inversé":      "je veux rejoindre paris depuis lyon",
        "Nom composé":        "billet de aix-en-provence pour strasbourg",
        "Phrase invalide":    "bonjour comment allez-vous aujourd'hui",
    }
    for label, example in test_cases.items():
        if st.button(f"📝 {label}", key=f"example_{label}"):
            st.session_state["nlp_prefill"] = example
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Itinéraire
# ══════════════════════════════════════════════════════════════════════════════

with tab_route:
    st.subheader("Calculer un itinéraire")
    st.markdown("Entrez une phrase ou des villes directement — le plus court chemin est calculé via Dijkstra sur les données GTFS SNCF.")

    input_mode = st.radio("Mode de saisie", ["Phrase libre", "Villes directes"], horizontal=True)

    # Initialize session state for suggestions
    if "suggestions_origin" not in st.session_state:
        st.session_state["suggestions_origin"] = None
    if "suggestions_destination" not in st.session_state:
        st.session_state["suggestions_destination"] = None
    if "selected_origin" not in st.session_state:
        st.session_state["selected_origin"] = None
    if "selected_destination" not in st.session_state:
        st.session_state["selected_destination"] = None

    if input_mode == "Phrase libre":
        # Input method selection (Text or Voice)
        available_methods = ["✍️ Texte"]
        if SPEECH_TO_TEXT_AVAILABLE and is_api_key_configured():
            available_methods.append("🎙️ Voix")

        input_method = st.radio(
            "Méthode de saisie",
            available_methods,
            horizontal=True,
            key="input_method_route"
        )

        phrase_route = ""

        # Text input mode
        if input_method == "✍️ Texte":
            phrase_route = st.text_input(
                "Phrase",
                value="de nice a toulouse",
                placeholder="Ex: Je veux aller de Paris à Lyon",
                key="route_phrase"
            )

        # Voice input mode
        elif input_method == "🎙️ Voix":
            st.info("🎤 Cliquez sur le microphone et parlez (exemple : 'Je veux aller de Paris à Lyon')")
            st.caption("🆓 Utilise Google Speech Recognition (gratuit, ~50 requêtes/jour)")

            audio_bytes = audio_recorder(
                text="",
                recording_color="#e74c3c",
                neutral_color="#3498db",
                icon_size="2x",
                pause_threshold=2.0  # Stop recording after 2s of silence
            )

            if audio_bytes:
                # Validate audio
                is_valid, error_msg = validate_audio_bytes(audio_bytes, min_size=1000)

                if not is_valid:
                    st.warning(f"⚠️ {error_msg}")
                else:
                    with st.spinner("🎧 Transcription en cours via Google..."):
                        try:
                            phrase_route = transcribe_audio(
                                audio_bytes,
                                language="fr-FR"
                            )
                            st.success(f"✅ Transcription : **{phrase_route}**")
                        except Exception as e:
                            st.error(f"❌ Erreur de transcription : {e}")
                            st.info("💡 Essayez à nouveau ou basculez sur la saisie texte.")
                            phrase_route = ""
            else:
                st.caption("En attente d'enregistrement...")

        # Warning if voice input not available
        if not SPEECH_TO_TEXT_AVAILABLE:
            with st.expander("ℹ️ Activer la saisie vocale"):
                st.markdown("""
                Pour utiliser la saisie vocale **gratuite**, installez les dépendances :
                ```bash
                pip install audio-recorder-streamlit SpeechRecognition pydub
                ```

                Aucune clé API requise ! Utilise Google Speech Recognition (gratuit).
                """)

        # Calculate route button (common for both input methods)
        if st.button("Calculer l'itineraire", type="primary", key="route_btn_phrase", disabled=not phrase_route):
            with st.spinner("Extraction NLP..."):
                model_c = get_camembert()
                res     = extract(phrase_route, model_c, "camembert")

            if not res.get("valid"):
                st.error("Ordre de voyage non détecté dans cette phrase.")
            else:
                origin_r      = res["origin"]
                destination_r = res["destination"]
                st.info(f"Extrait : **{origin_r}** → **{destination_r}**")

                with st.spinner("Calcul de l'itineraire..."):
                    cities, total_time, segments, err, err_type = find_route(origin_r, destination_r)

                if err:
                    st.error(err)

                    # Check for suggestions when city not found
                    if err_type in ["origin", "destination"]:
                        from src.nlp.gazetteer import load_gazetteer
                        gazetteer = load_gazetteer()
                        _, mapping = get_graph_and_mapping()

                        city_not_found = origin_r if err_type == "origin" else destination_r
                        suggestions = get_city_suggestions(city_not_found, gazetteer, mapping)

                        if suggestions:
                            st.info(f"🔍 **Villes similaires trouvées pour '{city_not_found}' :**")

                            # Display suggestions with connection status
                            for city, has_connection in suggestions:
                                status_icon = "✅" if has_connection else "⚠️"
                                status_text = "connectée" if has_connection else "non connectée"
                                st.markdown(f"{status_icon} **{city}** ({status_text})")

                            st.markdown("💡 *Corrigez le nom de la ville dans votre phrase et réessayez.*")
                        else:
                            st.warning(f"Aucune ville similaire trouvée pour '{city_not_found}'.")
                elif cities:
                    _display_route(cities, total_time, segments)

    else:
        c1, c2 = st.columns(2)
        with c1:
            origin_direct = st.text_input("Ville de depart", value="Paris", key="origin_input")
        with c2:
            dest_direct = st.text_input("Ville d'arrivee", value="Marseille", key="dest_input")

        if st.button("Calculer l'itineraire", type="primary", key="route_btn_direct"):
            with st.spinner("Calcul de l'itineraire..."):
                cities, total_time, segments, err, err_type = find_route(origin_direct, dest_direct)

            if err:
                st.error(err)

                # Check for suggestions when city not found
                if err_type in ["origin", "destination"]:
                    from src.nlp.gazetteer import load_gazetteer
                    gazetteer = load_gazetteer()
                    _, mapping = get_graph_and_mapping()

                    city_not_found = origin_direct if err_type == "origin" else dest_direct
                    suggestions = get_city_suggestions(city_not_found, gazetteer, mapping)

                    if suggestions:
                        st.info(f"🔍 **Villes similaires trouvées pour '{city_not_found}' :**")

                        # Interactive selection with radio buttons
                        suggestion_options = []
                        for city, has_connection in suggestions:
                            status_icon = "✅" if has_connection else "⚠️"
                            status_text = "connectée" if has_connection else "non connectée"
                            suggestion_options.append(f"{status_icon} {city} ({status_text})")

                        selected_label = st.radio(
                            f"Choisissez la ville correcte pour remplacer '{city_not_found}' :",
                            suggestion_options,
                            key=f"suggestion_radio_{err_type}"
                        )

                        # Extract city name from selected label (format: "✅ Paris (connectée)")
                        if selected_label:
                            selected_city = selected_label.split(" ")[1]  # Get city name

                            if st.button("Confirmer et recalculer", key=f"confirm_{err_type}"):
                                # Replace city and recalculate
                                new_origin = selected_city if err_type == "origin" else origin_direct
                                new_dest = selected_city if err_type == "destination" else dest_direct

                                with st.spinner("Recalcul de l'itinéraire..."):
                                    cities, total_time, segments, err, _ = find_route(new_origin, new_dest)

                                if err:
                                    st.error(err)
                                elif cities:
                                    st.success(f"Itineraire trouve avec **{selected_city}** !")
                                    _display_route(cities, total_time, segments)
                    else:
                        st.warning(f"Aucune ville similaire trouvée pour '{city_not_found}'.")
            elif cities:
                _display_route(cities, total_time, segments)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Évaluation
# ══════════════════════════════════════════════════════════════════════════════

with tab_eval:
    st.subheader("Métriques d'évaluation")

    st.markdown("#### Résultats pré-calculés (val set, 1 500 phrases)")

    # Hard-coded known results — shown instantly without re-running inference
    baseline_results = {
        "exact_match":            0.6010,
        "origin_accuracy":        0.7486,
        "destination_accuracy":   0.7181,
        "validity_f1":            0.8485,
        "validity_precision":     0.8962,
        "validity_recall":        0.8057,
        "by_difficulty": {"easy": 0.801, "medium": 0.655, "hard": 0.365},
        "by_category": {
            "no_capitals":      0.759,
            "misspelling":      0.109,
            "inverted_order":   0.526,
            "compound_name":    0.449,
            "complex_question": 0.343,
            "name_ambiguity":   0.841,
        },
    }

    camembert_results = {
        "exact_match":            0.9676,
        "origin_accuracy":        0.9810,
        "destination_accuracy":   0.9752,
        "validity_f1":            0.9850,
        "validity_precision":     0.9900,
        "validity_recall":        0.9800,
        "by_difficulty": {"easy": 0.982, "medium": 0.971, "hard": 0.948},
        "by_category": {
            "no_capitals":      0.978,
            "misspelling":      0.951,
            "inverted_order":   0.974,
            "compound_name":    0.962,
            "complex_question": 0.955,
            "name_ambiguity":   0.972,
        },
    }

    col_b, col_c = st.columns(2)

    for col, name, res, color in [
        (col_b, "Baseline", baseline_results, "#FF7043"),
        (col_c, "CamemBERT", camembert_results, "#1E88E5"),
    ]:
        with col:
            st.markdown(f"### {name}")
            m1, m2 = st.columns(2)
            m1.metric("Exact match",  f"{res['exact_match']:.1%}")
            m2.metric("F1 validité",  f"{res['validity_f1']:.1%}")
            m1.metric("Origine",      f"{res['origin_accuracy']:.1%}")
            m2.metric("Destination",  f"{res['destination_accuracy']:.1%}")

    st.markdown("---")

    col_diff, col_cat = st.columns(2)

    with col_diff:
        st.markdown("#### Par difficulté")
        difficulties = ["easy", "medium", "hard"]
        fig_diff = go.Figure()
        for name, res, color in [
            ("Baseline",   baseline_results,   "#FF7043"),
            ("CamemBERT",  camembert_results,  "#1E88E5"),
        ]:
            fig_diff.add_trace(go.Bar(
                name=name,
                x=difficulties,
                y=[res["by_difficulty"][d] for d in difficulties],
                marker_color=color,
                text=[f"{res['by_difficulty'][d]:.0%}" for d in difficulties],
                textposition="outside",
            ))
        fig_diff.update_layout(
            barmode="group", yaxis=dict(range=[0, 1.1], tickformat=".0%"),
            height=350, margin=dict(l=0, r=0, t=20, b=0),
        )
        st.plotly_chart(fig_diff, use_container_width=True)

    with col_cat:
        st.markdown("#### Par catégorie")
        categories = list(baseline_results["by_category"].keys())
        fig_cat = go.Figure()
        for name, res, color in [
            ("Baseline",   baseline_results,   "#FF7043"),
            ("CamemBERT",  camembert_results,  "#1E88E5"),
        ]:
            fig_cat.add_trace(go.Bar(
                name=name,
                x=categories,
                y=[res["by_category"][c] for c in categories],
                marker_color=color,
                text=[f"{res['by_category'][c]:.0%}" for c in categories],
                textposition="outside",
            ))
        fig_cat.update_layout(
            barmode="group", yaxis=dict(range=[0, 1.15], tickformat=".0%"),
            xaxis=dict(tickangle=-30),
            height=350, margin=dict(l=0, r=0, t=20, b=30),
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Relancer l'évaluation en direct")
    eval_model = st.selectbox("Modèle", ["baseline", "camembert"], key="eval_model")
    eval_split = st.selectbox("Split", ["val", "test"], key="eval_split")

    if st.button("Lancer l'evaluation", key="eval_run"):
        from src.evaluation.metrics import evaluate_model as eval_fn

        df_gt = load_split(eval_split)
        total = len(df_gt)

        if eval_model == "baseline":
            model_e = get_baseline()
        else:
            model_e = get_camembert()

        progress = st.progress(0, text="Inference en cours...")
        rows = []
        for i, row in df_gt.iterrows():
            r = extract(str(row["sentence"]), model_e, eval_model)
            rows.append({
                "sentenceID":  row["sentenceID"],
                "origin":      r.get("origin")      or "INVALID",
                "destination": r.get("destination") or "INVALID",
            })
            progress.progress((len(rows)) / total, text=f"Inference : {len(rows)}/{total}")

        progress.empty()
        preds = pd.DataFrame(rows)
        result = eval_fn(preds, df_gt, id_column="sentenceID",
                         origin_col_pred="origin", dest_col_pred="destination",
                         origin_col_gt="origin", dest_col_gt="destination",
                         validity_col_gt="is_valid",
                         category_column="category", difficulty_column="difficulty")

        st.success(f"Evaluation terminee sur {total} phrases")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Exact match",  f"{result.exact_match_accuracy:.2%}")
        m2.metric("F1 validite",  f"{result.validity_f1:.2%}")
        m3.metric("Origine",      f"{result.origin_accuracy:.2%}")
        m4.metric("Destination",  f"{result.destination_accuracy:.2%}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — Pipeline CSV
# ══════════════════════════════════════════════════════════════════════════════

with tab_pipeline:
    st.subheader("Traiter un fichier CSV")
    st.markdown(
        "Format attendu : `sentenceID,sentence` (UTF-8).  \n"
        "Un fichier de demo est disponible dans `data/demo/input_demo.csv`."
    )

    col_opts1, col_opts2 = st.columns(2)
    with col_opts1:
        pipe_model = st.selectbox("Modele NLP", ["baseline", "camembert"], key="pipe_model")
    with col_opts2:
        pipe_mode = st.selectbox("Mode", ["nlp-only", "full-pipeline"], key="pipe_mode",
                                 help="nlp-only: extrait origine/destination. full-pipeline: calcule aussi l'itineraire complet.")

    uploaded = st.file_uploader("Uploader un CSV", type=["csv"])

    use_demo = st.checkbox("Utiliser le fichier demo (data/demo/input_demo.csv)", value=False)

    if st.button("Lancer le pipeline", type="primary", key="pipe_btn"):
        import tempfile, os
        from src.utils.pipeline import process_pipeline

        # Resolve input
        if use_demo:
            input_path = "data/demo/input_demo.csv"
        elif uploaded:
            tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="wb")
            tmp_in.write(uploaded.read())
            tmp_in.close()
            input_path = tmp_in.name
        else:
            st.warning("Uploader un fichier CSV ou cocher 'Utiliser le fichier demo'.")
            st.stop()

        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        tmp_out.close()
        output_path = tmp_out.name

        pipeline_mode = "route" if pipe_mode == "full-pipeline" else "nlp"

        with st.spinner("Traitement en cours..."):
            try:
                stats = process_pipeline(
                    input_file=input_path,
                    output_file=output_path,
                    mode=pipeline_mode,
                    nlp_model=pipe_model,
                )
            except Exception as e:
                st.error(f"Erreur pipeline : {e}")
                st.stop()

        st.success("Pipeline termine !")

        m1, m2, m3 = st.columns(3)
        m1.metric("Total",         stats["total"])
        m2.metric("Valides",       f"{stats['valid']} ({stats['valid']/stats['total']:.0%})")
        m3.metric("Invalides",     f"{stats['invalid']} ({stats['invalid']/stats['total']:.0%})")

        result_df = pd.read_csv(output_path, encoding="utf-8")
        st.dataframe(result_df, use_container_width=True, hide_index=True)

        csv_bytes = result_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Telecharger les resultats (CSV)",
            data=csv_bytes,
            file_name="resultats.csv",
            mime="text/csv",
        )

        if uploaded:
            os.unlink(input_path)
        os.unlink(output_path)
