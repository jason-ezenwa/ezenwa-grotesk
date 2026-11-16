// Renders docs/feature-sheet.png: each OpenType feature off and on, side by side.
// Usage: node tools/feature-sheet.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const font = fs.readFileSync(path.join(root, 'fonts', 'EzenwaGrotesk-Regular.woff2')).toString('base64');

const rows = [
  ['Tabular figures (tnum)', '', 'tnum', '<div class=col>1,111.10<br>9,084.75<br>₦250,000.00</div>'],
  ['Case-sensitive forms (case)', '', 'case', 'H-H–H—H ¿ABC? ¡ABC!'],
  ['Slashed zero (zero)', '', 'zero', '0 100 2050'],
  ['Fractions (frac)', '', 'frac', '1/2 3/4 5/8'],
  ['Superscript (sups)', '', 'sups', 'x2 m3 10th'],
  ['Ordinals (ordn)', '', 'ordn', '1a 2o No'],
  ['Oldstyle figures (onum)', '', 'onum', '0123456789'],
  ['Turkish (locl, lang tr)', 'tr', '', 'İstanbul firma ﬁ'],
  ['Polish (locl, lang pl)', 'pl', '', 'Śćźńó ŚĆŹŃÓ'],
  ['Romanian (locl, lang ro)', 'ro', '', 'Ştiinţă ştiinţă'],
  ['Catalan (locl, lang ca)', 'ca', '', 'Col·lecció paral·lel'],
  ['Combining accents (mark)', '', '', 'x́ q̃ ậ ğ'],
];

// "Off" renders with no feature and no language; "on" adds whichever applies.
const cell = (lang, feature, text, on) =>
  `<td lang="${on ? lang : ''}" style="font-feature-settings:${on && feature ? `'${feature}' 1` : 'normal'}">${text}</td>`;

const html = `<style>
@font-face{font-family:Z;src:url(data:font/woff2;base64,${font}) format('woff2')}
body{margin:0;padding:32px;background:#fff;color:#0d1233;font-family:Z;width:1300px}
table{border-collapse:collapse;width:100%} td{padding:10px 14px;border-bottom:1px solid #e4e7f0;font-size:34px;vertical-align:top}
th{font:13px monospace;color:#888;text-align:left;padding:6px 14px} td.l{font:14px monospace;color:#666;width:260px}
.col{text-align:right;width:260px}
</style><table><tr><th>Feature</th><th>Off</th><th>On</th></tr>${rows.map(([label, lang, feature, text]) =>
  `<tr><td class=l>${label}</td>${cell(lang, feature, text, false)}${cell(lang, feature, text, true)}</tr>`).join('')}</table>`;

(async () => {
  const launch = process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {};
  const browser = await chromium.launch(launch);
  const tab = await browser.newPage({ viewport: { width: 1364, height: 600 }, deviceScaleFactor: 2 });
  await tab.setContent(html);
  await tab.evaluate(() => document.fonts.ready);
  await tab.screenshot({ path: path.join(root, 'docs', 'feature-sheet.png'), fullPage: true });
  await browser.close();
})();
