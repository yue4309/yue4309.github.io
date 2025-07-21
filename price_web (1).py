from flask import Flask, render_template_string, request
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# 工具：解析價格
def parse_price(text):
    digits = re.sub(r"[^\d]", "", text)
    return int(digits) if digits else None

# 🔍 momo 搜尋
def search_momo(keyword):
    url = "https://m.momoshop.com.tw/mosearch/Search.jsp"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://m.momoshop.com.tw"
    }
    html = requests.get(url, params={"searchKeyword": keyword}, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")
    items = []

    for prod in soup.select("li.goodsItem")[:5]:
        title_tag = prod.select_one("h3.prdName")
        price_tag = prod.select_one("b.price")
        link_tag = prod.select_one("a")

        if title_tag and price_tag and link_tag:
            title = title_tag.text.strip()
            price = parse_price(price_tag.text)
            link = "https://www.momoshop.com.tw" + link_tag.get("href")
            items.append({
                "platform": "momo",
                "title": title,
                "price": price,
                "link": link
            })

    if not items:
        items.append({
            "platform": "momo",
            "title": "無法抓取 momo 商品，請點連結自行查閱",
            "price": "",
            "link": f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={keyword}"
        })

    return items

# 🔍 PChome 搜尋
def search_pchome(keyword):
    try:
        url = "https://ecapi.pchome.com.tw/ecshop/prodapi/v2/search"
        params = {'q': keyword, 'page': 1, 'sort': 'sale/dc'}
        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://24h.pchome.com.tw'}
        resp = requests.get(f"{url}/all", params=params, headers=headers, timeout=10)
        data = resp.json()
        if "prods" not in data or len(data["prods"]) == 0:
            raise Exception("無資料")
        items = []
        for prod in data.get('prods', [])[:5]:
            items.append({
                "platform": "PChome",
                "title": prod.get("name"),
                "price": prod.get("price"),
                "link": f"https://24h.pchome.com.tw/prod/{prod.get('Id')}"
            })
        return items
    except:
        return [{
            "platform": "PChome",
            "title": "無法抓取 PChome 商品，請點連結自行查閱",
            "price": "",
            "link": f"https://24h.pchome.com.tw/search/v3.3/?q={keyword}"
        }]

# 🔍 Shopee 搜尋（提供搜尋頁連結）
def search_shopee(keyword):
    return [{
        "platform": "Shopee",
        "title": "點此前往 Shopee 搜尋該商品",
        "price": "",
        "link": f"https://shopee.tw/search?keyword={keyword}"
    }]

# 整合所有來源
def aggregate(keyword):
    return search_pchome(keyword) + search_momo(keyword) + search_shopee(keyword)

# HTML 網頁頁面（內嵌）
@app.route('/', methods=['GET', 'POST'])
def index():
    keyword = ''
    results = []
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        results = aggregate(keyword)
    return render_template_string("""
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>商品比價搜尋</title>
    <style>
        body { font-family: sans-serif; padding: 2rem; background-color: #f9f9f9; }
        input[type="text"] { width: 300px; padding: 0.5rem; }
        button { padding: 0.5rem 1rem; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 0.5rem; text-align: left; }
        th { background-color: #eee; }
    </style>
</head>
<body>
    <h1>🛒 商品比價搜尋</h1>
    <form method="POST">
        <input type="text" name="keyword" placeholder="請輸入商品名稱" value="{{ keyword }}">
        <button type="submit">開始搜尋</button>
    </form>

    {% if results %}
    <table>
        <tr><th>平台</th><th>商品名稱</th><th>價格</th><th>連結</th></tr>
        {% for item in results %}
        <tr>
            <td>{{ item.platform }}</td>
            <td>{{ item.title }}</td>
            <td>{{ item.price if item.price else '無資料' }}</td>
            <td><a href="{{ item.link }}" target="_blank">前往</a></td>
        </tr>
        {% endfor %}
    </table>
    {% endif %}
</body>
</html>
""", results=results, keyword=keyword)

# 執行網站
if __name__ == '__main__':
    app.run(debug=True)
