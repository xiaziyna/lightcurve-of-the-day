import tweepy
import requests
from keys import bearer_token, consumer_key, consumer_secret, access_token, access_token_secret

def main():

    # authorization of consumer key and consumer secret
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    # set access to user's access key and access secret
    auth.set_access_token(access_token, access_token_secret)
    # calling the api
    api = tweepy.API(auth)

    # the text to be tweeted
    status = "This is a media upload."
    # the path of the media to be uploaded
    filename = "cheetos.png"

    # posting the tweet
    api.update_status_with_media(status, filename)

if __name__ == "__main__":

    main()
