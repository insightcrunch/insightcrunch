---
layout: post
title: "How to Schedule Posts in Jekyll: A Practical Guide"
categories: [Technology]
tags: [jekyll, blogging, workflow]
read_time: 5
---

Jekyll's `future: false` setting combined with GitHub Actions daily builds gives you native scheduled publishing — no plugins required.

<!--more-->

This post is itself an example of scheduling. It's written and committed to the repository today, but dated June 15, 2026. Until that date arrives, the daily GitHub Actions rebuild will silently skip it. On June 15, the scheduled build at 9 AM CDT will include it for the first time.

## How It Works

Set `future: false` in `_config.yml`. This instructs Jekyll to exclude any post whose `date:` front matter is later than the current build time.

Commit your future-dated post. It lives in the repository but doesn't appear on the site.

The GitHub Actions workflow runs on a cron schedule — daily at 9 AM CDT in this setup. Each run is a full rebuild. When the build date finally passes your post's date, it appears automatically.

## Tips for Scheduling

- Date your post exactly: `2026-06-15` will publish on June 15. Jekyll uses midnight of that date in your configured timezone.
- Your `timezone: "America/Chicago"` in `_config.yml` determines how dates are interpreted.
- To publish at a specific time, use the full datetime format: `date: 2026-06-15 09:00:00 -0500`
- The cron schedule controls the earliest possible publish time. A `0 14 * * *` cron (9 AM CDT) means scheduled posts go live within minutes of 9 AM.
