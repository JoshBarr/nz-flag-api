var schedule = require('node-schedule');
var spawn = require('child_process').spawn;


function scrapeGovtNZSite() {
    console.log('Starting scrape', Date.now());
    var child = spawn('python', ['./flag/scrape.py', 'scrape']);

    child.stdout.on('data', function(data) {
        // console.log(data);
    });

    child.stderr.on('data', function(data) {
        // console.log(data);
    });

    child.on('close', function(code) {
        console.log(code);
    });

    child.on('error', function( err ){ throw err })
}


var j = schedule.scheduleJob('* 1 * * *', function(){
    scrapeGovtNZSite()
});


scrapeGovtNZSite()