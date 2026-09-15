from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'
    protocol = 'https'

    def items(self):
        return ['shop:home', 'shop:product_list', 'shop:about_us', 'shop:contact_us']

    def location(self, item):
        return reverse(item)

    def get_urls(self, page=1, site=None, protocol=None):
        urls = super().get_urls(page, site, protocol=self.protocol)
        for url_info in urls:
            url_info['location'] = url_info['location'].replace('example.com', settings.SITE_DOMAIN)
        return urls