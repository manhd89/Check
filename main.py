import urllib.request
import ssl
import json
import logging
from urllib.parse import urlparse, urlunparse
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

# Tạo context SSL
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False  # Bỏ qua kiểm tra hostname
ssl_context.verify_mode = ssl.CERT_NONE  # Bỏ qua xác minh chứng chỉ

# Danh sách headers để xử lý các trang web yêu cầu thông tin cụ thể
HEADERS_LIST = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    },
    None  # Không sử dụng headers (mặc định)
]

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
    """
    try:
        logging.debug(f"Đang kiểm tra tên miền: {domain}")
        url = f"https://{domain}"
        for headers in HEADERS_LIST:
            try:
                req = urllib.request.Request(url, headers=headers or {})
                with urllib.request.urlopen(req, timeout=15, context=ssl_context) as response:
                    redirected_url = response.geturl()
                    redirected_domain = urlparse(redirected_url).netloc
                    redirected_domain = get_main_domain(redirected_domain)
                    if redirected_domain != get_main_domain(domain):
                        logging.info(f"Tên miền {domain} chuyển hướng tới {redirected_domain}")
                    return redirected_domain
            except urllib.error.HTTPError as e:
                logging.warning(f"HTTP Error {e.code} với {url} và headers {headers}")
            except Exception as e:
                logging.debug(f"Lỗi với {url} và headers {headers}: {e}")
        # Nếu tất cả thử nghiệm đều thất bại
        return get_main_domain(domain)
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra tên miền {domain}: {e}")
        return get_main_domain(domain)

def update_url_filter(url_filter, old_domain, new_domain):
    """
    Cập nhật `urlFilter` bằng cách thay thế tên miền cũ bằng tên miền mới.
    Các phần khác của URL như path, wildcard sẽ giữ nguyên.
    """
    parsed_url = urlparse(url_filter)
    
    # Thay thế tên miền (netloc) trong URL
    if old_domain in parsed_url.netloc:
        new_netloc = parsed_url.netloc.replace(old_domain, new_domain)
        updated_url = parsed_url._replace(netloc=new_netloc)
        return urlunparse(updated_url)
    return url_filter

def update_domains_in_rule(rule):
    """
    Cập nhật các tên miền trong rule bằng cách kiểm tra và thay thế trực tiếp.
    Cập nhật cả `initiatorDomains` và `urlFilter`.
    """
    if "condition" in rule:
        # Cập nhật initiatorDomains
        if "initiatorDomains" in rule["condition"]:
            domains = rule["condition"]["initiatorDomains"]
            updated_domains = {}
            
            # Kiểm tra tên miền nào thay đổi
            for domain in domains:
                updated_domain = get_redirected_domain(domain)
                if updated_domain != get_main_domain(domain):
                    updated_domains[domain] = updated_domain

            # Cập nhật initiatorDomains nếu có tên miền thay đổi
            for old_domain, new_domain in updated_domains.items():
                # Cập nhật initiatorDomains
                rule["condition"]["initiatorDomains"] = [new_domain if d == old_domain else d for d in rule["condition"]["initiatorDomains"]]
                
                # Cập nhật urlFilter nếu có
                if "urlFilter" in rule["condition"]:
                    url_filter = rule["condition"]["urlFilter"]
                    updated_url_filter = update_url_filter(url_filter, old_domain, new_domain)
                    rule["condition"]["urlFilter"] = updated_url_filter

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
        update_domains_in_rule(rule)

    try:
        with open("dnr-lang-vi.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, separators=(",", ":"))
        logging.info("Tệp JSON đã được cập nhật và lưu thành công.")
    except Exception as e:
        logging.critical(f"Lỗi khi lưu tệp JSON: {e}")

if __name__ == "__main__":
    start_time = datetime.now()
    logging.info("Bắt đầu kiểm tra và cập nhật tên miền...")
    main()
    end_time = datetime.now()
    logging.info(f"Hoàn thành. Tổng thời gian: {end_time - start_time}")
