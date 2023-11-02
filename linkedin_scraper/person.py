import os
import random
import time

import backoff
import requests
import selenium
from linkedin_scraper import selectors
from linkedin_scraper.utils import ElementCountMismatchException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
from .objects import Experience, Education, Scraper, Interest, Accomplishment, Contact


class Person(Scraper):

    __TOP_CARD = "pv-top-card"
    __WAIT_FOR_ELEMENT_TIMEOUT = 5

    def __init__(
        self,
        linkedin_url=None,
        name=None,
        about=None,
        experiences=None,
        educations=None,
        interests=None,
        accomplishments=None,
        company=None,
        job_title=None,
        contacts=None,
        driver=None,
        get=True,
        scrape=True,
        close_on_complete=True,
        time_to_wait_after_login=0,
    ):
        self.linkedin_url = linkedin_url
        self.name = name
        self.about = about or []
        self.experiences = experiences or []
        self.educations = educations or []
        self.interests = interests or []
        self.accomplishments = accomplishments or []
        self.also_viewed_urls = []
        self.contacts = contacts or []

        if driver is None:
            try:
                if os.getenv("CHROMEDRIVER") == None:
                    driver_path = os.path.join(
                        os.path.dirname(__file__), "drivers/chromedriver"
                    )
                else:
                    driver_path = os.getenv("CHROMEDRIVER")

                driver = webdriver.Chrome(driver_path)
            except:
                driver = webdriver.Chrome()

        if get:
            driver.get(linkedin_url)

        self.driver = driver

        if scrape:
            self.scrape(close_on_complete)

    def add_about(self, about):
        self.about.append(about)

    def add_experience(self, experience):
        self.experiences.append(experience)

    def add_education(self, education):
        self.educations.append(education)

    def add_interest(self, interest):
        self.interests.append(interest)

    def add_accomplishment(self, accomplishment):
        self.accomplishments.append(accomplishment)

    def add_location(self, location):
        self.location = location

    def add_contact(self, contact):
        self.contacts.append(contact)

    def scrape(self, close_on_complete=True):
        if self.is_signed_in():
            self.scrape_logged_in(close_on_complete=close_on_complete)
        else:
            print("you are not logged in!")

    def _click_see_more_by_class_name(self, class_name):
        try:
            _ = WebDriverWait(self.driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, class_name))
            )
            div = self.driver.find_element(By.CLASS_NAME, class_name)
            div.find_element(By.TAG_NAME, "button").click()
        except Exception as e:
            pass

    def is_open_to_work(self):
        try:
            return "#OPEN_TO_WORK" in self.driver.find_element(By.CLASS_NAME, "pv-top-card-profile-picture").find_element(By.TAG_NAME, "img").get_attribute("title")
        except:
            return False

    @backoff.on_exception(
        backoff.expo,
        (
            selenium.common.exceptions.TimeoutException,
            selenium.common.exceptions.WebDriverException,
            selenium.common.exceptions.StaleElementReferenceException,
            selenium.common.exceptions.ElementNotInteractableException,
            selenium.common.exceptions.NoSuchElementException,
            selenium.common.exceptions.UnexpectedAlertPresentException,
        ),
        max_time=60
    )
    def get_experiences(self):
        def get_position_work_times(position_work_times: str):
            times = position_work_times.split("·")[0].strip() if position_work_times else ""
            duration = position_work_times.split("·")[1].strip() if len(position_work_times.split("·")) > 1 else ""
            from_date = " ".join(times.split(" ")[:2]) if times else ""
            to_date = " ".join(times.split(" ")[3:]) if times else ""
            return duration, from_date, to_date
        # url = os.path.join(self.linkedin_url, "details/experience")
        # time.sleep(random.uniform(0, 5))  # Sleep for a random time
        # self.driver.get(url)
        # self.focus()
        # main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
        # time.sleep(random.uniform(0, 5))  # Sleep for a random time
        experience_h2_elem: WebElement = self.driver.find_element(By.XPATH, "//section[.//h2[contains(text(), 'Experience')]]")
        experience_container_elem: WebElement = experience_h2_elem.find_element(By.XPATH, "./..")
        experience_ul_elem = experience_container_elem.find_element(By.CLASS_NAME, "experience__list")
        time.sleep(random.uniform(0, 2))  # Sleep for a random time
        self.scroll_to_half()
        time.sleep(random.uniform(0, 2))  # Sleep for a random time
        self.scroll_to_bottom()
        for li_elem in experience_ul_elem.find_elements(By.XPATH, "li"):
            company_link_elem: WebElement = li_elem.find_element(By.CLASS_NAME, 'profile-section-card__image-link')
            company_linkedin_url = company_link_elem.get_attribute("href") if company_link_elem else ""

            position_title_elem = li_elem.find_element(By.CLASS_NAME, "profile-section-card__title")
            position_title = position_title_elem.text if position_title_elem else ""

            position_company_elem = li_elem.find_element(By.CLASS_NAME, "profile-section-card__subtitle-link")
            position_company = position_company_elem.text if position_company_elem else ""

            duration_container_elem = li_elem.find_element(By.XPATH, "span[class='date-range text-color-text-secondary font-sans text-md leading-open font-regular']")
            time_elem_list = duration_container_elem.find_elements(By.TAG_NAME, 'time')
            duration_elem = duration_container_elem.find_element(By.CLASS_NAME, 'before:middot')
            duration = duration_elem.text if duration_elem else ""
            if len(time_elem_list) == 2:
                from_date = time_elem_list[0].text
                to_date = time_elem_list[1].text
            elif len(time_elem_list) == 1:
                from_date = time_elem_list[0].text
                to_date = 'Present'
            else:
                raise ElementCountMismatchException("experiences_time", 2, len(time_elem_list))
            
            position_location_elem = li_elem.find_element(By.CLASS_NAME, 'class="experience-item__location experience-item__meta-item"')
            position_location = position_location_elem.text if position_location_elem else ""

            description_elem = li_elem.find_element(By.CLASS_NAME, "experience-item__description experience-item__meta-item")
            description = description_elem.text if description_elem else ""
                
            experience = Experience(
                position_title=position_title,
                from_date=from_date,
                to_date=to_date,
                duration=duration,
                location=position_location,
                description=description,
                institution_name=position_company,
                linkedin_url=company_linkedin_url
            )
            self.add_experience(experience)
    
    @backoff.on_exception(
        backoff.expo,
        (
            selenium.common.exceptions.TimeoutException,
            selenium.common.exceptions.WebDriverException,
            selenium.common.exceptions.StaleElementReferenceException,
            selenium.common.exceptions.ElementNotInteractableException,
            selenium.common.exceptions.NoSuchElementException,
            selenium.common.exceptions.UnexpectedAlertPresentException,
        ),
        max_time=60
    )
    def get_educations(self):
        # time.sleep(random.uniform(0, 5))  # Sleep for a random time
        # url = os.path.join(self.linkedin_url, "details/education")
        # self.driver.get(url)
        # self.focus()
        # main = self.wait_for_element_to_load(by=By.TAG_NAME, name="main")
        # self.scroll_to_half()
        time.sleep(random.uniform(0, 5))  # Sleep for a random time
        education_h2_elem: WebElement = self.driver.find_element(By.XPATH, "//section[.//h2[contains(text(), 'EWducation')]]")
        education_container_elem: WebElement = education_h2_elem.find_element(By.XPATH, "./..")
        education_ul_elem: WebElement = education_container_elem.find_element(By.CLASS_NAME, "education__list")
        self.scroll_to_bottom()
        time.sleep(random.uniform(0, 5))  # Sleep for a random time
        for li_elem in education_ul_elem.find_elements(By.XPATH, "li"):
            school_link_elem = li_elem.find_element(By.CLASS_NAME, "profile-section-card__title-link")
            school_link = school_link_elem.get_attribute("href") if school_link_elem else ""
            school_name = school_link_elem.text if school_link_elem else ""

            degree_container_elem = li_elem.find_element(By.CLASS_NAME, "profile-section-card__subtitle")
            degree_container_elem.find_element

            # company elem
            institution_linkedin_url = institution_logo_elem.find_element(By.XPATH, "*").get_attribute("href")

            # position details
            position_details_list = position_details.find_elements(By.XPATH, "*")
            position_summary_details = position_details_list[0] if len(position_details_list) > 0 else None
            outer_positions = position_summary_details.find_element(By.XPATH, "*").find_elements(By.XPATH, "*")
            
            position_summary_text = position_details_list[1] if len(position_details_list) > 1 else None
            description = position_summary_text.text if position_summary_text else None
  
            institution_name = outer_positions[0].find_element(By.TAG_NAME, "span").text if len(outer_positions) > 0 else None
            degree = outer_positions[1].find_element(By.TAG_NAME, "span").text if len(outer_positions) > 1 else None
            if len(outer_positions) > 2:
                times = outer_positions[2].find_element(By.TAG_NAME, "span").text
                from_date = " ".join(times.split(" ")[:2])
                to_date = " ".join(times.split(" ")[3:])
            else:
                from_date = None
                to_date = None
            
            education = Education(
                from_date=from_date,
                to_date=to_date,
                description=description,
                degree=degree,
                institution_name=school_name,
                linkedin_url=school_link
            )
            self.add_education(education)

    @backoff.on_exception(
        backoff.expo,
        (
            selenium.common.exceptions.TimeoutException,
            selenium.common.exceptions.WebDriverException,
            selenium.common.exceptions.StaleElementReferenceException,
            selenium.common.exceptions.ElementNotInteractableException,
            selenium.common.exceptions.NoSuchElementException,
            selenium.common.exceptions.UnexpectedAlertPresentException,
        ),
        max_time=60
    )
    def get_name_and_location(self):
        time.sleep(random.uniform(0, 3))  # Sleep for a random time
        top_panels = self.driver.find_elements(By.CLASS_NAME, "pv-text-details__left-panel")
        name_container_elem = top_panels[0] if len(top_panels) > 0 else None
        location_container_elem = top_panels[1] if len(top_panels) > 1 else None
        
        if name_container_elem is None:
            self.name = None
        else:
            name_elem, *_ = name_container_elem.find_elements(By.XPATH, "*")
            self.name = name_elem.text if name_elem else None
        
        if location_container_elem is None:
            self.location = None
        else:
            location_elem = location_container_elem.find_element(By.TAG_NAME, "span")
            self.location = location_elem.text if location_elem else None

    @backoff.on_exception(
        backoff.expo,
        (
            selenium.common.exceptions.TimeoutException,
            selenium.common.exceptions.WebDriverException,
            selenium.common.exceptions.StaleEleme   ntReferenceException,
            selenium.common.exceptions.ElementNotInteractableException,
            selenium.common.exceptions.NoSuchElementException,
            selenium.common.exceptions.UnexpectedAlertPresentException,
        ),
        max_time=60
    )
    def get_about(self):
        time.sleep(random.uniform(0, 2))  # Sleep for a random time
        try:
            about = self.driver.find_element(By.ID, "about").find_element(By.XPATH, "..").find_element(By.CLASS_NAME, "display-flex").text
        except NoSuchElementException:
            about = None
        self.about = about

    def scrape_logged_in(self, close_on_complete=True):
        driver = self.driver
        duration = None

        root = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located(
                (
                    By.CLASS_NAME,
                    self.__TOP_CARD,
                )
            )
        )
        self.focus()
        self.wait(5)

        # get name and location
        self.get_name_and_location()

        self.open_to_work = self.is_open_to_work()

        # get about
        self.get_about()
        driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));"
        )
        driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight/1.5));"
        )

        # get experience
        self.get_experiences()

        # get education
        self.get_educations()

        driver.get(self.linkedin_url)

        # get interest
        try:

            _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[@class='pv-profile-section pv-interests-section artdeco-container-card artdeco-card ember-view']",
                    )
                )
            )
            interestContainer = driver.find_element(By.XPATH,
                                                    "//*[@class='pv-profile-section pv-interests-section artdeco-container-card artdeco-card ember-view']"
                                                    )
            for interestElement in interestContainer.find_elements(By.XPATH,
                                                                   "//*[@class='pv-interest-entity pv-profile-section__card-item ember-view']"
                                                                   ):
                interest = Interest(
                    interestElement.find_element(
                        By.TAG_NAME, "h3").text.strip()
                )
                self.add_interest(interest)
        except:
            pass

        # get accomplishment
        try:
            _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[@class='pv-profile-section pv-accomplishments-section artdeco-container-card artdeco-card ember-view']",
                    )
                )
            )
            acc = driver.find_element(By.XPATH,
                                      "//*[@class='pv-profile-section pv-accomplishments-section artdeco-container-card artdeco-card ember-view']"
                                      )
            for block in acc.find_elements(By.XPATH,
                                           "//div[@class='pv-accomplishments-block__content break-words']"
                                           ):
                category = block.find_element(By.TAG_NAME, "h3")
                for title in block.find_element(By.TAG_NAME,
                                                "ul"
                                                ).find_elements(By.TAG_NAME, "li"):
                    accomplishment = Accomplishment(category.text, title.text)
                    self.add_accomplishment(accomplishment)
        except:
            pass

        # get connections
        try:
            driver.get(
                "https://www.linkedin.com/mynetwork/invite-connect/connections/")
            _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "mn-connections"))
            )
            connections = driver.find_element(By.CLASS_NAME, "mn-connections")
            if connections is not None:
                for conn in connections.find_elements(By.CLASS_NAME, "mn-connection-card"):
                    anchor = conn.find_element(
                        By.CLASS_NAME, "mn-connection-card__link")
                    url = anchor.get_attribute("href")
                    name = conn.find_element(By.CLASS_NAME, "mn-connection-card__details").find_element(
                        By.CLASS_NAME, "mn-connection-card__name").text.strip()
                    occupation = conn.find_element(By.CLASS_NAME, "mn-connection-card__details").find_element(
                        By.CLASS_NAME, "mn-connection-card__occupation").text.strip()

                    contact = Contact(
                        name=name, occupation=occupation, url=url)
                    self.add_contact(contact)
        except:
            connections = None

        if close_on_complete:
            driver.quit()

    @property
    def company(self):
        if self.experiences:
            return (
                self.experiences[0].institution_name
                if self.experiences[0].institution_name
                else None
            )
        else:
            return None

    @property
    def job_title(self):
        if self.experiences:
            return (
                self.experiences[0].position_title
                if self.experiences[0].position_title
                else None
            )
        else:
            return None

    def __repr__(self):
        return "<Person {name}\n\nAbout\n{about}\n\nExperience\n{exp}\n\nEducation\n{edu}\n\nInterest\n{int}\n\nAccomplishments\n{acc}\n\nContacts\n{conn}>".format(
            name=self.name,
            about=self.about,
            exp=self.experiences,
            edu=self.educations,
            int=self.interests,
            acc=self.accomplishments,
            conn=self.contacts,
        )
