#!/Library/Frameworks/Python.framework/Versions/Current/bin/python
import tweepy
import sys

consumer_key='JnYy8IjOAthUtSEQmXYeg'
consumer_secret='ORmxgR56WH2IhvJ8p3BbB3BGnulAhFVMyUM98zhUc'
access_token='899267120-Blr95aJyIWbmqL6AKyGH4KsfZZXsXkErbnc8wuOa'
access_secret='vxcXCQ6djUWBtXeWpWBXlUJD2CNUrkMnmXPaTYhzI'

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)

text = " ".join(sys.argv[1:])

if not text:
    print("Usage: divtweet [username] this is my status update")
api.update_status(text)


