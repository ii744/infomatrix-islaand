const express = require('express');
const connectDB = require('./db');
const apiRoutes = require('./routes/api');
require('dotenv').config();

const app = express();
app.use(express.json());

connectDB();

app.use('/api', apiRoutes);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});