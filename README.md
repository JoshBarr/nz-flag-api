[ ![Codeship Status for JoshBarr/nz-flag-api](https://codeship.com/projects/4a698e60-7754-0132-4dc3-26527322a871/status?branch=master)](https://codeship.com/projects/55433)

# NZ Flag Consideration Project API

Lots of people have been asking for a way to get the NZ Govt Flags out of the
govt.nz site in a machine parsable format.

### [See it in action](http://flag.joshbarr.com/api/)

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
python scraper scrape     # This will take a while
python api                # API on port 5000 for you
```

You can then get all the flag submissions by visiting the API in your browser
```
http://localhost:5000/api/
```

You can also get individual submissions by passing an ID:

```
http://localhost:5000/api/610
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
directory. You should configure your wsgi app to serve these directly.


## Command reference

```
python api                  # runs the Flask API app on port 5000
python scraper scrape       # scrapes the govt.nz site for flags
python scraper              # List all available commands
```

### package.json
```shell
npm start           # runs the dev server on port 5000
npm run scrape      # scrapes the govt.nz site for flags
npm run dump        # dumps the results out as JSON `var/submissions.json`
npm run migrate     # populate the DB from JSON file `var/submissions.json`
npm run drop        # drops the table
npm run cron        # scheduled task to scrape the govt site every hour
```


## Deployment

### Set up a wsgi script to run the Flask app

Example wsgi script:
```python
import sys
import os
sys.path.insert(1, os.path.join(sys.path[0], '.'))

from api.app import app as application

```

### Env config

drop an `env.py` in the root of your project to override any configuration
options from `config.py`.

### Run the node cron task

To make sure you've got the freshest, juiciest flags, run this task to scrape
the site every couple of hours.

```
npm run cron
```

## Todo:
* Write better docs
* Add some caching
* Move the static assets to a CDN


