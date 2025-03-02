# middlewares.py

import random
from scrapy import signals
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware


class RandomUserAgentMiddleware(UserAgentMiddleware):
    """
    Middleware that assigns a random User-Agent string to each request.
    Inherits from Scrapy's built-in UserAgentMiddleware.
    """

    def __init__(self, settings, user_agent='Scrapy'):
        """
        Initialize the middleware and store the user agent list from settings.

        Args:
            settings (scrapy.settings.Settings): Scrapy settings object.
            user_agent (str): Default user agent to use if no list is provided.
        """
        # Call the parent constructor
        super(RandomUserAgentMiddleware, self).__init__()

        # Attempt to retrieve a custom list of user agents from settings;
        # if not found, store a default list with one entry.
        self.user_agent_list = settings.get('USER_AGENT_LIST', [user_agent])

    @classmethod
    def from_crawler(cls, crawler):
        """
        Create a middleware instance using the crawler settings and
        connect the spider_opened signal.

        Args:
            crawler (scrapy.crawler.Crawler): The Scrapy crawler instance.

        Returns:
            RandomUserAgentMiddleware: The middleware instance.
        """
        # Instantiate the middleware with settings
        instance = cls(crawler.settings)

        # Connect the spider_opened signal if needed
        crawler.signals.connect(instance.spider_opened, signal=signals.spider_opened)
        return instance

    def process_request(self, request, spider):
        """
        Assign a random User-Agent header to each outgoing request.

        Args:
            request (scrapy.http.Request): The request object.
            spider (scrapy.spiders.Spider): The active spider instance.
        """
        # Choose a random user agent from the list
        user_agent = random.choice(self.user_agent_list)

        # Set the User-Agent header if it is not already defined
        request.headers.setdefault('User-Agent', user_agent)


class ProxyMiddleware:
    """
    Middleware that assigns a random proxy address to each request.
    """

    def __init__(self, proxies):
        """
        Initialize the middleware with a list of proxy addresses.

        Args:
            proxies (list): A list of proxy addresses to randomly choose from.
        """
        super(ProxyMiddleware, self).__init__()
        self.proxies = proxies

    @classmethod
    def from_crawler(cls, crawler):
        """
        Create a middleware instance using the crawler settings.
        Retrieves a list of proxies from settings or defaults to a static list.

        Args:
            crawler (scrapy.crawler.Crawler): The Scrapy crawler instance.

        Returns:
            ProxyMiddleware: The middleware instance.
        """
        # Try to read a list of proxies from settings; if not found, fall back to a default list
        proxy_list = crawler.settings.get('PROXY_LIST', [
            "https://67.43.228.251:14791",
            "https://13.36.113.81:3128",
        ])
        return cls(proxy_list)

    def process_request(self, request, spider):
        """
        Attach a random proxy address to each request before it is sent.

        Args:
            request (scrapy.http.Request): The request object.
            spider (scrapy.spiders.Spider): The active spider instance.
        """
        # Pick a random proxy from the self.proxies list
        proxy = random.choice(self.proxies)

        # Set the 'proxy' meta key so Scrapy routes the request through the chosen proxy
        request.meta['proxy'] = proxy
