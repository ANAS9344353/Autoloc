import logging
import requests
from bs4 import BeautifulSoup
import re
import concurrent.futures

# Logger structure (configuration dans backend/settings.py)
logger = logging.getLogger(__name__)


# Marques de voitures connues (utilisees pour extraire la marque du titre)
MARQUES = [
    "Hyundai", "Renault", "Peugeot", "Toyota", "BMW", "Mercedes", "Audi",
    "Fiat", "Citroen", "Citroën", "Volkswagen", "VW", "Dacia", "Nissan", "Honda",
    "Mazda", "Ford", "Chevrolet", "Kia", "Seat", "Skoda", "Opel", "Suzuki",
    "Mitsubishi", "Jeep", "Land Rover", "Range Rover", "Mini", "Volvo",
    "Tesla", "Porsche", "Lexus", "Smart", "Alfa Romeo", "Lancia", "MG",
    "Changan", "Geely", "BYD", "Cupra",
]

# Modeles connus -> Marque (utilises quand le titre ne contient que le modele,
# ex: "CLIO 5 LOCATION" -> on devine Renault grace a "Clio")
MODELE_VERS_MARQUE = {
    "clio": "Renault", "megane": "Renault", "kadjar": "Renault", "captur": "Renault",
    "sandero": "Dacia", "logan": "Dacia", "duster": "Dacia", "lodgy": "Dacia",
    "dokker": "Dacia", "jogger": "Dacia", "stepway": "Dacia", "bigster": "Dacia",
    "208": "Peugeot", "308": "Peugeot", "2008": "Peugeot", "3008": "Peugeot",
    "5008": "Peugeot", "508": "Peugeot", "partner": "Peugeot",
    "c3": "Citroen", "c4": "Citroen", "c5": "Citroen", "berlingo": "Citroen",
    "ami": "Citroen",
    "tucson": "Hyundai", "accent": "Hyundai", "i10": "Hyundai", "i20": "Hyundai",
    "i30": "Hyundai", "elantra": "Hyundai", "sonata": "Hyundai", "creta": "Hyundai",
    "picanto": "Kia", "rio": "Kia", "ceed": "Kia", "sportage": "Kia",
    "seltos": "Kia",
    "yaris": "Toyota", "corolla": "Toyota", "rav4": "Toyota", "auris": "Toyota",
    "hilux": "Toyota", "land cruiser": "Toyota",
    "golf": "Volkswagen", "polo": "Volkswagen", "passat": "Volkswagen",
    "tiguan": "Volkswagen", "t-roc": "Volkswagen", "troc": "Volkswagen",
    "fiesta": "Ford", "focus": "Ford", "fiesta": "Ford", "kuga": "Ford",
    "qashqai": "Nissan", "juke": "Nissan", "micra": "Nissan",
    "500": "Fiat", "panda": "Fiat", "tipo": "Fiat", "punto": "Fiat",
    "express": "Renault",
    "renegade": "Jeep", "compass": "Jeep", "wrangler": "Jeep",
    "x1": "BMW", "x3": "BMW", "x5": "BMW", "serie 1": "BMW", "serie 3": "BMW",
    "classe a": "Mercedes", "classe c": "Mercedes", "classe e": "Mercedes",
    "gla": "Mercedes", "glc": "Mercedes",
    "a3": "Audi", "a4": "Audi", "q3": "Audi", "q5": "Audi",
}

VILLES_MAROC = [
    "Casablanca",
    "Casablanca-",
    "Rabat", "Salé", "Sale",
    "Marrakech",
    "Tanger",
    "Tétouan", "Tetouan",
    "Fès", "Fes",
    "Agadir",
    "Meknès", "Meknes",
    "Kenitra", "Kénitra",
    "Mohammedia",
    "Oujda",
    "Beni Mellal",
    "Nador",
    "El Jadida",
    "Settat",
    "Berkane",
    "Khouribga",
    "Taza",
    "Ouarzazate",
    "Essaouira",
    "Safi",
    "Larache",
    "Khemisset",
    "Temara", "Témara",
    "Dakhla",
    "Laayoune",
    "Ifrane",
    "Berrechid",
    "Errachidia",
    "Chefchaouen",
    "Taroudant",
    "Deroua",
    "Nouaceur",
    "Nouaceur-",
]


HEADERS_NAVIGATEUR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9",
}


def _nettoyer_titre(titre):
    """Enleve les mots generiques de location pour faciliter l'extraction marque/modele."""
    cleaned = re.sub(
        r'\b(location|location de voitures|location de voiture|voitures de location|'
        r'voiture de location|voiture|voitures|à louer|a louer|loué|louer|au maroc|'
        r'a partir de|pas cher|aéroport|aeroport|sans caution)\b',
        '', titre, flags=re.I
    ).strip()
    cleaned = re.sub(r'[_\-\|]+', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def _extraire_marque_modele(titre):
    """
    Extrait (marque, modele) du titre.
    GARANTIE : retourne TOUJOURS des valeurs non-vides.
    Strategie :
    1. Chercher une marque connue dans le titre
    2. Si rien, chercher un modele connu et deduire la marque
    3. Sinon valeurs par defaut
    """
    titre_propre = _nettoyer_titre(titre) or titre

    # Etape 1 : chercher une marque connue
    for m in MARQUES:
        pattern = r'\b' + re.escape(m) + r'\b'
        if re.search(pattern, titre_propre, re.I):
            modele = re.sub(pattern, '', titre_propre, flags=re.I).strip()
            modele = re.sub(r'\s+', ' ', modele).strip(' -|,')
            return m.capitalize() if not m.isupper() else m, (modele if modele else "Modele non specifie")

    # Etape 2 : chercher un modele connu pour deduire la marque
    titre_lower = titre_propre.lower()
    for modele_cle, marque in MODELE_VERS_MARQUE.items():
        if re.search(r'\b' + re.escape(modele_cle) + r'\b', titre_lower):
            # Trouver le modele complet (avec version eventuelle, ex: "Clio 5")
            m_match = re.search(
                r'\b' + re.escape(modele_cle) + r'(?:\s*\d+)?\b',
                titre_propre, re.I
            )
            modele_complet = m_match.group(0) if m_match else modele_cle.capitalize()
            return marque, modele_complet

    # Etape 3 : valeurs par defaut (eviter de prendre "De", "La" etc comme marque)
    return "Marque non specifiee", titre_propre or titre or "Modele non specifie"


def _extraire_ville(texte):
    """Cherche une ville marocaine connue dans le texte.

    Note: certains scrapers peuvent produire des tokens avec accents/variantes.
    On normalise un minimum pour améliorer la detection.
    """
    if not texte:
        return "Maroc"

    t = texte
    # Normalisation basique (accents)
    t = t.replace('é', 'e').replace('è', 'e').replace('ê', 'e')
    t = t.replace('à', 'a').replace('â', 'a')
    t = t.replace('î', 'i').replace('ï', 'i').replace('ô', 'o').replace('ö', 'o')

    for v in VILLES_MAROC:
        v_norm = v
        v_norm = v_norm.replace('é', 'e').replace('è', 'e').replace('ê', 'e')
        v_norm = v_norm.replace('à', 'a').replace('â', 'a')
        v_norm = v_norm.replace('î', 'i').replace('ï', 'i').replace('ô', 'o').replace('ö', 'o')

        # Utiliser \\b marche mal sur certains tirets; on évite 
        # les faux-negatifs en matchant sur le texte normalisé.
        if re.search(re.escape(v_norm), t, re.I):
            return v

    return "Maroc"



def _extraire_prix(texte):
    """Cherche un prix en DH dans le texte.

    Corrige les faux positifs du type "5 179 DH" quand le vrai prix est "179 DH".
    (On enlève les séparateurs d'espaces et on limite la longueur.)
    """
    if not texte:
        return "Demander le prix"

    # Prend la première occurrence "<nombre> DH". Le nombre peut contenir espaces.
    m = re.search(r'(\d[\d\s]*)\s*(?:DH|Dhs|dh|MAD)', texte, re.I)
    if not m:
        return "Demander le prix"

    raw = m.group(1).strip().replace(' ', '')

    # Exemple indésirable: 5179 (affiché comme "5 179") -> on ne garde que le dernier bloc (179)
    # Heuristique: si le nombre fait >= 4 chiffres, on garde les 3 derniers chiffres.
    if raw.isdigit() and len(raw) >= 4:
        raw = raw[-3:]

    return f"{raw} DH"



def _construire_voiture(titre, ville, prix, url, image, source):
    """Construit un dict voiture avec garantie que marque/modele/source soient remplis."""
    marque, modele = _extraire_marque_modele(titre)
    nom = titre.strip() if titre and len(titre.strip()) >= 2 else (marque + " " + modele)

    return {
        "nom": nom,
        "marque": marque,
        "modele": modele,
        "ville": ville or "Maroc",
        "prix": prix or "Demander le prix",
        "url": url,
        "image": image or "",
        "source": source,
        "is_owner_listing": False,
    }


# =================== SCRAPER 1 : AVITO.MA ===================
def _avito_extraire_image_detail(url_annonce):
    """Ouvre la page détail Avito et extrait une image (fallback quand la liste ne donne rien)."""
    try:
        r = requests.get(url_annonce, headers=HEADERS_NAVIGATEUR, timeout=12)
        s = BeautifulSoup(r.text, "html.parser")

        # Priorité: classifieds/images
        for img in s.find_all("img"):
            src = img.get("src", "") or img.get("data-src", "") or img.get("data-original", "")
            if src and "/classifieds/images/" in src:
                if src.startswith("//"):
                    return "https:" + src
                if src.startswith("/"):
                    return "https://www.avito.ma" + src
                return src

        # Fallback: première image non-boutique
        for img in s.find_all("img"):
            src = img.get("src", "") or img.get("data-src", "") or img.get("data-original", "")
            if not src or src.startswith("data:"):
                continue
            if "/stores/" in src:
                continue
            if src.startswith("//"):
                return "https:" + src
            if src.startswith("/"):
                return "https://www.avito.ma" + src
            return src

        return ""
    except Exception:
        return ""


def scraper_avito():
    """
    Scrape la section location de voitures sur Avito.ma.
    1) Dans la liste: on cherche l'image principale (content.avito.ma/classifieds/images/)
    2) Si image manquante: fallback en ouvrant la page détail Avito.
    """
    url = "https://www.avito.ma/fr/maroc/location_de_voitures-%C3%A0_louer"
    voitures = []


    try:
        reponse = requests.get(url, headers=HEADERS_NAVIGATEUR, timeout=15)
        soup = BeautifulSoup(reponse.text, "html.parser")

        liens = soup.find_all("a", href=True)
        deja_vu = set()

        for lien in liens:
            href = lien["href"]
            if "/voitures_de_location/" not in href or not href.endswith(".htm"):
                continue

            url_annonce = href if href.startswith("http") else "https://www.avito.ma" + href
            if url_annonce in deja_vu:
                continue
            deja_vu.add(url_annonce)

            # Chercher l'image principale (sur content.avito.ma/classifieds/images/)
            # NB: les avatars de boutique sont sur content.avito.ma/stores/ - on les ignore
            titre = ""
            image_url = ""

            # 1) Priorité: src contenant clairement /classifieds/images/
            for img in lien.find_all("img"):
                src = (
                    img.get("src", "")
                    or img.get("data-src", "")
                    or img.get("data-original", "")
                )
                if not src:
                    continue
                if "/classifieds/images/" in src:
                    image_url = src
                    titre = (img.get("alt", "") or "").strip()
                    break

            # Normalisation URL (quand src commence par // ou /)
            if image_url and image_url.startswith("//"):
                image_url = "https:" + image_url
            elif image_url and image_url.startswith("/"):
                image_url = "https://www.avito.ma" + image_url

            # 2) Fallback: si aucune image /classifieds/images/ n'a été trouvée,
            # on prend la première image non-boutique (sans data:)
            if not image_url:
                for img in lien.find_all("img"):
                    src = (
                        img.get("src", "")
                        or img.get("data-src", "")
                        or img.get("data-original", "")
                    )
                    if not src or src.startswith("data:"):
                        continue
                    if "/stores/" in src:
                        continue

                    image_url = src
                    titre = (img.get("alt", "") or "").strip()
                    break

                if image_url and image_url.startswith("//"):
                    image_url = "https:" + image_url
                elif image_url and image_url.startswith("/"):
                    image_url = "https://www.avito.ma" + image_url



            # Fallback titre : depuis le slug de l'URL
            if not titre or len(titre) < 3:
                slug = href.split("/")[-1].replace(".htm", "")
                parties = slug.split("_")
                # Le dernier element est generalement un ID numerique
                if parties and parties[-1].isdigit():
                    parties = parties[:-1]
                titre = " ".join(parties).strip()

            # Extraction ville + prix depuis les tokens textuels
            tokens = [t.strip() for t in lien.stripped_strings if t.strip()]
            texte_complet = " ".join(tokens)

            ville = ""
            for token in tokens:
                if token.lower().startswith("voitures de location dans"):
                    ville = token.split("dans", 1)[1].strip().split(",")[0].strip()
                    break
            if not ville:
                ville = _extraire_ville(texte_complet)

            prix = _extraire_prix(texte_complet)

            # Fallback sur la page détail si aucune image n'a été trouvée dans la liste
            if not image_url:
                image_url = _avito_extraire_image_detail(url_annonce)

            voitures.append(_construire_voiture(
                titre, ville, prix, url_annonce, image_url, "Avito.ma"
            ))


            if len(voitures) >= 25:
                break

    except Exception as e:
        logger.error("[Avito] Erreur : %s", e, exc_info=True)

    logger.info("[Avito] %d annonces recuperees", len(voitures))
    return voitures


# =================== SCRAPER 2 : MOTEUR.MA ===================
def _moteur_extraire_image_detail(url_annonce):
    """Fetch la page detail d'une annonce Moteur.ma et extrait la vraie image.

    Les images du modele sont sur /media/images/models/.
    """
    try:
        r = requests.get(url_annonce, headers=HEADERS_NAVIGATEUR, timeout=6)
        s = BeautifulSoup(r.text, "html.parser")
        for img in s.find_all("img"):
            src = img.get("src", "")
            if "/media/images/models/" in src:
                return src if src.startswith("http") else "https://www.moteur.ma" + src
        return ""
    except Exception:
        return ""


def _moteur_extraire_ville_detail(url_annonce):
    """Fetch la page detail d'une annonce Moteur.ma et extrait la ville.

    Sur les pages detail, la ville apparaît généralement sous la forme
    "location à <Ville>" (ou variantes minuscules/majuscules).

    On évite d'utiliser `_extraire_ville()` (qui renvoie souvent Casablanca
    car il matche dans l'ordre de la liste), et on extrait la ville
    directement depuis le motif.
    """
    try:
        r = requests.get(url_annonce, headers=HEADERS_NAVIGATEUR, timeout=6)
        s = BeautifulSoup(r.text, "html.parser")
        texte = s.get_text(" ", strip=True)

        m = re.search(r"location\s+à\s+([A-Za-zÀ-ÖØ-öø-ÿ\-\s]+)\s+Maroc", texte, flags=re.I)
        if m:
            ville = m.group(1).strip()
            # Nettoyage: enlever les tirets finaux/espaces multiples
            ville = re.sub(r"\s+", " ", ville).strip(" -|,")
            return ville

        # Fallback: tenter une extraction générique
        return _extraire_ville(texte)
    except Exception:
        return "Maroc"






def scraper_moteur():
    """
    Scrape la section location de voitures sur Moteur.ma.
    Strategie : extraire le titre depuis le h3 contenant le lien.
    Pour l'image : essayer plusieurs attributs de lazy-load,
    sinon fetch la page detail (en parallele pour la rapidite).
    """
    url = "https://www.moteur.ma/fr/voiture/location-voiture/"
    voitures = []

    try:
        reponse = requests.get(url, headers=HEADERS_NAVIGATEUR, timeout=15)
        soup = BeautifulSoup(reponse.text, "html.parser")

        # Chaque annonce est dans un h2/h3 avec un lien vers detail-annonce
        for h_tag in soup.find_all(["h2", "h3", "h4"]):
            lien = h_tag.find("a", href=re.compile(r'detail-annonce'))
            if not lien:
                continue

            href = lien.get("href", "")
            url_annonce = href if href.startswith("http") else "https://www.moteur.ma" + href

            titre = lien.get_text(strip=True)
            if not titre or len(titre) < 3:
                continue

            # Essayer de trouver l'image dans le parent (lazy-load attributes)
            image_url = ""
            parent = h_tag.parent
            niveaux = 0
            while parent is not None and niveaux < 4 and not image_url:
                for img in parent.find_all("img"):
                    for attr in ["data-original", "data-src", "data-lazy", "data-lazy-src", "src"]:
                        src = img.get(attr, "")
                        if (src and "lz_load" not in src and "fuel.png" not in src
                                and "logo" not in src.lower() and not src.startswith("data:")):
                            image_url = src
                            break
                    if image_url:
                        break
                parent = parent.parent
                niveaux += 1

            if image_url and image_url.startswith("/"):
                image_url = "https://www.moteur.ma" + image_url

            # Ville + prix depuis le contexte (listing)
            contexte = h_tag.parent.get_text(" ", strip=True) if h_tag.parent else titre
            ville = _extraire_ville(contexte)
            prix = _extraire_prix(contexte)

            # Fallback ville : extraction depuis la page detail
            # car la page listing peut ne pas contenir toutes les villes.
            if ville == "Maroc":
                ville = _moteur_extraire_ville_detail(url_annonce)

            voitures.append(_construire_voiture(
                titre, ville, prix, url_annonce, image_url, "Moteur.ma"
            ))


            if len(voitures) >= 15:
                break

        # Pour les voitures sans image, fetch la page detail en parallele
        sans_image = [v for v in voitures if not v["image"]]
        if sans_image:
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_v = {
                    executor.submit(_moteur_extraire_image_detail, v["url"]): v
                    for v in sans_image[:10]
                }
                for future in concurrent.futures.as_completed(future_to_v, timeout=20):
                    v = future_to_v[future]
                    try:
                        img = future.result()
                        if img:
                            v["image"] = img
                    except Exception:
                        pass

    except Exception as e:
        logger.error("[Moteur.ma] Erreur : %s", e, exc_info=True)

    logger.info("[Moteur.ma] %d annonces recuperees", len(voitures))
    return voitures


# =================== SCRAPER 3 : MAROCANNONCES.COM ===================
def scraper_marocannonces():
    """Scrape la section Auto-Moto sur MarocAnnonces.com, filtre les annonces de location."""
    url = "https://www.marocannonces.com/categorie/15/Auto-Moto.html"
    voitures = []

    try:
        reponse = requests.get(url, headers=HEADERS_NAVIGATEUR, timeout=15)
        soup = BeautifulSoup(reponse.text, "html.parser")

        annonces = soup.select("ul.list-ads li") or soup.select(".holder li") or []
        if not annonces:
            annonces = soup.find_all("a", href=re.compile(r'/annonces/.+\.html'))

        deja_vu = set()
        for item in annonces:
            lien = item if item.name == "a" else item.find("a", href=True)
            if not lien:
                continue
            href = lien.get("href", "")
            if not href or "annonces" not in href:
                continue

            url_annonce = href if href.startswith("http") else "https://www.marocannonces.com" + href
            if url_annonce in deja_vu:
                continue
            deja_vu.add(url_annonce)

            titre_tag = lien.find(["h3", "h2"]) if hasattr(lien, "find") else None
            titre = titre_tag.get_text(strip=True) if titre_tag else lien.get_text(strip=True)
            if not titre or len(titre) < 3:
                continue

            texte = " ".join(item.stripped_strings) if hasattr(item, 'stripped_strings') else titre

            # Garder uniquement les annonces de location
            if not re.search(r'\blocation\b|\blouer\b|\bà louer\b', titre + " " + texte, re.I):
                continue

            ville = _extraire_ville(texte)
            prix = _extraire_prix(texte)

            img_tag = item.find("img") if hasattr(item, "find") else None
            image_url = ""
            if img_tag:
                for attr in ["data-original", "data-src", "data-lazy-src", "src"]:
                    src = img_tag.get(attr, "")
                    if src and not src.startswith("data:") and "blank" not in src.lower():
                        image_url = src
                        break
                if image_url and image_url.startswith("/"):
                    image_url = "https://www.marocannonces.com" + image_url

            voitures.append(_construire_voiture(
                titre, ville, prix, url_annonce, image_url, "MarocAnnonces.com"
            ))

            if len(voitures) >= 15:
                break

    except Exception as e:
        logger.error("[MarocAnnonces] Erreur : %s", e, exc_info=True)

    logger.info("[MarocAnnonces] %d annonces recuperees", len(voitures))
    return voitures


# =================== FONCTION PRINCIPALE ===================
def scraper_locations():
    """
    Recupere les annonces de tous les sites externes configures.
    Chaque source est isolee : si une echoue, les autres continuent.
    """
    sources = [
        scraper_avito,
        scraper_moteur,
        scraper_marocannonces,
    ]

    logger.info("=== Demarrage du scraping multi-sites ===")
    toutes = []
    for fonction in sources:
        try:
            resultat = fonction() or []
            logger.info("[%s] Total fusionne : %d annonces", fonction.__name__, len(resultat))
            toutes.extend(resultat)
        except Exception as e:
            logger.error("[%s] Erreur globale : %s", fonction.__name__, e, exc_info=True)

    logger.info("=== Scraping termine : %d annonces au total ===", len(toutes))
    return toutes
