import time
import logging

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException

from .. import constants
from .. import actions

logger = logging.getLogger('__name__')


class GrabPostLinks(actions.Action):
    def __init__(self, scraper, link, xpath=None):
        super().__init__(scraper)
        self.__link = link
        self.__max_download = scraper.max_download
        self.__xpath = xpath
        self.__post_element_count = 0

    def do(self):
        """
        Scroll all the way down to the bottom of the page
        When xpath is given, only links inside the xpath will be retrieved
        """

        actions.GoToLink(self._scraper, self.__link).do()

        post_links = []

        increment_browser_height = True

        reties = 0
        while True:

            def grab_links():
                """ Search for links on the page and retrieve them """

                links = []

                # Grab post links inside the xpath only
                if self.__xpath:
                    try:
                        element_box = self._web_driver.find_element_by_xpath(self.__xpath)
                        posts_element = element_box.find_elements_by_css_selector(constants.POSTS_CSS + ' [href]')
                        links += [post_element.get_attribute('href') for post_element in posts_element]
                    except (NoSuchElementException, StaleElementReferenceException) as err1:
                        logger.error(err1)
                        return []

                # Grab all post links
                else:
                    try:
                        elements = self._web_driver.find_elements_by_css_selector('img.photo-item__img')
                    except (NoSuchElementException, StaleElementReferenceException) as err2:
                        logger.error(err2)
                        return []

                    try:
                        for post_element in elements:
                            self.__post_element_count = self.__post_element_count + 1
                            try:
                                link = post_element.get_attribute('src')
                                links.append(link)
                                # print ('added link: ' + link)    
                            except (NoSuchElementException, StaleElementReferenceException):
                                pass

                            # svg_element = post_element.find_element_by_xpath('//*[name()="svg" and @aria-label="Clip"]')
                            # if svg_element is not None:
                            #     links += post_element.get_attribute('href')
                        # links += [post_element.get_attribute('href') for post_element in elements]
                    except StaleElementReferenceException as err3:
                        logger.error(err3)
                        return []

                # Remove all duplicate links in the list and keep the list order
                links = sorted(set(links), key=lambda index: links.index(index))

                return links

            pre_length = len(post_links)
            post_links += grab_links()

            # Remove any duplicates and return the list if maximum was reached
            post_links = sorted(set(post_links), key=lambda index: post_links.index(index))
            if len(post_links) >= self.__max_download:
                self._web_driver.maximize_window()
                return post_links[:self.__max_download]
            # if self.__post_element_count >= 500:  # if this user has more than 500 posts, don't look further
            #     return post_links

            print ('lens', len(post_links), pre_length)
            if len(post_links) == pre_length:
                self._web_driver.maximize_window()
                reties = reties + 1
                if reties > 10:
                    print ('no more item, exiting')
                    return post_links
            else:
                reties = 0

            # Scroll down to bottom
            self._web_driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            print('scroll to bottom')
            time.sleep(5)

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
        print('error while retrieving post links')
        self._scraper.stop()
