from django.contrib import admin
from tabbed_model_admin import TabbedModelAdmin
from tests.test_app.models import Dummy


class Tab1(admin.ModelAdmin):
    fieldsets = ((None, {"fields": ("field_1", "field_2")}),)


class Tab2(admin.ModelAdmin):
    fieldsets = ((None, {"fields": ("field_3",)}),)


@admin.register(Dummy)
class DummyModelAdmin(TabbedModelAdmin):
    model_admins = [("Tab One", Tab1), ("Tab Two", Tab2)]
