import requests
import re
import logging
import subprocess
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# Файлы
INPUT_FILE = "goods.txt"
OUTPUT_FILE = "mails.txt"
LOG_FILE = "logs/mails.log"

# Заголовки для имитации обычного пользователя
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}

# Регулярное выражение для поиска email
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# Настройка логирования
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

def find_emails(url):
    """Пытается найти email на сайте."""
    emails = set()
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            logging.warning(f"Ошибка {response.status_code} при доступе к {url}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()
        emails.update(re.findall(EMAIL_REGEX, text))

        # Ищем дополнительные страницы с контактами
        for link in soup.find_all("a", href=True):
            href = link["href"].lower()
            if any(keyword in href for keyword in ["contact", "support", "help", "about"]):
                contact_url = urljoin(url, link["href"])
                emails.update(scrape_page(contact_url))

    except Exception as e:
        logging.error(f"Ошибка при обработке {url}: {e}")
    
    return emails

def scrape_page(url):
    """Парсит страницу и ищет email."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return set(re.findall(EMAIL_REGEX, response.text))
    except Exception as e:
        logging.error(f"Ошибка при парсинге {url}: {e}")
    return set()

def main():
    """Основной процесс сбора email-адресов."""
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as file:
            sites = [line.strip() for line in file]

        found_emails = []
        count = 0

        for site in sites:
            domain = urlparse(site).netloc
            emails = find_emails(site)
            limited_emails = list(emails)[:10]

            for email in limited_emails:
                found_emails.append(f"{email} {domain}")
                logging.info(f"Найден email: {email} для {domain}")
                count += 1

                # Каждый 10-й email добавляем тестовый
                if count % 10 == 0:
                    test_email = "vika.lernich@mail.ru example.com"
                    found_emails.append(test_email)
                    logging.info(f"Добавлен тестовый email: {test_email} после {count} найденных.")

        # Сохраняем результат
        with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
            file.write("\n".join(found_emails))

        print(f"\nСохранено {len(found_emails)} email в {OUTPUT_FILE}")
        logging.info(f"Сохранено {len(found_emails)} email в {OUTPUT_FILE}")

        # Запуск следующего скрипта
        subprocess.run(["python", "deleter.py"])

    except Exception as e:
        logging.error(f"Критическая ошибка в основном процессе: {e}")

if __name__ == "__main__":
    main()
