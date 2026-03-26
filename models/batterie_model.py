"""
MODÈLE MATHÉMATIQUE DE LA BATTERIE
===================================

Auteur: Votre Nom
Projet: Gestion Automatique d'un Micro-Réseau Hybride PV-SBEE-Diesel
"""

from dataclasses import dataclass
from typing import Literal

@dataclass
class ParametresBatterie:
    """Paramètres de la batterie de stockage"""
    tension: Literal[12, 24, 48] = 24  # V
    type_batterie: Literal['Lithium-ion', 'Plomb-acide', 'Gel'] = 'Lithium-ion'
    capacite_ah: float = 500  # Ah
    profondeur_decharge: float = 0.8  # 80%
    efficacite_charge: float = 0.95  # 95%
    efficacite_decharge: float = 0.95  # 95%
    etat_charge_initial: float = 0.5  # 50% au départ


class ModeleBatterie:
    """Modèle mathématique de la batterie"""
    
    def __init__(self, parametres: ParametresBatterie):
        self.params = parametres
        self.etat_charge = parametres.etat_charge_initial  # SOC (State of Charge)
    
    def energie_stockee_max(self) -> float:
        """Calcule l'énergie maximale stockable (kWh)"""
        return (self.params.capacite_ah * self.params.tension) / 1000
    
    def energie_utilisable(self) -> float:
        """Calcule l'énergie réellement utilisable (kWh)"""
        return self.energie_stockee_max() * self.params.profondeur_decharge
    
    def energie_actuelle(self) -> float:
        """Calcule l'énergie actuellement stockée (kWh)"""
        return self.energie_stockee_max() * self.etat_charge
    
    def peut_fournir(self, puissance_kw: float, duree_h: float) -> bool:
        """Vérifie si la batterie peut fournir une certaine puissance pendant une durée"""
        energie_demandee = puissance_kw * duree_h
        energie_disponible = self.energie_actuelle() * self.params.efficacite_decharge
        return energie_disponible >= energie_demandee
    
    def decharger(self, puissance_kw: float, duree_h: float) -> dict:
        """
        Décharge la batterie
        
        Returns:
            dict avec 'success', 'energie_fournie', 'nouveau_soc'
        """
        energie_demandee = puissance_kw * duree_h
        energie_disponible = self.energie_actuelle() * self.params.efficacite_decharge
        
        if energie_disponible >= energie_demandee:
            # Décharge complète possible
            energie_prelevee = energie_demandee / self.params.efficacite_decharge
            self.etat_charge -= energie_prelevee / self.energie_stockee_max()
            return {
                'success': True,
                'energie_fournie': energie_demandee,
                'nouveau_soc': self.etat_charge,
                'deficit': 0
            }
        else:
            # Décharge partielle
            energie_fournie = energie_disponible
            self.etat_charge = 0
            return {
                'success': False,
                'energie_fournie': energie_fournie,
                'nouveau_soc': 0,
                'deficit': energie_demandee - energie_fournie
            }
    
    def charger(self, puissance_kw: float, duree_h: float) -> dict:
        """
        Charge la batterie
        
        Returns:
            dict avec 'success', 'energie_stockee', 'nouveau_soc'
        """
        energie_apportee = puissance_kw * duree_h * self.params.efficacite_charge
        energie_max = self.energie_stockee_max()
        energie_actuelle = self.energie_actuelle()
        
        espace_disponible = energie_max - energie_actuelle
        
        if espace_disponible >= energie_apportee:
            # Charge complète possible
            self.etat_charge += energie_apportee / energie_max
            return {
                'success': True,
                'energie_stockee': energie_apportee,
                'nouveau_soc': self.etat_charge,
                'surplus': 0
            }
        else:
            # Charge partielle (batterie pleine)
            self.etat_charge = 1.0
            return {
                'success': False,
                'energie_stockee': espace_disponible,
                'nouveau_soc': 1.0,
                'surplus': energie_apportee - espace_disponible
            }
    
    def autonomie_estimee(self, puissance_charge_kw: float) -> float:
        """Estime l'autonomie en heures pour une charge donnée"""
        if puissance_charge_kw <= 0:
            return float('inf')
        energie_disponible = self.energie_actuelle() * self.params.efficacite_decharge
        return energie_disponible / puissance_charge_kw
    
    def reset(self, soc: float = 0.5):
        """Réinitialise l'état de charge"""
        self.etat_charge = soc