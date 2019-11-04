const textColor = '#eeeeee';

var dataJson = [];
var pmChart;
var tempHumChart;

var app = new Vue({
    el: '#website',
    data: {
        pm10: 0.0,
        pm25: 0.0,
        temp: 0.0,
        hum: 0.0,
    },
    methods: {
        update: function (data) {
            this.pm10 = data.pm10;
            this.pm25 = data.pm25;
            this.temp = data.temp;
            this.hum = data.hum;
        }
    }
});

function getData(timeframe = 'day') {
    fetch(window.location.origin + '/data?t=' + timeframe).then(response => {
        response.json().then(json => {
            dataJson = json;
            let latestData = dataJson.data[dataJson.data.length - 1];
            app.update(latestData);
            adaptColor(latestData);
            buildFeinstaubChart();
            buildTempHumChart();
        });
    });
}

function adaptColor(data) {
    let pm10 = data.pm10;
    let pm10BgColor = 240 - (6 * pm10);
    $('#pm10-card').css('backgroundColor', `hsl(${pm10BgColor}, 100%, 35%)`);
    $('#pm10-card').css('color', textColor);

    let pm25 = data.pm25;
    let pm25BgColor = 240 - (12 * pm25);
    $('#pm25-card').css('backgroundColor', `hsl(${pm25BgColor}, 100%, 35%)`);
    $('#pm25-card').css('color', textColor);

    let temp = data.temp;
    let tempColor = 300 + (2 * temp);
    $('#temp-card').css('backgroundColor', `hsl(${tempColor}, 100%, 35%)`);
    $('#temp-card').css('color', textColor);

    let hum = data.hum;
    let humBlur = hum / 100;
    $('#hum-card').css('textShadow', `0 0 5px rgba(0,0,0,${humBlur})`);
    $('#hum-card').css('color', 'transparent');
}

function buildFeinstaubChart(data = this.dataJson.data) {
    if (pmChart) {
        pmChart.destroy();
    }
    pmChart = new CanvasJS.Chart("pm-container", {
        animationEnabled: true,
        zoomEnabled: true,
        exportEnabled: true,
        legend: {
            cursor: "pointer",
            fontSize: 16,
        },
        toolTip: {
            shared: true
        },
        axisY: {
            includeZero: true,
            title: 'Feinstaub in µg/m^3'
        },
        axisX: {
            valueFormatString: "DD MMM, HH:mm"
        },
        data: [{
            type: 'spline',
            name: 'PM10',
            showInLegend: true,
            yValueFormatString: '###.# µg/m^3',
            dataPoints: data.map((elem, idx, arr) => {
                return {
                    x: new Date(elem.timestamp),
                    y: elem.pm10
                }
            })
        }, {
            type: 'spline',
            name: 'PM2.5',
            showInLegend: true,
            yValueFormatString: '###.# µg/m^3',
            dataPoints: data.map((elem, idx, arr) => {
                return {
                    x: new Date(elem.timestamp),
                    y: elem.pm25
                }
            })
        }]
    });
    pmChart.render();
}

function buildTempHumChart(data = this.dataJson.data) {
    if (tempHumChart) {
        tempHumChart.destroy()
    }
    tempHumChart = new CanvasJS.Chart("temp-hum-container", {
        animationEnabled: true,
        zoomEnabled: true,
        exportEnabled: true,
        legend: {
            cursor: "pointer",
            fontSize: 16,
        },
        toolTip: {
            shared: true
        },
        axisY: {
            includeZero: true,
            title: 'Luftfeuchte in %'
        },
        axisY2: {
            title: 'Temperatur in °C'
        },
        axisX: {
            valueFormatString: "DD MMM, HH"
        },
        data: [{
            type: 'spline',
            name: 'Luftfeuchtigkeit',
            showInLegend: true,
            yValueFormatString: '###.# %',
            dataPoints: data.filter((elem) => elem.hum).map((elem) => {
                return {
                    x: new Date(elem.timestamp),
                    y: elem.hum
                }
            })
        }, {
            type: 'spline',
            name: 'Temperatur',
            showInLegend: true,
            yValueFormatString: '###.# °C',
            axisYType: 'secondary',
            dataPoints: data.filter((elem) => elem.temp).map((elem) => {
                return {
                    x: new Date(elem.timestamp),
                    y: elem.temp
                }
            })
        }]
    });
    tempHumChart.render();
}

function assignDateChangeHandler() {}

$(document).ready(() => {
    getData();
    // $('#feinstaubChart').on('click', () => buildFeinstaubChart());
    // $('#tempHumChart').on('click', () => buildTempHumChart());
    $('.timeframeBtn').on('click', function () {
        console.log('timeframe btn clicked');
        getData(this.id)
    });
    // assignDateChangeHandler();
});