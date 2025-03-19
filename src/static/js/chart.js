document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById("rfChart").getContext("2d");
    const rfChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: "RF Scan",
                data: [],
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1,
                fill: false
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { title: { display: true, text: "Frequency (MHz)" } },
                y: { title: { display: true, text: "Signal Strength (dB)" } }
            }
        }
    });

    // Connect to the scan data stream
    const source = new EventSource("/scan/stream");
    source.onmessage = function (event) {
        const scanData = JSON.parse(event.data);

        if (scanData && scanData.frequencies && scanData.values) {
            rfChart.data.labels = scanData.frequencies;
            rfChart.data.datasets[0].data = scanData.values;
            rfChart.update();
        }
    };
});
