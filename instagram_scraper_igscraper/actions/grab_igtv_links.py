import time
import logging

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException

from .. import constants
from .. import actions

logger = logging.getLogger('__name__')


class GrabIgtvLinks(actions.Action):
    def __init__(self, scraper, link, xpath=None):
        super().__init__(scraper)
        self.__link = link
        self.__max_download = scraper.max_download
        self.__xpath = xpath

    def do(self):
        """
        Scroll all the way down to the bottom of the page
        When xpath is given, only links inside the xpath will be retrieved
        """

        actions.GoToLink(self._scraper, self.__link).do()

        igtv_links = []

        increment_browser_height = True

        while True:

            def grab_links():
                """ Search for links on the page and retrieve them """

                links = []

                # Grab igtv links inside the xpath only
                if self.__xpath:
                    try:
                        element_box = self._web_driver.find_element_by_xpath(self.__xpath)
                        igtvs_element = element_box.find_elements_by_css_selector(constants.IGTVS_CSS + ' [href]')
                        links += [igtv_element.get_attribute('href') for igtv_element in igtvs_element]
                    except (NoSuchElementException, StaleElementReferenceException) as err1:
                        logger.error(err1)
                        return []

                # Grab all igtv links
                else:
                    try:
                        elements = self._web_driver.find_elements_by_css_selector(constants.IGTVS_CSS + ' [href]')
                    except (NoSuchElementException, StaleElementReferenceException) as err2:
                        logger.error(err2)
                        return []

                    try:
                        links += [igtv_element.get_attribute('href') for igtv_element in elements]
                    except StaleElementReferenceException as err3:
                        logger.error(err3)
                        return []

                # Remove all duplicate links in the list and keep the list order
                links = sorted(set(links), key=lambda index: links.index(index))

                return links

            igtv_links += grab_links()

            # Remove any duplicates and return the list if maximum was reached
            igtv_links = sorted(set(igtv_links), key=lambda index: igtv_links.index(index))
            if len(igtv_links) >= self.__max_download:
                self._web_driver.maximize_window()
                return igtv_links[:self.__max_download]

            # Scroll down to bottom
            self._web_driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            time.sleep(3)

            # If instagram asks to show more igtvs, click it
            try:
                # TODO: not sure what's show_more tag
                show_more_igtvs = self._web_driver.find_element_by_css_selector(constants.SHOW_MORE_POSTS_CSS)
            except (NoSuchElementException, StaleElementReferenceException):
                pass
            else:
                try:
                    show_more_igtvs.click()
                except ElementClickInterceptedException as err:
                    logger.error(err)
                    self.on_fail()

            try:
                # TODO: not sure what's SCROLL_LOAD_CSS tag
                self._web_driver.find_element_by_css_selector(constants.SCROLL_LOAD_CSS)
            except (NoSuchElementException, StaleElementReferenceException):
                # Reached the end, grab links for the last time, remove any duplicates and return the list
                igtv_links += grab_links()
                self._web_driver.maximize_window()
                return sorted(set(igtv_links), key=lambda index: igtv_links.index(index))[:self.__max_download]
            else:
                # Change the browser height to prevent randomly being stuck while scrolling down
                height = self._web_driver.get_window_size()['height']
                if increment_browser_height:
                    height += 25
                    increment_browser_height = False
                else:
                    height -= 25
                    increment_browser_height = True

                width = self._web_driver.get_window_size()['width']
                self._web_driver.set_window_size(width, height)

    def on_fail(self):
        print('error while retrieving igtv links')
        self._scraper.stop()
