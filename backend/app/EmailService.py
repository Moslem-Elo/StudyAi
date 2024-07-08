import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import time


class EmailService:
    def __init__(self, from_address, password, smtp_server, smtp_port):
        self.from_address = from_address
        self.password = password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def send_email(self, to_address, subject, message):
        # Set up the MIME
        msg = MIMEMultipart()
        msg['From'] = self.from_address
        msg['To'] = to_address
        msg['Subject'] = subject

        # Add the message body to the MIME message
        msg.attach(MIMEText(message, 'plain'))

        try:
            # Establish a secure session with the server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.from_address, self.password)
            text = msg.as_string()
            server.sendmail(self.from_address, to_address, text)
            server.quit()
            print("Email sent successfully!")
        except Exception as e:
            print(f"Failed to send email. Error: {e}")

    def schedule_emails(self, moodle_data, user_email, days_before, frequency):
        for course in moodle_data['courses']:
            for abgabe in course['abgaben']:
                if abgabe['fälligkeitsdatum'] != 'Abgabe abgelaufen oder kein Fälligkeitsdatum bekannt':
                    due_date = datetime.strptime(abgabe['fälligkeitsdatum'], '%Y-%m-%d %H:%M:%S')
                    reminder_date = due_date - timedelta(days=days_before)

                    if frequency == 'täglich':
                        current_date = datetime.now()
                        while current_date <= due_date:
                            if current_date >= reminder_date:
                                subject = f"Erinnerung: Abgabe für {abgabe['name']} im Kurs {course['kurs']}"
                                message = f"Hallo,\n\nDies ist eine Erinnerung, dass die Abgabe '{abgabe['name']}' im Kurs '{course['kurs']}' am {abgabe['fälligkeitsdatum']} fällig ist.\n\nViele Grüße,\nDein AI-Lernassistent"
                                self.send_email(user_email, subject, message)
                            current_date += timedelta(days=1)
                            time.sleep(86400)  # Sleep for a day
                    elif frequency == 'einmalig':
                        current_date = datetime.now()
                        if current_date >= reminder_date:
                            subject = f"Erinnerung: Abgabe für {abgabe['name']} im Kurs {course['kurs']}"
                            message = f"Hallo,\n\nDies ist eine Erinnerung, dass die Abgabe '{abgabe['name']}' im Kurs '{course['kurs']}' am {abgabe['fälligkeitsdatum']} fällig ist.\n\nViele Grüße,\nDein AI-Lernassistent"
                            self.send_email(user_email, subject, message)
