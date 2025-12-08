"""
Fonctions nécessaires au traitement HE et DH ainsi qu'à quelques utilitaires
de correction supplémentaires pour le projet KOSMOS.
"""
import math

import cv2
import matplotlib.pyplot as plt
import numpy as np


##############################################
## Scripts généraux
##############################################


def Float2BGR(I):
    # Conversion d'un float (0 - 1) à nb sur 8 bits (0 - 255)
    erf = I * 255
    src = erf.astype("uint8")
    return src


def BGR2Float(src):
    # Conversion d'un nb sur 8 bits (0 - 255) vers un float
    a = src.astype("float64") / 255
    return a


def AnalyseHisto(I, mask=None):
    """Médiane et écart type de chaque canal, avec masque optionnel."""
    img = I.astype(np.float64)
    if mask is not None:
        valid = mask.astype(bool)
        if img.ndim == 3:
            pixels = img[valid]
        else:
            pixels = img[valid, ...]
    else:
        if img.ndim == 3:
            pixels = img.reshape(-1, img.shape[-1])
        else:
            pixels = img.reshape(-1, 1)

    mean = np.median(pixels, axis=0)
    square = np.std(pixels, axis=0, ddof=0)
    return mean, square


def PlotHistogram(I):
    """Fonction qui donne l'histogramme d'une image"""
    plt.figure()
    color = ("b", "g", "r")
    for i, col in enumerate(color):
        histr = cv2.calcHist([I], [i], None, [256], [0, 256])
        plt.plot(histr, color=col)
    plt.xlim([0, 256])
    plt.legend(color)
    plt.title("Histogramme des canaux RGB")


##############################################
## Egalisation d'histogramme
##############################################


def process_image_HE(I, vB, vG, vR):
    (MeanB, MeanG, MeanR), (SquareB, SquareG, SquareR) = AnalyseHisto(I)
    II = np.zeros(I.shape, dtype=np.float64)
    eps = 1e-6
    II[:, :, 0] = (I[:, :, 0] - MeanB + vB * SquareB) / (2 * max(vB * SquareB, eps))
    II[:, :, 1] = (I[:, :, 1] - MeanG + vG * SquareG) / (2 * max(vG * SquareG, eps))
    II[:, :, 2] = (I[:, :, 2] - MeanR + vR * SquareR) / (2 * max(vR * SquareR, eps))

    III = np.clip(II, 0, 1)
    IV = np.uint8(III * 255)
    return IV


##############################################
## Debrumage
##############################################


def DarkChannel(im, sz):
    """Determine le canal sombre de l'image"""
    b, g, r = cv2.split(im)  # Séparation des 3 canaux
    dc = cv2.min(cv2.min(r, g), b)  # La couleur minimale entre le canal bleu et vert.
    median_ksize = sz if sz % 2 == 1 else sz + 1
    dc8 = np.clip(dc * 255, 0, 255).astype(np.uint8)
    dc = cv2.medianBlur(dc8, median_ksize).astype(np.float32) / 255.0
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (sz, sz))  # Élément structurant pour l'érosion
    dark = cv2.erode(dc, kernel)  # Érosion de l'image en fonction de la couleur minimale
    return dark


def DarkChannelWater(im, sz):
    """Determine le canal sombre de l'image"""
    b, g, r = cv2.split(im)  # Séparation des 3 canaux
    dc = cv2.min(g, b)  # La couleur minimale entre le canal bleu et vert
    median_ksize = sz if sz % 2 == 1 else sz + 1
    dc8 = np.clip(dc * 255, 0, 255).astype(np.uint8)
    dc = cv2.medianBlur(dc8, median_ksize).astype(np.float32) / 255.0
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (sz, sz))  # Élément structurant pour l'érosion
    dark = cv2.erode(dc, kernel)  # Érosion de l'image en fonction de la couleur minimale
    return dark


def AtmLight(im, dark):
    """Estimation de la lumière atmosphérique"""
    [h, w] = im.shape[:2]
    imsz = h * w
    numpx = int(max(math.floor(imsz / 100), 1))  # Définition du nombre de valeurs à garder (0.1%)
    darkvec = dark.reshape(imsz)  # Façonne le tableau dark sans modification de données
    imvec = im.reshape(imsz, 3)
    indices = darkvec.argsort()  # Tri croissant des indices du tableau
    indices = indices[imsz - numpx :]  # Suppression des indices les plus faibles
    brightest = imvec[indices]
    A = np.mean(brightest, axis=0, keepdims=True)
    return A


def TransmissionEstimate(im, A, sz, omega=0.6):
    im3 = np.empty(im.shape, im.dtype)  # Initialisation du tableau correspondant à la transmission

    for ind in range(0, 3):
        denom = max(A[0, ind], 1e-6)
        im3[:, :, ind] = im[:, :, ind] / denom  # im3 = im/A (voir formule)
    transmission = 1 - omega * DarkChannel(im3, sz)  # Formule pour trouver la transmission
    return transmission


def Guidedfilter(im, p, r=60, eps=0.0001):
    """Filtre l'image d'entrée (p) sous la direction d'une autre image (im).
    Recherche les coefficients a et b qui minimisent la différence entre la sortie q et l'entrée p."""
    mean_I = cv2.boxFilter(im, cv2.CV_64F, (r, r))
    mean_p = cv2.boxFilter(p, cv2.CV_64F, (r, r))
    mean_Ip = cv2.boxFilter(im * p, cv2.CV_64F, (r, r))
    cov_Ip = mean_Ip - mean_I * mean_p

    mean_II = cv2.boxFilter(im * im, cv2.CV_64F, (r, r))
    var_I = mean_II - mean_I * mean_I

    a = cov_Ip / (var_I + eps)  # calcul de a selon la formule (voir doc)
    b = mean_p - a * mean_I  # calcul de b selon la formule (voir doc)

    mean_a = cv2.boxFilter(a, cv2.CV_64F, (r, r))  # moyenne de a
    mean_b = cv2.boxFilter(b, cv2.CV_64F, (r, r))  # moyenne de b

    q = mean_a * im + mean_b  # transmission affinée
    return q


def TransmissionRefine(im, et, r=60, eps=0.0001):
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)  # Image en teinte de gris
    gray = np.float64(gray) / 255
    t = Guidedfilter(gray, et, r, eps)
    return t


def Recover(im, t, A, tx=1.0):
    """Fonction servant à retrouver l'éclat"""
    res = np.empty(im.shape, im.dtype)  # Initialisation du tableau correspondant à l'éclat
    tt = np.zeros((t.shape[0], t.shape[1], 3))  # Initialisation du tableau tt

    tt[:, :, 0] = cv2.max(t, tx)  # blue
    tt[:, :, 1] = cv2.max(t, tx)  # green
    tt[:, :, 2] = cv2.max(t, tx)  # red

    for ind in range(0, 3):
        res[:, :, ind] = (im[:, :, ind] - A[0, ind]) / tt[:, :, ind] + A[0, ind]
    return res


def atm_calculation(II):
    srcc = BGR2Float(II)
    dark = DarkChannel(srcc, 15)
    A = AtmLight(srcc, dark)
    return A


def water_calculation(II):
    srcc = BGR2Float(II)
    dark = DarkChannelWater(srcc, 15)
    A = AtmLight(srcc, dark)
    return A


def process_image_dehaze(II, A, window=15, omega=0.6, guided_radius=60, guided_eps=0.0001, tx=0.1):
    srcc = BGR2Float(II)
    te = TransmissionEstimate(srcc, A, window, omega=omega)
    t = TransmissionRefine(II, te, r=guided_radius, eps=guided_eps)
    III = Recover(srcc, t, A, tx)
    IV = np.clip(III * 255, 0, 255)
    V = np.uint8(IV)
    return V


##############################################
## Denoising et évaluations
##############################################


def denoise_image(image, method="nlm", **kwargs):
    """
    Applique un filtre de débruitage sur l'image d'entrée.
    method -> "nlm" (Fast Non-Local Means) ou "bilateral".
    kwargs sont directement passés à l'appel OpenCV.
    """
    if method == "nlm":
        h = kwargs.get("h", 10)
        h_color = kwargs.get("hColor", 10)
        template_window_size = kwargs.get("templateWindowSize", 7)
        search_window_size = kwargs.get("searchWindowSize", 21)
        return cv2.fastNlMeansDenoisingColored(
            image,
            None,
            h,
            h_color,
            template_window_size,
            search_window_size,
        )
    if method == "bilateral":
        diameter = kwargs.get("diameter", 9)
        sigma_color = kwargs.get("sigmaColor", 75)
        sigma_space = kwargs.get("sigmaSpace", 75)
        return cv2.bilateralFilter(image, diameter, sigma_color, sigma_space)
    raise ValueError(f"Unknown denoise method: {method}")


def denoise_batch(frames, method="nlm", **kwargs):
    """
    Exécute un débruitage image par image pour une série de frames
    (utile pour traiter un dossier de captures).
    """
    return [denoise_image(frame, method=method, **kwargs) for frame in frames]


def tenengrad_contrast(image):
    """Renvoie une mesure de netteté basée sur le gradient de Sobel."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    return np.mean(gx**2 + gy**2)


##############################################
## Détection simple (espèces / événements)
##############################################


def init_motion_detector(history=500, var_threshold=16, detect_shadows=True):
    """
    Initialise un soustracteur de fond OpenCV.
    Utile pour repérer des sujets mobiles (poissons, plongeur...).
    """
    return cv2.createBackgroundSubtractorMOG2(
        history=history, varThreshold=var_threshold, detectShadows=detect_shadows
    )


def detect_moving_subjects(frame, subtractor, min_area=400):
    """
    Retourne les contours détectés comme sujets mobiles.
    Renvoie une liste de dictionnaires avec bounding boxes et surfaces.
    """
    fg_mask = subtractor.apply(frame)
    _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    detections = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(contour)
        detections.append({"bbox": (x, y, w, h), "area": area})
    return detections


def annotate_detections(frame, detections, color=(0, 255, 0)):
    """Dessine les bounding boxes sur une copie de l'image fournie."""
    annotated = frame.copy()
    for detection in detections:
        x, y, w, h = detection["bbox"]
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
    return annotated


# Il peut y avoir des messages d'erreurs du style :
"""RuntimeWarning: divide by zero encountered in divide
  im3[:,:,ind] = im[:,:,ind]/A[0,ind] # im3 = im/A (voir formule)
"""
# ils surviennent quand l'image brut ne contient quasiment pas de rouge. Ce n'est normalement pas bloquant.


##############################################
## Filtres rapides (Vectorisés)
##############################################

class UnderwaterFilters:
    """
    Collection de filtres rapides (vectorisés) pour améliorer des images sous-marines.
    Les méthodes opèrent sur des frames BGR (numpy.ndarray uint8).
    """

    @staticmethod
    def correct_blue_dominance(frame: np.ndarray, factor: float = 0.12) -> np.ndarray:
        """
        Réduit une dominante bleue en renforçant légèrement les canaux R et G.
        :param factor: intensité de correction (0.12 => +12% sur R/G).
        """
        r, g, b = cv2.split(frame)
        r = cv2.add(r, (r * factor).astype(np.uint8))
        g = cv2.add(g, (g * factor).astype(np.uint8))
        corrected = cv2.merge((r, g, b))
        return np.clip(corrected, 0, 255).astype(np.uint8)

    @staticmethod
    def apply_gamma(frame: np.ndarray, gamma: float = 1.2) -> np.ndarray:
        """
        Correction gamma via table de correspondance.
        gamma > 1 éclaircit les tons moyens.
        """
        gamma = max(gamma, 0.01)
        inv_gamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** inv_gamma * 255 for i in np.arange(256)]).astype("uint8")
        return cv2.LUT(frame, table)

    @staticmethod
    def enhance_contrast(frame: np.ndarray, clip_limit: float = 2.0, tile_grid: tuple[int, int] = (8, 8)) -> np.ndarray:
        """
        Améliore le contraste local via CLAHE sur la luminance (Y dans YCrCb).
        """
        ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(ycrcb)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid)
        y = clahe.apply(y)
        merged = cv2.merge((y, cr, cb))
        return cv2.cvtColor(merged, cv2.COLOR_YCrCb2BGR)

    @staticmethod
    def denoise(frame: np.ndarray, h: float = 10.0) -> np.ndarray:
        """
        Réduit le bruit dans l'image en utilisant la méthode fastNlMeansDenoisingColored de OpenCV.
        """
        return cv2.fastNlMeansDenoisingColored(frame, None, h, h, 7, 21)

    @staticmethod
    def sharpen(frame: np.ndarray) -> np.ndarray:
        """Applique un filtre de netteté simple."""
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        return cv2.filter2D(frame, -1, kernel)

    @staticmethod
    def apply_contrast_brightness(frame: np.ndarray, contrast: int, brightness: int) -> np.ndarray:
        """Ajuste le contraste et la luminosité. contrast/brightness de -100 à 100."""
        alpha = 1.0 + contrast / 100.0  # Facteur de contraste
        beta = brightness  # Décalage de luminosité
        adjusted = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
        return adjusted

    @staticmethod
    def apply_saturation(frame: np.ndarray, value: int) -> np.ndarray:
        """Ajuste la saturation. value de -100 à 100."""
        if value == 0: return frame
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        factor = 1.0 + value / 100.0
        s = np.clip(s * factor, 0, 255).astype(np.uint8)
        hsv = cv2.merge([h, s, v])
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    @staticmethod
    def apply_hue(frame: np.ndarray, value: int) -> np.ndarray:
        """Ajuste la teinte. value de -90 à 90."""
        if value == 0: return frame
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        # L'échelle de teinte dans OpenCV est 0-179
        h = (h.astype(np.int32) + value) % 180
        hsv = cv2.merge([h.astype(np.uint8), s, v])
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    @staticmethod
    def apply_temperature(frame: np.ndarray, value: int) -> np.ndarray:
        """Ajuste la température de couleur. value de -100 (froid) à 100 (chaud)."""
        if value == 0: return frame
        # Convertir la valeur en un ajustement pour les canaux bleu et rouge
        blue_factor = 1.0 - (value / 200.0 if value < 0 else 0)
        red_factor = 1.0 + (value / 200.0 if value > 0 else 0)
        b, g, r = cv2.split(frame)
        b = np.clip(b * blue_factor, 0, 255).astype(np.uint8)
        r = np.clip(r * red_factor, 0, 255).astype(np.uint8)
        return cv2.merge([b, g, r])

    @staticmethod
    def apply_lut(frame: np.ndarray, lut: list) -> np.ndarray:
        """Applique une table de correspondance (Look-Up Table)."""
        if len(lut) != 256: return frame
        table = np.array(lut, dtype=np.uint8)
        return cv2.LUT(frame, table)
