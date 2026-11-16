// Renders the Ezenwa Grotesk font book to docs/font-book.pdf and one PNG per page.
// Usage: node tools/font-book.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const fontsDir = path.join(root, 'fonts');
const outDir = path.join(root, 'docs');
const styles = [['Light', 300], ['Regular', 400], ['Medium', 500], ['Semibold', 600], ['Bold', 700]];

let css = '';
for (const [style, weight] of styles) {
  for (const italic of [false, true]) {
    const name = italic ? (style === 'Regular' ? 'Italic' : `${style}Italic`) : style;
    const data = fs.readFileSync(path.join(fontsDir, `EzenwaGrotesk-${name}.woff2`)).toString('base64');
    css += `@font-face{font-family:Ezenwa;src:url(data:font/woff2;base64,${data}) format('woff2');font-weight:${weight};font-style:${italic ? 'italic' : 'normal'}}`;
  }
}

const page = (inner) => `<section>${inner}</section>`;
let body = page(`<div class=cover><div>Ezenwa Grotesk</div><p>Light, Regular, Medium, Semibold, Bold and italics<br>By Chukwuemelie Ezenwa · built on Archivo · SIL Open Font License 1.1</p></div>`);
for (const [style, weight] of styles) {
  body += page(`<div class=lab>${style} ${weight}</div>
  <div style="font-weight:${weight};font-size:120px;line-height:1">Aa Gg Rr</div>
  <div style="font-weight:${weight};font-size:40px;line-height:1.2;margin-top:24px">ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>abcdefghijklmnopqrstuvwxyz<br>0123456789 ₦$€£ &amp;@?!.,:;()[]</div>
  <div style="font-weight:${weight};font-style:italic;font-size:40px;line-height:1.2;margin-top:16px">Italic: Quietly confident, clearly set</div>
  <p style="font-weight:${weight};font-size:17px;line-height:1.5;max-width:640px;margin-top:28px">Good interfaces get out of the way. Labels stay readable at small sizes, numbers line up in tables, and headings keep their character when they grow. The quick brown fox jumps over the lazy dog. 24 projects, ₦1,250,000 budget, 3 days left.</p>`);
}
body += page(`<div class=lab>Sizes · Regular and Medium</div>` + [12, 14, 16, 20, 28, 40, 64].map((px) =>
  `<div style="font-size:${px}px;line-height:1.35"><span style="font:11px monospace;color:#888;display:inline-block;width:40px">${px}</span>Your report is due in <b style="font-weight:500">3 days</b>. Keep going.</div>`).join(''));

const html = `<style>${css} body{margin:0;font-family:Ezenwa;color:#0d1233} section{width:1200px;height:800px;box-sizing:border-box;padding:64px 72px;page-break-after:always;overflow:hidden} .lab{font:13px monospace;color:#888;margin-bottom:20px} .cover{display:flex;flex-direction:column;justify-content:flex-end;height:100%} .cover div{font-size:150px;font-weight:500;letter-spacing:-0.03em;line-height:1} .cover p{font-size:18px;color:#555}</style>${body}`;

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const launch = process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {};
  const browser = await chromium.launch(launch);
  const tab = await browser.newPage({ viewport: { width: 1200, height: 800 }, deviceScaleFactor: 2 });
  await tab.setContent(html);
  await tab.evaluate(() => document.fonts.ready);
  await tab.pdf({ path: path.join(outDir, 'font-book.pdf'), width: '1200px', height: '800px', printBackground: true });
  const sections = await tab.$$('section');
  for (let i = 0; i < sections.length; i++) {
    await sections[i].screenshot({ path: path.join(outDir, `font-book-${i + 1}.png`) });
  }
  await browser.close();
})();
