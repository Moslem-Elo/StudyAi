import streamlit as st
import openai
import requests
import chromadb
from chromadb.config import Settings
import uuid
from datetime import datetime

from EmailService import EmailService
# Setze deinen OpenAI API-Schlüssel
openai.api_key = ""

# ChromaDB-Client einrichten
chroma_client = chromadb.PersistentClient(path="../storage/chromadb")
collection = chroma_client.get_or_create_collection("moodle_data")

# E-Mail-Service einrichten
email_service = EmailService(
    from_address="",
    password="",
    smtp_server="smtp.gmail.com",
    smtp_port=587
)

# Funktion, um das aktuelle Semester zu bestimmen
def get_current_semester():
    today = datetime.today()
    year = today.year
    if today.month >= 4 and today.month <= 9:
        return f"SoSe{year}"
    else:
        return f"WiSe{year}/{str(year+1)[-2:]}"

# Funktion, um Moodle-Daten abzurufen
def get_moodle_data(username, password):
    if not username or not password:
        st.error("Bitte Benutzername und Passwort eingeben.")
        return None

    moodle_url = "https://moodle.htw-berlin.de"
    service = "moodle_mobile_app"

    # Token abrufen
    login_url = f"{moodle_url}/login/token.php"
    params = {
        'username': username,
        'password': password,
        'service': service
    }
    response = requests.get(login_url, params=params)

    if response.status_code == 200:
        response_data = response.json()
        if 'token' in response_data:
            user_token = response_data['token']

            # Abgaben mit dem Benutzertoken abrufen
            abgaben_url = f"{moodle_url}/webservice/rest/server.php"
            abgaben_params = {
                'wstoken': user_token,
                'wsfunction': 'mod_assign_get_assignments',
                'moodlewsrestformat': 'json'
            }
            abgaben_response = requests.get(abgaben_url, params=abgaben_params).json()

            current_semester = get_current_semester()
            courses = []
            for course in abgaben_response.get('courses', []):
                course_name = course.get('fullname', 'Unbekannter Kurs')
                if current_semester in course_name:
                    course_abgaben = []
                    for abgabe in course.get('assignments', []):
                        abgabe_name = abgabe.get('name', 'Unbekannte Abgabe')
                        cutoff_date = abgabe.get('cutoffdate', 'kein Fälligkeitsdatum')

                        # Konvertiere Unix-Zeitstempel in lesbares Datum
                        if cutoff_date != 'kein Fälligkeitsdatum' and cutoff_date != 0:
                            readable_cutoff_date = datetime.fromtimestamp(cutoff_date).strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            readable_cutoff_date = 'Abgabe abgelaufen oder kein Fälligkeitsdatum bekannt'

                        course_abgaben.append({
                            "name": abgabe_name,
                            "fälligkeitsdatum": readable_cutoff_date
                        })
                    courses.append({
                        "kurs": course_name,
                        "abgaben": course_abgaben
                    })
            return {"courses": courses}
        else:
            st.error("Moodle-Login fehlgeschlagen: Token nicht in der Antwort gefunden.")
            return None
    else:
        st.error(f"Moodle-Login fehlgeschlagen mit Statuscode {response.status_code}")
        return None

# Funktion, um Moodle-Daten in ChromaDB zu speichern
def store_moodle_data_in_chromadb(moodle_data):
    for course in moodle_data['courses']:
        if 'abgaben' in course and len(course['abgaben']) > 0:
            documents = []
            ids = []
            for abgabe in course['abgaben']:
                if abgabe['fälligkeitsdatum'] == 'Abgabe abgelaufen oder kein Fälligkeitsdatum bekannt':
                    document = f"Abgabe: {abgabe['name']} {abgabe['fälligkeitsdatum']}"
                else:
                    document = f"Abgabe: {abgabe['name']} bis {abgabe['fälligkeitsdatum']}"
                documents.append(document)
                ids.append(str(uuid.uuid4()))
            collection.add(ids=ids, documents=documents)

# Funktion, um eine OpenAI-Antwort zu erhalten
def get_ai_response(prompt, history):
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=history
    )
    return response['choices'][0]['message']['content'].strip()

# Funktion, um AI-Empfehlungen zu erhalten
def get_ai_recommendations(moodle_data):
    current_date = datetime.now().strftime('%Y-%m-%d')
    courses_text = "\n".join(
        [f"- Kurs: {course['kurs']}, Abgaben: " +
         ", ".join([f"{abgabe['name']} {abgabe['fälligkeitsdatum']}" if abgabe['fälligkeitsdatum'] == 'Abgabe abgelaufen oder kein Fälligkeitsdatum bekannt'
                    else f"{abgabe['name']} bis {abgabe['fälligkeitsdatum']}" for abgabe in course['abgaben']])
         for course in moodle_data['courses']]
    )
    prompt = f"""
    Du bist ein AI-Assistent für Universitätsstudenten. Beachte, dass du nur Informationen zu Kursen hast, in denen es auch Abgaben gibt.
    Das heutige Datum ist {current_date}.
    Hier sind die Daten für einen Studenten:
    Kurse:
    {courses_text}

    Erstelle einen personalisierten Lernplan und Erinnerungen.
    """
    history = [{"role": "system", "content": prompt}]
    response = get_ai_response(prompt, history)
    return response

# Funktion, um eine Abfrage an ChromaDB zu stellen
def query_chromadb(query):
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_year = datetime.now().year
    current_semester = get_current_semester()
    query_with_date = f"{query} {current_date} {current_semester}"

    results = collection.query(query_texts=[query_with_date])

    if 'documents' in results:
        # Hier ebenfalls die Bedingung hinzufügen
        documents = results['documents'][0]
        for i in range(len(documents)):
            if 'Abgabe abgelaufen oder kein Fälligkeitsdatum bekannt' in documents[i]:
                documents[i] = documents[i].replace(" bis Abgabe abgelaufen oder kein Fälligkeitsdatum bekannt", " Abgabe abgelaufen oder kein Fälligkeitsdatum bekannt")
        return documents
    else:
        st.error("Fehler: 'documents' nicht in der Rückgabe von ChromaDB gefunden.")
        return []

# Funktion, um alle Daten aus der ChromaDB-Sammlung zu löschen
def delete_all_data_from_chromadb():
    chroma_client.delete_collection(name="moodle_data")  # Löscht alle Dokumente in der Sammlung
    st.success("Alle Daten wurden aus ChromaDB gelöscht.")

# Streamlit Benutzeroberfläche
st.title("AI-basierter Lernassistent für Studenten")

# Benutzer-Login
st.subheader("Melde dich bei deinem Moodle-Konto an")
username = st.text_input("Benutzername")
password = st.text_input("Passwort", type="password")

if st.button("Anmelden"):
    moodle_data = get_moodle_data(username, password)
    if moodle_data:
        st.session_state['moodle_data'] = moodle_data
        store_moodle_data_in_chromadb(moodle_data)
        st.success("Erfolgreich angemeldet!")

# Daten löschen
if st.button("Daten aus ChromaDB löschen"):
    delete_all_data_from_chromadb()

# Überprüfen, ob der Benutzer angemeldet ist
if 'moodle_data' in st.session_state:
    moodle_data = st.session_state['moodle_data']

    user_email = st.text_input("Deine E-Mail-Adresse")
    days_before = st.number_input("Tage vor Abgabe für Benachrichtigungen", min_value=1, max_value=30, value=1)
    frequency = st.selectbox("Benachrichtigungsfrequenz", ["einmalig", "täglich"])

    if st.button("E-Mail-Benachrichtigungen aktivieren"):
        if user_email:
            email_service.schedule_emails(moodle_data, user_email, days_before, frequency)
            st.success("E-Mail-Benachrichtigungen wurden gesendet!")

    # Moodle-Daten anzeigen
    st.subheader("Deine Kurse und Abgaben")
    for course in moodle_data['courses']:
        st.write(f"Kurs: {course['kurs']}")
        for abgabe in course['abgaben']:
            if abgabe['fälligkeitsdatum'] == 'kein Fälligkeitsdatum':
                abgabe['fälligkeitsdatum'] = 'Abgabe abgelaufen oder kein Fälligkeitsdatum bekannt'
            if abgabe['fälligkeitsdatum'] == 'Abgabe abgelaufen oder kein Fälligkeitsdatum bekannt':
                st.write(f"  - Abgabe: {abgabe['name']} {abgabe['fälligkeitsdatum']}")
            else:
                st.write(f"  - Abgabe: {abgabe['name']} bis {abgabe['fälligkeitsdatum']}")

    # AI-Empfehlungen erhalten
    st.subheader("AI-Empfehlungen")
    recommendations = get_ai_recommendations(moodle_data)
    st.write(recommendations)

    # Mit der AI chatten
    st.subheader("Frage die AI")
    user_question = st.text_input("Deine Frage")

    if st.button("Senden"):
        if user_question:
            history = [{"role": "system", "content": "Du bist ein AI-basierter Lernassistent für Studenten."}]
            history.append({"role": "user", "content": user_question})

            # Abfrage an ChromaDB stellen
            chromadb_results = query_chromadb(user_question)
            #st.write("Ähnliche Ergebnisse aus ChromaDB:")
            #for result in chromadb_results:
            #st.write(result)

            # Verwende die ChromaDB-Ergebnisse im Prompt
            if chromadb_results:
                courses_from_chromadb = "\n".join(chromadb_results)
                prompt = f"""
                Du bist ein AI-Assistent für Universitätsstudenten. Das heutige Datum ist {datetime.now().strftime('%Y-%m-%d')}, gib nur zeitlich relevante Antworten.
                Hier sind die Daten für einen Studenten basierend auf einer Abfrage:
                Kurse:
                {courses_from_chromadb}

                Erstelle eine Antwort basierend auf diesen Daten.
                """
                history.append({"role": "user", "content": prompt})
            ai_response = get_ai_response(user_question, history)
            st.write(f"AI: {ai_response}")
