import urllib.request
import json
import logging
from datetime import datetime

# Cấu hình logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # In log ra console
        logging.FileHandler("domain_check.log", encoding="utf-8")  # Lưu log vào file
    ]
)

def check_domain(domain):
    """
    Hàm kiểm tra tên miền bằng cách gửi yêu cầu HTTP.
    """
    try:
        logging.debug(f"Đang kiểm tra tên miền: {domain}")
        with urllib.request.urlopen(f"http://{domain}", timeout=5) as response:
            if response.status == 200:
                logging.info(f"Tên miền hợp lệ: {domain}")
                return True
            else:
                logging.warning(f"Tên miền không phản hồi trạng thái 200: {domain}")
                return False
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra tên miền {domain}: {e}")
        return False

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
            valid_domains = []
            for domain in rule["condition"]["initiatorDomains"]:
                if check_domain(domain):
                    valid_domains.append(domain)
            rule["condition"]["initiatorDomains"] = valid_domains

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
