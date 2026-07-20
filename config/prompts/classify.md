---
version: 1
role: link-classification prompt — stage S5 (PIPE-5), JSON mode
---
Do not use web search. Work only from what's given.

Below are news items. Each has: title,  article URL, and a
list of links. Classify every link into exactly one of four categories, based
on the URL plus the item's title and article URL:

- EXT   external page, related to this item (source doc, org, cited article, wiki)
- INT   internal page on the same domain, related to this item
        (earlier/related article)
- NAV   domain navigation: section, breadcrumb, tag, hub, or dossier page
        (whether or not it's on-topic)
- PROMO subscription, trial, ads, newsletter, tickets, follow-us
