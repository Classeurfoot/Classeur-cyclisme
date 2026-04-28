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
# ---------------------------

# ==========================================
# ⚙️ GESTION DE LA NAVIGATION & PANIER
# ==========================================
if 'page' not in st.session_state: st.session_state.page = 'accueil'
if 'chemin' not in st.session_state: st.session_state.chemin = []
if 'course_choisie' not in st.session_state: st.session_state.course_choisie = None
if 'recherche_coureur_cible' not in st.session_state: st.session_state.recherche_coureur_cible = None
if 'panier' not in st.session_state: st.session_state.panier = []

def go_home():
    st.session_state.page = 'accueil'
    st.session_state.chemin = []
    st.session_state.course_choisie = None
    st.session_state.recherche_coureur_cible = None

# ==========================================
# ⚙️ FONCTIONS DES POP-UPS (INFORMATIONS)
# ==========================================
@st.dialog("🧭 Guide & Contenu")
def popup_guide_contenu():
    st.markdown("""
    **Bienvenue dans l'antre du Grenier du Cyclisme !** Plus de 2100 vidéos de courses au chaud : des classiques mythiques, des étapes de légende, et des grands tours entiers. 
    
    **Dans ce catalogue :**
    * 💛 **Les Grands Tours** : Tour de France, Giro d'Italia, Vuelta.
    * 🪨 **Les Classiques** : Paris-Roubaix, Tour des Flandres, Liège-Bastogne-Liège...
    * 🌈 **Les Championnats** : Monde, Europe, Nationaux.
    * ⏱️ **Les Courses à étapes** : Paris-Nice, Dauphiné, Tirreno-Adriatico...
    """)

@st.dialog("💶 Tarifs & Offres")
def popup_tarifs():
    st.markdown("### 💰 Grille Tarifaire")
    st.markdown("""
    Les prix varient selon la **rareté**, le **format** (intégralité, résumé) et le **type de course**. 
    Le tarif exact de chaque vidéo est affiché directement dans le catalogue et s'ajoute automatiquement à votre panier.
    """)
    st.divider()
    st.markdown("### 🎁 Remises au volume")
    st.markdown("""
    Pour les passionnés qui souhaitent revivre un Grand Tour entier ou se faire une belle collection de Classiques, des réductions s'appliquent automatiquement dans votre panier :
    * 🥉 **Dès 5 vidéos :** -10% sur le total
    * 🥈 **Dès 10 vidéos :** -15% sur le total
    * 🥇 **Dès 20 vidéos :** -20% sur le total
    """)
# ==========================================
# 3. CHARGEMENT DES DONNÉES
# ==========================================
@st.cache_data
def load_data():
    try:
        # Lecture du fichier cyclisme.csv (bien vérifier que le séparateur est un point-virgule)
        df = pd.read_csv("cyclisme.csv", sep=";", encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        
        # Nettoyage des lignes vides
        df = df.dropna(subset=['🚴‍♂️ Course', '📅 Date'], how='all')
        
        # Formatage des prix (remplacer les virgules par des points si besoin)
        if 'Prix vidéo' in df.columns:
            df['Prix vidéo'] = df['Prix vidéo'].astype(str).str.replace(',', '.').apply(pd.to_numeric, errors='coerce').fillna(3.0)
            
        return df
    except Exception as e:
        st.error(f"Erreur de lecture du fichier : {e}")
        return pd.DataFrame()

df = load_data()

# Colonnes clés adaptées au cyclisme
colonnes_presentes = [c for c in ['📆 Saison', '🚴‍♂️ Course', '📅 Date', '🔢 Etape', '🟢 Ville départ', '🏁 Ville d\'arrivée', '📏 Distance', '🌄 Type', '🥇 Vainqueur', '👑 Leader général', 'Format vidéo', '📺 Diffuseur', 'Rareté', 'Prix vidéo'] if c in df.columns]

# --- OUTIL : FICHES DE COURSES ---
def afficher_resultats(df_resultats):
    if df_resultats.empty:
        st.warning("Aucune course trouvée.")
        return
        
    st.metric("Vidéos trouvées", len(df_resultats))
    
    st.markdown("<p style='color: gray; font-size:14px;'>☑️ Cochez les vidéos dans la première colonne, puis cliquez sur le bouton en dessous pour les ajouter au panier.</p>", unsafe_allow_html=True)
    
    # Création d'une copie du dataframe pour l'affichage interactif
    df_display = df_resultats[colonnes_presentes].copy()
    df_display.insert(0, "Sélection", False)
    
    # Affichage du tableau éditable
    edited_df = st.data_editor(
        df_display,
        column_config={
            "Sélection": st.column_config.CheckboxColumn("🛒 Ajouter", default=False),
            "Prix vidéo": st.column_config.NumberColumn("💶 Prix (€)", format="%.2f €")
        },
        disabled=colonnes_presentes, # Empêche de modifier les vraies données
        hide_index=True,
        use_container_width=True,
        height=500
    )
    
    # Récupérer les lignes cochées
    selected_rows = edited_df[edited_df["Sélection"] == True]
    
    if len(selected_rows) > 0:
        if st.button(f"🛒 Ajouter les {len(selected_rows)} vidéo(s) sélectionnée(s) au panier", type="primary", use_container_width=True):
            for _, row in selected_rows.iterrows():
                match_dict = {k: ("" if pd.isna(v) else v) for k, v in row.to_dict().items() if k != "Sélection"}
                # Création d'un ID unique basé sur la date et la course
                match_id = f"{match_dict.get('📅 Date', '')}_{match_dict.get('🚴‍♂️ Course', '')}_{match_dict.get('🔢 Etape', '')}"
                in_cart = any(f"{m.get('📅 Date', '')}_{m.get('🚴‍♂️ Course', '')}_{m.get('🔢 Etape', '')}" == match_id for m in st.session_state.panier)
                
                if not in_cart:
                    st.session_state.panier.append(match_dict)
            
            st.rerun()

# ==========================================
# 🧭 BARRE LATÉRALE PERSISTANTE
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🚴‍♂️ Menu Rapide</h2>", unsafe_allow_html=True)
    st.write("") 
    
    if st.button("🏠 Accueil", width="stretch"):
        go_home()
        st.rerun()
                
    if st.button("❓ F.A.Q & Infos", width="stretch"):
        st.session_state.page = 'faq'
        st.rerun()
        
    st.divider()
                     
    nb_articles = len(st.session_state.panier)
    if st.button(f"🛒 Mon Panier ({nb_articles})", width="stretch", type="primary" if nb_articles > 0 else "secondary"):
        st.session_state.page = 'panier'
        st.rerun()
            
    st.divider()
    st.markdown("### 📂 Explorer")
    
    if st.button("📖 Catalogue Complet", width="stretch"):
        st.session_state.page = 'catalogue'
        st.rerun()
    if st.button("🚴‍♂️ Par Coureur (Vainqueur)", width="stretch"):
        st.session_state.page = 'recherche_coureur'
        st.rerun()
    if st.button("🕵️ Recherche Avancée", width="stretch"):
        st.session_state.page = 'recherche_avancee'
        st.rerun()

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
    
    recherche_rapide = st.text_input("🔍 Recherche Rapide", placeholder="Tapez un coureur, une course, une année, un lieu...")
    if recherche_rapide:
        mask = pd.Series(False, index=df.index)
        for col in df.columns:
            mask = mask | df[col].astype(str).str.contains(recherche_rapide, case=False, na=False)
                
        df_trouve = df[mask]
        st.write(f"**Résultats trouvés pour :** '{recherche_rapide}'")
        afficher_resultats(df_trouve)
        st.write("---")

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("🧭 Guide & Contenu", use_container_width=True): popup_guide_contenu()
    with col_btn2:
        if st.button("💶 Tarifs & Formats", use_container_width=True): popup_tarifs()
    with col_btn3:
        if st.button("📖 Voir tout le catalogue", use_container_width=True, type="primary"): 
            st.session_state.page = 'catalogue'
            st.rerun()

# ==========================================
# PAGE : LE PANIER
# ==========================================
elif st.session_state.page == 'panier':
    st.header("🛒 Mon Panier")
    
    if len(st.session_state.panier) == 0:
        st.info("Votre panier est vide pour le moment. Naviguez dans le catalogue pour ajouter des vidéos !")
        if st.button("Retourner à l'accueil"):
            go_home()
            st.rerun()
    else:
        nb_articles = len(st.session_state.panier)
        st.markdown(f"**Vous avez sélectionné {nb_articles} vidéo(s).**")
        st.write("---")
        
        total_prix_brut = 0
        items_a_supprimer = []
        
        for i, match in enumerate(st.session_state.panier):
            col_info, col_prix, col_btn = st.columns([6, 2, 1])
            
            date_m = match.get('📅 Date', '?')
            course_m = match.get('🚴‍♂️ Course', '?')
            etape_m = match.get('🔢 Etape', '')
            vainqueur = match.get('🥇 Vainqueur', 'Inconnu')
            
            prix = float(match.get('Prix vidéo', 3.0))
            
            with col_info:
                txt_etape = f" - Etape {etape_m}" if str(etape_m).strip() and str(etape_m) not in ['nan', 'None'] else ""
                st.markdown(f"🗓️ **{date_m}** | 🚴‍♂️ **{course_m}{txt_etape}**<br>🥇 Vainqueur : {vainqueur}", unsafe_allow_html=True)
            
            with col_prix:
                st.markdown(f"<div style='margin-top: 10px; font-weight: bold; font-size: 18px;'>{prix:.2f} €</div>", unsafe_allow_html=True)
                
            with col_btn:
                if st.button("❌", key=f"del_cart_{i}"):
                    items_a_supprimer.append(i)
            
            st.divider()
            total_prix_brut += prix
                
        # Exécution de la suppression
        if items_a_supprimer:
            for idx in sorted(items_a_supprimer, reverse=True):
                st.session_state.panier.pop(idx)
            st.rerun()
            
        # ==================================
        # CALCUL DE LA REMISE DÉGRESSIVE
        # ==================================
        remise_pct = 0
        if nb_articles >= 20:
            remise_pct = 20
        elif nb_articles >= 10:
            remise_pct = 15
        elif nb_articles >= 5:
            remise_pct = 10
            
        montant_remise = total_prix_brut * (remise_pct / 100.0)
        total_final = total_prix_brut - montant_remise
            
        st.subheader("💳 Récapitulatif")
        
        if remise_pct > 0:
            st.markdown(f"**Sous-total brut :** {total_prix_brut:.2f} €")
            st.success(f"🎁 **Remise volume appliquée (-{remise_pct}%) :** -{montant_remise:.2f} €")
            
        st.markdown(f"### **Total à payer : {total_final:.2f} €**")
        st.write("---")
        
        texte_recap = "Bonjour, je souhaite commander ces vidéos vues dans Le Grenier du Cyclisme :\n\n"
        for match in st.session_state.panier:
            txt_etp = f" (Etape {match.get('🔢 Etape', '')})" if str(match.get('🔢 Etape', '')).strip() and str(match.get('🔢 Etape', '')) not in ['nan', 'None'] else ""
            texte_recap += f"- {match.get('📅 Date', '?')} | {match.get('🚴‍♂️ Course', '')}{txt_etp} - {float(match.get('Prix vidéo', 3.0)):.2f}€\n"
        
        texte_recap += f"\nTotal d'articles : {nb_articles}"
        if remise_pct > 0:
            texte_recap += f"\nSous-total : {total_prix_brut:.2f}€"
            texte_recap += f"\nRemise volume (-{remise_pct}%) : -{montant_remise:.2f}€"
            
        texte_recap += f"\nMontant Total : {total_final:.2f}€"
        
        st.markdown("Copiez le texte ci-dessous pour me l'envoyer par e-mail ou messagerie :")
        st.code(texte_recap, language="text")
        
        if st.button("🗑️ Vider tout le panier", type="secondary"):
            st.session_state.panier = []
            st.rerun()

# ==========================================
# PAGE : CATALOGUE COMPLET
# ==========================================
elif st.session_state.page == 'catalogue':
    st.header("📚 Le Catalogue Complet")
    afficher_resultats(df)

# ==========================================
# PAGE : RECHERCHE PAR COUREUR
# ==========================================
elif st.session_state.page == 'recherche_coureur':
    st.header("🥇 Recherche par Coureur (Vainqueur)")
    if '🥇 Vainqueur' in df.columns:
        tous_les_coureurs = sorted(df['🥇 Vainqueur'].dropna().astype(str).unique())
        
        idx_defaut = 0
        cible = st.session_state.get('recherche_coureur_cible')
        if cible and cible in tous_les_coureurs:
            idx_defaut = tous_les_coureurs.index(cible)
            
        choix = st.selectbox("Sélectionne un coureur :", tous_les_coureurs, index=idx_defaut)
        st.session_state.recherche_coureur_cible = choix 
        
        df_filtre = df[df['🥇 Vainqueur'].astype(str) == choix]
        afficher_resultats(df_filtre)
    else:
        st.error("La colonne '🥇 Vainqueur' est introuvable.")

# ==========================================
# PAGE : RECHERCHE AVANCÉE
# ==========================================
elif st.session_state.page == 'recherche_avancee':
    st.header("🕵️ Recherche Avancée")
    
    courses = sorted(df['🚴‍♂️ Course'].dropna().astype(str).unique()) if '🚴‍♂️ Course' in df.columns else []
    types_course = sorted(df['Type de course'].dropna().astype(str).unique()) if 'Type de course' in df.columns else []
    saisons = sorted(df['📆 Saison'].dropna().astype(str).unique(), reverse=True) if '📆 Saison' in df.columns else []
    
    col1, col2 = st.columns(2)
    with col1:
        f_courses = st.multiselect("🚴‍♂️ Courses :", courses)
    with col2:
        f_types = st.multiselect("🏷️ Type de course :", types_course)
        
    col3, col4 = st.columns(2)
    with col3:
        f_saisons = st.multiselect("🗓️ Saisons :", saisons)
        
    df_filtre = df.copy()
    if f_courses: df_filtre = df_filtre[df_filtre['🚴‍♂️ Course'].isin(f_courses)]
    if f_types: df_filtre = df_filtre[df_filtre['Type de course'].isin(f_types)]
    if f_saisons: df_filtre = df_filtre[df_filtre['📆 Saison'].isin(f_saisons)]
        
    st.write("---")
    afficher_resultats(df_filtre)

elif st.session_state.page == 'faq':
    st.header("❓ F.A.Q")
    st.write("Mettez ici vos informations de contact et d'échange.")
