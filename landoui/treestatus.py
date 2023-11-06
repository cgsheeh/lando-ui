# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

from itertools import (
    chain,
)
from typing import (
    Optional,
)

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
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
    ReasonCategory,
    TreeStatusLogUpdateForm,
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
        "reason": "test coverage",
        "status": "closed",
        "tags": ["Waiting for coverage"],
        "tree": "mozilla-central",
    },
    "esr102": {
        "log_id": 4,
        "message_of_the_day": "approval is required.",
        "reason": "waiting for some chemspill thing",
        "status": "approval required",
        "tags": ["Planned closure"],
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
                    "current_tags": ["Infrastructure related"],
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
                    "current_tags": ["Infrastructure related"],
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
                    "tags": ["Merges"],
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
                    "tags": ["Merges"],
                },
                "tree": "autoland",
            },
        ],
        "when": "0001-01-01T00:30:00+00:00",
        "who": "ad|Example-LDAP|testuser",
    },
]


def build_recent_changes_stack(
    api: LandoAPI,
) -> list[tuple[TreeStatusRecentChangesForm, dict]]:
    """Build the recent changes stack object."""
    try:
        response = api.request(
            "GET",
            "treestatus/stack",
        )
    except LandoAPIError as exc:
        if not exc.detail:
            raise exc

        return jsonify(errors=errors), 500

    return [
        (
            TreeStatusRecentChangesForm(
                id=change["id"],
                reason=change["reason"],
                reason_category=change["trees"][0]["last_state"]["current_tags"][0],
                who=change["who"],
                when=change["when"],
            ),
            change,
        )
        for change in response["result"]
    ]


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

    trees_response = api.request("GET", "treestatus/trees")
    trees = trees_response.get("result")

    treestatus_select_trees_form.trees.choices = [(tree, tree) for tree in trees.keys()]

    recent_changes_stack = build_recent_changes_stack(api)

    return render_template(
        "treestatus/trees.html",
        recent_changes_stack=recent_changes_stack,
        trees=trees,
        treestatus_select_trees_form=treestatus_select_trees_form,
    )


def new_tree_handler(api: LandoAPI, form: TreeStatusNewTreeForm):
    """Handler for the new tree form."""
    # Retrieve data from the form.
    tree = form.tree.data

    try:
        response = api.request(
            "PUT",
            f"treestatus/trees/{tree}",
            # TODO re-enable auth0 requirement.
            # require_auth0=True,
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

        # TODO better handling
        return jsonify(errors=[exc.detail]), 500

    flash(f"New tree {tree} created successfully.")
    return redirect(url_for("treestatus.treestatus"))


@treestatus_blueprint.route("/treestatus/new_tree/", methods=["GET", "POST"])
def new_tree():
    """View for the new tree form."""
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=get_phabricator_api_token(),
    )
    treestatus_new_tree_form = TreeStatusNewTreeForm()

    if treestatus_new_tree_form.validate_on_submit():
        return new_tree_handler(api, treestatus_new_tree_form)

    recent_changes_stack = build_recent_changes_stack(api)

    return render_template(
        "treestatus/new_tree.html",
        treestatus_new_tree_form=treestatus_new_tree_form,
        recent_changes_stack=recent_changes_stack,
    )


@treestatus_blueprint.route("/treestatus/update", methods=["POST"])
def update_treestatus_form():
    """Web UI for the tree status updating form."""
    token = get_phabricator_api_token()
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=token,
    )
    treestatus_select_trees_form = TreeStatusSelectTreesForm()

    # TODO figure out how to validate this in a better way.
    # if not treestatus_select_trees_form.validate():
    #     errors = list(chain(*treestatus_select_trees_form.errors.values()))
    #     return jsonify(errors=errors), 400

    # Retrieve trees from the selection form.
    trees = treestatus_select_trees_form.trees.data

    treestatus_update_trees_form = TreeStatusUpdateTreesForm()

    # Add each input from the selection form to the update form.
    for tree in trees:
        treestatus_update_trees_form.trees.append_entry(tree)

    recent_changes_stack = build_recent_changes_stack(api)

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

    # Retrieve data from the form.
    trees = treestatus_update_trees_form.trees.data
    status = treestatus_update_trees_form.status.data
    reason = treestatus_update_trees_form.reason.data
    message_of_the_day = treestatus_update_trees_form.message_of_the_day.data
    reason_category = treestatus_update_trees_form.reason_category.data
    remember = treestatus_update_trees_form.remember_this_change.data

    try:
        response = api.request(
            "PATCH",
            "treestatus/trees",
            # TODO re-add auth0 requirement.
            # require_auth0=True,
            json={
                "trees": trees,
                "status": status,
                "reason": reason,
                "message_of_the_day": message_of_the_day,
                "tags": [reason_category],
                "remember": remember,
            },
        )
    except LandoAPIError as exc:
        if not exc.detail:
            raise exc

        errors.append(exc.detail)
        return jsonify(errors=errors), 500

    # Redirect to the main Treestatus page.
    flash("Tree statuses updated successfully.")
    return redirect(url_for("treestatus.treestatus"))


@treestatus_blueprint.route("/treestatus/<tree>/", methods=["GET"])
def treestatus_tree(tree: str):
    """Display the log of statuses for a given tree."""
    token = get_phabricator_api_token()
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=token,
    )

    logs_response = api.request("GET", f"treestatus/trees/{tree}/logs")
    # TODO if we don't get any response we should perhaps render a message/error
    logs = logs_response.get("result") or []

    logs = [
        (
            TreeStatusLogUpdateForm(
                reason=log["reason"],
                # TODO is "No Category" right here?
                reason_category=log["tags"][0] if log["tags"] else ReasonCategory.NO_CATEGORY.value,
            ),
            log,
        )
        for log in logs
    ]

    recent_changes_stack = build_recent_changes_stack(api)

    return render_template(
        "treestatus/log.html",
        logs=logs,
        recent_changes_stack=recent_changes_stack,
        tree=tree,
    )


# TODO test this.
# TODO clearing reason doesn't work here
def build_update_json_body(
    reason: Optional[str], reason_category: Optional[str]
) -> dict:
    """Return a `dict` for use as a JSON body in a log/change update."""
    json_body = {}

    if reason:
        json_body["reason"] = reason

    if reason_category and ReasonCategory.is_valid_reason_category(reason_category):
        json_body["tags"] = [reason_category]

    return json_body


@treestatus_blueprint.route("/treestatus/stack/<int:id>", methods=["POST"])
def update_change(id: int):
    """Handler for stack updates."""
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=get_phabricator_api_token(),
    )
    recent_changes_form = TreeStatusRecentChangesForm()

    restore = recent_changes_form.restore.data
    update = recent_changes_form.update.data
    discard = recent_changes_form.discard.data

    if restore:
        # Restore is a DELETE with a status revert.
        method = "DELETE"
        request_args = {"params": {"revert": 1}}

        flash_message = "Statuses change restored."
    elif discard:
        # Discard is a DELETE without a status revert.
        method = "DELETE"
        request_args = {"params": {"revert": 0}}

        flash_message = "Status change discarded."
    elif update:
        # Update is a PATCH with any changed attributes passed in the body.
        method = "PATCH"

        reason = recent_changes_form.reason.data
        reason_category = recent_changes_form.reason_category.data

        request_args = {"json": build_update_json_body(reason, reason_category)}

        flash_message = "Status change updated."
    else:
        raise Exception("TODO")

    try:
        response = api.request(
            method,
            f"treestatus/stack/{id}",
            # TODO re-enable auth0 requirement.
            # require_auth0=True,
            **request_args,
        )
    except LandoAPIError as exc:
        if not exc.detail:
            raise exc

        return jsonify(errors=[exc.detail]), 500

    flash(flash_message)
    return redirect(request.referrer)


@treestatus_blueprint.route("/treestatus/log/<int:id>", methods=["POST"])
def update_log(id: int):
    """Handler for log updates."""
    api = LandoAPI(
        current_app.config["LANDO_API_URL"],
        auth0_access_token=session.get("access_token"),
        phabricator_api_token=get_phabricator_api_token(),
    )

    log_update_form = TreeStatusLogUpdateForm()

    reason = log_update_form.reason.data
    reason_category = log_update_form.reason_category.data

    json_body = build_update_json_body(reason, reason_category)

    try:
        response = api.request(
            "PATCH",
            f"treestatus/log/{id}",
            json=json_body,
        )
    except LandoAPIError as exc:
        if not exc.detail:
            raise exc

        return jsonify(errors=[exc.detail]), 500

    flash("Log entry updated.")
    return redirect(request.referrer)
