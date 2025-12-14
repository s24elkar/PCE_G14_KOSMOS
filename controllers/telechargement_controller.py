"""
CONTRÔLEUR - Page de téléchargement KOSMOS
Architecture MVC

Gère les transferts SSH/SFTP depuis le système KOSMOS embarqué et les
suppressions distantes après transfert. Utilise paramiko pour compatibilité
Windows et QThread pour éviter le gel de l'interface.
"""
import os
import stat
import socket
from pathlib import Path
from typing import Callable, Dict

import paramiko
from PyQt6.QtCore import QObject, QThread, pyqtSignal


class TelechargementService:
    """
    Service bas niveau pour les opérations SSH/SFTP avec le KOSMOS.
    
    Encapsule la logique réseau pure (pas de Qt) pour permettre la réutilisation.
    """

    def __init__(self, ip: str, user: str, password: str, port: int = 22, timeout: int = 30):
        self.ip = ip
        self.user = user
        self.password = password
        self.port = port
        self.timeout = timeout

    def _connect(self, log_cb: Callable[[str], None]):
        """
        Établit une connexion SSH avec le KOSMOS.
        
        Configure le keepalive pour éviter les déconnexions sur transferts longs.
        Désactive l'agent SSH et recherche de clés pour compatibilité Windows.
        """
        log_cb(f"Connexion SSH vers {self.ip}:{self.port} ...")
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            client.connect(
                self.ip,
                port=self.port,
                username=self.user,
                password=self.password,
                timeout=self.timeout,
                banner_timeout=self.timeout,
                auth_timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False,
            )
            
            # Keepalive pour maintenir la connexion active
            transport = client.get_transport()
            if transport:
                transport.set_keepalive(15)
            
            log_cb("Connexion SSH établie.")
            return client
            
        except (paramiko.AuthenticationException, paramiko.SSHException, socket.timeout, OSError) as e:
            raise RuntimeError(f"Connexion SSH impossible : {e}")

    def telecharger(self, remote_path: str, destination: str, log_cb: Callable[[str], None]):
        """
        Télécharge un fichier ou répertoire distant via SFTP.
        
        Supporte le téléchargement récursif avec préservation de la structure.
        """
        Path(destination).mkdir(parents=True, exist_ok=True)
        log_cb(f"Téléchargement depuis {self.ip}:{remote_path}")

        client = self._connect(log_cb)
        
        try:
            sftp = client.open_sftp()
            log_cb("Canal SFTP ouvert.")
        except Exception as e:
            client.close()
            raise RuntimeError(f"Ouverture SFTP impossible : {e}")

        try:
            self._download_recursive(sftp, remote_path, destination, log_cb)
            log_cb("Téléchargement terminé.")
        finally:
            sftp.close()
            client.close()

    def _download_recursive(self, sftp: paramiko.SFTPClient, remote_path: str, local_path: str, log_cb: Callable[[str], None]):
        """Télécharge récursivement un répertoire ou fichier distant."""
        try:
            attr = sftp.stat(remote_path)
        except FileNotFoundError as e:
            raise RuntimeError(f"Chemin distant introuvable: {remote_path}") from e

        if stat.S_ISDIR(attr.st_mode):
            # Répertoire : créer localement et parcourir le contenu
            Path(local_path).mkdir(parents=True, exist_ok=True)
            for entry in sftp.listdir_attr(remote_path):
                child_remote = f"{remote_path.rstrip('/')}/{entry.filename}"
                child_local = os.path.join(local_path, entry.filename)
                self._download_recursive(sftp, child_remote, child_local, log_cb)
        else:
            # Fichier : télécharger directement
            log_cb(f"   • {remote_path} → {local_path}")
            try:
                sftp.get(remote_path, local_path)
            except Exception as e:
                raise RuntimeError(f"Échec téléchargement {remote_path}: {e}")

    def supprimer(self, remote_path: str, log_cb: Callable[[str], None]):
        """
        Supprime un fichier ou répertoire distant via commande SSH.
        
        ATTENTION : Opération destructive et irréversible.
        """
        log_cb(f"Suppression à distance : {remote_path}")
        
        client = self._connect(log_cb)
        
        try:
            stdin, stdout, stderr = client.exec_command(f"rm -rf '{remote_path}'")
            err = stderr.read().decode().strip()
            if err:
                raise RuntimeError(err)
            log_cb("Suppression terminée.")
        finally:
            client.close()


class TelechargementWorker(QThread):
    """
    Thread de travail pour opérations réseau longues.
    
    Pattern Worker Thread Qt : Exécute les opérations en arrière-plan
    pour éviter le gel de l'interface.
    """

    log_emis = pyqtSignal(str)
    termine = pyqtSignal(bool, str)

    def __init__(self, params: Dict, action: str):
        """
        Args:
            params : Paramètres de connexion (ip, user, password, remote_path, etc.)
            action : "download" ou "delete"
        """
        super().__init__()
        self.params = params
        self.action = action

    def run(self):
        """Exécute l'action demandée en tâche de fond."""
        try:
            service = TelechargementService(
                self.params["ip"],
                self.params["user"],
                self.params["password"],
                self.params.get("port", 22),
                self.params.get("timeout", 30),
            )

            if self.action == "download":
                service.telecharger(
                    self.params["remote_path"],
                    self.params["destination"],
                    self.log_emis.emit
                )
                self.termine.emit(True, "Téléchargement terminé")
                
            elif self.action == "delete":
                service.supprimer(
                    self.params["remote_path"],
                    self.log_emis.emit
                )
                self.termine.emit(True, "Données supprimées")
                
            else:
                self.termine.emit(False, f"Action inconnue: {self.action}")
                
        except Exception as e:
            self.log_emis.emit(f"Erreur {type(e).__name__}: {e}")
            self.termine.emit(False, str(e))


class TelechargementController(QObject):
    """
    Contrôleur pour la page de téléchargement KOSMOS.
    
    Orchestre les workers pour opérations longues et émet des signaux
    pour feedback utilisateur.
    """

    navigation_demandee = pyqtSignal(str)
    log_emis = pyqtSignal(str)
    telechargement_termine = pyqtSignal(bool, str)
    suppression_terminee = pyqtSignal(bool, str)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.worker = None  # Un seul worker à la fois

    def _demarrer_worker(self, params: Dict, action: str):
        """
        Démarre un worker pour exécuter une action en tâche de fond.
        
        Returns:
            bool : True si démarré, False si opération déjà en cours
        """
        # Empêche les opérations concurrentes
        if self.worker and self.worker.isRunning():
            self.log_emis.emit("Une opération est déjà en cours.")
            return False

        self.worker = TelechargementWorker(params, action)
        self.worker.log_emis.connect(self.log_emis.emit)

        # Connexion du signal selon le type d'action
        if action == "download":
            self.worker.termine.connect(self.telechargement_termine.emit)
        else:
            self.worker.termine.connect(self.suppression_terminee.emit)

        self.worker.finished.connect(self._liberer_worker)
        self.worker.start()
        return True

    def _liberer_worker(self):
        """Libère la référence au worker une fois terminé."""
        self.worker = None

    def lancer_telechargement(self, params: Dict):
        """
        Lance un téléchargement en tâche de fond.
        
        Args:
            params : {ip, user, password, remote_path, destination}
        """
        return self._demarrer_worker(params, "download")

    def supprimer_donnees(self, params: Dict):
        """
        Supprime les données sur le KOSMOS distant.
        
        Args:
            params : {ip, user, password, remote_path}
        """
        return self._demarrer_worker(params, "delete")