# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import enum
import json

from json.decoder import JSONDecodeError
from typing import (
    Optional,
    Type,
)

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    Field,
    FieldList,
    HiddenField,
    IntegerField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
    ValidationError,
    widgets,
)
from wtforms.validators import (
    DataRequired,
    InputRequired,
    Regexp,
    optional,
)

TREESTATUS_CHOICES = [
    ("open", "Open"),
    ("closed", "Closed"),
    ("approval required", "Approval Required"),
]

# from landoui.template_helpers import treestatus_to_status_badge_class


class JSONDecodable:
    def __init__(
        self, decode_type: Optional[Type] = None, message: Optional[str] = None
    ):
        self.decode_type = decode_type
        self.message = message or "Field must be JSON decodable"

    def __call__(self, form: FlaskForm, field: Field):
        try:
            decoded = json.loads(field.data)
        except JSONDecodeError:
            raise ValidationError(self.message)

        if self.decode_type is not None and not isinstance(decoded, self.decode_type):
            raise ValidationError(self.message)

        return decoded


class LandingPath(JSONDecodable):
    def __init__(self, message: Optional[str] = None):
        super().__init__(decode_type=list, message=message)

    def __call__(self, form: FlaskForm, field: Field):
        decoded = super().__call__(form, field)

        if len(decoded) < 1:
            raise ValidationError(self.message)

        for i in decoded:
            if not (
                len(i) == 2
                and "revision_id" in i
                and isinstance(i["revision_id"], str)
                and "diff_id" in i
                and isinstance(i["diff_id"], int)
            ):
                raise ValidationError(self.message)


class TransplantRequestForm(FlaskForm):
    landing_path = HiddenField(
        "landing_path",
        validators=[
            InputRequired(message="A landing path is required"),
            LandingPath(message="Landing path must be a JSON array of path objects"),
        ],
    )
    confirmation_token = HiddenField("confirmation_token")
    flags = HiddenField(
        "flags", validators=[JSONDecodable(decode_type=list)], default=[]
    )


class SecApprovalRequestForm(FlaskForm):
    new_message = TextAreaField(
        "new_message",
        validators=[InputRequired(message="A valid commit message must be provided")],
    )
    revision_id = StringField(
        "revision_id",
        validators=[
            InputRequired(message="A valid Revision monogram must be provided"),
            Regexp("^D[0-9]+$"),
        ],
    )


class UpliftRequestForm(FlaskForm):
    """Form used to request uplift of a stack."""

    revision_id = StringField(
        "revision_id",
        validators=[
            InputRequired(message="A valid Revision monogram must be provided"),
            Regexp("^D[0-9]+$"),
        ],
    )
    repository = SelectField(
        "repository",
        coerce=str,
        validators=[
            InputRequired("An uplift repository is required."),
        ],
    )


class UserSettingsForm(FlaskForm):
    """Form used to provide the Phabricator API Token."""

    phab_api_token = StringField(
        "Phabricator API Token",
        validators=[
            optional(),
            Regexp("^api-[a-z0-9]{28}$", message="Invalid API Token format"),
        ],
    )
    reset_phab_api_token = BooleanField("Delete", default="")


class ReasonCategory(enum.Enum):
    """Allowable reasons for a Tree closure."""

    NO_CATEGORY = "No Category"
    JOB_BACKLOG = "Job Backlog"
    CHECKIN_COMPILE_FAILURE = "Check-in compilation failure"
    CHECKIN_TEST_FAILURE = "Check-in test failure"
    PLANNED_CLOSURE = "Planned closure"
    MERGES = "Merges"
    WAITING_FOR_COVERAGE = "Waiting for coverage"
    INFRASTRUCTURE_RELATED = "Infrastructure related"
    OTHER = "Other"

    @classmethod
    def to_choices(cls) -> list[tuple[str, str]]:
        """Return a list of choices for display."""
        return [(choice.value, choice.value) for choice in list(cls)]


def tree_table_widget(field, trees: dict[str, dict], **kwargs) -> str:
    """Render a table with checkbox elements as a selection."""
    kwargs.setdefault("type", "checkbox")
    field_id = kwargs.pop("id", field.id)

    html = []

    for value, label, checked in field.iter_choices():
        tree = trees[value]

        options = dict(
            kwargs,
            class_="tree-select-checkbox",
            name=field.name,
            value=value,
            id=field_id,
        )
        checkbox_options = widgets.html_params(**options)
        row = (
            "<tr>"
            f"<td><input {checkbox_options} /></td>"
            f'<td><a href="{value}">{value}</a></td>'
            # TODO resolve this dependency loop
            # f'<td><span class="{treestatus_to_status_badge_class(tree["status"])}">{tree["status"]}</span></td>'
            f'<td><span class="{tree["status"]}">{tree["status"]}</span></td>'
            f"<td>{tree['reason']}</td>"
            f"<td>{', '.join(tree['tags'])}</td>"
            f"<td>{tree['message_of_the_day']}</td>"
            "</tr>"
        )
        html.append(row)

    return "\n".join(html)


class TableSelectWidget(widgets.TableWidget):
    def __call__(self, field, trees=None, **kwargs):
        return tree_table_widget(field, trees=trees)


class MultiCheckboxField(SelectMultipleField):
    """Multiple select with a series of checkboxes."""

    widget = TableSelectWidget()


class TreeStatusSelectTreesForm(FlaskForm):
    """Form used to select trees for updating."""

    trees = MultiCheckboxField(
        # TODO this isn't properly checking the data is passed as I cna still pass empty trees.
        "Trees",
        validators=[DataRequired("A selection of trees is required.")],
    )


class TreeStatusUpdateTreesForm(FlaskForm):
    """Form used to update the state of a selection of trees."""

    trees = FieldList(
        StringField(
            "Trees",
            validators=[InputRequired("A selection of trees is required.")],
            widget=widgets.HiddenInput(),
        )
    )

    status = SelectField(
        "Status",
        choices=TREESTATUS_CHOICES,
        validators=[InputRequired("A status is required.")],
    )

    # TODO this field is only required when status != "open"
    reason = StringField("Reason", validators=[InputRequired("A reason is required.")])

    reason_category = SelectField(
        "Reason Category",
        choices=ReasonCategory.to_choices(),
        validators=[InputRequired("A reason category is required.")],
    )

    remember_this_change = BooleanField(
        "Remember",
        default=True,
    )

    message_of_the_day = StringField("Message of the day")


class TreeStatusNewTreeForm(FlaskForm):
    """Add a new tree to Treestatus."""

    tree = StringField("Tree", validators=[InputRequired("A tree name is required.")])


class TreeStatusRecentChangesForm(FlaskForm):
    """Modify a recent status change."""

    id = HiddenField("Id", validators=[InputRequired("An ID is required.")])

    reason = StringField("Reason")

    reason_category = SelectField(
        "Reason Category",
        choices=ReasonCategory.to_choices(),
        validators=[InputRequired("A reason category is required.")],
    )

    restore = SubmitField("Restore")

    update = SubmitField("Update")

    discard = SubmitField("Discard")
