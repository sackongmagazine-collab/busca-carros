import unicodedata
from fastapi import APIRouter

router = APIRouter(prefix="/fipe", tags=["fipe"])

# Lista abrangente de modelos populares no Brasil
MODELS = [
    # Hyundai
    "HB20", "HB20S", "HB20X", "Creta", "Tucson", "Santa Fe", "Azera", "Veloster",
    # Chevrolet
    "Onix", "Onix Plus", "Tracker", "Cruze", "Spin", "S10", "Montana", "Cobalt",
    "Trailblazer", "Equinox", "Captiva", "Camaro", "Corvette",
    # Ford
    "Ka", "Ka Sedan", "Ecosport", "Ranger", "Territory", "Maverick", "Bronco",
    "Fusion", "Edge", "Explorer", "F-250",
    # Volkswagen
    "Gol", "Polo", "Polo GTS", "T-Cross", "Virtus", "Saveiro", "Amarok",
    "Golf", "Jetta", "Tiguan", "Touareg", "Fox", "Up",
    # Renault
    "Kwid", "Sandero", "Duster", "Logan", "Captur", "Megane", "Fluence", "Oroch",
    # Fiat
    "Mobi", "Uno", "Argo", "Cronos", "Strada", "Toro", "Fiorino", "Doblo",
    "Bravo", "Punto", "Linea", "Palio", "Siena", "Ducato", "Pulse", "Fastback",
    # Honda
    "Civic", "HR-V", "Fit", "City", "WR-V", "Accord", "CR-V", "CR-Z",
    # Toyota
    "Corolla", "Corolla Cross", "Hilux", "SW4", "Yaris", "RAV4", "Etios",
    "Prius", "Camry", "Land Cruiser", "Fortuner",
    # Nissan
    "Kicks", "Versa", "Frontier", "Sentra", "Tiida", "March", "Livina",
    # Jeep
    "Compass", "Renegade", "Commander", "Wrangler", "Cherokee", "Gladiator",
    # Mitsubishi
    "Outlander", "Eclipse Cross", "ASX", "Pajero", "L200", "Lancer",
    # Citroën
    "C3", "C4 Cactus", "C4 Lounge", "Aircross", "Berlingo",
    # Peugeot
    "208", "2008", "308", "3008", "408", "Partner",
    # Chery/CAOA
    "Tiggo 5X", "Tiggo 7 Pro", "Tiggo 8 Pro", "Arrizo 6", "Tiggo 3X",
    # BYD
    "Dolphin", "Seal", "Han", "Atto 3", "King",
    # Kia
    "Sportage", "Sorento", "Carnival", "Stinger", "Cerato",
    # Subaru
    "Outback", "Forester", "Impreza", "XV",
    # Land Rover
    "Defender", "Discovery", "Range Rover", "Freelander",
    # Audi
    "A3", "A4", "A5", "A6", "Q3", "Q5", "Q7", "TT",
    # BMW
    "116i", "118i", "120i", "320i", "328i", "418i", "X1", "X3", "X5", "X6",
    # Mercedes
    "A200", "C180", "C200", "C250", "GLA", "GLC", "GLE", "Sprinter",
    # Volvo
    "XC40", "XC60", "XC90", "S60", "V60",
    # RAM/Dodge
    "RAM 1500", "RAM 2500", "Challenger", "Charger",
]


def _norm(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


@router.get("/models")
async def model_suggestions(q: str = ""):
    q = q.strip()
    if len(q) < 2:
        return []
    q_norm = _norm(q)
    # Prioriza começa-com, depois contém
    starts = [m for m in MODELS if _norm(m).startswith(q_norm)]
    contains = [m for m in MODELS if q_norm in _norm(m) and m not in starts]
    return (starts + contains)[:10]
