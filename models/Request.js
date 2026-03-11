const mongoose = require('mongoose');

const requestSchema = new mongoose.Schema({
  author_id: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  time_cost: { type: Number, required: true },
  location: { type: String, required: true },
  category: { type: String, required: true },
  status: {
    type: String,
    enum: ['open', 'in_progress', 'completed'],
    default: 'open'
  },
  volunteer_id: { type: String, default: null },
  created_at: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Request', requestSchema);