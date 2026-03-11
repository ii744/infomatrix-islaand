const mongoose = require('mongoose');

const responseSchema = new mongoose.Schema({
  request_id: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Request',
    required: true
  },
  volunteer_id: { type: String, required: true },
  status: {
    type: String,
    enum: ['pending', 'accepted', 'rejected'],
    default: 'pending'
  },
  message: { type: String, default: '' },
  created_at: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Response', responseSchema);