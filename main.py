import requests
from bs4 import BeautifulSoup
import csv

book_url = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"

def get_data(book_url) :
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

    category = soup.select_one("ul.breadcrumb li:nth-of-type(3) a").string

    rating_map = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5,
    }
    review_rating = rating_map[soup.select_one("p.star-rating.Three")["class"][1]]

    image_url = soup.select_one("div.item.active img")["src"]

    data = {
        "url page": product_page_url,
        "UPC": universal_product_code,
        "title": title,
        "price with tax": price_including_tax,
        "price without tax": price_excluding_tax,
        "availables": number_available,
        "description": product_description,
        "category": category,
        "rating": review_rating,
        "url image": image_url,
    }
    return data

def update_csv(data) :
    with open("books_details.csv", "w", newline="") as file:
        fieldnames = ['url page', "UPC", "title", "price with tax", "price without tax", "availables", "description", 'category', "rating", "url image"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(data)

update_csv(get_data(book_url))