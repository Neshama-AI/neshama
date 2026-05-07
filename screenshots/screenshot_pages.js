const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();
    
    const baseUrl = 'http://127.0.0.1:8423';
    const outDir = './screenshots';
    
    console.log('Opening Soul Panel...');
    await page.goto(baseUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // 1. Composite Emotion
    console.log('Taking screenshot: Composite Emotion');
    try {
        const navItem = page.locator('text="🎭"').first();
        await navItem.click();
        await page.waitForTimeout(3000);
        await page.screenshot({ path: `${outDir}/composite-emotion-cn.png`, fullPage: false });
        console.log('  ✓ composite-emotion-cn.png');
    } catch (e) {
        console.log('  ✗ Failed:', e.message);
    }
    
    // 2. Entity Graph
    console.log('Taking screenshot: Entity Graph');
    try {
        const navItem = page.locator('text="🕸️"').first();
        await navItem.click();
        await page.waitForTimeout(3000);
        await page.screenshot({ path: `${outDir}/entity-graph-cn.png`, fullPage: false });
        console.log('  ✓ entity-graph-cn.png');
    } catch (e) {
        console.log('  ✗ Failed:', e.message);
    }
    
    // 3. Progressive Summarization
    console.log('Taking screenshot: Progressive Summarization');
    try {
        const navItem = page.locator('text="📝"').first();
        await navItem.click();
        await page.waitForTimeout(3000);
        await page.screenshot({ path: `${outDir}/progressive-summarization-cn.png`, fullPage: false });
        console.log('  ✓ progressive-summarization-cn.png');
    } catch (e) {
        console.log('  ✗ Failed:', e.message);
    }
    
    await browser.close();
    console.log('Done!');
})();
