# Django Tabbed Model Admin

Give each tab its own Django `ModelAdmin`, form, validation, and save operation,
while editing the same model instance. Extracted from Vortexia's existing tabbed
admin implementation; this is page navigation, not JavaScript fieldset hiding.

## Installation

```sh
pip install django-tabbed-model-admin
```

Place the app **before** `django.contrib.admin` so Django finds its template:

```python
INSTALLED_APPS = [
    "tabbed_model_admin.apps.TabbedModelAdminConfig",
    "django.contrib.admin",
    # ...
]
```

Run `collectstatic` as usual for deployment. No database migrations are needed.

## Usage

```python
from django.contrib import admin
from tabbed_model_admin import TabbedModelAdmin
from .models import Event

class SettingsTab(admin.ModelAdmin):
    fields = ("name", "date")

class AppearanceTab(admin.ModelAdmin):
    fields = ("colour",)

@admin.register(Event)
class EventAdmin(TabbedModelAdmin):
    list_display = ("name", "date")
    model_admins = (
        ("Settings", SettingsTab),
        ("Appearance", AppearanceTab),
    )
```

Do not separately register the tab classes. All tab classes edit the parent model.
The standard add page uses the first tab and does not show navigation until an
object exists. The standard change URL redirects to the first tab. Each tab has
its own URL, `<object_id>/change/<slugified-tab-name>/`, named
`admin:<app_label>_<model_name>_change_<slugified-tab-name>`.

Provide at least one tab and unique, nonempty slugified tab names. The first tab
must support creating the object, including its required fields or defaults.
Each tab saves only its own form and inlines. Save changes before navigating away;
there is no automatic saving or unsaved-change prompt.

Put shared permission checks, queryset restrictions, and save hooks in a common
base class inherited by **every tab**. Options and overrides on the outer admin
control its own views and are not automatically inherited by its tab admins.
The initial release preserves the default `admin` URL namespace.

## Templates and styling

The package extends `admin/change_form.html` and renders tabs in `form_top`.
Project template overrides should preserve `{{ block.super }}` in that block.
CSS ships at `tabbed_model_admin/css/tabbed_model_admin.css`; customize the
`--admin-tabs-active-color`, `--admin-tabs-inactive-color`, and
`--admin-tabs-border-color` CSS variables to match your admin theme.

## Development

```sh
uv venv --python 3.12
uv pip install -e '.[test]'
uv run --no-project pytest
uv build
```

CI tests Django 4.2, 5.2, 6.0, and 6.1. Releases use GitHub Actions trusted
publishing to PyPI from version tags after tests pass.
