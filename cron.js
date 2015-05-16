var schedule = require('node-schedule');
var spawn = require('child_process').spawn;


function scrapeGovtNZSite() {
    console.log('Starting scrape', Date.now());
    var child = spawn('python', ['scraper', 'scrape'], {stdio: "inherit"});
}

var j = schedule.scheduleJob('* 1 * * *', function(){
    scrapeGovtNZSite()
});

scrapeGovtNZSite()