"""
GESTIONNAIRE D'ÉNERGIE - SYSTÈME DE GESTION AUTOMATIQUE
========================================================

Ce module contient la logique de gestion automatique du micro-réseau hybride.
Il détermine quelle source d'énergie doit être active selon les priorités :
1. PV (photovoltaïque) - Priorité 1
2. Batterie (stockage) - Priorité 2
3. SBEE (réseau national) - Priorité 3
4. Diesel (générateur) - Priorité 4 (secours)

Auteur: Votre Nom
Projet: Gestion Automatique d'un Micro-Réseau Hybride PV-SBEE-Diesel
"""

from dataclasses import dataclass
from typing import Literal, Optional
from datetime import datetime


@dataclass
class EtatSysteme:
    """État actuel du système énergétique"""
    production_pv_kw: float
    charge_demandee_kw: float
    pv_actif: bool
    sbee_disponible: bool
    puissance_sbee_kw: float
    diesel_actif: bool
    puissance_diesel_kw: float
    heure_actuelle: int


@dataclass
class FluxBatterie:
    """Résultat du flux de la batterie"""
    surplus_vers_batterie: float = 0.0  # kW chargé dans la batterie
    deficit_depuis_batterie: float = 0.0  # kW fourni par la batterie
    nouveau_soc: float = 0.5  # Nouveau State of Charge
    batterie_chargee: bool = False
    batterie_dechargee: bool = False


@dataclass
class DecisionGestion:
    """Décision prise par le gestionnaire"""
    source_principale: Literal['PV', 'SBEE', 'Diesel', 'PV+SBEE', 'PV+Diesel', 'SBEE+Diesel']
    sources_actives: list
    puissance_pv_utilisee: float
    puissance_sbee_utilisee: float
    puissance_diesel_utilisee: float
    deficit: float
    surplus: float
    raison: str
    icone: str


class GestionnaireEnergie:
    """
    Gestionnaire intelligent du micro-réseau hybride.
    
    Stratégie de gestion :
    ---------------------
    1. PV en priorité (gratuit, écologique)
    2. SBEE si PV insuffisant (fiable, pas de maintenance)
    3. Diesel en dernier recours (coûteux, polluant)
    
    Règles de gestion :
    ------------------
    - Jour (6h-18h) : Privilégier PV si ensoleillement suffisant
    - Nuit (18h-6h) : SBEE prioritaire, Diesel si panne SBEE
    - Toujours : Diesel démarre automatiquement si PV + SBEE insuffisants
    """
    
    def __init__(self):
        """Initialise le gestionnaire d'énergie"""
        self.historique_decisions = []
    
    def decider_source_active(self, etat: EtatSysteme) -> DecisionGestion:
        """
        Détermine quelle(s) source(s) doit/doivent être active(s).
        
        Algorithme de décision OPTION A (Universel) :
        --------------------------------------------
        1. PV en priorité (gratuit, écologique) - SI ACTIVÉ
        2. SBEE si PV insuffisant (fiable) - SI DISPONIBLE
        3. Diesel en dernier recours (coûteux, avec charge minimale 30%) - SI ACTIVÉ
        
        Règles critiques :
        - PV utilisé seulement si activé
        - Diesel démarre SEULEMENT si déficit ≥ 30% de sa puissance nominale
        - Sinon : délestage (charge non couverte)
        
        Args:
            etat: État actuel du système
        
        Returns:
            Décision détaillant les sources à utiliser
        """
        charge = etat.charge_demandee_kw
        pv = etat.production_pv_kw if etat.pv_actif else 0  # PV = 0 si non activé
        
        # ============================================================
        # CAS 1 : PV couvre entièrement la charge
        # ============================================================
        if pv >= charge:
            surplus = pv - charge
            return DecisionGestion(
                source_principale='PV',
                sources_actives=['PV'],
                puissance_pv_utilisee=charge,
                puissance_sbee_utilisee=0,
                puissance_diesel_utilisee=0,
                deficit=0,
                surplus=surplus,
                raison=f"PV couvre 100% ({charge:.1f} kW)",
                icone="🌞"
            )
        
        # ============================================================
        # CAS 2 : PV insuffisant, besoin de complément
        # ============================================================
        deficit = charge - pv
        
        # ------------------------------------------------------------
        # SOUS-CAS 2A : SBEE disponible
        # ------------------------------------------------------------
        if etat.sbee_disponible:
            if deficit <= etat.puissance_sbee_kw:
                # SBEE peut couvrir le déficit
                if pv > 0:
                    source = 'PV+SBEE'
                    icone = "🌞🔌"
                    raison = f"PV ({pv:.1f} kW) + SBEE ({deficit:.1f} kW)"
                else:
                    source = 'SBEE'
                    icone = "🔌"
                    raison = f"SBEE couvre 100% ({charge:.1f} kW)"
                
                return DecisionGestion(
                    source_principale=source,
                    sources_actives=['PV', 'SBEE'] if pv > 0 else ['SBEE'],
                    puissance_pv_utilisee=pv,
                    puissance_sbee_utilisee=deficit,
                    puissance_diesel_utilisee=0,
                    deficit=0,
                    surplus=0,
                    raison=raison,
                    icone=icone
                )
            else:
                # SBEE insuffisant, besoin de Diesel
                deficit_apres_sbee = deficit - etat.puissance_sbee_kw
                
                # Vérifier si le Diesel est activé
                if not etat.diesel_actif:
                    # Diesel non activé
                    sources = []
                    if pv > 0: sources.append('PV')
                    sources.append('SBEE')
                    
                    return DecisionGestion(
                        source_principale='PV+SBEE' if pv > 0 else 'SBEE',
                        sources_actives=sources,
                        puissance_pv_utilisee=pv,
                        puissance_sbee_utilisee=etat.puissance_sbee_kw,
                        puissance_diesel_utilisee=0,
                        deficit=deficit_apres_sbee,
                        surplus=0,
                        raison=f"⚠️ SBEE max ({etat.puissance_sbee_kw:.1f} kW) + Diesel non activé ! Déficit : {deficit_apres_sbee:.1f} kW",
                        icone="🌞🔌❌" if pv > 0 else "🔌❌"
                    )
                
                # VÉRIFICATION CHARGE MINIMALE DIESEL (30%)
                charge_min_diesel = etat.puissance_diesel_kw * 0.30  # 30% minimum
                
                if deficit_apres_sbee >= charge_min_diesel:
                    # Diesel peut démarrer (charge suffisante)
                    if deficit_apres_sbee <= etat.puissance_diesel_kw:
                        # Diesel couvre le reste
                        sources = []
                        if pv > 0: sources.append('PV')
                        sources.extend(['SBEE', 'Diesel'])
                        
                        return DecisionGestion(
                            source_principale='PV+SBEE+Diesel' if pv > 0 else 'SBEE+Diesel',
                            sources_actives=sources,
                            puissance_pv_utilisee=pv,
                            puissance_sbee_utilisee=etat.puissance_sbee_kw,
                            puissance_diesel_utilisee=deficit_apres_sbee,
                            deficit=0,
                            surplus=0,
                            raison=f"3 sources : PV ({pv:.1f}) + SBEE ({etat.puissance_sbee_kw:.1f}) + Diesel ({deficit_apres_sbee:.1f})",
                            icone="🌞🔌🛢️" if pv > 0 else "🔌🛢️"
                        )
                    else:
                        # Diesel à fond, mais encore insuffisant
                        deficit_final = deficit_apres_sbee - etat.puissance_diesel_kw
                        sources = []
                        if pv > 0: sources.append('PV')
                        sources.extend(['SBEE', 'Diesel'])
                        
                        return DecisionGestion(
                            source_principale='PV+SBEE+Diesel' if pv > 0 else 'SBEE+Diesel',
                            sources_actives=sources,
                            puissance_pv_utilisee=pv,
                            puissance_sbee_utilisee=etat.puissance_sbee_kw,
                            puissance_diesel_utilisee=etat.puissance_diesel_kw,
                            deficit=deficit_final,
                            surplus=0,
                            raison=f"⚠️ Toutes sources max ! Déficit : {deficit_final:.1f} kW",
                            icone="🌞🔌🛢️❌" if pv > 0 else "🔌🛢️❌"
                        )
                else:
                    # Déficit trop faible pour Diesel (< 30% charge minimale)
                    sources = []
                    if pv > 0: sources.append('PV')
                    sources.append('SBEE')
                    
                    return DecisionGestion(
                        source_principale='PV+SBEE' if pv > 0 else 'SBEE',
                        sources_actives=sources,
                        puissance_pv_utilisee=pv,
                        puissance_sbee_utilisee=etat.puissance_sbee_kw,
                        puissance_diesel_utilisee=0,
                        deficit=deficit_apres_sbee,
                        surplus=0,
                        raison=f"⚠️ Déficit {deficit_apres_sbee:.1f} kW trop faible pour Diesel (min: {charge_min_diesel:.1f} kW)",
                        icone="🌞🔌❌" if pv > 0 else "🔌❌"
                    )
        
        # ------------------------------------------------------------
        # SOUS-CAS 2B : SBEE indisponible, utiliser Diesel directement
        # ------------------------------------------------------------
        else:
            # Vérifier si le Diesel est activé
            if not etat.diesel_actif:
                # Diesel non activé, impossible de couvrir le déficit
                return DecisionGestion(
                    source_principale='PV' if pv > 0 else 'Aucune',
                    sources_actives=['PV'] if pv > 0 else [],
                    puissance_pv_utilisee=pv,
                    puissance_sbee_utilisee=0,
                    puissance_diesel_utilisee=0,
                    deficit=deficit,
                    surplus=0,
                    raison=f"⚠️ SBEE indispo + Diesel non activé ! Déficit : {deficit:.1f} kW",
                    icone="🌞❌" if pv > 0 else "❌"
                )
            
            # VÉRIFICATION CHARGE MINIMALE DIESEL
            charge_min_diesel = etat.puissance_diesel_kw * 0.30
            
            if deficit >= charge_min_diesel:
                # Diesel peut démarrer
                if deficit <= etat.puissance_diesel_kw:
                    # Diesel couvre le déficit
                    if pv > 0:
                        source = 'PV+Diesel'
                        icone = "🌞🛢️"
                        raison = f"PV ({pv:.1f} kW) + Diesel ({deficit:.1f} kW) - SBEE indispo"
                    else:
                        source = 'Diesel'
                        icone = "🛢️"
                        raison = f"Diesel seul ({charge:.1f} kW) - SBEE indispo"
                    
                    return DecisionGestion(
                        source_principale=source,
                        sources_actives=['PV', 'Diesel'] if pv > 0 else ['Diesel'],
                        puissance_pv_utilisee=pv,
                        puissance_sbee_utilisee=0,
                        puissance_diesel_utilisee=deficit,
                        deficit=0,
                        surplus=0,
                        raison=raison,
                        icone=icone
                    )
                else:
                    # Diesel insuffisant
                    deficit_final = deficit - etat.puissance_diesel_kw
                    return DecisionGestion(
                        source_principale='PV+Diesel' if pv > 0 else 'Diesel',
                        sources_actives=['PV', 'Diesel'] if pv > 0 else ['Diesel'],
                        puissance_pv_utilisee=pv,
                        puissance_sbee_utilisee=0,
                        puissance_diesel_utilisee=etat.puissance_diesel_kw,
                        deficit=deficit_final,
                        surplus=0,
                        raison=f"⚠️ PV + Diesel max ! Déficit : {deficit_final:.1f} kW",
                        icone="🌞🛢️❌" if pv > 0 else "🛢️❌"
                    )
            else:
                # Déficit trop faible pour Diesel
                return DecisionGestion(
                    source_principale='PV' if pv > 0 else 'Aucune',
                    sources_actives=['PV'] if pv > 0 else [],
                    puissance_pv_utilisee=pv,
                    puissance_sbee_utilisee=0,
                    puissance_diesel_utilisee=0,
                    deficit=deficit,
                    surplus=0,
                    raison=f"⚠️ SBEE indispo + Déficit {deficit:.1f} kW trop faible pour Diesel (min: {charge_min_diesel:.1f} kW)",
                    icone="🌞❌" if pv > 0 else "❌"
                )
    
    def calculer_bilan_energetique(self, etat: EtatSysteme) -> dict:
        """
        Calcule le bilan énergétique global du système.
        
        Returns:
            dict avec production totale, consommation, excédent/déficit
        """
        decision = self.decider_source_active(etat)
        
        production_totale = (decision.puissance_pv_utilisee + 
                           decision.puissance_sbee_utilisee + 
                           decision.puissance_diesel_utilisee)
        
        bilan = production_totale - etat.charge_demandee_kw
        
        return {
            'production_totale_kw': production_totale,
            'consommation_kw': etat.charge_demandee_kw,
            'bilan_kw': bilan,
            'type_bilan': 'Excédent' if bilan >= 0 else 'Déficit',
            'taux_couverture_pct': (production_totale / etat.charge_demandee_kw * 100) if etat.charge_demandee_kw > 0 else 0,
            'decision': decision
        }
    
    def enregistrer_decision(self, decision: DecisionGestion, timestamp: datetime = None):
        """Enregistre une décision dans l'historique"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.historique_decisions.append({
            'timestamp': timestamp,
            'decision': decision
        })
    
    def get_statistiques_utilisation(self) -> dict:
        """
        Calcule les statistiques d'utilisation des sources.
        
        Returns:
            dict avec pourcentages d'utilisation de chaque source
        """
        if not self.historique_decisions:
            return {
                'pv_pct': 0,
                'sbee_pct': 0,
                'diesel_pct': 0,
                'nombre_decisions': 0
            }
        
        total = len(self.historique_decisions)
        pv_count = sum(1 for h in self.historique_decisions if 'PV' in h['decision'].source_principale)
        sbee_count = sum(1 for h in self.historique_decisions if 'SBEE' in h['decision'].source_principale)
        diesel_count = sum(1 for h in self.historique_decisions if 'Diesel' in h['decision'].source_principale)
        
        return {
            'pv_pct': (pv_count / total * 100) if total > 0 else 0,
            'sbee_pct': (sbee_count / total * 100) if total > 0 else 0,
            'diesel_pct': (diesel_count / total * 100) if total > 0 else 0,
            'nombre_decisions': total
        }