import concurrent.futures
import logging
import shutil
import subprocess
import time
from colorama import init, Fore, Style

# Инициализация цвета вывода
init(autoreset=True)

# Настройки
LOG_FILE = "logs/main.log"
MAX_THREADS = 10
XSSER_TIMEOUT = 300
XSSER_CMD = "xsser"
XSSER_ARGS = ["--auto"]

# Индикаторы уязвимости в выводе XSSer
VULN_INDICATORS = [
    "xss found",
    "vulnerable",
    "successful injections",
    "injections successful",
]

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)


def save(url: str) -> None:
    """Сохраняет URL с уязвимостью в файл."""
    with open("goods.txt", "a", encoding="utf-8") as file:
        file.write(f"{url}\n")
    logging.info("URL сохранён: %s", url)


def is_vulnerable_output(output: str) -> bool:
    """Проверяет вывод XSSer на признаки уязвимости."""
    normalized = output.lower()
    return any(indicator in normalized for indicator in VULN_INDICATORS)


def scan_with_xsser(url: str) -> None:
    """Проверяет URL через XSSer."""
    cmd = [XSSER_CMD, "--url", url, *XSSER_ARGS]
    logging.info("Запуск XSSer: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=XSSER_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        logging.warning("Таймаут XSSer для %s", url)
        print(f"{Fore.YELLOW}[!] Таймаут XSSer: {url}{Style.RESET_ALL}")
        return
    except Exception as exc:
        logging.error("Ошибка запуска XSSer для %s: %s", url, exc)
        print(f"{Fore.RED}[-] Ошибка запуска XSSer: {url}{Style.RESET_ALL}")
        return

    combined_output = f"{result.stdout}\n{result.stderr}"

    if is_vulnerable_output(combined_output):
        save(url)
        logging.info("XSS обнаружен на %s", url)
        print(f"{Fore.RED}[+] XSS Detected on {url}{Style.RESET_ALL}")
    else:
        logging.info("XSS не обнаружен на %s", url)
        print(f"{Fore.GREEN}[-] No XSS found: {url}{Style.RESET_ALL}")


def process_url(url: str) -> None:
    """Обрабатывает один URL в потоке."""
    cleaned = url.strip()
    if not cleaned:
        return
    print(f"\033[37m{cleaned}")
    scan_with_xsser(cleaned)


def main() -> None:
    """Основной запуск сканера на базе XSSer."""
    if shutil.which(XSSER_CMD) is None:
        logging.critical("Утилита xsser не найдена в PATH")
        print(f"{Fore.RED}Ошибка: xsser не найден в PATH. Установите XSSer и повторите запуск.{Style.RESET_ALL}")
        return

    try:
        with open("site.txt", "r", encoding="utf-8") as urls:
            url_list = [line.strip() for line in urls if line.strip()]
    except FileNotFoundError:
        logging.critical("Файл site.txt не найден")
        print(f"{Fore.RED}Файл site.txt не найден. Проверьте наличие файла.{Style.RESET_ALL}")
        return

    if not url_list:
        logging.warning("site.txt пуст")
        print(f"{Fore.YELLOW}[!] Файл site.txt пуст. Нечего сканировать.{Style.RESET_ALL}")
        return

    # Очищаем прошлый результат перед новым прогоном
    with open("goods.txt", "w", encoding="utf-8"):
        pass

    start = time.time()
    print(f"{Fore.GREEN}[✔] Запуск XSSer-сканирования для {len(url_list)} URL.{Style.RESET_ALL}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        executor.map(process_url, url_list)

    elapsed = time.time() - start
    logging.info("Сканирование завершено за %.2f сек", elapsed)
    print(f"{Fore.CYAN}[i] Сканирование завершено за {elapsed:.2f} сек.{Style.RESET_ALL}")

    # Запуск фильтрации
    subprocess.run(["python", "filtr.py"], check=False)


if __name__ == "__main__":
    main()
