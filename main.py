from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import requests
import time
from deep_translator import GoogleTranslator  # Using deep-translator for translation
import re
import csv
import unicodedata

# Function to sanitize and normalize text (fix encoding issues)
def sanitize_text(text):
    # Normalize unicode characters (this will decompose accented characters and allow easier replacement)
    normalized_text = unicodedata.normalize('NFD', text)
    
    # Replace problematic characters with their proper Unicode equivalents
    replacements = {
        '�': 'a',  # Common encoding issue for "á"
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

    # Manually replace problematic characters
    for wrong, correct in replacements.items():
        normalized_text = normalized_text.replace(wrong, correct)

    # Return the normalized, sanitized text
    return normalized_text

# Initialize WebDriver
driver = webdriver.Chrome()  # Replace with webdriver.Firefox() if using Firefox
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

#Extract,Translate
output_dir = "elpais_opinion_articles"
os.makedirs(output_dir, exist_ok=True)  # Create output directory if it doesn't exist

for idx, article in enumerate(articles, start=1):
    try:
        
        title_element = article.find_element(By.TAG_NAME, "h2") # Extract title
        title = title_element.text
        print(f"Article {idx} Title (Spanish): {title}")

        # Sanitize normalize
        title = sanitize_text(title)

        translated_title = translator.translate(title) # Translate title
        print(f"Article {idx} Title (English): {translated_title}")

        # Extract the content (if available)
        content_element = article.find_element(By.TAG_NAME, "p")
        content = content_element.text if content_element else "No content available."
        print(f"Article {idx} Content: {content}")

        # Sanitize and normalize the content text
        content = sanitize_text(content)

        # Save the cover image (if available)
        img_element = article.find_elements(By.TAG_NAME, "img")  # Use find_elements to avoid errors
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

# Step 4: Repeated Word Analysis (remove stopwords and count)
all_titles = [article['title_english'] for article in articles_data]
word_counts = {}

# List of common stopwords (you can expand this list)
stopwords = set([
    "the", "and", "to", "a", "of", "in", "is", "for", "on", "with", "this", "at", "by", "as", "an", "it", "are", "that", "from", "but"
])
# Count word frequency in all translated titles
for title in all_titles:
    words = re.findall(r'\w+', title.lower())  # Use regex to split words and make them lowercase
    for word in words:
        if word not in stopwords:  # Remove stopwords from counting
            word_counts[word] = word_counts.get(word, 0) + 1

# Print repeated words and their counts
print("\nRepeated words in translated titles:")
for word, count in word_counts.items():
    if count > 2:  # Only print words repeated more than twice
        print(f"{word}: {count}")

# Step 5: Save Data to CSV (or JSON)
csv_file = os.path.join(output_dir, "elpais_opinion_articles.csv")
with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["article_number", "title_spanish", "title_english", "content"])
    writer.writeheader()
    for article in articles_data:
        writer.writerow(article)

print(f"Data saved to {csv_file}")

# Close the WebDriver
driver.quit()
print("Scraping completed!")