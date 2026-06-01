const puppeteer = require('puppeteer');

(async () => {
    try {
        const browser = await puppeteer.launch();
        const page = await browser.newPage();
        
        await page.setViewport({
            width: 1440,
            height: 900,
            deviceScaleFactor: 1,
        });

        console.log("Loading dashboard...");
        await page.goto('http://127.0.0.1:8080/', {waitUntil: 'networkidle2'});
        await new Promise(resolve => setTimeout(resolve, 1000));

        const sections = [
            { name: '1_dashboard', selector: 'div.nav-item[onclick*="dashboard"]' },
            { name: '2_taskList', selector: 'div.nav-item[onclick*="taskList"]' },
            { name: '3_tools', selector: 'div.nav-item[onclick*="tools"]' },
            { name: '4_reports', selector: 'div.nav-item[onclick*="reports"]' },
            { name: '5_memory', selector: 'div.nav-item[onclick*="memory"]' },
            { name: '6_builder', selector: 'div.nav-item[onclick*="builder"]' },
            { name: '7_hierarchy', selector: 'div.nav-item[onclick*="hierarchy"]' },
            { name: '8_settings', selector: 'div.nav-item[onclick*="settings"]' },
            { name: '9_debug', selector: 'div.nav-item[onclick*="debug"]' }
        ];

        for (const sec of sections) {
            console.log(`Switching to section: ${sec.name}`);
            try {
                if (sec.name !== '1_dashboard') {
                    await page.click(sec.selector);
                    // wait for transitions or animations
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
                await page.screenshot({ path: `screenshot_${sec.name}.png` });
                console.log(`Saved screenshot_${sec.name}.png`);
            } catch (err) {
                console.error(`Error in section ${sec.name}: ${err.message}`);
            }
        }

        await browser.close();
        console.log("Completed screenshots of all tabs.");
    } catch (e) {
        console.error(e);
    }
})();
