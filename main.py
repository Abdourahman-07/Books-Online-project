import requests
from bs4 import BeautifulSoup
import csv
from urllib.parse import urljoin

category_url = "https://books.toscrape.com/catalogue/category/books/historical-fiction_4/index.html"

def get_book_links_from_category_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for article in soup.select("article.product_pod h3 a"):
        relative_href = article["href"]
        full_url = urljoin(url, relative_href)
        links.append(full_url)
    return links, soup


def get_book_links():
    all_links = []
    url = category_url
    while True:
        links, soup = get_book_links_from_category_page(url)
        all_links.extend(links)
        next_link = soup.select_one("li.next a")
        if not next_link:
            break
        next_href = next_link["href"]
        url = urljoin(url, next_href)
    return all_links

def get_data_product(book_url):
    page_product = requests.get(book_url)
    soup = BeautifulSoup(page_product.text, 'html.parser')

    product_page_url = book_url
    universal_product_code = soup.select_one("table.table.table-striped tr:nth-of-type(1) td").string
    title = soup.select_one("div.col-sm-6.product_main h1").string
    price_including_tax = soup.select_one("table.table.table-striped tr:nth-of-type(4) td").string
    price_excluding_tax = soup.select_one("table.table.table-striped tr:nth-of-type(3) td").string
    p = soup.select_one("p.instock.availability")
    number_available = p.get_text(strip=True)
    product_description = soup.select_one("div.sub-header + p").string
    category = soup.select_one("ul.breadcrumb li:nth-of-type(3)").get_text(strip=True)
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    rating_word = soup.select_one("p.star-rating")["class"][1]
    review_rating = rating_map[rating_word]
    img_src = soup.select_one("div.item.active img")["src"]
    image_url = urljoin(product_page_url, img_src)

    data = {
        "product_page_url": product_page_url,
        "universal_product_code": universal_product_code,
        "title": title,
        "price_including_tax": price_including_tax,
        "price_excluding_tax": price_excluding_tax,
        "number_available": number_available,
        "product_description": product_description,
        "category": category,
        "review_rating": review_rating,
        "image_url": image_url,
    }
    return data

def update_csv_books(filename):
    fieldnames = [
        "product_page_url",
        "universal_product_code",
        "title",
        "price_including_tax",
        "price_excluding_tax",
        "number_available",
        "product_description",
        "category",
        "review_rating",
        "image_url",
    ]

    book_links = get_book_links()

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for url in book_links:
            data = get_data_product(url)
            writer.writerow(data)

update_csv_books("historical_fiction_books.csv")