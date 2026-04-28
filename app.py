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
# ⚙️ FONCTIONS DES POP-UPS (INFORMATIONS)
# ==========================================
@st.dialog("🧭 Guide & Contenu")
def popup_guide_contenu():
    st.markdown("""
    **Bienvenue dans l'antre du Grenier du Cyclisme !** Plus de 2100 archives pour revivre la légende du peloton.
    
    **Dans ce catalogue massif :**
    * 💛 **Les Grands Tours :** Tour de France, Giro, Vuelta (étapes intégrales ou résumés longs).
    * 🪨 **Les Classiques :** Les 5 Monuments (Roubaix, Flandres, Liège, San Remo, Lombardie) et les semi-classiques.
    * 🌈 **Championnats :** Courses en ligne et chronos des Championnats du Monde et d'Europe.
    * ⏱️ **Courses d'une semaine :** Paris-Nice, Dauphiné, Tirreno-Adriatico, Tour de Suisse...
    
    ### 🛠️ Mode d'emploi
    Utilisez la **Recherche Rapide** en page d'accueil ou la **Recherche Avancée** pour filtrer par coureur (vainqueur), par année ou par type de course (Montagne, Pavés, etc.).
    """)

@st.dialog("💾 Formats & Qualité")
def popup_formats():
    st.markdown("### 🗂️ Types de retransmissions")
    st.markdown("""
    * 🏁 **Intégralité :** La course ou l'étape du premier au dernier kilomètre.
    * 🎥 **Long Format / Résumé :** Les moments clés et le final (souvent 45min à 1h30).
    * 📺 **Diffuseurs :** Archives provenant de France TV, Eurosport, RAI, RTBF, etc.
    """)
    st.divider()
    st.markdown("### 📼 Formats disponibles")
    st.markdown("""
    * 💻 **Numérique :** Fichiers standards (.mp4, .mkv, .avi) envoyés par lien de téléchargement.
    * 💿 **Qualité DVD :** Fichiers .VOB originaux (meilleur débit d'image brut pour les archives anciennes).
    """)

@st.dialog("💶 Tarifs & Réductions")
def popup_tarifs():
    st.markdown("### 💰 Prix des vidéos")
    st.markdown("""
    Les prix sont indiqués individuellement pour chaque vidéo dans le catalogue. Ils dépendent de la **rareté** de l'archive et de son **format** (intégrale ou résumé).
    """)
    st.divider()
    st.markdown("### 🎁 Remises dégressives (Automatiques)")
    st.markdown("""
    Plus vous complétez votre collection, plus le prix baisse :
    * 🥉 **Dès 5 vidéos :** -10% sur le total
    * 🥈 **Dès 10 vidéos :** -15% sur le total
    * 🥇 **Dès 20 vidéos :** -20% sur le total
    """)

@st.dialog("✉️ Contact & Commandes")
def popup_contact_commandes():
    st.markdown("""
    **Comment valider votre sélection ?**
    1. 🛒 **Le Panier :** Ajoutez vos étapes ou classiques préférées au panier.
    2. ✉️ **L'envoi :** Copiez le récapitulatif du panier et envoyez-le par e-mail à **votre-email@exemple.com** (ou via Instagram).
    3. 💳 **Le Paiement :** Je vous répondrai avec les instructions pour un paiement sécurisé via **PayPal**.
    4. 🚀 **La Livraison :** Dès validation, vous recevez vos liens de téléchargement privés (généralement sous 24/48h).
    """)

@st.dialog("🤝 Proposer un Échange")
def popup_echanges():
    st.markdown("""
    **Faisons grandir le Grenier ensemble !** Je suis toujours à la recherche d'étapes manquantes, de versions TV spécifiques (anciens commentaires FR) ou de raretés des années 70-80-90.
    
    Si vous possédez vos propres numérisations ou archives sur disques durs, contactez-moi ! Je suis très ouvert aux échanges équitables entre passionnés de la petite reine.
    """)

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
cols_cat = [c for c in ['📆 Saison', '🚴‍♂️ Course', '📅 Date', '🔢 Etape', '🥇 Vainqueur', 'Format vidéo', '📺 Diffuseur', 'Prix vidéo'] if c in df.columns]

# --- AFFICHAGE RESULTATS ---
def afficher_resultats(df_res):
    if df_res.empty: return st.warning("Aucun résultat.")
    st.metric("Vidéos", len(df_res))
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
    st.markdown("<h2 style='text-align: center;'>🚴‍♂️ Menu</h2>", unsafe_allow_html=True)
    if st.button("🏠 Accueil", use_container_width=True): go_home(); st.rerun()
    if st.button("❓ F.A.Q & Infos", use_container_width=True): st.session_state.page = 'faq'; st.rerun()
    st.divider()
    nb = len(st.session_state.panier)
    if st.button(f"🛒 Panier ({nb})", use_container_width=True, type="primary" if nb>0 else "secondary"): st.session_state.page = 'panier'; st.rerun()
    st.divider()
    if st.button("📖 Catalogue Complet", use_container_width=True): st.session_state.page = 'catalogue'; st.rerun()
    if st.button("🕵️ Recherche Avancée", use_container_width=True): st.session_state.page = 'recherche_avancee'; st.rerun()

# ==========================================
# PAGE : ACCUEIL
# ==========================================
if st.session_state.page == 'accueil':
    st.markdown(f"<div style='text-align: center;'><h1>🚴‍♂️ Le Grenier du Cyclisme</h1><p>Revivez plus de 2100 moments historiques du peloton</p></div>", unsafe_allow_html=True)
    st.write("---")
    
    # RANGÉE DES 5 BOUTONS INFOS
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
    q = st.text_input("🔍 Recherche Rapide", placeholder="Ex: Pantani, Alpe d'Huez, 1998...")
    if q:
        m = df.apply(lambda x: x.astype(str).str.contains(q, case=False).any(), axis=1)
        afficher_resultats(df[m])

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
# PAGE : PANIER (MISE À JOUR FORMAT RÉCAP)
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
            
            # --- LOGIQUE D'AFFICHAGE ---
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
            
            # Affichage visuel dans le panier Streamlit
            c_i.markdown(f"**{m.get('🚴‍♂️ Course')} - {m.get('📆 Saison')}{txt_etape}**{txt_type}<br>Vainqueur : {m.get('🥇 Vainqueur')}", unsafe_allow_html=True)
            c_p.write(f"**{m.get('Prix vidéo')} €**")
            
            if c_b.button("❌", key=f"del_{i}"):
                st.session_state.panier.pop(i)
                st.rerun()
        
        st.divider()
        
        # --- CALCUL DES REMISES ---
        pct = 20 if nb_a >= 20 else (15 if nb_a >= 10 else (10 if nb_a >= 5 else 0))
        rem = tot_b * (pct/100)
        total_final = tot_b - rem
        
        if pct > 0:
            st.success(f"🎁 Remise volume de {pct}% appliquée : -{rem:.2f}€")
        
        st.subheader(f"Total à payer : {total_final:.2f} €")
        
        # --- GÉNÉRATION DU RÉCAP TEXTE (FORMAT DEMANDÉ) ---
        st.write("---")
        st.markdown("📩 **Récapitulatif de la commande :**")
        
        recap_intro = f"Bonjour, je souhaite commander ces {nb_a} vidéos sur Le Grenier du Cyclisme :\n\n"
        recap_items = ""
        
        for x in st.session_state.panier:
            # Nettoyage étape
            raw_e = x.get('🔢 Etape', '')
            t_etp = ""
            if pd.notna(raw_e) and str(raw_e).strip() not in ['', 'nan', 'none', '0']:
                try:
                    e_clean = str(int(float(raw_e)))
                    t_etp = f" - Etape {e_clean}"
                except ValueError:
                    t_etp = f" - Etape {str(raw_e).strip()}"
            
            # Type si Autre
            t_typ = ""
            if x.get('Type de course') == "Autre":
                val_t = x.get('🌄 Type', '')
                if val_t: t_typ = f" [{val_t}]"
            
            # CONSTRUCTION DU BLOC (Course-Saison-Etape + Saut de ligne + Vainqueur)
            recap_items += f"- {x.get('🚴‍♂️ Course')} - {x.get('📆 Saison')}{t_etp}{t_typ}\n"
            recap_items += f"  Vainqueur : {x.get('🥇 Vainqueur')} - {x.get('Prix vidéo')}€\n\n"
        
        recap_footer = f"TOTAL FINAL : {total_final:.2f}€"
        
        st.code(recap_intro + recap_items + recap_footer)
        
        if st.button("🗑️ Vider le panier"):
            st.session_state.panier = []
            st.rerun()
