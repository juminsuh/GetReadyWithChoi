import os
import time
import re
import json 
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import mimetypes

def wait_for_item(driver):
    
    # wait until "virtuoso-item-list" be found
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, 'div[data-testid="virtuoso-item-list"]')
    ))

def get_container(driver, i):

    # find the container which includes "virtuoso-item-list"
    container = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="virtuoso-item-list"]')
    
    # make item selector which indicates each item
    item_selector = f'div[data-testid="virtuoso-item-list"] div[data-index="{i}"]'
    
    return container, item_selector

def save_image(src_url, img_dir, label):

    # save results: download image, write dictionary
    if src_url:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.musinsa.com/"
        }
        resp = requests.get(src_url, headers=headers, timeout=20)
        if resp.status_code == 200:
            ext = None
            ctype = resp.headers.get("Content-Type", "")
            ext = mimetypes.guess_extension(ctype.split(";")[0]) if ctype else None
            if not ext:
                if ".jpg" in src_url or ".jpeg" in src_url:
                    ext = ".jpg"
                elif ".png" in src_url:
                    ext = ".png"
                else:
                    ext = ".jpg"

            fname = os.path.join(img_dir, f"snap_{label}{ext}")
            with open(fname, "wb") as f:
                f.write(resp.content)
            print(f"   💾 이미지 저장: {fname}")
        else:
            print(f"   ❌ 이미지 다운로드 실패: {resp.status_code}")

def crawl(url_lists, json_dir="json", img_dir="images", tpo_list=[], num_crawl=[]):
    
    # create directories
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)
    label = 0
    results = []
    
    # open chrome browser for once
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new") # no chrome display
    driver = webdriver.Chrome(options=options)
        
    try:
        for t, url_list in enumerate(url_lists):
            print(f"\n✅ === {t+1}/{len(url_lists)} processing...")
            tpo = tpo_list[t]
            for index, url in enumerate(url_list):
                print(f"\n  💬 === {index+1}/{len(url_list)} processing... ===")
                driver.get(url)
                wait_for_item(driver=driver)

                target_count = num_crawl[t][index]
                for i in range(1, target_count+1):
                    label += 1
                    print(f"\n👉 {label}번째 아이템 처리 중...")
                    container, item_selector = get_container(driver=driver, i=i)
                    
                    try:
                        # find i-th item if the item is shown at the screen
                        _ = driver.find_element(By.CSS_SELECTOR, item_selector)
                        print(f"📌 Try occurs")
                    except:
                        # i-th item not found, scroll a little bit so that i-th item be loaded at the screen
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", container)
                        time.sleep(0.5)
                        print(f"‼️ Exception occurs")
                    print(f"    😊 item {label} is found at the screen.")

                    # place i-th item to the center in order to be shown at the center of the screen
                    driver.execute_script(
                        "document.querySelector(arguments[0]).scrollIntoView({block:'center'});",
                        item_selector
                    )
                    time.sleep(0.8) 
                    print(f"    🥳 item {label} is shown at the center of the screen.")
                    
                    # find i-th item which has img[src] attribute
                    imgs = driver.find_elements(
                        By.CSS_SELECTOR,
                        f'{item_selector} img[src]'
                    )
                    # keep finding...
                    if not imgs:
                        print("   🔎 img[src] 없음(아직 로드 전일 수 있어요). 재시도...")
                        time.sleep(0.8)
                        imgs = driver.find_elements(
                            By.CSS_SELECTOR,
                            f'{item_selector} img[src]'
                        )
                    if not imgs:
                        print("     ⚠️ 끝까지 찾지 못했어요. 다음으로 넘어갑니다.")
                        continue

                    img = imgs[0] 
                    src_url  = img.get_attribute("src") or ""

                    save_image(src_url=src_url, img_dir=img_dir, label=label)
                    
                    results.append(
                        {"index": label, 
                        "TPO": tpo,
                        "src": src_url}
                    )

                    # scroll for 800 pixels down
                    driver.execute_script("window.scrollBy(0, 800);")
                    time.sleep(1.5)

    finally:
        driver.quit()
    
    json_path = os.path.join(json_dir, "snap.json")
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\n😆 Crawling is Done!")
        
def remove_duplicates(img_dir="images"):
    print("\n🧐 Start Remove Duplicates...")
    with open("json/snap.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    dup_label = []
    unique_item = []
    seen = set()
    for item in data:
        label = item.get("index")
        src_url = item.get("src")
        if src_url not in seen:
            unique_item.append(item)
            seen.add(src_url)
        else:
          dup_label.append(label)  
    
    with open("json/snap_dedup.json", "w", encoding="utf-8") as f:
        json.dump(unique_item, f, ensure_ascii=False, indent=2)
    
    print(f"\n😳 {len(dup_label)} data are removed and {len(unique_item)} are remained.")
    
    count = 0
    for fname in os.listdir(img_dir):
        fpath = os.path.join(img_dir, fname)
        match = re.search(r"\d+", fname)    
        if match:
            number = int(match.group()) # extract number only
            if number in dup_label:
                os.remove(fpath)
                count += 1
    
    print(f"\n😊 {count} images are removed.")
            

def main():

    # daily, date, workout, office, campus
    # url_lists = [["https://www.musinsa.com/snap/1334514528790613393", 
    #             "https://www.musinsa.com/snap/1334359719556024342",
    #             "https://www.musinsa.com/snap/1333668164386030866",
    #             "https://www.musinsa.com/snap/1420769922844155383",
    #             "https://www.musinsa.com/snap/1319201691483634299",
    #             "https://www.musinsa.com/snap/1430892659054540629"],
    #              ["https://www.musinsa.com/snap/1419982014799539986",
    #               "https://www.musinsa.com/snap/1417381374114169939",
    #               "https://www.musinsa.com/snap/1417086618578838130",
    #               "https://www.musinsa.com/snap/1413431412467073815",
    #               "https://www.musinsa.com/snap/1417397135591129251",
    #               "https://www.musinsa.com/snap/1417089013420525730",
    #               "https://www.musinsa.com/snap/1415624962822350116"],
    #              ["https://www.musinsa.com/snap/1427545244900966008",
    #               "https://www.musinsa.com/snap/1426042005138247675",
    #               "https://www.musinsa.com/snap/1410477486733280178", 
    #               "https://www.musinsa.com/snap/1329674062781559959",
    #               "https://www.musinsa.com/snap/1326802399413553549",
    #               "https://www.musinsa.com/snap/1325703847138064409",
    #               "https://www.musinsa.com/snap/1325758679303210893"],
    #              ["https://www.musinsa.com/snap/1415271992366132234",
    #               "https://www.musinsa.com/snap/1430838956915478027",
    #               "https://www.musinsa.com/snap/1330734033751089965",
    #               "https://www.musinsa.com/snap/1331145300847735300",
    #               "https://www.musinsa.com/snap/1332232180749187555",
    #               "https://www.musinsa.com/snap/1333701572845438166",
    #               "https://www.musinsa.com/snap/1415275649467868260"]]
    
    # tpo_list = ["데일리", "데이트", "출근", "캠퍼스"] # 테스트 -> 한글로 다시 돌리기

    # num_crawl = [[17, 11, 16, 6, 6, 12], [6, 5, 11, 9, 6, 8, 9], [6, 8, 7, 4, 14, 8, 7], [5, 10, 14, 7, 10, 3, 17]]
    # crawl(url_lists=url_lists, tpo_list=tpo_list, num_crawl=num_crawl)
    remove_duplicates()
    
if __name__ == "__main__":
    main()