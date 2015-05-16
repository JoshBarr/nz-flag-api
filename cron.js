var schedule = require('node-schedule');
var spawn = require('child_process').spawn;


function scrapeGovtNZSite() {
    console.log('Starting scrape', Date.now());
    var child = spawn('npm run dump && npm run scrape');

    child.stdout.on('data', function(data) {
        console.log(data);
    });

    child.stderr.on('data', function(data) {
        console.log(data);
    });

    child.on('close', function(code) {
        console.log(code);
    });
}


var j = schedule.scheduleJob('* 1 * * *', function(){
    console.log('The answer to life, the universe, and everything!');
    scrapeGovtNZSite()
});


scrapeGovtNZSite()