# -*- coding: utf-8 -*-
"""
Created on Mon Jul  1 09:45:52 2024

@author: ofauvarq
"""
import sys
import cv2
import numpy as np
import os
import time
import datetime
import ephem
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, QPushButton,QDialogButtonBox,QDialog,QComboBox,
                             QFileDialog, QSlider, QHBoxLayout, QLineEdit,QTabWidget, QMessageBox,QLineEdit,QToolButton,QTextEdit,
                             QCheckBox,QStyle,QProgressBar,QListWidget,QGridLayout,QStyleOptionSlider,QStyle, QInputDialog,QLayout,
                             QTreeWidget, QTreeWidgetItem, QMainWindow)
from PyQt6.QtCore import Qt, QTimer, QDir, QFileInfo, QRect, QPoint,QEvent,QSize
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QGuiApplication,QPaintEvent, QBrush, QKeyEvent
try:
    import pyqtgraph as pg
except Exception as exc:
    pg = None
    print(f"⚠️ pyqtgraph indisponible (non bloquant pour l'UI extraction): {exc}")

import pandas as pd

# Nouvelle UI (vue Extraction + contrôleur)
from controllers.extraction_controller import ExtractionController
from models.media_model import MediaModel
from models.campaign_model import CampaignModel
from views.vue_extraction import ExtractionView

# Algorithmes de correction (déplacés dans kosmos_processing)
from kosmos_processing.algos_correction import *

from shutil import copy
import json
import shutil

class TickSlider(QSlider):
    def __init__(self, *args):
        super().__init__(*args)
        self.ticks = []
        self.ticks2 = []

    def setTickPositions(self, ticks):
        self.ticks = ticks
        self.update()
        
    def setTick2Positions(self, ticks2):
        self.ticks2 = ticks2
        self.update()    

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setPen(QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.SolidLine))

        for tick in self.ticks:
            pos = self.tickPosition(tick)
            if self.orientation() == Qt.Orientation.Horizontal:
                painter.drawLine(pos, self.rect().bottom()-14, pos, self.rect().bottom() -20)
            else:
                print('Ne marche qu avec des slides horizontaux')
        
        painter2 = QPainter(self)
        painter2.setBrush(QBrush(QColor(0, 0, 255, 127)));       
        
        for tick2 in self.ticks2:
            pos_sta = self.tickPosition(tick2[0])
            pos_end = self.tickPosition(tick2[1])
            taille = pos_end-pos_sta
            if self.orientation() == Qt.Orientation.Horizontal:                
                rectangle = QRect(pos_sta, self.rect().bottom()-2,  taille , -6)
                painter2.drawRect(rectangle) 
                painter2.fillRect(rectangle, painter2.brush());
            else:
                print('Ne marche qu avec des slides horizontaux')

    def tickPosition(self, tick):
        if self.orientation() == Qt.Orientation.Horizontal:
            return int((tick - self.minimum()) / (self.maximum() - self.minimum()) * self.rect().width())
        else:
            return int((tick - self.minimum()) / (self.maximum() - self.minimum()) * self.rect().height())
    
    """
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Calculer la position relative du clic sur le slider
            if self.orientation() == Qt.Orientation.Vertical:
                new_value = self.minimum() + (self.maximum() - self.minimum()) * (self.height() - event.position().y()) / self.height()
            else:
                new_value = self.minimum() + (self.maximum() - self.minimum()) * event.position().x() / self.width()            
            self.setValue(int(new_value))
            
        super().mousePressEvent(event)
    """
class JSONEditorWindow(QDialog):
    def __init__(self, file_path):
        super().__init__()
        self.setWindowTitle(f"Éditeur de JSON - {file_path}")
        #self.setGeometry(3300, -350, 500, 1000)

        
        # Chemin du fichier JSON
        self.file_path = file_path
        
        # Initialiser l'éditeur JSON
        self.tree_widget = QTreeWidget()
        self.tree_widget.setColumnCount(2)
        self.tree_widget.setHeaderLabels(["Clé", "Valeur"])
        
        
        # Ajustement de la largeur des colonnes
        self.tree_widget.header().setStretchLastSection(True)  # Étend la dernière colonne
        self.tree_widget.setColumnWidth(0, 200)  # Définit une largeur fixe pour la première colonne
        
        # Bouton pour màj des données lune
        self.moon_button = QPushButton("Calcul de la phase de la lune")
        self.moon_button.clicked.connect(self.moon_calculation)
        
        
        # Bouton pour enregistrer
        self.save_button = QPushButton("Enregistrer les modifications")
        self.save_button.clicked.connect(self.save_file)
        
        # Layout principal
        layout = QVBoxLayout()
        layout.addWidget(self.tree_widget)
        layout.addWidget(self.moon_button)
        layout.addWidget(self.save_button)
        
        # Charger le fichier JSON
        self.load_file()
        
        
        
        self.setLayout(layout)
    
    def load_file(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Charger le JSON dans le QTreeWidget
                self.display_json(data, self.tree_widget.invisibleRootItem())
                # Déplier tous les éléments de l'arborescence
                self.tree_widget.expandAll()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de lire le fichier JSON:\n{e}")
            self.close()
    
    def display_json(self, data, parent):
        # Affiche les données JSON récursivement dans l'arborescence
        if isinstance(data, dict):
            for key, value in data.items():
                item = QTreeWidgetItem([str(key), ""])
                parent.addChild(item)
                if isinstance(value, (dict, list)):
                    self.display_json(value, item)  # Cas des sous-objets ou des listes
                else:
                    item.setText(1, str(value))  # Affiche les valeurs simples
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        elif isinstance(data, list):
            for i, value in enumerate(data):
                item = QTreeWidgetItem([f"[{i}]", ""])
                parent.addChild(item)
                if isinstance(value, (dict, list)):
                    self.display_json(value, item)
                else:
                    item.setText(1, str(value))
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

    def moon_calculation(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Charger le JSON dans le QTreeWidget
                year = 2000 + data['campagne']['dateDict']['year']
                month = data['campagne']['dateDict']['month']
                day = data['campagne']['dateDict']['day']
                hour = data['video']['heureDict']['heure']
                minute = data['video']['heureDict']['minute']
                
                date_cible = datetime.datetime(int(year),int(month),int(day),int(hour),int(minute))
                data['video']['astroDict']['lune'] = self.get_lunar_phase_description(date_cible)
                
                with open(self.file_path, 'w', encoding='utf-8') as ff:
                    ff.write(json.dumps(data, indent = 4))
                self.tree_widget.clear()
                self.load_file()               
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Phase de la lune non mise-à-jour\n{e}")
            self.close()
    
    def get_lunar_phase_description(self,date):
        # Obtenir la phase de la lune pour la date donnée
        lune = ephem.Moon(date)
        phase = lune.phase  # Phase de la lune en pourcentage (0 à 100)
        print(phase)
        # Identifier la phase selon le pourcentage
        if phase < 1:
            return "Nouvelle Lune"
        elif 1 <= phase < 7:
            return "Premier Croissant"
        elif 7 <= phase < 14:
            return "Premier Quartier"
        elif 14 <= phase < 21:
            return "Gibbeuse Croissante"
        elif 21 <= phase < 29:
            return "Pleine Lune"
        elif 29 <= phase < 36:
            return "Gibbeuse Décroissante"
        elif 36 <= phase < 43:
            return "Dernier Quartier"
        elif 43 <= phase < 50:
            return "Dernier Croissant"
        else:
            return "Nouvelle Lune"
            
    
    def save_file(self):
        try:
            # Sauvegarde le contenu du QTreeWidget sous forme de JSON
            data = self.tree_to_json(self.tree_widget.invisibleRootItem())
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            QMessageBox.information(self, "Succès", "Modifications enregistrées avec succès.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d'enregistrer le fichier JSON:\n{e}")
    
    def tree_to_json(self, parent):
        # Convertit le QTreeWidget en dictionnaire JSON récursivement
        data = {}
        for i in range(parent.childCount()):
            child = parent.child(i)
            key = child.text(0)
            if child.childCount() > 0:
                # Cas d'un objet ou d'une liste imbriquée
                value = self.tree_to_json(child)
            else:
                # Cas des valeurs simples
                value = child.text(1)
                # Essayer de convertir en nombre ou booléen si possible
                if value.isdigit():
                    value = int(value)
                elif value.lower() in ["true", "false"]:
                    value = value.lower() == "true"
                elif value.replace('.', '', 1).isdigit():
                    value = float(value)
            
            if key.startswith("[") and key.endswith("]"):
                # Gestion des listes
                if not isinstance(data, list):
                    data = []
                data.append(value)
            else:
                data[key] = value
        return data  
  
  
class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame_slot)
        self.playing = False
        self.start_pos = 0
        self.end_pos = 0

        self.start_pos_mouse = None
        self.end_pos_mouse = None
        self.start_mouse = None
        self.end_mouse = None 
        self.drawing = False
        self.setMouseTracking(True)
        self.video=False
        
        self.rect_start = None
        self.rect_end = None
        
        # Booléen pour réouverture de vidéo
        self.navigation_bool = False
        self.layout_bool = False
        self.metadata_bool = False
        self.histo_bool = False
        self.properties_bool = False
        self.jsonWindow = False
        
        # Initialisations de la liste évènements
        self.events_list = []
        
        # scaling de l'image, puissance de 2
        self.scaling = 2
    
        
    def initUI(self):
        
        # Initialisation des répertoires
        self.repetoirecourant = os.getcwd()
        self.workspace = ""
        self.folder_name = ""
        self.campaign_folder = ""
        self.list_campaign = []
    
        self.setWindowTitle('IHM KOSMOS')
        #self.move(1950,-300)
        
        # Création layout générale
        self.layout = QVBoxLayout()
        self.layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)
        
        # Définition générale des onglets
        self.tabs = QTabWidget() 
  
        self.event_type=['Poisson','Banc','Crustace','Autre']
        self.classif=['Lancon','Gobie','Lieu','Mulet','Tacaud','Rouget','Araignee']  
        
######## Bloc campagne journalière
        ## Initialisation        
        self.session_path = QLabel('Dossier de la sortie en mer', self)
        self.button_campaign = QToolButton(text='...')
        self.button_campaign.clicked.connect(self.openCampaignFolder)
        
        self.list_widget = QListWidget(self)
        self.list_widget.itemClicked.connect(self.print_item_name)
        self.list_widget.addItems(self.list_campaign)
        
        self.open2_button = QPushButton('Ouvrir Vidéo')
        self.open2_button.clicked.connect(self.open_video2)
        self.open2_button.setEnabled(False)  # Désactiver jusqu'à ce qu'un dossier soit sélectionné
        
        self.staticmtd_button = QPushButton('Compléter')
        self.staticmtd_button.clicked.connect(self.open_json)
        self.staticmtd_button.setEnabled(False)  # Désactiver jusqu'à ce qu'un dossier soit sélectionné
        
        self.close_button = QPushButton('Fermer')
        self.close_button.clicked.connect(self.close_video)
        self.close_button.setEnabled(False)  # Désactiver jusqu'à ce qu'un dossier soit sélectionné
        
        self.rename_button = QPushButton('Renommer', self)
        self.rename_button.clicked.connect(self.prompt_new_name)
        self.rename_button.setEnabled(False)  # Désactiver jusqu'à ce qu'un dossier soit sélectionné

        self.clear_button = QPushButton('Supprimer')
        self.clear_button.clicked.connect(self.confirm_delete) 
        self.clear_button.setEnabled(False)  # Désactiver jusqu'à ce qu'un dossier soit sélectionné
        
        
        ## Onglet 00
        self.tab00 = QWidget()
        self.tabs.addTab(self.tab00, "Validation Campagne")
        
        self.tab00.general_layout = QVBoxLayout(self)
 
        self.tab00.campaign_layout = QHBoxLayout(self)
        self.tab00.campaign_layout.addWidget(self.session_path)    
        self.tab00.campaign_layout.addWidget(self.button_campaign)    
       
        self.tab00.campaignn_layout = QGridLayout(self)
        self.tab00.campaignn_layout.addWidget(self.list_widget,0,0,5,1)
        self.tab00.campaignn_layout.addWidget(self.open2_button, 0, 1)
        self.tab00.campaignn_layout.addWidget(self.staticmtd_button, 1, 1)
        self.tab00.campaignn_layout.addWidget(self.close_button, 2, 1)
        self.tab00.campaignn_layout.addWidget(self.rename_button, 3, 1)
        self.tab00.campaignn_layout.addWidget(self.clear_button, 4, 1)
   
        self.tab00.general_layout.addLayout(self.tab00.campaign_layout)
        self.tab00.general_layout.addLayout(self.tab00.campaignn_layout)
       
        self.tab00.setLayout(self.tab00.general_layout)
    
######## Bloc ouverture
        ## Initialisation des boutons        
        self.open_button = QPushButton('Open Video', self)

        self.open_button.clicked.connect(self.open_video)
        
        self.pathEdit = QLabel('Choisir le réprtoire de travail', self)
        self.button = QToolButton(text='...')
        self.button.clicked.connect(self.openFolderDialog)
        self.dossier_label = QLabel('Entrez le nom du dossier à créer:', self)
        self.folderNameInput = QLineEdit(self)
        self.createButton = QPushButton('Créer Dossier', self)
        self.createButton.clicked.connect(self.createFolder)
        
        ## Onglet 0
        self.tab0 = QWidget()
        self.tabs.addTab(self.tab0, "Ouverture fichier")
        
        self.tab0.open_layout = QHBoxLayout()
        self.tab0.open_layout.addWidget(self.open_button)
        self.tab0.open_layout.addWidget(self.pathEdit)
        self.tab0.open_layout.addWidget(self.button)
        self.tab0.open_layout.addWidget(self.dossier_label)
        self.tab0.open_layout.addWidget(self.folderNameInput)
        self.tab0.open_layout.addWidget(self.createButton)
        
        self.tab0.setLayout(self.tab0.open_layout)

######### Bloc outils vidéos
        ## Initialisation des boutons
        self.ardsave_button = QPushButton('Save Ardoise', self)
        self.ardsave_button.clicked.connect(lambda: self.extract_image("Ardoise"))
        
        self.start_button = QPushButton('Start Section', self)
        self.start_button.clicked.connect(self.start_section)
        self.frame_start_label = QLabel(self)

        self.end_button = QPushButton('End Section', self)
        self.end_button.clicked.connect(self.end_section)
        self.frame_end_label = QLabel(self)
    
        self.save_button = QPushButton('Save Section', self)
        self.save_button.clicked.connect(self.save_section)
 
        self.progress = QProgressBar(self)
        self.progress.setValue(0)
        
        self.fastsave_button = QPushButton('Fast Save Section', self)
        self.fastsave_button.clicked.connect(self.save_section2)
        
        ## Onglet 2
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab2, "Segmentation de la vidéo")
        
        self.tab2.button_layout2 = QHBoxLayout()
        self.tab2.button_layout2.addWidget(self.ardsave_button)
        self.tab2.button_layout2.addWidget(self.start_button)
        self.tab2.button_layout2.addWidget(self.frame_start_label)
        self.tab2.button_layout2.addWidget(self.end_button)
        self.tab2.button_layout2.addWidget(self.frame_end_label)
        self.tab2.button_layout2.addWidget(self.save_button)
        self.tab2.button_layout2.addWidget(self.progress)
        self.tab2.button_layout2.addWidget(self.fastsave_button)

        self.tab2.setLayout(self.tab2.button_layout2)        

######### Bloc évènements
        ## Initialisation des boutons
        self.start_ev_button = QPushButton('Event Start', self)
        self.start_ev_button.clicked.connect(self.start_event)
        self.frame_ev_start_label = QLabel(self)

        self.end_ev_button = QPushButton('Event end', self)
        self.end_ev_button.clicked.connect(self.end_event)
        self.frame_ev_end_label = QLabel(self)
    
        self.event_vignette = QComboBox(self)
        self.event_vignette2 = QComboBox(self)

        self.event_vignette.addItems(self.event_type)  
        self.event_vignette2.addItems(self.classif)  

        self.save_ev_button = QPushButton('Save Event', self)
        self.save_ev_button.clicked.connect(self.save_event)
        
        self.reset_ev_button = QPushButton('Reset Event', self)
        self.reset_ev_button.clicked.connect(self.reset_event)
        
        ## Onglet 2
        self.tab3 = QWidget()
        self.tabs.addTab(self.tab3, "Evènements")
        
        self.tab3.event_layout = QHBoxLayout()
        self.tab3.event_layout.addWidget(self.start_ev_button)
        self.tab3.event_layout.addWidget(self.frame_ev_start_label)
        self.tab3.event_layout.addWidget(self.end_ev_button)
        self.tab3.event_layout.addWidget(self.frame_ev_end_label)
        self.tab3.event_layout.addWidget(self.event_vignette)
        self.tab3.event_layout.addWidget(self.event_vignette2)
        self.tab3.event_layout.addWidget(self.save_ev_button)
        self.tab3.event_layout.addWidget(self.reset_ev_button)

        self.tab3.setLayout(self.tab3.event_layout)      
                   
######### Bloc Annotation
        ## Initialisations des boutons
        self.HE_button = QPushButton('HE', self)
        self.HE_button.clicked.connect(self.HE)        
        self.DH_button = QPushButton('DH', self)
        self.DH_button.clicked.connect(self.DH) 
        self.RT_button = QPushButton('Reset', self)
        self.RT_button.clicked.connect(self.RT)
        self.histo_button = QPushButton('histogram', self)
        self.histo_button.setCheckable(True)
        self.histo_button.clicked.connect(self.Histogram)

        
        self.imgsave_button = QPushButton('Save Frame', self)
        self.imgsave_button.clicked.connect(lambda: self.extract_image("Frame"))       
        self.menu_vignette = QComboBox(self)
        self.menu_vignette.addItems(self.classif)       
        self.vigsave_button = QPushButton("Save Selection", self)
        self.vigsave_button.clicked.connect(self.save_selection)
        
        ## Onglet 4
        self.tab4 = QWidget()
        self.tabs.addTab(self.tab4, "Annotation")
        
        self.tab4.annotation_layout = QHBoxLayout()
        self.tab4.annotation_layout.addWidget(self.HE_button)
        self.tab4.annotation_layout.addWidget(self.DH_button)
        self.tab4.annotation_layout.addWidget(self.RT_button)
        self.tab4.annotation_layout.addWidget(self.histo_button)

        self.tab4.annotation_layout.addWidget(self.imgsave_button)
        self.tab4.annotation_layout.addWidget(self.menu_vignette)
        self.tab4.annotation_layout.addWidget(self.vigsave_button)

        self.tab4.setLayout(self.tab4.annotation_layout)
     
######## Général
        self.layout.addWidget(self.tabs)
        
        self.setLayout(self.layout)

    def open_video(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        self.read_video(filename)
        
    def open_video2(self):
        filename = os.path.join(os.path.join(self.campaign_folder,self.folder_path),self.folder_path)+".mp4"
        self.read_video(filename)
        self.close_button.setEnabled(True)
        self.clear_button.setEnabled(False)
        self.rename_button.setEnabled(False)
    
    def close_video(self):
        self.close_button.setEnabled(False)     
        self.clear_button.setEnabled(True)
        self.rename_button.setEnabled(True)
        

        '''
        # pour désélectionner la vidéo
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setSelected(False)
        self.open2_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.rename_button.setEnabled(False)
        self.staticmtd_button.setEnabled(False)
        '''      
        
        if self.properties_bool == True:
            self.clearLayout(self.prop1_layout)
            self.clearLayout(self.prop2_layout)
        if self.metadata_bool == True:
            self.clearLayout(self.metadata_layout)
            self.clearLayout(self.check_layout)
        if self.layout_bool == True:
            self.clearLayout(self.video_layout)            
        if self.navigation_bool == True:                
            self.clearLayout(self.defil_layout)
            self.slider.deleteLater()
        if self.histo_bool == True:                
            self.clearLayout(self.vertical_layout)
    
        self.navigation_bool = False
        self.layout_bool = False
        self.metadata_bool = False
        self.histo_bool = False
        self.properties_bool = False
        
        if self.video == True:
            self.cap.release() 
            self.video = False
            
        if self.jsonWindow == True:
            self.json_editor.close()
    
    def read_video(self,file):  
        if file: 
            # Path et nom de fichiers
            self.vidname=file
            self.dirname=os.path.dirname(self.vidname)
            self.basename=os.path.basename(self.vidname)
            if len(self.basename.split("Video.mp4")) > 1: 
                self.num_vid = self.basename.split("Video.mp4")[0]
            else:
                self.num_vid = ""

            # Ouverture de la vidéo 
            self.video = True
            self.cap = cv2.VideoCapture(self.vidname)
            
            # Extraction premières propriétés de la vidéo
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.frameduration = round(1000./self.fps)
            self.hauteur = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.largeur = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.nb_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                        
            # Vitesse du display
            self.displayframeduration = int(self.frameduration*1.0) # à ajuster si on veut aller plus vit
            self.timer.start(self.displayframeduration) 
            
            # Initialisation pour segmentation
            self.start_pos = 0
            self.end_pos = int(self.nb_frames)
            self.frame_start_label.setText(f"Start Frame: {self.start_pos}")
            self.frame_end_label.setText(f"End Frame: {self.end_pos}")
            
            self.playing = False
 
            # Initialisation des layout navigation, video et metadata
            if self.properties_bool == True:
                self.clearLayout(self.prop1_layout)
                self.clearLayout(self.prop2_layout)
            if self.metadata_bool == True:
                self.clearLayout(self.metadata_layout)
                self.clearLayout(self.check_layout)
            if self.layout_bool == True:
                self.clearLayout(self.video_layout)            
            if self.navigation_bool == True:                
                self.clearLayout(self.defil_layout)
                self.slider.deleteLater()
            if self.histo_bool == True:                
                self.clearLayout(self.vertical_layout)
                
            self.init_navigation()
            self.init_video()
            self.init_properties()
            self.init_ImageHisto()
            
            # Affichage première image    
            if self.cap:
                ret, self.frame = self.cap.read()
                if ret:
                    self.frame_svg = self.frame
                    self.display_frame()
                    
            self.init_metadata()
 
            # initialisation du CSV évènements si le fichier n'existe pas déjà
            self.event_csv_name = self.dirname+'/Evenements.csv'
            if not os.path.isfile(self.event_csv_name):
                event_line = "StartFrame;EndFrame;EventType;Species"        
                self.add_line(self.event_csv_name,event_line) 
            else :
                self.evenement = pd.read_csv(self.event_csv_name,delimiter=';')
                for i in range(0,len(self.evenement['StartFrame'])):
                    self.events_list.append([self.evenement['StartFrame'][i],self.evenement['EndFrame'][i]])
                    self.slider.setTick2Positions(self.events_list)
      
    def init_navigation(self):
        self.navigation_bool = True
        
        # Bloc lecture
        ## Initialisation slider
        self.slider = TickSlider(Qt.Orientation.Horizontal)
        self.slider.sliderMoved.connect(self.set_position)
        #self.slider.valueChanged.connect(self.set_position2)
        self.slider.setRange(0, int(self.nb_frames))
        ## set        
        self.layout.addWidget(self.slider)
        
        ## Initialisation de nav
        self.menu_vitesse = QComboBox(self)        
        self.vitesses=['x 1','x 0.5','x 2']
        self.menu_vitesse.addItems(self.vitesses)
        self.menu_vitesse.setFixedSize(self.menu_vitesse.sizeHint())
                
        self.start_video_button = QPushButton('Start Video', self)
        self.start_video_button.setFixedSize(self.start_video_button.sizeHint())
        self.start_video_button.clicked.connect(self.play_video)
        
        self.pause_video_button = QPushButton('Pause Video', self)
        self.pause_video_button.setFixedSize(self.pause_video_button.sizeHint())
        self.pause_video_button.clicked.connect(self.pause_video)
        
        self.avance_button_m100 = QPushButton('- 10', self)
        self.avance_button_m100.setFixedSize(self.avance_button_m100.sizeHint())
        self.avance_button_m100.clicked.connect(lambda: self.move_frame(-10))
        self.avance_button_m10 = QPushButton('- 1', self)
        self.avance_button_m10.setFixedSize(self.avance_button_m10.sizeHint())
        self.avance_button_m10.clicked.connect(lambda: self.move_frame(-1))
        self.avance_button_10 = QPushButton('+ 1', self)
        self.avance_button_10.setFixedSize(self.avance_button_10.sizeHint())
        self.avance_button_10.clicked.connect(lambda: self.move_frame(1))
        self.avance_button_100 = QPushButton('+ 10', self)
        self.avance_button_100.setFixedSize(self.avance_button_100.sizeHint())
        self.avance_button_100.clicked.connect(lambda: self.move_frame(10))
       
        self.frame_number_label = QLabel(self)
        self.frame_number_label.setText(f"Frame Number: {0}")
        
        self.avance_button_m10s = QPushButton('- 10s', self)
        self.avance_button_m10s.setFixedSize(self.avance_button_m100.sizeHint())
        self.avance_button_m10s.clicked.connect(lambda: self.move_frame(round(-10*self.fps)))
        self.avance_button_m1s = QPushButton('- 1s', self)
        self.avance_button_m1s.setFixedSize(self.avance_button_m10.sizeHint())
        self.avance_button_m1s.clicked.connect(lambda: self.move_frame(round(-self.fps)))
        self.avance_button_1s = QPushButton('+ 1s', self)
        self.avance_button_1s.setFixedSize(self.avance_button_10.sizeHint())
        self.avance_button_1s.clicked.connect(lambda: self.move_frame(round(self.fps)))
        self.avance_button_10s = QPushButton('+ 10s', self)
        self.avance_button_10s.setFixedSize(self.avance_button_100.sizeHint())
        self.avance_button_10s.clicked.connect(lambda: self.move_frame(round(10*self.fps)))
   
        self.time_label = QLabel(self)   
        self.time_label.setText(f"Time: {0}")
        
        self.timestamp_label = QLabel(self)
        self.timestamp_label.setText("Timestamp: ")

        
        ## Set layout
        self.defil_layout = QHBoxLayout()   
        self.defil_layout.addWidget(self.menu_vitesse)
        self.defil_layout.addWidget(self.start_video_button)
        self.defil_layout.addWidget(self.pause_video_button)
        
        self.defil_layout.addWidget(self.avance_button_m100)
        self.defil_layout.addWidget(self.avance_button_m10)
        self.defil_layout.addWidget(self.avance_button_10)
        self.defil_layout.addWidget(self.avance_button_100)
        self.defil_layout.addWidget(self.frame_number_label)
        self.defil_layout.addWidget(self.avance_button_m10s)
        self.defil_layout.addWidget(self.avance_button_m1s)
        self.defil_layout.addWidget(self.avance_button_1s)
        self.defil_layout.addWidget(self.avance_button_10s)
        self.defil_layout.addWidget(self.time_label)
        self.defil_layout.addWidget(self.timestamp_label)

        
        ## Insertion layouts
        self.layout.addLayout(self.defil_layout)    

    def init_video(self):
        self.layout_bool = True
        
        # Bloc Video & Image        
        ## Initialisation des fenêtres
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        ## Layout Video 
        self.video_layout = QHBoxLayout()
        self.video_layout.addWidget(self.video_label)
        
        self.layout.addLayout(self.video_layout)
        
        
    def init_properties(self):
        self.properties_bool = True
        ## Initialisation des labels
        self.vidname_label = QLabel(self)
        self.fps_label = QLabel(self)
        self.frameduration_label = QLabel(self)
        self.hauteur_label = QLabel(self)
        self.largeur_label = QLabel(self)
        self.nb_frames_label = QLabel(self)
        
        self.heuredebut_label = QLabel(self)
        self.latitude_label = QLabel(self)
        self.longitude_label = QLabel(self)
        self.profondeur_label = QLabel(self)
        self.temperature_label = QLabel(self)

        ##
        self.prop1_layout = QHBoxLayout()
        self.prop1_layout.addWidget(self.vidname_label)        
        self.prop1_layout.addWidget(self.fps_label)
        self.prop1_layout.addWidget(self.frameduration_label)
        self.prop1_layout.addWidget(self.hauteur_label)
        self.prop1_layout.addWidget(self.largeur_label)
        self.prop1_layout.addWidget(self.nb_frames_label)
        
        self.prop2_layout = QHBoxLayout()
        self.prop2_layout.addWidget(self.heuredebut_label)
        self.prop2_layout.addWidget(self.latitude_label)
        self.prop2_layout.addWidget(self.longitude_label)
        self.prop2_layout.addWidget(self.profondeur_label)
        self.prop2_layout.addWidget(self.temperature_label)
        
        
        # Ecriture des propriétés de la vidéo
        self.vidname_label.setText(f"{self.vidname}")       
        self.fps_label.setText(f"FPS: {self.fps:.2f}")
        self.frameduration_label.setText(f"Frame Duration: {round(self.frameduration)} ms")
        self.hauteur_label.setText(f"Hauteur: {int(self.hauteur)}")
        self.largeur_label.setText(f"Largeur: {int(self.largeur)}")
        self.nb_frames_label.setText(f"Nombre de frames: {int(self.nb_frames)}")
        self.heuredebut_label.setText("Heure de debut: ")
        self.latitude_label.setText("Latitude: ")
        self.longitude_label.setText("Longitude: ")
        self.profondeur_label.setText("Profondeur maximale: ")
        self.temperature_label.setText("Temperature au fond: ")
        
        self.layout.addLayout(self.prop1_layout)         
        self.layout.addLayout(self.prop2_layout)

    def init_metadata(self):        
        # Bloc metadata
        self.timestamp_name = self.dirname + '/' + self.num_vid + 'TimeStamp.txt'   
        self.camparam_name =  self.dirname + '/' + self.num_vid + 'CamParam.csv' 
        self.events_name =  self.dirname + '/' + 'Events.csv'
        
        if os.path.isfile(self.timestamp_name) and os.path.isfile(self.camparam_name):
            self.metadata_bool = True
            self.timestamp=np.loadtxt(self.timestamp_name)
            self.metadata = pd.read_csv(self.camparam_name,delimiter=';')
            print(self.timestamp)
            print('Nb de TS: ', len(self.timestamp), 'Nb de frames: ', self.nb_frames)
            
            self.check_layout = QHBoxLayout()
            self.metadata_layout = QHBoxLayout()
            
            for i in range(0, len(self.metadata.columns)):
                column = str(self.metadata.columns[i])
                exec("self.metadata_check"+str(i)+"=QCheckBox('"+column+"',self)")
                exec("self.check_layout.addWidget(self.metadata_check"+str(i)+")")
                #exec("self.metadata_check"+str(i)+".setFixedSize("+"self.metadata_check"+str(i)+".sizeHint())")
                exec("self.metadata_check"+str(i)+".setFixedSize(70,15)")
                exec("self.metadata_check"+str(i)+".setChecked(True)")
                #exec("self.metadata_check"+str(i)+".clicked.connect(self.write_metadata)")
                     
                exec("self.metadata"+str(i)+"_label=QLabel(self)")
                exec("self.metadata_layout.addWidget(self.metadata"+str(i)+"_label)")
            
            self.layout.addLayout(self.check_layout) 
            self.layout.addLayout(self.metadata_layout) 
            
            ## Calcul de la profondeur et de la température au fond       
            self.heure_debut = self.metadata['HMS'][0]
            self.pression_min = min(self.metadata['Pression'])
            self.pression_max = max(self.metadata['Pression'])
            index_max = np.argmax(self.metadata['Pression'])
            self.temperature = self.metadata['TempC'][index_max]
            self.profondeur = (self.pression_max-self.pression_min)/100.91 #(accélaration * densité edm)
            self.heuredebut_label.setText(f"Heure de début: {self.heure_debut}")
            self.profondeur_label.setText(f"Profondeur maximale: {self.profondeur:.1f} m")
            self.temperature_label.setText(f"Temperature au fond: {self.temperature} C")
           
            ## Extraction et affichage des évènements moteur
            self.events = pd.read_csv(self.events_name,delimiter=';')
            self.events_moteur=[]
                        
            for i in range(0, len(self.events['Heure'])):
                frame =int(self.fps * ((self.HMS2S(self.events['Heure'][i])-self.HMS2S(self.heure_debut))))
                if frame >= 0 and frame <= self.nb_frames:
                    if self.events['Event'][i] == 'START MOTEUR' or self.events['Event'][i] == 'END MOTEUR':
                        self.events_moteur.append(frame)
            
            self.slider.setTickPositions(self.events_moteur)

        else:
            self.metadata_bool = False
    
    def init_ImageHisto(self):
        self.histo_bool = True

        self.image_label = QLabel(self)
        self.image_label.setFixedWidth(int(self.hauteur/(2*self.scaling)))
        self.image_label.setFixedHeight(int(self.hauteur/(4*self.scaling)))
      
        self.plot_graph = pg.PlotWidget()
        self.plot_graph.setFixedWidth(int(self.hauteur/(4*self.scaling)))
        self.plot_graph.setFixedHeight(int(self.hauteur/(4**self.scaling)))
        self.AxeX = np.linspace(0,255,256)        
        self.penR = pg.mkPen(color=(255, 0, 0),width = 2)
        self.penV = pg.mkPen(color=(0, 255, 0),width = 2)
        self.penB = pg.mkPen(color=(0, 0, 255), width = 2)
        self.plot_graph.setXRange(0, 255)
        self.plot_graph.setYRange(0, 50000)
        self.plot_graph.setBackground((255,255,255,0))
        self.plot_graph.setTitle("Histogram RVB", color="k", size="10pt")
     
        
        self.vertical_layout = QVBoxLayout(self)
        self.vertical_layout.addWidget(self.plot_graph)
        self.vertical_layout.addWidget(self.image_label)
        self.vertical_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.video_layout.addLayout(self.vertical_layout)      

              
    def clearLayout(self,layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

###############################################################################
# Lecture de la video
    
    def play_video(self):
        if self.cap and not self.playing:
            self.playing = True
            coef = 1
            if self.menu_vitesse.currentText() == self.vitesses[0]:
                coef = 1
            elif self.menu_vitesse.currentText() == self.vitesses[1]:
                coef = 0.5
            elif self.menu_vitesse.currentText() == self.vitesses[2]:
                coef = 2
                
            self.timer.start(int(1./coef*self.displayframeduration))  

    def pause_video(self):
        if self.cap and self.playing:
            self.playing = False
            self.timer.stop()
            
    def move_frame(self,entier):
        frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES,frame_number + entier - 1 )    
        ret, self.frame = self.cap.read()
        if ret:
            self.frame_svg = self.frame
            self.display_frame()
            self.slider.setValue(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)))
        
        
    def next_frame_slot(self):
        if self.playing:
            if self.cap:
                ret, self.frame = self.cap.read()
                if ret:
                    self.frame_svg = self.frame
                    self.display_frame()
                    self.slider.setValue(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)))
                else:
                    self.timer.stop()
                    #self.cap.release()
                
    def display_frame(self):
        frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        self.frame_number_label.setText(f"Frame Number: {frame_number}")
        if self.metadata_bool:
            TS = self.timestamp[frame_number-1] # décalage d'une unité entre le TS et le numéro de frame 
            self.timestamp_label.setText(f"Timestamp: {TS}")
            self.write_metadata()
        self.time_label.setText(self.frame2time())
        image = QImage(self.frame, self.frame.shape[1], self.frame.shape[0], QImage.Format.Format_BGR888)
        pixmap = QPixmap.fromImage(image)
        self.pixmap2 = pixmap.scaledToWidth(int(self.largeur/2)) ###  ici pour diviser la taille de la fenêtre par deux
        self.video_label.setPixmap(self.pixmap2)
        self.Histogram()

    def set_position(self, position):
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)
            ret, self.frame = self.cap.read()
            if ret:
                self.frame_svg = self.frame
                self.display_frame()
                
    def set_position2(self, position):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)
            
    def frame2time(self):
        frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        TempsEnMs = (frame_number*self.frameduration // 1000 ) * 1000
        HMSstr = str(datetime.timedelta(milliseconds = TempsEnMs))
        return HMSstr 
    
    def HMS2S(self,hms):
        h=int(hms.split('h')[0])
        m=int(hms.split('h')[1].split('m')[0])
        s=int(hms.split('h')[1].split('m')[1].split('s')[0])
        return h*3600+m*60+s
    
    def write_metadata(self):
        frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        i=int(frame_number/(self.fps*5))
        for j in range(0, len(self.metadata.columns)):
             if eval("self.metadata_check"+str(j)+".isChecked()"):
                column = str(self.metadata.columns[j])
                value = str(self.metadata[column][i])
                exec("self.metadata"+str(j)+"_label.setText('"+column+": "+value+"')")
    
###############################################################################
# Création des évènements

    def add_line(self,csv_file,ligne):
        try:
            with open(csv_file,'a') as csv_variable:
                csv_variable.write(ligne + '\n')
                csv_variable.flush() 
                csv_variable.close()
        except:
            print('Problème écriture dans le CSV Event')    
    
    def start_event(self):
        if self.cap.isOpened():
            self.start_ev = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.frame_ev_start_label.setText(f"Event start : {self.start_ev}")
       
    def end_event(self):
        if self.cap.isOpened():
            self.end_ev = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.frame_ev_end_label.setText(f"Event start: {self.end_ev}") 
    
    def save_event(self):
        if self.end_ev and self.start_ev:
            self.events_list.append([self.start_ev,self.end_ev])
            event_line = f'{self.start_ev};{self.end_ev};{self.event_vignette.currentText()};{self.event_vignette2.currentText()}'        
            self.add_line(self.event_csv_name,event_line)
            
            self.start_ev = None
            self.end_ev = None
            self.slider.setTick2Positions([])
            self.slider.setTick2Positions(self.events_list)
        else:
            print('Evènement non défini')
            
    def reset_event(self):       
        self.events_list = []
        self.slider.setTick2Positions(self.events_list)
        
    
        
###############################################################################
# Segmentation de la vidéo

    def start_section(self):
        if self.cap.isOpened():
            self.start_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.frame_start_label.setText(f"Start Frame: {self.start_pos}")
       
    def end_section(self):
        if self.cap.isOpened():
            self.end_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.frame_end_label.setText(f"End Frame: {self.end_pos}")
    
    def save_section(self):
        if self.workspace != "" and self.folder_name != "":
            folder = self.workspace+'/'+self.folder_name
        else:
            folder = self.repetoirecourant     
        
        # Segmentation de la vidéo
        if self.cap.isOpened() and self.start_pos < self.end_pos:              
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_pos)
            out = cv2.VideoWriter(folder + '/'+ self.num_vid + 'Video.mp4',
                                  cv2.VideoWriter_fourcc(*'mp4v'),
                                  self.fps,
                                  (self.largeur,
                                   self.hauteur))
           
            i=1
            for _ in range(self.start_pos, self.end_pos):
                ret, frame = self.cap.read()
                self.progress.setValue(int(100*i/(self.end_pos-self.start_pos)))
                if not ret:
                    break
                out.write(frame)
                i=i+1
            out.release()
            QMessageBox.information(self, 'Succès', f'Vidéo segmentée dans le répertoire  \n'+folder)
            self.progress.setValue(0)
        
            
        #Nouvelles metadata
        if self.metadata_bool == True:
            # Nouveaux TS
            self.new_timestamp_name = folder+'/'+ self.num_vid +"TimeStamp.txt"
            file = open(self.new_timestamp_name, "w+")
            content = self.timestamp[self.start_pos-1:self.end_pos-1]
            for line in content:
                file.write(str(line) + "\n")         
            file.close()
            # Nouveaux csv metadata
            self.new_camparam_name = folder +'/'+ self.num_vid + 'CamParam.csv' 
            self.new_events_name = folder + '/Events.csv'
                      
            copy(self.events_name, self.new_events_name)
            copy(self.camparam_name, self.new_camparam_name)
        
            print(self.frame2time(self.start_pos),self.frame2time(self.end_pos))
            
        
        # Nouveau csv évènement
        self.new_event_csv_name = folder+'/Evenements.csv'
        event_line = "StartFrame;EndFrame;EventType;Species"        
        self.add_line(self.new_event_csv_name,event_line)
                       
        for i in range(0, len(self.evenement['StartFrame'])):
            start_ev = self.evenement['StartFrame'][i] 
            end_ev = self.evenement['EndFrame'][i] 
            type_ev = self.evenement['EventType'][i]
            species_ev = self.evenement['Species'][i]
            if start_ev < self.start_pos and self.start_pos <= end_ev < self.end_pos:
                print('Evenement raboté par la gauche')
                new_start_ev = 0
                new_end_ev = end_ev - self.start_pos
                event_line = f'{new_start_ev};{new_end_ev};{type_ev};{species_ev}'        
                self.add_line(self.new_event_csv_name,event_line)
            elif 0 <= start_ev < self.end_pos and 0 <= end_ev < self.end_pos :
                print('Evenement non raboté')
                new_start_ev = start_ev - self.start_pos
                new_end_ev = end_ev - self.start_pos
                event_line = f'{new_start_ev};{new_end_ev};{type_ev};{species_ev}'        
                self.add_line(self.new_event_csv_name,event_line)
            elif 0 <= start_ev < self.end_pos  and end_ev >= self.end_pos:
                print('Evenement raboté par la droite')
                new_start_ev = start_ev - self.start_pos
                new_end_ev = self.end_pos-self.start_pos+1
                event_line = f'{new_start_ev};{new_end_ev};{type_ev};{species_ev}'        
                self.add_line(self.new_event_csv_name,event_line)
            else:
                print('Evenement oublie')

    def save_section2(self):
        if self.workspace != "" and self.folder_name != "":
            folder = self.workspace+'/'+self.folder_name
        else:
            folder = self.repetoirecourant       
        if self.cap.isOpened() and self.start_pos < self.end_pos:
            T1 = round(self.start_pos / self.fps)
            T2 = round(self.end_pos / self.fps)
            ffmpeg_extract_subclip(self.vidname,T1,T2,targetname = folder + '/'+ self.num_vid + 'FastSegmentedVideo.mp4')
            QMessageBox.information(self, 'Succès', f'Vidéo segmentée dans le répertoire  \n'+folder)
    
###############################################################################
# Outils images
    
    def HE(self):
        self.pause_video()        
        frame_HE = process_image_HE(self.frame,3,3,3)
        self.frame = frame_HE     
        self.display_frame() 
               
    def DH(self):
        self.pause_video()
        A = atm_calculation(self.frame)
        frame_DH = process_image_dehaze(self.frame,A)
        self.frame = frame_DH     
        self.display_frame() 
        
    def RT(self):
        self.pause_video()
        self.frame = self.frame_svg
        self.display_frame()
       
    def Histogram(self):  
        if self.histo_button.isChecked():
            self.plot_graph.clear()
            self.plot_graph.plot(self.AxeX,cv2.calcHist([self.frame],[0],None,[256],[0,256])[:,0],pen=self.penB)
            self.plot_graph.plot(self.AxeX,cv2.calcHist([self.frame],[1],None,[256],[0,256])[:,0],pen=self.penV)
            self.plot_graph.plot(self.AxeX,cv2.calcHist([self.frame],[2],None,[256],[0,256])[:,0],pen=self.penR)
        else:
            self.plot_graph.clear()
        
    
    def extract_image(self,param):
        """ Enregistrement de la frame courante"""
        num_frame = f"{int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)):05d}"
        im_name = str(param)+num_frame+".png"
        if self.workspace != "" and self.folder_name != "":
            folder = self.workspace+'/'+self.folder_name
        else:
            folder = self.repetoirecourant
            
        image = QImage(self.frame, self.frame.shape[1], self.frame.shape[0], QImage.Format.Format_BGR888)
        image.save(folder+'/'+im_name)    
        QMessageBox.information(self, 'Succès', f'Image sauvegardée dans le répertoire  \n'+folder)

###############################################################################
# Routine dérushage
             
    def openCampaignFolder(self):
        # Ouvrir la boîte de dialogue de sélection de dossier
        folder = QFileDialog.getExistingDirectory(self, 'Sélectionner un dossier')
        self.campaign_folder = folder
        self.list_campaign = os.listdir(self.campaign_folder)
        self.list_widget.clear()
        self.list_widget.addItems(self.list_campaign)
        
    def print_item_name(self, item):
        # Afficher le nom de l'élément sélectionné dans la console
        self.folder_path = item.text()
        self.rename_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.open2_button.setEnabled(True)
        self.staticmtd_button.setEnabled(True)


    def prompt_new_name(self):
        # Vérifier si un dossier a été sélectionné
        if not hasattr(self, 'folder_path'):
            QMessageBox.warning(self, 'Erreur', 'Aucun dossier sélectionné')
            return
        
        # Demander un nouveau nom pour le dossier via une fenêtre modale
        new_name, ok = QInputDialog.getText(self, 'Nouveau nom', 'Entrez le nouveau nom du dossier:')
        
        # Si l'utilisateur a cliqué sur "OK" et le nouveau nom n'est pas vide
        if ok and new_name.strip():
            self.rename_folder(new_name.strip())
        else:
            QMessageBox.warning(self, 'Erreur', 'Le nom du dossier ne peut pas être vide.')
            
    def rename_folder(self, new_name):
        # Vérifier si un dossier avec ce nom existe déjà
        if os.path.exists(os.path.join(self.campaign_folder,new_name)):
            QMessageBox.warning(self, 'Erreur', 'Un dossier avec ce nom existe déjà.')
            return      
        # Renommer le dossier
        try:
            # on renomme le dossier de la vidéo
            os.rename(os.path.join(self.campaign_folder, self.folder_path), os.path.join(self.campaign_folder,new_name))
            # on renomme le contenu de ce dossier vidéo
            os.rename(os.path.join(os.path.join(self.campaign_folder, new_name),self.folder_path)+".csv", os.path.join(os.path.join(self.campaign_folder, new_name),new_name)+".csv")
            os.rename(os.path.join(os.path.join(self.campaign_folder, new_name),self.folder_path)+".mp4", os.path.join(os.path.join(self.campaign_folder, new_name),new_name)+".mp4")
            os.rename(os.path.join(os.path.join(self.campaign_folder, new_name),self.folder_path)+".txt", os.path.join(os.path.join(self.campaign_folder, new_name),new_name)+".txt")         
            # MàJ du fichier .json et rename
            with open(os.path.join(os.path.join(self.campaign_folder, new_name),self.folder_path)+".json") as f:
                infoStationDict = json.load(f)
                infoStationDict["video"]["codeStation"] = new_name
                with open(os.path.join(os.path.join(self.campaign_folder, new_name),new_name)+".json", mode = 'w', encoding = "utf-8") as ff:
                    ff.write(json.dumps(infoStationDict, indent = 4))
                    #json.dump(infoStationDict,ff)
            os.remove(os.path.join(os.path.join(self.campaign_folder, new_name),self.folder_path)+".json")
                           
            QMessageBox.information(self, 'Succès', f'Dossier et fichiers renommés avec le nouveau codeStation {new_name}')
            
            #MàJ de la liste Widget
            self.list_campaign = os.listdir(self.campaign_folder)
            self.list_widget.clear()
            self.list_widget.addItems(self.list_campaign)
            self.list_widget.findItems(new_name, Qt.MatchFlag.MatchExactly)[0].setSelected(True)
            self.folder_path = new_name
            
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors du renommage: {str(e)}')
            
    def confirm_delete(self):
        
        # Demander une confirmation à l'utilisateur avant de supprimer
        reply = QMessageBox.question(self, 'Confirmation', 
                                     f"Êtes-vous sûr de vouloir supprimer '{self.folder_path}' ?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_item(os.path.join(self.campaign_folder, self.folder_path),self.folder_path)
    
    def delete_item(self, file_path, list_item):
        try:
            # Supprimer le fichier ou dossier
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Pour supprimer un dossier vide uniquement
            else:
                raise ValueError("L'élément sélectionné n'est ni un fichier ni un dossier.")
            
            #MàJ de la liste Widget
            self.list_campaign = os.listdir(self.campaign_folder)
            self.list_widget.clear()
            self.list_widget.addItems(self.list_campaign)
            
            QMessageBox.information(self, 'Succès', f"'{os.path.basename(file_path)}' a été supprimé.")
            self.clear_button.setEnabled(False)
            self.rename_button.setEnabled(False)

        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Erreur lors de la suppression: {str(e)}")        
    
    def open_json(self):
        # Ouvrir une boîte de dialogue pour sélectionner un fichier JSON
        '''
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Fichiers JSON (*.json)")
        if file_dialog.exec():
            file_names = file_dialog.selectedFiles()
            if file_names:
                file_path = file_names[0]
                # Créer et afficher la fenêtre de l'éditeur JSON
        ''' 
        file_path = os.path.join(os.path.join(self.campaign_folder,self.folder_path),self.folder_path)+".json"
        self.json_editor = JSONEditorWindow(file_path)
        self.json_editor.show()
        self.jsonWindow = True
    

###############################################################################
# Création Dossier pour enregistrement des traitements
             
    def openFolderDialog(self):
        # Ouvrir la boîte de dialogue de sélection de dossier
        folder = QFileDialog.getExistingDirectory(self, 'Sélectionner un dossier')
        self.workspace = folder
    
    def createFolder(self):
        self.folder_name = self.folderNameInput.text()      
        if not self.folder_name:
            QMessageBox.warning(self, 'Erreur', 'Veuillez entrer un nom de dossier.')
            return       
        try:
            os.makedirs(self.workspace+'/'+self.folder_name)
            QMessageBox.information(self, 'Succès', f'Le dossier "{self.folder_name}" a été créé avec succès.')
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f'Erreur lors de la création du dossier: {e}')

###############################################################################      
# Outils vignette   

    def mousePressEvent(self, event):
        if self.video == True:
            # suppression précédent rectangle
            self.start_mouse = None
            self.end_mouse = None
            self.display_frame()
            
            if event.button() == Qt.MouseButton.LeftButton:           
                self.drawing = True
                self.start_pos_mouse = event.pos()
                self.end_pos_mouse = self.start_pos 
                self.update()
            if event.button() == Qt.MouseButton.RightButton:
                self.drawing = False
                # suppression du rectangle
                self.start_mouse = None
                self.end_mouse = None
                self.display_frame()
                # suppression de l'aperçu vignette
                emptyImage = QImage()
                emptycropped = QPixmap.fromImage(emptyImage)
                self.image_label.setPixmap(emptycropped)          
                self.update()
            
    def mouseMoveEvent(self, event):
        if self.video == True:
            if self.start_pos_mouse:
                self.end_pos_mouse = event.pos()
                self.update()
    
    def mouseReleaseEvent(self, event):
       if self.video == True:
            if event.button() == Qt.MouseButton.LeftButton:
                self.end_pos_mouse = event.pos()
                self.start_mouse = self.start_pos_mouse 
                self.end_mouse = self.end_pos_mouse               
                self.start_pos_mouse = None
                self.end_pos_mouse = None            
                self.update()
          
    def paintEvent(self, event):
        super().paintEvent(event)        
        if self.video and self.drawing:
            if self.start_mouse and self.end_mouse:
                start_norm = self.start_mouse - self.video_label.pos()
                end_norm = self.end_mouse - self.video_label.pos()
                # Affichage du rectangle sur la fenêtre vidéo
                painter2 = QPainter(self.pixmap2)  
                painter2.setPen(QPen(Qt.GlobalColor.blue, 2, Qt.PenStyle.SolidLine))
                rectangle = QRect(start_norm, end_norm)
                painter2.drawRect(rectangle)  
                self.video_label.setPixmap(self.pixmap2)                   
                # affichage si le cadre est dans l'image
                if 0 <=  start_norm.x() <  int(self.frame.shape[1]/2) and 0 <=  start_norm.y() <  int(self.frame.shape[0]/2) and  0 <=  end_norm.x() <  int(self.frame.shape[1]/2) and 0 <=  end_norm.y() <  int(self.frame.shape[0]/2):
                    # Affichage de la vignette en full résolution
                    rect = QRect(2*start_norm,2*end_norm).normalized()
                    image = QImage(self.frame, self.frame.shape[1], self.frame.shape[0], QImage.Format.Format_BGR888)
                    self.cropped_image = image.copy(rect)
                    cropped_pixmap = QPixmap.fromImage(self.cropped_image)               
                    self.image_label.setPixmap(cropped_pixmap) 
                else :
                    self.drawing = False
                    emptyImage = QImage()
                    emptycropped = QPixmap.fromImage(emptyImage)
                    self.image_label.setPixmap(emptycropped)          
                    self.update()
                    
    def save_selection(self):
        if self.start_mouse and self.end_mouse and self.drawing:         
            try:
                num_frame = f"{int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)):05d}"
                im_name = self.menu_vignette.currentText() + num_frame +".png"
                if self.workspace != "":
                    folder = self.workspace
                else:
                    folder = self.repetoirecourant
                self.cropped_image.save(folder + '/' + im_name)     
                self.update()                                                     
            except Exception as e:
                QMessageBox.critical(self, 'Erreur ', f'{e}')
        else :
           QMessageBox.critical(self, 'Erreur: Pas de rectangle défini') 

    def keyPressEvent(self, event: QKeyEvent):
        # Vérification de la touche pressée
        if event.key() == Qt.Key.Key_P:
            self.startstop()
        if event.key() == Qt.Key.Key_A:
            self.move_frame(10)

    def startstop(self):
        if self.playing == True:
            self.pause_video()
        elif self.playing == False:
            self.play_video()
            
        

###############################################################################            
# Main
def launch_new_extraction_ui() -> int:
    """
    Point d'entrée vers la nouvelle interface extraction (design refondu).
    """
    app = QApplication(sys.argv)
    model = MediaModel()
    campaign_model = CampaignModel()
    view = ExtractionView()
    ExtractionController(view, model, campaign_model)

    window = QMainWindow()
    window.setWindowTitle("Kosmos - Extraction sous-marine")
    window.setCentralWidget(view)
    window.resize(1600, 900)
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(launch_new_extraction_ui())

