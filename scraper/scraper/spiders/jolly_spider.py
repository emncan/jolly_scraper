"""
Scrapy spider that integrates with the Selenium driver defined in jolly_selenium.py.
"""

import re
import time
import scrapy
from scrapy.selector import Selector
from selenium.webdriver.common.by import By
from jolly_selenium import JollyTurSeleniumDriver


class JollySpider(scrapy.Spider):
    """
    A Scrapy spider that uses the JollyTurSeleniumDriver to interact with jollytur.com,
    select dates, adjust adult counts, and scroll through results.
    """

    name = "jolly"
    allowed_domains = ["jollytur.com"]
    custom_settings = {
        "LOG_LEVEL": "INFO"
    }

    def __init__(
        self,
        destination="Ölüdeniz",
        target_month="Ağustos",
        target_year="2025",
        checkin_day="4",
        checkout_day="8",
        adult_count="3",
        *args,
        **kwargs
    ):
        """
        Initializes the spider with parameters passed via -a on the command line.

        Example usage:
          scrapy crawl jolly -a destination=Ölüdeniz -a target_month=Ağustos -a target_year=2025 \
                             -a checkin_day=4 -a checkout_day=8 -a adult_count=3

        :param destination: The destination to search for (e.g., "Ölüdeniz").
        :param target_month: The target check-in month as a string (e.g., "Ağustos").
        :param target_year: The target check-in year as a string (e.g., "2025").
        :param checkin_day: The day of the month to check in (string).
        :param checkout_day: The day of the month to check out (string).
        :param adult_count: Number of adults (string), which will be converted to int.
        """
        super().__init__(*args, **kwargs)
        self.destination = destination
        self.target_month = target_month
        self.target_year = target_year
        self.checkin_day = checkin_day
        self.checkout_day = checkout_day
        self.adult_count = int(adult_count)

        # Initialize the Selenium driver.
        # Set headless=False if you want to see the browser in action.
        # Set headless=True for a headless mode in production.
        self.bot = JollyTurSeleniumDriver(headless=False)

    def start_requests(self):
        """
        Scrapy's entry point. Instead of yielding multiple Requests,
        we yield just one request that triggers the parse() method.
        """
        yield scrapy.Request(
            url="https://www.jollytur.com/",
            callback=self.parse,
            dont_filter=True
        )

    def parse(self, response):
        """
        Main logic of the spider:
          1) Opens the site using Selenium.
          2) Enters the search form data (destination, dates, adult count).
          3) Scrolls through the results to load them all.
          4) Collects hotel URLs and navigates to each hotel's detail page.
        """
        self.logger.info("Navigating to the site using Selenium...")
        # Open the main site via Selenium driver.
        self.bot.open_site()

        # Set the destination in the search form.
        self.bot.set_destination(self.destination)

        # Select the check-in and check-out dates.
        self.bot.select_dates(
            target_month=self.target_month,
            target_year=self.target_year,
            checkin_day=self.checkin_day,
            checkout_day=self.checkout_day
        )

        # Adjust the number of adults in the form.
        self.bot.adjust_room_count(adult_count=self.adult_count)

        # Click the search button.
        self.bot.click_search()

        # Wait for the results to load.
        time.sleep(8)

        # Scroll through the results until all are displayed.
        # We use two XPath expressions:
        # - 'status_xpath' to identify how many hotels are currently shown
        # - 'next_button_xpath' for the "Load more" button, if present
        status_xpath = "//div[@class='listMoreCt']/span[@class='moreTextList']"
        next_button_xpath = "//div[@class='listMoreCt']/a/button"
        self.bot.scroll_and_click_until_all_displayed(status_xpath, next_button_xpath)

        # Additional waiting time to ensure final elements are loaded.
        time.sleep(5)

        # Convert current page source into a Scrapy Selector.
        list_html_source = self.bot.driver.page_source
        sel = Selector(text=list_html_source)

        self.logger.info(
            "Extracting hotel URLs from the list page using Scrapy Selector...")

        # Extract data-url attributes that contain the detail pages.
        # Note: We exclude not available hotels with the alert-danger class.
        hotel_urls = sel.xpath(
            "//div[@class='list' and not(descendant::div[@class='alert alert-danger alert-error'])]/@data-url"
        ).getall()

        self.logger.info(f"Found {len(hotel_urls)} hotels via Selector.")

        # For each hotel, open the detail page and extract the data.
        for url in hotel_urls:
            self.logger.info(f"Opening hotel detail page: {url}")
            detail_data = self.parse_hotel_details(url)
            if detail_data:
                yield detail_data

        # Close the Selenium browser session.
        self.bot.close()
        time.sleep(3)

    def parse_hotel_details(self, partial_url):
        """
        Opens the hotel detail page with Selenium, waits for relevant elements,
        and extracts additional information (e.g., hotel name, price, features).

        :param partial_url: The relative or absolute URL of the hotel detail page.
        :return: A dictionary of extracted detail data.
        """
        # Construct the full URL if the partial_url starts with "/".
        full_url = partial_url
        if partial_url.startswith("/"):
            full_url = "https://www.jollytur.com" + partial_url

        # Navigate to the detailed page in Selenium.
        self.bot.driver.get(full_url)

        # Extract the price using an explicit wait to ensure the element is
        # present.
        price = self.bot.wait.until(
            self.bot.EC.presence_of_element_located((
                By.XPATH,
                "//div[@class='reservation-col']/div[@class='col total-price']"
                "/span[contains(@class,'current-price')]"
            ))
        ).text

        # Extract the cancellation policy from 'data-content' attribute,
        # then remove any HTML tags using a regex.
        cancel_policy_element = self.bot.driver.find_element(
            By.XPATH,
            "//div[@class='reservation-col']/div[contains(@class,'cancelPolicy-badge')]")
        cancel_policy_html = cancel_policy_element.get_attribute(
            "data-content")
        cancel_policy = re.sub(
            r"<[^>]*>", "", cancel_policy_html or "").strip()

        # Extract recommended hotel info from detailrecommend div
        try:
            recomended_hotel_element = self.bot.driver.find_element(
                By.XPATH, "//div[@class='detailrecommend']"
            )
            recomended_hotel = recomended_hotel_element.get_attribute(
                "data-content")
        except self.bot.NoSuchElementException:
            recomended_hotel = None

        # Click on the "Genel Bilgiler" tab (general info section).
        try:
            self.bot.driver.find_element(
                By.XPATH,
                "//ul[@class='etabs']/li/a[@href='#genel-bilgiler']"
            ).click()
        except self.bot.NoSuchElementException:
            # if general info tab is not found, no need to proceed.
            self.logger.info("Could not find the 'Genel Bilgiler' tab.")
            return
        time.sleep(3)

        # Convert the detail page's HTML source into a Scrapy Selector.
        detail_html_source = self.bot.driver.page_source
        sel = Selector(text=detail_html_source)

        # Extract the hotel name.
        hotel_name = sel.xpath("//h1[@class='title']/@title").get()
        if hotel_name:
            hotel_name = hotel_name.strip()

        # Extract the location from the Maps anchor.
        location = sel.xpath(
            "//ul[@class='title-bottom-info']/li/a[@title='Maps']/text()").get()

        # Extract accommodation types (e.g., Ultra Her Şey Dahil).
        accommodation_types_list = sel.xpath(
            "//div[@class='meal-type-info-content']//div[@class='info']/div//text()"
        ).getall()
        accommodation_types = "".join(
            t.strip() for t in accommodation_types_list if t.strip())

        # Extract check-in and check-out times.
        checkin_time = sel.xpath(
            "//div[@class='checkin-checkout']"
            "//span[@class='title' and contains(., 'Check-in')]/following-sibling::span/text()"
        ).get()

        checkout_time = sel.xpath(
            "//div[@class='checkin-checkout']"
            "//span[@class='title' and contains(., 'Check-out')]/following-sibling::span/text()"
        ).get()

        # Extract the hotel features. We locate the "Otel Özellikleri" title
        # and then find the <ul class='detail-list'> that follows it.
        features_list = sel.xpath(
            "//div[@class='hotel-deatil-box']/header[span[@class='title' and contains(., 'Otel Özellikleri')]]"
            "/following-sibling::div[@class='content']/ul[@class='detail-list']/li//text()").getall()
        hotel_features = ", ".join(f.strip()
                                   for f in features_list if f.strip())

        self.logger.info(f"Extracted hotel detail - Name: {hotel_name}")

        # Return a dictionary with all the extracted details.
        return {
            "detail_page_url": full_url,
            "hotel_name": hotel_name,
            "price": price,
            "location": location,
            "accommodation_types": accommodation_types,
            "checkin_time": checkin_time,
            "checkout_time": checkout_time,
            "hotel_features": hotel_features,
            "cancel_policy": cancel_policy,
            "recomended_hotel": recomended_hotel
        }
