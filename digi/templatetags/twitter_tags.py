import tweepy
from django import template
from django.conf import settings

from digi.utils import get_cached_with_mtime

TWEET_CACHE_REFRESH_AGE = 60 * 15  # if tweets are 15 minutes old, attempt reload

register = template.Library()


def get_tweepy_api():
    auth = tweepy.OAuthHandler(
        consumer_key=settings.TWITTER_CONSUMER_KEY,
        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
    )
    auth.set_access_token(
        key=settings.TWITTER_ACCESS_TOKEN,
        secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
    )
    return tweepy.API(auth)


@register.simple_tag()
def twitter_search(query):
    """
    Search Twitter for the given query and result results
    :param query:
    :type query:
    :return:
    :rtype:
    """
    return get_cached_with_mtime(
        cache_key='twitter_%s' % query,
        max_mtime=TWEET_CACHE_REFRESH_AGE,
        getter=lambda: get_tweepy_api().search(q=query, rpp=100, result_type='recent'),
        default=[],
    )
