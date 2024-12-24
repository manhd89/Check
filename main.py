import urllib.request
import ssl
import json
import logging
from urllib.parse import urlparse, urlunparse

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
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

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
    None
]

def get_main_domain(domain):
    """
    Lấy tên miền chính (domain + suffix), loại bỏ 'www.' nếu có.
    """
    domain = domain.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    parts = domain.split('.')
    return '.'.join(parts[-2:])  # Lấy 2 phần cuối của tên miền

def get_redirected_domain(domain):
    """
    Kiểm tra xem domain có bị chuyển hướng hay không và trả về tên miền chính.
    """
    try:
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
            except Exception:
                continue
        return get_main_domain(domain)
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra tên miền {domain}: {e}")
        return get_main_domain(domain)

def collect_initiator_domains(data):
    """
    Thu thập tất cả các tên miền trong `initiatorDomains`.
    """
    domains = set()
    for rule in data:
        if "condition" in rule and "initiatorDomains" in rule["condition"]:
            domains.update(rule["condition"]["initiatorDomains"])
    return domains

def replace_domain_in_url(url, domain_mapping):
    """
    Thay thế phần tên miền chính trong URL bằng ánh xạ từ domain_mapping.
    """
    parsed_url = urlparse(url)
    old_domain = parsed_url.netloc
    new_domain = domain_mapping.get(old_domain, old_domain)
    if old_domain != new_domain:
        # Xây dựng lại URL với tên miền mới
        updated_url = urlunparse(parsed_url._replace(netloc=new_domain))
        logging.debug(f"URL được thay đổi từ '{url}' thành '{updated_url}'")
        return updated_url
    return url

def update_domains_in_rule(rule, domain_mapping):
    """
    Cập nhật các domain trong `initiatorDomains` và `urlFilter` của một rule.
    """
    # Cập nhật initiatorDomains
    if "condition" in rule and "initiatorDomains" in rule["condition"]:
        rule["condition"]["initiatorDomains"] = [
            domain_mapping.get(domain, domain)
            for domain in rule["condition"]["initiatorDomains"]
        ]

    # Cập nhật urlFilter
    if "condition" in rule and "urlFilter" in rule["condition"]:
        rule["condition"]["urlFilter"] = replace_domain_in_url(
            rule["condition"]["urlFilter"],
            domain_mapping
        )

    return rule

def main():
    try:
        with open("dnr-lang-vi.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        logging.info("Tệp JSON đã được tải thành công.")
    except Exception as e:
        logging.critical(f"Lỗi khi đọc tệp JSON: {e}")
        return

    # Thu thập danh sách tên miền từ `initiatorDomains`
    logging.info("Thu thập danh sách tên miền từ `initiatorDomains`...")
    domains = collect_initiator_domains(data)

    # Kiểm tra trạng thái chuyển hướng của các tên miền
    logging.info("Đang kiểm tra và ánh xạ tên miền...")
    domain_mapping = {}
    for domain in domains:
        redirected_domain = get_redirected_domain(domain)
        if redirected_domain != domain:
            domain_mapping[domain] = redirected_domain

    # Ánh xạ lại các rule trong JSON
    logging.info("Cập nhật `initiatorDomains` và `urlFilter` trong JSON...")
    for i, rule in enumerate(data):
        data[i] = update_domains_in_rule(rule, domain_mapping)

    # Lưu lại file JSON
    try:
        with open("dnr-lang-vi.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, separators=(",", ":"))
        logging.info("Tệp JSON đã được cập nhật và lưu thành công.")
    except Exception as e:
        logging.critical(f"Lỗi khi lưu tệp JSON: {e}")

if __name__ == "__main__":
    logging.info("Bắt đầu kiểm tra và cập nhật `initiatorDomains` & `urlFilter`...")
    main()
    logging.info("Hoàn thành!")
