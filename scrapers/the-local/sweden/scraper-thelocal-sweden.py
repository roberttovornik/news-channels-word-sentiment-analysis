import csv
import datetime 
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class THE_LOCAL_SCRAPER():

    def __init__(self, base_url, search_url, driver_path, search_keywords=[], max_articles=1):
        self.url = base_url
        self.search_url = search_url
        self.news_pages = []
        self.news_articles = {}
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
        
        # elimintate inital connection popup
        driver.get(self.url)
        time.sleep(5) # let the page load
        driver.find_element_by_xpath("""/html/body/div[7]/div[1]/div[2]/div/span""").click()

        # initiate search

        article_limit_reached = False

        for keyword in self.search_keywords:

            page_num = 0

            thelocal_search_url = self.search_url + keyword
            driver.get(thelocal_search_url)
            wait = WebDriverWait(driver, 10)
            time.sleep(3)

            for i in range(1, 11):
                
                time.sleep(2)
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")
                page_articles_list = soup.find_all("a", {"class":"gs-title"}, href=True)
                print("PAGE ", i)
                if len(page_articles_list) > 0:

                    self.news_pages.append(thelocal_search_url+"-page-"+str(i))

                    for article in page_articles_list:
                        article_link = article.get('href')
                        if article_link not in self.news_articles:
                            self.news_articles[article_link] = self.time_stamp.strftime("%Y-%m-%d %H:%M")
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

                if i < 10:
                    driver.find_element_by_xpath("""//*[@id="___gcse_0"]/div/div/div/div[5]/div[2]/div/div/div[2]/div[11]/div/div["""+str(i+1)+"""]""").click()
                    time.sleep(2)
            
            if article_limit_reached:
                break
        print("Search results contained ", page_num, " page(s).")
        driver.quit()


    def scrape_news(self):

        with open('scraped_thelocal-sweden_news.csv','w') as f1:
            writer=csv.writer(f1)
            row = ["source", "info", "author", "headline", "article_text"]          
            writer.writerow(row)
            counter = 1
            str_num_all = str(len(self.news_articles))

            num_skipped = 0

            for news_article in self.news_articles:

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
                article_body = soup.find("div", {"id":"article-inner"})

                if not article_body:
                    self.failed_articles.append(article_url)
                    self.failed_article_body.append(article_body)
                    counter += 1
                    continue

                if article_body.h1:
                    headline = article_body.h1.text
                if article_body.find("div", {"class":"article-date"}) and article_body.find("div", {"class":"article-time"}):
                    info = article_body.find("div", {"class":"article-date"}).text + " " + article_body.find("div", {"class":"article-time"}).text
                if article_body.find("div", {"class":"article-author-name"}):
                    author = article_body.find("div", {"class":"article-author-name"}).text
                if article_body.find("div", {"id":"article-description"}) and article_body.find("div", {"id":"article-body"}):
                    article_text = article_body.find("div", {"id":"article-description"}).text + "\n" + article_body.find("div", {"id":"article-body"}).text

                row = [article_url, info, author, headline, article_text]
                writer.writerow(row)
                print("Writing ", str(counter), " of ", str_num_all, "...")
                counter += 1
                time.sleep(.500) 

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

    base_url = "https://www.thelocal.se"
    search_url = "https://www.thelocal.se/search/?q="
    web_driver_path = "/usr/lib/chromium-browser/chromedriver"

    the_local_scraper = THE_LOCAL_SCRAPER(base_url, search_url, web_driver_path, ["migrants"], 100000)
    
    the_local_scraper.check_request_status()
    the_local_scraper.gather_news_links()

    for k, v in the_local_scraper.news_articles.items():
        print("UPDATED: ", v," - ", k)

    print("FOUND ", the_local_scraper.num_articles, " articles.")
    # exit()
    the_local_scraper.scrape_news()
    the_local_scraper.report_problems()

if __name__ == "__main__": 
    main()

