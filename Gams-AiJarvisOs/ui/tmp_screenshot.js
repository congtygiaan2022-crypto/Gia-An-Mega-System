const puppeteer = require('puppeteer');

(async () => {
    try {
        const browser = await puppeteer.launch();
        const page = await browser.newPage();
        
        // Log all console messages
        page.on('console', msg => {
            console.log(`[BROWSER CONSOLE - ${msg.type()}]: ${msg.text()}`);
        });

        // Log page errors (JS crashes)
        page.on('pageerror', err => {
            console.error(`[BROWSER EXCEPTION]: ${err.toString()}`);
        });

        // Log failed network requests
        page.on('requestfailed', request => {
            console.log(`[REQUEST FAILED]: ${request.url()} - ${request.failure().errorText}`);
        });

        // Log non-200 responses
        page.on('response', response => {
            if (response.status() >= 400) {
                console.log(`[HTTP ERROR ${response.status()}]: ${response.url()}`);
            }
        });

        // Set viewport size
        await page.setViewport({
            width: 1280,
            height: 800,
            deviceScaleFactor: 1,
        });

        console.log("Loading page at http://127.0.0.1:8080/ ...");
        await page.goto('http://127.0.0.1:8080/', {waitUntil: 'networkidle2'});

        // Wait a bit to ensure animations or JS render completely
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Click all navigation items to check if clicking them triggers any JS exceptions
        const navSelectors = [
            'div.nav-item[onclick*="taskList"]',
            'div.nav-item[onclick*="tools"]',
            'div.nav-item[onclick*="reports"]',
            'div.nav-item[onclick*="memory"]',
            'div.nav-item[onclick*="builder"]',
            'div.nav-item[onclick*="hierarchy"]',
            'div.nav-item[onclick*="settings"]',
            'div.nav-item[onclick*="debug"]'
        ];

        for (const selector of navSelectors) {
            console.log(`Clicking navigation: ${selector}`);
            try {
                await page.click(selector);
                await new Promise(resolve => setTimeout(resolve, 500));
            } catch (e) {
                console.error(`Failed to click selector ${selector}: ${e.message}`);
            }
        }

        console.log('Testing finished.');
        await browser.close();
    } catch (e) {
        console.error(e);
    }
})();
