from urllib.parse import urlparse
import subprocess
import logging

# Настройка логирования
logging.basicConfig(
    filename="logs/filtr.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

def load_urls(file_path):
    """Загружает URL из файла."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        logging.error(f"Ошибка при загрузке URL из {file_path}: {e}")
        return []

def save_urls(file_path, urls):
    """Сохраняет уникальные URL в файл."""
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("\n".join(urls))
        logging.info(f"Файл {file_path} успешно обновлён.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении URL в {file_path}: {e}")

def filter_urls(urls):
    """Удаляет дубликаты доменов из списка URL."""
    unique_domains = set()
    filtered_urls = []

    for url in urls:
        domain = urlparse(url).netloc.lower()
        if domain and domain not in unique_domains:
            unique_domains.add(domain)
            filtered_urls.append(url)

    return filtered_urls

def main():
    """Основная функция фильтрации URL."""
    input_file = "goods.txt"
    urls = load_urls(input_file)

    if not urls:
        logging.warning("Файл goods.txt пустой или не найден.")
        return

    filtered_urls = filter_urls(urls)
    save_urls(input_file, filtered_urls)

    removed_count = len(urls) - len(filtered_urls)
    logging.info(f"Фильтрация завершена. Дубликаты удалены: {removed_count}. Осталось уникальных сайтов: {len(filtered_urls)}.")
    print(f"Фильтрация завершена. Дубликаты удалены: {removed_count}. Осталось уникальных сайтов: {len(filtered_urls)}.")

    # Запуск следующего скрипта
    subprocess.run(["python", "mails.py"])

if __name__ == "__main__":
    main()
