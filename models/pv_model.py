"""
MODÈLE MATHÉMATIQUE DU SYSTÈME PHOTOVOLTAÏQUE
==============================================

Ce fichier contient le modèle complet d'un panneau solaire photovoltaïque
avec tous les paramètres influençant sa production d'énergie.

Auteur: Votre Nom
Projet: Gestion Automatique d'un Micro-Réseau Hybride PV-SBEE-Diesel
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Literal

@dataclass
class ParametresPV:
    """
    Classe pour stocker tous les paramètres d'un panneau photovoltaïque.
    
    Attributs techniques du panneau :
    ---------------------------------
    - puissance_nominale : Puissance crête en Wc (Watts crête)
    - surface : Surface du panneau en m²
    - type_technologie : 'monocristallin' ou 'polycristallin'
    
    Coefficients de performance :
    ----------------------------
    - rendement : Rendement du panneau (automatique selon technologie)
    - coeff_temperature : Perte de puissance par °C au-dessus de 25°C (en /°C)
    - NOCT : Nominal Operating Cell Temperature en °C
    
    Pertes système :
    ---------------
    - perte_cables : Pertes dans les câbles (0-1, ex: 0.03 = 3%)
    - efficacite_onduleur : Efficacité de l'onduleur (0-1, ex: 0.96 = 96%)
    - perte_salissure : Perte due à la poussière/saleté (0-1, ex: 0.05 = 5%)
    - efficacite_mppt : Efficacité du MPPT (0-1, ex: 0.98 = 98%)
    """
    
    # Paramètres techniques
    puissance_nominale: float = 5000  # Wc (5 kWc par défaut)
    surface: float = 30.0  # m²
    type_technologie: Literal['monocristallin', 'polycristallin'] = 'monocristallin'
    
    # Coefficients
    rendement: float = None  # Sera calculé automatiquement
    coeff_temperature: float = -0.0045  # /°C (typique: -0.4% à -0.5% par °C)
    NOCT: float = 45.0  # °C
    
    # Pertes système
    perte_cables: float = 0.03  # 3%
    efficacite_onduleur: float = 0.96  # 96%
    perte_salissure: float = 0.05  # 5%
    efficacite_mppt: float = 0.98  # 98%
    
    def __post_init__(self):
        """Calcule automatiquement le rendement selon la technologie choisie."""
        if self.rendement is None:
            if self.type_technologie == 'monocristallin':
                self.rendement = 0.18  # 18% pour monocristallin
            elif self.type_technologie == 'polycristallin':
                self.rendement = 0.15  # 15% pour polycristallin
            else:
                raise ValueError("Type de technologie invalide. Choisir 'monocristallin' ou 'polycristallin'")
    
    def pertes_systeme_total(self) -> float:
        """
        Calcule le facteur de perte total du système.
        
        Retourne le coefficient multiplicateur global (0-1) tenant compte de :
        - Pertes câbles
        - Efficacité onduleur
        - Salissure
        - Efficacité MPPT
        """
        return (1 - self.perte_cables) * self.efficacite_onduleur * \
               (1 - self.perte_salissure) * self.efficacite_mppt


class ModelePV:
    """
    Modèle mathématique complet d'un système photovoltaïque.
    
    Ce modèle calcule la puissance produite par un panneau PV en fonction :
    - De l'irradiation solaire
    - De la température ambiante
    - Des caractéristiques du panneau
    - Des pertes système
    """
    
    # Profil de température type sur 24h (°C)
    PROFIL_TEMPERATURE_TYPE = [
        22, 21, 21, 20, 20, 21,  # 0-5h : Nuit fraîche
        23, 25, 27, 29, 31, 33,  # 6-11h : Montée température
        35, 35, 34, 32, 30, 28,  # 12-17h : Pic et descente
        26, 24, 23, 22, 22, 22   # 18-23h : Refroidissement
    ]
    
    def __init__(self, parametres: ParametresPV):
        """
        Initialise le modèle PV avec ses paramètres.
        
        Args:
            parametres: Instance de ParametresPV contenant tous les paramètres
        """
        self.params = parametres
    
    @staticmethod
    def generer_profil_irradiation_horaire(irradiation_journaliere_kwh_m2: float) -> list:
        """
        Convertit l'irradiation journalière (kWh/m²/jour) en profil horaire (W/m²).
        
        Principe :
        ---------
        - L'irradiation journalière est l'intégrale de l'irradiation instantanée sur 24h
        - On utilise un profil type de distribution solaire
        - Le profil est normalisé pour que la somme corresponde à l'énergie journalière
        
        Formule :
        --------
        Pour chaque heure h :
        Irradiation(h) [W/m²] = Irradiation_journalière [kWh/m²/jour] × 1000 × Coefficient_normalisé(h)
        
        Où Coefficient_normalisé(h) représente la fraction d'énergie reçue à l'heure h
        
        Exemple :
        --------
        Irradiation journalière = 5.5 kWh/m²/jour (typique Bénin)
        À midi (h=12), coefficient = 0.145
        → Irradiation instantanée = 5.5 × 1000 × 0.145 = 797.5 W/m²
        
        Args:
            irradiation_journaliere_kwh_m2: Irradiation totale sur 24h (kWh/m²/jour)
                                           Bénin : 3.9 à 6.2 kWh/m²/jour
        
        Returns:
            Liste de 24 valeurs d'irradiation instantanée (W/m²)
        """
        # Profil type normalisé (coefficient pour chaque heure, somme ≈ 1)
        # Représente la distribution typique de l'ensoleillement
        profil_normalise = [
            0.000, 0.000, 0.000, 0.000, 0.000, 0.005,  # 0-5h : Nuit
            0.020, 0.045, 0.075, 0.105, 0.125, 0.140,  # 6-11h : Montée progressive
            0.145, 0.140, 0.125, 0.105, 0.075, 0.045,  # 12-17h : Pic puis descente
            0.020, 0.005, 0.000, 0.000, 0.000, 0.000   # 18-23h : Nuit
        ]
        
        # Conversion : kWh/m²/jour → Wh/m²/jour → W/m² moyen par heure
        irradiation_journaliere_wh = irradiation_journaliere_kwh_m2 * 1000
        
        profil_horaire = []
        for coeff in profil_normalise:
            # L'irradiation moyenne sur 1h (W/m²) = Énergie horaire (Wh/m²)
            irradiation_horaire_wh = irradiation_journaliere_wh * coeff
            profil_horaire.append(round(irradiation_horaire_wh, 1))
        
        return profil_horaire
    
    @staticmethod
    def get_profil_temperature_type() -> list:
        """
        Retourne le profil de température type sur 24h.
        
        Returns:
            Liste de 24 températures (°C)
        """
        return ModelePV.PROFIL_TEMPERATURE_TYPE.copy()

    
    def temperature_cellules(self, irradiation: float, temp_ambiante: float) -> float:
        """
        ÉQUATION 1 : TEMPÉRATURE DES CELLULES
        ======================================
        
        Calcule la température des cellules photovoltaïques.
        
        Formule :
        --------
        Tc = Ta + (NOCT - 20) × (G / 800)
        
        Où :
        - Tc = Température des cellules (°C)
        - Ta = Température ambiante (°C)
        - NOCT = Nominal Operating Cell Temperature (°C) - généralement 45°C
        - G = Irradiation solaire (W/m²)
        - 800 = Irradiation de référence pour NOCT (W/m²)
        - 20 = Température ambiante de référence pour NOCT (°C)
        
        Explication physique :
        ---------------------
        Les cellules PV chauffent sous l'effet du rayonnement solaire.
        Plus l'irradiation est forte, plus elles chauffent.
        Cette équation estime la surchauffe par rapport à l'air ambiant.
        
        Exemple :
        --------
        Si Ta = 30°C, G = 1000 W/m², NOCT = 45°C
        Tc = 30 + (45-20) × (1000/800) = 30 + 25 × 1.25 = 61.25°C
        → Les cellules sont 31.25°C plus chaudes que l'air ambiant !
        
        Args:
            irradiation: Irradiation solaire en W/m²
            temp_ambiante: Température de l'air ambiant en °C
        
        Returns:
            Température des cellules en °C
        """
        Tc = temp_ambiante + (self.params.NOCT - 20) * (irradiation / 800)
        return Tc
    
    def facteur_temperature(self, temp_cellules: float) -> float:
        """
        ÉQUATION 2 : FACTEUR DE CORRECTION DE TEMPÉRATURE
        ==================================================
        
        Calcule le coefficient de réduction de puissance dû à la température.
        
        Formule :
        --------
        FT = 1 + γ × (Tc - 25)
        
        Où :
        - FT = Facteur de température (sans unité, <1 si Tc>25°C)
        - γ = Coefficient de température (/°C) - négatif, typiquement -0.0045
        - Tc = Température des cellules (°C)
        - 25 = Température de référence STC (°C)
        
        Explication physique :
        ---------------------
        Les cellules PV perdent de l'efficacité quand elles chauffent.
        C'est un phénomène physique lié aux semi-conducteurs.
        À 25°C (conditions standard), le facteur est 1 (100% de puissance).
        Au-dessus de 25°C, le facteur devient < 1 (perte de puissance).
        
        Exemple :
        --------
        Si Tc = 61.25°C, γ = -0.0045 /°C
        FT = 1 + (-0.0045) × (61.25 - 25)
        FT = 1 - 0.0045 × 36.25 = 1 - 0.163 = 0.837
        → Le panneau ne produit que 83.7% de sa puissance nominale à cause de la chaleur !
        
        Args:
            temp_cellules: Température des cellules en °C
        
        Returns:
            Facteur de température (coefficient multiplicateur)
        """
        FT = 1 + self.params.coeff_temperature * (temp_cellules - 25)
        return max(FT, 0)  # Ne peut pas être négatif
    
    def puissance_ideale(self, irradiation: float) -> float:
        """
        ÉQUATION 3 : PUISSANCE IDÉALE (SANS PERTES DE TEMPÉRATURE)
        ===========================================================
        
        Calcule la puissance que produirait le panneau si la température était idéale (25°C).
        Utilise le rendement spécifique à la technologie (mono vs polycristallin).
        
        Formule :
        --------
        Pidéale = Surface × Rendement × Irradiation
        
        Où :
        - Pidéale = Puissance idéale (W)
        - Surface = Surface totale des panneaux (m²)
        - Rendement = Rendement de la technologie (18% mono, 15% poly)
        - Irradiation = G (W/m²)
        
        Explication physique :
        ---------------------
        Le rendement dépend de la technologie :
        - Monocristallin : 18% (plus efficace)
        - Polycristallin : 15% (moins efficace)
        
        Exemple :
        --------
        Surface = 30 m², Rendement = 18%, G = 1000 W/m²
        Pidéale = 30 × 0.18 × 1000 = 5400 W = 5.4 kW
        
        Args:
            irradiation: Irradiation solaire en W/m²
        
        Returns:
            Puissance idéale en W
        """
        P_ideale = self.params.surface * self.params.rendement * irradiation
        return P_ideale
    
    def puissance_instantanee(self, irradiation: float, temp_ambiante: float) -> dict:
        """
        ÉQUATION COMPLÈTE : PUISSANCE RÉELLE PRODUITE
        =============================================
        
        Calcule la puissance réellement produite par le panneau PV.
        
        Formule complète :
        -----------------
        P(t) = Pnom × (G/1000) × [1 + γ(Tc-25)] × ηMPPT × ηsystème
        
        Ou en décomposant :
        P(t) = Pidéale × FT × ηMPPT × (1-Pcâbles) × ηonduleur × (1-Psalissure)
        
        Étapes de calcul :
        -----------------
        1. Calculer Tc (température cellules)
        2. Calculer FT (facteur température)
        3. Calculer Pidéale (puissance idéale)
        4. Appliquer les pertes système
        5. Obtenir Préelle
        
        Explication complète :
        ---------------------
        La puissance réelle est le produit de :
        - La puissance idéale (dépend de l'irradiation)
        - Le facteur de température (perte due à la chaleur)
        - L'efficacité MPPT (optimisation du point de puissance max)
        - Les pertes dans les câbles (résistance électrique)
        - L'efficacité de l'onduleur (conversion DC→AC)
        - Les pertes de salissure (poussière sur les panneaux)
        
        Exemple complet :
        ----------------
        Données : Pnom=5000W, G=800W/m², Ta=30°C, γ=-0.0045/°C, NOCT=45°C
        
        Étape 1 - Tc :
        Tc = 30 + (45-20)×(800/800) = 30 + 25 = 55°C
        
        Étape 2 - FT :
        FT = 1 + (-0.0045)×(55-25) = 1 - 0.135 = 0.865
        
        Étape 3 - Pidéale :
        Pidéale = 5000 × (800/1000) = 4000 W
        
        Étape 4 - Pertes système (exemple : 88% au total) :
        Pertes = 0.98(MPPT) × 0.97(câbles) × 0.96(onduleur) × 0.95(salissure) = 0.866
        
        Étape 5 - Préelle :
        Préelle = 4000 × 0.865 × 0.866 = 2995 W ≈ 3 kW
        
        Conclusion : Avec 800 W/m² et 30°C, le panneau de 5 kWc produit 3 kW
        (60% de sa puissance nominale)
        
        Args:
            irradiation: Irradiation solaire en W/m²
            temp_ambiante: Température ambiante en °C
        
        Returns:
            Dictionnaire contenant :
            - 'puissance_W': Puissance en Watts
            - 'puissance_kW': Puissance en kiloWatts
            - 'temp_cellules': Température des cellules en °C
            - 'facteur_temp': Facteur de température appliqué
            - 'pertes_systeme': Coefficient de pertes système
        """
        # Étape 1 : Température des cellules
        Tc = self.temperature_cellules(irradiation, temp_ambiante)
        
        # Étape 2 : Facteur de température
        FT = self.facteur_temperature(Tc)
        
        # Étape 3 : Puissance idéale
        P_ideale = self.puissance_ideale(irradiation)
        
        # Étape 4 : Pertes système globales
        pertes_sys = self.params.pertes_systeme_total()
        
        # Étape 5 : Puissance réelle finale
        P_reelle = P_ideale * FT * pertes_sys
        
        return {
            'puissance_W': P_reelle,
            'puissance_kW': P_reelle / 1000,
            'puissance_ideale_W': P_ideale,
            'puissance_ideale_kW': P_ideale / 1000,
            'temp_cellules': Tc,
            'facteur_temp': FT,
            'pertes_systeme': pertes_sys,
            'efficacite_globale': (P_reelle / self.params.puissance_nominale) if irradiation == 1000 else None
        }
    
    def simulation_journee(self, 
                          irradiation_par_heure: list,
                          temperature_par_heure: list) -> pd.DataFrame:
        """
        Simule la production sur 24 heures.
        
        Args:
            irradiation_par_heure: Liste de 24 valeurs d'irradiation (W/m²)
            temperature_par_heure: Liste de 24 valeurs de température (°C)
        
        Returns:
            DataFrame avec la production heure par heure
        """
        if len(irradiation_par_heure) != 24 or len(temperature_par_heure) != 24:
            raise ValueError("Les listes doivent contenir 24 valeurs (une par heure)")
        
        resultats = []
        
        for heure in range(24):
            G = irradiation_par_heure[heure]
            Ta = temperature_par_heure[heure]
            
            res = self.puissance_instantanee(G, Ta)
            
            resultats.append({
                'Heure': heure,
                'Irradiation_W/m2': G,
                'Temp_Ambiante_C': Ta,
                'Temp_Cellules_C': round(res['temp_cellules'], 2),
                'Facteur_Temp': round(res['facteur_temp'], 3),
                'Puissance_kW': round(res['puissance_kW'], 3),
                'Energie_kWh': round(res['puissance_kW'], 3)  # Sur 1 heure, E = P
            })
        
        df = pd.DataFrame(resultats)
        df['Energie_Total_kWh'] = df['Energie_kWh'].sum()
        
        return df


# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("EXEMPLE D'UTILISATION DU MODÈLE PHOTOVOLTAÏQUE")
    print("="*70)
    
    # 1. Création des paramètres pour un panneau monocristallin
    print("\n1. Configuration d'un système PV de 5 kWc monocristallin")
    print("-" * 70)
    
    params_mono = ParametresPV(
        puissance_nominale=5000,  # 5 kWc
        surface=30,
        type_technologie='monocristallin',
        perte_cables=0.03,
        efficacite_onduleur=0.96,
        perte_salissure=0.05,
        efficacite_mppt=0.98
    )
    
    print(f"Puissance nominale : {params_mono.puissance_nominale} Wc")
    print(f"Technologie : {params_mono.type_technologie}")
    print(f"Rendement : {params_mono.rendement*100}%")
    print(f"Coefficient température : {params_mono.coeff_temperature} /°C")
    print(f"Pertes système totales : {(1-params_mono.pertes_systeme_total())*100:.1f}%")
    
    # 2. Création du modèle
    modele_mono = ModelePV(params_mono)
    
    # 3. Test à différentes conditions
    print("\n2. Test de production à différentes conditions")
    print("-" * 70)
    
    conditions = [
        (1000, 25, "Conditions optimales (STC)"),
        (800, 30, "Journée ensoleillée typique"),
        (400, 28, "Temps nuageux"),
        (150, 26, "Très nuageux / pluie"),
        (0, 20, "Nuit")
    ]
    
    for G, Ta, description in conditions:
        resultat = modele_mono.puissance_instantanee(G, Ta)
        print(f"\n{description}:")
        print(f"  Irradiation = {G} W/m², Temp. ambiante = {Ta}°C")
        print(f"  → Temp. cellules = {resultat['temp_cellules']:.1f}°C")
        print(f"  → Facteur température = {resultat['facteur_temp']:.3f}")
        print(f"  → Puissance produite = {resultat['puissance_kW']:.2f} kW")
    
    # 4. Simulation journée complète
    print("\n3. Simulation d'une journée complète")
    print("-" * 70)
    
    # Profil d'irradiation typique (0-23h)
    irradiation_jour = [
        0, 0, 0, 0, 0, 50,      # 0-5h : Nuit puis aube
        150, 300, 500, 700, 850, 950,  # 6-11h : Montée
        1000, 950, 850, 700, 500, 300,  # 12-17h : Descente
        150, 50, 0, 0, 0, 0     # 18-23h : Crépuscule puis nuit
    ]
    
    # Profil de température typique
    temperature_jour = [
        22, 21, 21, 20, 20, 21,  # 0-5h : Nuit fraîche
        23, 25, 27, 29, 31, 33,  # 6-11h : Montée
        35, 35, 34, 32, 30, 28,  # 12-17h : Descente
        26, 24, 23, 22, 22, 22   # 18-23h : Soirée
    ]
    
    df_journee = modele_mono.simulation_journee(irradiation_jour, temperature_jour)
    
    print("\nProduction par tranches horaires :")
    print(df_journee[['Heure', 'Irradiation_W/m2', 'Temp_Cellules_C', 'Puissance_kW']].to_string(index=False))
    
    energie_totale = df_journee['Energie_kWh'].sum()
    print(f"\n✓ ÉNERGIE TOTALE PRODUITE SUR 24H : {energie_totale:.2f} kWh")
    
    # 5. Comparaison monocristallin vs polycristallin
    print("\n4. Comparaison monocristallin vs polycristallin")
    print("-" * 70)
    
    params_poly = ParametresPV(
        puissance_nominale=5000,
        type_technologie='polycristallin'
    )
    modele_poly = ModelePV(params_poly)
    
    G_test, Ta_test = 800, 30
    res_mono = modele_mono.puissance_instantanee(G_test, Ta_test)
    res_poly = modele_poly.puissance_instantanee(G_test, Ta_test)
    
    print(f"Conditions : G = {G_test} W/m², Ta = {Ta_test}°C")
    print(f"\nMonocristallin (η = {params_mono.rendement*100}%):")
    print(f"  → Puissance = {res_mono['puissance_kW']:.2f} kW")
    print(f"\nPolycristallin (η = {params_poly.rendement*100}%):")
    print(f"  → Puissance = {res_poly['puissance_kW']:.2f} kW")
    print(f"\nDifférence : {(res_mono['puissance_kW'] - res_poly['puissance_kW']):.2f} kW")
    print(f"Avantage monocristallin : {((res_mono['puissance_kW']/res_poly['puissance_kW']-1)*100):.1f}%")
    
    print("\n" + "="*70)
    print("FIN DE L'EXEMPLE")
    print("="*70)