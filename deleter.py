import os
import logging
import subprocess

# Файлы
MAILS_FILE = "mails.txt"
DELETE_FILE = "delete.txt"
LOG_FILE = "logs/deleter.log"

# Настройка логирования
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

def load_domains_to_delete():
    """Загружает список доменов, которые нужно удалить."""
    try:
        if not os.path.exists(DELETE_FILE):
            logging.warning(f"Файл {DELETE_FILE} не найден. Продолжаю без фильтрации.")
            return set()

        with open(DELETE_FILE, "r", encoding="utf-8") as file:
            domains = set(line.strip().lower() for line in file)
            logging.info(f"Загружено {len(domains)} доменов для удаления.")
            return domains
    except Exception as e:
        logging.error(f"Ошибка при загрузке доменов из {DELETE_FILE}: {e}")
        return set()

def clean_mails():
    """Удаляет email, у которых домен есть в delete.txt или содержит .jpg/.png."""
    try:
        if not os.path.exists(MAILS_FILE):
            print("Файл mails.txt не найден.")
            logging.error("Файл mails.txt не найден.")
            return

        domains_to_delete = load_domains_to_delete()

        with open(MAILS_FILE, "r", encoding="utf-8") as file:
            emails = [line.strip() for line in file]

        new_emails = []
        removed_emails = []

        for email in emails:
            parts = email.split()
            if len(parts) == 2:
                email_address, domain = parts
                if domain.lower() in domains_to_delete or ".jpg" in email_address or ".png" in email_address:
                    removed_emails.append(email)
                    logging.info(f"Удалён email: {email}")
                    continue
            
            new_emails.append(email)

        # Перезаписываем файл с оставшимися email
        with open(MAILS_FILE, "w", encoding="utf-8") as file:
            file.write("\n".join(new_emails))

        # Логируем результаты
        logging.info(f"Удалено {len(removed_emails)} email. Осталось {len(new_emails)} email.")
        print(f"\nУдалено {len(removed_emails)} email. Осталось {len(new_emails)} email.")

        # Запуск следующего скрипта
        subprocess.run(["python", "sender.py"])

    except Exception as e:
        logging.error(f"Критическая ошибка в процессе очистки: {e}")

if __name__ == "__main__":
    clean_mails()
