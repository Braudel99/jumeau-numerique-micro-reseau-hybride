"""
Module de Génération de Rapports PDF
=====================================

Génère des rapports PDF professionnels pour l'analyse économique
du micro-réseau hybride.

Auteur: Master Énergie
Date: Janvier 2025
"""

from fpdf import FPDF
from datetime import datetime
import io


class RapportPDF(FPDF):
    """
    Classe personnalisée pour générer des rapports PDF formatés.
    """
    
    def __init__(self):
        super().__init__()
        self.add_page()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        """En-tête du document"""
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(0, 100, 150)
        self.cell(0, 10, 'Rapport d\'Analyse Économique - Micro-Réseau Hybride', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        """Pied de page"""
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def titre_section(self, titre):
        """Ajoute un titre de section"""
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(0, 80, 120)
        self.cell(0, 10, titre, 0, 1, 'L')
        self.set_draw_color(0, 100, 150)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
    
    def sous_titre(self, titre):
        """Ajoute un sous-titre"""
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, titre, 0, 1, 'L')
        self.ln(1)
    
    def ligne_donnee(self, label, valeur, unite=""):
        """Ajoute une ligne de données"""
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        self.cell(80, 6, f"  {label}", 0, 0)
        self.set_font('Helvetica', 'B', 10)
        self.cell(60, 6, f"{valeur} {unite}", 0, 1)
    
    def espace(self, h=5):
        """Ajoute un espace vertical"""
        self.ln(h)
    
    def texte_normal(self, texte):
        """Ajoute du texte normal"""
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, texte)
        self.ln(2)
    
    def encadre_resultat(self, titre, valeur, couleur_fond=(230, 240, 250)):
        """Ajoute un résultat encadré"""
        self.set_fill_color(*couleur_fond)
        self.set_font('Helvetica', 'B', 11)
        self.cell(90, 10, f"  {titre}", 1, 0, 'L', True)
        self.set_font('Helvetica', 'B', 12)
        self.cell(90, 10, f"{valeur}", 1, 1, 'R', True)


def generer_rapport_pdf(config, resultats, params):
    """
    Génère un rapport PDF complet.
    
    Args:
        config: Dictionnaire avec la configuration du système
        resultats: Objet ResultatsEconomiques
        params: Objet ParametresEconomiques
    
    Returns:
        bytes: Contenu du PDF
    """
    pdf = RapportPDF()
    
    # Titre principal
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(0, 60, 100)
    pdf.cell(0, 15, 'ANALYSE ECONOMIQUE', 0, 1, 'C')
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, 'Micro-Réseau Hybride PV-SBEE-Diesel', 0, 1, 'C')
    pdf.cell(0, 8, f'Date: {datetime.now().strftime("%d/%m/%Y à %H:%M")}', 0, 1, 'C')
    pdf.espace(10)
    
    # 1. Configuration du système
    pdf.titre_section('1. CONFIGURATION DU SYSTEME')
    pdf.ligne_donnee('Puissance PV installée', f"{config['pv_kwc']:.1f}", 'kWc')
    pdf.ligne_donnee('Capacité Batterie', f"{config['batterie_kwh']:.1f}", 'kWh')
    pdf.ligne_donnee('Type Batterie', config['type_batterie'], '')
    pdf.ligne_donnee('Tension Système', f"{config['tension_v']}", 'V')
    pdf.ligne_donnee('Onduleur', f"{config['onduleur_kw']:.1f}", 'kW')
    pdf.ligne_donnee('Groupe Diesel', 'Oui' if config['diesel_actif'] else 'Non', '')
    if config['diesel_actif']:
        pdf.ligne_donnee('Puissance Diesel', f"{config['diesel_kw']:.0f}", 'kW')
    pdf.ligne_donnee('Réseau SBEE', 'Connecté' if config['sbee_actif'] else 'Non connecté', '')
    pdf.espace(5)
    
    # 2. Investissement Initial (CAPEX)
    pdf.titre_section('2. INVESTISSEMENT INITIAL (CAPEX)')
    pdf.ligne_donnee('Panneaux PV', f"{resultats.capex_pv:,.0f}", 'FCFA')
    pdf.ligne_donnee('Régulateur MPPT', f"{resultats.capex_regulateur:,.0f}", 'FCFA')
    pdf.ligne_donnee('Batterie', f"{resultats.capex_batterie:,.0f}", 'FCFA')
    pdf.ligne_donnee('Onduleur', f"{resultats.capex_onduleur:,.0f}", 'FCFA')
    if config['diesel_actif']:
        pdf.ligne_donnee('Groupe Diesel', f"{resultats.capex_diesel:,.0f}", 'FCFA')
    pdf.ligne_donnee('Installation', f"{resultats.capex_installation:,.0f}", 'FCFA')
    pdf.espace(3)
    pdf.encadre_resultat('TOTAL CAPEX', f"{resultats.capex_total:,.0f} FCFA", (200, 230, 200))
    pdf.espace(5)
    
    # 3. Coûts d'exploitation (OPEX)
    pdf.titre_section('3. COUTS D\'EXPLOITATION ANNUELS (OPEX)')
    pdf.ligne_donnee('Maintenance PV', f"{resultats.opex_maintenance_pv:,.0f}", 'FCFA/an')
    pdf.ligne_donnee('Maintenance Batterie', f"{resultats.opex_maintenance_batterie:,.0f}", 'FCFA/an')
    if config['diesel_actif']:
        pdf.ligne_donnee('Maintenance Diesel', f"{resultats.opex_maintenance_diesel:,.0f}", 'FCFA/an')
        pdf.ligne_donnee('Carburant Diesel', f"{resultats.opex_carburant_diesel:,.0f}", 'FCFA/an')
    if config['sbee_actif']:
        pdf.ligne_donnee('Électricité SBEE', f"{resultats.opex_electricite_sbee:,.0f}", 'FCFA/an')
    pdf.espace(3)
    pdf.encadre_resultat('TOTAL OPEX ANNUEL', f"{resultats.opex_total_annuel:,.0f} FCFA/an", (255, 230, 200))
    pdf.espace(5)
    
    # 4. Remplacements
    pdf.titre_section('4. COUTS DE REMPLACEMENT')
    if resultats.annees_remplacement_batterie:
        pdf.ligne_donnee('Remplacement Batterie', f"Années {', '.join(map(str, resultats.annees_remplacement_batterie))}", '')
    pdf.ligne_donnee('Coût Batterie (actualisé)', f"{resultats.cout_remplacement_batterie:,.0f}", 'FCFA')
    if resultats.annees_remplacement_onduleur:
        pdf.ligne_donnee('Remplacement Onduleur', f"Année {', '.join(map(str, resultats.annees_remplacement_onduleur))}", '')
    pdf.ligne_donnee('Coût Onduleur (actualisé)', f"{resultats.cout_remplacement_onduleur:,.0f}", 'FCFA')
    pdf.espace(5)
    
    # 5. Indicateurs financiers
    pdf.titre_section('5. INDICATEURS FINANCIERS')
    pdf.sous_titre(f'Sur une durée de {params.duree_vie_projet} ans')
    pdf.ligne_donnee('Coût Total Actualisé', f"{resultats.cout_total_actualise:,.0f}", 'FCFA')
    pdf.ligne_donnee('Coût du kWh produit', f"{resultats.cout_kwh_actualise:.0f}", 'FCFA/kWh')
    pdf.espace(3)
    
    # Payback
    if resultats.payback_annees < 100:
        pdf.encadre_resultat('Temps de Retour (Payback)', f"{resultats.payback_annees:.1f} ans", (200, 230, 200))
    else:
        pdf.encadre_resultat('Temps de Retour (Payback)', "Non rentable", (255, 200, 200))
    pdf.espace(3)
    
    # ROI
    if resultats.roi_pourcent > 0:
        pdf.encadre_resultat('Retour sur Investissement (ROI)', f"{resultats.roi_pourcent:.0f}%", (200, 230, 200))
    else:
        pdf.encadre_resultat('Retour sur Investissement (ROI)', f"{resultats.roi_pourcent:.0f}%", (255, 200, 200))
    pdf.espace(3)
    
    # VAN
    if resultats.van > 0:
        pdf.encadre_resultat('Valeur Actuelle Nette (VAN)', f"{resultats.van:,.0f} FCFA", (200, 230, 200))
    else:
        pdf.encadre_resultat('Valeur Actuelle Nette (VAN)', f"{resultats.van:,.0f} FCFA", (255, 200, 200))
    pdf.espace(5)
    
    # 6. Économies réalisées
    pdf.titre_section('6. ECONOMIES REALISEES')
    pourcentage_eco = (resultats.economie_vs_sbee / resultats.cout_reference_100_sbee * 100) if resultats.cout_reference_100_sbee > 0 else 0
    
    pdf.ligne_donnee('Coût référence 100% SBEE', f"{resultats.cout_reference_100_sbee:,.0f}", 'FCFA')
    pdf.ligne_donnee('Coût référence 100% Diesel', f"{resultats.cout_reference_100_diesel:,.0f}", 'FCFA')
    pdf.espace(3)
    
    if resultats.economie_vs_sbee > 0:
        pdf.encadre_resultat('Économie vs 100% SBEE', f"{resultats.economie_vs_sbee:,.0f} FCFA ({pourcentage_eco:.0f}%)", (200, 255, 200))
    else:
        pdf.encadre_resultat('Surcoût vs 100% SBEE', f"{abs(resultats.economie_vs_sbee):,.0f} FCFA", (255, 200, 200))
    pdf.espace(3)
    
    if resultats.economie_vs_diesel > 0:
        pdf.encadre_resultat('Économie vs 100% Diesel', f"{resultats.economie_vs_diesel:,.0f} FCFA", (200, 255, 200))
    else:
        pdf.encadre_resultat('Surcoût vs 100% Diesel', f"{abs(resultats.economie_vs_diesel):,.0f} FCFA", (255, 200, 200))
    pdf.espace(3)
    
    pdf.ligne_donnee('Économie annuelle moyenne', f"{resultats.economie_annuelle_moyenne:,.0f}", 'FCFA/an')
    pdf.espace(10)
    
    # 7. Conclusion
    pdf.titre_section('7. CONCLUSION')
    if resultats.economie_vs_sbee > 0 and resultats.payback_annees < params.duree_vie_projet:
        pdf.set_fill_color(200, 255, 200)
        pdf.set_font('Helvetica', 'B', 11)
        conclusion = f"""Le système hybride est RENTABLE.

Avec un investissement initial de {resultats.capex_total:,.0f} FCFA, le système permettra d'économiser {resultats.economie_vs_sbee:,.0f} FCFA sur {params.duree_vie_projet} ans par rapport à une alimentation 100% SBEE.

Le temps de retour sur investissement est de {resultats.payback_annees:.1f} ans, ce qui est inférieur à la durée de vie du projet.

Le ROI de {resultats.roi_pourcent:.0f}% confirme la rentabilité du projet."""
    else:
        pdf.set_fill_color(255, 230, 200)
        conclusion = f"""Le système hybride nécessite une optimisation pour être rentable.

Recommandations :
- Réduire la capacité de stockage batterie (composant le plus coûteux)
- Augmenter la puissance PV pour maximiser l'autoconsommation
- Négocier les coûts d'installation
- Envisager des batteries plomb-acide si le budget est limité"""
    
    pdf.multi_cell(0, 6, conclusion)
    pdf.espace(10)
    
    # Signature
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, 'Rapport généré par Digital Twin Micro-Réseau Hybride - Bénin 2025', 0, 1, 'C')
    
    # Retourner le PDF en bytes
    return bytes(pdf.output())