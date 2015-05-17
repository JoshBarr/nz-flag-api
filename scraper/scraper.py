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

# Add the parent dir to the path, which is I think what Flask does.
# I'm no python expert but this feels hackish.. is there a better way?
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from api.app import session, engine, Submission, Base, ApiJSONEncoder
from config import BASE_URL, BASE_PATH, STATIC_PATH, IMAGE_PATH


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


def get_submissions():
    submissions_per_page, max_offset, total = get_search_criteria_from_index_page()
    urls = build_urls(submissions_per_page, max_offset)
    # scrape_start_time = datetime.datetime.now()

    for url in urls:
        soup = get_url_as_soup(url)

        for submission in soup.findAll('div', {'class': 'flag'}):
            title = submission.find('span', {'class': 'flag-title'}).getText().strip()
            designer = submission.find('span', {'class': 'flag-submitter'}).getText().strip()
            href = submission.find_all('a')[0]['href']
            submission_id = re.search('\d+', href).group(0)
            scrape_time = datetime.datetime.now()

            existing = session.query(Submission).filter_by(id=submission_id).first()

            # Save ourselves an HTTP requeset or two if we already have this
            # flag stored in the DB
            if (existing):
                print "Already scraped #%s" % submission_id
                continue

            image_node = submission.find('img')
            image_path = save_image(submission_id, image_node)

            tag_arr = []
            tag_match = re.search('tagged with:\s+(.*)$', image_node['alt'])

            if tag_match:
                # Clean up the tagged with and remove the fullstop on the end
                tag_text = tag_match.group(0).replace("tagged with: ", "")[:-1]
                tag_arr = tag_text.split(", ")

            print "Scraped #%s" % (submission_id)

            instance = Submission(
                id=int(submission_id),
                title=title,
                designer=designer,
                url=BASE_URL + href,
                image_path=image_path,
                last_scraped=scrape_time,
                tags=",".join(tag_arr)
            )

            # The item description and some location data is stored on the
            # detail view for each item. So we traverse all those URLs as well.
            get_extended_metadata(instance)
            session.merge(instance)
            session.commit()

    # scrape_end_time = datetime.datetime.now()


def get_extended_metadata(item):
    soup = get_url_as_soup(item.url)
    description_node = soup.find('p', {'class': 'flag-story'})
    designer_node = soup.find('p', {'class': 'designed-by'})
    designer_text = designer_node.getText()
    suggested_by_node = designer_node.findNext('p')
    designer_location = re.search('(from)(?!.*from).+', designer_text).group(0)
    designer_location = designer_location.replace("from ", "")

    # If this node has a class defined, it's probably the flag-story instead.
    # Sorry, this is very very dirty.
    if not hasattr(suggested_by_node, 'class'):
        item.suggested_by = suggested_by_node.find('span', {'class': 'fira-bold'}).getText()

    item.description = description_node.getText().strip()
    item.designer_location = designer_location


def dump_to_json():
    items = session.query(Submission).all()
    json_models = [x.__json__() for x in items]
    print json.dumps(json_models, indent=4, sort_keys=True, separators=(',', ': '),
                     cls=ApiJSONEncoder, ensure_ascii=False).encode('utf-8')


def migrate_from_json(path):
    with open(path, 'r') as infile:
        submissions = json.load(infile)

        for item in submissions:
            t = arrow.get(item['last_scraped'])
            item['last_scraped'] = t.naive
            item = Submission(**item)
            session.merge(item)

    session.commit()
    print "%d submissions merged" % session.query(Submission).count()


def save_image(id, img):
    d = os.path.join(STATIC_PATH, IMAGE_PATH)

    if not os.path.exists(d):
        os.makedirs(d)

    filename = str(id) + '.jpg'
    dest_path = os.path.join(STATIC_PATH, IMAGE_PATH, filename)
    urllib.urlretrieve(BASE_URL + img['src'], dest_path)
    print "Created %s" % dest_path
    return os.path.join(IMAGE_PATH, filename)


def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(engine)
