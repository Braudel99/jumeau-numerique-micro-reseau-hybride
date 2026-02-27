"""
MODULE PÉDAGOGIQUE - TRAVAUX PRATIQUES GUIDÉS
==============================================
Module pour le projet de Master en Technopédagogie et Didactique
Permet aux étudiants de suivre des TPs guidés avec génération de compte-rendu PDF
"""

import streamlit as st
from datetime import datetime
from fpdf import FPDF
import json

# ============================================================================
# DÉFINITION DES TRAVAUX PRATIQUES
# ============================================================================

TRAVAUX_PRATIQUES = {
    "TP1": {
        "titre": "Découverte du système hybride",
        "objectif": "Comprendre les composants d'un micro-réseau hybride et leur rôle",
        "duree": "1h30",
        "niveau": "Débutant",
        "icon": "🔍",
        "etapes": [
            {
                "numero": 1,
                "titre": "Exploration de l'interface",
                "consigne": "Parcourez l'interface de la plateforme et identifiez les différentes sections de configuration.",
                "type": "observation",
                "questions": [
                    {
                        "id": "tp1_q1",
                        "texte": "Combien de sections de configuration y a-t-il dans la sidebar ?",
                        "type": "number",
                        "reponse_attendue": 7,
                        "tolerance": 0,
                        "points": 2
                    },
                    {
                        "id": "tp1_q2",
                        "texte": "Listez les 4 sources d'énergie du système hybride :",
                        "type": "text",
                        "mots_cles": ["pv", "solaire", "batterie", "sbee", "diesel"],
                        "points": 3
                    }
                ]
            },
            {
                "numero": 2,
                "titre": "Comprendre le système PV",
                "consigne": "Dans la section 'Système PV', observez les différents paramètres disponibles.",
                "type": "manipulation",
                "questions": [
                    {
                        "id": "tp1_q3",
                        "texte": "Quelle est la différence de rendement entre monocristallin et polycristallin ?",
                        "type": "text",
                        "mots_cles": ["18", "15", "3", "rendement", "efficacité"],
                        "points": 2
                    },
                    {
                        "id": "tp1_q4",
                        "texte": "Si vous installez 10 panneaux de 200W, quelle est la puissance totale en kWc ?",
                        "type": "number",
                        "reponse_attendue": 2,
                        "tolerance": 0,
                        "points": 2
                    }
                ]
            },
            {
                "numero": 3,
                "titre": "Comprendre la batterie",
                "consigne": "Examinez la section batterie et comprenez le concept de DoD (Depth of Discharge).",
                "type": "theorie",
                "questions": [
                    {
                        "id": "tp1_q5",
                        "texte": "Quel est le DoD recommandé pour une batterie Lithium-ion ?",
                        "type": "choice",
                        "options": ["50%", "60%", "80%", "100%"],
                        "reponse_attendue": "80%",
                        "points": 2
                    },
                    {
                        "id": "tp1_q6",
                        "texte": "Pourquoi le DoD du Plomb-acide est-il plus faible que le Lithium-ion ?",
                        "type": "textarea",
                        "mots_cles": ["durée de vie", "cycles", "dégradation", "chimie"],
                        "points": 3
                    }
                ]
            },
            {
                "numero": 4,
                "titre": "Première simulation",
                "consigne": "Lancez votre première simulation avec les paramètres par défaut et observez les résultats.",
                "type": "simulation",
                "questions": [
                    {
                        "id": "tp1_q7",
                        "texte": "Quel est le taux de couverture obtenu (en %) ?",
                        "type": "number",
                        "reponse_attendue": None,  # Réponse variable
                        "tolerance": 100,  # Accepte toute valeur
                        "points": 2
                    },
                    {
                        "id": "tp1_q8",
                        "texte": "Quelle source d'énergie contribue le plus à la couverture de la charge ?",
                        "type": "choice",
                        "options": ["PV", "Batterie", "SBEE", "Diesel"],
                        "reponse_attendue": None,  # Variable selon config
                        "points": 2
                    }
                ]
            }
        ],
        "synthese": {
            "question": "En quelques phrases, expliquez le principe de fonctionnement d'un micro-réseau hybride PV-Batterie-SBEE.",
            "points": 5
        }
    },
    
    "TP2": {
        "titre": "Influence de la puissance PV",
        "objectif": "Observer l'impact du dimensionnement PV sur la couverture énergétique",
        "duree": "2h",
        "niveau": "Intermédiaire",
        "icon": "🌞",
        "etapes": [
            {
                "numero": 1,
                "titre": "Configuration de base",
                "consigne": "Configurez une charge résidentielle (villa) avec une consommation d'environ 50 kWh/jour.",
                "type": "manipulation",
                "questions": [
                    {
                        "id": "tp2_q1",
                        "texte": "Quelle puissance max avez-vous configurée (kW) ?",
                        "type": "number",
                        "reponse_attendue": 15,
                        "tolerance": 10,
                        "points": 2
                    }
                ]
            },
            {
                "numero": 2,
                "titre": "Simulation avec 3 kWc",
                "consigne": "Réglez la puissance PV à environ 3 kWc (15 panneaux de 200W) et lancez la simulation.",
                "type": "simulation",
                "questions": [
                    {
                        "id": "tp2_q2",
                        "texte": "Quelle est la couverture PV avec 3 kWc (%) ?",
                        "type": "number",
                        "reponse_attendue": None,
                        "tolerance": 100,
                        "points": 3
                    },
                    {
                        "id": "tp2_q3",
                        "texte": "Quelle est la production PV journalière (kWh) ?",
                        "type": "number",
                        "reponse_attendue": None,
                        "tolerance": 100,
                        "points": 2
                    }
                ]
            },
            {
                "numero": 3,
                "titre": "Simulation avec 5 kWc",
                "consigne": "Augmentez la puissance PV à 5 kWc (25 panneaux de 200W) et relancez.",
                "type": "simulation",
                "questions": [
                    {
                        "id": "tp2_q4",
                        "texte": "Quelle est la couverture PV avec 5 kWc (%) ?",
                        "type": "number",
                        "reponse_attendue": None,
                        "tolerance": 100,
                        "points": 3
                    },
                    {
                        "id": "tp2_q5",
                        "texte": "Quelle est la production PV journalière (kWh) ?",
                        "type": "number",
                        "reponse_attendue": None,
                        "tolerance": 100,
                        "points": 2
                    }
                ]
            },
            {
                "numero": 4,
                "titre": "Analyse comparative",
                "consigne": "Comparez les résultats des deux configurations.",
                "type": "analyse",
                "questions": [
                    {
                        "id": "tp2_q6",
                        "texte": "De combien de % la couverture a-t-elle augmenté ?",
                        "type": "number",
                        "reponse_attendue": None,
                        "tolerance": 100,
                        "points": 3
                    },
                    {
                        "id": "tp2_q7",
                        "texte": "La couverture est-elle proportionnelle à la puissance PV ? Pourquoi ?",
                        "type": "textarea",
                        "mots_cles": ["non", "saturation", "batterie", "stockage", "nuit", "limite"],
                        "points": 4
                    }
                ]
            }
        ],
        "synthese": {
            "question": "Expliquez pourquoi doubler la puissance PV ne double pas nécessairement la couverture énergétique.",
            "points": 5
        }
    },
    
    "TP3": {
        "titre": "Rôle du stockage batterie",
        "objectif": "Comprendre l'importance de la capacité de stockage dans un système hybride",
        "duree": "2h",
        "niveau": "Intermédiaire",
        "icon": "🔋",
        "etapes": [
            {
                "numero": 1,
                "titre": "Configuration sans batterie suffisante",
                "consigne": "Configurez un système avec 5 kWc de PV mais seulement 2h d'autonomie batterie.",
                "type": "manipulation",
                "questions": [
                    {
                        "id": "tp3_q1",
                        "texte": "Quelle est la capacité batterie configurée (kWh) ?",
                        "type": "number",
                        "reponse_attendue": None,
                        "tolerance": 100,
                        "points": 2
                    }
                ]
            },
            {
                "numero": 2,
                "titre": "Observation du profil SOC",
                "consigne": "Lancez la simulation et observez l'évolution du SOC (State of Charge) sur 24h.",
                "type": "simulation",
                "questions": [
                    {
                        "id": "tp3_q2",
                        "texte": "À quelle heure le SOC atteint-il son maximum ?",
                        "type": "number",
                        "reponse_attendue": 14,
                        "tolerance": 2,
                        "points": 2
                    },
                    {
                        "id": "tp3_q3",
                        "texte": "À quelle heure la batterie est-elle épuisée (SOC minimum) ?",
                        "type": "number",
                        "reponse_attendue": None,
                        "tolerance": 100,
                        "points": 2
                    }
                ]
            },
            {
                "numero": 3,
                "titre": "Augmentation de l'autonomie",
                "consigne": "Augmentez l'autonomie batterie à 8h et relancez la simulation.",
                "type": "simulation",
                "questions": [
                    {
                        "id": "tp3_q4",
                        "texte": "Quelle est la nouvelle capacité batterie (kWh) ?",
                        "type": "number",
                        "reponse_attendue": None,
                        "tolerance": 100,
                        "points": 2
                    },
                    {
                        "id": "tp3_q5",
                        "texte": "Comment a évolué la consommation SBEE (kWh) ?",
                        "type": "textarea",
                        "mots_cles": ["diminué", "baisse", "réduit", "moins"],
                        "points": 3
                    }
                ]
            },
            {
                "numero": 4,
                "titre": "Analyse économique",
                "consigne": "Activez l'analyse économique et comparez les deux configurations.",
                "type": "analyse",
                "questions": [
                    {
                        "id": "tp3_q6",
                        "texte": "Quel est l'impact sur le CAPEX (investissement) ?",
                        "type": "textarea",
                        "mots_cles": ["augmente", "plus élevé", "coût", "investissement"],
                        "points": 3
                    },
                    {
                        "id": "tp3_q7",
                        "texte": "Est-ce que l'augmentation de capacité batterie est toujours rentable ?",
                        "type": "textarea",
                        "mots_cles": ["dépend", "payback", "économie", "sbee", "tarif"],
                        "points": 4
                    }
                ]
            }
        ],
        "synthese": {
            "question": "Décrivez le compromis entre capacité de stockage, coût d'investissement et autonomie du système.",
            "points": 5
        }
    },
    
    "TP4": {
        "titre": "Impact de la fiabilité SBEE",
        "objectif": "Analyser l'effet des coupures de courant sur le dimensionnement du système",
        "duree": "1h30",
        "niveau": "Intermédiaire",
        "icon": "🔌",
        "etapes": [
            {
                "numero": 1,
                "titre": "Scénario SBEE stable",
                "consigne": "Configurez le scénario SBEE sur 'Stable (95%)' et lancez une simulation.",
                "type": "simulation",
                "questions": [
                    {
                        "id": "tp4_q1",
                        "texte": "Quelle est la consommation SBEE sur 24h (kWh) ?",
                        "type": "number",
                        "reponse_attendue": None,
                        "tolerance": 100,
                        "points": 2
                    },
                    {
                        "id": "tp4_q2",
                        "texte": "Y a-t-il des heures de déficit (hors tension) ?",
                        "type": "choice",
                        "options": ["Oui", "Non"],
                        "reponse_attendue": None,
                        "points": 2
                    }
                ]
            },
            {
                "numero": 2,
                "titre": "Scénario SBEE instable",
                "consigne": "Changez le scénario SBEE sur 'Instable (60%)' et relancez.",
                "type": "simulation",
                "questions": [
                    {
                        "id": "tp4_q3",
                        "texte": "Combien d'heures de déficit observez-vous ?",
                        "type": "number",
                        "reponse_attendue": None,
                        "tolerance": 100,
                        "points": 3
                    },
                    {
                        "id": "tp4_q4",
                        "texte": "Comment évolue l'utilisation de la batterie ?",
                        "type": "textarea",
                        "mots_cles": ["augmente", "sollicitée", "décharge", "plus"],
                        "points": 3
                    }
                ]
            },
            {
                "numero": 3,
                "titre": "Activation du diesel",
                "consigne": "Activez le groupe diesel (ATS) et relancez la simulation.",
                "type": "simulation",
                "questions": [
                    {
                        "id": "tp4_q5",
                        "texte": "Le diesel a-t-il été utilisé ?",
                        "type": "choice",
                        "options": ["Oui", "Non"],
                        "reponse_attendue": None,
                        "points": 2
                    },
                    {
                        "id": "tp4_q6",
                        "texte": "Quelle est maintenant la couverture totale (%) ?",
                        "type": "number",
                        "reponse_attendue": 100,
                        "tolerance": 5,
                        "points": 3
                    }
                ]
            }
        ],
        "synthese": {
            "question": "Expliquez comment la fiabilité du réseau SBEE influence le dimensionnement d'un micro-réseau hybride au Bénin.",
            "points": 5
        }
    },
    
    "TP5": {
        "titre": "Analyse technico-économique",
        "objectif": "Maîtriser l'analyse économique et optimiser un système",
        "duree": "2h30",
        "niveau": "Avancé",
        "icon": "💰",
        "etapes": [
            {
                "numero": 1,
                "titre": "Configuration du cas d'étude",
                "consigne": "Configurez une clinique (40 kW max) avec les paramètres économiques activés.",
                "type": "manipulation",
                "questions": [
                    {
                        "id": "tp5_q1",
                        "texte": "Quel est le CAPEX total estimé (en millions FCFA) ?",
                        "type": "number",
                        "reponse_attendue": None,
                        "tolerance": 100,
                        "points": 2
                    }
                ]
            },
            {
                "numero": 2,
                "titre": "Analyse du Payback",
                "consigne": "Observez le temps de retour sur investissement (Payback).",
                "type": "analyse",
                "questions": [
                    {
                        "id": "tp5_q2",
                        "texte": "Quel est le Payback obtenu (années) ?",
                        "type": "number",
                        "reponse_attendue": None,
                        "tolerance": 100,
                        "points": 3
                    },
                    {
                        "id": "tp5_q3",
                        "texte": "Le projet est-il rentable sur 25 ans ? Justifiez.",
                        "type": "textarea",
                        "mots_cles": ["oui", "non", "roi", "économie", "payback"],
                        "points": 4
                    }
                ]
            },
            {
                "numero": 3,
                "titre": "Optimisation",
                "consigne": "Utilisez la section 'Optimisation Système' pour voir les recommandations.",
                "type": "analyse",
                "questions": [
                    {
                        "id": "tp5_q4",
                        "texte": "Combien de panneaux 200W sont recommandés ?",
                        "type": "number",
                        "reponse_attendue": None,
                        "tolerance": 100,
                        "points": 2
                    },
                    {
                        "id": "tp5_q5",
                        "texte": "Quelle est la capacité batterie recommandée (kWh) ?",
                        "type": "number",
                        "reponse_attendue": None,
                        "tolerance": 100,
                        "points": 2
                    }
                ]
            },
            {
                "numero": 4,
                "titre": "Comparaison de scénarios",
                "consigne": "Créez deux scénarios (avec et sans diesel) et comparez-les.",
                "type": "simulation",
                "questions": [
                    {
                        "id": "tp5_q6",
                        "texte": "Quel scénario a le meilleur ROI ?",
                        "type": "text",
                        "mots_cles": [],
                        "points": 3
                    },
                    {
                        "id": "tp5_q7",
                        "texte": "Quel scénario recommanderiez-vous pour une clinique ? Pourquoi ?",
                        "type": "textarea",
                        "mots_cles": ["fiabilité", "continuité", "critique", "santé"],
                        "points": 5
                    }
                ]
            }
        ],
        "synthese": {
            "question": "Rédigez une recommandation professionnelle pour l'installation d'un micro-réseau hybride pour une clinique au Bénin, en justifiant vos choix techniques et économiques.",
            "points": 10
        }
    }
}

# ============================================================================
# FONCTIONS D'INITIALISATION
# ============================================================================

def init_tp_session_state():
    """Initialise les variables de session pour le mode pédagogique"""
    if 'tp_actif' not in st.session_state:
        st.session_state.tp_actif = None
    if 'tp_etape_courante' not in st.session_state:
        st.session_state.tp_etape_courante = 0
    if 'tp_reponses' not in st.session_state:
        st.session_state.tp_reponses = {}
    if 'tp_scores' not in st.session_state:
        st.session_state.tp_scores = {}
    if 'tp_etudiant' not in st.session_state:
        st.session_state.tp_etudiant = {"nom": "", "prenom": "", "matricule": ""}
    if 'tp_termine' not in st.session_state:
        st.session_state.tp_termine = False
    if 'pdf_tp_ready' not in st.session_state:
        st.session_state.pdf_tp_ready = False
    if 'pdf_tp_data' not in st.session_state:
        st.session_state.pdf_tp_data = None

# ============================================================================
# FONCTIONS D'AFFICHAGE
# ============================================================================

def afficher_liste_tps():
    """Affiche la liste des TPs disponibles"""
    st.markdown("### 📚 Travaux Pratiques Disponibles")
    
    # Informations étudiant
    st.markdown("#### 👤 Informations Étudiant")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.tp_etudiant["nom"] = st.text_input("Nom", st.session_state.tp_etudiant["nom"])
    with col2:
        st.session_state.tp_etudiant["prenom"] = st.text_input("Prénom", st.session_state.tp_etudiant["prenom"])
    with col3:
        st.session_state.tp_etudiant["matricule"] = st.text_input("Matricule", st.session_state.tp_etudiant["matricule"])
    
    st.markdown("---")
    
    # Liste des TPs
    for tp_id, tp_data in TRAVAUX_PRATIQUES.items():
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(145deg, #1e293b 0%, #334155 100%); border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; border-left: 4px solid #0ea5e9;">
                <h3 style="color: #f8fafc; margin: 0;">{tp_data['icon']} {tp_id} : {tp_data['titre']}</h3>
                <p style="color: #94a3b8; margin: 0.5rem 0;"><strong>Objectif :</strong> {tp_data['objectif']}</p>
                <p style="color: #94a3b8; margin: 0;">
                    <span style="background: rgba(14, 165, 233, 0.2); padding: 0.2rem 0.5rem; border-radius: 4px; margin-right: 0.5rem;">⏱️ {tp_data['duree']}</span>
                    <span style="background: rgba(34, 197, 94, 0.2); padding: 0.2rem 0.5rem; border-radius: 4px;">📊 {tp_data['niveau']}</span>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"▶️ Commencer {tp_id}", key=f"btn_start_{tp_id}", use_container_width=True):
                if st.session_state.tp_etudiant["nom"] and st.session_state.tp_etudiant["prenom"]:
                    st.session_state.tp_actif = tp_id
                    st.session_state.tp_etape_courante = 0
                    st.session_state.tp_reponses[tp_id] = {}
                    st.session_state.tp_termine = False
                    st.rerun()
                else:
                    st.warning("⚠️ Veuillez renseigner votre nom et prénom avant de commencer.")

def afficher_tp_actif():
    """Affiche le TP en cours"""
    tp_id = st.session_state.tp_actif
    tp_data = TRAVAUX_PRATIQUES[tp_id]
    etape_idx = st.session_state.tp_etape_courante
    
    # En-tête du TP
    col_header, col_quit = st.columns([4, 1])
    with col_header:
        st.markdown(f"### {tp_data['icon']} {tp_id} : {tp_data['titre']}")
    with col_quit:
        if st.button("❌ Quitter", key="btn_quit_tp"):
            st.session_state.tp_actif = None
            st.session_state.tp_etape_courante = 0
            st.rerun()
    
    # Barre de progression
    total_etapes = len(tp_data['etapes']) + 1  # +1 pour la synthèse
    progress = (etape_idx) / total_etapes
    st.progress(progress)
    st.caption(f"Progression : {etape_idx}/{total_etapes} étapes")
    
    st.markdown("---")
    
    # Afficher l'étape courante ou la synthèse
    if etape_idx < len(tp_data['etapes']):
        afficher_etape(tp_id, tp_data['etapes'][etape_idx])
    else:
        afficher_synthese(tp_id, tp_data)

def afficher_etape(tp_id, etape):
    """Affiche une étape du TP"""
    # Type d'étape avec icône
    type_icons = {
        "observation": "👁️",
        "manipulation": "🔧",
        "simulation": "▶️",
        "theorie": "📖",
        "analyse": "📊"
    }
    type_icon = type_icons.get(etape.get('type', ''), "📝")
    
    st.markdown(f"""
    <div style="background: rgba(14, 165, 233, 0.1); border-radius: 10px; padding: 1rem; border-left: 4px solid #0ea5e9; margin-bottom: 1rem;">
        <h4 style="color: #0ea5e9; margin: 0;">Étape {etape['numero']} : {etape['titre']} {type_icon}</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Consigne
    st.markdown("#### 📋 CONSIGNE :")
    st.info(etape['consigne'])
    
    # Questions
    st.markdown("#### ❓ QUESTIONS :")
    
    for question in etape['questions']:
        q_id = question['id']
        
        # Initialiser la réponse si nécessaire
        if q_id not in st.session_state.tp_reponses.get(tp_id, {}):
            if tp_id not in st.session_state.tp_reponses:
                st.session_state.tp_reponses[tp_id] = {}
            st.session_state.tp_reponses[tp_id][q_id] = ""
        
        st.markdown(f"**{q_id.upper().replace('_', ' ')}** : {question['texte']} *({question['points']} pts)*")
        
        # Type de question
        if question['type'] == 'number':
            st.session_state.tp_reponses[tp_id][q_id] = st.number_input(
                "Votre réponse", 
                key=f"input_{q_id}",
                value=float(st.session_state.tp_reponses[tp_id][q_id]) if st.session_state.tp_reponses[tp_id][q_id] != "" else 0.0,
                label_visibility="collapsed"
            )
        elif question['type'] == 'text':
            st.session_state.tp_reponses[tp_id][q_id] = st.text_input(
                "Votre réponse",
                value=st.session_state.tp_reponses[tp_id][q_id],
                key=f"input_{q_id}",
                label_visibility="collapsed"
            )
        elif question['type'] == 'textarea':
            st.session_state.tp_reponses[tp_id][q_id] = st.text_area(
                "Votre réponse",
                value=st.session_state.tp_reponses[tp_id][q_id],
                key=f"input_{q_id}",
                height=100,
                label_visibility="collapsed"
            )
        elif question['type'] == 'choice':
            options = ["-- Sélectionnez --"] + question['options']
            current_value = st.session_state.tp_reponses[tp_id][q_id]
            idx = options.index(current_value) if current_value in options else 0
            st.session_state.tp_reponses[tp_id][q_id] = st.selectbox(
                "Votre réponse",
                options,
                index=idx,
                key=f"input_{q_id}",
                label_visibility="collapsed"
            )
        
        st.markdown("")  # Espacement
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.session_state.tp_etape_courante > 0:
            if st.button("⬅️ Précédent", key="btn_prev", use_container_width=True):
                st.session_state.tp_etape_courante -= 1
                st.rerun()
    
    with col3:
        if st.button("Suivant ➡️", key="btn_next", type="primary", use_container_width=True):
            st.session_state.tp_etape_courante += 1
            st.rerun()

def afficher_synthese(tp_id, tp_data):
    """Affiche la question de synthèse finale"""
    st.markdown("""
    <div style="background: rgba(34, 197, 94, 0.1); border-radius: 10px; padding: 1rem; border-left: 4px solid #22c55e; margin-bottom: 1rem;">
        <h4 style="color: #22c55e; margin: 0;">🎯 Question de Synthèse</h4>
    </div>
    """, unsafe_allow_html=True)
    
    synthese = tp_data['synthese']
    q_id = f"{tp_id}_synthese"
    
    if q_id not in st.session_state.tp_reponses.get(tp_id, {}):
        st.session_state.tp_reponses[tp_id][q_id] = ""
    
    st.markdown(f"**{synthese['question']}** *({synthese['points']} pts)*")
    
    st.session_state.tp_reponses[tp_id][q_id] = st.text_area(
        "Votre réponse",
        value=st.session_state.tp_reponses[tp_id][q_id],
        height=200,
        key=f"input_{q_id}",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Boutons finaux
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Précédent", key="btn_prev_synthese", use_container_width=True):
            st.session_state.tp_etape_courante -= 1
            st.rerun()
    
    with col2:
        if st.button("✅ Valider mes réponses", key="btn_validate", type="primary", use_container_width=True):
            score = calculer_score(tp_id)
            st.session_state.tp_scores[tp_id] = score
            st.session_state.tp_termine = True
            st.rerun()
    
    with col3:
        if st.session_state.tp_termine:
            if st.button("📄 Générer compte-rendu PDF", key="btn_gen_pdf", use_container_width=True):
                st.session_state.pdf_tp_data = generer_compte_rendu_pdf(tp_id)
                st.session_state.pdf_tp_ready = True
    
    # Afficher le score et le bouton de téléchargement
    if st.session_state.tp_termine:
        score = st.session_state.tp_scores.get(tp_id, {})
        st.success(f"✅ TP validé ! Score : {score.get('obtenu', 0)}/{score.get('total', 0)} points ({score.get('pourcentage', 0):.0f}%)")
        
        if st.session_state.get('pdf_tp_ready', False) and st.session_state.get('pdf_tp_data'):
            st.download_button(
                "📥 Télécharger le compte-rendu PDF",
                data=st.session_state.pdf_tp_data,
                file_name=f"Compte_Rendu_{tp_id}_{st.session_state.tp_etudiant.get('matricule', 'etudiant')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

# ============================================================================
# FONCTIONS DE CALCUL
# ============================================================================

def calculer_score(tp_id):
    """Calcule le score pour un TP"""
    tp_data = TRAVAUX_PRATIQUES[tp_id]
    reponses = st.session_state.tp_reponses.get(tp_id, {})
    
    total_points = 0
    points_obtenus = 0
    details = []
    
    # Score des étapes
    for etape in tp_data['etapes']:
        for question in etape['questions']:
            q_id = question['id']
            points = question['points']
            total_points += points
            
            reponse = reponses.get(q_id, "")
            
            # Vérification selon le type
            if question['type'] == 'number':
                if question.get('reponse_attendue') is not None:
                    tolerance = question.get('tolerance', 0)
                    if abs(float(reponse or 0) - question['reponse_attendue']) <= tolerance:
                        points_obtenus += points
                        details.append((q_id, points, points, "Correct"))
                    else:
                        details.append((q_id, 0, points, f"Attendu: {question['reponse_attendue']}"))
                else:
                    # Réponse variable - donner les points si répondu
                    if reponse != "" and reponse != 0:
                        points_obtenus += points
                        details.append((q_id, points, points, "Répondu"))
                    else:
                        details.append((q_id, 0, points, "Non répondu"))
            
            elif question['type'] == 'choice':
                if question.get('reponse_attendue'):
                    if reponse == question['reponse_attendue']:
                        points_obtenus += points
                        details.append((q_id, points, points, "Correct"))
                    else:
                        details.append((q_id, 0, points, f"Attendu: {question['reponse_attendue']}"))
                else:
                    # Réponse variable
                    if reponse and reponse != "-- Sélectionnez --":
                        points_obtenus += points
                        details.append((q_id, points, points, "Répondu"))
                    else:
                        details.append((q_id, 0, points, "Non répondu"))
            
            elif question['type'] in ['text', 'textarea']:
                mots_cles = question.get('mots_cles', [])
                reponse_lower = str(reponse).lower()
                
                if mots_cles:
                    mots_trouves = sum(1 for mot in mots_cles if mot.lower() in reponse_lower)
                    ratio = mots_trouves / len(mots_cles)
                    pts = int(points * min(ratio * 1.5, 1))  # Bonus si plusieurs mots clés
                    points_obtenus += pts
                    details.append((q_id, pts, points, f"{mots_trouves}/{len(mots_cles)} mots-clés"))
                else:
                    # Pas de mots-clés, donner les points si répondu
                    if len(str(reponse).strip()) > 10:
                        points_obtenus += points
                        details.append((q_id, points, points, "Répondu"))
                    else:
                        details.append((q_id, 0, points, "Réponse trop courte"))
    
    # Score de la synthèse
    synthese = tp_data['synthese']
    total_points += synthese['points']
    synthese_reponse = reponses.get(f"{tp_id}_synthese", "")
    
    if len(str(synthese_reponse).strip()) > 50:
        points_obtenus += synthese['points']
        details.append(("synthese", synthese['points'], synthese['points'], "Répondu"))
    else:
        details.append(("synthese", 0, synthese['points'], "Réponse insuffisante"))
    
    return {
        'obtenu': points_obtenus,
        'total': total_points,
        'pourcentage': (points_obtenus / total_points * 100) if total_points > 0 else 0,
        'details': details
    }

# ============================================================================
# GÉNÉRATION PDF
# ============================================================================

def generer_compte_rendu_pdf(tp_id):
    """Génère le compte-rendu PDF du TP"""
    tp_data = TRAVAUX_PRATIQUES[tp_id]
    reponses = st.session_state.tp_reponses.get(tp_id, {})
    score = st.session_state.tp_scores.get(tp_id, calculer_score(tp_id))
    etudiant = st.session_state.tp_etudiant
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # En-tête
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(0, 80, 120)
    pdf.cell(0, 15, 'COMPTE-RENDU DE TRAVAUX PRATIQUES', 0, 1, 'C')
    
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(0, 100, 150)
    pdf.cell(0, 10, f'{tp_id} : {tp_data["titre"]}', 0, 1, 'C')
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f'Date : {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
    pdf.ln(5)
    
    # Informations étudiant
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, 'INFORMATIONS ETUDIANT', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(40, 6, 'Nom :', 0, 0)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(60, 6, etudiant.get('nom', ''), 0, 0)
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(40, 6, 'Prenom :', 0, 0)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, etudiant.get('prenom', ''), 0, 1)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(40, 6, 'Matricule :', 0, 0)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, etudiant.get('matricule', ''), 0, 1)
    pdf.ln(5)
    
    # Score
    pdf.set_fill_color(230, 245, 255)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, f'SCORE : {score["obtenu"]}/{score["total"]} points ({score["pourcentage"]:.0f}%)', 0, 1, 'C', True)
    pdf.ln(5)
    
    # Objectif du TP
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 80, 120)
    pdf.cell(0, 8, 'OBJECTIF DU TP', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 6, tp_data['objectif'])
    pdf.ln(5)
    
    # Réponses par étape
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 80, 120)
    pdf.cell(0, 8, 'REPONSES AUX QUESTIONS', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    for etape in tp_data['etapes']:
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 100, 150)
        pdf.cell(0, 7, f'Etape {etape["numero"]} : {etape["titre"]}', 0, 1)
        
        for question in etape['questions']:
            q_id = question['id']
            reponse = reponses.get(q_id, "Non repondu")
            
            pdf.set_font('Helvetica', 'I', 9)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 5, f'Q: {question["texte"]}')
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 5, f'R: {reponse}')
            pdf.ln(2)
        
        pdf.ln(3)
    
    # Synthèse
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(0, 80, 120)
    pdf.cell(0, 8, 'QUESTION DE SYNTHESE', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, f'Q: {tp_data["synthese"]["question"]}')
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(0, 0, 0)
    synthese_reponse = reponses.get(f"{tp_id}_synthese", "Non repondu")
    pdf.multi_cell(0, 5, f'R: {synthese_reponse}')
    
    # Pied de page
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 5, 'Jumeau Numerique - Plateforme de Simulation Micro-Reseau Hybride', 0, 1, 'C')
    pdf.cell(0, 5, 'Master en Technopedagogie et Didactique - Benin 2025', 0, 1, 'C')
    
    # Retourner les bytes du PDF correctement
    return pdf.output()

# ============================================================================
# FONCTION PRINCIPALE
# ============================================================================

def render_mode_pedagogique():
    """Fonction principale pour afficher le mode pédagogique"""
    init_tp_session_state()
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%); padding: 1rem 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;">
        <h2 style="color: white; margin: 0;">🎓 MODE PÉDAGOGIQUE</h2>
        <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0 0 0;">Travaux Pratiques Guidés - Master en Technopédagogie et Didactique</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.tp_actif is None:
        afficher_liste_tps()
    else:
        afficher_tp_actif()