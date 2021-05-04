import logging

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import colorama

from .. import constants
from .. import actions
from ..progress_bar import ProgressBar

logger = logging.getLogger('__name__')


class ScrapeTopTags(actions.Action):
    def __init__(self, scraper, link, tag):
        super().__init__(scraper)
        self.__c_fore = colorama.Fore
        self.__c_style = colorama.Style
        colorama.init()

        self.__link = link
        self.__tag = tag
        self.__max_download = scraper.max_download
        self.__database = scraper.database

    def do(self):
        """ Find the post links from the top tags """

        print('retrieving post links from explore, please wait... ')

        actions.GoToLink(self._scraper, self.__link).do()

        try:
            top_tags_box_element = self._web_driver.find_element_by_xpath(constants.TOP_TAGS_XPATH)
        except (NoSuchElementException, StaleElementReferenceException):
            print(self.__c_fore.RED + 'no posts found' + self.__c_style.RESET_ALL)
            return

        try:
            post_elements = top_tags_box_element.find_elements_by_css_selector(constants.POSTS_CSS + ' [href]')
        except (NoSuchElementException, StaleElementReferenceException) as err:
            logger.error(err)
            self.on_fail()
            return

        try:
            self.__tag.post_links = [post_element.get_attribute('href') for post_element in post_elements]
        except StaleElementReferenceException as err:
            logger.error(err)
            self.on_fail()
            return
        else:
            self.__tag.post_links = self.__tag.post_links[:self.__max_download]

            print(self.__c_fore.GREEN + str(len(self.__tag.post_links)) + ' top post(s) will be downloaded: ' +
                  self.__c_style.RESET_ALL)

            progress_bar = ProgressBar(len(self.__tag.post_links), show_count=True)
            for post_link in self.__tag.post_links:
                actions.InitScrape(self._scraper, post_link, None, self.__tag.output_top_tag_path).do()
                self.__database.insert_tag_post(post_link, self.__tag.tagname, in_top=True)
                progress_bar.update(1)
            progress_bar.close()

    def on_fail(self):
        print('\nan error occurred while downloading images/videos')
        self._scraper.stop()
