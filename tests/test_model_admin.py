import pytest
from django.contrib import admin
from django.urls import reverse
from tests.test_app.models import Dummy


pytestmark = pytest.mark.django_db


def test_model_admin_has_tabs():
    """
    A registered TabbedModelAdmin should have a tabs property
    """
    dummy_model_admin = admin.site._registry[Dummy]
    assert dummy_model_admin.tabs == [
        {"name": "Tab One", "slug": "tab-one", "url_name": "admin:test_app_dummy_change_tab-one"},
        {"name": "Tab Two", "slug": "tab-two", "url_name": "admin:test_app_dummy_change_tab-two"},
    ]


def test_add_view_renders_first_tab(admin_client):
    """
    A request to the changeform_view of a TabbedModelAdmin redirects
    to the changeform_view of the first tab.
    """
    dummy_model_admin = admin.site._registry[Dummy]
    tab_1_model_admin = dummy_model_admin._model_admins[0]["model_admin"]

    add_url = reverse("admin:test_app_dummy_add")
    response = admin_client.get(add_url)
    assert response.context_data["adminform"].model_admin == tab_1_model_admin
    # 'tabs' aren't included in the context data when adding a new instance
    assert "tabs" not in response.context_data


def test_change_view_redirects_to_first_tab(admin_client):
    """
    A request to the TabbedModelAdmin's changeview for an existing object
    redirects to the first tab's changeview'
    """
    dummy_model_admin = admin.site._registry[Dummy]
    dummy = Dummy.objects.create()
    original_url = reverse("admin:test_app_dummy_change", kwargs={"object_id": dummy.id})
    tab_url = reverse(dummy_model_admin.tabs[0]["url_name"], kwargs={"object_id": dummy.id})
    response = admin_client.get(original_url)
    assert response.status_code == 302
    assert response.url == tab_url


def test_change_view_renders_tabs(admin_client):
    """
    A rendered changeview template renders tab HTML
    """
    dummy_model_admin = admin.site._registry[Dummy]
    dummy = Dummy.objects.create()
    tab_url = reverse(dummy_model_admin.tabs[0]["url_name"], kwargs={"object_id": dummy.id})
    response = admin_client.get(tab_url)
    content = str(response.content)

    assert "admin-tabs" in content
    for tab in dummy_model_admin.tabs:
        assert tab["name"] in content
        tab_url = reverse(tab["url_name"], kwargs={"object_id": dummy.id})
        assert tab_url in content


def test_second_tab_saves_only_its_fields(admin_client):
    dummy = Dummy.objects.create(field_1=10, field_2=20, field_3=30)
    url = reverse("admin:test_app_dummy_change_tab-two", args=[dummy.pk])
    response = admin_client.post(url, {"field_3": 99, "_continue": "Save"})
    assert response.status_code == 302
    dummy.refresh_from_db()
    assert (dummy.field_1, dummy.field_2, dummy.field_3) == (10, 20, 99)


def test_invalid_tab_does_not_save(admin_client):
    dummy = Dummy.objects.create()
    url = reverse("admin:test_app_dummy_change_tab-two", args=[dummy.pk])
    response = admin_client.post(url, {"field_3": "invalid"})
    assert response.status_code == 200
    assert response.context_data["adminform"].form.errors
    assert response.context_data["current_tab"] == "tab-two"
    dummy.refresh_from_db()
    assert dummy.field_3 == 3


def test_tab_requires_login(client):
    dummy = Dummy.objects.create()
    url = reverse("admin:test_app_dummy_change_tab-two", args=[dummy.pk])
    response = client.get(url)
    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))


def test_tab_enforces_model_permissions(client, django_user_model):
    user = django_user_model.objects.create_user(username="staff", is_staff=True)
    client.force_login(user)
    dummy = Dummy.objects.create()
    url = reverse("admin:test_app_dummy_change_tab-two", args=[dummy.pk])
    assert client.get(url).status_code == 403


def test_tabs_render_inside_form_and_css_is_available(admin_client):
    from django.contrib.staticfiles import finders

    dummy = Dummy.objects.create()
    url = reverse("admin:test_app_dummy_change_tab-two", args=[dummy.pk])
    html = admin_client.get(url).content.decode()
    assert html.index('id="dummy_form"') < html.index('id="admin-tabs"')
    assert 'class="active"><a href="' + url in html
    assert finders.find("tabbed_model_admin/css/tabbed_model_admin.css")
