const express = require('express');
const path = require('path');

const app = express();
const port = 8083;

// Serve demo HTML page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(port, () => {
  console.log(`[Q3 Testbed] Demo page running at http://localhost:${port}`);
});
