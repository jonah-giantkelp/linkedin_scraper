import scrapy
from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess

class LinkedCompanySpider(scrapy.Spider):
    name = "linkedin_company_profile"
    api_url = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=python&location=United%2BStates&geoId=103644278&trk=public_jobs_jobs-search-bar_search-submit&start='

    def __init__(self, company_urls=None, *args, **kwargs):
        super(LinkedCompanySpider, self).__init__(*args, **kwargs)
        if company_urls:
            self.company_pages = company_urls

    def start_requests(self):

        company_index_tracker = 0

        first_url = self.company_pages[company_index_tracker]

        yield scrapy.Request(url=first_url, callback=self.parse_response, meta={'company_index_tracker': company_index_tracker})


    def parse_response(self, response):
        company_index_tracker = response.meta['company_index_tracker']
        print('***************')
        print('****** Scraping page ' + str(company_index_tracker+1) + ' of ' + str(len(self.company_pages)))
        print('***************')

        company_item = {}

        company_item['name'] = response.css('.top-card-layout__entity-info h1::text').get(default='not-found').strip()
        company_item['summary'] = response.css('.top-card-layout__entity-info h4 span::text').get(default='not-found').strip()
        company_item['about_us'] = response.css('p.break-words.whitespace-pre-wrap.text-color-text::text').get(default='not-found').strip()

        try:
            ## all company details
            company_details = response.css('.core-section-container__content .mb-2')

            #industry line
            company_industry_line = company_details[1].css('.text-md::text').getall()
            company_item['industry'] = company_industry_line[1].strip()

            #company size line
            company_size_line = company_details[2].css('.text-md::text').getall()
            company_item['size'] = company_size_line[1].strip()

            #company founded
            company_size_line = company_details[5].css('.text-md::text').getall()
            company_item['founded'] = company_size_line[1].strip()

            specialties_block = response.css('div[data-test-id="about-us__specialties"] dd::text').get()
            company_item['specialties'] = specialties_block.strip() if specialties_block else 'not-found'
        except IndexError:
            print("Error: Skipped Company - Some details missing")

        """
            EMPLOYEE DETAILS SECTION
        """
        company_item['employees'] = []
        employee_blocks = response.css('ul > li > a.base-card.base-main-card')
        for block in employee_blocks:
            employee = {}

            ## Employee LinkedIn profile URL
            try:
                employee['profile_url'] = block.css('a::attr(href)').get()
            except Exception as e:
                print('employee --> profile_url', e)
                employee['profile_url'] = ''

            ## Employee Name
            try:
                employee['name'] = block.css('h3.base-main-card__title::text').get().strip()
            except Exception as e:
                print('employee --> name', e)
                employee['name'] = ''

            ## Employee Role
            try:
                employee['role'] = block.css('h4.base-main-card__subtitle::text').get().strip()
            except Exception as e:
                print('employee --> role', e)
                employee['role'] = ''

            company_item['employees'].append(employee)

        """
            LOCATION DETAILS SECTION
        """
        company_item['locations'] = []
        location_blocks = response.css('section.locations ul li')

        for block in location_blocks:
            location = {}

            ## Location Address Lines
            try:
                address_parts = block.css('div[id^="address-"] p::text').getall()
                location['address'] = ', '.join([part.strip() for part in address_parts])
            except Exception as e:
                print('location --> address', e)
                location['address'] = ''

            ## Location Type (e.g., Primary)
            try:
                location['type'] = block.css('span.tag-sm::text').get().strip()
            except Exception as e:
                print('location --> type', e)
                location['type'] = ''

            company_item['locations'].append(location)

        """
            POSTS SECTION
        """
        company_item['posts'] = []
        post_blocks = response.css('article')

        for block in post_blocks:
            post = {}

            try:
                # Extract post content
                post_content_parts = block.css('div.attributed-text-segment-list__container p.attributed-text-segment-list__content::text').getall()
                post['content'] = ' '.join([part.strip() for part in post_content_parts]).strip()
            except Exception as e:
                print('post --> content', e)
                post['content'] = ''

            try:
                # Extract timestamp
                post['timestamp'] = block.css('div.flex span time::text').get().strip()
            except Exception as e:
                print('post --> timestamp', e)
                post['timestamp'] = ''

            company_item['posts'].append(post)

        yield company_item

        company_index_tracker = company_index_tracker + 1

        if company_index_tracker <= (len(self.company_pages)-1):
            next_url = self.company_pages[company_index_tracker]

            yield scrapy.Request(url=next_url, callback=self.parse_response, meta={'company_index_tracker': company_index_tracker})

def run_spider(company_urls):

    # Define output file
    output_file = 'scraper_output.json'

    # Set default scraper settings
    settings = get_project_settings()

    # Add output file option
    settings.set('FEEDS', {
        output_file: {
            'format': 'json',
            'encoding': 'utf8',
            'store_empty': False,
            'overwrite': True,
            'fields': None,
            'indent': 4,
        },
    })

    # Create instance of crawler process with correct settings and run the spider
    process = CrawlerProcess(settings=settings)
    process.crawl(LinkedCompanySpider, company_urls=company_urls)
    process.start()


if __name__ == "__main__":

    # Spider takes a list of company urls as an argument
    companies = ["https://uk.linkedin.com/company/giantkelp?trk=public_profile_topcard-current-company",
                 "https://uk.linkedin.com/company/candyspace-media?trk=similar-pages",
                 "https://uk.linkedin.com/company/profound-works-limited?trk=similar-pages"]

    run_spider(company_urls=companies)
