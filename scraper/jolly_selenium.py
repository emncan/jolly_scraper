"""
This file contains a helper class for automating interactions with jollytur.com
using Selenium. It does not handle any Scrapy logic.
"""

import time
import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException


class JollyTurSeleniumDriver:
    """
    This class encapsulates all Selenium-based interactions with jollytur.com.

    Responsibilities:
      - Open the website
      - Fill out the search form (destination, dates, room counts)
      - Continuously scroll and click "Load more" until all items are displayed
      - Close the browser once all operations are finished
    """

    def __init__(self, headless=True):
        """
        Initializes the Selenium WebDriver.

        :param headless: If True, the browser will run in headless mode (invisible in the UI).
                         If False, you will see the browser in action.
        """
        chrome_options = Options()
        if headless:
            # Headless mode: runs without opening a visible browser window
            chrome_options.add_argument("--headless")

        # Use Undetected ChromeDriver to reduce blocking or detection issues
        self.driver = uc.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        # Set the browser window size to avoid hidden elements
        self.driver.set_window_size(1300, 1000)

        # WebDriverWait for explicit waiting until certain conditions are met
        self.wait = WebDriverWait(self.driver, 10)
        # Shortcut to Expected Conditions (EC) for readability
        self.EC = EC
        self.NoSuchElementException = NoSuchElementException

    def open_site(self, url="https://www.jollytur.com/"):
        """
        Navigates to the specified URL and waits for the 'destination' element to load.

        :param url: The URL to open. Defaults to the jollytur.com homepage.
        """
        self.driver.get(url)
        # Wait until 'destination' input is located on the page
        self.wait.until(
            self.EC.presence_of_element_located((By.NAME, "destination"))
        )

    def set_destination(self, destination_text="Kemer"):
        """
        Sets the 'destination' field in the search form.

        :param destination_text: Text to be entered into the 'destination' field (e.g. "Kemer").
        """
        # Wait until the destination field is clickable
        destination = self.wait.until(
            self.EC.element_to_be_clickable((By.NAME, "destination"))
        )
        # Clear any existing text, then enter the destination
        destination.click()
        destination.clear()
        destination.send_keys(destination_text)

        # Pause briefly to allow the autocomplete suggestions to appear
        time.sleep(2)

    def select_dates(self, target_month="Ağustos", target_year="2025",
                     checkin_day="4", checkout_day="8"):
        """
        Opens the date selection widget and chooses the desired check-in/out days.

        Note:
          - 'target_month' must be in Turkish, matching the month name displayed on the site.
          - 'target_year' should be a string representing the year (e.g., "2025").
          - 'checkin_day' and 'checkout_day' should be string values like "4", "8".

        :param target_month: The month to select on the calendar (in Turkish, e.g. "Ağustos").
        :param target_year:  The year to select on the calendar (e.g. "2025").
        :param checkin_day:  The day of the month for check-in (string).
        :param checkout_day: The day of the month for check-out (string).
        """
        # Click the date row to open the calendar
        date_row = self.wait.until(
            self.EC.element_to_be_clickable((By.XPATH, "//div[@class='date-row']"))
        )
        date_row.click()

        # Ensure the calendar has loaded
        self.wait.until(
            self.EC.presence_of_element_located((By.XPATH, "//div[@class='ui-datepicker-title']"))
        )

        # Loop until we find the desired month/year in the calendar header
        while True:
            current_month = self.driver.find_element(
                By.XPATH,
                "//div[@class='ui-datepicker-title']/span[@class='ui-datepicker-month']"
            ).text
            current_year = self.driver.find_element(
                By.XPATH,
                "//div[@class='ui-datepicker-title']/span[@class='ui-datepicker-year']"
            ).text

            if current_month == target_month and current_year == target_year:
                break

            # If it's not the target month/year, click the "next" arrow
            next_button = self.wait.until(self.EC.element_to_be_clickable(
                (By.XPATH, "//span[@class='ui-icon ui-icon-circle-triangle-e']")))
            next_button.click()
            time.sleep(1)

        # Once the correct month/year is displayed, select the check-in date
        checkin = self.wait.until(
            self.EC.element_to_be_clickable(
                (By.XPATH,
                 f"//table[@class='ui-datepicker-calendar']/tbody//a[text()={checkin_day}]"))
        )
        checkin.click()
        time.sleep(1)

        # Then select the check-out date
        checkout = self.wait.until(
            self.EC.element_to_be_clickable(
                (By.XPATH,
                 f"//table[@class='ui-datepicker-calendar']/tbody//a[text()={checkout_day}]"))
        )
        checkout.click()
        time.sleep(1)

    def adjust_room_count(self, adult_count=2):
        """
        Adjusts the number of adults in the room selection dropdown.

        :param adult_count: Desired number of adults (integer). Will be capped at 9 for safety.
        """
        if adult_count > 9:
            adult_count = 9  # Prevent selecting more than 9 adults, if that's a site limit

        # Click the room/person count section to open its dropdown
        room_dropdown = self.wait.until(self.EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(@class,'list person-count')]"))
        )
        room_dropdown.click()
        time.sleep(1)
        # Sometimes an extra click is needed if the dropdown does not expand fully
        room_dropdown.click()
        time.sleep(1)

        # XPath for the current adult count, and the increment/decrement buttons
        adult_xpath = (
            "//div[@class='room-count-dropdown hotel-room-count-dropdown show']"
            "/div[@class='room-info']/div[1]/div[2]//span[contains(@class,'primary-select async adult-number')]"
        )
        inc_adult_btn_xpath = (
            "//div[@class='room-count-dropdown hotel-room-count-dropdown show']"
            "/div[@class='room-info']/div[1]/div[2]//div[@data-name='inc']"
        )
        dec_adult_btn_xpath = (
            "//div[@class='room-count-dropdown hotel-room-count-dropdown show']"
            "/div[@class='room-info']/div[1]/div[2]//div[@data-name='dec']"
        )

        # Read the current adult count in the dropdown
        current_adult_count = self.wait.until(
            self.EC.presence_of_element_located((By.XPATH, adult_xpath))
        ).text
        current_adult_count = int(current_adult_count.strip())

        # Decrement down to 1 adult first, just to have a known baseline
        while current_adult_count > 1:
            dec_btn = self.wait.until(
                self.EC.element_to_be_clickable((By.XPATH, dec_adult_btn_xpath))
            )
            dec_btn.click()
            time.sleep(0.5)
            current_adult_count = int(
                self.driver.find_element(By.XPATH, adult_xpath).text.strip()
            )

        # Then increment up to the desired adult_count
        for _ in range(adult_count - 1):
            inc_btn = self.wait.until(
                self.EC.element_to_be_clickable((By.XPATH, inc_adult_btn_xpath))
            )
            inc_btn.click()
            time.sleep(0.5)

    def click_search(self):
        """
        Clicks the search button to initiate a hotel search.
        """
        # Locate and click the search button on the form
        search_button = self.wait.until(
            self.EC.element_to_be_clickable((
                By.XPATH,
                "//div[@class='travel-planner-inner travel-planner-hotel']/div/div[@class='list action-button']"
            ))
        )
        search_button.click()

    def scroll_and_click_until_all_displayed(self, status_xpath, next_button_xpath):
        """
        Continuously scrolls the page and clicks the "Load more" button
        until a specific status element indicates that all items have been displayed.

        :param status_xpath: XPath of the element showing how many items are currently displayed
                            (or whether everything is fully loaded).
        :param next_button_xpath: XPath of the "Load more" button (or next button).
        """

        def is_in_viewport(elem):
            """
            Checks if a given element is currently visible in the viewport
            by verifying that the center of the element matches the elementFromPoint() call.
            """
            return self.driver.execute_script(
                """
                var elem = arguments[0],
                    box = elem.getBoundingClientRect(),
                    cx = box.left + (box.width / 2),
                    cy = box.top + (box.height / 2),
                    e = document.elementFromPoint(cx, cy);
                return e === elem;
                """,
                elem
            )

        def scroll_until_element_visible(xpath, scroll_step=550, max_scrolls=50):
            """
            Scrolls the page down in increments until the specified element
            is visible or a maximum number of scrolls is reached.
            """
            try:
                element = self.driver.find_element(By.XPATH, xpath)
            except Exception as e:
                print(f"Element not found while scrolling: {e}")
                return None

            scroll_count = 0
            while not is_in_viewport(element) and scroll_count < max_scrolls:
                self.driver.execute_script(f"window.scrollBy(0, {scroll_step});")
                time.sleep(2)
                scroll_count += 1

            if is_in_viewport(element):
                return element
            return None

        while True:
            # Scroll until the status element (e.g., "You have viewed all items") is visible
            status_element = scroll_until_element_visible(status_xpath)
            if not status_element:
                print("Status element could not be made visible.")
                break

            status_text = status_element.text.strip().lower()
            print("Status text:", status_text)

            # Check if the site indicates that we've loaded all items
            if "tamamını görüntülediniz" in status_text:
                print("All items have been displayed.")
                break

            # Otherwise, click the 'next'/'load more' button
            try:
                next_button = self.driver.find_element(By.XPATH, next_button_xpath)
                next_button.click()
                print("Clicked the 'next' (or 'Load more') button.")
            except Exception as e:
                print(f"Could not click the 'next' button: {e}")
                break

            # Wait a bit for new content to load before checking again
            time.sleep(5)

    def close(self):
        """
        Closes the Selenium WebDriver and quits the browser session.
        """
        self.driver.quit()
        print("Browser session has been closed.")