# NZ Flag Consideration Project API

This isn't an API quite yet. But it will be. Right now, it sucks the submission
metadata down into a SQLite DB. It also allows you to cache the scraped data in a
JSON file so you don't have to hit the server while developing the tool

## Todo:
* Create methods for scraping individual submissions to get the image/description
* Implement an HTTP endpoint for querying the db from your web service
* Schedule the scraper to run every so often
* Make migration non-destructive (it's a drop_all and reload right now)
* Write docs
* Host it somewhere


## Getting started

```shell
pip install -r requirements.txt
python ./scrape.py fetch
```
The fetch command is also aliased to `npm start` if you use node-based tooling.