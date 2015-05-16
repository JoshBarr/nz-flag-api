# NZ Flag Consideration Project API

Lots of people have been asking for a way to get the NZ Govt Flags out of the
govt.nz site in a machine parsable format.

This is an extension of @fogonwater's
[getflags](https://github.com/fogonwater/getflags) tool. It uses BeautifulSoup
to get the images and metadata of the flag submissions, and store them in a
SQLite DB.

It then serves them up over a JSON API via a tiny Flask application.


## Requirements

Assumes you have:
* python
* setuptools/pip
* nodejs

All the lifecycle commands are in the `package.json`

## Installation

```shell
npm install
```

## Running commands

```shell
npm start           # runs the dev server on port 3000 (change it in config.py)
npm run scrape      # scrapes the govt.nz site for flags
npm run dump        # dumps the results out as JSON `var/submissions.json`
npm run migrate     # populate the DB from JSON file `var/submissions.json`
npm run drop        # drops the table
npm run cron        # scheduled task to scrape the govt site every hour
```

## Deployment

* Set up a uWSGI script to run the Flask app with nginx
* Run the cron task to populate the DB and scrape the live site for new submissions every hour

```
npm run cron
```

## Todo:
* Write better docs
* Host it somewhere


