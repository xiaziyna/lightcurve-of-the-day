import argparse
import tweepy
from keys import bearer_token, api_key, api_key_secret, access_token, access_token_secret
from generate_media import generate_animation, generate_text
from get_lightcurve import get_lightcurve
from matplotlib import animation
import matplotlib.pyplot as plt

def test(args):

    lc, lc_info = get_lightcurve(test=True)
    print(generate_text(lc_info))
    anim = generate_animation(lc, lc_info)
    plt.show()


def twitter(args):
    mywriter = animation.FFMpegWriter(fps=60)
    lc, lc_info = get_lightcurve()
    status = generate_text(lc_info)
    print("Generating animation...")
    anim = generate_animation(lc, lc_info)
    anim.save('animation.mp4', writer=mywriter)

    print("Posting to Twitter")
    auth = tweepy.OAuthHandler(api_key, api_key_secret)
    # set access to user's access key and access secret
    auth.set_access_token(access_token, access_token_secret)
    # calling the api
    api = tweepy.API(auth)

    # posting the tweet
    media = api.media_upload('animation.mp4', media_category='tweet_video')
    tweetinfo = api.update_status(status=status, media_ids=[media.media_id])
    print(tweetinfo._json['entities']['urls'][0]['expanded_url'])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Exoplanet of the Day")
    parser._positionals.title = "commands"

    subparsers = parser.add_subparsers()
    subparsers.required = True

    # subparser for `add` command
    test_parser = subparsers.add_parser('test', help="generate plot and text only")
    test_parser.set_defaults(func=test)
    twitter_parser = subparsers.add_parser('twitter', help="plot and post to Twitter")
    twitter_parser.set_defaults(func=twitter)

    args = parser.parse_args()

    args.func(args)
