"""
Huge thanks to https://github.com/fogonwater/getflags
"""

from bs4 import BeautifulSoup
import urllib
import urllib2
import re
import datetime
import json
import sys
import os
import arrow
from threading import Thread
from time import sleep

from sqlalchemy.orm import sessionmaker, scoped_session


# Add the parent dir to the path, which is I think what Flask does.
# I'm no python expert but this feels hackish.. is there a better way?
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from api.app import engine, Submission, Tag, Designer, Location, Base, ApiJSONEncoder
from config import BASE_URL, BASE_PATH, STATIC_PATH, IMAGE_PATH

Session = scoped_session(sessionmaker(bind=engine,
                         autocommit=False,
                         autoflush=False))


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance



class FlagScraper():

    def __init__(self):
        self.urls = []
        self.dbStack = []
        self.threads = []
        self.maxThreads = 20

        self.activeThreads = 0
        self.done = False

    def get_submissions_per_page(self, soup):
        submissions = soup.findAll('div', {'class': 'flag'})
        return len(submissions)

    def get_maximum_offset(self, soup):
        pagination_last = soup.find('a', {'aria-label': 'Last'})
        max_offset = 0

        try:
            href = pagination_last['href']

            try:
                max_offset = re.search('\d+', href).group(0)
            except AttributeError:
                print "Couldn't determine maximum offset"
                exit()

        except KeyError:
            print 'Couldn\'t find an <a aria-label="last"> in the DOM'
            exit()

        return int(max_offset)

    def get_url_as_soup(self, url):
        print "Scraping from %s" % url
        html = urllib2.urlopen(url)
        soup = BeautifulSoup(html)
        return soup

    def get_total_submissions(self, soup):
        """
        Returns the total number of submissions listed in the <h2> element.
        """
        total_text = soup.find('h2', {'class': 'gallery-count'}).getText()
        return int(re.search('\d+', total_text).group(0))

    def get_search_criteria_from_index_page(self):
        soup = self.get_url_as_soup(BASE_URL + BASE_PATH)

        return (
            self.get_submissions_per_page(soup),
            self.get_maximum_offset(soup),
            self.get_total_submissions(soup)
        )

    def build_urls(self, submissions_per_page, max_offset):
        urls = []
        num_pages = max_offset / submissions_per_page + 1

        for i in range(0, num_pages):
            urls.append({"type": "index", "url": BASE_URL + BASE_PATH + "?start=%s" % (i * submissions_per_page)})

        print "Flags per page\t\t%d" % submissions_per_page
        print "Last page offset\t%d" % max_offset
        print "Total pages to scrape\t%d" % len(urls)

        return urls

    # Execute scraper after adding urks
    def run(self, _callFinal):
        if len(self.urls) > 0:
            print("Starting threaded scraping for " + str(len(self.urls)) + "...")
            self.start_scrapeThreads(_callFinal)

        else:
            print("No urls to scrape")

    # Starting point for new thread workers
    def start_scrapeThreads(self, _finalFunc):
        if len(self.urls) == 0:
            self.checkAllThreadsHaveRun(_finalFunc)

        elif self.activeThreads >= self.maxThreads:
            sleep(1)
            self.start_scrapeThreads(_finalFunc)

        else:
            self.activeThreads += 1
            _item = self.urls.pop()

            print("Thread created from url pool (" + str(len(self.urls)) + ") for url: " + _item["url"])

            thread = Thread( target=self.run_scrapeThread, args=(_item, _finalFunc))
            thread.start()

            self.threads.append(thread)

            if self.activeThreads < self.maxThreads:
                self.start_scrapeThreads(_finalFunc)

    # Method run from with newly started thread
    def run_scrapeThread(self, _item, _finalFunc):
        try:
            if (_item["type"] == "index"):
                self.process_url_content(_item["url"], _finalFunc)
            elif (_item["type"] == "extended"):
                self.get_extended_metadata(_item)
        except:
            pass

        self.activeThreads -= 1
        self.start_scrapeThreads(_finalFunc)


    # Finish scraper if no more url's are left in the list
    def checkAllThreadsHaveRun(self, _finalFunc):
        if len(self.urls) == 0 and self.activeThreads <= 0:
            _finalFunc()
        else:
            print("Waiting for " + str(self.activeThreads) + " threads to finish operations...")

    def get_submissions(self):
        submissions_per_page, max_offset, total = self.get_search_criteria_from_index_page()
        self.urls = self.build_urls(submissions_per_page, max_offset)

        self.run(self.finished_scraping)

        while (self.activeThreads > 0 and self.done == False):
            sleep(1)

    def finished_scraping(self):
        self.done = True
        print "Done"

    def process_url_content(self, url, _finalFunc):

        soup = self.get_url_as_soup(url)

        for submission in soup.findAll('div', {'class': 'flag'}):
            title = submission.find('span', {'class': 'flag-title'}).getText().strip()
            designer = submission.find('span', {'class': 'flag-submitter'}).getText().strip()
            href = submission.find_all('a')[0]['href']
            submission_id = re.search('\d+', href).group(0)

            # print "Adding #%s to scrape list." % submission_id
            self.urls.append({"type": "extended",
                              "id": submission_id,
                              "url": BASE_URL + href,
                              "title": title,
                              "designer": designer})

    def get_extended_metadata(self, _item):
        print ""
        print "Fetching extended data for %s" % _item['id']
        soup = self.get_url_as_soup(_item["url"])

        href = _item["url"]
        submission_id = int(_item["id"])
        scrape_time = datetime.datetime.now()

        session = Session()

        image_container = soup.find('div', {'class': 'flag-suggestion-img'})
        detail_container = soup.find('div', {'class': 'flag-suggestion-detail'})
        image_node = image_container.findNext('img')
        image_path = self.save_image(submission_id, image_node)

        tag_arr = []
        tag_match = re.search('tagged with:\s+(.*)$', image_node['alt'])

        if tag_match:
            # Clean up the tagged with and remove the fullstop on the end
            tag_text = tag_match.group(0).replace("tagged with: ", "")[:-1]
            tag_arr = tag_text.split(", ")

        description_node = soup.find('p', {'class': 'flag-story'})
        designer_node = soup.find('p', {'class': 'designed-by'})
        designer_text = designer_node.getText()

        designer_location = re.search('(from)(?!.*from).+',designer_text).group(0).replace("from ", "")
        location_name = designer_location.strip()
        suggested_by = detail_container.find('span', {'class': 'fira-bold'})
        suggested_by_location = ''
        suggested_by_text = ''

        if suggested_by:
            suggested_by_text = suggested_by.getText().strip()

        suggested_by_node = detail_container.find('p', {'class': None})

        if suggested_by_node:
            suggested_by_location = re.search('(from)(?!.*from).+', suggested_by_node.getText()).group(0)
            if suggested_by_location:
                suggested_by_location = suggested_by_location.replace("from ", "")


        print "CREATING SUBMISSION ID %s %s %s" % (submission_id, suggested_by_text, suggested_by_location)
        designer = get_or_create(session, Designer, name=_item["designer"])

        location = get_or_create(session, Location, name=location_name)

        designer.location = location
        session.merge(designer)
        session.merge(location)
        session.commit()
        print "CREATED DESIGNER FOR %s" % submission_id
        tag_models = []
        if len(tag_arr) > 0:
            for tag in tag_arr:
                tag_models.append(get_or_create(session, Tag, name=tag.strip()))


        # print tag_models

        try:
            instance = get_or_create(session, Submission,
                id=int(submission_id),
                title=_item["title"],
                description=description_node.getText().strip(),
                url=href,
                image_path=image_path,
                # last_scraped=scrape_time
            )

            instance.designer = designer
            instance.tags = tag_models
            instance.last_scraped = scrape_time
            instance.suggested_by = suggested_by_text
            instance.suggested_by_location = suggested_by_location

            session.merge(instance)
            session.commit()
            Session.remove()

        except Exception, err:
            print Exception, err

        print "Content scraped for #%s" % submission_id

    def dump_to_json(self):
        items = session.query(Submission).all()
        json_models = [x.__json__() for x in items]
        print json.dumps(json_models, indent=4, sort_keys=True, separators=(',', ': '),
                         cls=ApiJSONEncoder, ensure_ascii=False).encode('utf-8')

    def migrate_from_json(self, path):
        with open(path, 'r') as infile:
            submissions = json.load(infile)

            for item in submissions:
                t = arrow.get(item['last_scraped'])
                item['last_scraped'] = t.naive
                item = Submission(**item)
                session.merge(item)

        session.commit()
        print "%d submissions merged" % session.query(Submission).count()

    def save_image(self, id, img):
        d = os.path.join(STATIC_PATH, IMAGE_PATH)

        if not os.path.exists(d):
            os.makedirs(d)

        filename = str(id) + '.jpg'
        dest_path = os.path.join(STATIC_PATH, IMAGE_PATH, filename)
        urllib.urlretrieve(BASE_URL + img['src'], dest_path)
        print "Created %s" % dest_path
        return os.path.join(IMAGE_PATH, filename)

    def reset_db(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(engine)
