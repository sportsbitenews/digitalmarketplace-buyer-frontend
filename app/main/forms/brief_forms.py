from flask_wtf import Form
from wtforms import IntegerField, SelectMultipleField
from wtforms.validators import NumberRange


BRIEF_AWARD_STATUSES = ['awarded', 'cancelled', 'unsuccessful']


class BriefSearchForm(Form):
    page = IntegerField(default=1, validators=(NumberRange(min=1),))
    status = SelectMultipleField("Status", choices=(
        ("live", "Open",),
        ("closed", "Closed",)
    ))
    # lot choices expected to be set at runtime
    lot = SelectMultipleField("Category")

    def __init__(self, *args, **kwargs):
        """
            Requires extra keyword arguments:
             - `framework` - information on the target framework as returned by the api
             - `data_api_client` - a data api client (should be able to remove the need for this arg at some point)
        """
        super(BriefSearchForm, self).__init__(*args, **kwargs)
        try:
            # popping this kwarg so we don't risk it getting fed to wtforms default implementation which might use it
            # as a data field if there were a name collision
            frameworks = kwargs.pop("frameworks")
            self._framework_slug = ",".join(v["slug"] for v in frameworks)
            seen = set()
            self.lot.choices = tuple((v['slug'], v['name']) for f in frameworks
                                     for v in f['lots'] if v['allowsBrief'] and
                                     not (v['slug'] in seen or seen.add(v['slug'])))
        except KeyError:
            raise TypeError("Expected keyword argument 'frameworks' with framework information")
        try:
            # data_api_client argument only needed so we can fit in with the current way the tests mock.patch the
            # the data_api_client directly on the view. would be nice to able to use the global reference to this
            self._data_api_client = kwargs.pop("data_api_client")
        except KeyError:
            raise TypeError("Expected keyword argument 'data_api_client'")

    def get_briefs(self):
        if not self.validate():
            raise ValueError("Invalid form")

        # Treat 'awarded' briefs as closed for filtering purposes, but don't show as a status filter option on the form.
        if self.status.data:
            statuses = self.status.data.copy()
        else:
            statuses = [id_ for id_, label in self.status.choices]
        if 'closed' in statuses:
            statuses.extend(BRIEF_AWARD_STATUSES)

        lots = self.lot.data or tuple(id_ for id_, label in self.lot.choices)

        return self._data_api_client.find_briefs(
            status=",".join(statuses),
            lot=",".join(lots),
            framework=self._framework_slug,
            page=self.page.data,
            human=True,
        )

    def get_filters(self):
        """
            generate the same "filters" structure as expected by search page templates
        """
        if not self.validate():
            raise ValueError("Invalid form")

        return [
            {
                "label": field.label,
                "filters": [
                    {
                        "label": choice_label,
                        "name": field.name,
                        "id": "{}-{}".format(field.id, choice_id),
                        "value": choice_id,
                        "checked": field.data and choice_id in field.data,
                    }
                    for choice_id, choice_label in field.choices
                ],
            }
            for field in (self.lot, self.status,)
        ]

    def filters_applied(self):
        """
            returns boolean indicating whether the results are actually filtered at all
        """
        if not self.validate():
            raise ValueError("Invalid form")

        return bool(self.lot.data or self.status.data)
