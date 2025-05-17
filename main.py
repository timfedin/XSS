import concurrent.futures
from colorama import init, Fore, Style
from bs4 import BeautifulSoup as bs
import requests
import subprocess
from urllib.parse import urljoin
from pprint import pprint
import time
import logging

# Инициализация цвета вывода
init(autoreset=True)

# Настройки
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36"
}
STOP_TIME = 180  # Максимальное время проверки одного сайта (в секундах)
TIMEOUT = 20     # Максимальное время ожидания ответа от сайта (в секундах)
XSS_SCRIPT = "<Script>alert('XSS')</scripT>"
LOG_FILE = "logs/main.log"
MAX_THREADS = 15  # Максимальное количество потоков

# Настройка логирования
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def stop(stop_time):
    """Проверяет, истекло ли время выполнения."""
    return time.time() >= stop_time

def save(url):
    """Сохраняет URL с уязвимостью в файл."""
    try:
        with open("goods.txt", "a", encoding="utf-8") as file:
            file.write(f"{url}\n")
        logging.info(f"URL сохранён: {url}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении URL {url}: {e}")

def scan_xss(url, stop_time, timeout):
    """Сканирует сайт на уязвимость XSS."""
    stop_time = time.time() + stop_time
    try:
        html = requests.get(url, headers=HEADERS, timeout=timeout)
        soup = bs(html.content, "html.parser")
        forms = soup.find_all("form")
        is_vulnerable = False

        for form in forms:
            if stop(stop_time):
                logging.warning(f"Время проверки сайта {url} истекло")
                break
            
            action = form.attrs.get("action", "").lower()
            method = form.attrs.get("method", "get").lower()

            # Игнорируем формы с действиями на JavaScript
            if not action or action.startswith("javascript"):
                continue

            inputs = [{"type": input_tag.attrs.get("type", "text"), "name": input_tag.attrs.get("name")}
                      for input_tag in form.find_all("input")]
            
            form_details = {"action": action, "method": method, "inputs": inputs}
            target_url = urljoin(url, action)
            data = {input["name"]: XSS_SCRIPT for input in inputs if input["type"] in ["text", "search"]}

            try:
                if method == "post":
                    response = requests.post(target_url, data=data, headers=HEADERS, timeout=timeout)
                else:
                    response = requests.get(target_url, params=data, headers=HEADERS, timeout=timeout)

                content = response.content.decode('latin-1')

                if XSS_SCRIPT in content:
                    save(url)
                    print(f"{Fore.RED}[+] XSS Detected on {url}{Style.RESET_ALL}\n[*] Form details:")
                    pprint(form_details)
                    logging.info(f"XSS обнаружен на {url}")
                    is_vulnerable = True
            except requests.RequestException as e:
                logging.error(f"Ошибка при проверке формы на {url}: {e}")

        if not is_vulnerable:
            logging.info(f"XSS не обнаружен на {url}")

    except requests.RequestException as e:
        logging.error(f"Ошибка подключения к {url}: {e}")

def process_url(url):
    """Обрабатывает один URL в потоке."""
    try:
        print(f"\033[37m{url}")
        scan_xss(url, STOP_TIME, TIMEOUT)
    except Exception as e:
        logging.error(f"Ошибка сканирования {url}: {e}")

if __name__ == "__main__":
    try:
        # Спрашиваем пользователя об использовании многопоточности
        use_threads = input("Использовать многопоточность? (y/n): ").strip().lower()

        with open("site.txt", "r", encoding="utf-8") as urls:
            url_list = [line.strip() for line in urls]

        if use_threads == "y":
            print(f"{Fore.GREEN}[✔] Многопоточность включена. Используется до {MAX_THREADS} потоков.{Style.RESET_ALL}")
            # Используем пул потоков для многопоточности
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                executor.map(process_url, url_list)
        else:
            print(f"{Fore.YELLOW}[!] Многопоточность отключена. Последовательная обработка сайтов.{Style.RESET_ALL}")
            for url in url_list:
                process_url(url)

    except FileNotFoundError:
        logging.critical("Файл site.txt не найден")
        print(f"{Fore.RED}Файл site.txt не найден. Проверьте наличие файла.{Style.RESET_ALL}")
    except Exception as e:
        logging.critical(f"Ошибка при открытии файла site.txt: {e}")

    # Запуск фильтрации
    subprocess.run(["python", "filtr.py"])