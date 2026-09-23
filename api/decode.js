const { GoogleDecoder } = require('google-news-url-decoder');

const decoder = new GoogleDecoder();

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({
      success: false,
      source_url: '',
      error: 'Method not allowed'
    });
  }

  const expectedKey = process.env.DECODER_KEY;
  const suppliedKey = req.headers['x-api-key'];

  if (expectedKey && suppliedKey !== expectedKey) {
    return res.status(401).json({
      success: false,
      source_url: '',
      error: 'Unauthorized'
    });
  }

  try {
    const body = req.body || {};

    const googleNewsUrl =
      body.google_news_url ||
      body.url ||
      '';

    if (!googleNewsUrl) {
      return res.status(200).json({
        ...body,
        success: false,
        source_url: '',
        error: 'google_news_url is required'
      });
    }

    if (!googleNewsUrl.includes('news.google.com')) {
      return res.status(200).json({
        ...body,
        success: false,
        source_url: '',
        error: 'Not a Google News URL'
      });
    }

    const result = await decoder.decode(googleNewsUrl);

    if (!result || !result.status || !result.decoded_url) {
      return res.status(200).json({
        ...body,
        success: false,
        source_url: '',
        error: result?.message || 'Could not decode Google News URL'
      });
    }

    return res.status(200).json({
      ...body,
      google_news_url: googleNewsUrl,
      source_url: result.decoded_url,
      success: true
    });

  } catch (error) {
    return res.status(200).json({
      ...(req.body || {}),
      success: false,
      source_url: '',
      error: error?.message || 'Decoder error'
    });
  }
};
