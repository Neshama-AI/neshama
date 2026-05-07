const { chromium } = require('playwright');

async function captureScreenshots() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 }
  });
  const page = await context.newPage();
  
  const baseUrl = 'http://127.0.0.1:8425';
  
  try {
    // 访问首页
    console.log('访问首页...');
    await page.goto(baseUrl, { waitUntil: 'networkidle', timeout: 10000 });
    await page.waitForTimeout(1000);
    
    // 截图首页
    await page.screenshot({ path: 'screenshots/homepage.png' });
    console.log('首页截图已保存');
    
    // 尝试点击模型市场导航
    console.log('尝试点击模型市场...');
    const modelMarketplaceSelectors = [
      'text="Model Marketplace"',
      'text="🤖"',
      '[data-testid="model-marketplace"]',
      'a[href*="model"]',
      'nav >> text=Model'
    ];
    
    let clicked = false;
    for (const selector of modelMarketplaceSelectors) {
      try {
        const element = await page.locator(selector).first();
        if (await element.isVisible({ timeout: 2000 })) {
          await element.click();
          clicked = true;
          console.log(`已点击: ${selector}`);
          break;
        }
      } catch (e) {
        continue;
      }
    }
    
    if (!clicked) {
      // 尝试直接访问模型市场URL
      console.log('尝试直接访问模型市场URL...');
      await page.goto(`${baseUrl}/model-marketplace`, { waitUntil: 'networkidle', timeout: 10000 });
    }
    
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/model-marketplace-cn.png' });
    console.log('模型市场截图已保存');
    
    // 点击编码套餐
    console.log('尝试点击编码套餐...');
    const codingPlansSelectors = [
      'text="Coding Plans"',
      'text="📋"',
      '[data-testid="coding-plans"]',
      'a[href*="coding"]',
      'nav >> text=Coding'
    ];
    
    clicked = false;
    for (const selector of codingPlansSelectors) {
      try {
        const element = await page.locator(selector).first();
        if (await element.isVisible({ timeout: 2000 })) {
          await element.click();
          clicked = true;
          console.log(`已点击: ${selector}`);
          break;
        }
      } catch (e) {
        continue;
      }
    }
    
    if (!clicked) {
      console.log('尝试直接访问编码套餐URL...');
      await page.goto(`${baseUrl}/coding-plans`, { waitUntil: 'networkidle', timeout: 10000 });
    }
    
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'screenshots/coding-plans-cn.png' });
    console.log('编码套餐截图已保存');
    
    console.log('所有截图完成!');
    
  } catch (error) {
    console.error('发生错误:', error.message);
  } finally {
    await browser.close();
  }
}

captureScreenshots();
