# Insight Crunch

Jekyll-powered blog at [insightcrunch.com](https://insightcrunch.com).

## Setup

```bash
bundle install
bundle exec jekyll serve
```

## Writing Posts

Create a file in `_posts/` named `YYYY-MM-DD-your-title.md` with front matter:

```yaml
---
layout: post
title: "Your Post Title"
categories: [Technology]   # Technology | Society | Life | Analytics | Travel
tags: [tag1, tag2]
read_time: 5               # estimated reading time in minutes
---

Your excerpt ends here — this appears on the home page.

<!--more-->

Rest of the post content...
```

## Scheduling Future Posts

To schedule a post:
1. Name the file with a **future date**: `_posts/2026-09-01-my-future-post.md`
2. Set the `date:` in front matter if you need a specific time
3. Commit and push — the post will be hidden until its date arrives
4. GitHub Actions rebuilds the site daily at 9 AM CDT, automatically publishing scheduled posts

## Categories

- Technology
- Society  
- Life
- Analytics
- Travel

## Theme

Espresso sidebar theme (ic-b). Lora serif + Inter sans-serif fonts.
