import os
import time
import re
import csv
import requests
import unicodedata
from selenium import webdriver
from selenium.webdriver.common.by import By
from deep_translator import GoogleTranslator
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


BROWSERSTACK_USERNAME = 'vedantshiradhonk_g0msUx'
BROWSERSTACK_ACCESS_KEY = 'CrEL4joRsysd4zCqPezp'


BROWSERSTACK_CAPABILITIES = {
    "os": "Windows",
    "os_version": "10",
    "browser": "Chrome",
    "browser_version": "latest",
    "name": "El Pais Opinion Scraper Test",
    "build": "ElPais-Scraper-Build",
    "browserstack.local": False,
    "browserstack.debug": True,
}


def sanitize_text(text: str) -> str:
    normalized_text = unicodedata.normalize('NFD', text)
    replacements = {
        '�': 'a', 'í': 'i', 'ó': 'o', 'é': 'e', 'ú': 'u',
        'ñ': 'n', 'ü': 'u', 'á': 'a', 'è': 'e', 'ç': 'c',
        'ò': 'o', 'â': 'a', 'ô': 'o'
    }
    for wrong, correct in replacements.items():
        normalized_text = normalized_text.replace(wrong, correct)
    return normalized_text

def initialize_browserstack() -> webdriver.Remote:
    options = Options()
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.add_argument('--headless') 

    driver = webdriver.Remote(
        command_executor=f'https://{BROWSERSTACK_USERNAME}:{BROWSERSTACK_ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub',
        options=options
    )
    return driver


def scrape_opinion_articles(driver: webdriver.Remote):
    driver.get("https://elpais.com/")
    time.sleep(5)


    try:
        opinion_link = driver.find_element(By.LINK_TEXT, "Opinión")
        opinion_link.click()
        print("Navigated to the Opinion section.")
    except Exception as e:
        print(f"Failed to navigate to the Opinion section: {e}")
        return []

    time.sleep(5)


    articles = driver.find_elements(By.CSS_SELECTOR, "article")[:5]
    if not articles:
        print("No articles found in the Opinion section.")
        return []

    articles_data = []
    translator = GoogleTranslator(source='es', target='en')
    output_dir = "elpais_opinion_articles"
    os.makedirs(output_dir, exist_ok=True)

    for idx, article in enumerate(articles, start=1):
        try:
        
            title_element = article.find_element(By.TAG_NAME, "h2")
            title = sanitize_text(title_element.text)
            translated_title = translator.translate(title)
            print(f"Article {idx} Title (Spanish): {title}")
            print(f"Article {idx} Title (English): {translated_title}")

            content_element = article.find_element(By.TAG_NAME, "p")
            content = sanitize_text(content_element.text) if content_element else "No content available."

            
            img_element = article.find_elements(By.TAG_NAME, "img")
            if img_element:
                img_url = img_element[0].get_attribute("src")
                img_path = os.path.join(output_dir, f"article_{idx}_cover.jpg")
                response = requests.get(img_url)
                if response.status_code == 200:
                    with open(img_path, "wb") as img_file:
                        img_file.write(response.content)
                    print(f"Cover image for Article {idx} saved as {img_path}")
                else:
                    print(f"Failed to download cover image for Article {idx}")
            else:
                print(f"No cover image for Article {idx}")

            
            articles_data.append({
                'article_number': idx,
                'title_spanish': title,
                'title_english': translated_title,
                'content': content
            })

        except Exception as e:
            print(f"Error processing Article {idx}: {e}")

    return articles_data


def analyze_titles(articles_data):
    all_titles = [article['title_english'] for article in articles_data]
    word_counts = {}

    stopwords = set([
        "the", "and", "to", "a", "of", "in", "is", "for", "on", "with", "this", "at", "by", "as", "an", "it", "are", "that", "from", "but"
    ])

    for title in all_titles:
        words = re.findall(r'\w+', title.lower())
        for word in words:
            if word not in stopwords:
                word_counts[word] = word_counts.get(word, 0) + 1

    print("\nRepeated words in translated titles:")
    for word, count in word_counts.items():
        if count > 2:
            print(f"{word}: {count}")

def save_to_csv(articles_data):
    output_dir = "elpais_opinion_articles"
    csv_file = os.path.join(output_dir, "elpais_opinion_articles.csv")
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["article_number", "title_spanish", "title_english", "content"])
        writer.writeheader()
        for article in articles_data:
            writer.writerow(article)
    print(f"Data saved to {csv_file}")

def main():
    driver = initialize_browserstack()
    try:
        articles_data = scrape_opinion_articles(driver)
        if articles_data:
            analyze_titles(articles_data)
            save_to_csv(articles_data)
    finally:
        driver.quit()
        print("Scraping completed!")

if __name__ == "__main__":
    main()
