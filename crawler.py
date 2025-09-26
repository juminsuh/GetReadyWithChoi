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

def crawl_with_scroll(target_count=10, json_dir="json", img_dir="images"):
    
    # create directories
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)

    # open chrome browser
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)

    hashtag_pattern = r'#[^\s#]+'
    results = []

    try:
        url = "https://www.musinsa.com/snap/1341301737858921303" # snap url
        driver.get(url)

        # wait until "virtuoso-item-list" be found
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'div[data-testid="virtuoso-item-list"]')
        ))

        for i in range(1, target_count+1):
            print(f"\n👉 {i}번째 아이템 처리 중...")

            # find the container which includes "virtuoso-item-list"
            container = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="virtuoso-item-list"]')
            # make item selector which indicates each item
            item_selector = f'div[data-testid="virtuoso-item-list"] div[data-index="{i}"]'
            
            try:
                # find i-th item if the item is shown at the screen
                item = driver.find_element(By.CSS_SELECTOR, item_selector)
                print(f"📌 Try occurs")
            except:
                # i-th item not found, scroll a little bit so that i-th item be loaded at the screen
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", container)
                time.sleep(0.5)
                print(f"‼️ Exception occurs")
            print(f"    😊 item {i} is found at the screen.")

            # place i-th item to the center in order to be shown at the center of the screen
            driver.execute_script(
                "document.querySelector(arguments[0]).scrollIntoView({block:'center'});",
                item_selector
            )
            time.sleep(0.8) 
            print(f"    🥳 item {i} is shown at the center of the scree.")
            
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
            alt_text = img.get_attribute("alt") or ""
            src_url  = img.get_attribute("src") or ""
            
            # extract hashtags and description of snap image
            hashtags = re.findall(hashtag_pattern, alt_text)
            hashtags = [tag[1:] for tag in hashtags]
            season = ['가을', '겨울']
            style = re.compile(f'(캐주얼|미니멀|스포티|클래식|워크웨어|고프코어|프레피|에스닉|스트릿|걸리시|로맨틱|시크|시티보이|레트로|리조트)')
            TPO = re.compile(f'(데일리|캠퍼스|대학생|바다/수영|러닝|결혼식|요가/필라테스|데이트|출근|등산/아웃도어|페스티벌|피트니스|골프)')
            filtered_hashtags = []
            for tag in hashtags:
                if tag in season:
                    filtered_hashtags.append(tag)
                style_tag = style.search(tag)
                TPO_tag = TPO.search(tag)
                if style_tag:
                    filtered_hashtags.append(style_tag.group(1))
                if TPO_tag:
                    filtered_hashtags.append(TPO_tag.group(1))
            
            set_hashtags = list(set(filtered_hashtags))      
            print(f"    🧩 hashtags: {set_hashtags}")
            
            description = re.sub(hashtag_pattern, '', alt_text)
            description = ' '.join(description.split())
            print(f"    📄 description: {description}")

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

                    fname = os.path.join(img_dir, f"snap_{i}{ext}")
                    with open(fname, "wb") as f:
                        f.write(resp.content)
                    print(f"   💾 이미지 저장: {fname}")
                else:
                    print(f"   ❌ 이미지 다운로드 실패: {resp.status_code}")
                    
            results.append(
                {"index": i, 
                 "description": description, 
                 "tags": set_hashtags, 
                 "src": src_url}
            )

            # scroll for 800 pixels down
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(1.5)
            
        json_path = os.path.join(json_dir, "snap.json")
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return results

    finally:
        driver.quit()

def main():
    crawl_with_scroll()
    
if __name__ == "__main__":
    main()