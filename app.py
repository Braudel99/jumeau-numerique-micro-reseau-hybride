"""
PLATEFORME DE SIMULATION - MICRO-RÉSEAU HYBRIDE
===============================================
Version 4.0 - Design Optimisé
- Interface Glassmorphism moderne
- Header Sticky
- KPI Cards avec Sparklines
- Indicateur de progression
- Notifications Toast améliorées
- Mode Présentation
- Footer informatif
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import io
import time
import json
import base64

# Import des modèles
from models import (
    ModelePV, ParametresPV,
    ModeleCharge, ParametresCharge,
    ModeleBatterie, ParametresBatterie,
    ModeleSBEE, ParametresSBEE,
    ModeleDiesel, ParametresDiesel,
    GestionnaireEnergie, EtatSysteme, DecisionGestion
)
from models.analyse_economique import AnalyseurEconomique, ParametresEconomiques
from models.rapport_pdf import generer_rapport_pdf

# Import du module pédagogique
from mode_pedagogique import render_mode_pedagogique

# ============================================================================
# CONFIGURATION DE LA PAGE
# ============================================================================
st.set_page_config(
    page_title="Jumeau Numérique - Micro-Réseau Hybride",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# MASQUER LES ÉLÉMENTS STREAMLIT (Share, GitHub, etc.)
# ============================================================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stDecoration"] {display: none;}
    [data-testid="stStatusWidget"] {display: none;}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# INITIALISATION SESSION STATE
# ============================================================================
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = {}
if 'simulation_lancee' not in st.session_state:
    st.session_state.simulation_lancee = False
if 'resultats_simulation' not in st.session_state:
    st.session_state.resultats_simulation = None
if 'multi_jours_resultats' not in st.session_state:
    st.session_state.multi_jours_resultats = None
if 'pdf_eco_ready' not in st.session_state:
    st.session_state.pdf_eco_ready = False
    st.session_state.pdf_eco_data = None
if 'pdf_opt_ready' not in st.session_state:
    st.session_state.pdf_opt_ready = False
    st.session_state.pdf_opt_data = None
if 'pdf_tech_ready' not in st.session_state:
    st.session_state.pdf_tech_ready = False
    st.session_state.pdf_tech_data = None
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'
if 'mode_presentation' not in st.session_state:
    st.session_state.mode_presentation = False
if 'etape_progression' not in st.session_state:
    st.session_state.etape_progression = 1  # 1=Config, 2=Simulation, 3=Analyse, 4=Export

# ============================================================================
# CONFIGURATION DES THÈMES GLASSMORPHISM
# ============================================================================
THEMES = {
    'dark': {
        'bg_primary': '#0f172a',
        'bg_secondary': '#1e293b',
        'bg_card': 'linear-gradient(145deg, #1e293b 0%, #334155 100%)',
        'glass_bg': 'rgba(30, 41, 59, 0.7)',
        'glass_border': 'rgba(255, 255, 255, 0.1)',
        'glass_shadow': '0 8px 32px rgba(0, 0, 0, 0.3)',
        'text_primary': '#f8fafc',
        'text_secondary': '#94a3b8',
        'border': 'rgba(255,255,255,0.1)',
        'plot_bg': 'rgba(15, 23, 42, 0.8)',
        'paper_bg': 'rgba(0,0,0,0)',
        'grid_color': 'rgba(255,255,255,0.1)',
        'accent': '#0ea5e9',
        'success': '#22c55e',
        'warning': '#f59e0b',
        'danger': '#ef4444',
    },
    'light': {
        'bg_primary': '#f8fafc',
        'bg_secondary': '#e2e8f0',
        'bg_card': 'linear-gradient(145deg, #ffffff 0%, #f1f5f9 100%)',
        'glass_bg': 'rgba(255, 255, 255, 0.7)',
        'glass_border': 'rgba(0, 0, 0, 0.1)',
        'glass_shadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
        'text_primary': '#1e293b',
        'text_secondary': '#64748b',
        'border': 'rgba(0,0,0,0.1)',
        'plot_bg': 'rgba(255, 255, 255, 0.9)',
        'paper_bg': 'rgba(255,255,255,0)',
        'grid_color': 'rgba(0,0,0,0.1)',
        'accent': '#0ea5e9',
        'success': '#22c55e',
        'warning': '#f59e0b',
        'danger': '#ef4444',
    }
}

def get_theme():
    """Retourne le thème actuel"""
    return THEMES[st.session_state.theme]

# ============================================================================
# STYLES CSS GLASSMORPHISM + AMÉLIORATIONS
# ============================================================================
def apply_theme_css():
    theme = get_theme()
    is_dark = st.session_state.theme == 'dark'
    
    # CSS pour mode présentation (cache sidebar)
    presentation_css = """
        [data-testid="stSidebar"] { display: none; }
        .main .block-container { max-width: 100%; padding-left: 2rem; padding-right: 2rem; }
    """ if st.session_state.mode_presentation else ""
    
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
        
        /* ============ GLASSMORPHISM BASE ============ */
        .stApp {{
            background: {theme['bg_primary']};
            background-image: radial-gradient(at 20% 80%, rgba(14, 165, 233, 0.15) 0px, transparent 50%),
                              radial-gradient(at 80% 20%, rgba(139, 92, 246, 0.1) 0px, transparent 50%),
                              radial-gradient(at 50% 50%, rgba(34, 197, 94, 0.05) 0px, transparent 50%);
        }}
        
        .main .block-container {{
            background-color: transparent;
            padding-top: 1rem;
        }}
        
        /* ============ HEADER STICKY ============ */
        .sticky-header {{
            position: sticky;
            top: 0;
            z-index: 999;
            background: {theme['glass_bg']};
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid {theme['glass_border']};
            border-radius: 16px;
            padding: 1rem 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: {theme['glass_shadow']};
        }}
        
        /* ============ GLASS CARDS ============ */
        .glass-card {{
            background: {theme['glass_bg']};
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid {theme['glass_border']};
            border-radius: 16px;
            padding: 1.25rem;
            box-shadow: {theme['glass_shadow']};
            transition: all 0.3s ease;
        }}
        
        .glass-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
        }}
        
        /* ============ KPI CARDS AVEC SPARKLINES ============ */
        .kpi-card {{
            background: {theme['glass_bg']};
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid {theme['glass_border']};
            border-radius: 16px;
            padding: 1.25rem;
            box-shadow: {theme['glass_shadow']};
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            border-radius: 16px 16px 0 0;
        }}
        
        .kpi-card.pv::before {{ background: linear-gradient(90deg, #fbbf24, #f59e0b); }}
        .kpi-card.battery::before {{ background: linear-gradient(90deg, #0ea5e9, #0284c7); }}
        .kpi-card.sbee::before {{ background: linear-gradient(90deg, #22c55e, #16a34a); }}
        .kpi-card.diesel::before {{ background: linear-gradient(90deg, #f97316, #ea580c); }}
        .kpi-card.charge::before {{ background: linear-gradient(90deg, #ef4444, #dc2626); }}
        .kpi-card.coverage::before {{ background: linear-gradient(90deg, #8b5cf6, #7c3aed); }}
        
        .kpi-card:hover {{
            transform: translateY(-6px);
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4);
        }}
        
        .kpi-value {{
            font-size: 2rem;
            font-weight: 700;
            color: {theme['text_primary']};
            margin: 0.5rem 0;
        }}
        
        .kpi-label {{
            font-size: 0.85rem;
            color: {theme['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .kpi-sparkline {{
            height: 30px;
            margin-top: 0.5rem;
            opacity: 0.8;
        }}
        
        .kpi-delta {{
            font-size: 0.8rem;
            padding: 0.2rem 0.5rem;
            border-radius: 8px;
            display: inline-block;
            margin-top: 0.5rem;
        }}
        
        .kpi-delta.positive {{ background: rgba(34, 197, 94, 0.2); color: #22c55e; }}
        .kpi-delta.negative {{ background: rgba(239, 68, 68, 0.2); color: #ef4444; }}
        .kpi-delta.neutral {{ background: rgba(148, 163, 184, 0.2); color: #94a3b8; }}
        
        /* ============ PROGRESSION INDICATOR ============ */
        .progress-container {{
            background: {theme['glass_bg']};
            backdrop-filter: blur(20px);
            border: 1px solid {theme['glass_border']};
            border-radius: 12px;
            padding: 1rem 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: {theme['glass_shadow']};
        }}
        
        .progress-steps {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
        }}
        
        .progress-step {{
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
            position: relative;
            z-index: 2;
        }}
        
        .progress-step-icon {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            transition: all 0.3s ease;
        }}
        
        .progress-step.completed .progress-step-icon {{
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
            box-shadow: 0 4px 15px rgba(34, 197, 94, 0.4);
        }}
        
        .progress-step.active .progress-step-icon {{
            background: linear-gradient(135deg, #0ea5e9, #0284c7);
            color: white;
            box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4);
            animation: pulse-ring 2s infinite;
        }}
        
        .progress-step.pending .progress-step-icon {{
            background: {theme['bg_secondary']};
            color: {theme['text_secondary']};
            border: 2px dashed {theme['border']};
        }}
        
        .progress-step-label {{
            margin-top: 0.5rem;
            font-size: 0.75rem;
            color: {theme['text_secondary']};
            text-align: center;
        }}
        
        .progress-line {{
            position: absolute;
            top: 20px;
            left: 10%;
            right: 10%;
            height: 3px;
            background: {theme['bg_secondary']};
            z-index: 1;
        }}
        
        .progress-line-fill {{
            height: 100%;
            background: linear-gradient(90deg, #22c55e, #0ea5e9);
            border-radius: 3px;
            transition: width 0.5s ease;
        }}
        
        @keyframes pulse-ring {{
            0% {{ box-shadow: 0 0 0 0 rgba(14, 165, 233, 0.4); }}
            70% {{ box-shadow: 0 0 0 10px rgba(14, 165, 233, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(14, 165, 233, 0); }}
        }}
        
        /* ============ TOAST NOTIFICATIONS ============ */
        .toast-notification {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: {theme['glass_bg']};
            backdrop-filter: blur(20px);
            border: 1px solid {theme['glass_border']};
            border-radius: 12px;
            padding: 1rem 1.5rem;
            box-shadow: {theme['glass_shadow']};
            z-index: 9999;
            animation: slideIn 0.3s ease, fadeOut 0.3s ease 4.7s;
            max-width: 350px;
        }}
        
        .toast-notification.success {{ border-left: 4px solid #22c55e; }}
        .toast-notification.error {{ border-left: 4px solid #ef4444; }}
        .toast-notification.warning {{ border-left: 4px solid #f59e0b; }}
        .toast-notification.info {{ border-left: 4px solid #0ea5e9; }}
        
        @keyframes slideIn {{
            from {{ transform: translateX(100%); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}
        
        @keyframes fadeOut {{
            from {{ opacity: 1; }}
            to {{ opacity: 0; }}
        }}
        
        /* ============ TABS SPACE-AROUND ============ */
        .stTabs [data-baseweb="tab-list"] {{
            display: flex;
            justify-content: space-around;
            gap: 0;
            background: {theme['glass_bg']};
            backdrop-filter: blur(20px);
            border: 1px solid {theme['glass_border']};
            border-radius: 16px;
            padding: 8px 12px;
            box-shadow: {theme['glass_shadow']};
            width: 100%;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            background: transparent;
            border-radius: 12px;
            color: {theme['text_secondary']};
            padding: 12px 8px;
            margin: 0 4px;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            border: none;
            white-space: nowrap;
        }}
        
        .stTabs [data-baseweb="tab"]:hover {{
            background: rgba(14, 165, 233, 0.15);
            color: #0ea5e9;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
            color: white !important;
            box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4);
            transform: translateY(-2px);
        }}
        
        .stTabs [data-baseweb="tab-border"],
        .stTabs [data-baseweb="tab-highlight"] {{
            display: none;
        }}
        
        /* ============ FOOTER ============ */
        .footer {{
            background: {theme['glass_bg']};
            backdrop-filter: blur(20px);
            border: 1px solid {theme['glass_border']};
            border-radius: 16px;
            padding: 1.5rem;
            margin-top: 2rem;
            box-shadow: {theme['glass_shadow']};
        }}
        
        .footer-links {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}
        
        .footer-link {{
            color: {theme['text_secondary']};
            text-decoration: none;
            font-size: 0.9rem;
            transition: color 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .footer-link:hover {{
            color: {theme['accent']};
        }}
        
        .footer-copyright {{
            text-align: center;
            color: {theme['text_secondary']};
            font-size: 0.8rem;
        }}
        
        /* ============ SIDEBAR GLASSMORPHISM ============ */
        [data-testid="stSidebar"] {{
            background: {theme['glass_bg']} !important;
            backdrop-filter: blur(20px);
            border-right: 1px solid {theme['glass_border']};
        }}
        
        [data-testid="stSidebar"] > div:first-child {{
            background: transparent;
        }}
        
        [data-testid="stSidebar"] * {{
            color: {theme['text_primary']} !important;
        }}
        
        /* ============ INPUTS GLASSMORPHISM ============ */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > div {{
            background: {theme['glass_bg']} !important;
            backdrop-filter: blur(10px);
            border: 1px solid {theme['glass_border']} !important;
            border-radius: 10px !important;
            color: {theme['text_primary']} !important;
        }}
        
        /* ============ BUTTONS ============ */
        .stButton > button {{
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3);
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4);
        }}
        
        /* ============ EXPANDERS GLASSMORPHISM ============ */
        .streamlit-expanderHeader {{
            background: {theme['glass_bg']} !important;
            backdrop-filter: blur(10px);
            border: 1px solid {theme['glass_border']} !important;
            border-radius: 12px !important;
        }}
        
        .streamlit-expanderContent {{
            background: {theme['glass_bg']} !important;
            backdrop-filter: blur(10px);
            border: 1px solid {theme['glass_border']} !important;
            border-radius: 0 0 12px 12px !important;
        }}
        
        /* ============ METRICS ============ */
        [data-testid="stMetricValue"] {{
            color: {theme['text_primary']} !important;
        }}
        
        [data-testid="stMetricLabel"] {{
            color: {theme['text_secondary']} !important;
        }}
        
        /* ============ DATAFRAMES ============ */
        .stDataFrame {{
            background: {theme['glass_bg']};
            backdrop-filter: blur(10px);
            border-radius: 12px;
            overflow: hidden;
        }}
        
        /* ============ HIDE STREAMLIT BRANDING ============ */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        
        /* ============ MODE PRESENTATION ============ */
        {presentation_css}
        
        /* ============ ANIMATIONS ============ */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .animate-fade-in {{
            animation: fadeInUp 0.5s ease forwards;
        }}
    </style>
    """, unsafe_allow_html=True)

apply_theme_css()

# ============================================================================
# FONCTIONS POUR EXPORT PNG
# ============================================================================
def fig_to_png_bytes(fig, width=1200, height=600):
    """Convertit une figure Plotly en bytes PNG"""
    try:
        img_bytes = fig.to_image(format="png", width=width, height=height, scale=2)
        return img_bytes
    except Exception as e:
        return None

def render_download_button_for_chart(fig, filename, key, width=1200, height=500):
    """Affiche un bouton de téléchargement pour un graphique"""
    try:
        img_bytes = fig_to_png_bytes(fig, width, height)
        if img_bytes:
            st.download_button(
                label="📥 PNG",
                data=img_bytes,
                file_name=f"{filename}.png",
                mime="image/png",
                key=key,
                help="Télécharger le graphique en PNG"
            )
        else:
            html_bytes = fig.to_html().encode()
            st.download_button(
                label="📥 HTML",
                data=html_bytes,
                file_name=f"{filename}.html",
                mime="text/html",
                key=key,
                help="Télécharger le graphique en HTML"
            )
    except Exception as e:
        st.caption(f"Export non disponible")

def get_plot_colors():
    """Retourne les couleurs pour les graphiques selon le thème"""
    theme = get_theme()
    return {
        'plot_bg': theme['plot_bg'],
        'paper_bg': theme['paper_bg'],
        'font_color': theme['text_primary'],
        'grid_color': theme['grid_color']
    }

# ============================================================================
# NOUVELLES FONCTIONS - HEADER STICKY
# ============================================================================
def render_header_sticky():
    """Affiche l'en-tête sticky avec effet glassmorphism"""
    theme = get_theme()
    current_time = datetime.now().strftime("%H:%M")
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    # Boutons mode présentation et thème
    col_pres, col_theme_btn = st.columns([1, 1])
    with col_pres:
        if st.button("🖥️ Mode Présentation" if not st.session_state.mode_presentation else "📱 Mode Normal", 
                     key="btn_presentation", use_container_width=True):
            st.session_state.mode_presentation = not st.session_state.mode_presentation
            st.rerun()
    with col_theme_btn:
        theme_icon = "☀️ Mode Clair" if st.session_state.theme == 'dark' else "🌙 Mode Sombre"
        if st.button(theme_icon, key="btn_theme", use_container_width=True):
            st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
            st.rerun()
    
    # Header principal
    st.markdown(f"""
    <div class="sticky-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="font-size: 2.5rem;">⚡</div>
                <div>
                    <h1 style="margin: 0; font-size: 1.8rem; font-weight: 700; background: linear-gradient(135deg, #0ea5e9, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                        Jumeau Numérique
                    </h1>
                    <p style="margin: 0; font-size: 0.9rem; color: {theme['text_secondary']};">
                        Simulation & Gestion Micro-Réseau Hybride
                    </p>
                </div>
            </div>
            <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
                <div style="background: rgba(34, 197, 94, 0.15); padding: 0.5rem 1rem; border-radius: 25px; display: flex; align-items: center; gap: 0.5rem; border: 1px solid rgba(34, 197, 94, 0.3);">
                    <span style="width: 8px; height: 8px; background: #22c55e; border-radius: 50%; animation: pulse-ring 2s infinite;"></span>
                    <span style="color: #22c55e; font-size: 0.85rem; font-weight: 500;">Système Actif</span>
                </div>
                <div style="background: rgba(14, 165, 233, 0.15); padding: 0.5rem 1rem; border-radius: 25px; border: 1px solid rgba(14, 165, 233, 0.3);">
                    <span style="color: #0ea5e9; font-size: 0.85rem;">📍 Bénin</span>
                </div>
                <div style="background: rgba(139, 92, 246, 0.15); padding: 0.5rem 1rem; border-radius: 25px; border: 1px solid rgba(139, 92, 246, 0.3);">
                    <span style="color: #8b5cf6; font-size: 0.85rem;">📅 {current_date}</span>
                </div>
                <div style="background: rgba(148, 163, 184, 0.15); padding: 0.5rem 1rem; border-radius: 25px; border: 1px solid rgba(148, 163, 184, 0.3);">
                    <span style="color: {theme['text_secondary']}; font-size: 0.85rem;">🕐 {current_time}</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# INDICATEUR DE PROGRESSION
# ============================================================================
def render_progress_indicator():
    """Affiche l'indicateur de progression du workflow"""
    theme = get_theme()
    etape = st.session_state.etape_progression
    
    etapes = [
        {"num": 1, "label": "Configuration", "icon": "⚙️"},
        {"num": 2, "label": "Simulation", "icon": "▶️"},
        {"num": 3, "label": "Analyse", "icon": "📊"},
        {"num": 4, "label": "Export", "icon": "📥"}
    ]
    
    progress_pct = ((etape - 1) / (len(etapes) - 1)) * 100 if etape > 1 else 0
    
    steps_html = ""
    for e in etapes:
        if e["num"] < etape:
            status = "completed"
            icon_display = "✅"
        elif e["num"] == etape:
            status = "active"
            icon_display = e["icon"]
        else:
            status = "pending"
            icon_display = e["icon"]
        
        steps_html += f'<div class="progress-step {status}"><div class="progress-step-icon">{icon_display}</div><div class="progress-step-label">{e["label"]}</div></div>'
    
    html_content = f'''<div class="progress-container"><div class="progress-steps"><div class="progress-line"><div class="progress-line-fill" style="width: {progress_pct}%;"></div></div>{steps_html}</div></div>'''
    
    st.markdown(html_content, unsafe_allow_html=True)

# ============================================================================
# KPI CARDS AVEC SPARKLINES
# ============================================================================
def generate_sparkline_svg(values, color="#0ea5e9", width=100, height=30):
    """Génère un SVG sparkline simple"""
    if not values or len(values) < 2:
        return ""
    
    # Filtrer les valeurs None ou non numériques
    clean_values = [v for v in values if v is not None and isinstance(v, (int, float))]
    if len(clean_values) < 2:
        return ""
    
    min_val = min(clean_values)
    max_val = max(clean_values)
    range_val = max_val - min_val if max_val != min_val else 1
    
    points = []
    for i, v in enumerate(clean_values):
        x = (i / (len(clean_values) - 1)) * width
        y = height - ((v - min_val) / range_val) * height
        points.append(f"{x:.1f},{y:.1f}")
    
    path = "M" + " L".join(points)
    color_id = color.replace('#', '')
    
    svg = f'<svg width="{width}" height="{height}" style="overflow:visible;"><defs><linearGradient id="grad_{color_id}" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" style="stop-color:{color};stop-opacity:0.3"/><stop offset="100%" style="stop-color:{color};stop-opacity:0"/></linearGradient></defs><path d="{path} L{width},{height} L0,{height} Z" fill="url(#grad_{color_id})"/><path d="{path}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    return svg

def render_kpi_cards_with_sparklines(data):
    """Affiche les KPI cards avec sparklines"""
    theme = get_theme()
    cols = st.columns(len(data))
    
    for i, item in enumerate(data):
        with cols[i]:
            card_type = item.get('type', 'default')
            
            # Générer sparkline si données disponibles
            sparkline_html = ""
            if 'sparkline_data' in item and item['sparkline_data']:
                color_map = {
                    'pv': '#fbbf24', 'battery': '#0ea5e9', 'sbee': '#22c55e',
                    'diesel': '#f97316', 'charge': '#ef4444', 'coverage': '#8b5cf6'
                }
                color = color_map.get(card_type, '#0ea5e9')
                svg = generate_sparkline_svg(item["sparkline_data"], color)
                if svg:
                    sparkline_html = f'<div class="kpi-sparkline">{svg}</div>'
            
            # Générer delta si disponible
            delta_html = ""
            if item.get('delta'):
                delta_type = item.get('delta_type', 'neutral')
                delta_html = f'<span class="kpi-delta {delta_type}">{item["delta"]}</span>'
            
            # Construire le HTML de la carte sur une seule ligne
            card_html = f'<div class="kpi-card {card_type}"><div style="font-size:1.5rem;margin-bottom:0.25rem;">{item["icon"]}</div><div class="kpi-value">{item["value"]}</div><div class="kpi-label">{item["label"]}</div>{sparkline_html}{delta_html}</div>'
            
            st.markdown(card_html, unsafe_allow_html=True)

# ============================================================================
# TOAST NOTIFICATIONS
# ============================================================================
def show_toast(message, toast_type="info", duration=5):
    """Affiche une notification toast"""
    icons = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
    icon = icons.get(toast_type, "ℹ️")
    
    st.markdown(f"""
    <div class="toast-notification {toast_type}" id="toast_{int(time.time())}">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.2rem;">{icon}</span>
            <span>{message}</span>
        </div>
    </div>
    <script>
        setTimeout(function() {{
            var toast = document.querySelector('.toast-notification');
            if (toast) toast.style.display = 'none';
        }}, {duration * 1000});
    </script>
    """, unsafe_allow_html=True)

# ============================================================================
# FOOTER AMÉLIORÉ
# ============================================================================
def render_footer():
    """Affiche le footer avec liens utiles"""
    theme = get_theme()
    current_year = datetime.now().year
    
    st.markdown(f"""
    <div class="footer">
        <div class="footer-links">
            <a href="#" class="footer-link">
                <span>📖</span> Documentation
            </a>
            <a href="#" class="footer-link">
                <span>🐛</span> Signaler un bug
            </a>
            <a href="#" class="footer-link">
                <span>💡</span> Suggestions
            </a>
            <a href="#" class="footer-link">
                <span>📧</span> Contact
            </a>
            <a href="#" class="footer-link">
                <span>🎓</span> Tutoriels
            </a>
        </div>
        <div class="footer-copyright">
            <p style="margin: 0;">
                🌍 <strong>Jumeau Numérique</strong> - Plateforme de Simulation Micro-Réseau Hybride PV - SBEE- Diesel
            </p>
            <p style="margin: 0.5rem 0 0 0;">
                Version 4.0 | Master en Technopédagogie et Didactique | Bénin {current_year}
            </p>
            <p style="margin: 0.25rem 0 0 0; font-size: 0.75rem; opacity: 0.7;">
                Développé avec Wilson BARNOR pour l'éducation et la transition énergétique
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# ANCIENNES FONCTIONS (pour compatibilité)
# ============================================================================
def render_header():
    """Fonction de compatibilité - utilise le nouveau header sticky"""
    render_header_sticky()

def render_alert(message, alert_type="info"):
    """Affiche une alerte stylisée avec effet glassmorphism"""
    theme = get_theme()
    colors = {
        "success": ("#22c55e", "rgba(34, 197, 94, 0.15)"),
        "warning": ("#f59e0b", "rgba(245, 158, 11, 0.15)"),
        "danger": ("#ef4444", "rgba(239, 68, 68, 0.15)"),
        "info": ("#0ea5e9", "rgba(14, 165, 233, 0.15)")
    }
    icons = {"success": "✅", "warning": "⚠️", "danger": "🚨", "info": "ℹ️"}
    
    color, bg = colors.get(alert_type, colors["info"])
    icon = icons.get(alert_type, "ℹ️")
    
    st.markdown(f"""
    <div class="glass-card" style="border-left: 4px solid {color}; background: {bg}; backdrop-filter: blur(10px); padding: 1rem; margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-size: 1.3rem;">{icon}</span>
            <span style="color: {color}; font-size: 0.95rem; font-weight: 500;">{message}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_kpi_dashboard(data):
    """Affiche le dashboard KPI avec sparklines (version améliorée)"""
    render_kpi_cards_with_sparklines(data)

def validate_configuration(config):
    """Valide la configuration et retourne les alertes"""
    alerts = []
    
    if config['ptot'] > 0:
        ratio = config['ptot'] / (config['puissance_max_charge'] * 1000)
        if ratio < 0.5:
            alerts.append(("warning", f"PV sous-dimensionné ({ratio:.0%})"))
        elif ratio > 2:
            alerts.append(("warning", f"PV surdimensionné ({ratio:.0%})"))
        else:
            alerts.append(("success", f"PV bien dimensionné ({ratio:.0%})"))
    
    autonomie = config['energie_bat_max'] / config['puissance_max_charge'] if config['puissance_max_charge'] > 0 else 0
    if autonomie < 2:
        alerts.append(("warning", f"Autonomie faible ({autonomie:.1f}h)"))
    else:
        alerts.append(("success", f"Autonomie OK ({autonomie:.1f}h)"))
    
    return alerts

def export_to_excel(resultats, config):
    """Exporte les résultats vers Excel"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Configuration
        config_df = pd.DataFrame([
            {'Paramètre': 'Type charge', 'Valeur': config['type_charge']},
            {'Paramètre': 'P. max charge (kW)', 'Valeur': config['puissance_max_charge']},
            {'Paramètre': 'PV (kWc)', 'Valeur': config['ptot'] / 1000},
            {'Paramètre': 'Batterie (kWh)', 'Valeur': config['energie_bat_max']},
            {'Paramètre': 'Type batterie', 'Valeur': config['tbat']},
            {'Paramètre': 'SBEE', 'Valeur': 'Oui' if config['sbee_dispo'] else 'Non'},
            {'Paramètre': 'Diesel', 'Valeur': 'Oui' if config['diesel_on'] else 'Non'},
        ])
        config_df.to_excel(writer, sheet_name='Configuration', index=False)
        
        # Données horaires
        if 'hrs' in resultats:
            horaire_df = pd.DataFrame({
                'Heure': resultats['hrs'],
                'PV (kW)': resultats['ppv'],
                'Charge (kW)': resultats['pch'],
                'PV→Charge (kW)': resultats['ppv_vers_charge'],
                'Batterie (kW)': resultats['pbat_vers_charge'],
                'SBEE (kW)': resultats['psbee'],
                'Diesel (kW)': resultats['pdiesel'],
                'SOC (%)': resultats['soc_24h'],
                'Déficit (kW)': resultats['deficits']
            })
            horaire_df.to_excel(writer, sheet_name='Données Horaires', index=False)
        
        # Résumé
        resume_df = pd.DataFrame([
            {'Indicateur': 'PV total (kWh)', 'Valeur': resultats.get('epv', 0)},
            {'Indicateur': 'Batterie (kWh)', 'Valeur': resultats.get('ebat', 0)},
            {'Indicateur': 'SBEE (kWh)', 'Valeur': resultats.get('esbee', 0)},
            {'Indicateur': 'Diesel (kWh)', 'Valeur': resultats.get('ediesel', 0)},
            {'Indicateur': 'Charge (kWh)', 'Valeur': resultats.get('ech', 0)},
            {'Indicateur': 'Couverture (%)', 'Valeur': resultats.get('couverture', 0)},
        ])
        resume_df.to_excel(writer, sheet_name='Résumé', index=False)
        
        # Multi-jours
        if 'jours' in resultats:
            jours_df = pd.DataFrame([{
                'Jour': r['jour'], 'PV': r['epv'], 'SBEE': r['esbee'], 
                'Charge': r['ech'], 'Couverture': r['couverture']
            } for r in resultats['jours']])
            jours_df.to_excel(writer, sheet_name='Multi-Jours', index=False)
    
    return output.getvalue()

# ============================================================================
# EN-TÊTE
# ============================================================================
render_header()

# ============================================================================
# INDICATEUR DE PROGRESSION
# ============================================================================
render_progress_indicator()

# ============================================================================
# SIDEBAR - CONFIGURATION COMPLÈTE
# ============================================================================
with st.sidebar:
    st.markdown('<div style="text-align: center; padding: 1rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);"><h2 style="color: #f8fafc; font-size: 1.2rem; margin: 0;">⚙️ Configuration</h2></div>', unsafe_allow_html=True)
    
    # === PRESETS ===
    st.markdown("#### 📋 Presets")
    preset = st.selectbox("Config", ["Personnalisé", "🏥 Clinique", "🏨 Hôtel", "🏭 Industrie", "🏠 Villa"], label_visibility="collapsed")
    
    presets_config = {
        "🏥 Clinique": {'type': 'clinique', 'pmax': 40.0, 'nb200': 15},
        "🏨 Hôtel": {'type': 'hotel', 'pmax': 60.0, 'nb200': 25},
        "🏭 Industrie": {'type': 'industrie', 'pmax': 100.0, 'nb200': 40},
        "🏠 Villa": {'type': 'residence_villa', 'pmax': 15.0, 'nb200': 8},
    }
    
    if preset in presets_config:
        default_type = presets_config[preset]['type']
        default_pmax = presets_config[preset]['pmax']
        default_nb200 = presets_config[preset]['nb200']
    else:
        default_type, default_pmax, default_nb200 = 'clinique', 40.0, 15
    
    # === 1. CHARGE ===
    st.markdown("---")
    st.markdown("#### ⚡ 1. Charge")
    type_charge = st.selectbox("Type", ['clinique', 'hopital', 'centre_commercial', 'lycee_universite', 'residence_villa', 'hotel', 'industrie'],
                               format_func=lambda x: ModeleCharge.PROFILS_TYPES[x]['description'],
                               index=['clinique', 'hopital', 'centre_commercial', 'lycee_universite', 'residence_villa', 'hotel', 'industrie'].index(default_type))
    puissance_max_charge = st.number_input("P. Max (kW)", 5.0, 500.0, default_pmax, 5.0)
    puissance_min_charge = st.number_input("P. Min (kW)", 1.0, 100.0, float(puissance_max_charge*0.3), 1.0)
    facteur_simultaneite = st.slider("Simultanéité", 0.5, 1.0, 0.85, 0.05)
    
    # === 2. PV ===
    st.markdown("---")
    st.markdown("#### 🌞 2. Système PV")
    pv_actif = st.checkbox("PV Activé", True)
    
    col_pv1, col_pv2 = st.columns(2)
    with col_pv1:
        type_techno = st.selectbox("Techno", ['monocristallin', 'polycristallin'])
    with col_pv2:
        tension_pv = st.selectbox("Tension (V)", [12, 24, 48], index=2)
    
    st.markdown("**Panneaux:**")
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        nb_100 = st.number_input("100W", 0, 100, 0, key="nb100")
        nb_130 = st.number_input("130W", 0, 100, 0, key="nb130")
    with col_p2:
        nb_150 = st.number_input("150W", 0, 100, 10, key="nb150")
        nb_200 = st.number_input("200W", 0, 100, default_nb200, key="nb200")
    with col_p3:
        nb_300 = st.number_input("300W", 0, 100, 0, key="nb300")
        nb_500 = st.number_input("500W", 0, 100, 0, key="nb500")
    
    ptot = nb_100*100 + nb_130*130 + nb_150*150 + nb_200*200 + nb_300*300 + nb_500*500
    surf = nb_100*0.7 + nb_130*0.9 + nb_150*1.0 + nb_200*1.3 + nb_300*1.9 + nb_500*3.2
    st.success(f"**{ptot/1000:.2f} kWc** | {surf:.0f} m²")
    
    with st.expander("⚙️ Pertes & Onduleur"):
        pcab = st.slider("Câbles (%)", 0.0, 10.0, 3.0, 0.5) / 100
        psal = st.slider("Salissure (%)", 0.0, 15.0, 5.0, 1.0) / 100
        eond = st.slider("Rendement Onduleur (%)", 80.0, 99.0, 96.0, 1.0) / 100
        empt = st.slider("Rendement MPPT (%)", 90.0, 99.0, 98.0, 1.0) / 100
        st.markdown("---")
        pond_rec = puissance_max_charge * 1.2
        st.info(f"💡 Onduleur recommandé: {pond_rec:.1f} kW")
        mode_ond = st.radio("Mode Onduleur", ["Auto", "Manuel"], horizontal=True)
        if mode_ond == "Manuel":
            pond = st.number_input("Puissance Onduleur (kW)", 1.0, 500.0, pond_rec, 1.0)
        else:
            pond = pond_rec
    
    # === 3. MÉTÉO (après PV) ===
    st.markdown("---")
    st.markdown("#### 🌤️ 3. Météo")
    irr_journaliere = st.slider("Irradiation (kWh/m²/j)", 3.0, 7.0, 5.5, 0.1, help="Bénin: 3.9-6.2")
    temp = st.slider("Température (°C)", 15, 45, 30)
    
    # === 4. BATTERIE ===
    st.markdown("---")
    st.markdown("#### 🔋 4. Batterie")
    vbat = tension_pv
    st.info(f"Tension: {vbat}V (= PV)")
    
    col_bat1, col_bat2 = st.columns(2)
    with col_bat1:
        tbat = st.selectbox("Type Bat.", ['Lithium-ion', 'Plomb-acide'])
    with col_bat2:
        mode_bat = st.radio("Mode", ["Auto", "Manuel"], horizontal=True, key="mode_bat")
    
    if mode_bat == "Auto":
        ha = st.slider("Autonomie (h)", 1, 48, 6)
        dod = 0.8 if tbat == 'Lithium-ion' else 0.5
        cap = (puissance_max_charge * 1000 * ha) / (vbat * dod)
    else:
        cap = st.number_input("Capacité (Ah)", 50, 10000, 500, 50)
        dod = st.slider("DoD (%)", 30, 90, 80 if tbat == 'Lithium-ion' else 50) / 100
    
    energie_bat_max = (cap * vbat) / 1000
    st.success(f"**{cap:.0f} Ah** | {energie_bat_max:.1f} kWh")
    
    # === 5. SBEE ===
    st.markdown("---")
    st.markdown("#### 🔌 5. Réseau SBEE")
    sbee_dispo = st.checkbox("SBEE Connecté", True)
    scenario_sbee = st.selectbox("Fiabilité", ['stable', 'normal', 'instable'], index=1,
                                  format_func=lambda x: {'stable': '🟢 Stable (95%)', 'normal': '🟡 Normal (80%)', 'instable': '🔴 Instable (60%)'}[x])
    psbee = ModeleCharge.PROFILS_TYPES[type_charge]['puissance_sbee_recommandee']
    tarif_kwh = st.number_input("Tarif (FCFA/kWh)", 50, 200, 100, 5)
    mode_coupures_sbee = "automatique"
    coupures_manuelles = []
    
    # === 6. DIESEL ===
    st.markdown("---")
    st.markdown("#### 🛢️ 6. Diesel (ATS)")
    diesel_on = st.checkbox("Diesel Activé", False)
    pdies = ModeleCharge.PROFILS_TYPES[type_charge]['puissance_diesel_recommandee']
    
    if diesel_on:
        pdies = st.number_input("Puissance (kW)", 5, 500, pdies, 5)
        charge_min_pct = st.slider("Charge Min (%)", 20, 50, 30, 5)
        with st.expander("⚙️ Paramètres Diesel"):
            temps_demarrage = st.number_input("Temps démarrage (s)", 5, 60, 15, 5)
            consommation_spe = st.number_input("Conso. (L/kWh)", 0.20, 0.40, 0.28, 0.01)
            cout_carburant = st.number_input("Coût (FCFA/L)", 400, 1200, 750, 50)
            avec_refroidissement = st.checkbox("Refroidissement", False)
    else:
        charge_min_pct = 30
        temps_demarrage = 15
        consommation_spe = 0.28
        cout_carburant = 750
        avec_refroidissement = False
    
    # === 7. ÉCONOMIQUE ===
    st.markdown("---")
    st.markdown("#### 💰 7. Analyse Économique")
    analyse_eco_active = st.checkbox("Activer analyse", False)
    
    if analyse_eco_active:
        with st.expander("💵 Paramètres CAPEX/OPEX"):
            cout_pv_wc = st.number_input("PV (FCFA/Wc)", 100, 500, 300, 10)
            cout_bat_lithium = st.number_input("Bat. Li-ion (FCFA/kWh)", 100000, 400000, 200000, 10000)
            cout_bat_plomb = st.number_input("Bat. Plomb (FCFA/kWh)", 50000, 200000, 90000, 5000)
            cout_onduleur = st.number_input("Onduleur (FCFA/kW)", 50000, 400000, 240000, 5000)
            cout_mppt = st.number_input("MPPT (FCFA)", 200000, 800000, 575000, 10000)
            cout_diesel_kw = st.number_input("Diesel (FCFA/kW)", 100000, 600000, 200000, 10000)
            taux_installation = st.slider("Installation (%)", 5, 25, 15, 1)
            prix_diesel_litre = st.number_input("Diesel (FCFA/L)", 500, 1500, 675, 10)
            conso_diesel_l_kwh = 0.28
            tarif_sbee = st.number_input("SBEE (FCFA/kWh)", 50, 200, 115, 5)
            taux_maint_pv = st.slider("Maintenance (%/an)", 0.5, 3.0, 1.0, 0.1) / 100
            duree_vie_projet = st.number_input("Durée (ans)", 10, 30, 25, 1)
            taux_actualisation = st.slider("Actualisation (%)", 3, 15, 8, 1) / 100
            taux_inflation = st.slider("Inflation (%)", 0, 10, 3, 1) / 100
    else:
        cout_pv_wc, cout_bat_lithium, cout_bat_plomb = 300, 200000, 90000
        cout_onduleur, cout_mppt, cout_diesel_kw = 240000, 575000, 200000
        taux_installation, prix_diesel_litre, conso_diesel_l_kwh = 15, 675, 0.28
        tarif_sbee, taux_maint_pv = 115, 0.01
        duree_vie_projet, taux_actualisation, taux_inflation = 25, 0.08, 0.03

# Configuration complète
config = {
    'type_charge': type_charge, 'puissance_max_charge': puissance_max_charge,
    'puissance_min_charge': puissance_min_charge, 'facteur_simultaneite': facteur_simultaneite,
    'pv_actif': pv_actif, 'type_techno': type_techno, 'tension_pv': tension_pv,
    'ptot': ptot, 'surf': surf, 'pcab': pcab, 'psal': psal, 'eond': eond, 'empt': empt, 'pond': pond,
    'vbat': vbat, 'tbat': tbat, 'cap': cap, 'dod': dod, 'energie_bat_max': energie_bat_max,
    'sbee_dispo': sbee_dispo, 'scenario_sbee': scenario_sbee, 'psbee': psbee, 'tarif_kwh': tarif_kwh,
    'mode_coupures_sbee': mode_coupures_sbee, 'coupures_manuelles': coupures_manuelles,
    'diesel_on': diesel_on, 'pdies': pdies, 'charge_min_pct': charge_min_pct,
    'temps_demarrage': temps_demarrage, 'consommation_spe': consommation_spe,
    'cout_carburant': cout_carburant, 'avec_refroidissement': avec_refroidissement,
    'irr_journaliere': irr_journaliere, 'temp': temp, 'analyse_eco_active': analyse_eco_active,
    'cout_pv_wc': cout_pv_wc, 'cout_bat_lithium': cout_bat_lithium, 'cout_bat_plomb': cout_bat_plomb,
    'cout_onduleur': cout_onduleur, 'cout_mppt': cout_mppt, 'cout_diesel_kw': cout_diesel_kw,
    'taux_installation': taux_installation, 'prix_diesel_litre': prix_diesel_litre,
    'tarif_sbee': tarif_sbee, 'taux_maint_pv': taux_maint_pv, 'duree_vie_projet': duree_vie_projet,
    'taux_actualisation': taux_actualisation, 'taux_inflation': taux_inflation
}

# ============================================================================
# VALIDATION EN TEMPS RÉEL
# ============================================================================
st.markdown("### ✅ Validation Configuration")
validation_alerts = validate_configuration(config)

cols_valid = st.columns(len(validation_alerts))
for i, (alert_type, message) in enumerate(validation_alerts):
    with cols_valid[i]:
        colors = {'success': '#22c55e', 'warning': '#fbbf24', 'danger': '#ef4444'}
        icons = {'success': '✅', 'warning': '⚠️', 'danger': '🚨'}
        st.markdown(f'<div style="background: {colors[alert_type]}20; padding: 0.5rem; border-radius: 8px; border-left: 3px solid {colors[alert_type]};"><span style="color: {colors[alert_type]}; font-size: 0.85rem;">{icons[alert_type]} {message}</span></div>', unsafe_allow_html=True)

# ============================================================================
# FONCTION DE SIMULATION
# ============================================================================
def run_simulation_24h(config):
    """Exécute une simulation 24h complète"""
    mpv = ModelePV(ParametresPV(config['ptot'], config['surf'], config['type_techno'], None, -0.0045, 45.0, config['pcab'], config['eond'], config['psal'], config['empt']))
    mch = ModeleCharge(ParametresCharge(config['type_charge'], config['puissance_max_charge'], config['puissance_min_charge'], config['facteur_simultaneite']))
    mbat = ModeleBatterie(ParametresBatterie(config['vbat'], config['tbat'], config['cap'], config['dod']))
    msbee = ModeleSBEE(ParametresSBEE(puissance_max=config['psbee'], disponible=config['sbee_dispo'], tarif_base=config['tarif_kwh'], tarif_pointe=config['tarif_kwh'], tarif_hors_pointe=config['tarif_kwh'], scenario=config['scenario_sbee'], mode_coupures=config['mode_coupures_sbee'], coupures_manuelles=config['coupures_manuelles']))
    mdies = ModeleDiesel(ParametresDiesel(puissance_nominale=config['pdies'], puissance_min_pct=config['charge_min_pct']/100, temps_demarrage=config['temps_demarrage'], temps_refroidissement=5.0, consommation_specifique=config['consommation_spe'], cout_carburant=config['cout_carburant'], actif=config['diesel_on'], avec_refroidissement=config['avec_refroidissement']))
    gestionnaire = GestionnaireEnergie()
    
    irr24 = ModelePV.generer_profil_irradiation_horaire(config['irr_journaliere'])
    tmp24 = ModelePV.get_profil_temperature_type()
    profil_sbee = msbee.get_profil_disponibilite_numerique_24h()
    hrs = list(range(24))
    
    ppv = [mpv.puissance_instantanee(irr24[h], tmp24[h])['puissance_kW'] for h in hrs]
    pch = [mch.puissance_instantanee(h, 0.05) for h in hrs]
    
    soc_24h, pbat_charge_24h, pbat_decharge_24h = [], [], []
    ppv_vers_charge_24h, pbat_vers_charge_24h = [], []
    psbee_24h, pdiesel_24h = [], []
    
    soc_actuel = 0.5
    soc_min = 1 - config['dod']
    energie_bat_max = config['energie_bat_max']
    puissance_charge_max_bat = (config['cap'] * config['vbat'] / 2000)
    
    for h in hrs:
        pv_h = ppv[h] if config['pv_actif'] else 0
        charge_h = pch[h]
        
        espace_dispo = energie_bat_max * (1 - soc_actuel)
        energie_pv_bat = min(pv_h, puissance_charge_max_bat, espace_dispo)
        
        if energie_pv_bat > 0 and soc_actuel < 1.0:
            soc_actuel += (energie_pv_bat * 0.95) / energie_bat_max
            soc_actuel = min(soc_actuel, 1.0)
            pbat_charge_24h.append(energie_pv_bat)
        else:
            pbat_charge_24h.append(0)
        
        pv_restant = pv_h - energie_pv_bat
        pv_vers_charge = min(pv_restant, charge_h)
        ppv_vers_charge_24h.append(pv_vers_charge)
        
        deficit = charge_h - pv_vers_charge
        if deficit > 0.01:
            energie_dispo = max(0, (soc_actuel - soc_min) * energie_bat_max * 0.95)
            decharge = min(deficit, puissance_charge_max_bat, energie_dispo)
            if decharge > 0:
                soc_actuel -= decharge / (energie_bat_max * 0.95)
                soc_actuel = max(soc_actuel, soc_min)
            pbat_decharge_24h.append(decharge)
            pbat_vers_charge_24h.append(decharge)
        else:
            pbat_decharge_24h.append(0)
            pbat_vers_charge_24h.append(0)
        
        soc_24h.append(soc_actuel * 100)
        
        fourni = pv_vers_charge + pbat_vers_charge_24h[-1]
        deficit_restant = max(0, charge_h - fourni)
        
        etat = EtatSysteme(production_pv_kw=0, charge_demandee_kw=deficit_restant, pv_actif=False, sbee_disponible=profil_sbee[h]==1 and config['sbee_dispo'], puissance_sbee_kw=config['psbee'], diesel_actif=config['diesel_on'], puissance_diesel_kw=config['pdies'], heure_actuelle=h)
        decision = gestionnaire.decider_source_active(etat)
        psbee_24h.append(decision.puissance_sbee_utilisee)
        pdiesel_24h.append(decision.puissance_diesel_utilisee)
    
    epv = sum(ppv) if config['pv_actif'] else 0
    ebat = sum(pbat_vers_charge_24h)
    ech = sum(pch)
    esbee = sum(psbee_24h)
    ediesel = sum(pdiesel_24h)
    
    deficits = [max(0, pch[h] - ppv_vers_charge_24h[h] - pbat_vers_charge_24h[h] - psbee_24h[h] - pdiesel_24h[h]) for h in hrs]
    deficit_total = sum(deficits)
    heures_hors_tension = sum(1 for d in deficits if d > 0.1)
    couverture = ((ech - deficit_total) / ech * 100) if ech > 0 else 0
    
    return {
        'hrs': hrs, 'ppv': ppv, 'pch': pch, 'soc_24h': soc_24h,
        'ppv_vers_charge': ppv_vers_charge_24h, 'pbat_vers_charge': pbat_vers_charge_24h,
        'psbee': psbee_24h, 'pdiesel': pdiesel_24h, 'pbat_charge': pbat_charge_24h,
        'pbat_decharge': pbat_decharge_24h, 'deficits': deficits, 'profil_sbee': profil_sbee,
        'epv': epv, 'ebat': ebat, 'ech': ech, 'esbee': esbee, 'ediesel': ediesel,
        'deficit_total': deficit_total, 'heures_hors_tension': heures_hors_tension,
        'couverture': couverture, 'energie_bat_max': energie_bat_max
    }

def run_simulation_multi_jours(config, nb_jours, variabilite=True):
    """Simulation multi-jours"""
    np.random.seed(42)
    irr_var = np.random.normal(1, 0.15, nb_jours) if variabilite else np.ones(nb_jours)
    irr_var = np.clip(irr_var, 0.5, 1.3)
    
    resultats = []
    progress = st.progress(0)
    
    for jour in range(nb_jours):
        progress.progress((jour + 1) / nb_jours)
        cfg = config.copy()
        cfg['irr_journaliere'] = config['irr_journaliere'] * irr_var[jour]
        res = run_simulation_24h(cfg)
        res['jour'] = jour + 1
        res['irr_jour'] = cfg['irr_journaliere']
        resultats.append(res)
    
    progress.empty()
    
    return {
        'jours': resultats, 'nb_jours': nb_jours,
        'total_pv': sum(r['epv'] for r in resultats),
        'total_sbee': sum(r['esbee'] for r in resultats),
        'total_charge': sum(r['ech'] for r in resultats),
        'couverture_moyenne': np.mean([r['couverture'] for r in resultats]),
        'irr_variations': irr_var
    }

# ============================================================================
# ONGLETS PRINCIPAUX
# ============================================================================
st.markdown("---")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Simulation 24h", "📅 Multi-Jours", "🔄 Comparaison", "📥 Export", "🎓 Mode Pédagogique"])

# ============================================================================
# TAB 1: SIMULATION 24H
# ============================================================================
with tab1:
    # Mise à jour de l'étape de progression
    if not st.session_state.simulation_lancee:
        st.session_state.etape_progression = 1
    
    # Bouton centré
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        if st.button("🚀 LANCER SIMULATION", type="primary", use_container_width=True):
            with st.spinner("Simulation en cours..."):
                st.session_state.resultats_simulation = run_simulation_24h(config)
                st.session_state.simulation_lancee = True
                st.session_state.etape_progression = 2
                # Passer en mode présentation automatiquement
                st.session_state.mode_presentation = True
            st.rerun()
    
    if st.session_state.simulation_lancee and st.session_state.resultats_simulation:
        res = st.session_state.resultats_simulation
        
        # Mise à jour progression vers Analyse
        st.session_state.etape_progression = 3
        
        # Alerte
        if res['heures_hors_tension'] > 0:
            render_alert(f"⚠️ {res['heures_hors_tension']}h hors tension - Déficit: {res['deficit_total']:.1f} kWh", "danger")
        else:
            render_alert("✅ Charge 100% couverte - Système optimal", "success")
        
        # KPIs avec sparklines (seulement pour ceux qui ont des données valides)
        kpi_data = [
            {'icon': '🌞', 'value': f"{res['epv']:.1f} kWh", 'label': 'Production PV', 'type': 'pv', 
             'sparkline_data': res['ppv'], 'delta': f"+{(res['epv']/res['ech']*100):.0f}% couv.", 'delta_type': 'positive'},
            {'icon': '🔋', 'value': f"{res['ebat']:.1f} kWh", 'label': 'Batterie', 'type': 'battery',
             'sparkline_data': res['soc_24h'], 'delta': f"SOC {res['soc_24h'][-1]:.0f}%", 'delta_type': 'positive' if res['soc_24h'][-1]>50 else 'warning'},
            {'icon': '🔌', 'value': f"{res['esbee']:.1f} kWh", 'label': 'SBEE', 'type': 'sbee',
             'sparkline_data': res['psbee'] if sum(res['psbee']) > 0 else None},
            {'icon': '🛢️', 'value': f"{res['ediesel']:.1f} kWh", 'label': 'Diesel', 'type': 'diesel',
             'sparkline_data': res['pdiesel'] if sum(res['pdiesel']) > 0 else None},
            {'icon': '⚡', 'value': f"{res['ech']:.1f} kWh", 'label': 'Charge Totale', 'type': 'charge',
             'sparkline_data': res['pch']},
            {'icon': '✅', 'value': f"{res['couverture']:.0f}%", 'label': 'Couverture', 'type': 'coverage',
             'delta': 'Excellent' if res['couverture'] >= 95 else 'À améliorer', 'delta_type': 'positive' if res['couverture'] >= 95 else 'warning'},
        ]
        render_kpi_dashboard(kpi_data)
        
        # Graphique principal
        st.markdown("---")
        col_g1, col_g2 = st.columns([2, 1])
        
        with col_g1:
            plot_colors = get_plot_colors()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=res['hrs'], y=res['pch'], name='Charge', line=dict(color='#ef4444', width=3, dash='dot')))
            if pv_actif:
                fig.add_trace(go.Scatter(x=res['hrs'], y=res['ppv'], name='PV', fill='tozeroy', line=dict(color='#fbbf24'), fillcolor='rgba(251,191,36,0.3)'))
            if sum(res['pbat_vers_charge']) > 0:
                fig.add_trace(go.Scatter(x=res['hrs'], y=res['pbat_vers_charge'], name='Batterie', line=dict(color='#0ea5e9')))
            if sum(res['psbee']) > 0:
                fig.add_trace(go.Scatter(x=res['hrs'], y=res['psbee'], name='SBEE', line=dict(color='#22c55e')))
            if sum(res['pdiesel']) > 0:
                fig.add_trace(go.Scatter(x=res['hrs'], y=res['pdiesel'], name='Diesel', line=dict(color='#f97316')))
            
            for h in res['hrs']:
                if res['deficits'][h] > 0.1:
                    fig.add_vrect(x0=h-0.5, x1=h+0.5, fillcolor="red", opacity=0.2, line_width=0)
            
            fig.update_layout(
                title='Production et Consommation 24h', 
                xaxis_title='Heure', yaxis_title='kW', 
                height=400, 
                plot_bgcolor=plot_colors['plot_bg'], 
                paper_bgcolor=plot_colors['paper_bg'], 
                font=dict(color=plot_colors['font_color']), 
                legend=dict(orientation='h', y=1.1),
                xaxis=dict(gridcolor=plot_colors['grid_color']),
                yaxis=dict(gridcolor=plot_colors['grid_color'])
            )
            st.plotly_chart(fig, use_container_width=True)
            # Bouton téléchargement PNG
            render_download_button_for_chart(fig, "graphique_24h", "dl_graph_24h")
        
        with col_g2:
            # Camembert
            labels, values, colors = [], [], []
            if sum(res['ppv_vers_charge']) > 0: labels.append('PV'); values.append(sum(res['ppv_vers_charge'])); colors.append('#fbbf24')
            if res['ebat'] > 0: labels.append('Batterie'); values.append(res['ebat']); colors.append('#0ea5e9')
            if res['esbee'] > 0: labels.append('SBEE'); values.append(res['esbee']); colors.append('#22c55e')
            if res['ediesel'] > 0: labels.append('Diesel'); values.append(res['ediesel']); colors.append('#f97316')
            
            if labels:
                fig_pie = go.Figure(go.Pie(labels=labels, values=values, hole=0.6, marker=dict(colors=colors)))
                fig_pie.update_layout(title='Répartition Sources', height=280, paper_bgcolor=plot_colors['paper_bg'], font=dict(color=plot_colors['font_color']))
                st.plotly_chart(fig_pie, use_container_width=True)
                # Bouton téléchargement PNG camembert
                render_download_button_for_chart(fig_pie, "repartition_sources", "dl_pie", 600, 400)
            
            # Jauge SOC - Plus grande
            st.markdown("#### 🔋 État Batterie")
            fig_soc = go.Figure(go.Indicator(
                mode="gauge+number", 
                value=res['soc_24h'][-1], 
                number={'suffix': '%', 'font': {'size': 40, 'color': plot_colors['font_color']}}, 
                title={'text': f"SOC Final<br><span style='font-size:14px;color:#94a3b8'>{energie_bat_max:.1f} kWh</span>", 'font': {'size': 16, 'color': plot_colors['font_color']}}, 
                gauge={
                    'axis': {'range': [0,100], 'tickwidth': 2, 'tickcolor': '#64748b', 'tickvals': [0, 25, 50, 75, 100]}, 
                    'bar': {'color': '#0ea5e9', 'thickness': 0.7}, 
                    'bgcolor': '#1e293b' if st.session_state.theme == 'dark' else '#e2e8f0',
                    'borderwidth': 2,
                    'bordercolor': '#334155' if st.session_state.theme == 'dark' else '#cbd5e1',
                    'steps': [
                        {'range': [0,20], 'color': 'rgba(239,68,68,0.3)'}, 
                        {'range': [20,50], 'color': 'rgba(251,191,36,0.3)'}, 
                        {'range': [50,100], 'color': 'rgba(34,197,94,0.3)'}
                    ]
                }
            ))
            fig_soc.update_layout(height=280, paper_bgcolor=plot_colors['paper_bg'], font=dict(color=plot_colors['font_color']), margin=dict(l=30, r=30, t=60, b=30))
            st.plotly_chart(fig_soc, use_container_width=True)
            # Bouton téléchargement PNG jauge
            render_download_button_for_chart(fig_soc, "jauge_soc", "dl_soc", 500, 350)
        
        # ============================================================================
        # ANALYSE ÉCONOMIQUE
        # ============================================================================
        if analyse_eco_active:
            st.markdown("---")
            with st.expander("💰 Analyse Économique", expanded=True):
                try:
                    params_eco = ParametresEconomiques(
                        cout_pv_par_wc=cout_pv_wc, cout_batterie_lithium_par_kwh=cout_bat_lithium,
                        cout_batterie_plomb_par_kwh=cout_bat_plomb, cout_onduleur_par_kw=cout_onduleur,
                        cout_regulateur_mppt=cout_mppt, cout_diesel_par_kw=cout_diesel_kw,
                        taux_installation=taux_installation/100, taux_maintenance_pv=taux_maint_pv,
                        prix_diesel_litre=prix_diesel_litre, consommation_diesel_l_par_kwh=conso_diesel_l_kwh,
                        tarif_sbee_kwh=tarif_sbee, duree_vie_projet=duree_vie_projet,
                        taux_actualisation=taux_actualisation, taux_inflation=taux_inflation
                    )
                    
                    analyseur = AnalyseurEconomique(params_eco)
                    resultats_eco = analyseur.analyser_systeme_complet(
                        puissance_pv_wc=ptot, capacite_batterie_kwh=energie_bat_max,
                        type_batterie=tbat, puissance_onduleur_kw=pond,
                        puissance_diesel_kw=pdies if diesel_on else 0, diesel_actif=diesel_on,
                        energie_pv_kwh=sum(res['ppv_vers_charge']), energie_batterie_kwh=res['ebat'],
                        energie_sbee_kwh=res['esbee'], energie_diesel_kwh=res['ediesel'],
                        energie_charge_totale_kwh=res['ech']
                    )
                    
                    # Affichage amélioré des métriques
                    st.markdown("""
                    <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; margin: 1rem 0;">
                    """, unsafe_allow_html=True)
                    
                    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
                    col_e1.metric("💵 CAPEX", f"{resultats_eco.capex_total/1e6:.2f} M FCFA")
                    col_e2.metric("💳 OPEX/an", f"{resultats_eco.opex_total_annuel/1e6:.2f} M FCFA")
                    col_e3.metric("⏱️ Payback", f"{resultats_eco.payback_annees:.1f} ans" if resultats_eco.payback_annees < 100 else "∞")
                    col_e4.metric("📈 ROI", f"{resultats_eco.roi_pourcent:.0f}%")
                    
                    if resultats_eco.economie_vs_sbee > 0:
                        render_alert(f"💚 Économie estimée: {resultats_eco.economie_vs_sbee/1e6:.2f} M FCFA sur {duree_vie_projet} ans vs 100% SBEE", "success")
                    else:
                        render_alert(f"⚠️ Surcoût estimé: {abs(resultats_eco.economie_vs_sbee)/1e6:.2f} M FCFA (mais indépendance énergétique)", "warning")
                    
                    # Stocker les données pour l'export PDF
                    st.session_state.config_rapport_eco = {'pv_kwc': ptot/1000, 'batterie_kwh': energie_bat_max, 'type_batterie': tbat, 'tension_v': vbat, 'onduleur_kw': pond, 'diesel_actif': diesel_on, 'diesel_kw': pdies if diesel_on else 0, 'sbee_actif': sbee_dispo}
                    st.session_state.resultats_eco = resultats_eco
                    st.session_state.params_eco = params_eco
                    
                    st.info("💡 Le rapport PDF économique est disponible dans l'onglet **📥 Export**")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse économique: {str(e)}")
                    st.info("Vérifiez que tous les paramètres économiques sont correctement configurés dans la sidebar.")
        
        # ============================================================================
        # OPTIMISATION SYSTÈME
        # ============================================================================
        st.markdown("---")
        with st.expander("🤖 Optimisation Système - Recommandation", expanded=False):
            ech = res['ech']
            COUVERTURE_CIBLE = 95.0
            heures_soleil = 5.0
            
            energie_pv_necessaire = ech * (COUVERTURE_CIBLE / 100) * 1.2
            pv_optimal_kwc = energie_pv_necessaire / heures_soleil
            nb_panneaux_200w = int(np.ceil((pv_optimal_kwc * 1000) / 200))
            pv_reel_kwc = (nb_panneaux_200w * 200) / 1000
            
            charge_moyenne = ech / 24
            autonomie_heures = 4
            capacite_batterie_kwh = charge_moyenne * autonomie_heures * 1.25 / 0.5
            nb_batteries_200ah = int(np.ceil(capacite_batterie_kwh / 2.4))
            capacite_reelle_kwh = nb_batteries_200ah * 2.4
            
            nb_onduleurs = int(np.ceil((puissance_max_charge * 1.2) / 5))
            
            courant_pv = (pv_reel_kwc * 1000) / 48
            if courant_pv <= 70:
                regulateur = "MPPT 250/70 Victron"
            elif courant_pv <= 100:
                regulateur = "MPPT 250/100 Victron"
            else:
                regulateur = f"{int(np.ceil(courant_pv/100))}x MPPT 250/100"
            
            surface_totale = nb_panneaux_200w * 1.5
            production_estimee = pv_reel_kwc * heures_soleil
            couverture_estimee = min((production_estimee / ech) * 100, 100) if ech > 0 else 100
            complement_sbee = max(0, ech - production_estimee)
            
            st.markdown("#### 📋 Recommandation")
            
            # Tableau centré avec HTML
            st.markdown(f"""
            <div style="display: flex; justify-content: center; margin: 1rem 0;">
                <table style="border-collapse: collapse; background: rgba(30, 41, 59, 0.5); border-radius: 10px; overflow: hidden;">
                    <thead>
                        <tr style="background: linear-gradient(135deg, #0ea5e9, #0284c7);">
                            <th style="padding: 12px 20px; color: white; text-align: left;">Composant</th>
                            <th style="padding: 12px 20px; color: white; text-align: center;">Quantité</th>
                            <th style="padding: 12px 20px; color: white; text-align: left;">Spécification</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <td style="padding: 10px 20px; color: #f8fafc;">🔆 Panneaux</td>
                            <td style="padding: 10px 20px; color: #fbbf24; font-weight: bold; text-align: center;">{nb_panneaux_200w}</td>
                            <td style="padding: 10px 20px; color: #94a3b8;">200W polycristallin</td>
                        </tr>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <td style="padding: 10px 20px; color: #f8fafc;">🔋 Batteries</td>
                            <td style="padding: 10px 20px; color: #0ea5e9; font-weight: bold; text-align: center;">{nb_batteries_200ah}</td>
                            <td style="padding: 10px 20px; color: #94a3b8;">200Ah 12V</td>
                        </tr>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);">
                            <td style="padding: 10px 20px; color: #f8fafc;">⚡ Onduleur</td>
                            <td style="padding: 10px 20px; color: #22c55e; font-weight: bold; text-align: center;">{nb_onduleurs}</td>
                            <td style="padding: 10px 20px; color: #94a3b8;">5kVA Victron</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 20px; color: #f8fafc;">🎛️ Régulateur</td>
                            <td style="padding: 10px 20px; color: #8b5cf6; font-weight: bold; text-align: center;">1</td>
                            <td style="padding: 10px 20px; color: #94a3b8;">{regulateur}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div style="text-align: center; margin: 1rem 0;">
                <span style="background: rgba(251, 191, 36, 0.2); padding: 8px 16px; border-radius: 20px; color: #fbbf24; margin: 0 5px;">🌞 PV: {pv_reel_kwc:.1f} kWc</span>
                <span style="background: rgba(14, 165, 233, 0.2); padding: 8px 16px; border-radius: 20px; color: #0ea5e9; margin: 0 5px;">🔋 Batterie: {capacite_reelle_kwh:.1f} kWh</span>
                <span style="background: rgba(34, 197, 94, 0.2); padding: 8px 16px; border-radius: 20px; color: #22c55e; margin: 0 5px;">📐 Surface: {surface_totale:.0f} m²</span>
            </div>
            """, unsafe_allow_html=True)
            
            if analyse_eco_active:
                cout_panneaux = nb_panneaux_200w * 55000
                cout_batteries = nb_batteries_200ah * 218000
                cout_ond = nb_onduleurs * 1250000
                cout_reg = 575000
                sous_total = cout_panneaux + cout_batteries + cout_ond + cout_reg
                cout_inst = sous_total * (taux_installation / 100)
                cout_total = sous_total + cout_inst
                st.success(f"💰 **Investissement estimé: {cout_total/1e6:.2f} M FCFA**")
            else:
                cout_panneaux = cout_batteries = cout_ond = cout_reg = cout_inst = cout_total = 0
            
            st.info(f"📊 Couverture estimée: {couverture_estimee:.0f}% | Autonomie: {autonomie_heures}h | Complément SBEE: {complement_sbee:.1f} kWh/j")
            
            # Stocker les données pour l'export PDF
            st.session_state.opt_data = {
                'nb_panneaux_200w': nb_panneaux_200w, 'pv_reel_kwc': pv_reel_kwc,
                'nb_batteries_200ah': nb_batteries_200ah, 'capacite_reelle_kwh': capacite_reelle_kwh,
                'nb_onduleurs': nb_onduleurs, 'regulateur': regulateur,
                'production_estimee': production_estimee, 'couverture_estimee': couverture_estimee,
                'autonomie_heures': autonomie_heures, 'complement_sbee': complement_sbee,
                'cout_panneaux': cout_panneaux, 'cout_batteries': cout_batteries,
                'cout_ond': cout_ond, 'cout_inst': cout_inst, 'cout_total': cout_total
            }
            
            st.info("💡 Les rapports PDF sont disponibles dans l'onglet **📥 Export**")
        
        # Sauvegarder scénario
        st.markdown("---")
        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            scenario_name = st.text_input("Nom du scénario", f"Scénario {len(st.session_state.scenarios)+1}")
        with col_s2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Sauvegarder", use_container_width=True, key="btn_save_scenario"):
                # Copie sécurisée des résultats (convertir numpy arrays en listes)
                res_copy = {}
                for k, v in res.items():
                    if isinstance(v, np.ndarray):
                        res_copy[k] = v.tolist()
                    elif isinstance(v, list):
                        res_copy[k] = v.copy()
                    else:
                        res_copy[k] = v
                
                # Copie sécurisée de la config
                config_copy = {}
                for k, v in config.items():
                    if isinstance(v, (np.floating, np.integer)):
                        config_copy[k] = float(v)
                    elif isinstance(v, np.ndarray):
                        config_copy[k] = v.tolist()
                    else:
                        config_copy[k] = v
                
                st.session_state.scenarios[scenario_name] = {
                    'config': config_copy, 
                    'resultats': res_copy, 
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.toast(f"✅ '{scenario_name}' sauvegardé!", icon="✅")

# ============================================================================
# TAB 2: MULTI-JOURS
# ============================================================================
with tab2:
    st.markdown("### 📅 Simulation Multi-Jours")
    
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        nb_jours = st.selectbox("Durée", [7, 14, 30], format_func=lambda x: f"{x} jours")
    with col_m2:
        variabilite = st.checkbox("Variabilité météo", True)
    with col_m3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Lancer Multi-Jours", type="primary", use_container_width=True):
            st.session_state.multi_jours_resultats = run_simulation_multi_jours(config, nb_jours, variabilite)
            st.success("✅ Terminé!")
    
    if st.session_state.multi_jours_resultats:
        mj = st.session_state.multi_jours_resultats
        
        kpi_mj = [
            {'icon': '🌞', 'value': f"{mj['total_pv']:.0f} kWh", 'label': f'PV Total ({nb_jours}j)', 'type': 'pv'},
            {'icon': '🔌', 'value': f"{mj['total_sbee']:.0f} kWh", 'label': 'SBEE Total', 'type': 'sbee'},
            {'icon': '⚡', 'value': f"{mj['total_charge']:.0f} kWh", 'label': 'Charge Totale', 'type': 'charge'},
            {'icon': '✅', 'value': f"{mj['couverture_moyenne']:.1f}%", 'label': 'Couverture Moy.', 'type': 'coverage'},
        ]
        render_kpi_dashboard(kpi_mj)
        
        # Graphique
        plot_colors = get_plot_colors()
        fig_mj = go.Figure()
        fig_mj.add_trace(go.Bar(x=[f"J{r['jour']}" for r in mj['jours']], y=[r['epv'] for r in mj['jours']], name='PV', marker_color='#fbbf24'))
        fig_mj.add_trace(go.Bar(x=[f"J{r['jour']}" for r in mj['jours']], y=[r['esbee'] for r in mj['jours']], name='SBEE', marker_color='#22c55e'))
        fig_mj.add_trace(go.Scatter(x=[f"J{r['jour']}" for r in mj['jours']], y=[r['ech'] for r in mj['jours']], name='Charge', line=dict(color='#ef4444', width=3)))
        fig_mj.update_layout(
            barmode='stack', height=400, 
            title='Évolution Journalière',
            xaxis_title='Jour', yaxis_title='kWh',
            plot_bgcolor=plot_colors['plot_bg'], 
            paper_bgcolor=plot_colors['paper_bg'], 
            font=dict(color=plot_colors['font_color']),
            xaxis=dict(gridcolor=plot_colors['grid_color']),
            yaxis=dict(gridcolor=plot_colors['grid_color'])
        )
        st.plotly_chart(fig_mj, use_container_width=True)
        # Bouton téléchargement PNG multi-jours
        render_download_button_for_chart(fig_mj, f"simulation_{nb_jours}_jours", "dl_multi_jours")

# ============================================================================
# TAB 3: COMPARAISON
# ============================================================================
with tab3:
    st.markdown("### 🔄 Comparaison Scénarios")
    
    if len(st.session_state.scenarios) == 0:
        st.info("💡 Aucun scénario sauvegardé. Lancez une simulation et cliquez sur **💾 Sauvegarder**.")
    elif len(st.session_state.scenarios) == 1:
        st.warning("⚠️ Sauvegardez au moins 2 scénarios pour les comparer.")
        st.markdown("**Scénario actuel:**")
        for name, data in st.session_state.scenarios.items():
            st.write(f"- **{name}**: PV {data['config']['ptot']/1000:.2f} kWc, Batterie {data['config']['energie_bat_max']:.1f} kWh, Couverture {data['resultats']['couverture']:.1f}%")
    else:
        st.success(f"✅ {len(st.session_state.scenarios)} scénarios disponibles pour comparaison")
        
        # Liste des scénarios
        for name, data in st.session_state.scenarios.items():
            with st.expander(f"📁 {name} ({data['timestamp']})"):
                col_sc1, col_sc2 = st.columns(2)
                with col_sc1:
                    st.write(f"**PV:** {data['config']['ptot']/1000:.2f} kWc")
                    st.write(f"**Batterie:** {data['config']['energie_bat_max']:.1f} kWh ({data['config']['tbat']})")
                    st.write(f"**Charge Max:** {data['config']['puissance_max_charge']:.1f} kW")
                with col_sc2:
                    st.write(f"**Couverture:** {data['resultats']['couverture']:.1f}%")
                    st.write(f"**Déficit:** {data['resultats']['deficit_total']:.1f} kWh")
                    st.write(f"**SBEE utilisé:** {data['resultats']['esbee']:.1f} kWh")
        
        # Graphique de comparaison
        st.markdown("---")
        st.markdown("#### 📊 Comparaison Graphique")
        
        plot_colors = get_plot_colors()
        scenario_names = list(st.session_state.scenarios.keys())
        
        # Graphique barres groupées
        fig_comp = go.Figure()
        
        metrics = [
            ('epv', 'Production PV', '#fbbf24'),
            ('ebat', 'Batterie', '#0ea5e9'),
            ('esbee', 'SBEE', '#22c55e'),
            ('ediesel', 'Diesel', '#f97316'),
        ]
        
        for metric_key, metric_name, color in metrics:
            values = [st.session_state.scenarios[name]['resultats'].get(metric_key, 0) for name in scenario_names]
            fig_comp.add_trace(go.Bar(name=metric_name, x=scenario_names, y=values, marker_color=color))
        
        fig_comp.update_layout(
            barmode='group',
            title='Comparaison des Sources d\'Énergie (kWh)',
            xaxis_title='Scénario',
            yaxis_title='Énergie (kWh)',
            height=400,
            plot_bgcolor=plot_colors['plot_bg'],
            paper_bgcolor=plot_colors['paper_bg'],
            font=dict(color=plot_colors['font_color']),
            legend=dict(orientation='h', y=1.1)
        )
        st.plotly_chart(fig_comp, use_container_width=True)
        render_download_button_for_chart(fig_comp, "comparaison_scenarios", "dl_comp")
        
        # Tableau comparatif détaillé
        st.markdown("#### 📋 Tableau Comparatif")
        comp_data = []
        for n, d in st.session_state.scenarios.items():
            comp_data.append({
                'Scénario': n,
                'PV (kWc)': f"{d['config']['ptot']/1000:.2f}",
                'Batterie (kWh)': f"{d['config']['energie_bat_max']:.1f}",
                'Type Bat.': d['config']['tbat'],
                'Prod. PV (kWh)': f"{d['resultats']['epv']:.1f}",
                'SBEE (kWh)': f"{d['resultats']['esbee']:.1f}",
                'Couverture': f"{d['resultats']['couverture']:.1f}%",
                'Déficit (kWh)': f"{d['resultats']['deficit_total']:.1f}"
            })
        st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)
        
        # Bouton effacer
        st.markdown("---")
        if st.button("🗑️ Effacer tous les scénarios", type="secondary"):
            st.session_state.scenarios = {}
            st.rerun()

# ============================================================================
# TAB 4: EXPORT
# ============================================================================
with tab4:
    # Mise à jour de l'étape de progression
    if st.session_state.simulation_lancee:
        st.session_state.etape_progression = 4
    
    st.markdown("### 📥 Export des Données et Rapports")
    
    # Section Excel
    st.markdown("#### 📊 Exports Excel")
    col_x1, col_x2 = st.columns(2)
    
    with col_x1:
        st.markdown("**Simulation 24h**")
        if st.session_state.resultats_simulation:
            excel = export_to_excel(st.session_state.resultats_simulation, config)
            st.download_button("📥 Télécharger Excel 24h", data=excel, file_name=f"simulation_24h_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        else:
            st.info("Lancez une simulation 24h d'abord")
    
    with col_x2:
        st.markdown("**Multi-Jours**")
        if st.session_state.multi_jours_resultats:
            excel_mj = export_to_excel(st.session_state.multi_jours_resultats, config)
            st.download_button("📥 Télécharger Excel Multi-Jours", data=excel_mj, file_name=f"multi_jours_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        else:
            st.info("Lancez une simulation multi-jours d'abord")
    
    # Section PDF
    st.markdown("---")
    st.markdown("#### 📄 Rapports PDF")
    
    col_pdf1, col_pdf2, col_pdf3 = st.columns(3)
    
    # PDF Technique
    with col_pdf1:
        st.markdown("**📋 Rapport Technique Complet**")
        st.caption("Configuration, bilan 24h, profil horaire")
        
        if st.session_state.resultats_simulation:
            if st.button("📄 Générer PDF Technique", key="btn_gen_tech", use_container_width=True):
                try:
                    from fpdf import FPDF
                    res = st.session_state.resultats_simulation
                    
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=15)
                    
                    # Titre
                    pdf.set_font('Helvetica', 'B', 20)
                    pdf.set_text_color(0, 80, 120)
                    pdf.cell(0, 15, 'RAPPORT TECHNIQUE - SIMULATION 24H', 0, 1, 'C')
                    pdf.set_font('Helvetica', '', 11)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(0, 8, f'Date: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
                    pdf.cell(0, 8, f'Installation: {config["type_charge"].replace("_", " ").title()}', 0, 1, 'C')
                    pdf.ln(10)
                    
                    # Configuration
                    pdf.set_font('Helvetica', 'B', 14)
                    pdf.set_text_color(0, 80, 120)
                    pdf.cell(0, 10, '1. CONFIGURATION SYSTEME', 0, 1, 'L')
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(5)
                    
                    pdf.set_font('Helvetica', '', 10)
                    pdf.set_text_color(0, 0, 0)
                    configs_data = [
                        ("PV installe", f"{config['ptot']/1000:.2f} kWc ({config['type_techno']})"),
                        ("Surface PV", f"{config['surf']:.1f} m2"),
                        ("Batterie", f"{config['cap']:.0f} Ah / {config['energie_bat_max']:.1f} kWh ({config['tbat']})"),
                        ("Tension systeme", f"{config['vbat']} V"),
                        ("Onduleur", f"{config['pond']:.1f} kW"),
                        ("SBEE", f"{'Connecte' if config['sbee_dispo'] else 'Non'} - {config['psbee']} kW - {config['scenario_sbee']}"),
                        ("Diesel", f"{'Actif' if config['diesel_on'] else 'Inactif'} - {config['pdies']} kW"),
                        ("Irradiation", f"{config['irr_journaliere']} kWh/m2/jour"),
                    ]
                    for label, val in configs_data:
                        pdf.cell(60, 6, f"  {label}:", 0, 0)
                        pdf.set_font('Helvetica', 'B', 10)
                        pdf.cell(0, 6, val, 0, 1)
                        pdf.set_font('Helvetica', '', 10)
                    
                    # Bilan
                    pdf.ln(5)
                    pdf.set_font('Helvetica', 'B', 14)
                    pdf.set_text_color(0, 80, 120)
                    pdf.cell(0, 10, '2. BILAN ENERGETIQUE 24H', 0, 1, 'L')
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(5)
                    
                    pdf.set_font('Helvetica', '', 10)
                    pdf.set_text_color(0, 0, 0)
                    bilans = [
                        ("Production PV", f"{res['epv']:.1f} kWh"),
                        ("Batterie fournie", f"{res['ebat']:.1f} kWh"),
                        ("SBEE consomme", f"{res['esbee']:.1f} kWh"),
                        ("Diesel consomme", f"{res['ediesel']:.1f} kWh"),
                        ("Charge totale", f"{res['ech']:.1f} kWh"),
                        ("Deficit", f"{res['deficit_total']:.1f} kWh"),
                        ("Heures hors tension", f"{res['heures_hors_tension']}"),
                        ("Taux couverture", f"{res['couverture']:.1f}%"),
                    ]
                    for label, val in bilans:
                        pdf.cell(60, 6, f"  {label}:", 0, 0)
                        pdf.set_font('Helvetica', 'B', 10)
                        pdf.cell(0, 6, val, 0, 1)
                        pdf.set_font('Helvetica', '', 10)
                    
                    # Batterie
                    pdf.ln(5)
                    pdf.set_font('Helvetica', 'B', 14)
                    pdf.set_text_color(0, 80, 120)
                    pdf.cell(0, 10, '3. ETAT BATTERIE', 0, 1, 'L')
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(5)
                    
                    pdf.set_font('Helvetica', '', 10)
                    pdf.set_text_color(0, 0, 0)
                    energie_chargee = sum(res['pbat_charge'])
                    energie_dechargee = sum(res['pbat_decharge'])
                    cycles = energie_dechargee / config['energie_bat_max'] if config['energie_bat_max'] > 0 else 0
                    
                    bats = [
                        ("Energie chargee", f"{energie_chargee:.1f} kWh"),
                        ("Energie dechargee", f"{energie_dechargee:.1f} kWh"),
                        ("Cycles equivalent", f"{cycles:.2f}"),
                        ("SOC initial", f"{res['soc_24h'][0]:.1f}%"),
                        ("SOC final", f"{res['soc_24h'][-1]:.1f}%"),
                        ("SOC min", f"{min(res['soc_24h']):.1f}%"),
                        ("SOC max", f"{max(res['soc_24h']):.1f}%"),
                    ]
                    for label, val in bats:
                        pdf.cell(60, 6, f"  {label}:", 0, 0)
                        pdf.set_font('Helvetica', 'B', 10)
                        pdf.cell(0, 6, val, 0, 1)
                        pdf.set_font('Helvetica', '', 10)
                    
                    # Tableau horaire
                    pdf.add_page()
                    pdf.set_font('Helvetica', 'B', 14)
                    pdf.set_text_color(0, 80, 120)
                    pdf.cell(0, 10, '4. PROFIL HORAIRE DETAILLE', 0, 1, 'L')
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(5)
                    
                    pdf.set_fill_color(240, 240, 240)
                    pdf.set_font('Helvetica', 'B', 8)
                    pdf.cell(15, 7, 'Heure', 1, 0, 'C', True)
                    pdf.cell(25, 7, 'Charge', 1, 0, 'C', True)
                    pdf.cell(25, 7, 'PV', 1, 0, 'C', True)
                    pdf.cell(25, 7, 'Batterie', 1, 0, 'C', True)
                    pdf.cell(25, 7, 'SBEE', 1, 0, 'C', True)
                    pdf.cell(25, 7, 'Diesel', 1, 0, 'C', True)
                    pdf.cell(20, 7, 'SOC', 1, 0, 'C', True)
                    pdf.cell(25, 7, 'Deficit', 1, 1, 'C', True)
                    
                    pdf.set_font('Helvetica', '', 7)
                    for h in res['hrs']:
                        pdf.cell(15, 5, f'{h}:00', 1, 0, 'C')
                        pdf.cell(25, 5, f'{res["pch"][h]:.1f}', 1, 0, 'C')
                        pdf.cell(25, 5, f'{res["ppv"][h]:.1f}', 1, 0, 'C')
                        pdf.cell(25, 5, f'{res["pbat_vers_charge"][h]:.1f}', 1, 0, 'C')
                        pdf.cell(25, 5, f'{res["psbee"][h]:.1f}', 1, 0, 'C')
                        pdf.cell(25, 5, f'{res["pdiesel"][h]:.1f}', 1, 0, 'C')
                        pdf.cell(20, 5, f'{res["soc_24h"][h]:.0f}%', 1, 0, 'C')
                        pdf.cell(25, 5, f'{res["deficits"][h]:.1f}' if res["deficits"][h] > 0 else '-', 1, 1, 'C')
                    
                    pdf.ln(10)
                    pdf.set_font('Helvetica', 'I', 9)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(0, 6, 'Jumeau Numerique - Benin 2025', 0, 1, 'C')
                    
                    st.session_state.pdf_tech_data = bytes(pdf.output())
                    st.session_state.pdf_tech_ready = True
                    st.success("✅ PDF généré!")
                except Exception as e:
                    st.error(f"Erreur: {e}")
            
            if st.session_state.pdf_tech_ready and st.session_state.pdf_tech_data:
                st.download_button("📥 Télécharger PDF Technique", data=st.session_state.pdf_tech_data, file_name="Rapport_Technique_24h.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.info("Lancez une simulation d'abord")
    
    # PDF Économique
    with col_pdf2:
        st.markdown("**💰 Rapport Économique**")
        st.caption("CAPEX, OPEX, Payback, ROI")
        
        if hasattr(st.session_state, 'resultats_eco') and st.session_state.resultats_eco:
            if st.button("📄 Générer PDF Économique", key="btn_gen_eco", use_container_width=True):
                try:
                    pdf_eco_bytes = generer_rapport_pdf(
                        st.session_state.config_rapport_eco, 
                        st.session_state.resultats_eco, 
                        st.session_state.params_eco
                    )
                    st.session_state.pdf_eco_data = pdf_eco_bytes
                    st.session_state.pdf_eco_ready = True
                    st.success("✅ PDF généré!")
                except Exception as e:
                    st.error(f"Erreur: {e}")
            
            if st.session_state.pdf_eco_ready and st.session_state.pdf_eco_data:
                st.download_button("📥 Télécharger PDF Économique", data=st.session_state.pdf_eco_data, file_name="Rapport_Economique.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.info("Activez l'analyse économique et lancez une simulation")
    
    # PDF Optimisation
    with col_pdf3:
        st.markdown("**🤖 Rapport Optimisation**")
        st.caption("Recommandation dimensionnement")
        
        if hasattr(st.session_state, 'opt_data') and st.session_state.opt_data:
            if st.button("📄 Générer PDF Optimisation", key="btn_gen_opt", use_container_width=True):
                try:
                    from fpdf import FPDF
                    opt = st.session_state.opt_data
                    
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font('Helvetica', 'B', 18)
                    pdf.set_text_color(0, 100, 50)
                    pdf.cell(0, 15, 'OPTIMISATION SYSTEME PV', 0, 1, 'C')
                    pdf.set_font('Helvetica', '', 11)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(0, 8, f'Date: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
                    pdf.ln(10)
                    
                    pdf.set_font('Helvetica', 'B', 12)
                    pdf.set_text_color(0, 80, 120)
                    pdf.cell(0, 8, '1. CONFIGURATION RECOMMANDEE', 0, 1)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(5)
                    
                    pdf.set_font('Helvetica', '', 10)
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(60, 6, 'Panneaux 200W:', 0, 0)
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.cell(0, 6, f'{opt["nb_panneaux_200w"]} unites ({opt["pv_reel_kwc"]:.1f} kWc)', 0, 1)
                    pdf.set_font('Helvetica', '', 10)
                    pdf.cell(60, 6, 'Batteries 200Ah:', 0, 0)
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.cell(0, 6, f'{opt["nb_batteries_200ah"]} unites ({opt["capacite_reelle_kwh"]:.1f} kWh)', 0, 1)
                    pdf.set_font('Helvetica', '', 10)
                    pdf.cell(60, 6, 'Onduleurs 5kVA:', 0, 0)
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.cell(0, 6, f'{opt["nb_onduleurs"]} unites', 0, 1)
                    pdf.set_font('Helvetica', '', 10)
                    pdf.cell(60, 6, 'Regulateur:', 0, 0)
                    pdf.set_font('Helvetica', 'B', 10)
                    pdf.cell(0, 6, opt["regulateur"], 0, 1)
                    
                    pdf.ln(5)
                    pdf.set_font('Helvetica', 'B', 12)
                    pdf.set_text_color(0, 80, 120)
                    pdf.cell(0, 8, '2. PERFORMANCES ESTIMEES', 0, 1)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(5)
                    
                    pdf.set_font('Helvetica', '', 10)
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(60, 6, 'Production estimee:', 0, 0)
                    pdf.cell(0, 6, f'{opt["production_estimee"]:.1f} kWh/jour', 0, 1)
                    pdf.cell(60, 6, 'Couverture:', 0, 0)
                    pdf.cell(0, 6, f'{opt["couverture_estimee"]:.0f}%', 0, 1)
                    pdf.cell(60, 6, 'Autonomie:', 0, 0)
                    pdf.cell(0, 6, f'{opt["autonomie_heures"]} heures', 0, 1)
                    pdf.cell(60, 6, 'Complement SBEE:', 0, 0)
                    pdf.cell(0, 6, f'{opt["complement_sbee"]:.1f} kWh/jour', 0, 1)
                    
                    if opt["cout_total"] > 0:
                        pdf.ln(5)
                        pdf.set_font('Helvetica', 'B', 12)
                        pdf.set_text_color(0, 80, 120)
                        pdf.cell(0, 8, '3. ESTIMATION DES COUTS', 0, 1)
                        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                        pdf.ln(5)
                        
                        pdf.set_font('Helvetica', '', 10)
                        pdf.set_text_color(0, 0, 0)
                        pdf.cell(60, 6, 'Panneaux:', 0, 0)
                        pdf.cell(0, 6, f'{opt["cout_panneaux"]:,.0f} FCFA', 0, 1)
                        pdf.cell(60, 6, 'Batteries:', 0, 0)
                        pdf.cell(0, 6, f'{opt["cout_batteries"]:,.0f} FCFA', 0, 1)
                        pdf.cell(60, 6, 'Onduleurs:', 0, 0)
                        pdf.cell(0, 6, f'{opt["cout_ond"]:,.0f} FCFA', 0, 1)
                        pdf.cell(60, 6, 'Installation:', 0, 0)
                        pdf.cell(0, 6, f'{opt["cout_inst"]:,.0f} FCFA', 0, 1)
                        pdf.set_font('Helvetica', 'B', 11)
                        pdf.cell(60, 8, 'TOTAL:', 0, 0)
                        pdf.cell(0, 8, f'{opt["cout_total"]:,.0f} FCFA', 0, 1)
                    
                    pdf.ln(10)
                    pdf.set_font('Helvetica', 'I', 9)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(0, 6, 'Jumeau Numerique - Benin 2025', 0, 1, 'C')
                    
                    st.session_state.pdf_opt_data = bytes(pdf.output())
                    st.session_state.pdf_opt_ready = True
                    st.success("✅ PDF généré!")
                except Exception as e:
                    st.error(f"Erreur: {e}")
            
            if st.session_state.pdf_opt_ready and st.session_state.pdf_opt_data:
                st.download_button("📥 Télécharger PDF Optimisation", data=st.session_state.pdf_opt_data, file_name="Rapport_Optimisation.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.info("Lancez une simulation pour voir les recommandations")
    
    # Section JSON
    st.markdown("---")
    st.markdown("#### 📋 Export Scénarios (JSON)")
    if st.session_state.scenarios:
        json_data = json.dumps({n: {'config': {k: float(v) if isinstance(v, (np.floating, np.integer)) else v for k, v in d['config'].items()}, 'timestamp': d['timestamp']} for n, d in st.session_state.scenarios.items()}, indent=2, default=str)
        st.download_button("📥 Télécharger Scénarios JSON", data=json_data, file_name="scenarios.json", mime="application/json", use_container_width=True)
    else:
        st.info("Aucun scénario sauvegardé")

# ============================================================================
# TAB 5: MODE PÉDAGOGIQUE
# ============================================================================
with tab5:
    render_mode_pedagogique()

# ============================================================================
# FOOTER AMÉLIORÉ
# ============================================================================
render_footer()