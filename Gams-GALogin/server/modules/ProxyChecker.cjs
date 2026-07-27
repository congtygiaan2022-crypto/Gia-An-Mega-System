const axios = require('axios');
const { HttpsProxyAgent } = require('https-proxy-agent');
const { SocksProxyAgent } = require('socks-proxy-agent');

class ProxyChecker {
  /**
   * Validates a proxy connection and fetches its geolocation details.
   * 
   * @param {Object} config - { type, host, port, username, password }
   * @returns {Promise<Object>} geo details or failure status
   */
  static async check(config) {
    const { type, host, port, username, password } = config;
    if (!host || !port) {
      return { success: false, error: 'Host and port are required.', latency: 0 };
    }

    const typeStr = (type || 'HTTP').toUpperCase();
    const authString = username && password 
      ? `${encodeURIComponent(username)}:${encodeURIComponent(password)}@` 
      : '';
    
    let agent;
    const startTime = Date.now();

    try {
      if (typeStr === 'SOCKS5') {
        agent = new SocksProxyAgent(`socks5://${authString}${host}:${port}`);
      } else {
        // HTTP or HTTPS proxies
        agent = new HttpsProxyAgent(`http://${authString}${host}:${port}`);
      }

      // Query primary geo-IP resolver (ip-api.com over HTTP)
      const res = await axios.get('http://ip-api.com/json', {
        httpAgent: agent,
        httpsAgent: agent,
        timeout: 6000
      });

      const data = res.data;
      const latency = Date.now() - startTime;

      if (data && data.status === 'success') {
        return {
          success: true,
          ip: data.query,
          country: data.country,
          countryCode: data.countryCode, // e.g. "US"
          region: data.regionName,
          city: data.city,
          timezone: data.timezone, // e.g. "America/New_York"
          latency
        };
      }
      throw new Error('IP-API returned fail status');

    } catch (err) {
      // Fallback resolver: ipapi.co (HTTPS)
      try {
        if (!agent) throw err;
        const res = await axios.get('https://ipapi.co/json/', {
          httpAgent: agent,
          httpsAgent: agent,
          timeout: 6000
        });
        const data = res.data;
        const latency = Date.now() - startTime;
        if (data && data.ip) {
          return {
            success: true,
            ip: data.ip,
            country: data.country_name,
            countryCode: data.country_code,
            region: data.region,
            city: data.city,
            timezone: data.timezone,
            latency
          };
        }
      } catch (e) {
        // Ignore fallback error, report original error
      }

      return {
        success: false,
        error: err.message || 'Connection timeout',
        latency: Date.now() - startTime
      };
    }
  }
}

module.exports = ProxyChecker;
