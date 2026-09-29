import copy
from functools import update_wrapper
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path
from django.utils.text import slugify


def inject_media(source_media_class, target):
    "Inject media from a source Media class into the target's Media class"

    source_css = getattr(source_media_class, "css", {})
    source_js = getattr(source_media_class, "js", ())
    target_media_class = getattr(target, "Media", None)

    if target_media_class is None:
        # target has no media class. create a new one with a copy of
        # the source media's css and js attributes
        target.Media = type(
            "Media", (), {"css": copy.deepcopy(source_css), "js": copy.deepcopy(source_js)}
        )
    else:
        # target has a media class. merge the source's Media into
        # the target's Media attributes.

        # make sure target has a css attribute
        if not hasattr(target_media_class, "css"):
            target_media_class.css = {}
        for key, source_assets in source_css.items():
            target_assets = target_media_class.css.get(key, ())
            # determine which css files need to be added. we don't want duplicates
            assets_to_add = set(source_assets).difference(set(target_assets))
            merged_assets = tuple(a for a in source_assets if a in assets_to_add) + tuple(
                target_assets
            )
            target_media_class.css[key] = merged_assets

        # make sure target has a js attribute
        if not hasattr(target_media_class, "js"):
            target_media_class.js = ()
        # add any required js to the target Media's js attribute
        assets_to_add = set(source_js).difference(set(target_media_class.js))
        target_media_class.js = tuple(a for a in source_js if a in assets_to_add) + tuple(
            target_media_class.js
        )


class TabbedModelAdmin(admin.ModelAdmin):
    """
    A subclass of ModelAdmin that provides tab support.

    Each tab is backed by its own ModelAdmin, which can be configured via
    the normal ModelAdmin options. All tabs must operate on the same Model
    that the TabbedModelAdmin is registered with.

    The TabbedModelAdmin can be customized to control options on the
    changelist view like normal.

    Requests to the TabbedModelAdmin's add_view or change_view are
    automatically redirected to the first tab's add_view or change_view.

    A working example:

        class TabOne(admin.ModelAdmin):
            fields = ('foo', 'bar')

        class TabTwo(admin.ModelAdmin):
            fields = ('bing', 'baz')

        @admin.register(models.MyModel)
        class MyModelAdmin(TabbedModelAdmin):
            model_admins = (
                ('Tab One Name', TabOne),
                ('Tab Two Name', TabTwo),
            )

    """

    model_admins = []

    class Media:
        css = {"all": ("tabbed_model_admin/css/tabbed_model_admin.css",)}

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)

        app_label = model._meta.app_label
        model_name = model._meta.model_name
        self._model_admins = []

        for name, model_admin in self.model_admins:
            slug = slugify(name)
            inject_media(self.Media, model_admin)
            model_admin = model_admin(model, admin_site)

            self._model_admins.append(
                {
                    "name": name,
                    "slug": slug,
                    "url": f"<path:object_id>/change/{slug}/",
                    "url_name": f"{app_label}_{model_name}_change_{slug}",
                    "model_admin": model_admin,
                }
            )

    def get_urls(self):
        "Include URLs of each tab"

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        urls = []

        for model_admin_info in self._model_admins:
            extra_context = {"current_tab": model_admin_info["slug"], "tabs": self.tabs}
            urls.append(
                path(
                    model_admin_info["url"],
                    wrap(model_admin_info["model_admin"].change_view),
                    name=model_admin_info["url_name"],
                    kwargs={"extra_context": extra_context},
                )
            )

        urls.extend(super().get_urls())
        return urls

    @property
    def tabs(self):
        "Return a list of tab dicts for rendering"
        return [
            {
                "name": model_admin_info["name"],
                "slug": model_admin_info["slug"],
                "url_name": f'admin:{model_admin_info["url_name"]}',
            }
            for model_admin_info in self._model_admins
        ]

    def add_view(self, request, *args, **kwargs):
        "Adding an object should render the first tab's model admin"
        return self._model_admins[0]["model_admin"].add_view(request, *args, **kwargs)

    def changeform_view(self, request, object_id=None, *args, **kwargs):
        "Redirect to the first model admin changeform_view"
        primary_tab_url_name = self._model_admins[0]["url_name"]
        return redirect(f"admin:{primary_tab_url_name}", object_id=object_id)
