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

class BBC_UK_SCRAPER():

    def __init__(self, base_url, search_url, driver_path, search_keywords=[], max_articles=1):
        self.url = base_url
        self.search_url = search_url
        self.news_pages = []
        self.news_articles = []
        self.articles_href = []
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

       # setup chromium driver
        driver = webdriver.Chrome(self.web_driver)  

        for keyword in self.search_keywords:

            page_num = 0
            self.news_articles.append({})

            bbc_uk_search_url = self.search_url + keyword
            driver.get(bbc_uk_search_url)
            wait = WebDriverWait(driver, 10)
            time.sleep(3)

            while True:

                time.sleep(1.5)
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")

                if soup.find("nav", {"class":"pagination"}):
                    page_num += 1
                    driver.find_element_by_xpath("""//*[@id="search-content"]/nav[1]/a""").click()

                if soup.find("section", {"id":"search-content"}):   
                    seach_res = soup.find("section", {"id":"search-content"})
                    num_search_res = len(seach_res.find_all("ol", {"class":"search-results results"}))
                    self.news_pages.append(bbc_uk_search_url+"#page="+str(page_num))

                    if num_search_res == (page_num-1):
                        break

                    if len(soup.find_all("h1", {"itemprop":"headline"})) > self.max_articles:
                        break

                else:
                    break

            page_articles_list = soup.find_all("h1", {"itemprop":"headline"})

            for article in page_articles_list:
                article_link = article.a.get('href')
                if article_link not in self.news_articles[-1] and article_link not in self.articles_href:
                    self.news_articles[-1][article_link] = self.time_stamp.strftime("%Y-%m-%d %H:%M")
                    self.num_articles += 1
                    print(article_link)
                    self.articles_href.append(article_link)

                if self.num_articles > self.max_articles:
                    article_limit_reached = True
                    break
            
        print("Search results contained ", page_num, " page(s).")
        print("Search results contained ", self.num_articles, " article(s).")
        driver.quit()


    def scrape_news(self):

              

        for key_i, keyword in enumerate(self.search_keywords):

            csv_dir = os.path.join(keyword)
            
            if not os.path.exists(csv_dir):
                os.makedirs(csv_dir)

            csv_name = "scraped_bbc-uk-" + keyword + "_news.csv"
            csv_path = os.path.join(csv_dir, csv_name)

            with open(csv_path, 'w') as f1:
                writer=csv.writer(f1)
                row = ["href", "keyword", "word_count", "info", "author", "headline", "article_text"]          
                writer.writerow(row)
                counter = 1
                str_num_all = str(len(self.news_articles[key_i]))

                num_skipped = 0

                for news_article in self.news_articles[key_i]:

                    headline = "None"
                    info = "None"
                    author = "None"
                    article_text = "None"
                    word_count = 0              
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
                    article_body = soup.find("div", {"class":"story-body"})

                    if not article_body:
                        self.failed_articles.append(article_url)
                        self.failed_article_body.append(article_body)
                        counter += 1
                        continue

                    if article_body.find("h1", {"class":"story-body__h1"}):
                        headline = article_body.find("h1", {"class":"story-body__h1"}).text
                    if article_body.find("div", {"class":"date"}):
                        info = article_body.find("div", {"class":"date"}).get("data-datetime")
                    if article_body.find("span", {"class":"byline__name"}):
                        author = article_body.find("span", {"class":"byline__name"}).text
                    if article_body.find("div", {"class":"story-body__inner"}):
                        article_text = ""
                        text_body = article_body.find("div", {"class":"story-body__inner"})
                        for p in text_body.find_all("p"):
                            article_text += p.text + "\n"

                        article_text = clean_text(article_text)
                        word_count = len(article_text.split())

                    row = [article_url, keyword, word_count, info, author, headline, article_text]
                    writer.writerow(row)
                    print("Keyword: " + keyword + " Writing ", str(counter), " of ", str_num_all, "...")
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

def clean_text(article):
    paragraphs = article.split("\n")    
    paragraphs = [ ' '.join(x.split()) for x in paragraphs if len(x.strip()) > 0]

    return '\n'.join(paragraphs)

def main():


    base_url = "https://www.bbc.co.uk/"
    search_url = "https://www.bbc.co.uk/search?filter=news&q="
    web_driver_path = "/usr/lib/chromium-browser/chromedriver"

    bbc_uk_scraper = BBC_UK_SCRAPER(base_url, search_url, web_driver_path, ["refugee", "migrant", "asylum seeker"], 10000)
    
    bbc_uk_scraper.check_request_status()
    bbc_uk_scraper.gather_news_links()

    
    for colleciton in bbc_uk_scraper.news_articles:
        for k, v in colleciton.items():
            print("UPDATED: ", v," - ", k)

    print(" FOUND ", bbc_uk_scraper.num_articles, " articles.")
    # exit()
    bbc_uk_scraper.scrape_news()
    bbc_uk_scraper.report_problems()

if __name__ == "__main__": 
    main()

