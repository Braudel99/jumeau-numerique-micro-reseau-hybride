"""
MODÈLE MATHÉMATIQUE DU GÉNÉRATEUR DIESEL ATS
============================================

Générateur Diesel avec démarrage automatique (ATS - Automatic Transfer Switch)

Auteur: Votre Nom
Projet: Gestion Automatique d'un Micro-Réseau Hybride PV-SBEE-Diesel
"""

from dataclasses import dataclass

@dataclass
class ParametresDiesel:
    """Paramètres du générateur diesel ATS"""
    puissance_nominale: float = 30.0  # kW
    puissance_min_pct: float = 0.30  # 30% charge minimale (évite encrassement)
    temps_demarrage: float = 15.0  # secondes (10-30s typique)
    temps_refroidissement: float = 5.0  # minutes
    consommation_specifique: float = 0.28  # L/kWh (0.25-0.30 typique diesel)
    cout_carburant: float = 600.0  # FCFA/L (Bénin)
    actif: bool = False
    avec_refroidissement: bool = False  # Optionnel pour simplifier


class ModeleDiesel:
    """Modèle mathématique du générateur diesel ATS"""
    
    def __init__(self, parametres: ParametresDiesel):
        self.params = parametres
        self.temps_fonctionnement_total = 0.0  # heures
        self.carburant_consomme_total = 0.0  # litres
        self.nombre_demarrages = 0
        self.cout_total = 0.0  # FCFA
        self.en_refroidissement = False
        self.temps_refroidissement_restant = 0.0
    
    def est_actif(self) -> bool:
        """Vérifie si le générateur est en marche"""
        return self.params.actif
    
    def puissance_minimale_requise(self) -> float:
        """
        Calcule la puissance minimale pour démarrer le diesel.
        
        Évite l'encrassement : le diesel doit tourner à minimum 30% de charge.
        
        Returns:
            Puissance minimale en kW
        """
        return self.params.puissance_nominale * self.params.puissance_min_pct
    
    def peut_demarrer_pour_charge(self, puissance_demandee: float) -> bool:
        """
        Vérifie si le diesel peut démarrer pour une charge donnée.
        
        Args:
            puissance_demandee: Puissance que le diesel devrait fournir (kW)
        
        Returns:
            True si la charge est suffisante (≥30% nominal)
        """
        return puissance_demandee >= self.puissance_minimale_requise()
    
    def demarrer(self) -> dict:
        """
        Démarre le générateur.
        
        Returns:
            dict avec success, temps, message
        """
        if not self.params.actif:
            self.params.actif = True
            self.nombre_demarrages += 1
            return {
                'success': True,
                'temps_demarrage': self.params.temps_demarrage,
                'message': f'✅ Diesel démarré en {self.params.temps_demarrage}s (démarrage #{self.nombre_demarrages})'
            }
        return {
            'success': False,
            'temps_demarrage': 0,
            'message': '⚠️ Diesel déjà en marche'
        }
    
    def arreter(self) -> dict:
        """
        Arrête le générateur (avec ou sans refroidissement).
        
        Returns:
            dict avec success, temps, message
        """
        if self.params.actif:
            if self.params.avec_refroidissement:
                self.en_refroidissement = True
                self.temps_refroidissement_restant = self.params.temps_refroidissement
                return {
                    'success': True,
                    'temps_arret': self.params.temps_refroidissement * 60,  # en secondes
                    'message': f'🔄 Diesel en refroidissement ({self.params.temps_refroidissement} min)'
                }
            else:
                self.params.actif = False
                return {
                    'success': True,
                    'temps_arret': 0,
                    'message': '✅ Diesel arrêté'
                }
        return {
            'success': False,
            'temps_arret': 0,
            'message': '⚠️ Diesel déjà arrêté'
        }
    
    def peut_fournir(self, puissance_demandee: float) -> bool:
        """
        Vérifie si le générateur peut fournir la puissance demandée.
        
        Conditions :
        - Diesel actif
        - Charge entre 30% et 100% de la puissance nominale
        """
        if not self.est_actif():
            return False
        
        p_min = self.puissance_minimale_requise()
        p_max = self.params.puissance_nominale
        
        return p_min <= puissance_demandee <= p_max
    
    def fournir_puissance(self, puissance_demandee: float, duree_h: float = 1.0) -> dict:
        """
        Fournit de la puissance pendant une durée donnée.
        
        Args:
            puissance_demandee: Puissance demandée en kW
            duree_h: Durée en heures (défaut 1h)
        
        Returns:
            dict avec success, puissance_fournie, carburant, cout, deficit
        """
        if not self.est_actif():
            return {
                'success': False,
                'puissance_fournie': 0,
                'energie_fournie': 0,
                'carburant_consomme': 0,
                'cout': 0,
                'deficit': puissance_demandee,
                'message': '❌ Diesel arrêté'
            }
        
        # Vérification charge minimale
        p_min = self.puissance_minimale_requise()
        if puissance_demandee < p_min:
            return {
                'success': False,
                'puissance_fournie': 0,
                'energie_fournie': 0,
                'carburant_consomme': 0,
                'cout': 0,
                'deficit': puissance_demandee,
                'message': f'⚠️ Charge trop faible (<{p_min:.1f} kW minimum)'
            }
        
        # Limitation de puissance
        puissance_effective = min(puissance_demandee, self.params.puissance_nominale)
        
        # Calcul consommation carburant
        energie_fournie = puissance_effective * duree_h  # kWh
        carburant = energie_fournie * self.params.consommation_specifique  # L
        cout = carburant * self.params.cout_carburant  # FCFA
        
        # Mise à jour statistiques
        self.temps_fonctionnement_total += duree_h
        self.carburant_consomme_total += carburant
        self.cout_total += cout
        
        deficit = max(0, puissance_demandee - puissance_effective)
        
        return {
            'success': True,
            'puissance_fournie': puissance_effective,
            'energie_fournie': energie_fournie,
            'carburant_consomme': carburant,
            'cout': cout,
            'deficit': deficit,
            'message': f'✅ Diesel fournit {puissance_effective:.1f} kW'
        }
    
    def consommation_horaire(self, puissance_kw: float) -> float:
        """Calcule la consommation horaire en litres pour une puissance donnée"""
        return puissance_kw * self.params.consommation_specifique
    
    def cout_horaire(self, puissance_kw: float) -> float:
        """Calcule le coût horaire en FCFA pour une puissance donnée"""
        return self.consommation_horaire(puissance_kw) * self.params.cout_carburant
    
    def statistiques(self) -> dict:
        """
        Retourne les statistiques d'utilisation détaillées.
        
        Returns:
            dict avec toutes les statistiques importantes
        """
        return {
            'heures_fonctionnement': round(self.temps_fonctionnement_total, 2),
            'carburant_total_L': round(self.carburant_consomme_total, 2),
            'cout_total_FCFA': round(self.cout_total, 2),
            'nombre_demarrages': self.nombre_demarrages,
            'consommation_moyenne_L_h': (
                round(self.carburant_consomme_total / self.temps_fonctionnement_total, 2)
                if self.temps_fonctionnement_total > 0 else 0
            ),
            'cout_moyen_FCFA_h': (
                round(self.cout_total / self.temps_fonctionnement_total, 2)
                if self.temps_fonctionnement_total > 0 else 0
            ),
            'charge_minimale_kW': round(self.puissance_minimale_requise(), 2),
            'puissance_nominale_kW': self.params.puissance_nominale
        }
    
    def reset_statistiques(self):
        """Réinitialise les statistiques"""
        self.temps_fonctionnement_total = 0.0
        self.carburant_consomme_total = 0.0
        self.cout_total = 0.0
        self.nombre_demarrages = 0