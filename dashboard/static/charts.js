const socket = io();
const ctx = document.getElementById('tradeChart').getContext('2d');
const labels = [], dataPoints = [];
const chart = new Chart(ctx, { type: 'line', data: { labels, datasets: [{ label: 'Confidence', data: dataPoints }] }, options: { scales: { y: { min: 0, max: 1 } } } });
const eventsDiv = document.getElementById('events');

function addEvent(e) {
  let p = document.createElement('pre');
  p.textContent = JSON.stringify(e, null, 2);
  eventsDiv.prepend(p);
  if (eventsDiv.children.length > 200) eventsDiv.removeChild(eventsDiv.lastChild);
}

socket.on('bootstrap', (logs) => {
  labels.length = 0; dataPoints.length = 0;
  logs.forEach(l => { labels.push(l.timestamp || ''); dataPoints.push(l.confidence || 0); addEvent(l); });
  chart.update();
});

socket.on('trade_data', (log) => {
  labels.push(log.timestamp || ''); dataPoints.push(log.confidence || 0); if (labels.length > 200) { labels.shift(); dataPoints.shift(); }
  addEvent(log);
  chart.update();
});
