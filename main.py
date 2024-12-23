import urllib.request
import json
import logging
from urllib.parse import urlparse
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
    Kiểm tra xem domain có bị chuyển hướng hay không và trả về tên miền đích.
    """
    try:
        logging.debug(f"Đang kiểm tra tên miền: {domain}")
        url = f"http://{domain}"
        with urllib.request.urlopen(url, timeout=5) as response:
            redirected_url = response.geturl()  # URL sau khi redirect (nếu có)
            redirected_domain = urlparse(redirected_url).netloc  # Lấy tên miền đích
            logging.info(f"Tên miền {domain} chuyển hướng tới {redirected_domain}")
            return redirected_domain
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra tên miền {domain}: {e}")
        return None

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
            updated_domains = []
            for domain in rule["condition"]["initiatorDomains"]:
                # Lấy tên miền đích sau khi kiểm tra redirect
                redirected_domain = get_redirected_domain(domain)
                if redirected_domain:
                    # Thêm tên miền đích vào danh sách mới nếu hợp lệ
                    updated_domains.append(redirected_domain)
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
