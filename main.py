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

def get_redirected_domain(domain):
    """
    Kiểm tra xem domain có bị chuyển hướng hay không và trả về tên miền đích không có tiền tố 'www.'.
    """
    try:
        logging.debug(f"Đang kiểm tra tên miền: {domain}")
        url = f"http://{domain}"  # Chuẩn hóa URL với http
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            redirected_url = response.geturl()  # URL sau khi redirect (nếu có)
            redirected_domain = urlparse(redirected_url).netloc  # Lấy tên miền đầy đủ
            # Loại bỏ 'www.' nếu có
            redirected_domain = redirected_domain.lstrip("www.")
            if redirected_domain != domain.lstrip("www."):
                logging.info(f"Tên miền {domain} chuyển hướng tới {redirected_domain}")
            return redirected_domain
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra tên miền {domain}: {e}")
        return domain.lstrip("www.")  # Giữ nguyên tên miền cũ (không có 'www.') nếu có lỗi

def process_domains(domains):
    """
    Kiểm tra danh sách tên miền bằng đa luồng và trả về danh sách các tên miền đã cập nhật.
    """
    updated_domains = []
    with ThreadPoolExecutor(max_workers=10) as executor:  # Tối đa 10 luồng
        future_to_domain = {executor.submit(get_redirected_domain, domain): domain for domain in domains}
        for future in as_completed(future_to_domain):
            try:
                result = future.result()
                updated_domains.append(result)
            except Exception as e:
                logging.error(f"Lỗi xử lý một tên miền: {e}")
    return updated_domains

def main():
    # Đọc tệp JSON
    try:
        with open("dnr-lang-vi.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        logging.info("Tệp JSON đã được tải thành công.")
    except Exception as e:
        logging.critical(f"Lỗi khi đọc tệp JSON: {e}")
        return

    # Kiểm tra và cập nhật initiatorDomains
    for i, rule in enumerate(data):
        logging.debug(f"Đang xử lý rule {i+1}/{len(data)}")
        if "initiatorDomains" in rule.get("condition", {}):
            domains = rule["condition"]["initiatorDomains"]
            # Xử lý đa luồng để kiểm tra redirect của các domain
            updated_domains = process_domains(domains)
            rule["condition"]["initiatorDomains"] = updated_domains

    # Lưu kết quả vào tệp mới
    try:
        with open("updated-dnr-lang-vi.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logging.info("Tệp JSON đã được cập nhật và lưu thành công.")
    except Exception as e:
        logging.critical(f"Lỗi khi lưu tệp JSON: {e}")

if __name__ == "__main__":
    start_time = datetime.now()
    logging.info("Bắt đầu kiểm tra tên miền...")
    main()
    end_time = datetime.now()
    logging.info(f"Hoàn thành kiểm tra tên miền. Tổng thời gian: {end_time - start_time}")
