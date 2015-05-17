import scraper
import sys
import os


def cli_help():
    print "CLI options:"
    print "\scrape\t\tScrape the live site and generate a DB"
    print "\tmigrate [PATH] Pulls in a json file and migrates it into the DB"
    print "\tdump > [PATH] \t\tDumps the DB as JSON to stout. Redirect it to your file."
    print "\tdrop\t\tDrops the database tables and rebuilds them"
    exit()


if __name__ == '__main__':

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
        scraper.get_submissions()

    elif sys.argv[1] == 'drop':
        scraper.reset_db()

    else:
        cli_help()
