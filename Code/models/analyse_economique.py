"""
Module d'Analyse Économique pour Micro-Réseau Hybride
======================================================

Ce module calcule tous les indicateurs économiques d'un système hybride
PV-Batterie-SBEE-Diesel pour le contexte béninois.

Auteur: Master Énergie
Date: Janvier 2025
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class ParametresEconomiques:
    """
    Paramètres économiques pour l'analyse financière.
    Tous les coûts sont en FCFA (Franc CFA).
    
    Valeurs par défaut basées sur le marché béninois (2025).
    """
    # CAPEX (Coûts d'investissement) - PRIX RÉELS BÉNIN
    cout_pv_par_wc: float = 300.0                     # FCFA/Wc (545W à 165 000F)
    cout_batterie_lithium_par_kwh: float = 200000.0   # FCFA/kWh (estimation marché)
    cout_batterie_plomb_par_kwh: float = 90000.0      # FCFA/kWh (200Ah à 218 000F)
    cout_onduleur_par_kw: float = 240000.0            # FCFA/kW (Quattro 5kVA à 1 250 000F)
    cout_regulateur_mppt: float = 575000.0            # FCFA (MPPT 250/100 Victron)
    cout_diesel_par_kw: float = 200000.0              # FCFA/kW (groupes standards)
    taux_installation: float = 0.15                    # 15% du matériel (main d'œuvre Bénin)
    
    # OPEX (Coûts d'exploitation annuels)
    taux_maintenance_pv: float = 0.01                 # 1% CAPEX_PV/an (climat Bénin)
    taux_maintenance_batterie: float = 0.02           # 2% CAPEX_Bat/an
    taux_maintenance_diesel: float = 0.05             # 5% CAPEX_Diesel/an (usure tropicale)
    
    # Remplacement
    duree_vie_batterie_lithium: int = 12              # années (climat Bénin)
    duree_vie_batterie_plomb: int = 4                 # années (chaleur accélère vieillissement)
    duree_vie_onduleur: int = 15                      # années
    duree_vie_regulateur: int = 15                    # années
    
    # Diesel
    prix_diesel_litre: float = 675.0                  # FCFA/L (prix Bénin 2025)
    consommation_diesel_l_par_kwh: float = 0.28       # L/kWh
    
    # SBEE (Société Béninoise d'Énergie Électrique)
    tarif_sbee_kwh: float = 115.0                     # FCFA/kWh (tarif moyen Bénin)
    
    # Paramètres financiers
    duree_vie_projet: int = 25                        # années
    taux_actualisation: float = 0.08                  # 8% (contexte UEMOA/BCEAO)
    taux_inflation: float = 0.03                      # 3% (moyenne UEMOA)


@dataclass
class ResultatsEconomiques:
    """
    Résultats de l'analyse économique.
    """
    # CAPEX (Investissement initial)
    capex_pv: float
    capex_regulateur: float
    capex_batterie: float
    capex_onduleur: float
    capex_diesel: float
    capex_installation: float
    capex_total: float
    
    # OPEX (Coûts annuels)
    opex_maintenance_pv: float
    opex_maintenance_batterie: float
    opex_maintenance_diesel: float
    opex_carburant_diesel: float
    opex_electricite_sbee: float
    opex_total_annuel: float
    
    # Coûts de remplacement
    cout_remplacement_batterie: float
    cout_remplacement_onduleur: float
    annees_remplacement_batterie: List[int]
    annees_remplacement_onduleur: List[int]
    
    # Économies
    cout_reference_100_sbee: float              # Coût sur 25 ans si 100% SBEE
    cout_reference_100_diesel: float            # Coût sur 25 ans si 100% Diesel
    economie_vs_sbee: float                     # Économie vs 100% SBEE
    economie_vs_diesel: float                   # Économie vs 100% Diesel
    economie_annuelle_moyenne: float            # Économie moyenne par an
    
    # Indicateurs financiers
    cout_total_actualise: float                 # Coût total sur 25 ans (actualisé)
    cout_kwh_actualise: float                   # Coût du kWh produit (actualisé)
    roi_pourcent: float                         # Return on Investment (%)
    payback_annees: float                       # Temps de retour sur investissement
    van: float                                  # Valeur Actuelle Nette
    tir: float                                  # Taux Interne de Rentabilité


class AnalyseurEconomique:
    """
    Analyseur économique pour systèmes hybrides.
    
    Calcule tous les indicateurs économiques : CAPEX, OPEX, ROI, Payback, VAN, TIR
    """
    
    def __init__(self, params: ParametresEconomiques):
        """
        Initialise l'analyseur avec les paramètres économiques.
        
        Args:
            params: Paramètres économiques (coûts, taux, durées)
        """
        self.params = params
    
    def calculer_capex(
        self,
        puissance_pv_wc: float,
        capacite_batterie_kwh: float,
        type_batterie: str,
        puissance_onduleur_kw: float,
        puissance_diesel_kw: float,
        diesel_actif: bool
    ) -> Dict[str, float]:
        """
        Calcule les coûts d'investissement (CAPEX).
        
        Args:
            puissance_pv_wc: Puissance PV installée (Wc)
            capacite_batterie_kwh: Capacité batterie (kWh)
            type_batterie: 'Lithium-ion' ou 'Plomb-acide'
            puissance_onduleur_kw: Puissance onduleur (kW)
            puissance_diesel_kw: Puissance groupe diesel (kW)
            diesel_actif: Si le diesel est installé
        
        Returns:
            Dictionnaire avec détails CAPEX
        """
        # PV
        capex_pv = puissance_pv_wc * self.params.cout_pv_par_wc
        
        # Régulateur MPPT (1 pour systèmes < 50 kWc, plus pour grands systèmes)
        nb_regulateurs = max(1, int(puissance_pv_wc / 50000) + 1)
        capex_regulateur = nb_regulateurs * self.params.cout_regulateur_mppt
        
        # Batterie
        if type_batterie == 'Lithium-ion':
            cout_kwh = self.params.cout_batterie_lithium_par_kwh
        else:  # Plomb-acide
            cout_kwh = self.params.cout_batterie_plomb_par_kwh
        capex_batterie = capacite_batterie_kwh * cout_kwh
        
        # Onduleur (Quattro pour hybride)
        capex_onduleur = puissance_onduleur_kw * self.params.cout_onduleur_par_kw
        
        # Diesel
        capex_diesel = 0.0
        if diesel_actif:
            capex_diesel = puissance_diesel_kw * self.params.cout_diesel_par_kw
        
        # Installation
        capex_materiel = capex_pv + capex_regulateur + capex_batterie + capex_onduleur + capex_diesel
        capex_installation = capex_materiel * self.params.taux_installation
        
        # Total
        capex_total = capex_materiel + capex_installation
        
        return {
            'capex_pv': capex_pv,
            'capex_regulateur': capex_regulateur,
            'capex_batterie': capex_batterie,
            'capex_onduleur': capex_onduleur,
            'capex_diesel': capex_diesel,
            'capex_installation': capex_installation,
            'capex_total': capex_total
        }
    
    def calculer_opex_annuel(
        self,
        capex: Dict[str, float],
        energie_diesel_kwh_an: float,
        energie_sbee_kwh_an: float,
        diesel_actif: bool
    ) -> Dict[str, float]:
        """
        Calcule les coûts d'exploitation annuels (OPEX).
        
        Args:
            capex: Dictionnaire avec CAPEX de chaque composant
            energie_diesel_kwh_an: Énergie diesel consommée (kWh/an)
            energie_sbee_kwh_an: Énergie SBEE consommée (kWh/an)
            diesel_actif: Si le diesel est utilisé
        
        Returns:
            Dictionnaire avec détails OPEX annuel
        """
        # Maintenance
        opex_maintenance_pv = capex['capex_pv'] * self.params.taux_maintenance_pv
        opex_maintenance_batterie = capex['capex_batterie'] * self.params.taux_maintenance_batterie
        opex_maintenance_diesel = 0.0
        if diesel_actif:
            opex_maintenance_diesel = capex['capex_diesel'] * self.params.taux_maintenance_diesel
        
        # Carburant diesel
        litres_diesel = energie_diesel_kwh_an * self.params.consommation_diesel_l_par_kwh
        opex_carburant = litres_diesel * self.params.prix_diesel_litre
        
        # Électricité SBEE
        opex_sbee = energie_sbee_kwh_an * self.params.tarif_sbee_kwh
        
        # Total annuel
        opex_total = (opex_maintenance_pv + opex_maintenance_batterie + 
                     opex_maintenance_diesel + opex_carburant + opex_sbee)
        
        return {
            'opex_maintenance_pv': opex_maintenance_pv,
            'opex_maintenance_batterie': opex_maintenance_batterie,
            'opex_maintenance_diesel': opex_maintenance_diesel,
            'opex_carburant_diesel': opex_carburant,
            'opex_electricite_sbee': opex_sbee,
            'opex_total_annuel': opex_total
        }
    
    def calculer_remplacements(
        self,
        type_batterie: str,
        capex_batterie: float,
        capex_onduleur: float
    ) -> Dict[str, any]:
        """
        Calcule les coûts et années de remplacement.
        
        Args:
            type_batterie: Type de batterie
            capex_batterie: Coût initial batterie
            capex_onduleur: Coût initial onduleur
        
        Returns:
            Dictionnaire avec infos remplacements
        """
        # Durée de vie batterie
        if type_batterie == 'Lithium-ion':
            duree_vie_bat = self.params.duree_vie_batterie_lithium
        else:
            duree_vie_bat = self.params.duree_vie_batterie_plomb
        
        # Années de remplacement
        annees_rempl_bat = [duree_vie_bat * i for i in range(1, self.params.duree_vie_projet // duree_vie_bat + 1)]
        annees_rempl_ond = [self.params.duree_vie_onduleur * i for i in range(1, self.params.duree_vie_projet // self.params.duree_vie_onduleur + 1)]
        
        # Coûts (actualisés)
        cout_rempl_bat = sum([capex_batterie / ((1 + self.params.taux_actualisation) ** annee) 
                             for annee in annees_rempl_bat])
        cout_rempl_ond = sum([capex_onduleur / ((1 + self.params.taux_actualisation) ** annee) 
                             for annee in annees_rempl_ond])
        
        return {
            'cout_remplacement_batterie': cout_rempl_bat,
            'cout_remplacement_onduleur': cout_rempl_ond,
            'annees_remplacement_batterie': annees_rempl_bat,
            'annees_remplacement_onduleur': annees_rempl_ond
        }
    
    def calculer_cout_total_actualise(
        self,
        capex_total: float,
        opex_annuel: float,
        cout_remplacements: float
    ) -> float:
        """
        Calcule le coût total actualisé sur la durée de vie.
        
        Args:
            capex_total: Investissement initial
            opex_annuel: Coût d'exploitation annuel
            cout_remplacements: Coûts de remplacement actualisés
        
        Returns:
            Coût total actualisé (FCFA)
        """
        # OPEX actualisé sur toute la durée
        opex_actualise = sum([
            opex_annuel * ((1 + self.params.taux_inflation) ** annee) / 
            ((1 + self.params.taux_actualisation) ** annee)
            for annee in range(1, self.params.duree_vie_projet + 1)
        ])
        
        # Total
        cout_total = capex_total + opex_actualise + cout_remplacements
        
        return cout_total
    
    def calculer_scenarios_reference(
        self,
        energie_totale_kwh_an: float
    ) -> Tuple[float, float]:
        """
        Calcule les coûts de référence (100% SBEE ou 100% Diesel).
        
        Args:
            energie_totale_kwh_an: Énergie totale consommée (kWh/an)
        
        Returns:
            Tuple (coût_100_SBEE, coût_100_Diesel) actualisés sur 25 ans
        """
        # Scénario 100% SBEE
        cout_annuel_sbee = energie_totale_kwh_an * self.params.tarif_sbee_kwh
        cout_total_sbee = sum([
            cout_annuel_sbee * ((1 + self.params.taux_inflation) ** annee) /
            ((1 + self.params.taux_actualisation) ** annee)
            for annee in range(1, self.params.duree_vie_projet + 1)
        ])
        
        # Scénario 100% Diesel (avec CAPEX groupe + maintenance + carburant)
        puissance_diesel_necessaire = energie_totale_kwh_an / 8760  # kW moyen
        capex_diesel_ref = puissance_diesel_necessaire * self.params.cout_diesel_par_kw
        
        litres_an = energie_totale_kwh_an * self.params.consommation_diesel_l_par_kwh
        cout_carburant_an = litres_an * self.params.prix_diesel_litre
        cout_maintenance_an = capex_diesel_ref * self.params.taux_maintenance_diesel
        opex_diesel_an = cout_carburant_an + cout_maintenance_an
        
        opex_diesel_actualise = sum([
            opex_diesel_an * ((1 + self.params.taux_inflation) ** annee) /
            ((1 + self.params.taux_actualisation) ** annee)
            for annee in range(1, self.params.duree_vie_projet + 1)
        ])
        
        cout_total_diesel = capex_diesel_ref + opex_diesel_actualise
        
        return cout_total_sbee, cout_total_diesel
    
    def analyser_systeme_complet(
        self,
        # Configuration système
        puissance_pv_wc: float,
        capacite_batterie_kwh: float,
        type_batterie: str,
        puissance_onduleur_kw: float,
        puissance_diesel_kw: float,
        diesel_actif: bool,
        # Résultats simulation 24h
        energie_pv_kwh: float,
        energie_batterie_kwh: float,
        energie_sbee_kwh: float,
        energie_diesel_kwh: float,
        energie_charge_totale_kwh: float
    ) -> ResultatsEconomiques:
        """
        Analyse économique complète du système.
        
        Args:
            Configuration et résultats de simulation
        
        Returns:
            ResultatsEconomiques avec tous les indicateurs
        """
        # Énergies annuelles (extrapoler 24h → 365 jours)
        energie_diesel_an = energie_diesel_kwh * 365
        energie_sbee_an = energie_sbee_kwh * 365
        energie_totale_an = energie_charge_totale_kwh * 365
        
        # 1. CAPEX
        capex = self.calculer_capex(
            puissance_pv_wc, capacite_batterie_kwh, type_batterie,
            puissance_onduleur_kw, puissance_diesel_kw, diesel_actif
        )
        
        # 2. OPEX annuel
        opex = self.calculer_opex_annuel(capex, energie_diesel_an, energie_sbee_an, diesel_actif)
        
        # 3. Remplacements
        remplacements = self.calculer_remplacements(
            type_batterie, capex['capex_batterie'], capex['capex_onduleur']
        )
        
        # 4. Coût total actualisé
        cout_total_actualise = self.calculer_cout_total_actualise(
            capex['capex_total'],
            opex['opex_total_annuel'],
            remplacements['cout_remplacement_batterie'] + remplacements['cout_remplacement_onduleur']
        )
        
        # 5. Coût du kWh
        energie_totale_25ans = energie_totale_an * self.params.duree_vie_projet
        cout_kwh = cout_total_actualise / energie_totale_25ans if energie_totale_25ans > 0 else 0
        
        # 6. Scénarios de référence
        cout_ref_sbee, cout_ref_diesel = self.calculer_scenarios_reference(energie_totale_an)
        
        # 7. Économies
        economie_vs_sbee = cout_ref_sbee - cout_total_actualise
        economie_vs_diesel = cout_ref_diesel - cout_total_actualise
        economie_annuelle = economie_vs_sbee / self.params.duree_vie_projet
        
        # 8. ROI et Payback
        if economie_annuelle > 0:
            payback = capex['capex_total'] / economie_annuelle
            roi = (economie_vs_sbee / capex['capex_total']) * 100
        else:
            payback = float('inf')
            roi = -100
        
        # 9. VAN (Valeur Actuelle Nette)
        van = economie_vs_sbee
        
        # 10. TIR (approximation simple)
        tir = (economie_annuelle / capex['capex_total']) if capex['capex_total'] > 0 else 0
        
        return ResultatsEconomiques(
            # CAPEX
            capex_pv=capex['capex_pv'],
            capex_regulateur=capex['capex_regulateur'],
            capex_batterie=capex['capex_batterie'],
            capex_onduleur=capex['capex_onduleur'],
            capex_diesel=capex['capex_diesel'],
            capex_installation=capex['capex_installation'],
            capex_total=capex['capex_total'],
            # OPEX
            opex_maintenance_pv=opex['opex_maintenance_pv'],
            opex_maintenance_batterie=opex['opex_maintenance_batterie'],
            opex_maintenance_diesel=opex['opex_maintenance_diesel'],
            opex_carburant_diesel=opex['opex_carburant_diesel'],
            opex_electricite_sbee=opex['opex_electricite_sbee'],
            opex_total_annuel=opex['opex_total_annuel'],
            # Remplacements
            cout_remplacement_batterie=remplacements['cout_remplacement_batterie'],
            cout_remplacement_onduleur=remplacements['cout_remplacement_onduleur'],
            annees_remplacement_batterie=remplacements['annees_remplacement_batterie'],
            annees_remplacement_onduleur=remplacements['annees_remplacement_onduleur'],
            # Économies
            cout_reference_100_sbee=cout_ref_sbee,
            cout_reference_100_diesel=cout_ref_diesel,
            economie_vs_sbee=economie_vs_sbee,
            economie_vs_diesel=economie_vs_diesel,
            economie_annuelle_moyenne=economie_annuelle,
            # Indicateurs
            cout_total_actualise=cout_total_actualise,
            cout_kwh_actualise=cout_kwh,
            roi_pourcent=roi,
            payback_annees=payback,
            van=van,
            tir=tir
        )