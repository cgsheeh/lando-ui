# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import (
    Blueprint,
    current_app,
    render_template,
    session,
)

from landoui.landoapi import (
    LandoAPI,
)
from landoui.helpers import (
    get_phabricator_api_token,
    set_last_local_referrer,
)

treestatus_blueprint = Blueprint("treestatus", __name__)
treestatus_blueprint.before_request(set_last_local_referrer)

fake_trees = {
    "autoland": {
        "log_id": 2,
        "message_of_the_day": "",
        "reason": "",
        "status": "open",
        "tags": [],
        "tree": "autoland",
    },
    "mozilla-central": {
        "log_id": 3,
        "message_of_the_day": "message",
        "reason": "",
        "status": "closed",
        "tags": ["we are CLOSED!"],
        "tree": "mozilla-central",
    },
    "esr102": {
        "log_id": 4,
        "message_of_the_day": "approval is required.",
        "reason": "this is an esr.",
        "status": "approval required",
        "tags": ["ESR release train chooo chooo"],
        "tree": "esr102",
    },
}
fake_logs = [
    {
        "id": 8,
        "reason": "fourth close",
        "status": "closed",
        "tags": ["sometag1"],
        "tree": "tree",
        "when": "0001-01-01T01:20:00+00:00",
        "who": "ad|Example-LDAP|testuser",
    },
    {
        "id": 7,
        "reason": "fourth open",
        "status": "open",
        "tags": [],
        "tree": "tree",
        "when": "0001-01-01T01:10:00+00:00",
        "who": "ad|Example-LDAP|testuser",
    },
    {
        "id": 6,
        "reason": "third close",
        "status": "closed",
        "tags": ["sometag1"],
        "tree": "tree",
        "when": "0001-01-01T01:00:00+00:00",
        "who": "ad|Example-LDAP|testuser",
    },
    {
        "id": 5,
        "reason": "third open",
        "status": "open",
        "tags": [],
        "tree": "tree",
        "when": "0001-01-01T00:50:00+00:00",
        "who": "ad|Example-LDAP|testuser",
    },
    {
        "id": 4,
        "reason": "second close",
        "status": "closed",
        "tags": ["sometag1"],
        "tree": "tree",
        "when": "0001-01-01T00:40:00+00:00",
        "who": "ad|Example-LDAP|testuser",
    },
]


# TODO doesn't work
@treestatus_blueprint.route("/treestatus", methods=["GET"])
def treestatus():
    """Display the status of all the current trees."""
    token = get_phabricator_api_token()
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=token,
    )

    trees_response = api.request("GET", "treestatus/trees")
    trees = trees_response.get("result")
    if not trees:
        # TODO this should load some error or an error should be added
        # to the trees view.
        # TODO don't use fake trees here
        return render_template("treestatus/trees.html", trees=fake_trees)

    return render_template("treestatus/trees.html", trees=trees)


# TODO doesn't work
@treestatus_blueprint.route("/treestatus/<tree>", methods=["GET"])
def treestatus_tree(tree: str):
    """Display the log of statuses for a given tree."""
    token = get_phabricator_api_token()
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=token,
    )

    # TODO make this work without fake data.
    # tree_response = api.request("GET", f"treestatus/trees/{tree}/logs_all")
    # tree = tree_response.get("result")
    # if not tree:
    #     return render_template("error")

    return render_template("treestatus/log.html", logs=fake_logs)


# TODO doesn't work
@treestatus_blueprint.route("/treestatus/stack", methods=["GET"])
def treestatus_stack():
    """Display the current change stack."""
    token = get_phabricator_api_token()
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=token,
    )

    # TODO is the API endpoint correct here?
    stack_response = api.request("GET", "treestatus/stack")
    stack = stack_response.get("result")
    if not stack:
        # TODO how to render an error correctly?
        return render_template("error")

    return render_template("treestatus/stack.html")
