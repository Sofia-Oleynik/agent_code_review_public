from dotenv import load_dotenv
import os
from typing import Tuple
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


load_dotenv("/home/oleynikss/agent_code_review/.env")

USERNAME_EMAIL = os.getenv("USERNAME_EMAIL")
PASSWORD_EMAIL_APP = os.getenv("PASSWORD_EMAIL")

USERNAME_EMAIL="coderevieweragent@gmail.com"
PASSWORD_EMAIL_APP="yjnskxryffdyfpvm"


smtp_server = 'smtp.gmail.com'
smtp_port = 587

def send_message(subject: str, body: str, recipient_email: str = USERNAME_EMAIL):

    msg = MIMEMultipart()
    msg['From'] = USERNAME_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Подключаемся к SMTP серверу Яндекса
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Начинаем шифрование
        server.login(USERNAME_EMAIL, PASSWORD_EMAIL_APP)  # Входим в учетную запись
        server.send_message(msg)  # Отправляем сообщение
        return (True, "Сообщение успешно отправлено!")
    except Exception as e:
        return (False, f"Ошибка: {e}")
    finally:
        server.quit()

