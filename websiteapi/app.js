const express = require('express');
const fs = require('fs');
const cron = require('node-cron');
const cp = require('child_process')
const app = express();

// serve static files such as index.html, stylesheets and scripts
app.use(express.static(__dirname + '/public'));
// for parsing application/json
app.use(express.json());
// for parsing application/x-www-form-urlencoded
app.use(express.urlencoded({
    extended: true
}));

app.listen(8080, () => {
    console.log('Listen to Port 8080');
});

// GET method to get the latest data
// t sets the timeframe (last day / week / month / year)
app.get('/data', (req, res) => {
    let timeframe = req.query.t;
    if (!timeframe) {
        timeframe = 'day';
    }
    let data = getDataFor(timeframe);
    res.status(200).json(data);
});

// POST method to add new data
// for every day there is one data file, so the files don't get too big
app.post('/data', (req, res) => {
    let newData = req.body;
    newData = saveData(newData);
    res.status(201).json(newData);
});

function saveData(newData) {
    let today = new Date();
    newData.timestamp = today.toISOString();
    console.log(newData);
    let filename = `data/data-${today.getFullYear()}-${today.getMonth() + 1}-${today.getDate()}.json`;
    let data;
    if (fs.existsSync(filename)) {
        data = JSON.parse(fs.readFileSync(filename, 'utf8'));
    } else {
        data = {
            data: []
        }
    }
    data.data.push(newData);
    data = doSomeStatisticsOn(data);
    fs.writeFileSync(filename, JSON.stringify(data));
    return data;
}

function getDataFor(t) {
    let currDate = new Date();
    let oldestDate = new Date();
    if (t == 'day') {
        oldestDate.setDate(currDate.getDate() - 1);
    } else if (t == 'week') {
        oldestDate.setDate(currDate.getDate() - 7);
    } else if (t == 'month') {
        oldestDate.setMonth(currDate.getMonth() - 1);
    } else if (t == 'year') {
        oldestDate.setFullYear(currDate.getFullYear() - 1);
    }
    let data = {
        data: []
    };
    while (currDate >= oldestDate) {
        const filename = `data/data-${currDate.getFullYear()}-${currDate.getMonth() + 1}-${currDate.getDate()}.json`;
        if (fs.existsSync(filename)) {
            let json = fs.readFileSync(filename, 'utf8');
            let newData = JSON.parse(json).data;
            if (new Date(newData[newData.length - 1].timestamp) >= oldestDate) {
                data.data = newData.concat(data.data);
            } else {
                newDataArr = [];
                for (let i in newData) {
                    if (new Date(newData[i].timestamp) >= oldestDate) {
                        newDataArr.append(newData[i]);
                    }
                }
                data.data = newDataArr.concat(data.data);
            }
        }
        currDate.setDate(currDate.getDate() - 1);
    }
    data = doSomeStatisticsOn(data);
    return data;
}

function doSomeStatisticsOn(data) {
    if (data.data.length == 0) {
        return data;
    }
    for (let i in data.data) {
        let elem = data.data[i];
        data.maxPm10 = data.maxPm10 ? Math.max(data.maxPm10, elem.pm10) : elem.pm10;
        data.minPm10 = data.minPm10 ? Math.min(data.minPm10, elem.pm10) : elem.pm10;
        data.maxPm25 = data.maxPm25 ? Math.max(data.maxPm25, elem.pm25) : elem.pm25;
        data.minPm25 = data.minPm25 ? Math.min(data.minPm25, elem.pm25) : elem.pm25;
        data.maxTemp = data.maxTemp ? Math.min(data.maxTemp, elem.temp) : elem.temp;
        data.minTemp = data.minTemp ? Math.min(data.minTemp, elem.temp) : elem.temp;
        data.maxHum = data.maxHum ? Math.min(data.maxHum, elem.hum) : elem.hum;
        data.minHum = data.minHum ? Math.min(data.minHum, elem.hum) : elem.hum;
    }
    return data;
}

cron.schedule('*/5 * * * *', () => { readSensorValues() });

function readSensorValues() {
    const sensorReader = cp.spawn('python', ['../datalogger/read-sensors.py'])
    sensorReader.stdout.on('data', (data) => {
        var pm10, pm25, temp, hum;
        values = Buffer.from(data, 'hex').toString();
        values = values.split('\n');
        for (var i in values) {
            var elem = values[i].split('=');
            if (elem[0] === 'pm10') {
                pm10 = elem[1];
            } else if (elem[0] === 'pm25') {
                pm25 = elem[1];
            } else if (elem[0] === 'temp') {
                temp = elem[1];
            } else if (elem[0] === 'hum') {
                hum = elem[1];
            } else {
                console.log(elem[0]);
            }
        }
        saveData({
            pm10: pm10,
            pm25: pm25,
            temp: temp,
            hum: hum
        });
    });

}