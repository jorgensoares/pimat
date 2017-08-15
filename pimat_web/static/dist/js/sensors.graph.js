    // set default to straight lines - no curves
    // Chart.defaults.global.elements.line.tension = 0;
    // set default no fill beneath the line
    Chart.defaults.global.elements.line.fill = false;

    var barChartData = {
      labels: [{% for item in sensors_data %}
                  "{{ item.timestamp.strftime('%Y-%m-%d %H:%M') }}",
              {% endfor %}],
      datasets: [{
        type: 'line',
        label: 'Temperature1',
        yAxisID: "y-axis-0",
        borderColor: "rgba(217,83,79,0.75)",
        backgroundColor: "rgba(217,83,79,0.75)",
        data: [{% for item in sensors_data %}
                      "{{ item.temperature1 }}",
                    {% endfor %}]
      }, {
        type: 'line',
        label: 'Temperature2',
        yAxisID: "y-axis-0",
        borderColor: "rgba(92,184,92,0.75)",
        backgroundColor: "rgba(92,184,92,0.75)",
        data: [{% for item in sensors_data %}
                      "{{ item.temperature2 }}",
                    {% endfor %}]
      }, {
        type: 'line',
        label: 'Humidity',
        yAxisID: "y-axis-0",
        borderColor: "rgba(92,184,92,0.75)",
        backgroundColor: "rgba(92,184,92,0.75)",
        data: [{% for item in sensors_data %}
                      "{{ item.humidity }}",
                    {% endfor %}]
      }, {
        type: 'line',
        label: 'Ligh level',
        yAxisID: "y-axis-1",
        borderColor: "rgba(51,51,51,0.5)",
        backgroundColor: "rgba(51,51,51,0.5)",
        data: [{% for item in sensors_data %}
                      "{{ item.light1 }}",
                    {% endfor %}]
      }, {
        type: 'line',
        label: 'Pressure',
        yAxisID: "y-axis-1",
        borderColor: "rgba(151,187,205,0.5)",
        backgroundColor: "rgba(151,187,205,0.5)",
        data: [{% for item in sensors_data %}
                      "{{ item.pressure }}",
                    {% endfor %}]
      }]
    };

    var ctx = document.getElementById("chart");
    // allocate and initialize a chart
    var ch = new Chart(ctx, {
      type: 'line',
      data: barChartData,
      options: {
        title: {
          display: false,
          text: "Chart.js Bar Chart - Stacked"
        },
        tooltips: {
          mode: 'label'
        },
        responsive: false,
        scales: {
          xAxes: [{
            stacked: true,
            scaleLabel: {
                display: true,
                labelString: 'Datetime'
            },
            gridLines : {
                display : true
            }
          }],
          yAxes: [{
            stacked: false,
            position: "left",
            id: "y-axis-0",
            scaleLabel: {
                display: true,
                labelString: 'Temperature / Humidity'
            },
            gridLines : {
                display : true
            }
          }, {
            stacked: false,
            position: "right",
            id: "y-axis-1",
            scaleLabel: {
                display: true,
                labelString: 'Pressure / Light Intensity'
            },
            gridLines : {
                display : true
            }
          }]
        }
      }
    });