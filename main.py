from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import requests
import time
from deep_translator import GoogleTranslator
import re
import csv
import unicodedata


def sanitize_text(text):

    normalized_text = unicodedata.normalize('NFD', text)
    
    # Replacing problematic characters
    replacements = {
        '�': 'a', 
        'í': 'i',
        'ó': 'o',
        'é': 'e',
        'ú': 'u',
        'ñ': 'n',
        'ü': 'u',
        'á': 'a',
        'è': 'e',
        'ç': 'c',
        'ò': 'o',
        'â': 'a',
        'ô': 'o'
    }

    # replacng blematic characters
    for wrong, correct in replacements.items():
        normalized_text = normalized_text.replace(wrong, correct)

    return normalized_text


driver = webdriver.Chrome()  
driver.get("https://elpais.com/")


time.sleep(5) 

#Navigate to Opinion
try:
    opinion_link = driver.find_element(By.LINK_TEXT, "Opinión") 
    opinion_link.click()
    print("Navigated to the Opinion section.")
except Exception as e:
    print("Failed to navigate to the Opinion section:", e)
    driver.quit()
    exit()

#Fetch First5Articles
time.sleep(5)  # Wait for Opinion page to load
articles = driver.find_elements(By.CSS_SELECTOR, "article")[:5]

if not articles:
    print("No articles found in the Opinion section.")
    driver.quit()
    exit()

translator = GoogleTranslator(source='es', target='en')

#list store data
articles_data = []

#Extract,Translate here
output_dir = "elpais_opinion_articles"
os.makedirs(output_dir, exist_ok=True)

for idx, article in enumerate(articles, start=1):
    try:
        
        title_element = article.find_element(By.TAG_NAME, "h2") # Extracting title
        title = title_element.text
        print(f"Article {idx} Title (Spanish): {title}")

        title = sanitize_text(title)

        translated_title = translator.translate(title) # Translating title
        print(f"Article {idx} Title (English): {translated_title}")

        # Extract the content (if available)
        content_element = article.find_element(By.TAG_NAME, "p")
        content = content_element.text if content_element else "No content available."
        print(f"Article {idx} Content: {content}")


        content = sanitize_text(content)

        # Saving the cover file
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

        # Save article data
        articles_data.append({
            'article_number': idx,
            'title_spanish': title,
            'title_english': translated_title,
            'content': content
        })

    except Exception as e:
        print(f"Error processing Article {idx}: {e}")

#Repeated Word Analysis
all_titles = [article['title_english'] for article in articles_data]
word_counts = {}

# List of common stopwords
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

# Save Data to CSV (or JSON)
csv_file = os.path.join(output_dir, "elpais_opinion_articles.csv")
with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["article_number", "title_spanish", "title_english", "content"])
    writer.writeheader()
    for article in articles_data:
        writer.writerow(article)

print(f"Data saved to {csv_file}")

driver.quit()
print("Scraping completed!")
# Close the WebDriver
