
from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
import pandas as pd
import requests
import io
import time
import csv

DELAY = 2

def download_image(down_path, url, file_name):
    request = requests.get(url)

    image_content = request.content
    image_file = io.BytesIO(image_content)
    image = Image.open(image_file)
    file_path = down_path + file_name

    with open(file_path, 'wb') as file:
        image.save(file)


def get_google_image(wd, delay, search):
    url = "https://images.google.com/"
    wd.get(url)
    search_bar = wd.find_element("id", "APjFqb")
    search_bar.send_keys(search + "\n")
    time.sleep(delay)

    image_urls = set()

    thumbnails = wd.find_elements(By.CSS_SELECTOR, "a[class=\"wXeWr islib nfEiy\"]")
    for thumbnail in thumbnails:
        thumbnail.click()
        time.sleep(delay)
        images = wd.find_elements(By.CSS_SELECTOR, "img[class=\"r48jcc pT0Scc iPVvYb\"]")
        for image in images:
            src = image.get_attribute('src')
            if src and "http" in src and ".jpg" in src:
                image_urls.add(image.get_attribute('src'))

        if len(image_urls) == 1:
            break

    return image_urls.pop()

def main():
    item_data = pd.read_csv('data/games.csv')
    title_frame = item_data[['app_id', 'title']]
    titles = [(id, title) for _, id, title in title_frame.itertuples()]

    wd = webdriver.Chrome()

    # Gather image urls
    urls = {}
    for id, title in titles[:10]:
        url = get_google_image(wd, DELAY, title + " videogame cover art")
        urls[id, title] = url
        print(title, url)
        
    # Download images
    for id, title in urls:
        url = urls[id, title]
        download_image("covers/", url, str(id) + ".jpg")
        
    input()

if __name__ == '__main__':
    main()