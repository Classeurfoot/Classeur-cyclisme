import streamlit as st
import pandas as pd
import os
from datetime import datetime
import unicodedata
import re
import base64
import urllib.parse
import plotly.express as px

# 1. Configuration de la page
st.set_page_config(page_title="Le Grenier du Cyclisme", layout="wide")

# --- LECTURE DU LOGO ---
@st.cache_data  
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""

logo_b64 = get_base64_image("logo.png")

# ==========================================
# ⚙️ GESTION DE LA NAVIGATION & PANIER
# ==========================================
if 'page' not in st.session_state: st.session_state.page = 'accueil'
if 'chemin' not in st.session_state: st.session_state.chemin = []
if 'panier' not in st.session_state: st.session_state.panier = []

def go_home():
    st.session_state.page = 'accueil'
    st.session_state.chemin = []

# ==========================================
# 🌳 L'ARBORESCENCE DU CYCLISME
# ==========================================
MENU_ARBO = {
    "Grands Tours": [
        "Giro d’Italia", "Tour de France", "Tour de France Femmes", 
        "Vuelta a España", "Vuelta Femenina"
    ],
    "Les Monuments": [
        "Milan-Sanremo", "Tour des Flandres", "Paris-Roubaix", 
        "Liège-Bastogne-Liège", "Tour de Lombardie"
    ],
    "Classiques & Courses d'un jour": {
        "Campagne Flandrienne & Pavés": ["Omloop Het Nieuwsblad", "Kuurne–Brussels–Kuurne", "Nokere Koerse", "GP Denain", "Bruges-La Panne", "E3 Saxo Classic", "Gand-Wevelgem", "A Travers la Flandre", "GP Escaut", "Tour de Drenthe"],
        "Les Ardennaises": ["Flèche Brabançonne", "Amstel Gold Race", "Flèche Wallonne"],
        "Italiennes & Chemins Blancs": ["Trofeo Laigueglia", "Strade Bianche", "Strade Bianche féminine", "Milan-Turin", "Coppa Sabatini", "Tour d'Emilie", "Tre Valli Varesine"],
        "Le Calendrier Français": ["La Marseillaise", "Faun Ardèche Classic", "Faun Drôme Classic", "Cholet-Pays de la Loire", "Tro Bro Leon", "Bretagne Classic-GP Plouay", "Paris-Tours"],
        "Les Internationales": ["Clásica Jaén", "Clásica San Sebastián", "Grand Prix Cycliste de Québec", "Grand Prix Cycliste de Montréal"]
    },
    "Courses par étapes": {
        "World Tour Historique": ["Paris-Nice", "Tirreno-Adriatico", "Tour de Catalogne", "Tour du Pays Basque", "Tour de Romandie", "Dauphiné Libéré", "Tour de Suisse"],
        "Début de saison & Préparation": ["Etoile de Bessèges", "Tour de la Provence", "Tour d'Andalousie-Ruta del Sol", "Tour d'Algarve", "Gran Camino", "Tour des Alpes", "Tour des Abruzzes", "Tour de Belgique", "Tour de Slovénie", "Route d'Occitanie"],
        "Internationales & Relève": ["UAE Tour", "Tour de Turquie", "Tour de l'Avenir"]
    },
    "Mondiaux, Europe et JO": [
        "Jeux Olympiques", "Championnats du Monde", 
        "Championnats du Monde Espoirs", "Championnats d’Europe"
    ]
}

# --- DICTIONNAIRE DE TRADUCTION POUR LA RECHERCHE ---
MAPPING_RECHERCHE = {
    "Giro d’Italia": "Giro",
    "Vuelta a España": "Vuelta",
    "Grand Prix Cycliste de Québec": "Québec|Quebec",
    "Grand Prix Cycliste de Montréal": "Montréal|Montreal",
    "E3 Saxo Classic": "E3", 
    "Bretagne Classic-GP Plouay": "Plouay",
    "Milan-Sanremo": "San Remo|Sanremo"
}

# ==========================================
# ⚙️ FONCTIONS DES POP-UPS (INFORMATIONS)
# ==========================================
@st.dialog("🧭 Guide & Contenu")
def popup_guide_contenu():
    st.markdown("""
    **Bienvenue dans l'antre du Grenier du Cyclisme !** Plus de 2100 archives pour revivre la légende du peloton.
    
    **Dans ce catalogue massif :**
    * 🏔️ **Les Grands Tours :** Tour de France, Giro, Vuelta (étapes intégrales ou résumés longs).
    * 🏛️ **Les Monuments :** Les 5 grandes légendes d'un jour.
    * 🧱 **Classiques :** Flandriennes, Ardennaises et courses régionales.
    * 🛣️ **Courses par étapes :** De Paris-Nice au Dauphiné.
    * 🌍 **Championnats :** Mondiaux, JO, courses en ligne et chronos.
    """)

@st.dialog("💾 Formats & Qualité")
def popup_formats():
    st.markdown("### 🗂️ Types de retransmissions")
    st.markdown("""
    * 🏁 **Intégralité :** La course ou l'étape du premier au dernier kilomètre.
    * 🎥 **Long Format / Résumé :** Les moments clés et le final (souvent 45min à 1h30).
    """)
    st.divider()
    st.markdown("### 📼 Formats disponibles")
    st.markdown("""
    * 💻 **Numérique :** Fichiers standards (.mp4, .mkv, .avi).
    * 💿 **Qualité DVD :** Fichiers .VOB originaux (meilleur débit d'image pour les archives anciennes).
    """)

@st.dialog("💶 Tarifs & Réductions")
def popup_tarifs():
    st.markdown("### 💰 Grille Tarifaire")
    st.markdown("Le tarif de chaque vidéo est affiché directement dans le catalogue. Il dépend de la rareté et du format.")
    st.divider()
    st.markdown("### 🎁 Remises au volume")
    st.markdown("""
    Pour les passionnés qui souhaitent revivre un Grand Tour entier :
    * 🥉 **Dès 5 vidéos :** -10% sur le total
    * 🥈 **Dès 10 vidéos :** -15% sur le total
    * 🥇 **Dès 20 vidéos :** -20% sur le total
    """)

@st.dialog("✉️ Contact & Commandes")
def popup_contact_commandes():
    st.markdown("""
    1. 🛒 **Le Panier :** Ajoutez vos étapes ou courses préférées.
    2. ✉️ **L'envoi :** Copiez le récapitulatif et envoyez-le par e-mail à **legrenierdufootball@hotmail.com** (ou via Instagram).
    3. 💳 **Le Paiement :** Via **PayPal** de manière sécurisée.
    4. 🚀 **La Livraison :** Lien de téléchargement privé envoyé rapidement.
    """)

@st.dialog("🤝 Proposer un Échange")
def popup_echanges():
    st.markdown("Je suis très ouvert aux échanges équitables entre passionnés si vous possédez vos propres numérisations d'étapes manquantes ou avec des commentaires FR d'époque !")

# ==========================================
# 3. CHARGEMENT DES DONNÉES
# ==========================================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("cyclisme.csv", sep=";", encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        df = df.dropna(subset=['🚴‍♂️ Course', '📅 Date'], how='all')
        if 'Prix vidéo' in df.columns:
            df['Prix vidéo'] = df['Prix vidéo'].astype(str).str.replace(',', '.').apply(pd.to_numeric, errors='coerce').fillna(3.0)
        return df
    except Exception as e:
        st.error(f"Erreur : {e}")
        return pd.DataFrame()

df = load_data()

cols_cat = [c for c in ['📆 Saison', '🚴‍♂️ Course', '📅 Date', '🔢 Etape', '🌄 Type', '🥇 Vainqueur', '👑 Leader général', 'Format vidéo', '📺 Diffuseur', 'Prix vidéo'] if c in df.columns]

# --- AFFICHAGE RESULTATS ---
def afficher_resultats(df_res):
    if df_res.empty: return st.warning("Aucun résultat.")
    st.metric("Vidéos trouvées", len(df_res))
    df_disp = df_res[cols_cat].copy()
    df_disp.insert(0, "🛒", False)
    ed_df = st.data_editor(df_disp, column_config={"🛒": st.column_config.CheckboxColumn("Ajouter")}, disabled=cols_cat, hide_index=True, use_container_width=True)
    sel = ed_df[ed_df["🛒"] == True]
    if len(sel) > 0:
        if st.button(f"Ajouter {len(sel)} vidéos au panier", type="primary", use_container_width=True):
            for _, r in sel.iterrows():
                d = {k: v for k, v in r.to_dict().items() if k != "🛒"}
                id_m = f"{d.get('📅 Date')}_{d.get('🚴‍♂️ Course')}_{d.get('🔢 Etape')}"
                if not any(f"{m.get('📅 Date')}_{m.get('🚴‍♂️ Course')}_{m.get('🔢 Etape')}" == id_m for m in st.session_state.panier):
                    st.session_state.panier.append(d)
            st.rerun()

# ==========================================
# 🧭 BARRE LATÉRALE
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🚴‍♂️ Menu Rapide</h2>", unsafe_allow_html=True)
    if st.button("🏠 Accueil", use_container_width=True): go_home(); st.rerun()
    if st.button("❓ F.A.Q & Infos", use_container_width=True): st.session_state.page = 'faq'; st.rerun()
    st.divider()
    
    nb = len(st.session_state.panier)
    if st.button(f"🛒 Panier ({nb})", use_container_width=True, type="primary" if nb>0 else "secondary"): st.session_state.page = 'panier'; st.rerun()
    
    st.divider()
    st.markdown("<h3 style='margin-bottom: -10px;'>📂 Catégories</h3>", unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    div.element-container:has(.css-tours) + div.element-container button { background-color: #ca8a04 !important; border-color: #ca8a04 !important; }
    div.element-container:has(.css-tours) + div.element-container button p { color: white !important; font-weight: bold;}
    div.element-container:has(.css-tours) + div.element-container button:hover { background-color: #a16207 !important; border-color: #a16207 !important; transform: scale(1.02); }

    div.element-container:has(.css-monuments) + div.element-container button { background-color: #3f3f46 !important; border-color: #3f3f46 !important; }
    div.element-container:has(.css-monuments) + div.element-container button p { color: white !important; font-weight: bold;}
    div.element-container:has(.css-monuments) + div.element-container button:hover { background-color: #27272a !important; border-color: #27272a !important; transform: scale(1.02); }

    div.element-container:has(.css-classiques) + div.element-container button { background-color: #52525b !important; border-color: #52525b !important; }
    div.element-container:has(.css-classiques) + div.element-container button p { color: white !important; font-weight: bold;}
    div.element-container:has(.css-classiques) + div.element-container button:hover { background-color: #3f3f46 !important; border-color: #3f3f46 !important; transform: scale(1.02); }

    div.element-container:has(.css-etapes) + div.element-container button { background-color: #0284c7 !important; border-color: #0284c7 !important; }
    div.element-container:has(.css-etapes) + div.element-container button p { color: white !important; font-weight: bold;}
    div.element-container:has(.css-etapes) + div.element-container button:hover { background-color: #0369a1 !important; border-color: #0369a1 !important; transform: scale(1.02); }

    div.element-container:has(.css-champ) + div.element-container button { background-color: #7e22ce !important; border-color: #7e22ce !important; }
    div.element-container:has(.css-champ) + div.element-container button p { color: white !important; font-weight: bold;}
    div.element-container:has(.css-champ) + div.element-container button:hover { background-color: #6b21a8 !important; border-color: #6b21a8 !important; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="css-tours" style="margin-bottom: -15px;"></div>', unsafe_allow_html=True)
    if st.button("🏔️ Grands Tours", use_container_width=True):
        st.session_state.page = 'arborescence'; st.session_state.chemin = ['Grands Tours']; st.rerun()
        
    st.markdown('<div class="css-monuments" style="margin-bottom: -15px;"></div>', unsafe_allow_html=True)
    if st.button("🏛️ Les Monuments", use_container_width=True):
        st.session_state.page = 'arborescence'; st.session_state.chemin = ['Les Monuments']; st.rerun()

    st.markdown('<div class="css-classiques" style="margin-bottom: -15px;"></div>', unsafe_allow_html=True)
    if st.button("🧱 Classiques & 1 jour", use_container_width=True):
        st.session_state.page = 'arborescence'; st.session_state.chemin = ["Classiques & Courses d'un jour"]; st.rerun()
        
    st.markdown('<div class="css-etapes" style="margin-bottom: -15px;"></div>', unsafe_allow_html=True)
    if st.button("🛣️ Courses par étapes", use_container_width=True):
        st.session_state.page = 'arborescence'; st.session_state.chemin = ["Courses par étapes"]; st.rerun()
        
    st.markdown('<div class="css-champ" style="margin-bottom: -15px;"></div>', unsafe_allow_html=True)
    if st.button("🌍 Mondiaux, Europe & JO", use_container_width=True):
        st.session_state.page = 'arborescence'; st.session_state.chemin = ['Mondiaux, Europe et JO']; st.rerun()

    st.divider()
    st.markdown("### 🔍 Outils")
    if st.button("📖 Catalogue Complet", use_container_width=True): st.session_state.page = 'catalogue'; st.rerun()
    if st.button("📊 Statistiques", use_container_width=True): st.session_state.page = 'statistiques'; st.rerun()
    if st.button("🎯 Progression Collection", use_container_width=True): st.session_state.page = 'progression'; st.rerun()
    if st.button("🕵️ Recherche Avancée", use_container_width=True): st.session_state.page = 'recherche_avancee'; st.rerun()

# ==========================================
# PAGE : ACCUEIL
# ==========================================
if st.session_state.page == 'accueil':
    if logo_b64:
        logo_html = f"<img src='data:image/png;base64,{logo_b64}' style='width: 120px; vertical-align: middle; margin-right: 0px; border-radius: 80%;'>"
    else:
        logo_html = "🚴‍♂️ "

    st.markdown(f"""
        <div style='text-align: center; margin-bottom: 10px;'>
            <h1 style='margin-bottom: 0px; display: flex; align-items: center; justify-content: center; line-height: 1;'>
                {logo_html}
                <span>Le Grenier du Cyclisme</span>
            </h1>
            <div style='max-width: 850px; margin: 0 auto; line-height: 1.5; font-size: 16px; color: #fafafa;'>
                Découvrez un catalogue interactif de plus de <b>2100 vidéos de cyclisme rétro et moderne</b>.<br>
                Retrouvez les émotions du <i>Tour de France</i>, des <i>Classiques Flandriennes</i> et des <i>Championnats du Monde</i>.<br>
                <b>Parcourez les archives, commandez vos étapes préférées et revivez la légende du peloton.</b>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    
    # --- CSS POUR COLORER LES BOUTONS COMMANDES ET ÉCHANGES ---
    st.markdown("""
    <style>
    /* 🟢 BOUTON COMMANDES (4ème colonne) */
    div[data-testid="stHorizontalBlock"] > div:nth-child(4) button {
        background-color: #2e7d32 !important; border-color: #2e7d32 !important; transition: all 0.3s ease;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(4) button p { color: #ffffff !important; font-weight: 600 !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(4) button:hover { background-color: #1b5e20 !important; border-color: #1b5e20 !important; transform: scale(1.02); }

    /* 🔵 BOUTON ÉCHANGES (5ème colonne) */
    div[data-testid="stHorizontalBlock"] > div:nth-child(5) button {
        background-color: #1565c0 !important; border-color: #1565c0 !important; transition: all 0.3s ease;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(5) button p { color: #ffffff !important; font-weight: 600 !important; }
    div[data-testid="stHorizontalBlock"] > div:nth-child(5) button:hover { background-color: #0d47a1 !important; border-color: #0d47a1 !important; transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: 
        if st.button("🧭 Guide", use_container_width=True): popup_guide_contenu()
    with c2: 
        if st.button("💾 Formats", use_container_width=True): popup_formats()
    with c3: 
        if st.button("💶 Tarifs", use_container_width=True): popup_tarifs()
    with c4: 
        if st.button("✉️ Commandes", use_container_width=True): popup_contact_commandes()
    with c5: 
        if st.button("🤝 Échanges", use_container_width=True): popup_echanges()

    st.write("---")
    
    q = st.text_input("🔍 Recherche Rapide", placeholder="Ex: Pantani, Alpe d'Huez, 1998, Roubaix...")
    if q:
        m = df.apply(lambda x: x.astype(str).str.contains(q, case=False).any(), axis=1)
        st.write(f"**Résultats pour :** '{q}'")
        afficher_resultats(df[m])
        st.write("---")

    # 📅 L'ÉPHÉMÉRIDE DU PELOTON
    st.markdown("### 📅 L'Éphéméride du Peloton")
    aujourdhui = datetime.now()
    mois_francais = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    date_affichee = f"{aujourdhui.day} {mois_francais[aujourdhui.month - 1]}"
    
    if '📅 Date' in df.columns:
        df['Mois_Jour'] = pd.to_datetime(df['📅 Date'], errors='coerce').dt.strftime('%m-%d')
        jour_cible = aujourdhui.strftime('%m-%d')
        df_ephem = df[df['Mois_Jour'] == jour_cible]
        
        if not df_ephem.empty:
            st.success(f"🔥 **{len(df_ephem)} course(s)** ont eu lieu un {date_affichee} dans l'Histoire !")
            with st.expander(f"Voir les {len(df_ephem)} vidéos du {date_affichee}"):
                afficher_resultats(df_ephem)
        else:
            st.info(f"Que s'est-il passé un {date_affichee} ? Le peloton se reposait, aucune course répertoriée à cette date.")
            
    st.write("---")

    st.markdown("### 📂 Explorer le Grenier par Catégorie")
    col_cat1, col_cat2 = st.columns(2)
    
    with col_cat1:
        st.markdown('<div class="css-tours" style="margin-bottom: -15px;"></div>', unsafe_allow_html=True)
        if st.button("🏔️ Les Grands Tours", use_container_width=True, key="btn_acc_tours"):
            st.session_state.page = 'arborescence'; st.session_state.chemin = ['Grands Tours']; st.rerun()
            
        st.markdown('<div class="css-classiques" style="margin-bottom: -15px;"></div>', unsafe_allow_html=True)
        if st.button("🧱 Classiques & Courses d'un jour", use_container_width=True, key="btn_acc_classiques"):
            st.session_state.page = 'arborescence'; st.session_state.chemin = ["Classiques & Courses d'un jour"]; st.rerun()

        st.markdown('<div class="css-champ" style="margin-bottom: -15px;"></div>', unsafe_allow_html=True)
        if st.button("🌍 Mondiaux, Europe & JO", use_container_width=True, key="btn_acc_champ"):
            st.session_state.page = 'arborescence'; st.session_state.chemin = ['Mondiaux, Europe et JO']; st.rerun()

    with col_cat2:
        st.markdown('<div class="css-monuments" style="margin-bottom: -15px;"></div>', unsafe_allow_html=True)
        if st.button("🏛️ Les Monuments", use_container_width=True, key="btn_acc_monuments"):
            st.session_state.page = 'arborescence'; st.session_state.chemin = ['Les Monuments']; st.rerun()

        st.markdown('<div class="css-etapes" style="margin-bottom: -15px;"></div>', unsafe_allow_html=True)
        if st.button("🛣️ Courses par étapes", use_container_width=True, key="btn_acc_etapes"):
            st.session_state.page = 'arborescence'; st.session_state.chemin = ["Courses par étapes"]; st.rerun()

# ==========================================
# PAGE : ARBORESCENCE (NAVIGATION DYNAMIQUE)
# ==========================================
elif st.session_state.page == 'arborescence':
    
    if len(st.session_state.chemin) > 0:
        cat_principale = st.session_state.chemin[0]
        c_fond, c_surv = "#333333", "#222222"
        if cat_principale == "Grands Tours": c_fond, c_surv = "#ca8a04", "#a16207"
        elif cat_principale == "Les Monuments": c_fond, c_surv = "#3f3f46", "#27272a"
        elif cat_principale == "Classiques & Courses d'un jour": c_fond, c_surv = "#52525b", "#3f3f46"
        elif cat_principale == "Courses par étapes": c_fond, c_surv = "#0284c7", "#0369a1"
        elif cat_principale == "Mondiaux, Europe et JO": c_fond, c_surv = "#7e22ce", "#6b21a8"

        st.markdown(f"""
        <style>
        div[data-testid="column"] div.stButton > button {{ background-color: {c_fond} !important; border-color: {c_fond} !important; transition: all 0.2s ease; }}
        div[data-testid="column"] div.stButton > button p {{ color: #ffffff !important; font-weight: bold; }}
        div[data-testid="column"] div.stButton > button:hover {{ background-color: {c_surv} !important; border-color: {c_surv} !important; transform: scale(1.02); }}
        </style>
        """, unsafe_allow_html=True)

    noeud_actuel = MENU_ARBO
    for etape in st.session_state.chemin:
        if isinstance(noeud_actuel, dict): noeud_actuel = noeud_actuel.get(etape, noeud_actuel)
        elif isinstance(noeud_actuel, list) and etape in noeud_actuel: noeud_actuel = etape

    fil_ariane = " > ".join(st.session_state.chemin)
    st.caption(f"📂 Chemin : {fil_ariane}")
    
    if st.button("⬅️ Retour"):
        st.session_state.chemin.pop()
        if len(st.session_state.chemin) == 0:
            st.session_state.page = 'accueil'
        st.rerun()
        
    st.divider()
    
    if isinstance(noeud_actuel, dict):
        cles = list(noeud_actuel.keys())
        for i in range(0, len(cles), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(cles):
                    cle = cles[i + j]
                    with cols[j]:
                        if st.button(cle, use_container_width=True):
                            st.session_state.chemin.append(cle)
                            st.rerun()

    elif isinstance(noeud_actuel, list):
        for i in range(0, len(noeud_actuel), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(noeud_actuel):
                    element = noeud_actuel[i + j]
                    with cols[j]:
                        if st.button(element, use_container_width=True):
                            st.session_state.chemin.append(element)
                            st.rerun()

    elif isinstance(noeud_actuel, str):
        st.header(f"🏁 {noeud_actuel}")
        
        terme_recherche = MAPPING_RECHERCHE.get(noeud_actuel, noeud_actuel)
        mask = df['🚴‍♂️ Course'].astype(str).str.contains(terme_recherche, case=False, na=False, regex=True)
        df_final = df[mask]
        afficher_resultats(df_final)

# ==========================================
# PAGE : PANIER
# ==========================================
elif st.session_state.page == 'panier':
    st.header("🛒 Mon Panier")
    if not st.session_state.panier:
        st.info("Votre panier est vide pour le moment.")
        if st.button("Retourner à l'accueil"):
            go_home()
            st.rerun()
    else:
        nb_a = len(st.session_state.panier)
        tot_b = sum(float(m.get('Prix vidéo', 3)) for m in st.session_state.panier)
        
        st.markdown(f"**Vous avez sélectionné {nb_a} vidéo(s).**")
        st.write("---")
        
        for i, m in enumerate(st.session_state.panier):
            c_i, c_p, c_b = st.columns([6, 2, 1])
            
            raw_etape = m.get('🔢 Etape', '')
            txt_etape = ""
            if pd.notna(raw_etape) and str(raw_etape).strip() not in ['', 'nan', 'none', '0']:
                try:
                    etp_clean = str(int(float(raw_etape)))
                    txt_etape = f" - Etape {etp_clean}"
                except ValueError:
                    txt_etape = f" - Etape {str(raw_etape).strip()}"
            
            txt_type = ""
            if m.get('Type de course') == "Autre":
                type_val = m.get('🌄 Type', '')
                if type_val: txt_type = f" [{type_val}]"

            txt_leader = ""
            val_leader = str(m.get('👑 Leader général', '')).strip()
            if val_leader and val_leader.lower() not in ['nan', 'none', '0', '']:
                txt_leader = f" | Leader : {val_leader}"
            
            c_i.markdown(f"**{m.get('🚴‍♂️ Course')} - {m.get('📆 Saison')}{txt_etape}**{txt_type}<br><small>Vainqueur : {m.get('🥇 Vainqueur')}{txt_leader}</small>", unsafe_allow_html=True)
            c_p.write(f"**{m.get('Prix vidéo')} €**")
            
            if c_b.button("❌", key=f"del_{i}"):
                st.session_state.panier.pop(i)
                st.rerun()
        
        st.divider()
        
        pct = 20 if nb_a >= 20 else (15 if nb_a >= 10 else (10 if nb_a >= 5 else 0))
        rem = tot_b * (pct/100)
        total_final = tot_b - rem
        
        if pct > 0:
            st.success(f"🎁 Remise volume de {pct}% appliquée : -{rem:.2f}€")
        
        st.subheader(f"Total à payer : {total_final:.2f} €")
        
        st.write("---")
        st.markdown("📩 **Récapitulatif de la commande :**")
        
        recap_intro = f"Bonjour, je souhaite commander ces {nb_a} vidéos sur Le Grenier du Cyclisme :\n\n"
        recap_items = ""
        
        for x in st.session_state.panier:
            raw_e = x.get('🔢 Etape', '')
            t_etp = ""
            if pd.notna(raw_e) and str(raw_e).strip() not in ['', 'nan', 'none', '0']:
                try:
                    e_clean = str(int(float(raw_e)))
                    t_etp = f" - Etape {e_clean}"
                except ValueError:
                    t_etp = f" - Etape {str(raw_e).strip()}"
            
            t_typ = ""
            if x.get('Type de course') == "Autre":
                val_t = x.get('🌄 Type', '')
                if val_t: t_typ = f" [{val_t}]"

            t_leader = ""
            l_val = str(x.get('👑 Leader général', '')).strip()
            if l_val and l_val.lower() not in ['nan', 'none', '0', '']:
                t_leader = f" (Leader : {l_val})"
            
            recap_items += f"- {x.get('🚴‍♂️ Course')} - {x.get('📆 Saison')}{t_etp}{t_typ}\n"
            recap_items += f"  Vainqueur : {x.get('🥇 Vainqueur')}{t_leader} - {x.get('Prix vidéo')}€\n\n"
        
        recap_footer = f"TOTAL FINAL : {total_final:.2f}€"
        
        st.code(recap_intro + recap_items + recap_footer)
        
        if st.button("🗑️ Vider le panier"):
            st.session_state.panier = []
            st.rerun()

# ==========================================
# PAGE : FAQ
# ==========================================
elif st.session_state.page == 'faq':
    st.header("❓ Foire Aux Questions & Infos")
    st.write("---")
    with st.expander("📺 D'où proviennent ces archives cyclistes ?"):
        st.write("Ces vidéos sont issues d'une collection personnelle bâtie sur des années : enregistrements TV d'époque (VHS), numérisations de DVD officiels et échanges entre passionnés internationaux. C'est un travail de mémoire pour ne pas oublier les exploits du passé.")
    with st.expander("🎞️ Quelle est la qualité des images ?"):
        st.write("Pour les courses des années 70 à 90, l'image possède le grain typique de l'époque (SD). C'est ce qui fait le charme du rétro ! Les fichiers DVD (.VOB) offrent la meilleure qualité possible sans compression supplémentaire. Les années 2010+ sont généralement disponibles en bien meilleure résolution.")
    with st.expander("🎙️ Y a-t-il les commentaires en français ?"):
        st.write("La majorité des archives possède des commentaires en français (Antenne 2, France TV, Eurosport). Cependant, certaines raretés (Giro ou courses belges anciennes) peuvent être en italien ou en flamand. C'est précisé dans la colonne 'Langue/Diffuseur'.")
    with st.expander("💳 Comment se déroule le paiement et la livraison ?"):
        st.write("Une fois votre panier validé, le paiement se fait par PayPal. Dès réception, je vous envoie un lien de téléchargement sécurisé (SwissTransfer ou WeTransfer). Attention, les liens sont temporaires (7 à 30 jours), pensez à sauvegarder vos fichiers sur votre disque dur !")
    with st.expander("🔄 Je cherche une étape précise qui n'est pas dans la liste..."):
        st.write("Le catalogue est mis à jour régulièrement. Si vous cherchez un 'Graal' précis (une étape oubliée, un critérium d'époque), contactez-moi par mail, je fouillerai mes cartons non encore répertoriés !")

# ==========================================
# PAGES CATALOGUE, RECHERCHE, STATS, PROGRESSION
# ==========================================
elif st.session_state.page == 'catalogue':
    st.header("📚 Catalogue Complet")
    afficher_resultats(df)

elif st.session_state.page == 'recherche_avancee':
    st.header("🕵️ Recherche Avancée")
    
    # 1. Extraction et tri des listes uniques pour les menus déroulants
    saisons = sorted(df['📆 Saison'].dropna().unique(), reverse=True)
    courses = sorted(df['🚴‍♂️ Course'].dropna().unique())
    # On gère le cas où des vainqueurs seraient manquants ou mal formatés
    vainqueurs = sorted(df['🥇 Vainqueur'].dropna().astype(str).unique())
    
    # On nettoie la liste des vainqueurs (retirer les '0', 'nan', etc.)
    vainqueurs_propres = [v for v in vainqueurs if v.lower() not in ['0', 'nan', 'none', 'inconnu']]

    # 2. Affichage des filtres sur 3 colonnes pour que ce soit harmonieux
    c1, c2, c3 = st.columns(3)
    with c1: 
        f_s = st.multiselect("🗓️ Saisons", saisons)
    with c2: 
        f_c = st.multiselect("🚴‍♂️ Courses", courses)
    with c3: 
        f_v = st.multiselect("🥇 Vainqueur", vainqueurs_propres)
    
    # 3. Application des filtres sur les données
    df_f = df.copy()
    if f_s: 
        df_f = df_f[df_f['📆 Saison'].isin(f_s)]
    if f_c: 
        df_f = df_f[df_f['🚴‍♂️ Course'].isin(f_c)]
    if f_v: 
        df_f = df_f[df_f['🥇 Vainqueur'].astype(str).isin(f_v)]
        
    st.write("---")
    
    # 4. Affichage du résultat final
    afficher_resultats(df_f)
elif st.session_state.page == 'statistiques':
    st.header("📊 Le Tableau de Bord du Peloton")
    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total Vidéos", len(df))
    with c2: st.metric("Coureurs Victorieux", df['🥇 Vainqueur'].dropna().nunique() if '🥇 Vainqueur' in df.columns else 0)
    with c3: st.metric("Courses Différentes", df['🚴‍♂️ Course'].dropna().nunique() if '🚴‍♂️ Course' in df.columns else 0)
    st.write("---")
    colA, colB = st.columns(2)
    with colA:
        st.markdown("### 🏆 Le Top 10 des Vainqueurs")
        if '🥇 Vainqueur' in df.columns:
            df_vainq = df['🥇 Vainqueur'].dropna().value_counts().reset_index()
            df_vainq.columns = ['Coureur', 'Victoires']
            df_vainq = df_vainq[~df_vainq['Coureur'].isin(['0', 'inconnu', 'Inconnu'])].head(10)
            fig_vainq = px.bar(df_vainq, x='Victoires', y='Coureur', orientation='h', text='Victoires', color='Victoires', color_continuous_scale='Reds')
            fig_vainq.update_traces(textposition='outside', textfont=dict(weight='bold'))
            fig_vainq.update_layout(yaxis={'categoryorder':'total ascending'}, yaxis_title="")
            st.plotly_chart(fig_vainq, use_container_width=True)
    with colB:
        st.markdown("### 🏁 Les Courses les plus présentes")
        if '🚴‍♂️ Course' in df.columns:
            df_course = df['🚴‍♂️ Course'].dropna().value_counts().head(10).reset_index()
            df_course.columns = ['Course', 'Nombre']
            fig_course = px.bar(df_course, x='Nombre', y='Course', orientation='h', text='Nombre', color='Nombre', color_continuous_scale='Blues')
            fig_course.update_traces(textposition='outside', textfont=dict(weight='bold'))
            fig_course.update_layout(yaxis={'categoryorder':'total ascending'}, yaxis_title="")
            st.plotly_chart(fig_course, use_container_width=True)

elif st.session_state.page == 'progression':
    st.header("🎯 Progression de la Collection")
    st.markdown("<p style='color: gray; font-size:16px;'>L'objectif ultime : archiver l'histoire intégrale des plus grandes courses du monde.</p>", unsafe_allow_html=True)
    st.divider()

    tdf_eds = df[df['🚴‍♂️ Course'].astype(str).str.contains('Tour de France', case=False, na=False)]['📆 Saison'].nunique() if '🚴‍♂️ Course' in df.columns else 0
    giro_eds = df[df['🚴‍♂️ Course'].astype(str).str.contains('Giro', case=False, na=False)]['📆 Saison'].nunique() if '🚴‍♂️ Course' in df.columns else 0
    vuelta_eds = df[df['🚴‍♂️ Course'].astype(str).str.contains('Vuelta', case=False, na=False)]['📆 Saison'].nunique() if '🚴‍♂️ Course' in df.columns else 0
    roub_eds = df[df['🚴‍♂️ Course'].astype(str).str.contains('Roubaix', case=False, na=False)]['📆 Saison'].nunique() if '🚴‍♂️ Course' in df.columns else 0
    flandres_eds = df[df['🚴‍♂️ Course'].astype(str).str.contains('Flandres', case=False, na=False)]['📆 Saison'].nunique() if '🚴‍♂️ Course' in df.columns else 0

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏔️ Grands Tours")
        st.markdown(f"**Tour de France** ({tdf_eds}/110 éditions historiques)")
        st.progress(min(1.0, tdf_eds / 110.0))
        
        st.markdown(f"**Giro d'Italia** ({giro_eds}/106 éditions)")
        st.progress(min(1.0, giro_eds / 106.0))
        
        st.markdown(f"**Vuelta a España** ({vuelta_eds}/78 éditions)")
        st.progress(min(1.0, vuelta_eds / 78.0))
        
    with col2:
        st.markdown("### 🏛️ Les Monuments Pavés")
        st.markdown(f"**Paris-Roubaix** ({roub_eds}/120 éditions)")
        st.progress(min(1.0, roub_eds / 120.0))
        
        st.markdown(f"**Tour des Flandres** ({flandres_eds}/107 éditions)")
        st.progress(min(1.0, flandres_eds / 107.0))
        
    st.write("---")
    st.info("💡 *Ce tableau compte le nombre de Saisons annuelles couvertes par au moins une vidéo de l'épreuve dans le catalogue.*")

# ==========================================
# 🛑 PIED DE PAGE (FOOTER GLOBAL)
# ==========================================
st.write("---")

foot_a, foot_b = st.columns([1, 1])

with foot_a:
    annee_actuelle = datetime.now().year
    st.markdown(f"<br><p style='color: gray; font-size: 14px;'>© {annee_actuelle} - Le Grenier du Cyclisme<br><i>La mémoire de la petite reine.</i></p>", unsafe_allow_html=True)

with foot_b:
    st.markdown("**La Voiture Balai**")
    st.markdown("✉️ [legrenierdufootball@hotmail.com](mailto:legrenierdufootball@hotmail.com)") # Mets ton vrai email ici
    
   
