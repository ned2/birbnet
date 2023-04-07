# birbnet
Twitter network graph analytics

## Installing

After cloning the repo, creating and activating a Python 3.11 virtual
environment, run the following command from within the top level of the repo:

    pip install .

The following optional dependencies are also available:

    pip install .[analysis] # deps for an analysis environment
    pip install .[dev]      # deps for development on this package


Alternatively, you can first install the pinned deps for all optional
dependencies, (`-e` provides an editable install):

    pip install -r requirements-all.txt
    pip install -e .


## Configuring

To interact with the Twitter API, you'll need a sign up for a developer account
and generate a bearer token to authenticate requests to the API. See the
[Twitter developer
docs](https://developer.twitter.com/en/docs/authentication/oauth-2-0/bearer-tokens)
for details.

Then set this environment variable:

    export BIRBNET_TWITTER_BEARER_TOKEN=<your-bearer-token>

Other (optional) configuration is available through these environment variables:

- `BIRBNET_TWITTER_USER_ID`: The ID of the Twitter user to start crawls at by default.
- `BIRBNET_DATA_PATH`: The path to. Will default to `~/birbnet_data` if not set.

See `src/birbnet/config.py` for crawler defaults that can be set globally across
the tool.


## Usage

To run the crawler at a depth of 3, in the output directory with name `crawl_run`:

    birbnet get-users --run-id crawl_run --depth 3

Note that by default, this command will resume where it left off, re-hydrating
the current state of the crawl from any existing output in crawl run directory.

For documentation of this command:

    `birbnet get-users --help`

To get statistics for the output of an existing run, optionally saving granular
stats with the number of unique nodes and edges added with each crawled user to
a Parquet file with the `--stats-path` flag:

    birbnet crawl-stats <path-to-run-output> (--stats-path <path-to-output>>)


## Updating pinned deps

    pip install pip-tools
    pip-compile -U --resolver=backtracking --extra dev --extra analysis -o requirements-all.txt pyproject.toml
