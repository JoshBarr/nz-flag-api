import sys
import os
from scraper import FlagScraper

def cli_help():
    print "CLI options:"
    print "\tscrape\t\tScrape the live site and generate a DB"
    print "\tmigrate [PATH] \tPulls in a json file and migrates it into the DB"
    print "\tdump > [PATH] \tDumps the DB as JSON to stdout. Redirect it to your file."
    print "\tdrop\t\tDrops the database tables and rebuilds them"
    exit()


if __name__ == '__main__':

    scraper = FlagScraper()
    if len(sys.argv) < 2:
        cli_help()

    if sys.argv[1] == 'dump':
        scraper.dump_to_json()

    elif sys.argv[1] == 'migrate':
        if not sys.argv[2]:
            print "Please specify a json file to read in."
            exit()
        if not os.path.exists(sys.argv[2]):
            print "Make sure the path exists"
            exit()

        scraper.migrate_from_json(sys.argv[2])

    elif sys.argv[1] == 'scrape':
        try:
            scraper.get_submissions()
        except KeyboardInterrupt:
            print "Stopping %d workers" % scraper.activeThreads
            os._exit(0)

    elif sys.argv[1] == 'drop':
        scraper.reset_db()

    else:
        cli_help()
