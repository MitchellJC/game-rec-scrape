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
    try:
        request = requests.get(url, timeout=10)
    except requests.exceptions.Timeout:
        print("Request timed out")


    # Convert request data to image
    image_content = request.content
    image_file = io.BytesIO(image_content)
    image = Image.open(image_file)
    file_path = down_path + file_name

    # Save image
    with open(file_path, 'wb') as file:
        image.save(file)


def get_google_image(wd, delay, search, id):
    url = "https://images.google.com/"
    wd.get(url)
    search_bar = wd.find_element("id", "APjFqb")
    search_bar.send_keys(search + "\n")
    time.sleep(delay)

    image_urls = set()
    hrefs = set()

    downloaded_image = False
    got_href = False   

    while not (downloaded_image and got_href):
        # Scroll to bottom of page
        wd.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)

        # Load more images
        show_mores = wd.find_elements(By.CSS_SELECTOR, "input[class=\"LZ4I\"]")
        for show_more in show_mores:
            try:
                show_more.click()
            except:
                continue
            time.sleep(delay)
            break
        see_more_anyways = wd.find_elements(By.CSS_SELECTOR, "span[class=\"XfJHbe\"]")
        for see_more_anyway in see_more_anyways:
            try:
                see_more_anyway.click()
            except:
                continue
            time.sleep(delay)
            break

        # Find all image thumbnails
        thumbnails = wd.find_elements(By.CSS_SELECTOR, "a[class=\"wXeWr islib nfEiy\"]")
        for thumbnail in thumbnails:
            if downloaded_image and got_href:
                    break
            
            # Get image and source for thumbnail
            try:
                thumbnail.click()
            except:
                continue

            time.sleep(delay)
            
            # Try find image and link
            try:
                images = wd.find_elements(By.CSS_SELECTOR, "img[class=\"r48jcc pT0Scc iPVvYb\"]")
                links = wd.find_elements(By.CSS_SELECTOR, "a[class=\"Du2c7e\"]")
            except:
                print("Error finding images and links for", search)

            # Download image and save source
            for image in images:
                if downloaded_image and got_href:
                    break

                # If valid image link
                src = image.get_attribute('src')
                if src and "http" in src and ".jpg" in src:
                    url = image.get_attribute('src')

                    # Try downloading
                    try:
                        download_image("covers/", url, str(id) + ".jpg")
                        downloaded_image = True
                    except:
                        downloaded_image = False
                        print("Error with downloading", search)
                        continue
                    
                    # Try finding source link
                    for link in links:
                        try:
                            href = link.get_attribute('href')
                            got_href = True
                            break
                        except:
                            got_href = False
                            print("Error getting ref for", search)
                            continue

    return url, href

def scrape_for_titles(titles):
    wd = webdriver.Chrome()

    titles = [(id, title) for id, title in titles if not os.path.exists(f"covers/{id}.jpg")]

    # Gather image urls
    urls = {}
    i = 0
    for id, title in titles:
        # Ignore if already downloaded
        if os.path.exists(f"covers/{id}.jpg"):
            i += 1
            continue
        
        # Get links and download
        extra_search = " videogame cover art"
  
        # Try download image
        url, href = get_google_image(wd, DELAY, title + extra_search, id)
        urls[id, title] = url, href
        
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

    num_cpu =  mp.cpu_count()
    indices = np.arange(len(titles))
    splits_ind = np.array_split(indices, num_cpu)
    splits = [titles[indices[0]:indices[-1]] for indices in splits_ind]
    
    # Spawn a process for each cpu
    for p in range(num_cpu):
        process = mp.Process(target=scrape_for_titles, args=[splits[p]])
        process.start()
    

if __name__ == '__main__':
    main()