from PyQt6.QtCore import QObject, pyqtSignal


class MediaModel(QObject):
    """Modèle contenant les données et la logique métier"""
    
    media_changed = pyqtSignal(str)
    position_changed = pyqtSignal(int)
    duration_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self._current_file = None
        self._position = 0
        self._duration = 0
        self._brightness = 0
        self._contrast = 0
        self._saturation = 0
    
    @property
    def current_file(self):
        return self._current_file
    
    @current_file.setter
    def current_file(self, value):
        self._current_file = value
        self.media_changed.emit(value if value else "")
    
    @property
    def position(self):
        return self._position
    
    @position.setter
    def position(self, value):
        self._position = value
        self.position_changed.emit(value)
    
    @property
    def duration(self):
        return self._duration
    
    @duration.setter
    def duration(self, value):
        self._duration = value
        self.duration_changed.emit(value)
    
    @property
    def brightness(self):
        return self._brightness
    
    @brightness.setter
    def brightness(self, value):
        self._brightness = value
    
    @property
    def contrast(self):
        return self._contrast
    
    @contrast.setter
    def contrast(self, value):
        self._contrast = value
    
    @property
    def saturation(self):
        return self._saturation
    
    @saturation.setter
    def saturation(self, value):
        self._saturation = value