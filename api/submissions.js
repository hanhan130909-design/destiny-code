/**
 * Vercel Serverless Function — Submissions API
 * Stores form submissions in Vercel Blob Storage (free tier).
 * 
 * GET  /api/submissions  → list all submissions
 * POST /api/submissions  → store a new submission
 */
import { list, put, head, del } from '@vercel/blob';

const BLOB_PATH = 'submissions/data.json';

export default async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }

  if (req.method === 'GET') {
    try {
      // Try to read existing submissions blob
      const { blobs } = await list({ prefix: 'submissions/' });
      const dataBlob = blobs.find(b => b.pathname === BLOB_PATH);
      
      if (!dataBlob) {
        return res.status(200).json({ total: 0, submissions: [] });
      }

      const response = await fetch(dataBlob.url);
      if (!response.ok) {
        return res.status(200).json({ total: 0, submissions: [] });
      }
      
      const data = await response.json();
      return res.status(200).json({
        total: data.length,
        submissions: data,
      });
    } catch (err) {
      console.error('GET submissions error:', err);
      return res.status(500).json({ error: err.message });
    }
  }

  if (req.method === 'POST') {
    try {
      const submission = req.body;
      
      if (!submission || !submission.name) {
        return res.status(400).json({ error: 'Missing required fields' });
      }

      // Add timestamp
      const entry = {
        ...submission,
        date: new Date().toISOString(),
      };

      // Read existing submissions
      let submissions = [];
      try {
        const { blobs } = await list({ prefix: 'submissions/' });
        const dataBlob = blobs.find(b => b.pathname === BLOB_PATH);
        if (dataBlob) {
          const response = await fetch(dataBlob.url);
          if (response.ok) {
            submissions = await response.json();
          }
        }
      } catch (e) {
        // Start fresh if read fails
      }

      // Append new submission
      submissions.push(entry);

      // Write back to blob
      await put(BLOB_PATH, JSON.stringify(submissions, null, 2), {
        access: 'public',
        contentType: 'application/json',
      });

      return res.status(200).json({ ok: true, total: submissions.length });
    } catch (err) {
      console.error('POST submission error:', err);
      return res.status(500).json({ error: err.message });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
