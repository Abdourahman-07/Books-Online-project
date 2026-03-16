import os  # Pour créer des dossiers et fichiers
import csv  # Pour interagir avec les fichiers csv
import time  # Pour ajouter des délais de code
from urllib.parse import urljoin  # Pour combiner des URL
import requests  # Pour envoyer des requêtes
from bs4 import BeautifulSoup  # Pour interagir avec le HTML

base_url = "https://books.toscrape.com/"

def get_home_page(url):
    try:
        response = requests.get(url)
        return response
    except requests.RequestException:
        print(f"Erreur réseau sur {url}")
        return None

def get_categories_links():
    response = get_home_page(base_url)
    if response is None:
        return {}
    category_links = {}
    soup = BeautifulSoup(response.text, "html.parser")
    for a in soup.select("ul.nav-list ul li a"):
        category_name = a.get_text(strip=True)
        relative_href = a["href"]
        category_url = urljoin(base_url, relative_href)
        category_links[category_name] = category_url
    return category_links

def get_book_links_from_category_page(url):
    response = get_home_page(url)
    if response is None:
        print(f"Impossible de récupérer la page de catégorie : {url}")
        return [], None
    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for article in soup.select("article.product_pod h3 a"):
        relative_href = article["href"]
        full_url = urljoin(url, relative_href)
        links.append(full_url)
    return links, soup

def get_book_links_for_category(category_url):
    all_links = []
    while True:
        links, soup = get_book_links_from_category_page(category_url)
        if soup is None:
            break
        all_links.extend(links)
        next_link = soup.select_one("li.next a")
        if not next_link:
            break
        next_href = next_link["href"]
        category_url = urljoin(category_url, next_href)
    return all_links

def sanitize_filename(text):
    invalid_chars = r'\/:*?"<>|'
    for char in invalid_chars:
        text = text.replace(char, "_")
    return text.strip().replace(" ", "_")


def download_image(image_url, category, upc, title, images_root="images"):
    safe_category = category.lower().replace(" ", "_").replace("/", "_")
    category_dir = os.path.join(images_root, safe_category)
    os.makedirs(category_dir, exist_ok=True)
    ext = os.path.splitext(image_url)[1]
    if not ext:
        ext = ".jpg"
    safe_title = sanitize_filename(title)
    filename = f"{upc}_{safe_title}{ext}"
    filepath = os.path.join(category_dir, filename)
    response = get_home_page(image_url)
    if response is None:
        print(f"Impossible de télécharger l'image : {image_url}")
        return ""
    with open(filepath, "wb") as file:
        file.write(response.content)
    return filepath

def get_data_product(book_url):
    page_product = get_home_page(book_url)
    if page_product is None:
        return {
            "product_page_url": book_url,
            "universal_product_code": "",
            "title": "",
            "price_including_tax": "",
            "price_excluding_tax": "",
            "number_available": "",
            "product_description": "",
            "category": "",
            "review_rating": "",
            "image_url": "",
            "image_path": "",
            "error": "connection_failed",
        }
    soup = BeautifulSoup(page_product.text, "html.parser")
    product_page_url = book_url
    universal_product_code = soup.select_one("table.table.table-striped tr:nth-of-type(1) td").get_text(strip=True)
    title = soup.select_one("div.col-sm-6.product_main h1").get_text(strip=True)
    price_including_tax = soup.select_one("table.table.table-striped tr:nth-of-type(4) td").get_text(strip=True)
    price_excluding_tax = soup.select_one("table.table.table-striped tr:nth-of-type(3) td").get_text(strip=True)
    p = soup.select_one("p.instock.availability")
    number_available = p.get_text(strip=True)
    description_tag = soup.select_one("div.sub-header + p")
    product_description = (description_tag.get_text(strip=True) if description_tag else "")
    category = soup.select_one("ul.breadcrumb li:nth-of-type(3)").get_text(strip=True)
    rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    rating_word = soup.select_one("p.star-rating")["class"][1]#Sélection de la 2ème classe de p (cette classe représente un nombre de 1 à 5 en toutes lettres)
    review_rating = rating_map.get(rating_word, 0)
    img_src = soup.select_one("div.item.active img")["src"]
    image_url = urljoin(product_page_url, img_src)
    local_image_path = download_image(image_url, category, universal_product_code, title)
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
        "image_path": local_image_path,
        "error": "",
    }
    return data

def save_category_to_csv(category_name, book_links, output_dir="csv_books"):
    os.makedirs(output_dir, exist_ok=True)
    safe_category = category_name.lower().replace(" ", "_").replace("/", "_")
    filename = os.path.join(output_dir, f"{safe_category}.csv")
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
        "image_path",
        "error",
    ]
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for url in book_links:
            data = get_data_product(url)
            writer.writerow(data)
    print(f"Catégorie '{category_name}' sauvegardée : {filename}")

def main():
    categories = get_categories_links()
    for category_name, category_url in categories.items():
        book_links = get_book_links_for_category(category_url)
        save_category_to_csv(category_name, book_links)
        time.sleep(0.5)#léger temps de pause entre chaque nouveau fichier enregistré, pour ne pas surcharger le site

main()