from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        return ['shop:home', 'shop:product_list', 'shop:about_us', 'shop:contact_us']

    def location(self, item):
        return reverse(item)