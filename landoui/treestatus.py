# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    session,
)

from landoui.helpers import (
    get_phabricator_api_token,
    is_user_authenticated,
    is_user_authenticated_TODO,
    set_last_local_referrer,
)
from landoui.landoapi import (
    LandoAPI,
)
from landoui.forms import (
    TreeStatusUpdateForm,
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
        "status": "approval required",
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
@treestatus_blueprint.route("/treestatus/", methods=["GET"])
def treestatus():
    """Display the status of all the current trees."""
    token = get_phabricator_api_token()
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=token,
    )

    treestatus_update_form = TreeStatusUpdateForm()

    trees_response = api.request("GET", "treestatus/trees")
    trees = trees_response.get("result")
    if not trees:
        # TODO this should load some error or an error should be added
        # to the trees view.
        # TODO don't use fake trees here
        return render_template(
            "treestatus/trees.html",
            trees=fake_trees,
            treestatus_update_form=treestatus_update_form,
        )

    return render_template(
        "treestatus/trees.html",
        trees=trees,
        treestatus_update_form=treestatus_update_form,
    )


@treestatus_blueprint.route("/treestatus/update", methods=["POST"])
def update_treestatus():
    """Handler for the tree status updating form."""
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=get_phabricator_api_token(),
    )
    treestatus_update_form = TreeStatusUpdateForm()

    return_code = None

    errors = []

    if not treestatus_update_form.is_submitted():
        # TODO fix this.
        return jsonify(errors=[]), 401

    if not is_user_authenticated_TODO():
        # TODO fix this.
        return jsonify(errors=[]), 401

    if not treestatus_update_form.validate():
        for field_errors in treestatus_update_form.errors.values():
            errors.extend(field_errors)
        return jsonify(errors=errors), 400

    try:
        # TODO is this the right way to get data from the form?
        trees = treestatus_update_form.trees.data
        status = treestatus_update_form.status.data
        reason = treestatus_update_form.reason.data
        message_of_the_day = treestatus_update_form.message_of_the_day.data
        tags = treestatus_update_form.tags.data
        remember = treestatus_update_form.remember_this_change.data
    except json.JSONDecodeError as exc:
        raise LandoAPICommunicationException(
            "Landing path could not be decoded as JSON"
        ) from exc

    try:
        response = api.request(
            "PATCH",
            "treestatus/trees",
            require_auth0=True,
            json={
                "trees": [],
                "status": "",
                "reason": "",
                "message_of_the_day": "",
                "tags": [],
                "remember": True,
            },
        )
    except LandoAPIError as exc:
        if not exc.detail:
            raise exc

        errors.append(exc.detail)
        return jsonify(errors=errors), 500

    # TODO make this redirect to the right place.
    return redirect("treestatus")


# TODO doesn't work
@treestatus_blueprint.route("/treestatus/<tree>/", methods=["GET"])
def treestatus_tree(tree: str):
    """Display the log of statuses for a given tree."""
    token = get_phabricator_api_token()
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=token,
    )

    # TODO test this works with real data from API.
    # logs_response = api.request("GET", f"treestatus/trees/{tree}/logs")
    # logs = logs_response.get("result")
    # if not logs:
    #     return render_template("error")

    # TODO use real logs.
    # return render_template("treestatus/log.html", logs=logs)
    return render_template("treestatus/log.html", logs=fake_logs)


# TODO doesn't work
@treestatus_blueprint.route("/treestatus/stack/", methods=["GET"])
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
