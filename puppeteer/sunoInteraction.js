import puppeteer from "puppeteer";

const delay = ms => new Promise(res => setTimeout(res, ms));
const test = async () => {
    const browser = await puppeteer.launch({
        headless: false
    });
    const page = await browser.newPage();
    await page.goto('https://app.suno.ai');
    const discordSelector = '.cl-socialButtonsBlockButtonText__discord';
    await page.waitForSelector(discordSelector)
    await page.click(discordSelector);
    await page.waitForNavigation();
    const [emailSelector, passwordSelector, submitButtonSelector] = ['input[name="email"]', 'input[name="password"]', 'button[type="submit"]'];
    await page.waitForSelector(emailSelector);
    await page.waitForSelector(passwordSelector);
    await page.waitForSelector(submitButtonSelector);
    await page.type(emailSelector, 'icemetalpunk@gmail.com');
    await page.type(passwordSelector, 'disicecordkinf1');
    await page.click(submitButtonSelector);
    await page.waitForNavigation({

    })
    const sunoLogoSelector = 'a[href="/create"]'
    await page.waitForSelector(sunoLogoSelector);
    await page.goto('https://app.suno.ai/create');
    await page.waitForNavigation();

    const [lyricsSelector, styleSelector, generateButtonSelector] = ['textarea[placeholder="Enter your lyrics"]', 'textarea[placeholder="Enter style of music"]', 'button.css-r7xd4a[type="button"]'];
    await page.waitForSelector(lyricsSelector);
    await page.waitForSelector(styleSelector);
    await page.waitForSelector(generateButtonSelector);
    await page.type(lyricsSelector, 'Testing out some automation\nWriting mock lyrics oh so fast\nThis will be abomination\nLuckily it will not last');
    await page.type(styleSelector, 'New Wave, female vocals');
    await page.click(generateButtonSelector);
    // TODO: Determine when clip is generated, find continue/save button, click, and loop until done
    // browser.close();
}
test();