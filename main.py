import argparse
import tweepy
import requests
from keys import (
    bearer_token, api_key, api_key_secret, access_token, access_token_secret,
    mastodon_host, mastodon_token
)
from generate_media import generate_animation, generate_text
from get_lightcurve import get_lightcurve
from matplotlib import animation
import matplotlib.pyplot as plt

def test(args):

    lc, lc_info = get_lightcurve(test=not args.r)
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

def mastodon(args):
    mywriter = animation.FFMpegWriter(fps=60)
    lc, lc_info = get_lightcurve()
    status = generate_text(lc_info)
    print("Generating animation...")
    anim = generate_animation(lc, lc_info)
    anim.save('animation.mp4', writer=mywriter)

    print("Posting to Mastodon")
    headers = {'Authorization': f'Bearer {mastodon_token}'}
    response = requests.post(
        f"{mastodon_host}/api/v1/media",
        files={'file': ('animation.mp4', open('animation.mp4', 'rb'), 'application/octet-stream')},
        headers=headers
    ).json()
    media_id = response['id']

    data = {
        "status": status,
        "media_ids[]": [media_id]
    }
    response = requests.post(
        f"{mastodon_host}/api/v1/statuses",
        data=data,
        headers=headers
    ).json()
    print(response['url'])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Exoplanet of the Day")
    parser._positionals.title = "commands"

    subparsers = parser.add_subparsers()
    subparsers.required = True

    # subparser for `test` command
    test_parser = subparsers.add_parser('test', help="generate plot and text only")
    test_parser.add_argument('-r', action='store_true', default=False, help="select random candidate")
    test_parser.set_defaults(func=test)
    # subparser for `twitter` command
    twitter_parser = subparsers.add_parser('twitter', help="plot and post to Twitter")
    twitter_parser.set_defaults(func=twitter)
    # subparser for `mastodon` command
    mastodon_parser = subparsers.add_parser('mastodon', help="plot and post to Mastodon")
    mastodon_parser.set_defaults(func=mastodon)

    args = parser.parse_args()

    args.func(args)
