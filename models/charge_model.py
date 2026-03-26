"""
MODÈLE MATHÉMATIQUE DE LA CHARGE ÉLECTRIQUE
============================================

Auteur: Votre Nom
Projet: Gestion Automatique d'un Micro-Réseau Hybride PV-SBEE-Diesel
"""

import numpy as np
from dataclasses import dataclass
from typing import Literal

@dataclass
class ParametresCharge:
    """Paramètres de la charge électrique"""
    type_charge: Literal['clinique', 'hopital', 'centre_commercial', 'lycee_universite', 
                         'residence_villa', 'hotel', 'industrie'] = 'clinique'
    puissance_max: float = 40.0  # kW
    puissance_min: float = 15.0  # kW
    facteur_simultaneite: float = 0.85


class ModeleCharge:
    """Modèle mathématique de la charge électrique"""
    
    PROFILS_TYPES = {
        'clinique': {
            'profil_24h': [
                0.60, 0.55, 0.55, 0.55, 0.60, 0.65,
                0.70, 0.80, 0.90, 0.95, 0.95, 0.90,
                0.90, 0.95, 1.00, 0.95, 0.90, 0.85,
                0.80, 0.75, 0.70, 0.65, 0.60, 0.60
            ],
            'description': '🏥 Clinique - Charge élevée consultations',
            'puissance_type': (20, 60),
            'puissance_sbee_recommandee': 40,  # kW
            'puissance_diesel_recommandee': 30  # kW (secours)
        },
        'hopital': {
            'profil_24h': [
                0.85, 0.80, 0.80, 0.80, 0.85, 0.88,
                0.90, 0.92, 0.95, 0.98, 0.95, 0.92,
                0.95, 0.98, 1.00, 0.98, 0.95, 0.92,
                0.90, 0.88, 0.85, 0.85, 0.85, 0.85
            ],
            'description': '🏥 Hôpital - Charge très élevée 24/7',
            'puissance_type': (50, 200),
            'puissance_sbee_recommandee': 150,
            'puissance_diesel_recommandee': 100  # Critique, besoin important
        },
        'centre_commercial': {
            'profil_24h': [
                0.15, 0.15, 0.15, 0.15, 0.15, 0.20,
                0.30, 0.45, 0.70, 0.85, 0.92, 0.95,
                0.95, 0.98, 1.00, 1.00, 0.98, 0.95,
                0.90, 0.75, 0.50, 0.30, 0.20, 0.15
            ],
            'description': '🏬 Centre Commercial - Pics 10h-18h',
            'puissance_type': (30, 150),
            'puissance_sbee_recommandee': 100,
            'puissance_diesel_recommandee': 80
        },
        'lycee_universite': {
            'profil_24h': [
                0.10, 0.10, 0.10, 0.10, 0.15, 0.25,
                0.45, 0.75, 0.90, 0.95, 0.95, 0.90,
                0.85, 0.95, 1.00, 0.98, 0.90, 0.75,
                0.55, 0.35, 0.20, 0.15, 0.10, 0.10
            ],
            'description': '🎓 Lycée/Université - Heures de cours',
            'puissance_type': (25, 100),
            'puissance_sbee_recommandee': 70,
            'puissance_diesel_recommandee': 50
        },
        'residence_villa': {
            'profil_24h': [
                0.25, 0.20, 0.20, 0.20, 0.25, 0.40,
                0.60, 0.80, 0.90, 0.70, 0.55, 0.50,
                0.45, 0.45, 0.45, 0.50, 0.55, 0.65,
                0.80, 0.95, 1.00, 0.95, 0.75, 0.45
            ],
            'description': '🏠 Résidence/Villa - Pics matin/soir',
            'puissance_type': (5, 30),
            'puissance_sbee_recommandee': 15,
            'puissance_diesel_recommandee': 10  # Petit groupe
        },
        'hotel': {
            'profil_24h': [
                0.50, 0.45, 0.45, 0.45, 0.50, 0.60,
                0.70, 0.85, 0.90, 0.85, 0.80, 0.75,
                0.70, 0.70, 0.75, 0.80, 0.85, 0.90,
                0.95, 1.00, 0.95, 0.85, 0.70, 0.60
            ],
            'description': '🏨 Hôtel - Charge continue avec pic soir',
            'puissance_type': (20, 80),
            'puissance_sbee_recommandee': 60,
            'puissance_diesel_recommandee': 40
        },
        'industrie': {
            'profil_24h': [
                0.20, 0.20, 0.20, 0.20, 0.25, 0.35,
                0.55, 0.80, 0.95, 1.00, 1.00, 0.98,
                0.98, 1.00, 1.00, 0.98, 0.90, 0.75,
                0.55, 0.40, 0.30, 0.25, 0.20, 0.20
            ],
            'description': '🏭 Industrie - Pleine charge 8h-17h',
            'puissance_type': (40, 300),
            'puissance_sbee_recommandee': 250,
            'puissance_diesel_recommandee': 200  # Besoin important
        }
    }
    
    def __init__(self, parametres: ParametresCharge):
        self.params = parametres
        self.profil_type = self.PROFILS_TYPES[parametres.type_charge]
    
    def puissance_instantanee(self, heure: int, variabilite: float = 0.05) -> float:
        """Calcule la puissance demandée à une heure donnée"""
        if not 0 <= heure <= 23:
            raise ValueError("L'heure doit être entre 0 et 23")
        
        coeff_profil = self.profil_type['profil_24h'][heure]
        alea = np.random.uniform(-variabilite, variabilite)
        puissance_variable = (self.params.puissance_max - self.params.puissance_min) * \
                            coeff_profil * self.params.facteur_simultaneite * (1 + alea)
        puissance_totale = self.params.puissance_min + puissance_variable
        return max(puissance_totale, self.params.puissance_min)