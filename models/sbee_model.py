"""
MODÈLE MATHÉMATIQUE DU RÉSEAU SBEE
===================================

Modèle réaliste du réseau électrique national (SBEE - Bénin) avec :
- Profils de disponibilité réalistes sur 24h
- Scénarios de fiabilité (Stable, Normal, Instable)
- Simulation de coupures aux heures de pointe
- Tarification SBEE
- Statistiques de disponibilité

Auteur: Votre Nom
Projet: Gestion Automatique d'un Micro-Réseau Hybride PV-SBEE-Diesel
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Literal, List, Optional

@dataclass
class ParametresSBEE:
    """Paramètres du réseau SBEE"""
    puissance_max: float = 50.0  # kW
    tension_nominale: float = 220.0  # V
    frequence: float = 50.0  # Hz
    disponible: bool = True
    
    # Tarification SBEE (FCFA/kWh) - Approximation tarifs Bénin
    tarif_base: float = 100.0  # Tranche normale
    tarif_pointe: float = 120.0  # Heures de pointe (18h-22h)
    tarif_hors_pointe: float = 85.0  # Heures creuses (22h-6h)
    
    # Scénario de fiabilité
    scenario: Literal['stable', 'normal', 'instable'] = 'normal'
    
    # Mode de gestion des coupures
    mode_coupures: Literal['automatique', 'manuel'] = 'automatique'
    
    # Coupures manuelles (liste des heures où SBEE est indisponible)
    coupures_manuelles: List[int] = field(default_factory=list)


class ModeleSBEE:
    """
    Modèle mathématique réaliste du réseau SBEE.
    
    Scénarios de fiabilité :
    -----------------------
    - STABLE : 95% disponibilité, rares coupures courtes
    - NORMAL : 80% disponibilité, coupures fréquentes en soirée
    - INSTABLE : 60% disponibilité, coupures fréquentes et longues
    
    Profils de coupures réalistes :
    ------------------------------
    Au Bénin, les coupures SBEE sont plus fréquentes :
    - Heures de pointe (18h-22h) : forte demande
    - Après-midi chaud (14h-16h) : climatisation excessive
    - Nuit (2h-4h) : maintenance
    """
    
    # Profils de probabilité de coupure par heure (0-23h)
    PROFILS_COUPURES = {
        'stable': {  # 95% disponibilité moyenne
            'profil_24h': [
                0.02, 0.02, 0.03, 0.03, 0.02, 0.02,  # 0-5h : Nuit calme
                0.01, 0.01, 0.01, 0.02, 0.02, 0.03,  # 6-11h : Matin stable
                0.03, 0.04, 0.05, 0.04, 0.05, 0.06,  # 12-17h : Après-midi
                0.08, 0.10, 0.08, 0.06, 0.03, 0.02   # 18-23h : Pic soirée
            ],
            'description': '🟢 STABLE - Réseau fiable (95% dispo)',
            'taux_disponibilite': 0.95
        },
        'normal': {  # 80% disponibilité moyenne
            'profil_24h': [
                0.10, 0.10, 0.15, 0.15, 0.10, 0.10,  # 0-5h : Nuit
                0.05, 0.05, 0.08, 0.10, 0.12, 0.15,  # 6-11h : Matin
                0.15, 0.20, 0.25, 0.20, 0.25, 0.30,  # 12-17h : Après-midi chaud
                0.40, 0.50, 0.45, 0.35, 0.20, 0.15   # 18-23h : Pointe forte
            ],
            'description': '🟡 NORMAL - Coupures fréquentes (80% dispo)',
            'taux_disponibilite': 0.80
        },
        'instable': {  # 60% disponibilité moyenne
            'profil_24h': [
                0.30, 0.30, 0.35, 0.35, 0.30, 0.25,  # 0-5h : Nuit instable
                0.20, 0.20, 0.25, 0.30, 0.35, 0.40,  # 6-11h : Matin
                0.45, 0.50, 0.60, 0.55, 0.60, 0.65,  # 12-17h : Très instable
                0.70, 0.80, 0.75, 0.65, 0.50, 0.40   # 18-23h : Pointe critique
            ],
            'description': '🔴 INSTABLE - Réseau fragile (60% dispo)',
            'taux_disponibilite': 0.60
        }
    }
    
    def __init__(self, parametres: ParametresSBEE):
        self.params = parametres
        self.historique_pannes = []
        self.historique_disponibilite_24h = [True] * 24  # Par défaut tout disponible
        self._generer_profil_disponibilite()
    
    def _generer_profil_disponibilite(self):
        """Génère le profil de disponibilité sur 24h selon le mode"""
        if self.params.mode_coupures == 'manuel':
            # Mode manuel : utiliser les coupures définies par l'utilisateur
            self.historique_disponibilite_24h = [
                False if h in self.params.coupures_manuelles else True
                for h in range(24)
            ]
        else:
            # Mode automatique : simulation probabiliste
            profil = self.PROFILS_COUPURES[self.params.scenario]['profil_24h']
            self.historique_disponibilite_24h = []
            
            for proba_coupure in profil:
                # Tirage aléatoire : si random < proba_coupure → coupure
                est_disponible = np.random.random() > proba_coupure
                self.historique_disponibilite_24h.append(est_disponible)
    
    def est_disponible_a_heure(self, heure: int) -> bool:
        """
        Vérifie si le réseau SBEE est disponible à une heure donnée.
        
        Args:
            heure: Heure de 0 à 23
        
        Returns:
            True si disponible, False sinon
        """
        if not 0 <= heure <= 23:
            raise ValueError("L'heure doit être entre 0 et 23")
        
        return self.historique_disponibilite_24h[heure]
    
    def est_disponible(self) -> bool:
        """Vérifie si le réseau SBEE est actuellement disponible"""
        return self.params.disponible
    
    def puissance_disponible(self) -> float:
        """Retourne la puissance disponible du réseau"""
        if self.est_disponible():
            return self.params.puissance_max
        return 0.0
    
    def peut_fournir(self, puissance_demandee: float) -> bool:
        """Vérifie si le réseau peut fournir la puissance demandée"""
        return self.est_disponible() and puissance_demandee <= self.params.puissance_max
    
    def fournir_puissance(self, puissance_demandee: float, heure: int = 12) -> dict:
        """
        Tente de fournir la puissance demandée
        
        Args:
            puissance_demandee: Puissance demandée en kW
            heure: Heure de la journée (pour tarification)
        
        Returns:
            dict avec 'success', 'puissance_fournie', 'deficit', 'cout'
        """
        if not self.est_disponible():
            return {
                'success': False,
                'puissance_fournie': 0,
                'deficit': puissance_demandee,
                'cout': 0,
                'tarif_applique': 0
            }
        
        if puissance_demandee <= self.params.puissance_max:
            # Peut fournir la totalité
            tarif = self._get_tarif_horaire(heure)
            cout = puissance_demandee * tarif
            return {
                'success': True,
                'puissance_fournie': puissance_demandee,
                'deficit': 0,
                'cout': cout,
                'tarif_applique': tarif
            }
        else:
            # Peut fournir partiellement
            tarif = self._get_tarif_horaire(heure)
            cout = self.params.puissance_max * tarif
            return {
                'success': False,
                'puissance_fournie': self.params.puissance_max,
                'deficit': puissance_demandee - self.params.puissance_max,
                'cout': cout,
                'tarif_applique': tarif
            }
    
    def _get_tarif_horaire(self, heure: int) -> float:
        """
        Retourne le tarif applicable selon l'heure.
        
        Tranches horaires :
        - Heures creuses (22h-6h) : Tarif réduit
        - Heures normales (6h-18h) : Tarif base
        - Heures de pointe (18h-22h) : Tarif majoré
        """
        if 22 <= heure or heure < 6:  # Heures creuses
            return self.params.tarif_hors_pointe
        elif 18 <= heure < 22:  # Heures de pointe
            return self.params.tarif_pointe
        else:  # Heures normales
            return self.params.tarif_base
    
    def calculer_statistiques_disponibilite(self) -> dict:
        """
        Calcule les statistiques de disponibilité sur 24h.
        
        Returns:
            dict avec taux de disponibilité, nombre de coupures, durée totale
        """
        heures_disponibles = sum(self.historique_disponibilite_24h)
        heures_coupure = 24 - heures_disponibles
        taux_dispo = (heures_disponibles / 24) * 100
        
        # Compter les coupures (changement False → True ou True → False)
        nombre_coupures = 0
        for i in range(1, 24):
            if self.historique_disponibilite_24h[i] != self.historique_disponibilite_24h[i-1]:
                nombre_coupures += 1
        nombre_coupures = nombre_coupures // 2  # Diviser par 2 (début + fin = 1 coupure)
        
        return {
            'taux_disponibilite_pct': taux_dispo,
            'heures_disponibles': heures_disponibles,
            'heures_coupure': heures_coupure,
            'nombre_coupures': nombre_coupures,
            'duree_moyenne_coupure': heures_coupure / nombre_coupures if nombre_coupures > 0 else 0,
            'scenario': self.params.scenario,
            'mode': self.params.mode_coupures
        }
    
    def get_profil_disponibilite_24h(self) -> List[bool]:
        """Retourne le profil de disponibilité sur 24h"""
        return self.historique_disponibilite_24h.copy()
    
    def get_profil_disponibilite_numerique_24h(self) -> List[int]:
        """Retourne le profil en format numérique (1=dispo, 0=coupure)"""
        return [1 if dispo else 0 for dispo in self.historique_disponibilite_24h]
    
    def simuler_panne(self):
        """Simule une panne instantanée"""
        self.params.disponible = False
        self.historique_pannes.append({'type': 'panne', 'moment': 'instantanée'})
    
    def restaurer(self):
        """Restaure le réseau après une panne"""
        self.params.disponible = True
        self.historique_pannes.append({'type': 'restauration', 'moment': 'instantanée'})
    
    def cout_journalier(self, energie_consommee_kwh: float) -> float:
        """Calcule le coût journalier moyen en FCFA"""
        # Utilise le tarif base comme approximation
        return energie_consommee_kwh * self.params.tarif_base
    
    @staticmethod
    def get_scenarios_disponibles() -> dict:
        """Retourne les scénarios disponibles avec leurs descriptions"""
        return {
            'stable': ModeleSBEE.PROFILS_COUPURES['stable']['description'],
            'normal': ModeleSBEE.PROFILS_COUPURES['normal']['description'],
            'instable': ModeleSBEE.PROFILS_COUPURES['instable']['description']
        }