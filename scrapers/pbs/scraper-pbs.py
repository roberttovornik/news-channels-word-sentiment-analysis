import csv
import datetime
import os 
import requests
import time
from bs4 import BeautifulSoup


class PBS_SCRAPER():

    def __init__(self, base_url, search_url, search_keywords=[], max_articles=1):
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

        article_limit_reached = False

        for keyword in self.search_keywords:

            page_num = 0
            self.news_articles.append({})

            for i in range(1, 51):
                print("Checking page ", str(i),"...")
                url_search = self.search_url + keyword + "&pnb="+str(i)
                # print("SEARCH URL: ", url_search)
                r = requests.get(url_search)

                soup = BeautifulSoup(r.content, "lxml")
                page_articles_list = soup.find_all("h4", {"class":"search-result__title"})

                if len(page_articles_list) > 0:

                    self.news_pages.append(url_search)

                    for article in page_articles_list:
                        article_link = article.a.get('href')
                        if article_link not in self.news_articles[-1] and article_link not in self.articles_href:
                            self.news_articles[-1][article_link] = self.time_stamp.strftime("%Y-%m-%d %H:%M")
                            self.num_articles += 1
                            self.articles_href.append(article_link)

                        if self.num_articles > self.max_articles:
                            article_limit_reached = True
                            break

                    page_num += 1
                else:
                    break      

                if article_limit_reached:
                    break

                time.sleep(2.5)  

            
            if article_limit_reached:
                break

        print("Search results contained ", page_num, " page(s).")        


    def scrape_news(self):

        for key_i, keyword in enumerate(self.search_keywords):

            if not os.path.exists(keyword):
                os.makedirs(keyword)

            csv_name = "scraped_pbs-"+ keyword + "_news.csv"
            csv_path = os.path.join(keyword, csv_name)

            with open(csv_path,'w') as f1:
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
                    print(article_url)

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
                                # exit(-1)
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
                    article_body = soup.find("article", {"class":"post__article"})

                    if not article_body:
                        self.failed_articles.append(article_url)
                        self.failed_article_body.append(article_body)
                        counter += 1
                        continue

                    if article_body.find("h1", {"class":"post__title"}):
                        headline = article_body.find("h1", {"class":"post__title"}).text
                    if article_body.find("time", {"class":"post__date"}):
                        info = article_body.find("time", {"class":"post__date"}).get("content")
                    if article_body.find("span", {"itemprop":"name"}):
                        author = article_body.find("span", {"itemprop":"name"}).text
                    if article_body.find("article", {"itemprop":"articleBody"}):
                        article_body = article_body.find("article", {"itemprop":"articleBody"})
                        article_text = ""
                        for p in article_body.find_all("p"):
                            article_text += p.text + "\n"

                        article_text = clean_text(article_text)
                        word_count = len(article_text.split())

                    row = [article_url, keyword, word_count, info, author, headline, article_text]
                    writer.writerow(row)
                    print("Keyword: " + keyword + " Writing ", str(counter), " of ", str_num_all, "...")
                    counter += 1

                    time.sleep(2) 

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

    base_url = "https://www.pbs.org"
    search_url = "https://www.pbs.org/newshour/search-results?q="

    pbs_scraper = PBS_SCRAPER(base_url, search_url, ["refugee", "migrant", "asylum seeker"], 10000)
    # pbs_scraper = PBS_SCRAPER(base_url, search_url, ["migrantje"], 10000) # better for testing purpose - single page
    pbs_scraper.check_request_status()
    pbs_scraper.gather_news_links()

    for collection in pbs_scraper.news_articles:
        for k, v in collection.items():
            print("UPDATED: ", v," - ", k)

    pbs_scraper.scrape_news()
    pbs_scraper.report_problems()

if __name__ == "__main__": 
    main()

