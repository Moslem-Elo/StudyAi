Gruppenmitglieder

- Moslem El-Omar

# AI-basierter Lernassistent für Studenten

Dieses Projekt ist ein AI-basierter Lernassistent, der Studenten dabei hilft, ihre Kurs- und Abgabeinformationen von Moodle zu verwalten und Erinnerungen per E-Mail zu erhalten.

## Inhaltsverzeichnis
- [Features](#features)
- [Installation](#installation)
- [Verwendung](#verwendung)
- [Konfiguration](#konfiguration)
- [Projektstruktur](#projektstruktur)


## Features
- Abrufen von Kurs- und Abgabeinformationen von Moodle
- Speicherung der Daten in ChromaDB
- AI-generierte Empfehlungen und Lernpläne basierend auf Kursdaten
- E-Mail-Benachrichtigungen für bevorstehende Abgaben

## Installation

### Voraussetzungen
- Python 3.8 oder höher
- Ein GitHub-Account
- Ein E-Mail-Konto für das Senden von Benachrichtigungen

### Schritte
1. **Klone das Repository:**
    ```bash
    git clone https://github.com/username/repository.git
    cd repository
    ```

2. **Erstelle und aktiviere eine virtuelle Umgebung:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Für Windows: venv\Scripts\activate
    ```

3. **Installiere die Abhängigkeiten:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Erstelle eine `.env`-Datei im Projektverzeichnis und füge deine OpenAI API-Schlüssel hinzu:**
    ```env
    OPENAI_API_KEY=your_openai_api_key
    ```

## Verwendung

### Starten der Anwendung
1. **Starte Streamlit:**
    ```bash
    streamlit run backend/app/main.py
    ```

2. **Melde dich bei deinem Moodle-Konto an:**
   - Gib deinen Benutzernamen und dein Passwort ein
   - Klicke auf "Anmelden"

3. **Aktiviere E-Mail-Benachrichtigungen:**
   - Gib deine E-Mail-Adresse ein
   - Wähle die Anzahl der Tage vor der Abgabe für die Benachrichtigung
   - Wähle die Benachrichtigungsfrequenz (einmalig oder täglich)
   - Klicke auf "E-Mail-Benachrichtigungen aktivieren"

## Konfiguration

### E-Mail-Service
Der E-Mail-Service verwendet die `EmailService`-Klasse, um Erinnerungen zu senden. Konfiguriere deine E-Mail-Anmeldedaten in der `EmailService`-Klasse:

```python
email_service = EmailService(
    from_address="your_email@example.com",
    password="your_email_password",
    smtp_server="smtp.gmail.com",
    smtp_port=587
)
