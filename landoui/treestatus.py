# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from flask import (
    current_app,
    render_template,
    session,
)

from landoui.landoapi import (
    LandoAPI,
    LandoAPICommunicationException,
    LandoAPIError,
)
from landoui.helpers import (
    get_phabricator_api_token,
)
from landoui.pages import pages


@pages.route("/treestatus", methods=["GET"])
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
        return render_template("treestatus/trees.html")

    return render_template("treestatus/trees.html", trees=trees)


@pages.route("/treestatus/{tree}", methods=["GET"])
def treestatus_tree(tree: str):
    """Display the log of statuses for a given tree."""
    token = get_phabricator_api_token()
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=token,
    )

    tree_response = api.request("GET", f"treestatus/trees/{tree}")
    tree = tree_response.get("result")
    if not tree:
        return render_template("error")

    return render_template("treestatus/tree.html", tree=tree)
