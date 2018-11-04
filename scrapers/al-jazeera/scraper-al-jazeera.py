import csv
import datetime
import os 
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AL_JAZEERA_SCRAPER():

    def __init__(self, base_url, search_url, driver_path, search_keywords=[], max_articles=1):
        self.url = base_url
        self.search_url = search_url
        self.news_pages = []
        self.news_articles = []
        self.search_keywords = search_keywords
        self.max_articles = max_articles
        self.num_articles = 0
        self.time_stamp = datetime.datetime.now()
        # certain pages specific - requires User-Agent defintion to allow scraping
        self.headers = requests.utils.default_headers()
        self.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
        })

        self.failed_articles = []
        self.failed_article_body = []

        # selenium requirement
        self.web_driver = driver_path

    def check_request_status(self):
        """ Connection test method. Sends request to the server, expecting a success message 200 on return.

        Returns True on success.
        """
        if requests.get(self.url, headers=self.headers).status_code == 200:
            print("Request successful. Connection established.")
            return True
        else:
            print("Request failed.")
            return False

    def gather_news_links(self):

        # chrome_options = Options()
        # chrome_options.add_argument("--kiosk")
        # driver = webdriver.Chrome(self.web_driver, chrome_options=chrome_options)

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(self.web_driver, chrome_options=options)

        article_limit_reached = False

        for keyword in self.search_keywords:

            page_num = 0
            self.news_articles.append({})

            al_jazeera_search_url = self.search_url + keyword
            driver.get(al_jazeera_search_url)
            wait = WebDriverWait(driver, 5)

            # eliminates cookies notification
            html = driver.page_source
            soup = BeautifulSoup(html, "lxml")

            if soup.find("div", {"id":"ensNotifyBanner"}):
                driver.find_element_by_id("ensCloseBanner").click()

            time.sleep(1)
            # time.sleep(3)
            # search bar selection
            driver.find_element_by_xpath("""//*[@id="search"]/div/div/div[1]/div/div/div[4]/div[6]/label/input""").click() # mark news only
            wait = WebDriverWait(driver, 5)
            print("just clicked")
            time.sleep(5)

            while True:

                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")
                page_articles_list = soup.find_all("a", {"ctype":"c"}, href=True)
                print("PAGE ", page_num)

                if len(page_articles_list) > 0:

                    self.news_pages.append(al_jazeera_search_url+"-page-"+str(page_num))

                    for article in page_articles_list:
                        article_link = article.get('href')
                        if article_link not in self.news_articles[-1]:
                            self.news_articles[-1][article_link] = self.time_stamp.strftime("%Y-%m-%d %H:%M")
                            self.num_articles += 1
                            print(article_link)

                        if self.num_articles > self.max_articles:
                            article_limit_reached = True
                            break

                    page_num += 1
                else:
                    break      

                if article_limit_reached:
                    break
                    
                if soup.find("span", {"class":"next-pagination"}):
                    driver.find_element_by_class_name("next-pagination").click()
                else:
                    break

                time.sleep(3)

        print("Search results contained ", page_num, " page(s).")
        driver.quit()


    def scrape_news(self):

              

        for key_i, keyword in enumerate(self.search_keywords):

            csv_dir = os.path.join(keyword)
            
            if not os.path.exists(csv_dir):
                os.makedirs(csv_dir)

            csv_name = "scraped_al-jazeera-" + keyword + "_news.csv"
            csv_path = os.path.join(csv_dir, csv_name)

            with open(csv_path, 'w') as f1:
                writer=csv.writer(f1)
                row = ["href", "keyword", "info", "author", "headline", "article_text"]          
                writer.writerow(row)
                counter = 1
                str_num_all = str(len(self.news_articles[key_i]))

                num_skipped = 0

                for news_article in self.news_articles[key_i]:

                    headline = "None"
                    info = "None"
                    author = "None"
                    article_text = "None"              
                    article_url = news_article
                    print("Article: ", article_url)

                    r = None
                    num_reconnect = 0
                    skip_article = False

                    while r is None:
                        try:
                            r = requests.get(article_url)
                        except:
                            print("Connection refused by the server..")
                            print("Sleep for 10 seconds")
                            time.sleep(10)
                            print("Reconnecting..")
                            num_reconnect += 1
                            if num_reconnect > 10:
                                print("SERVER IS REFUSING CONNECTION AT THIS TIME, TRY SKIPPING ARTICLE.")
                                skip_article = True
                                num_skipped += 1
                                break
                            continue

                    if num_skipped > 10:
                        print("SERVER IS REFUSING CONNECTION AT THIS TIME, TRY AGAIN LATER.")
                        exit(-1)
                    if skip_article:
                        continue

                    soup = BeautifulSoup(r.content, "lxml")
                    article_body = soup.find("section", {"id":"article-page"})

                    if not article_body:
                        self.failed_articles.append(article_url)
                        self.failed_article_body.append(article_body)
                        counter += 1
                        continue

                    if article_body.find("h1", {"class":"post-title"}):
                        headline = article_body.find("h1", {"class":"post-title"}).text
                    if article_body.find("time", {"class":"timeagofunction"}):
                        info = article_body.find("time", {"class":"timeagofunction"}).get("datetime")
                    if article_body.find("a", {"rel":"author"}):
                        author = article_body.find("a", {"rel":"author"}).text
                    if article_body.find("div", {"class":"main-article-body"}):
                        article_text = ""
                        text_body = article_body.find("div", {"class":"main-article-body"})
                        for p in text_body.find_all("p"):
                            article_text += p.text + "\n"

                    row = [article_url, keyword, info, author, headline, article_text]
                    writer.writerow(row)
                    print("Writing ", str(counter), " of ", str_num_all, "...")
                    counter += 1
                    time.sleep(1)

    def report_problems(self):

        if len(self.failed_articles) == 0:
            print(" PASSED WITHOUT PROBLEMS ")
        else:
            print("Exceptions found")
            print("REPORTING DIAGNOSTICS")
            for i in range(len(self.failed_articles)):
                print(" FAILED LINK: ", self.failed_articles[i])
                print(self.failed_article_body[i])
                print("==========================================")
                print()

def main():


    base_url = "https://www.aljazeera.com"
    search_url = "https://www.aljazeera.com/Search/?q="
    web_driver_path = "/usr/lib/chromium-browser/chromedriver"

    the_local_scraper = AL_JAZEERA_SCRAPER(base_url, search_url, web_driver_path, ["refugee"], 1000)
    
    the_local_scraper.check_request_status()
    the_local_scraper.gather_news_links()

    
    for colleciton in the_local_scraper.news_articles:
        for k, v in colleciton.items():
            print("UPDATED: ", v," - ", k)

    print(" FOUND ", the_local_scraper.num_articles, " articles.")
    # exit()
    the_local_scraper.scrape_news()
    the_local_scraper.report_problems()

if __name__ == "__main__": 
    main()

