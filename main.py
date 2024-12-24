import urllib.request
import ssl
import json
import logging
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from time import sleep

# Cấu hình logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("domain_check.log", encoding="utf-8")
    ]
)

# Tạo context SSL
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False  # Bỏ qua kiểm tra hostname
ssl_context.verify_mode = ssl.CERT_NONE  # Bỏ qua xác minh chứng chỉ

def get_main_domain(domain):
    """
    Lấy tên miền chính (domain + suffix), loại bỏ 'www.' nếu có.
    """
    domain = domain.lower()
    if domain.startswith("www."):
        domain = domain[4:]  # Loại bỏ 'www.'
    parts = domain.split('.')
    return '.'.join(parts[-2:])  # Lấy 2 phần cuối cùng của tên miền

def get_redirected_domain(domain):
    """
    Kiểm tra xem domain có bị chuyển hướng hay không và trả về tên miền chính.
    Chỉ sử dụng HTTPS.
    """
    try:
        logging.debug(f"Đang kiểm tra tên miền: {domain}")
        # Danh sách các cấu hình header phù hợp với trang web ở Việt Nam
        headers_list = [
            {  # Header chi tiết
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
                "Connection": "keep-alive",
            },
            {  # Header đơn giản
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
            None  # Không sử dụng header
        ]

        for headers in headers_list:
            try:
                url = f"https://{domain}"  # Chỉ kiểm tra HTTPS
                if headers is not None:
                    req = urllib.request.Request(url, headers=headers)
                else:
                    req = urllib.request.Request(url)

                with urllib.request.urlopen(req, timeout=15, context=ssl_context) as response:
                    # Kiểm tra chuyển hướng
                    redirected_url = response.geturl()
                    redirected_domain = urlparse(redirected_url).netloc
                    redirected_domain = get_main_domain(redirected_domain)
                    if redirected_domain != get_main_domain(domain):
                        logging.info(f"Tên miền {domain} chuyển hướng tới {redirected_domain}")
                    return redirected_domain

            except urllib.error.HTTPError as e:
                logging.warning(f"HTTP Error {e.code} với https://{domain} và header {headers}")
            except Exception as e:
                logging.debug(f"Lỗi với https://{domain} và header {headers}: {e}")
        
        return get_main_domain(domain)  # Giữ nguyên tên miền nếu tất cả thử nghiệm đều thất bại
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra tên miền {domain}: {e}")
        return get_main_domain(domain)

def process_domains(domains):
    """
    Kiểm tra danh sách tên miền bằng đa luồng và trả về danh sách các tên miền đã cập nhật.
    """
    updated_domains = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        future_to_domain = {executor.submit(get_redirected_domain, domain): domain for domain in domains}
        for future in as_completed(future_to_domain):
            try:
                result = future.result()
                updated_domains.append(result)
            except Exception as e:
                logging.error(f"Lỗi xử lý một tên miền: {e}")
    return updated_domains

def main():
    try:
        with open("dnr-lang-vi.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        logging.info("Tệp JSON đã được tải thành công.")
    except Exception as e:
        logging.critical(f"Lỗi khi đọc tệp JSON: {e}")
        return

    for i, rule in enumerate(data):
        logging.debug(f"Đang xử lý rule {i+1}/{len(data)}")
        if "initiatorDomains" in rule.get("condition", {}):
            domains = rule["condition"]["initiatorDomains"]
            updated_domains = process_domains(domains)
            rule["condition"]["initiatorDomains"] = updated_domains

    try:
        # Nén file JSON bằng cách loại bỏ khoảng trắng thừa
        with open("dnr-lang-vi.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, separators=(",", ":"))
        logging.info("Tệp JSON đã được cập nhật và lưu thành công.")
    except Exception as e:
        logging.critical(f"Lỗi khi lưu tệp JSON: {e}")

if __name__ == "__main__":
    start_time = datetime.now()
    logging.info("Bắt đầu kiểm tra tên miền...")
    main()
    end_time = datetime.now()
    logging.info(f"Hoàn thành kiểm tra tên miền. Tổng thời gian: {end_time - start_time}")
