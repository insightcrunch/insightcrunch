---
layout: post
title: "Blogger Blog Security: Disable Right Click, Disable Text Selection"
date: 2010-06-20
categories: ["Leisure"]
tags: ["Surfing"]
excerpt: "All of us, into blogging or engaged in online activities, at some time or the other has faced the issue of our images and own articles being copied to other sites without our permission. This causes ..."
image: "/assets/images/technology-industry-analysis-insightcrunch.webp"
reading_time: 1
author: "Insight Crunch Team"
---

All of us, into blogging or engaged in online activities, at some time or the other has faced the issue of our images and own articles being copied to other sites without our permission. This causes annoying to no doubt. So you can at least take steps to minimize it, because we can’t entirely prevent it. Here are some simple ways by which you can protect your blogger blog from plagiarism and from your images being copied away, thus affecting your precious bandwidth.

Read more: [Bing Toolbar and Search Box for Blog »](https://insightcrunch.com/2009/06/01/bing-toolbar-and-search-box-for-blog/)

Just keep these two codes in your website. They will ensure 80% less stealing of your content. Replace the singlequote in red below by a single quote.

## Disable Right Click Code

```
<script>
var isNS = (navigator.appName == "Netscape") ? 1 : 0;
if(navigator.appName == "Netscape") document.captureEvents(Event.MOUSEDOWN||Event.MOUSEUP);
function mischandler(){
return false;
}
function mousehandler(e){
var myevent = (isNS) ? e : event;
var eventbutton = (isNS) ? myevent.which : myevent.button;
if((eventbutton==2)||(eventbutton==3)) return false;
}
document.oncontextmenu = mischandler;
document.onmousedown = mousehandler;
document.onmouseup = mousehandler;
</script>
```

## Disable Text Selection Code

```
<script type="text/javascript">
//form tags to omit in NS6+:
var omitformtags=["input", "textarea", "select"]
omitformtags=omitformtags.join("|")
function disableselect(e){
if (omitformtags.indexOf(e.target.tagName.toLowerCase())==-1)
return false
}
function reEnable(){
return true
}
if (typeof document.onselectstart!="undefined")
document.onselectstart=new Function ("return false")
else{
document.onmousedown=disableselect
document.onmouseup=reEnable
}
</script>    
```

![Disable Text Selection and Right Click Code](https://insightcrunch.com/wp-content/uploads/2010/06/pexels-photo-5926393.jpeg)
Disable Text Selection and Right Click Code