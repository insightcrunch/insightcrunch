---
layout: post
title: "OBIEE Dashboard Export to Excel PDF HTML using Custom Links"
date: 2017-05-24
categories: ["Analytics"]
tags: ["OBIEE"]
excerpt: "Oracle Business Intelligence Application in it's out of the box form do not provide any solution to export a dashboard from another dashboard using custom links. But given the available resources, it ..."
image: "/assets/images/technology-industry-analysis-insightcrunch.webp"
reading_time: 1
author: "Insight Crunch Team"
---

Oracle Business Intelligence Application in it's out of the box form do not provide any solution to export a dashboard from another dashboard using custom links. But given the available resources, it is possible to create custom links to export a dashboard in Excel format, PDF format, or HTML format. To do this we need to create few snippets of HTML and Javascript coding, and can add some cool animations as well if need be.

![OBIEE Dashboard Export to Excel PDF HTML using Custom Links](/assets/images/technology-industry-analysis-insightcrunch.webp)
OBIEE Dashboard Export to Excel PDF HTML using Custom Links

To achieve our goal, we first need to have the name of the dashboard and the tab which we will be using to create our extracts. Once that is ready, the below HTML and Javascript codes will help create few export links that will extract exactly what we want.

```
<blockquote class="tr_bq">
<div id="exports_hdr">
<span style="color: mediumblue; font-size: small;">
<u>
<b>
Export
</b>
</u>
</span>
</div>

<div id="exports_dtls" style="display: none;"><img style="vertical-align: middle; margin: 0 0 0 5px;" src="res/sk_blafp/catalog/exporttoexcel_ena.png" alt="">&lt;a name="ReportLinkMenu" title="Export to different format" href="javascript:void(null)" onclick="return saw.dashboard.exportToExcel('&lt;&gt;', '&lt;&gt;', true);"&gt;<span style="color: mediumblue; font-size: small;">
<b>Excel 2007+</b></span><br><img style="vertical-align: middle; margin: 0 0 0 5px;" src="res/sk_blafp/catalog/printtopdf_ena.png" alt="">&lt;a name="ReportLinkMenu" title="Export to different format" href="javascript:void(null)" onclick="return PortalPrint('&lt;&gt;', '&lt;&gt;', true, 'pdf');"&gt;<span style="color: mediumblue; font-size: small;">
<b>PDF</b></span><br><img style="vertical-align: middle; margin: 0 0 0 5px;" src="res/sk_blafp/catalog/printtohtml_ena.png" alt="">&lt;a name="ReportLinkMenu" title="Export to different format" href="javascript:void(null)" onclick="return PortalPrint('&lt;&gt;', '&lt;&gt;', true, 'html');"&gt;<span style="color: mediumblue; font-size: small;">
<b>HTML</b></span></div></blockquote>
```

Once this is working fine, it will show a cool 'Export' link, and when we do a mouse hover it will instantly show three Export links for Excel format, PDF format, and HTML format.

Let me know if you have any other ideas to export in different formats!