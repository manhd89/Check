import urllib.request
import json

def check_domain(domain):
    try:
        # Thử gửi yêu cầu tới tên miền
        with urllib.request.urlopen(f"http://{domain}", timeout=5) as response:
            return response.status == 200
    except:
        return False

# Đọc tệp JSON
with open("dnr-lang-vi.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Kiểm tra và cập nhật initiatorDomains
for rule in data:
    if "initiatorDomains" in rule["condition"]:
        valid_domains = []
        for domain in rule["condition"]["initiatorDomains"]:
            if check_domain(domain):
                valid_domains.append(domain)
        rule["condition"]["initiatorDomains"] = valid_domains

# Lưu kết quả vào tệp mới
with open("updated-dnr-lang-vi.json", "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=4)

print("Kiểm tra và cập nhật xong.")
