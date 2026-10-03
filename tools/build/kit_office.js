// FusionSpace kit: Office templates. Called by kit.py as `node kit_office.js <OUT>/kit`.
// Needs the npm packages pptxgenjs and docx (npm i -g pptxgenjs docx, or a local node_modules).
// Writes documents/slides/fusionspace-slides.pptx and documents/letterhead/letterhead-{letter,a4}.docx.
const fs = require("fs"), path = require("path");
const KIT = process.argv[2];
const P = (...p) => path.join(KIT, ...p);
const img = p => "image/png;base64," + fs.readFileSync(P(p)).toString("base64");
const aspect = p => { const b = fs.readFileSync(P(p)); return b.readUInt32BE(20) / b.readUInt32BE(16); };   // height / width

const C = {void: "0B0F1C", abyss: "141A2B", graphite: "2A3248", slate: "566079", haze: "98A1B8", mist: "D6DAE4",
           paper: "F3F4F7", white: "FFFFFF", ion: "3350D6", ember: "B34F0C", m: "DA7C30", o: "768DF5"};
const HEAD = "Cascadia Mono", BODY = "Archivo";
const META = JSON.parse(fs.readFileSync(path.join(KIT, ".office.json"), "utf8"));   // written by kit.py
const TAGLINE = META.tagline, ROLE = META.role, EMAIL = META.email, SITE = META.site, GITHUB = META.github;

// ------------------------------------------------------------------ slides
async function slides() {
  const pptxgen = require("pptxgenjs");
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";                       // 13.333 × 7.5 in
  pres.author = "Neer Patel"; pres.company = "FusionSpace"; pres.title = "FusionSpace slide template";
  pres.theme = {headFontFace: HEAD, bodyFontFace: BODY};
  const W = 13.333, H = 7.5, M = 0.6;
  const bgDark = {data: img("documents/slides/slide-background-dark.png")};
  const bgLight = {data: img("documents/slides/slide-background-light.png")};
  const logoC = img("documents/slides/_logo-horizontal-color.png"), logoV = img("documents/slides/_logo-horizontal-light.png");
  const markC = img("documents/slides/_logo-mark-color.png");
  const LR = aspect("documents/slides/_logo-horizontal-color.png");   // lockup height / width
  const footer = (dark) => ([
    {image: {data: dark ? logoC : logoV, x: M, y: H - 0.55, w: 1.35, h: 1.35 * LR}},
    {text: {text: "FS-VEGA · REV A", options: {x: W - M - 4.75, y: H - 0.6, w: 4, h: 0.3, fontFace: HEAD, fontSize: 10, color: dark ? C.haze : C.slate, align: "right", margin: 0}}},
  ]);
  pres.defineSlideMaster({title: "FS Title", background: bgDark, objects: []});
  pres.defineSlideMaster({title: "FS Section", background: bgDark, objects: [...footer(true),
      {placeholder: {options: {name: "label", type: "body", x: M, y: 2.5, w: 9, h: 0.4, fontFace: HEAD, fontSize: 14, color: C.o, margin: 0}, text: "SECTION 01"}},
      {placeholder: {options: {name: "title", type: "title", x: M, y: 3.0, w: 11.5, h: 1.3, fontFace: HEAD, fontSize: 44, bold: true, color: C.paper, margin: 0, valign: "top", align: "left"}, text: "Section title"}}],
    slideNumber: {x: W - M - 0.5, y: H - 0.6, w: 0.5, h: 0.3, fontFace: HEAD, fontSize: 10, color: C.haze, align: "right"}});
  pres.defineSlideMaster({title: "FS Content", background: bgLight, objects: [...footer(false),
      {placeholder: {options: {name: "title", type: "title", x: M, y: 0.45, w: 12, h: 0.8, fontFace: HEAD, fontSize: 30, bold: true, color: C.void, margin: 0, valign: "top", align: "left"}, text: "Slide title"}},
      {placeholder: {options: {name: "body", type: "body", x: M, y: 1.55, w: 12, h: 4.9, fontFace: BODY, fontSize: 20, color: C.void, margin: 0, valign: "top", align: "left"}, text: "Body text"}}],
    slideNumber: {x: W - M - 0.5, y: H - 0.6, w: 0.5, h: 0.3, fontFace: HEAD, fontSize: 10, color: C.slate, align: "right"}});
  pres.defineSlideMaster({title: "FS Two Column", background: bgLight, objects: [...footer(false),
      {placeholder: {options: {name: "title", type: "title", x: M, y: 0.45, w: 12, h: 0.8, fontFace: HEAD, fontSize: 30, bold: true, color: C.void, margin: 0, valign: "top", align: "left"}, text: "Slide title"}},
      {placeholder: {options: {name: "left", type: "body", x: M, y: 1.55, w: 5.8, h: 4.9, fontFace: BODY, fontSize: 20, color: C.void, margin: 0, valign: "top", align: "left"}, text: "Left column"}},
      {placeholder: {options: {name: "right", type: "body", x: M + 6.3, y: 1.55, w: 5.8, h: 4.9, fontFace: BODY, fontSize: 20, color: C.void, margin: 0, valign: "top", align: "left"}, text: "Right column"}}],
    slideNumber: {x: W - M - 0.5, y: H - 0.6, w: 0.5, h: 0.3, fontFace: HEAD, fontSize: 10, color: C.slate, align: "right"}});
  pres.defineSlideMaster({title: "FS Closing", background: bgDark, objects: []});
  // more layouts (design review, October 2026): picture placeholders for images, and a dark content layout for code and quotes
  const titleLight = {placeholder: {options: {name: "title", type: "title", x: M, y: 0.45, w: 12, h: 0.8, fontFace: HEAD, fontSize: 30, bold: true, color: C.void, margin: 0, valign: "top", align: "left"}, text: "Slide title"}};
  const numLight = {x: W - M - 0.5, y: H - 0.6, w: 0.5, h: 0.3, fontFace: HEAD, fontSize: 10, color: C.slate, align: "right"};
  const numDark = {...numLight, color: C.haze};
  pres.defineSlideMaster({title: "FS Image", background: bgLight, objects: [...footer(false), titleLight,
      {placeholder: {options: {name: "pic", type: "pic", x: M, y: 1.55, w: 8.0, h: 4.5}, text: ""}},
      {placeholder: {options: {name: "caption", type: "body", x: M + 8.4, y: 1.55, w: 3.6, h: 4.5, fontFace: BODY, fontSize: 16, color: C.slate, margin: 0, valign: "top", align: "left"}, text: "Caption"}}],
    slideNumber: numLight});
  pres.defineSlideMaster({title: "FS Full Image", background: bgDark, objects: [
      {placeholder: {options: {name: "pic", type: "pic", x: 0, y: 0, w: W, h: H}, text: ""}},
      {rect: {x: 0, y: H - 1.55, w: W, h: 1.55, fill: {color: C.void, transparency: 15}}},
      {placeholder: {options: {name: "title", type: "title", x: M, y: H - 1.35, w: 10, h: 0.6, fontFace: HEAD, fontSize: 26, bold: true, color: C.paper, margin: 0, valign: "top", align: "left"}, text: "Image title"}},
      {placeholder: {options: {name: "caption", type: "body", x: M, y: H - 0.72, w: 10, h: 0.35, fontFace: BODY, fontSize: 14, color: C.haze, margin: 0, valign: "top", align: "left"}, text: "Caption or credit"}}],
    slideNumber: numDark});
  pres.defineSlideMaster({title: "FS Dark Content", background: bgDark, objects: [...footer(true),
      {placeholder: {options: {name: "title", type: "title", x: M, y: 0.45, w: 12, h: 0.8, fontFace: HEAD, fontSize: 30, bold: true, color: C.paper, margin: 0, valign: "top", align: "left"}, text: "Slide title"}}],
    slideNumber: numDark});

  // 1 · title
  let s = pres.addSlide({masterName: "FS Title"});
  s.addImage({data: logoC, x: M, y: 0.55, w: 2.6, h: 2.6 * LR});
  s.addText("FS-VEGA · DESIGN REVIEW · REV A", {x: M, y: 3.0, w: 10, h: 0.4, fontFace: HEAD, fontSize: 14, color: C.o, margin: 0, isTextBox: true, charSpacing: 2});
  s.addText("Presentation title", {x: M, y: 3.45, w: 11.5, h: 1.2, fontFace: HEAD, fontSize: 50, bold: true, color: C.paper, margin: 0, isTextBox: true, valign: "top"});
  s.addText("Subtitle or one-line summary", {x: M, y: 4.7, w: 11, h: 0.5, fontFace: BODY, fontSize: 20, color: C.haze, margin: 0, isTextBox: true});
  s.addText("Neer Patel · " + new Date().toLocaleDateString("en-GB", {month: "long", year: "numeric"}), {x: M, y: H - 0.95, w: 6, h: 0.3, fontFace: HEAD, fontSize: 12, color: C.haze, margin: 0, isTextBox: true});
  s.addImage({data: markC, x: W - 4.6, y: 1.4, w: 3.9, h: 3.9});
  s.addNotes("Title layout. Replace the designation, title, subtitle and date. The mark on the right is optional.");
  // agenda
  s = pres.addSlide({masterName: "FS Content"});
  s.addText("Agenda", {placeholder: "title", align: "left"});
  ["Mission overview", "Design", "Test results", "Risks and open items", "Next steps"].forEach((t, i) => {
    const y = 1.65 + i * 0.85;
    s.addText(String(i + 1).padStart(2, "0"), {x: M, y, w: 0.9, h: 0.6, fontFace: HEAD, fontSize: 26, bold: true, color: C.ion, margin: 0, isTextBox: true, valign: "middle"});
    s.addText(t, {x: M + 1.0, y, w: 10, h: 0.6, fontFace: BODY, fontSize: 22, color: C.void, margin: 0, isTextBox: true, valign: "middle"});
    if (i < 4) s.addShape(pres.shapes.LINE, {x: M + 1.0, y: y + 0.72, w: 8, h: 0, line: {color: C.mist, width: 1}});
  });
  s.addNotes("Agenda: up to five items. The numbers are Cascadia Mono in Ion.");
  // section
  s = pres.addSlide({masterName: "FS Section"});
  s.addText("SECTION 01", {placeholder: "label"}); s.addText("Mission overview", {placeholder: "title", align: "left"});
  // 3 · content
  s = pres.addSlide({masterName: "FS Content"});
  s.addText("Content slide title", {placeholder: "title", align: "left"});
  s.addText([
    {text: "Use this layout for most content. Headings are Cascadia Mono SemiBold, body text is Archivo.", options: {bullet: true, breakLine: true}},
    {text: "Keep one idea per slide; put detail in the speaker notes.", options: {bullet: true, breakLine: true}},
    {text: "Accent colours on light backgrounds: Ion #3350D6 for links and highlights, Ember #B34F0C for warnings.", options: {bullet: true}},
  ], {placeholder: "body", fontSize: 20, paraSpaceAfter: 12});
  // 4 · two column
  s = pres.addSlide({masterName: "FS Two Column"});
  s.addText("Two-column slide", {placeholder: "title", align: "left"});
  s.addText([{text: "Requirement", options: {bold: true, breakLine: true}}, {text: "Left column text, a figure, or a table."}], {placeholder: "left", fontSize: 20});
  s.addText([{text: "Result", options: {bold: true, breakLine: true}}, {text: "Right column text, a chart, or an image."}], {placeholder: "right", fontSize: 20});
  // image and caption
  const imgL = img("documents/slides/_img-light.png"), imgD = img("documents/slides/_img-dark.png");
  s = pres.addSlide({masterName: "FS Image"});
  s.addText("Image and caption", {placeholder: "title", align: "left"});
  s.addImage({placeholder: "pic", data: imgL, x: M, y: 1.55, w: 8.0, h: 4.5});
  s.addText([{text: "Figure 1", options: {bold: true, color: C.void, breakLine: true}}, {text: "What the image shows and why it matters. Right-click the picture → Change Picture to use your own."}],
            {placeholder: "caption", fontSize: 16});
  // full-bleed image
  s = pres.addSlide({masterName: "FS Full Image"});
  s.addImage({placeholder: "pic", data: imgD, x: 0, y: 0, w: W, h: H});
  s.addText("Full-bleed image", {placeholder: "title", align: "left"});
  s.addText("Static fire, test stand 2 · photo credit", {placeholder: "caption"});
  // table
  s = pres.addSlide({masterName: "FS Content"});
  s.addText("Table", {placeholder: "title", align: "left"});
  const th = t => ({text: t, options: {bold: true, color: C.paper, fill: {color: C.void}, fontFace: HEAD, fontSize: 14}});
  const rows = [[th("Parameter"), th("Target"), th("Measured"), th("Status")],
                ["Total impulse", "2,560 N·s", "2,611 N·s", "Pass"], ["Burn time", "3.2 s", "3.4 s", "Pass"],
                ["Peak thrust", "1,100 N", "1,182 N", "Check"], ["Dry mass", "1.85 kg", "1.79 kg", "Pass"]];
  s.addTable(rows.map((r, i) => i === 0 ? r : r.map((c, j) => ({text: c, options: {color: j === 3 && c === "Check" ? C.ember : C.void,
                fontFace: j ? HEAD : BODY, bold: j === 3, fill: {color: i % 2 ? C.white : C.paper}}}))),
             {x: M, y: 1.6, w: 12.1, colW: [4.0, 2.7, 2.7, 2.7], fontSize: 16, rowH: 0.62, border: {type: "solid", color: C.mist, pt: 1}, valign: "middle", margin: [0, 0.15, 0, 0.15]});
  // chart
  s = pres.addSlide({masterName: "FS Content"});
  s.addText("Chart", {placeholder: "title", align: "left"});
  s.addChart(pres.charts.BAR, [{name: "Predicted", labels: ["Flight 1", "Flight 2", "Flight 3", "Flight 4"], values: [1520, 1780, 2210, 2450]},
                               {name: "Measured", labels: ["Flight 1", "Flight 2", "Flight 3", "Flight 4"], values: [1475, 1810, 2105, 2390]}],
             {x: M, y: 1.5, w: 12.1, h: 4.9, barDir: "col", barGapWidthPct: 60, chartColors: [C.ion, C.m],
              catAxisLabelFontFace: HEAD, catAxisLabelFontSize: 12, catAxisLabelColor: C.slate, valAxisLabelFontFace: HEAD, valAxisLabelFontSize: 12,
              valAxisLabelColor: C.slate, valGridLine: {color: C.mist, size: 1}, catAxisLineShow: false, valAxisLineShow: false,
              showLegend: true, legendPos: "t", legendFontFace: BODY, legendFontSize: 14, legendColor: C.void,
              showValAxisTitle: true, valAxisTitle: "Apogee (m)", valAxisTitleFontFace: BODY, valAxisTitleFontSize: 12, valAxisTitleColor: C.slate});
  s.addNotes("Chart colours: Ion and M orange on light. Edit the data in PowerPoint (right-click → Edit Data).");
  // 5 · stat callouts on light
  s = pres.addSlide({masterName: "FS Content"});
  s.addText("Key numbers", {placeholder: "title", align: "left"});
  [["212 s", "specific impulse"], ["2.1 MPa", "chamber pressure"], ["18.4 mm", "throat diameter"]].forEach(([v, l], i) => {
    const x = M + i * 4.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {x, y: 1.7, w: 3.8, h: 2.6, fill: {color: C.white}, line: {color: C.mist, width: 1}, rectRadius: 0.08});
    s.addText(v, {x: x + 0.3, y: 2.0, w: 3.2, h: 1.0, fontFace: HEAD, fontSize: 40, bold: true, color: i % 2 ? C.ember : C.ion, margin: 0, isTextBox: true});
    s.addText(l, {x: x + 0.3, y: 3.1, w: 3.2, h: 0.5, fontFace: BODY, fontSize: 16, color: C.slate, margin: 0, isTextBox: true});
  });
  // timeline
  s = pres.addSlide({masterName: "FS Content"});
  s.addText("Timeline", {placeholder: "title", align: "left"});
  const ms = [["MAR", "Design review"], ["MAY", "Static fire"], ["JUL", "First flight"], ["SEP", "Recovery test"], ["NOV", "Level 3 flight"]];
  const grad = ["DA7C30", "D07D7A", "B983A4", "A188CB", "768DF5"];
  const TX = M + 1.1, TW = W - 2 * M - 2.2;            // keep the end labels inside the slide
  s.addShape(pres.shapes.LINE, {x: TX, y: 3.35, w: TW, h: 0, line: {color: C.mist, width: 2}});
  ms.forEach(([d, t], i) => {
    const x = TX + i * (TW / 4);
    s.addShape(pres.shapes.OVAL, {x: x - 0.14, y: 3.21, w: 0.28, h: 0.28, fill: {color: grad[i]}, line: {color: C.paper, width: 2}});
    s.addText(d, {x: x - 1.2, y: 2.45, w: 2.4, h: 0.5, fontFace: HEAD, fontSize: 18, bold: true, color: C.void, align: "center", margin: 0, isTextBox: true});
    s.addText(t, {x: x - 1.2, y: 3.75, w: 2.4, h: 0.8, fontFace: BODY, fontSize: 16, color: C.slate, align: "center", valign: "top", margin: 0, isTextBox: true});
  });
  s.addNotes("Timeline: five milestones; the dots step along the Fusion gradient.");
  // code
  s = pres.addSlide({masterName: "FS Dark Content"});
  s.addText("Code", {placeholder: "title", align: "left"});
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {x: M, y: 1.55, w: 12.1, h: 4.7, fill: {color: C.abyss}, line: {color: C.graphite, width: 1}, rectRadius: 0.06});
  const code = [["// thrust curve: integrate to total impulse", C.haze], ["double total_impulse(const double *t, const double *f, size_t n) {", C.paper],
                ["    double sum = 0.0;", C.paper], ["    for (size_t i = 1; i < n; i++)", C.paper],
                ["        sum += 0.5 * (f[i] + f[i - 1]) * (t[i] - t[i - 1]);", C.paper], ["    return sum;   /* N·s */", C.paper], ["}", C.paper]];
  s.addText(code.map(([t, c], i) => ({text: t, options: {color: c, breakLine: i < code.length - 1}})),
            {x: M + 0.35, y: 1.85, w: 11.4, h: 4.1, fontFace: HEAD, fontSize: 18, valign: "top", margin: 0, isTextBox: true, paraSpaceAfter: 4});
  s.addNotes("Code: Cascadia Mono on Abyss. Paste code as plain text and keep it under about 12 lines.");
  // quote
  s = pres.addSlide({masterName: "FS Closing"});
  const ql = TAGLINE.split(/(?<=\.) /);              // one sentence per line
  s.addText(ql.map((t, i) => ({text: (i ? "" : "“") + t + (i === ql.length - 1 ? "”" : ""), options: {breakLine: i < ql.length - 1}})), {x: M + 0.6, y: 2.0, w: W - 2 * M - 1.2, h: 1.9, fontFace: HEAD, fontSize: 40, bold: true, color: C.paper, margin: 0, isTextBox: true, valign: "middle"});
  s.addShape(pres.shapes.RECTANGLE, {x: M + 0.6, y: 4.15, w: 1.2, h: 0.06, fill: {color: C.o}, line: {color: C.o, width: 0}});
  s.addText("Name, role · source", {x: M + 0.6, y: 4.4, w: 8, h: 0.4, fontFace: BODY, fontSize: 18, color: C.haze, margin: 0, isTextBox: true});
  s.addNotes("Quote or key statement: one sentence, set large.");
  // closing
  s = pres.addSlide({masterName: "FS Closing"});
  s.addImage({data: logoC, x: (W - 5.2) / 2, y: 2.6, w: 5.2, h: 5.2 * LR});
  s.addText("Thank you", {x: 0, y: 4.1, w: W, h: 0.6, fontFace: HEAD, fontSize: 24, color: C.paper, align: "center", margin: 0, isTextBox: true});
  s.addText(`${EMAIL} · ${SITE}`, {x: 0, y: 4.75, w: W, h: 0.4, fontFace: HEAD, fontSize: 14, color: C.o, align: "center", margin: 0, isTextBox: true});
  const out = P("documents/slides/fusionspace-slides.pptx");
  await pres.writeFile({fileName: out});
  await setTheme(out);
}

// Reproducible Office files: fixed dates in docProps/core.xml and on every zip entry (SOURCE_DATE_EPOCH, set by build.py),
// so a rebuild only changes a file when its content changes.
const FIXED = new Date(1000 * Number(process.env.SOURCE_DATE_EPOCH || 1790812800));
async function fixZip(buf) {
  const JSZip = require(require.resolve("jszip", {paths: [path.dirname(require.resolve("pptxgenjs"))]}));
  const zip = await JSZip.loadAsync(buf), out = new JSZip(), iso = FIXED.toISOString().replace(/\.\d+Z$/, "Z");
  for (const name of Object.keys(zip.files).sort()) {
    const f = zip.files[name]; if (f.dir) continue;
    let data = await f.async("nodebuffer");
    if (name === "docProps/core.xml") data = Buffer.from(data.toString("utf8").replace(/(<dcterms:(?:created|modified)[^>]*>)[^<]*/g, `$1${iso}`));
    if (/\.(xlsx|docx|pptx)$/.test(name)) data = await fixZip(data);      // embedded files (a chart's workbook) carry dates too
    out.file(name, data, {date: FIXED, createFolders: false});
  }
  return out.generateAsync({type: "nodebuffer", compression: "DEFLATE"});
}
async function fixDates(file) { fs.writeFileSync(file, await fixZip(fs.readFileSync(file))); }

// Write the brand colours and fonts into the deck's theme (pptxgenjs can't): dk1 Void, lt1 White, dk2 Abyss, lt2 Paper,
// accents Ion, Ember, O blue, M orange, Slate, Haze.
async function setTheme(file) {
  const JSZip = require(require.resolve("jszip", {paths: [path.dirname(require.resolve("pptxgenjs"))]}));
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const name = Object.keys(zip.files).find(n => /^ppt\/theme\/theme\d+\.xml$/.test(n));
  let x = await zip.file(name).async("string");
  const set = (tag, hex) => { x = x.replace(new RegExp(`<a:${tag}>[\\s\\S]*?</a:${tag}>`), `<a:${tag}><a:srgbClr val="${hex}"/></a:${tag}>`); };
  set("dk1", C.void); set("lt1", C.white); set("dk2", C.abyss); set("lt2", C.paper);
  set("accent1", C.ion); set("accent2", C.ember); set("accent3", C.o); set("accent4", C.m); set("accent5", C.slate); set("accent6", C.haze);
  set("hlink", C.ion); set("folHlink", C.slate);
  x = x.replace(/<a:clrScheme name="[^"]*">/, '<a:clrScheme name="FusionSpace">');
  zip.file(name, x);
  fs.writeFileSync(file, await zip.generateAsync({type: "nodebuffer", compression: "DEFLATE"}));
  await fixDates(file);
}

// ------------------------------------------------------------------ letterhead (.docx)
async function letterhead(page) {
  const d = require("docx");
  const size = page === "letter" ? {width: 12240, height: 15840} : {width: 11906, height: 16838};
  const logo = fs.readFileSync(P("logo/png/fusion-space-horizontal-color-1000w.png"));
  const pngSize = b => [b.readUInt32BE(16), b.readUInt32BE(20)];
  const [lwpx, lhpx] = pngSize(logo);
  const logoW = 180, logoH = Math.round(logoW * lhpx / lwpx);     // points-ish (docx uses pixels at 96 dpi)
  const mono = (t, o = {}) => new d.TextRun({text: t, font: HEAD, size: 16, color: C.slate, ...o});
  const doc = new d.Document({
    creator: "Neer Patel", title: "FusionSpace letterhead",
    styles: {default: {document: {run: {font: BODY, size: 22, color: C.void}}}},
    sections: [{
      properties: {page: {size, margin: {top: 1900, bottom: 1500, left: 1134, right: 1134, header: 600, footer: 600}}},
      headers: {default: new d.Header({children: [
        new d.Paragraph({children: [new d.ImageRun({type: "png", data: logo, transformation: {width: logoW, height: logoH},
                                                     altText: {title: "FusionSpace", description: "FusionSpace logo", name: "logo"}})]}),
        new d.Paragraph({alignment: d.AlignmentType.RIGHT, spacing: {before: 0}, children: [mono("FS-VEGA · LETTER · REV A", {color: C.ion})]}),
      ]})},
      footers: {default: new d.Footer({children: [
        new d.Paragraph({border: {top: {style: d.BorderStyle.SINGLE, size: 4, color: C.mist, space: 6}},
                         children: [mono("FUSIONSPACE · " + TAGLINE.toUpperCase())]}),
        new d.Paragraph({children: [mono(`${EMAIL} · ${SITE} · ${GITHUB}`)]}),
      ]})},
      children: [
        new d.Paragraph({children: [new d.TextRun(new Date().toLocaleDateString("en-GB", {day: "numeric", month: "long", year: "numeric"}))], spacing: {after: 240}}),
        new d.Paragraph({children: [new d.TextRun("Recipient name")]}),
        new d.Paragraph({children: [new d.TextRun("Organisation")]}),
        new d.Paragraph({children: [new d.TextRun("Address")], spacing: {after: 360}}),
        new d.Paragraph({children: [new d.TextRun("Dear Recipient,")], spacing: {after: 200}}),
        new d.Paragraph({children: [new d.TextRun("Body text is Archivo 11 pt. Replace this paragraph with your letter. The header and footer repeat on every page; edit the reference line and contact details there once.")], spacing: {after: 200, line: 300}}),
        new d.Paragraph({children: [new d.TextRun("Kind regards,")], spacing: {before: 200, after: 600}}),
        new d.Paragraph({children: [new d.TextRun({text: "Neer Patel", font: HEAD, bold: true})]}),
        new d.Paragraph({children: [new d.TextRun({text: ROLE, color: C.slate, size: 20})]}),
      ],
    }],
  });
  fs.mkdirSync(P("documents/letterhead"), {recursive: true});
  fs.writeFileSync(P(`documents/letterhead/letterhead-${page}.docx`), await d.Packer.toBuffer(doc)); await fixDates(P(`documents/letterhead/letterhead-${page}.docx`));
}

// ------------------------------------------------------------------ report / technical document (.docx)
async function report(page) {
  const d = require("docx");
  const size = page === "letter" ? {width: 12240, height: 15840} : {width: 11906, height: 16838};
  const contentW = size.width - 2 * 1134;
  const logo = fs.readFileSync(P("logo/png/fusion-space-horizontal-color-1000w.png"));
  const [lw, lh] = [logo.readUInt32BE(16), logo.readUInt32BE(20)];
  const mono = (t, o = {}) => new d.TextRun({text: t, font: HEAD, ...o});
  const cell = (t, head) => new d.TableCell({
    width: {size: Math.round(contentW / 3), type: d.WidthType.DXA},
    shading: head ? {type: d.ShadingType.CLEAR, color: "auto", fill: C.void} : undefined,
    margins: {top: 80, bottom: 80, left: 120, right: 120},
    children: [new d.Paragraph({children: [head ? mono(t, {bold: true, color: C.paper, size: 18}) : new d.TextRun({text: t, size: 20})]})]});
  const rows = [["Requirement", "Value", "Status"], ["Mass", "1.2 kg", "Met"], ["Telemetry rate", "50 Hz", "Met"], ["Battery life", "4 h", "Open"]];
  const doc = new d.Document({
    creator: "Neer Patel", title: "FusionSpace report template",
    styles: {
      default: {document: {run: {font: BODY, size: 21, color: C.void}, paragraph: {spacing: {after: 120, line: 288, lineRule: d.LineRuleType.AUTO}}}},
      paragraphStyles: [
        {id: "Title", name: "Title", basedOn: "Normal", run: {font: HEAD, size: 56, bold: true, color: C.void}, paragraph: {spacing: {after: 120}}},
        {id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: {font: HEAD, size: 32, bold: true, color: C.void}, paragraph: {spacing: {before: 360, after: 120}, outlineLevel: 0}},
        {id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: {font: HEAD, size: 24, bold: true, color: C.void}, paragraph: {spacing: {before: 240, after: 80}, outlineLevel: 1}},
        {id: "Caption", name: "Caption", basedOn: "Normal", run: {font: HEAD, size: 16, color: C.slate}, paragraph: {spacing: {before: 60, after: 240}}},
        {id: "Code", name: "Code", basedOn: "Normal", run: {font: HEAD, size: 18, color: C.void}, paragraph: {shading: {type: d.ShadingType.CLEAR, color: "auto", fill: C.paper}, spacing: {after: 0}}},
      ]},
    sections: [
      {properties: {page: {size, margin: {top: 1134, bottom: 1134, left: 1134, right: 1134}}},
       children: [
         new d.Paragraph({children: [new d.ImageRun({type: "png", data: logo, transformation: {width: 220, height: Math.round(220 * lh / lw)}, altText: {title: "FusionSpace", description: "FusionSpace logo", name: "logo"}})], spacing: {after: 3600, line: 240, lineRule: d.LineRuleType.AUTO}}),
         new d.Paragraph({children: [mono("FS-VEGA · REPORT 001 · REV A", {color: C.ion, size: 20})]}),
         new d.Paragraph({style: "Title", children: [new d.TextRun("Report title")]}),
         new d.Paragraph({children: [new d.TextRun({text: "A one-line subtitle for this document.", size: 26, color: C.slate})], spacing: {after: 2400}}),
         new d.Paragraph({children: [mono("NEER PATEL · " + ROLE.toUpperCase(), {size: 16, color: C.slate})]}),
         new d.Paragraph({children: [mono(new Date().toLocaleDateString("en-GB", {day: "numeric", month: "long", year: "numeric"}).toUpperCase(), {size: 16, color: C.slate})]}),
       ]},
      {properties: {page: {size, margin: {top: 1600, bottom: 1400, left: 1134, right: 1134, header: 600, footer: 600}}},
       headers: {default: new d.Header({children: [new d.Paragraph({tabStops: [{type: d.TabStopType.RIGHT, position: contentW}],
         children: [mono("FusionSpace", {size: 16, color: C.slate}), mono("\tFS-VEGA · REPORT 001 · REV A", {size: 16, color: C.slate})]})]})},
       footers: {default: new d.Footer({children: [new d.Paragraph({alignment: d.AlignmentType.RIGHT, children: [new d.TextRun({children: [d.PageNumber.CURRENT], font: HEAD, size: 16, color: C.slate})]})]})},
       children: [
         new d.Paragraph({heading: d.HeadingLevel.HEADING_1, children: [new d.TextRun("1  Summary")]}),
         new d.Paragraph({children: [new d.TextRun("Body text is Archivo 10.5 pt. Headings, captions and code use Cascadia Mono. Replace this text; the styles (Heading 1, Heading 2, Caption, Code) are set up in the document, so Word's navigation pane and table of contents work.")]}),
         new d.Paragraph({heading: d.HeadingLevel.HEADING_2, children: [new d.TextRun("1.1  Requirements")]}),
         new d.Table({width: {size: contentW, type: d.WidthType.DXA}, columnWidths: [1, 2, 3].map(() => Math.round(contentW / 3)),
           rows: rows.map((r, i) => new d.TableRow({tableHeader: i === 0, children: r.map(t => cell(t, i === 0))}))}),
         new d.Paragraph({style: "Caption", children: [new d.TextRun("TABLE 1 · REQUIREMENTS AND STATUS")]}),
         new d.Paragraph({heading: d.HeadingLevel.HEADING_2, children: [new d.TextRun("1.2  Code")]}),
         ...["void fs_boot_logo(void) {", "    display_draw_bitmap(0, 0, fs_logo_oled_128x64_gfx, 128, 64);", "}"].map(l => new d.Paragraph({style: "Code", children: [new d.TextRun(l)]})),
         new d.Paragraph({heading: d.HeadingLevel.HEADING_1, children: [new d.TextRun("2  Design")]}),
         new d.Paragraph({children: [new d.TextRun("Continue here.")]}),
       ]},
    ],
  });
  fs.mkdirSync(P("documents/report"), {recursive: true});
  fs.writeFileSync(P(`documents/report/report-template-${page}.docx`), await d.Packer.toBuffer(doc)); await fixDates(P(`documents/report/report-template-${page}.docx`));
}

(async () => {
  await slides();
  await letterhead("letter"); await letterhead("a4");
  await report("letter"); await report("a4");
  console.log("office ok");
})().catch(e => { console.error(e); process.exit(1); });
