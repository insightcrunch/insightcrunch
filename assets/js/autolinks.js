/*  InsightCrunch Auto-Linker
 *  Scans .post-content for brand/product mentions and wraps the FIRST
 *  plain-text occurrence of each in an <a> tag so Skimlinks can affiliate it.
 *  -  Runs once on DOMContentLoaded (before Skimlinks fires).
 *  -  Never touches text already inside an <a>, <code>, <pre>, or <script>.
 *  -  Case-insensitive matching, preserves original casing in output.
 *  -  Only links first occurrence per brand per page to keep it natural.
 *
 *  To add a new brand: just add a row to the BRANDS array below.
 *  Format: [matchPattern, url]
 *    - matchPattern: string (exact) or regex
 *    - url: destination URL (Skimlinks rewrites it automatically)
 */

(function () {
  'use strict';

  // ── BRAND MAP ─────────────────────────────────────────────────
  // [displayPattern, destinationURL]
  // Ordered longest-first so "Google Docs" matches before "Google"
  var BRANDS = [

    // ── AI / Productivity Tools ──
    ['ChatGPT Plus',          'https://openai.com/chatgpt/pricing'],
    ['ChatGPT',               'https://chat.openai.com'],
    ['OpenAI',                'https://openai.com'],
    ['Claude',                'https://claude.ai'],
    ['Google Gemini',         'https://gemini.google.com'],
    ['Microsoft Copilot',     'https://copilot.microsoft.com'],
    ['Perplexity AI',         'https://www.perplexity.ai'],
    ['Perplexity',            'https://www.perplexity.ai'],
    ['Grammarly',             'https://www.grammarly.com'],
    ['QuillBot',              'https://quillbot.com'],
    ['Hemingway Editor',      'https://hemingwayapp.com'],
    ['Hemingway App',         'https://hemingwayapp.com'],
    ['Jasper AI',             'https://www.jasper.ai'],
    ['Copy.ai',               'https://www.copy.ai'],
    ['Writesonic',            'https://writesonic.com'],

    // ── Note-Taking / Organisation ──
    ['Notion AI',             'https://www.notion.so/product/ai'],
    ['Notion',                'https://www.notion.so'],
    ['Obsidian',              'https://obsidian.md'],
    ['Evernote',              'https://evernote.com'],
    ['Microsoft OneNote',     'https://www.onenote.com'],
    ['OneNote',               'https://www.onenote.com'],
    ['Google Keep',           'https://keep.google.com'],
    ['Apple Notes',           'https://www.icloud.com/notes'],
    ['Roam Research',         'https://roamresearch.com'],
    ['Logseq',                'https://logseq.com'],
    ['Bear App',              'https://bear.app'],

    // ── Transcription / Audio ──
    ['Otter.ai',              'https://otter.ai'],
    ['Otter AI',              'https://otter.ai'],
    ['Rev.com',               'https://www.rev.com'],
    ['Descript',              'https://www.descript.com'],
    ['Fireflies.ai',         'https://fireflies.ai'],

    // ── Study / Flashcards ──
    ['Anki',                  'https://apps.ankiweb.net'],
    ['Quizlet',               'https://quizlet.com'],
    ['Brainscape',            'https://www.brainscape.com'],
    ['RemNote',               'https://www.remnote.com'],

    // ── Research ──
    ['Semantic Scholar',      'https://www.semanticscholar.org'],
    ['Zotero',                'https://www.zotero.org'],
    ['Mendeley',              'https://www.mendeley.com'],
    ['Elicit',                'https://elicit.com'],
    ['Consensus',             'https://consensus.app'],
    ['Connected Papers',      'https://www.connectedpapers.com'],
    ['Google Scholar',        'https://scholar.google.com'],
    ['SciSpace',              'https://scispace.com'],

    // ── Design / Creative ──
    ['Canva',                 'https://www.canva.com'],
    ['Figma',                 'https://www.figma.com'],
    ['Adobe Creative Cloud',  'https://www.adobe.com/creativecloud.html'],
    ['Adobe Photoshop',       'https://www.adobe.com/products/photoshop.html'],
    ['Adobe Premiere',        'https://www.adobe.com/products/premiere.html'],

    // ── Online Learning Platforms ──
    ['Coursera',              'https://www.coursera.org'],
    ['Udemy',                 'https://www.udemy.com'],
    ['edX',                   'https://www.edx.org'],
    ['Skillshare',            'https://www.skillshare.com'],
    ['Khan Academy',          'https://www.khanacademy.org'],
    ['LinkedIn Learning',     'https://www.linkedin.com/learning'],
    ['Codecademy',            'https://www.codecademy.com'],
    ['freeCodeCamp',          'https://www.freecodecamp.org'],
    ['Pluralsight',           'https://www.pluralsight.com'],
    ['Udacity',               'https://www.udacity.com'],
    ['Brilliant',             'https://brilliant.org'],
    ['MasterClass',           'https://www.masterclass.com'],
    ['Unacademy',             'https://unacademy.com'],
    ['BYJU\'S',              'https://byjus.com'],
    ['Vedantu',               'https://www.vedantu.com'],
    ['Testbook',              'https://testbook.com'],
    ['Magoosh',               'https://magoosh.com'],

    // ── Coding / Dev Tools ──
    ['LeetCode',              'https://leetcode.com'],
    ['HackerRank',            'https://www.hackerrank.com'],
    ['AlgoExpert',            'https://www.algoexpert.io'],
    ['Educative.io',          'https://www.educative.io'],
    ['Educative',             'https://www.educative.io'],
    ['GitHub',                'https://github.com'],
    ['VS Code',               'https://code.visualstudio.com'],
    ['Visual Studio Code',    'https://code.visualstudio.com'],
    ['Replit',                'https://replit.com'],
    ['CodePen',               'https://codepen.io'],
    ['GeeksforGeeks',         'https://www.geeksforgeeks.org'],
    ['InterviewBit',          'https://www.interviewbit.com'],

    // ── Freelancing / Gig Platforms ──
    ['Fiverr',                'https://www.fiverr.com'],
    ['Upwork',                'https://www.upwork.com'],
    ['Toptal',                'https://www.toptal.com'],
    ['Freelancer.com',        'https://www.freelancer.com'],

    // ── E-Commerce / Selling ──
    ['Amazon',                'https://www.amazon.com'],
    ['Shopify',               'https://www.shopify.com'],
    ['Etsy',                  'https://www.etsy.com'],
    ['Gumroad',               'https://gumroad.com'],
    ['Teachable',             'https://teachable.com'],
    ['Thinkific',             'https://www.thinkific.com'],
    ['Amazon KDP',            'https://kdp.amazon.com'],

    // ── Finance / Investment (India) ──
    ['Zerodha',               'https://zerodha.com'],
    ['Groww',                 'https://groww.in'],
    ['Kuvera',                'https://kuvera.in'],
    ['INDmoney',              'https://www.indmoney.com'],
    ['Smallcase',             'https://www.smallcase.com'],
    ['ET Money',              'https://www.etmoney.com'],

    // ── Math / Science Tools ──
    ['Wolfram Alpha',         'https://www.wolframalpha.com'],
    ['WolframAlpha',          'https://www.wolframalpha.com'],
    ['Desmos',                'https://www.desmos.com'],
    ['Symbolab',              'https://www.symbolab.com'],
    ['GeoGebra',              'https://www.geogebra.org'],
    ['MATLAB',                'https://www.mathworks.com/products/matlab.html'],
    ['Photomath',             'https://photomath.com'],

    // ── Exam Prep (India specific) ──
    ['Toppers Academy',       'https://www.toppersacademy.com'],
    ['Drishti IAS',           'https://www.drishtiias.com'],
    ['Vision IAS',            'https://www.visionias.in'],
    ['ClearIAS',              'https://www.clearias.com'],
    ['InsightsIAS',           'https://www.insightsonindia.com'],

    // ── SAT / US College Prep ──
    ['College Board',         'https://www.collegeboard.org'],
    ['Princeton Review',      'https://www.princetonreview.com'],
    ['Kaplan',                'https://www.kaplan.com'],
    ['PrepScholar',           'https://www.prepscholar.com'],
    ['Barron\'s',             'https://www.barrons.com'],

    // ── IELTS / TOEFL ──
    ['British Council',       'https://www.britishcouncil.org'],
    ['ETS',                   'https://www.ets.org'],
    ['IELTS Liz',             'https://ieltsliz.com'],
    ['Duolingo',              'https://www.duolingo.com'],

    // ── Project Management / Collaboration ──
    ['Trello',                'https://trello.com'],
    ['Asana',                 'https://asana.com'],
    ['Monday.com',            'https://monday.com'],
    ['ClickUp',               'https://clickup.com'],
    ['Slack',                 'https://slack.com'],
    ['Discord',               'https://discord.com'],
    ['Zoom',                  'https://zoom.us'],
    ['Google Meet',           'https://meet.google.com'],
    ['Microsoft Teams',       'https://www.microsoft.com/en-us/microsoft-teams'],

    // ── Cloud / Productivity Suites ──
    ['Google Workspace',      'https://workspace.google.com'],
    ['Google Docs',           'https://docs.google.com'],
    ['Google Sheets',         'https://sheets.google.com'],
    ['Google Slides',         'https://slides.google.com'],
    ['Google Drive',          'https://drive.google.com'],
    ['Microsoft 365',         'https://www.microsoft.com/en-us/microsoft-365'],
    ['Microsoft Word',        'https://www.microsoft.com/en-us/microsoft-365/word'],
    ['Microsoft Excel',       'https://www.microsoft.com/en-us/microsoft-365/excel'],
    ['Microsoft PowerPoint',  'https://www.microsoft.com/en-us/microsoft-365/powerpoint'],
    ['Dropbox',               'https://www.dropbox.com'],

    // ── Resume / Career ──
    ['LinkedIn',              'https://www.linkedin.com'],
    ['Indeed',                'https://www.indeed.com'],
    ['Glassdoor',             'https://www.glassdoor.com'],
    ['Naukri',                'https://www.naukri.com'],
    ['Resume.io',             'https://resume.io'],
    ['Novoresume',            'https://novoresume.com'],
    ['Zety',                  'https://zety.com'],

    // ── VPN / Privacy ──
    ['NordVPN',               'https://nordvpn.com'],
    ['ExpressVPN',            'https://www.expressvpn.com'],
    ['Surfshark',             'https://surfshark.com'],
    ['ProtonVPN',             'https://protonvpn.com'],

    // ── Password Managers ──
    ['1Password',             'https://1password.com'],
    ['Bitwarden',             'https://bitwarden.com'],
    ['LastPass',              'https://www.lastpass.com'],
    ['Dashlane',              'https://www.dashlane.com'],

    // ── Web Hosting / Domains ──
    ['Namecheap',             'https://www.namecheap.com'],
    ['Cloudflare',            'https://www.cloudflare.com'],
    ['DigitalOcean',          'https://www.digitalocean.com'],
    ['Bluehost',              'https://www.bluehost.com'],
    ['Hostinger',             'https://www.hostinger.com'],
    ['SiteGround',            'https://www.siteground.com'],

    // ── Email Marketing ──
    ['Mailchimp',             'https://mailchimp.com'],
    ['ConvertKit',            'https://convertkit.com'],
    ['Substack',              'https://substack.com'],

    // ── Hardware / Laptops ──
    ['Chromebook',            'https://www.google.com/chromebook'],
    ['MacBook',               'https://www.apple.com/macbook-air'],
    ['iPad',                  'https://www.apple.com/ipad'],
    ['Kindle',                'https://www.amazon.com/kindle']
  ];

  // Tags to skip: never inject a link inside these elements
  var SKIP_TAGS = { A:1, CODE:1, PRE:1, SCRIPT:1, STYLE:1, TEXTAREA:1, INPUT:1, BUTTON:1, SVG:1 };

  // ── helpers ───────────────────────────────────────────────────

  function escapeRe(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function isInsideSkipTag(node) {
    var p = node.parentNode;
    while (p && p !== document) {
      if (SKIP_TAGS[p.tagName]) return true;
      p = p.parentNode;
    }
    return false;
  }

  // ── main ──────────────────────────────────────────────────────

  function run() {
    var container = document.querySelector('.post-content');
    if (!container) return;  // not a post page

    var linked = {};  // track which brands have already been linked

    BRANDS.forEach(function (entry) {
      var term = entry[0];
      var url  = entry[1];

      if (linked[term.toLowerCase()]) return;  // already linked this page

      // Build word-boundary regex for the brand
      var re = new RegExp('(?<![\\w-])(' + escapeRe(term) + ')(?![\\w-])', 'i');

      // Walk all text nodes in .post-content
      var walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null, false);
      var node;
      while (node = walker.nextNode()) {
        if (isInsideSkipTag(node)) continue;

        var match = re.exec(node.nodeValue);
        if (!match) continue;

        // Split the text node and insert an <a> element
        var before   = node.nodeValue.substring(0, match.index);
        var matchTxt = match[1];
        var after    = node.nodeValue.substring(match.index + matchTxt.length);

        var a = document.createElement('a');
        a.href = url;
        a.textContent = matchTxt;
        a.setAttribute('target', '_blank');
        a.setAttribute('rel', 'noopener');

        var parent = node.parentNode;
        if (before) parent.insertBefore(document.createTextNode(before), node);
        parent.insertBefore(a, node);
        if (after) parent.insertBefore(document.createTextNode(after), node);
        parent.removeChild(node);

        linked[term.toLowerCase()] = true;
        break;  // first occurrence only, move to next brand
      }
    });
  }

  // Fire on DOMContentLoaded (before Skimlinks async script loads)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
