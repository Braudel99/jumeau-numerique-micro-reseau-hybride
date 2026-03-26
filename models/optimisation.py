"""
Module d'Optimisation Automatique pour Micro-Réseau Hybride
============================================================

Ce module calcule le dimensionnement optimal du système PV-Batterie
en fonction de la charge et des contraintes définies.

Auteur: Master Énergie
Date: Janvier 2025
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import numpy as np


@dataclass
class ContraintesOptimisation:
    """
    Contraintes pour l'optimisation du système.
    """
    # Limites PV
    pv_min_kwc: float = 1.0
    pv_max_kwc: float = 500.0
    pv_pas_kwc: float = 5.0
    
    # Limites Batterie
    batterie_min_kwh: float = 0.0
    batterie_max_kwh: float = 1000.0
    batterie_pas_kwh: float = 10.0
    
    # Objectifs
    autonomie_cible_heures: float = 4.0  # Heures d'autonomie sans SBEE
    couverture_cible_pourcent: float = 95.0  # % de couverture minimum
    
    # Priorité (1 = Coût, 2 = Autonomie, 3 = Équilibré)
    priorite: int = 3


@dataclass
class ResultatOptimisation:
    """
    Résultat de l'optimisation.
    """
    # Configuration optimale
    pv_optimal_kwc: float
    batterie_optimal_kwh: float
    
    # Performances
    couverture_pourcent: float
    autonomie_heures: float
    energie_pv_kwh: float
    energie_batterie_kwh: float
    energie_sbee_kwh: float
    deficit_kwh: float
    
    # Coûts (si analyse économique activée)
    capex_total: Optional[float] = None
    opex_annuel: Optional[float] = None
    cout_kwh: Optional[float] = None
    payback_annees: Optional[float] = None
    
    # Score global
    score: float = 0.0
    
    # Recommandations
    recommandations: List[str] = None


class OptimiseurMicroReseau:
    """
    Optimiseur pour dimensionner le micro-réseau hybride.
    
    Algorithme : Grid Search avec scoring multi-critères
    """
    
    def __init__(
        self,
        profil_charge_24h: List[float],
        profil_irradiation_24h: List[float],
        profil_temperature_24h: List[float],
        sbee_disponible: bool = True,
        diesel_disponible: bool = False,
        parametres_eco: Optional[object] = None
    ):
        """
        Initialise l'optimiseur.
        
        Args:
            profil_charge_24h: Charge horaire sur 24h (kW)
            profil_irradiation_24h: Irradiation horaire (W/m²)
            profil_temperature_24h: Température horaire (°C)
            sbee_disponible: Si SBEE est disponible en backup
            diesel_disponible: Si Diesel est disponible en backup
            parametres_eco: Paramètres économiques (optionnel)
        """
        self.charge_24h = profil_charge_24h
        self.irradiation_24h = profil_irradiation_24h
        self.temperature_24h = profil_temperature_24h
        self.sbee_dispo = sbee_disponible
        self.diesel_dispo = diesel_disponible
        self.params_eco = parametres_eco
        
        # Calculs préliminaires
        self.charge_totale_kwh = sum(profil_charge_24h)
        self.charge_max_kw = max(profil_charge_24h)
        self.charge_moyenne_kw = np.mean(profil_charge_24h)
    
    def _simuler_configuration(
        self,
        pv_kwc: float,
        batterie_kwh: float,
        dod: float = 0.8,
        rendement_pv: float = 0.18,
        surface_par_kwc: float = 5.0  # m² par kWc
    ) -> Dict:
        """
        Simule une configuration donnée sur 24h.
        
        Returns:
            Dictionnaire avec les résultats de simulation
        """
        # Initialisation
        soc = 100.0  # État de charge initial (%)
        soc_min = (1 - dod) * 100
        
        energie_pv_total = 0.0
        energie_batterie_fournie = 0.0
        energie_sbee_total = 0.0
        deficit_total = 0.0
        heures_autonomes = 0
        
        surface_pv = pv_kwc * surface_par_kwc
        capacite_utilisable = batterie_kwh * dod
        
        for h in range(24):
            charge_h = self.charge_24h[h]
            irrad_h = self.irradiation_24h[h]
            
            # Production PV
            prod_pv = surface_pv * rendement_pv * irrad_h / 1000  # kW
            energie_pv_total += prod_pv
            
            # Bilan énergétique
            surplus = prod_pv - charge_h
            
            if surplus >= 0:
                # Excédent PV → Charge batterie
                energie_charge = min(surplus, (100 - soc) / 100 * batterie_kwh)
                soc += (energie_charge / batterie_kwh * 100) if batterie_kwh > 0 else 0
                heures_autonomes += 1
            else:
                # Déficit → Décharge batterie
                deficit_h = abs(surplus)
                
                # Batterie peut fournir ?
                energie_dispo_bat = (soc - soc_min) / 100 * batterie_kwh
                energie_bat = min(deficit_h, energie_dispo_bat)
                soc -= (energie_bat / batterie_kwh * 100) if batterie_kwh > 0 else 0
                energie_batterie_fournie += energie_bat
                
                deficit_restant = deficit_h - energie_bat
                
                if deficit_restant > 0:
                    if self.sbee_dispo:
                        energie_sbee_total += deficit_restant
                    else:
                        deficit_total += deficit_restant
                else:
                    heures_autonomes += 1
        
        # Calcul couverture
        couverture = ((self.charge_totale_kwh - deficit_total) / self.charge_totale_kwh * 100) if self.charge_totale_kwh > 0 else 100
        
        return {
            'energie_pv': energie_pv_total,
            'energie_batterie': energie_batterie_fournie,
            'energie_sbee': energie_sbee_total,
            'deficit': deficit_total,
            'couverture': couverture,
            'heures_autonomes': heures_autonomes,
            'autonomie_pourcent': (heures_autonomes / 24) * 100
        }
    
    def _calculer_score(
        self,
        resultats_sim: Dict,
        pv_kwc: float,
        batterie_kwh: float,
        contraintes: ContraintesOptimisation
    ) -> Tuple[float, Optional[Dict]]:
        """
        Calcule le score d'une configuration.
        
        Returns:
            Tuple (score, infos_economiques)
        """
        score = 0.0
        infos_eco = None
        
        # Score couverture (max 40 points)
        couverture = resultats_sim['couverture']
        if couverture >= contraintes.couverture_cible_pourcent:
            score += 40
        else:
            score += (couverture / contraintes.couverture_cible_pourcent) * 40
        
        # Score autonomie (max 30 points)
        heures_auto = resultats_sim['heures_autonomes']
        if heures_auto >= contraintes.autonomie_cible_heures:
            score += 30
        else:
            score += (heures_auto / contraintes.autonomie_cible_heures) * 30
        
        # Score économique (max 30 points) - si paramètres disponibles
        if self.params_eco:
            # Calcul CAPEX simplifié
            capex_pv = pv_kwc * 1000 * self.params_eco.cout_pv_par_wc
            capex_bat = batterie_kwh * (
                self.params_eco.cout_batterie_lithium_par_kwh 
                if hasattr(self.params_eco, 'cout_batterie_lithium_par_kwh') 
                else 200000
            )
            capex_ond = pv_kwc * self.params_eco.cout_onduleur_par_kw
            capex_mppt = self.params_eco.cout_regulateur_mppt
            capex_total = (capex_pv + capex_bat + capex_ond + capex_mppt) * (1 + self.params_eco.taux_installation)
            
            # OPEX annuel
            opex_maintenance = capex_pv * 0.01 + capex_bat * 0.02
            opex_sbee = resultats_sim['energie_sbee'] * 365 * self.params_eco.tarif_sbee_kwh
            opex_total = opex_maintenance + opex_sbee
            
            # Coût du kWh
            energie_annuelle = self.charge_totale_kwh * 365
            cout_total_25ans = capex_total + opex_total * 25
            cout_kwh = cout_total_25ans / (energie_annuelle * 25) if energie_annuelle > 0 else float('inf')
            
            # Payback simplifié
            cout_sbee_annuel = energie_annuelle * self.params_eco.tarif_sbee_kwh
            economie_annuelle = cout_sbee_annuel - opex_total
            payback = capex_total / economie_annuelle if economie_annuelle > 0 else float('inf')
            
            infos_eco = {
                'capex_total': capex_total,
                'opex_annuel': opex_total,
                'cout_kwh': cout_kwh,
                'payback_annees': payback
            }
            
            # Score coût (inversement proportionnel)
            if cout_kwh < 150:
                score += 30
            elif cout_kwh < 200:
                score += 20
            elif cout_kwh < 300:
                score += 10
            else:
                score += 5
        else:
            # Sans économie : pénaliser les grosses installations
            ratio_pv = pv_kwc / self.charge_max_kw if self.charge_max_kw > 0 else 1
            ratio_bat = batterie_kwh / self.charge_totale_kwh if self.charge_totale_kwh > 0 else 1
            
            # Optimal : ratio_pv entre 1.5 et 2.5, ratio_bat entre 0.3 et 0.5
            if 1.5 <= ratio_pv <= 2.5:
                score += 15
            elif 1.0 <= ratio_pv <= 3.0:
                score += 10
            else:
                score += 5
            
            if 0.3 <= ratio_bat <= 0.5:
                score += 15
            elif 0.2 <= ratio_bat <= 0.8:
                score += 10
            else:
                score += 5
        
        return score, infos_eco
    
    def optimiser(
        self,
        contraintes: Optional[ContraintesOptimisation] = None
    ) -> ResultatOptimisation:
        """
        Lance l'optimisation pour trouver la meilleure configuration.
        
        Args:
            contraintes: Contraintes d'optimisation (optionnel)
        
        Returns:
            ResultatOptimisation avec la configuration optimale
        """
        if contraintes is None:
            contraintes = ContraintesOptimisation()
        
        # Ajuster les limites selon la charge
        pv_max = min(contraintes.pv_max_kwc, self.charge_max_kw * 4)
        bat_max = min(contraintes.batterie_max_kwh, self.charge_totale_kwh * 2)
        
        # Grid search
        meilleur_score = -1
        meilleure_config = None
        meilleures_infos_eco = None
        meilleurs_resultats = None
        
        for pv in np.arange(contraintes.pv_min_kwc, pv_max + 1, contraintes.pv_pas_kwc):
            for bat in np.arange(contraintes.batterie_min_kwh, bat_max + 1, contraintes.batterie_pas_kwh):
                # Simuler
                resultats = self._simuler_configuration(pv, bat)
                
                # Vérifier couverture minimum
                if resultats['couverture'] < contraintes.couverture_cible_pourcent * 0.8:
                    continue
                
                # Calculer score
                score, infos_eco = self._calculer_score(resultats, pv, bat, contraintes)
                
                if score > meilleur_score:
                    meilleur_score = score
                    meilleure_config = (pv, bat)
                    meilleures_infos_eco = infos_eco
                    meilleurs_resultats = resultats
        
        # Si aucune config trouvée, prendre la plus grande
        if meilleure_config is None:
            meilleure_config = (pv_max, bat_max)
            meilleurs_resultats = self._simuler_configuration(pv_max, bat_max)
            meilleur_score, meilleures_infos_eco = self._calculer_score(
                meilleurs_resultats, pv_max, bat_max, contraintes
            )
        
        # Générer recommandations
        recommandations = self._generer_recommandations(
            meilleure_config[0], 
            meilleure_config[1], 
            meilleurs_resultats,
            meilleures_infos_eco
        )
        
        # Construire résultat
        resultat = ResultatOptimisation(
            pv_optimal_kwc=meilleure_config[0],
            batterie_optimal_kwh=meilleure_config[1],
            couverture_pourcent=meilleurs_resultats['couverture'],
            autonomie_heures=meilleurs_resultats['heures_autonomes'],
            energie_pv_kwh=meilleurs_resultats['energie_pv'],
            energie_batterie_kwh=meilleurs_resultats['energie_batterie'],
            energie_sbee_kwh=meilleurs_resultats['energie_sbee'],
            deficit_kwh=meilleurs_resultats['deficit'],
            score=meilleur_score,
            recommandations=recommandations
        )
        
        # Ajouter infos économiques si disponibles
        if meilleures_infos_eco:
            resultat.capex_total = meilleures_infos_eco['capex_total']
            resultat.opex_annuel = meilleures_infos_eco['opex_annuel']
            resultat.cout_kwh = meilleures_infos_eco['cout_kwh']
            resultat.payback_annees = meilleures_infos_eco['payback_annees']
        
        return resultat
    
    def _generer_recommandations(
        self,
        pv_kwc: float,
        batterie_kwh: float,
        resultats: Dict,
        infos_eco: Optional[Dict]
    ) -> List[str]:
        """
        Génère des recommandations textuelles.
        """
        recos = []
        
        # Recommandation principale
        recos.append(
            f"Configuration optimale : {pv_kwc:.0f} kWc PV + {batterie_kwh:.0f} kWh batterie"
        )
        
        # Panneaux nécessaires (approximation 545W par panneau)
        nb_panneaux = int(np.ceil(pv_kwc * 1000 / 545))
        recos.append(f"Nombre de panneaux 545W recommandé : {nb_panneaux} unités")
        
        # Surface nécessaire
        surface = pv_kwc * 5  # ~5 m² par kWc
        recos.append(f"Surface toiture nécessaire : environ {surface:.0f} m²")
        
        # Batteries (approximation 200Ah 12V = 2.4 kWh)
        if batterie_kwh > 0:
            nb_batteries_200ah = int(np.ceil(batterie_kwh / 2.4))
            recos.append(f"Batteries 200Ah 12V recommandées : {nb_batteries_200ah} unités")
        
        # Autonomie
        recos.append(
            f"Autonomie estimée : {resultats['heures_autonomes']} heures/jour sans SBEE"
        )
        
        # Couverture
        if resultats['couverture'] >= 100:
            recos.append("✅ La charge est entièrement couverte")
        else:
            recos.append(f"⚠️ Couverture : {resultats['couverture']:.1f}% - SBEE nécessaire en complément")
        
        # Recommandations économiques
        if infos_eco:
            if infos_eco['payback_annees'] < 10:
                recos.append(f"💰 Investissement rentable : retour en {infos_eco['payback_annees']:.1f} ans")
            elif infos_eco['payback_annees'] < 15:
                recos.append(f"💰 Investissement acceptable : retour en {infos_eco['payback_annees']:.1f} ans")
            else:
                recos.append(f"⚠️ Retour sur investissement long : {infos_eco['payback_annees']:.1f} ans")
            
            recos.append(f"Coût du kWh produit : {infos_eco['cout_kwh']:.0f} FCFA")
        
        # Onduleur recommandé
        puissance_onduleur = max(pv_kwc, self.charge_max_kw) * 1.2
        nb_onduleurs_5kva = int(np.ceil(puissance_onduleur / 5))
        recos.append(f"Onduleur recommandé : {nb_onduleurs_5kva}x Quattro 5kVA ou équivalent")
        
        return recos


def generer_rapport_optimisation_pdf(resultat: ResultatOptimisation, config_charge: Dict) -> bytes:
    """
    Génère un rapport PDF pour les recommandations d'optimisation.
    
    Args:
        resultat: Résultat de l'optimisation
        config_charge: Configuration de la charge
    
    Returns:
        bytes: Contenu du PDF
    """
    from fpdf import FPDF
    from datetime import datetime
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Titre
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(0, 100, 50)
    pdf.cell(0, 15, 'RAPPORT D\'OPTIMISATION', 0, 1, 'C')
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, 'Dimensionnement Optimal du Micro-Reseau Hybride', 0, 1, 'C')
    pdf.cell(0, 8, f'Date: {datetime.now().strftime("%d/%m/%Y a %H:%M")}', 0, 1, 'C')
    pdf.ln(10)
    
    # Section 1 : Profil de charge analysé
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 80, 120)
    pdf.cell(0, 10, '1. PROFIL DE CHARGE ANALYSE', 0, 1, 'L')
    pdf.set_draw_color(0, 100, 150)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(80, 6, f"  Type de charge", 0, 0)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(60, 6, f"{config_charge.get('type', 'Non specifie')}", 0, 1)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(80, 6, f"  Puissance maximale", 0, 0)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(60, 6, f"{config_charge.get('puissance_max', 0):.1f} kW", 0, 1)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(80, 6, f"  Energie journaliere", 0, 0)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(60, 6, f"{config_charge.get('energie_jour', 0):.1f} kWh/jour", 0, 1)
    pdf.ln(5)
    
    # Section 2 : Configuration optimale
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 80, 120)
    pdf.cell(0, 10, '2. CONFIGURATION OPTIMALE RECOMMANDEE', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Encadré PV
    pdf.set_fill_color(255, 250, 200)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(90, 10, '  Puissance PV', 1, 0, 'L', True)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(90, 10, f"{resultat.pv_optimal_kwc:.0f} kWc", 1, 1, 'C', True)
    
    # Encadré Batterie
    pdf.set_fill_color(200, 230, 255)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(90, 10, '  Capacite Batterie', 1, 0, 'L', True)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(90, 10, f"{resultat.batterie_optimal_kwh:.0f} kWh", 1, 1, 'C', True)
    pdf.ln(5)
    
    # Performances
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(80, 6, f"  Couverture de la charge", 0, 0)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(60, 6, f"{resultat.couverture_pourcent:.1f}%", 0, 1)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(80, 6, f"  Autonomie journaliere", 0, 0)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(60, 6, f"{resultat.autonomie_heures} heures", 0, 1)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(80, 6, f"  Score d'optimisation", 0, 0)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(60, 6, f"{resultat.score:.0f}/100", 0, 1)
    pdf.ln(5)
    
    # Section 3 : Coûts (si disponibles)
    if resultat.capex_total:
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(0, 80, 120)
        pdf.cell(0, 10, '3. ESTIMATION DES COUTS', 0, 1, 'L')
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_fill_color(200, 255, 200)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(90, 10, '  Investissement (CAPEX)', 1, 0, 'L', True)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(90, 10, f"{resultat.capex_total:,.0f} FCFA", 1, 1, 'R', True)
        
        pdf.set_fill_color(255, 230, 200)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(90, 10, '  Exploitation annuelle (OPEX)', 1, 0, 'L', True)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(90, 10, f"{resultat.opex_annuel:,.0f} FCFA/an", 1, 1, 'R', True)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)
        pdf.cell(80, 6, f"  Cout du kWh", 0, 0)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(60, 6, f"{resultat.cout_kwh:.0f} FCFA/kWh", 0, 1)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(80, 6, f"  Retour sur investissement", 0, 0)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(60, 6, f"{resultat.payback_annees:.1f} ans", 0, 1)
        pdf.ln(5)
    
    # Section 4 : Recommandations
    section_num = 4 if resultat.capex_total else 3
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 80, 120)
    pdf.cell(0, 10, f'{section_num}. RECOMMANDATIONS DETAILLEES', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(0, 0, 0)
    
    for i, reco in enumerate(resultat.recommandations, 1):
        pdf.multi_cell(0, 6, f"  {i}. {reco}")
        pdf.ln(2)
    
    pdf.ln(5)
    
    # Conclusion
    section_num += 1
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(0, 80, 120)
    pdf.cell(0, 10, f'{section_num}. CONCLUSION', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    if resultat.couverture_pourcent >= 95 and (resultat.payback_annees is None or resultat.payback_annees < 15):
        conclusion = f"""Cette configuration de {resultat.pv_optimal_kwc:.0f} kWc PV et {resultat.batterie_optimal_kwh:.0f} kWh de batterie est recommandee pour votre installation.

Elle permet de couvrir {resultat.couverture_pourcent:.1f}% de vos besoins energetiques avec une autonomie de {resultat.autonomie_heures} heures par jour sans reseau SBEE."""
    else:
        conclusion = f"""Cette configuration represente le meilleur compromis trouve pour votre profil de charge.

Des ajustements peuvent etre necessaires selon vos contraintes specifiques de budget ou d'espace disponible."""
    
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 6, conclusion)
    pdf.ln(10)
    
    # Signature
    pdf.set_font('Helvetica', 'I', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, 'Rapport genere par Digital Twin Micro-Reseau Hybride - Benin 2025', 0, 1, 'C')
    
    return bytes(pdf.output())