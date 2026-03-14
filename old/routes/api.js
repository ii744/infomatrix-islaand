const express = require('express');
const router = express.Router();
const Request = require('../models/Request');
const Response = require('../models/Response');

// GET: всі open запити + фільтри
router.get('/requests', async (req, res) => {
  try {
    const { location, category } = req.query;
    const filters = { status: 'open' };
    if (location) filters.location = location;
    if (category) filters.category = category;

    const requests = await Request.find(filters).sort({ created_at: -1 });
    res.json(requests);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST: створити запит
router.post('/requests', async (req, res) => {
  try {
    const { title, description, time_cost, location, category } = req.body;
    const newRequest = new Request({
      author_id: req.user?.id || 'temp-user-id', // ← заміни на реальну аутентифікацію пізніше
      title,
      description,
      time_cost,
      location,
      category
    });
    await newRequest.save();
    res.status(201).json(newRequest);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// GET: один запит за ID
router.get('/requests/:id', async (req, res) => {
  try {
    const request = await Request.findById(req.params.id);
    if (!request) return res.status(404).json({ error: 'Not found' });
    res.json(request);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST: створити відгук
router.post('/responses', async (req, res) => {
  try {
    const { request_id, message } = req.body;
    const newResponse = new Response({
      request_id,
      volunteer_id: req.user?.id || 'temp-volunteer-id',
      message: message || ''
    });
    await newResponse.save();
    res.status(201).json(newResponse);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// GET: відгуки до запиту
router.get('/requests/:id/responses', async (req, res) => {
  try {
    const responses = await Response.find({ request_id: req.params.id }).sort({ created_at: -1 });
    res.json(responses);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PATCH: зміна статусу відгуку (вибір виконавця)
router.patch('/responses/:id', async (req, res) => {
  try {
    const { status } = req.body;
    if (!['accepted', 'rejected'].includes(status)) {
      return res.status(400).json({ error: 'Invalid status' });
    }

    const response = await Response.findByIdAndUpdate(req.params.id, { status }, { new: true });
    if (!response) return res.status(404).json({ error: 'Not found' });

    if (status === 'accepted') {
      // rejected інші
      await Response.updateMany(
        { request_id: response.request_id, _id: { $ne: req.params.id } },
        { status: 'rejected' }
      );
      // оновлюємо Request
      await Request.findByIdAndUpdate(response.request_id, {
        status: 'in_progress',
        volunteer_id: response.volunteer_id
      });
    }

    res.json(response);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// PATCH: зміна статусу запиту (in_progress / completed)
router.patch('/requests/:id', async (req, res) => {
  try {
    const { status } = req.body;
    const update = { status };

    if (status === 'in_progress' && req.body.volunteer_id) {
      update.volunteer_id = req.body.volunteer_id;
    }

    const request = await Request.findByIdAndUpdate(req.params.id, update, { new: true });
    if (!request) return res.status(404).json({ error: 'Not found' });
    res.json(request);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

module.exports = router;