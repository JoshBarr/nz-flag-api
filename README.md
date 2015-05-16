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

## Running the app

First, you'll need to populate the DB. The scraper has to traverse every
submission on the first run. At the time of writing, there's about 850 of them,
so it takes a while.

Subsequent scrapes are much faster, since it traverses the listing pages first,
to harvest new submissions.

```shell
npm run quickstart
```

You can then get all the flag submissions by visiting the API in your browser
```
http://localhost:3000/api/
```

You can also get individual submissions by passing an ID:

```
http://localhost:3000/api/610
```

## API example

```json

{
  "description": "Bird accualy is kiwi. Is well known icon of our country and people. Also stars are southern cross and blue is pacific ocean. Where we're from and how we got here.",
  "designer": "Aku A.",
  "designer_location": "Waikato",
  "id": 4338,
  "image_path": "http://localhost:3000/static/submissions/4338.jpg",
  "last_scraped": "2015-05-16T15:45:03.146103+00:00",
  "suggested_by": null,
  "suggested_by_location": null,
  "tags": [
    "blue",
    "red",
    "white",
    "kiwi",
    "Southern Cross",
    "history",
    "Kiwiana",
    "Ocean",
    "brown"
  ],
  "title": "Southern Kiwi",
  "url": "https://www.govt.nz/browse/engaging-with-government/the-nz-flag-your-chance-to-decide/gallery/design/4338"
}
```

## Images

Image of flag submissions are saved via `urllib` to the `static/submissions`
directory. You should configure your wSGI app to serve these directly.


## Command reference

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
* Move the static assets to a CDN


