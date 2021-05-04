import logging

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

from .. import constants
from .. import actions

logger = logging.getLogger('__name__')

class CheckIfHasLink(actions.Action):
    def __init__(self, scraper, user, partialLink):
        super().__init__(scraper)
        self.__user = user
        self.__partialLink = partialLink

    def do(self):
        """ Check if there are reels link in the profile """

        actions.GoToLink(self._scraper, self.__user.profile_link).do()

        try:
            elements = self._web_driver.find_elements_by_css_selector(constants.NAV_MENU_CSS + ' [href]')
        except (NoSuchElementException, StaleElementReferenceException) as err:
            logger.error(err)
            logger.error('Nav menu not found')
            self.on_fail()

        for element in elements:
            link = element.get_attribute('href')
            print ('check ', self.__partialLink, ' in link: ', link)
            if link is not None and self.__partialLink in link:
                return True
        return False

    def on_fail(self):
        pass
