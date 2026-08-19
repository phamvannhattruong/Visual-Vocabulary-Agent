import json
import re
import time
import requests
from bs4 import BeautifulSoup

# Danh sách các link cần cào
TARGET_URLS = [
    "https://langgo.edu.vn/huong-dan-doc-bang-phien-am-tieng-anh-ipa-luyen-phat-am-chuan-quoc-te",
    "https://ielts-fighter.com/tin-tuc/bang-phien-am-tieng-anh-ipa_mt1567386908.html", 
    "https://vn.elsaspeak.com/hoc-cach-phat-am-44-am-trong-tieng-anh/?srsltid=AfmBOorRkCxo3SFJdqjd3Lih5zqi_JL-iF7h02sIovZT1hMGmCNKFvWD",
    "https://ktdcgroup.vn/tai-lieu/bang-phien-am-tieng-anh-ipa-cach-phat-am-chuan-44-am-quoc-te/",
    "https://amslink.edu.vn/luyen-thi-cambridge/bang-phien-am-tieng-anh-ipa-hoc-cach-phat-am-ngan-gon-de-hieu.html"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def clean_text(text: str) -> str:
    """Xóa khoảng trắng thừa và dòng trống liên tiếp."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()

def crawl_single_url(url: str):
    """Cào nội dung của 1 đường link cụ thể."""
    print(f"[*] Đang gửi request tới: {url}...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"[!] Bỏ qua URL do lỗi kết nối: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # 1. Lấy Tiêu đề
    title_elem = soup.find("h1")
    title = title_elem.get_text(strip=True) if title_elem else "Bài viết hướng dẫn IPA"

    # 2. Vùng chứa bài viết
    content_container = (
        soup.find("article")
        or soup.find("div", class_=re.compile(r"content|detail|post-body|article-body|entry-content", re.I))
        or soup.find("main")
    )
    if not content_container:
        content_container = soup.body

    # 3. Loại bỏ thành phần rác
    for garbage in content_container.find_all(["script", "style", "nav", "footer", "form", "iframe", "noscript"]):
        garbage.decompose()

    # 4. Trích xuất nội dung và Bảng (Markdown Table)
    extracted_sections = []
    for elem in content_container.find_all(["h2", "h3", "h4", "p", "li", "table"]):
        tag_name = elem.name
        text = elem.get_text(separator=" ", strip=True)

        if not text or len(text) < 4:
            continue

        if tag_name in ["h2", "h3", "h4"]:
            extracted_sections.append(f"\n### {text}\n")
        elif tag_name == "li":
            extracted_sections.append(f"- {text}")
        elif tag_name == "table":
            # Chuyển bảng HTML sang bảng Markdown
            rows = []
            trs = elem.find_all("tr")
            for idx, tr in enumerate(trs):
                cols = [td.get_text(separator=" ", strip=True) for td in tr.find_all(["td", "th"])]
                if cols:
                    rows.append("| " + " | ".join(cols) + " |")
                    if idx == 0:
                        rows.append("| " + " | ".join(["---"] * len(cols)) + " |")
            if rows:
                extracted_sections.append("\n\n" + "\n".join(rows) + "\n\n")
        else:
            extracted_sections.append(text)

    full_content = clean_text("\n".join(extracted_sections))
    return {
        "title": title,
        "url": url,
        "content": full_content
    }

def crawl_all_articles(urls: list, output_txt="ipa_knowledge.txt", output_json="ipa_data.json"):
    all_data = []
    full_text_list = []

    # Duyệt qua từng URL
    for url in urls:
        data = crawl_single_url(url)
        if data and len(data["content"]) > 100:
            all_data.append(data)
            full_text_list.append(f"# {data['title']}\nNguồn: {data['url']}\n\n{data['content']}")
            print(f"[✓] Đã cào xong: {data['title']} ({len(data['content'])} ký tự)")
        time.sleep(1)  # Nghỉ 1 giây giữa các request để tránh bị chặn IP

    # 1. Lưu file Text tổng hợp
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write("\n\n" + "="*50 + "\n\n".join(full_text_list))

    # 2. Lưu file JSON tổng hợp
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 HOÀN THÀNH CÀO {len(all_data)}/{len(urls)} TRANG WEB!")
    print(f" -> File Text: {output_txt}")
    print(f" -> File JSON: {output_json}")

if __name__ == "__main__":
    crawl_all_articles(TARGET_URLS)