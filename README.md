# EmergencyCard - Digitalt Nodkort

Enkel offline-forst app for att bara ditt digitala nodkort med medicinsk information, kontaktpersoner och kommunikationsbehov.

## Funktioner

- **Personlig info**: Namn, personnummer, diagnoser, mediciner, allergier
- **Kontaktpersoner**: Namn, telefon och relation
- **Kommunikationsbehov**: T.ex. "behover extra tid", "autism", "icke-verbal"
- **QR-kod**: Visa for sjukvardspersonal sa de kan skanna din info
- **Offline**: Fungerar helt utan internet - all data sparas lokalt

## Installation

```bash
# Krav: GTK4 + libadwaita maste vara installerat pa systemet

# Installera Python-beroenden
pip install PyGObject qrcode pillow

# Kor appen
python emergency_card.py

# Eller installera
pip install .
emergency-card
```

## Beroenden

- Python 3.8+
- GTK4 + libadwaita (systempaket)
- PyGObject
- qrcode + pillow (for QR-kod, valfritt)

## Anvandning

1. Oppna appen
2. Ga till **Redigera** och fyll i dina uppgifter
3. Tryck **Spara**
4. Visa **Nodkort**-fliken i nodsituationer
5. Visa **QR-kod** for sjukvardspersonal

Data sparas lokalt i `~/.local/share/emergency-card/card.json`.

## Licens

MIT
