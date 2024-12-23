import urllib.request
import json
import logging
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Cấu hình logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("domain_check.log", encoding="utf-8")
    ]
)

def get_main_domain(domain):
    """
    Lấy tên miền chính (bỏ subdomains).
    """
    parts = domain.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])  # Lấy hai phần cuối cùng (ví dụ: example.com)
    return domain

def check_redirect(domain):
    """
    Kiểm tra redirect của một tên miền và lấy tên miền chính.
    """
    try:
        # Thêm User-Agent để tránh bị chặn
        request = urllib.request.Request(
            url=f"http://{domain}",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"}
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            final_url = response.geturl()  # URL cuối cùng sau redirect
            final_domain = get_main_domain(urlparse(final_url).netloc)
            logging.info(f"Domain {domain} redirected to {final_domain}")
            return final_domain
    except Exception as e:
        logging.error(f"Failed to check domain {domain}: {e}")
        return None

def process_domains(input_file, output_file, max_threads=10):
    """
    Xử lý danh sách tên miền từ file input và lưu kết quả vào file output.
    """
    # Đọc file JSON
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Kiểm tra redirect cho từng tên miền
    domains = data if isinstance(data, list) else []
    results = []

    with ThreadPoolExecutor(max_threads) as executor:
        futures = {executor.submit(check_redirect, domain): domain for domain in domains}
        for future in as_completed(futures):
            new_domain = future.result()
            if new_domain:
                results.append(new_domain)

    # Ghi lại kết quả vào file JSON mới
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    logging.info("Processing completed and saved to output file.")

if __name__ == "__main__":
    # Tên file input và output
    input_file = "dnr-lang-vi.json"
    output_file = "dnr-lang-vi-updated.json"

    start_time = datetime.now()
    process_domains(input_file, output_file, max_threads=10)
    end_time = datetime.now()
    logging.info(f"Completed in {end_time - start_time}")
