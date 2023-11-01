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
    LandoAPIError,
)
from landoui.forms import (
    TreeStatusNewTreeForm,
    TreeStatusRecentChangesForm,
    TreeStatusSelectTreesForm,
    TreeStatusUpdateTreesForm,
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
fake_stack = [
    {
        "id": 2,
        "reason": "hgmo is busted.",
        "status": "closed",
        "trees": [
            {
                "id": 1,
                "last_state": {
                    "current_log_id": 1,
                    "current_reason": "hgmo is busted",
                    "current_status": "closed",
                    "current_tags": ["sometag1", "sometag2"],
                    "log_id": None,
                    "reason": "",
                    "status": "open",
                    "tags": [],
                },
                "tree": "mozilla-central",
            },
            {
                "id": 2,
                "last_state": {
                    "current_log_id": 2,
                    "current_reason": "hgmo is busted",
                    "current_status": "closed",
                    "current_tags": ["sometag1", "sometag2"],
                    "log_id": None,
                    "reason": "",
                    "status": "open",
                    "tags": [],
                },
                "tree": "autoland",
            },
        ],
        "when": "0001-01-01T00:30:00+00:00",
        "who": "ad|Example-LDAP|testuser",
    },
    {
        "id": 1,
        "reason": "",
        "status": "open",
        "trees": [
            {
                "id": 1,
                "last_state": {
                    "current_log_id": 1,
                    "current_reason": "",
                    "current_status": "open",
                    "current_tags": [],
                    "log_id": None,
                    "reason": "merging",
                    "status": "approval required",
                    "tags": [],
                },
                "tree": "mozilla-central",
            },
            {
                "id": 2,
                "last_state": {
                    "current_log_id": 2,
                    "current_reason": "",
                    "current_status": "open",
                    "current_tags": [],
                    "log_id": None,
                    "reason": "merging",
                    "status": "approval required",
                    "tags": [],
                },
                "tree": "autoland",
            },
        ],
        "when": "0001-01-01T00:30:00+00:00",
        "who": "ad|Example-LDAP|testuser",
    },
]


def build_recent_changes_stack() -> list[tuple[TreeStatusRecentChangesForm, dict]]:
    """Build the recent changes stack object."""
    return [
        (
            TreeStatusRecentChangesForm(
                id=change["id"],
                reason=change["reason"],
                # reason_category=change["tags"],
                who=change["who"],
                when=change["when"],
            ),
            change,
        )
        for change in fake_stack
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

    treestatus_select_trees_form = TreeStatusSelectTreesForm()

    # trees_response = api.request("GET", "treestatus/trees")
    # trees = trees_response.get("result")
    trees = fake_trees
    treestatus_select_trees_form.trees.choices = [(tree, tree) for tree in trees.keys()]

    recent_changes_stack = build_recent_changes_stack()

    return render_template(
        "treestatus/trees.html",
        recent_changes_stack=recent_changes_stack,
        trees=trees,
        treestatus_select_trees_form=treestatus_select_trees_form,
    )


@treestatus_blueprint.route("/treestatus/new_tree/", methods=["POST"])
def new_tree_handler():
    """Handler for the new tree form."""
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=get_phabricator_api_token(),
    )
    treestatus_new_tree_form = TreeStatusNewTreeForm()

    # Retrieve data from the form.
    tree = treestatus_new_tree_form.tree.data

    return {"tree": tree}, 200

    # TODO test this actually works with the API.
    try:
        response = api.request(
            "PUT",
            f"treestatus/trees/{tree}",
            require_auth0=True,
            json={
                "tree": tree,
                # Trees are open on creation.
                "status": "open",
                "reason": "",
                "message_of_the_day": "",
            },
        )
    except LandoAPIError as exc:
        if not exc.detail:
            raise exc

        return jsonify(errors=[exc.detail]), 500

    # TODO what to return here? reirect to another page?
    return jsonify(
        returned=[
            {
                "tree": tree,
                "status": status,
                "reason": reason,
                "motd": message_of_the_day,
            }
        ]
    )


@treestatus_blueprint.route("/treestatus/new_tree/", methods=["GET"])
def new_tree():
    """View for the new tree form."""
    treestatus_new_tree_form = TreeStatusNewTreeForm()

    recent_changes_stack = build_recent_changes_stack()

    return render_template(
        "treestatus/new_tree.html",
        treestatus_new_tree_form=treestatus_new_tree_form,
        recent_changes_stack=recent_changes_stack,
    )


@treestatus_blueprint.route("/treestatus/update", methods=["POST"])
def update_treestatus_form():
    """Web UI for the tree status updating form."""
    treestatus_select_trees_form = TreeStatusSelectTreesForm()

    # Retrieve trees from the selection form.
    trees = treestatus_select_trees_form.trees.data

    treestatus_update_trees_form = TreeStatusUpdateTreesForm()

    # Add each input from the selection form to the update form.
    for tree in trees:
        treestatus_update_trees_form.trees.append_entry(tree)

    recent_changes_stack = build_recent_changes_stack()

    return render_template(
        "treestatus/update_trees.html",
        recent_changes_stack=recent_changes_stack,
        treestatus_update_trees_form=treestatus_update_trees_form,
    )


@treestatus_blueprint.route("/treestatus/update_handler", methods=["POST"])
def update_treestatus():
    """Handler for the tree status updating form."""
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=get_phabricator_api_token(),
    )
    treestatus_update_trees_form = TreeStatusUpdateTreesForm()

    errors = []

    if not is_user_authenticated_TODO():
        # TODO fix this.
        return jsonify(errors=["Not authenticated."]), 401

    # if not treestatus_select_trees_form.validate():
    #     for field_errors in treestatus_select_trees_form.errors.values():
    #         errors.extend(field_errors)
    #     return jsonify(errors=errors), 400

    # Retrieve data from the form.
    trees = treestatus_update_trees_form.trees.data
    status = treestatus_update_trees_form.status.data
    reason = treestatus_update_trees_form.reason.data
    message_of_the_day = treestatus_update_trees_form.message_of_the_day.data
    tags = treestatus_update_trees_form.tags.data
    remember = treestatus_update_trees_form.remember_this_change.data

    return {
        "trees": treestatus_update_trees_form.trees.data,
        "status": treestatus_update_trees_form.status.data,
        "reason": treestatus_update_trees_form.reason.data,
        "message_of_the_day": treestatus_update_trees_form.message_of_the_day.data,
        "tags": treestatus_update_trees_form.tags.data,
        "remember": treestatus_update_trees_form.remember_this_change.data,
    }, 200

    try:
        response = api.request(
            "PATCH",
            "treestatus/trees",
            require_auth0=True,
            json={
                "trees": trees,
                "status": status,
                "reason": reason,
                "message_of_the_day": message_of_the_day,
                "tags": tags,
                "remember": remember,
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

    recent_changes_stack = build_recent_changes_stack()

    # TODO use real logs.
    # return render_template("treestatus/log.html", logs=logs)
    return render_template(
        "treestatus/log.html",
        logs=fake_logs,
        recent_changes_stack=recent_changes_stack,
        tree=tree,
    )


@treestatus_blueprint.route("/treestatus/stack/<int:id>", methods=["PATCH"])
def patch_stack(id: int):
    """Handler for stack updates."""
    return jsonify({"id": id}), 200
