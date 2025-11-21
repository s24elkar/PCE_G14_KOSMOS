"""
CONTRÔLEUR - Page d'accueil KOSMOS
Architecture MVC
"""
import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class AccueilKosmosController(QObject):
    """Contrôleur pour la page d'accueil KOSMOS"""
    
    navigation_demandee = pyqtSignal(str)
    campagne_creee = pyqtSignal(str, str)
    campagne_ouverte = pyqtSignal(str)
    
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
    
    def on_creer_campagne(self, view_parent=None):
        """Crée une nouvelle campagne"""
        from views.accueil_view import FenetreNouvelleCampagne
        
        dialogue = FenetreNouvelleCampagne(view_parent)
        
        def on_campagne_creee(nom, emplacement):
            # Créer la campagne SANS sauvegarder immédiatement
            # L'emplacement sera défini lors de l'importation
            campagne = self.model.creer_campagne(nom, "")  # Emplacement vide pour l'instant
            
            print(f"✅ Campagne créée : {campagne.nom}")
            
            self.campagne_creee.emit(nom, emplacement)
            self.navigation_demandee.emit('importation')
    
        dialogue.campagneCreee.connect(on_campagne_creee)
        dialogue.exec()
    
    def on_ouvrir_campagne(self, view_parent=None):
        """Ouvre une campagne existante"""
        chemin_fichier, _ = QFileDialog.getOpenFileName(
            view_parent,
            "Ouvrir une campagne",
            "",
            "Fichiers JSON (*.json)"
        )
        
        if chemin_fichier:
            if self.model.ouvrir_campagne(chemin_fichier):
                print(f"✅ Campagne ouverte : {self.model.campagne_courante.nom}")
                self.campagne_ouverte.emit(chemin_fichier)
                self.navigation_demandee.emit('tri')
            else:
                QMessageBox.critical(view_parent, "Erreur", "Impossible d'ouvrir la campagne.")
    
    def on_enregistrer(self, view_parent=None):
        """Enregistre la campagne courante"""
        if self.model.campagne_courante:
            if self.model.sauvegarder_campagne():
                QMessageBox.information(
                    view_parent,
                    "Sauvegarde réussie",
                    f"Campagne '{self.model.campagne_courante.nom}' sauvegardée."
                )
            else:
                QMessageBox.critical(view_parent, "Erreur", "Impossible de sauvegarder.")
        else:
            QMessageBox.warning(view_parent, "Aucune campagne", "Aucune campagne ouverte.")
    
    def on_enregistrer_sous(self, view_parent=None):
        """Enregistre sous un nouveau nom"""
        if not self.model.campagne_courante:
            QMessageBox.warning(view_parent, "Aucune campagne", "Aucune campagne ouverte.")
            return
        
        from views.accueil_view import FenetreNouvelleCampagne
        
        dialogue = FenetreNouvelleCampagne(view_parent)
        
        def on_nouvelle_campagne(nom, emplacement):
            self.model.campagne_courante.nom = nom
            self.model.campagne_courante.emplacement = emplacement
            self.model.sauvegarder_campagne()
            QMessageBox.information(view_parent, "Succès", "Campagne enregistrée sous un nouveau nom.")
        
        dialogue.campagneCreee.connect(on_nouvelle_campagne)
        dialogue.exec()