"""
Huge thanks to https://github.com/fogonwater/getflags
"""

from bs4 import BeautifulSoup
import urllib
import urllib2
import re
import time
import datetime
import json
import sqlalchemy as sql
import sys

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import sessionmaker


BASE_URL = 'https://www.govt.nz'
BASE_PATH = '/browse/engaging-with-government/the-nz-flag-your-chance-to-decide/\
gallery/'
JSON_FILE = 'var/scrape.json'

Base = declarative_base()


class Submission(Base):
    __tablename__ = 'submissions'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    designer = Column(String)
    url = Column(String)
    thumbnail = Column(String)
    last_scraped = Column(Date)

    def __repr__(self):
        return "<Submission(id='%s', designer='%s', title='%s')>" % (
                             self.id, self.designer, self.title)



def get_submissions_per_page(soup):
    submissions = soup.findAll('div', {'class': 'flag'})
    return len(submissions)


def get_maximum_offset(soup):
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


def get_url_as_soup(url):
    print "Scraping from %s" % url
    html = urllib2.urlopen(url)
    soup = BeautifulSoup(html)
    return soup


def get_total_submissions(soup):
    """
    Returns the total number of submissions listed in the <h2> element.
    """
    total_text = soup.find('h2', {'class': 'gallery-count'}).getText()
    return int(re.search('\d+', total_text).group(0))


def get_search_criteria_from_index_page():
    soup = get_url_as_soup(BASE_URL + BASE_PATH)

    return (
        get_submissions_per_page(soup),
        get_maximum_offset(soup),
        get_total_submissions(soup)
    )


def build_urls(submissions_per_page, max_offset):
    urls = []
    num_pages = max_offset / submissions_per_page + 1

    for i in range(0, num_pages):
        urls.append(BASE_URL + BASE_PATH + "?start=%s" % (i * submissions_per_page))

    print "Flags per page\t\t%d" % submissions_per_page
    print "Last page offset\t%d" % max_offset
    print "Total pages to scrape\t%d" % len(urls)

    return urls


def get_submission_listings():
    submissions_per_page, max_offset, total = get_search_criteria_from_index_page()
    urls = build_urls(submissions_per_page, max_offset)

    submissions = []
    scrape_start_time = time.strftime("%c")

    for url in urls:
        soup = get_url_as_soup(url)

        for submission in soup.findAll('div', {'class': 'flag'}):
            title = submission.find('span', {'class': 'flag-title'}).getText().strip()
            designer = submission.find('span', {'class': 'flag-submitter'}).getText().strip()
            href = submission.find_all('a')[0]['href']
            thumbnail = submission.find('img')['src']
            scrape_time = time.strftime("%c")
            submission_id = re.search('\d+', href).group(0)

            print  "%s\t%s\t%s" % (submission_id, designer, title)

            submissions.append({
                'id': submission_id,
                'title': title,
                'designer': designer,
                'url': BASE_URL + href,
                'thumbnail': thumbnail,
                'scrape_time': scrape_time
            })

    scrape_end_time = time.strftime("%c")

    return {
        'meta': {
            'scrape_start_time': scrape_start_time,
            'scrape_end_time': scrape_end_time,
            'submissions_per_page': submissions_per_page,
            'max_offset': max_offset,
            'total_stated_submissions': total,
            'total_scraped_submissions': len(submissions),
            'urls': urls
        },
        'submissions': submissions
    }


def save_submission_data(path, data):
    with open(path, 'w') as outfile:
        json_gunn = json.dumps(data, indent=4, sort_keys=True, separators=(',', ': '))
        outfile.write(json_gunn.encode('utf-8'))


def cli_help():
    print "CLI options:"
    print "\tfetch\t\tScrape the live site and generate a DB"
    print "\tmigrate\t\tMake an SQLITE db from submissions"
    print "\tcache\t\tScrape the live site into a JSON file"
    print "\timages\t\tRetrieve images for submissions"
    exit()


def migrate(engine, Session, data):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(engine)

    session = Session()

    for item in data['submissions']:
        session.add(Submission(
            id=item['id'],
            title=item['title'],
            designer=item['designer'],
            url=item['url'],
            thumbnail=item['thumbnail'],
            last_scraped=datetime.datetime.strptime(item['scrape_time'], '%c')
        ))

    session.commit()
    print "Migrated %d submissions" % len(data['submissions'])


def main():
    data = {}
    engine = sql.create_engine('sqlite:///var/submissions.sqlite', echo=False)
    Session = sessionmaker(bind=engine)

    if len(sys.argv) < 2:
        cli_help()

    if sys.argv[1] == 'migrate':
        with open(JSON_FILE) as json_data:
            data = json.load(json_data)
            migrate(engine, Session, data)

    elif sys.argv[1] == 'cache':
        data = get_submission_listings()
        save_submission_data(JSON_FILE, data)
        print "Saved submissions into %s. Run the 'migrate' command to add to the DB " % JSON_FILE

    elif sys.argv[1] == 'fetch':
        data = get_submission_listings()
        save_submission_data(JSON_FILE, data)
        migrate(engine, Session, data)

    elif sys.argv[1] == 'details':
        print "TODO... iterate over all the submissions and get the image/description"
        # start = 1
        # img_num = 1
        # while start < NUM_FLAGS:
        #     url = BASE_URL + img_path + str(start)
        #     html = urllib2.urlopen(url)
        #     soup = BeautifulSoup(html)

        #     for img in soup.findAll('img'):
        #         img_url = img['src']
        #         if not 'flags-designs' in img_url:
        #             continue
        #         dst_name = 'img/' + str(img_num) + img_url[-4:]
        #         # just awful
        #         dst_name = dst_name.lower()
        #         dst_name = dst_name.replace('jpeg', '.jpg')
        #         urllib.urlretrieve(BASE_URL + img_url, dst_name)
        #         print dst_name, 'created.'
        #         img_num += 1

        #     # increment by number of imgs in visible gallery
        #     start += 9

    elif sys.argv[1] == 'list':
        session = Session()
        for id, url, designer, title in session.query(Submission.id, Submission.url, Submission.designer, Submission.title).group_by(Submission.designer):
            print id, '\t', designer, '\t', title, '\t\t\t'

    else:
        print "Oops. Argument '%s' not found" % sys.argv[1]
        cli_help()



if __name__ == '__main__':
    main()
