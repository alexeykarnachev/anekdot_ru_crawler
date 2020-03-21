import asyncio
import datetime
import logging
import re
import urllib.parse
from typing import Generator, Tuple, Sequence

import aiofiles
import aiohttp as aiohttp
import bs4

from anekdot_ru_crawler import constants

logger = logging.getLogger(__name__)

START_DAY = '1995-11-08'
HOME_URL = 'https://www.anekdot.ru/'
DAY_REGEX = re.compile(r'^\d{4}-\d{2}-\d{2}$')
DATE_FMT = '%Y-%m-%d'
CATEGORIES = ('anekdot', 'story', 'aphorism', 'poems')

UTTERANCE_SEP = ''

_HEADERS = headers = {
    'user-agent':
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like '
        'Gecko) Ubuntu Chromium/80.0.3987.87 Chrome/80.0.3987.87 Safari/537.36',
}


class CrawlerError(Exception):
    pass


def iterate_on_day_base_urls(day: str) -> Generator[str, None, None]:
    """Constructs base urls for specific day

    Args:
        day (str):
            The day to construct urls for.

    Yields (str):
        The base day url for each category (check `CATEGORIES` module variable).
        "Base" [url] means, that specific pagination pages numbers still need
        to be obtained.
    """
    if not DAY_REGEX.match(day):
        raise CrawlerError(
            f'Incorrect day format: {day}. Mast match {DAY_REGEX}'
        )

    for category in CATEGORIES:
        url = f'https://www.anekdot.ru/release/{category}/day/{day}/'
        yield url


async def get_page(url: str, sess, sem, retries: int = 9):
    """Requests a page and returns content."""
    logger.debug('Requesting page: %s' % (url,))
    i_retry = 0
    while i_retry <= retries:
        try:
            async with sem, sess.get(url) as response:
                text = await response.text()
                break
        except asyncio.TimeoutError:
            i_retry += 1
            logger.warning(
                'Timeout for page [%s/%s]: %s' % (i_retry, retries + 1, url,)
            )
    logger.debug('Page source obtained: %s' % (url,))
    return text


async def iterate_on_day_page_soups(day_url: str, sess, sem):
    """Generates soups for base day url.

    It requests day base url page, search for pagination, make requests
    for all found urls and yields their soups.
    """
    first_page = await get_page(day_url, sess, sem)
    first_soup = bs4.BeautifulSoup(first_page, "html.parser")
    yield first_soup

    page_list = first_soup.find('div', {'class': 'pageslist'})
    page_urls = page_list.find_all('a', href=True) if page_list else []
    page_urls = list(set([page['href'] for page in page_urls]))

    for page_url in page_urls:
        url = urllib.parse.urljoin(HOME_URL, page_url)
        page = await get_page(url, sess, sem)
        yield bs4.BeautifulSoup(page, "html.parser")


def prepare_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def prepare_result_to_write(result: Tuple[Sequence[str], str]) -> str:
    tags_str = ', '.join(result[0])
    text = prepare_text(result[1])
    result = f'{tags_str}\n{constants.END_OF_UTTERANCE}\n' \
             f'{text}\n{constants.END_OF_DIALOG}\n'
    return result


def iterate_on_parsed_results(soup):
    topic_boxes = soup.find_all(
        'div', {
            'class': 'topicbox',
            'id': lambda val: val is not None
        }
    )
    if len(topic_boxes) == 0:
        return None
    link = soup.find('link', {'rel': 'canonical'})['href']
    category = re.search(r'release/(.+?)/day/', link).group(1)
    for topic_box in topic_boxes:
        tags = topic_box.find('div', {'class': 'tags'})
        tags = [a.text for a in tags.find_all('a')] if tags else []
        tags.insert(0, category)
        text = topic_box.find('div', {'class': 'text'}).get_text('\n')
        yield tags, text


def get_next_day(day):
    date = datetime.datetime.strptime(day, DATE_FMT)
    next_date = date + datetime.timedelta(days=1)
    next_day = next_date.strftime(DATE_FMT)
    return next_day


async def iterate_on_day_prepared_results(day, sess, sem):
    for day_url in iterate_on_day_base_urls(day):
        async for soup in iterate_on_day_page_soups(day_url, sess, sem):
            for result in iterate_on_parsed_results(soup):
                prepared_result = prepare_result_to_write(result)
                yield prepared_result


def get_days_range(start_day, last_day):
    last_date = datetime.datetime.strptime(last_day, DATE_FMT)
    start_date = datetime.datetime.strptime(start_day, DATE_FMT)

    for delta in range(0, (last_date - start_date).days):
        date = start_date + datetime.timedelta(days=delta)
        day = date.strftime(DATE_FMT)
        yield day


async def crawl_day(day, sess, sem, out_file_path):
    async with aiofiles.open(out_file_path, "w") as f:
        async for result in iterate_on_day_prepared_results(
                day=day, sess=sess, sem=sem
        ):
            await f.write(result)
            await f.flush()

            active_tasks = len(
                [task for task in asyncio.Task.all_tasks() if not task.done()]
            )

            logger.info('Tasks remain: %s' % (active_tasks,))


async def crawl(start_day, last_day, out_file_path, timeout, concurrency):
    connector = aiohttp.TCPConnector()
    timeout = aiohttp.ClientTimeout(total=timeout)
    sem = asyncio.BoundedSemaphore(concurrency)
    days = get_days_range(start_day, last_day)

    async with aiohttp.ClientSession(
            connector=connector, timeout=timeout, headers=_HEADERS
    ) as sess:
        tasks = [
            asyncio.ensure_future(
                crawl_day(day, sess, sem, out_file_path)
            ) for day in days
        ]
        await asyncio.gather(*tasks)


def get_today():
    return datetime.datetime.now().strftime(DATE_FMT)
