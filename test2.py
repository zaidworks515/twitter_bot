from twitter_functions import get_news

data = get_news(last_category='AI')
article = None

if data:
    article = data[0]
    article_category = data[1]
    print(article)


if not article:
    print("No articles found for the given category.")
