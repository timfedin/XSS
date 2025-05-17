import smtplib
import time
import random
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse

# ДАННЫЕ ДЛЯ ВХОДА В ПОЧТУ
SMTP_SERVER = "smtp.mail.ru"
SMTP_PORT = 465

ACCOUNTS = [
    {"email": "ПОЧТА1", "password": "ПАРОЛЬ"},
    {"email": "ПОЧТА2", "password": "ПАРОЛЬ"}
]
# Можно добавить сколько угодно почт 
# Файл с email-ами техподдержки
INPUT_FILE = "mails.txt"
# Файл для сохранения доменов, куда удалось отправить письмо
OUTPUT_FILE = "sent.txt"

# Шаблоны сообщений (будут рандомно варьироваться)
TEMPLATES = [
    "Здравствуйте! Я обнаружил уязвимость на вашем сайте {domain}. Она может поставить под угрозу безопасность пользователей. Хотите ли вы получить детали?",
    "Добрый день! Я провёл анализ вашего сайта {domain} и нашёл уязвимость, которая потенциально может быть опасной. Могу предоставить информацию, если вам интересно.",
    "Приветствую! Ваш сайт {domain} имеет уязвимость, которая может быть использована злоумышленниками. Вы хотите получить подробности?",
    "Здравствуйте! Я занимаюсь кибербезопасностью и заметил серьёзную проблему на {domain}. Вы заинтересованы в дополнительной информации?",
    "Добрый день! Нашёл потенциально критическую уязвимость на вашем сайте {domain}. Если хотите, могу рассказать подробнее."
]

lock = threading.Lock()

def send_email(to_email, domain, account):
    """Отправляет письмо на указанный email с динамическим текстом."""
    try:
        # Создаём сообщение
        msg = MIMEMultipart()
        msg["From"] = account["email"]
        msg["To"] = to_email
        msg["Subject"] = "Важная информация о безопасности вашего сайта"

        # Генерируем случайный текст письма
        email_body = random.choice(TEMPLATES).format(domain=domain)
        msg.attach(MIMEText(email_body, "plain"))

        # Подключаемся к SMTP-серверу и отправляем письмо
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(account["email"], account["password"])
        server.sendmail(account["email"], to_email, msg.as_string())
        server.quit()

        print(f"[+] Успешно отправлено на {to_email} ({domain}) с {account['email']}")
        return True

    except Exception as e:
        print(f"[-] Ошибка отправки на {to_email} ({domain}) с {account['email']}: {e}")
        return False

def send_from_account(account, lines):
    """Отправляет письма с конкретного аккаунта."""
    sent_domains = set()

    for line in lines:
        try:
            email, site = line.split()
            parsed_url = urlparse(site)
            domain = parsed_url.netloc if parsed_url.netloc else parsed_url.path

            if send_email(email, domain, account):
                with lock:
                    sent_domains.add(domain)

            # Ждём случайное время перед следующим письмом (5-10 минут)
            wait_time = random.randint(300, 600)
            print(f"[*] {account['email']} ожидает {wait_time // 60} минут перед следующим письмом...")
            time.sleep(wait_time)

        except Exception as e:
            print(f"[-] Ошибка обработки строки: {line} - {e}")

    # Сохраняем отправленные домены в файл
    with lock:
        with open(OUTPUT_FILE, "a", encoding="utf-8") as file:
            file.write("\n".join(sent_domains) + "\n")

    print(f"\n[✔] Все письма с {account['email']} отправлены.")

def main():
    """Основная функция отправки писем с любого количества почт."""
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file]

    # Вычисляем количество строк на один аккаунт
    part_size = len(lines) // len(ACCOUNTS)
    threads = []

    # Создаем потоки динамически для каждого аккаунта
    for i, account in enumerate(ACCOUNTS):
        # Выбираем свою часть email-адресов для каждой почты
        start = i * part_size
        end = start + part_size if i < len(ACCOUNTS) - 1 else len(lines)
        part_lines = lines[start:end]

        # Создаём и запускаем поток
        thread = threading.Thread(target=send_from_account, args=(account, part_lines))
        threads.append(thread)
        thread.start()

    # Дожидаемся завершения всех потоков
    for thread in threads:
        thread.join()

    print("\n[✔] Все письма отправлены со всех почт.")

if __name__ == "__main__":
    main()
input()
input()