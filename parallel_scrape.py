from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
import pandas as pd
import numpy as np
import requests
import io
import multiprocessing as mp
import time
import csv
import os

DELAY = 2

def download_image(down_path, url, file_name):
    request = requests.get(url)

    # Convert request data to image
    image_content = request.content
    image_file = io.BytesIO(image_content)
    image = Image.open(image_file)
    file_path = down_path + file_name

    # Save image
    with open(file_path, 'wb') as file:
        image.save(file)


def get_google_image(wd, delay, search):
    url = "https://images.google.com/"
    wd.get(url)
    search_bar = wd.find_element("id", "APjFqb")
    search_bar.send_keys(search + "\n")
    time.sleep(delay)

    image_urls = set()
    hrefs = set()

    # Scroll to bottom of page
    wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Find all image thumbnails
    thumbnails = wd.find_elements(By.CSS_SELECTOR, "a[class=\"wXeWr islib nfEiy\"]")
    for thumbnail in thumbnails:

        # Get image and source for thumbnail
        thumbnail.click()
        time.sleep(delay)
        images = wd.find_elements(By.CSS_SELECTOR, "img[class=\"r48jcc pT0Scc iPVvYb\"]")
        links = wd.find_elements(By.CSS_SELECTOR, "a[class=\"Du2c7e\"]")

        # Save download links
        for image in images:
            src = image.get_attribute('src')
            if src and "http" in src and ".jpg" in src:
                image_urls.add(image.get_attribute('src'))
                
                for link in links:
                    href = link.get_attribute('href')
                    hrefs.add(href)

        # Stop going through thumbnails if we got valid download link
        if len(image_urls) == 1:
            break

    return image_urls.pop(), hrefs.pop()

def scrape_for_titles(titles):
    wd = webdriver.Chrome()

    # Gather image urls
    urls = {}
    i = 0
    for id, title in titles:
        # Ignore if already downloaded
        if os.path.exists(f"covers/{id}.jpg"):
            i += 1
            continue
        
        # Get links and download
        downloaded = False
        extra_search = " videogame cover art"
        while not downloaded:
            # Get image links
            try:
                url, href = get_google_image(wd, DELAY, title + extra_search)
                urls[id, title] = url, href
            except:
                print("Error with getting", title)

            # Try downloading
            try:
                download_image("covers/", url, str(id) + ".jpg")
                downloaded = True
            except:
                print("Error with downloading", title)
                extra_search += " download"
        

        # Save link
        try:
            with open("links.csv", "w", ) as file:
                writer = csv.writer(file, delimiter=',')
                for id, title in urls:
                    url, href = urls[id, title]
                    writer.writerow([id, href])
        except:
            print("Error with saving link", title)

        print(f"Done {i}/{len(titles)}", title)
        i += 1

def main():
    item_data = pd.read_csv('data/games.csv')
    title_frame = item_data[['app_id', 'title']]
    titles = [(id, title) for _, id, title in title_frame.itertuples()]

    num_cpu = mp.cpu_count() - 1 # Leave one free
    indices = np.arange(len(titles))
    splits_ind = np.array_split(indices, num_cpu)
    splits = [titles[indices[0]:indices[-1]] for indices in splits_ind]
    
    for p in range(num_cpu):
        process = mp.Process(target=scrape_for_titles, args=[splits[p]])
        process.start()
    

if __name__ == '__main__':
    main()