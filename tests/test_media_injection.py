from tabbed_model_admin.admin import inject_media


def test_target_media_class_created_when_none_exists():
    """
    A Media object is created on the target ModelAdmin with a copy
    of the source Media when the target doesn't already have a Media class
    """

    class Source:
        class Media:
            css = {"all": ("foo.css", "bar.css")}
            js = ("foo.js", "bar.js")

    class Target:
        pass

    inject_media(Source.Media, Target)

    assert hasattr(Target, "Media")
    assert Target.Media.css == Source.Media.css
    assert Target.Media.js == Source.Media.js


def test_target_media_with_no_css_attribute():
    """
    If the target has a Media class that doesn't define a css attribute,
    the source's entire css is injected onto the target's Media.
    """

    class Source:
        class Media:
            css = {"all": ("foo.css", "bar.css")}

    class Target:
        class Media:
            js = ("foo.js", "bar.js")

    inject_media(Source.Media, Target)

    assert Target.Media.css == Source.Media.css
    assert Target.Media.js == ("foo.js", "bar.js")


def test_target_media_with_no_js_attribute():
    """
    If the target has a Media class that doesn't define a js attribute,
    the source's entire js is injected onto the target's Media.
    """

    class Source:
        class Media:
            js = ("foo.js", "bar.js")

    class Target:
        class Media:
            css = {"all": ("foo.css", "bar.css")}

    inject_media(Source.Media, Target)

    assert Target.Media.css == {"all": ("foo.css", "bar.css")}
    assert Target.Media.js == Source.Media.js


def test_target_media_with_existing_css_attribute():
    """
    If the target has a Media class with a css attribute, the source's
    css is injected ahead of the target's css with duplicate assets removed.
    """

    class Source:
        class Media:
            css = {"all": ("foo.css", "bar.css"), "mobile": ("small.css", "tiny.css")}

    class Target:
        class Media:
            css = {"all": ("target.css", "foo.css")}

    inject_media(Source.Media, Target)

    assert Target.Media.css == {
        "all": ("bar.css", "target.css", "foo.css"),
        "mobile": ("small.css", "tiny.css"),
    }


def test_target_media_with_existing_js_attribute():
    """
    If the target has a Media class with a js attribute, the source's
    js is injected ahead of the target's js with duplicate assets removed.
    """

    class Source:
        class Media:
            js = ("foo.js", "bar.js")

    class Target:
        class Media:
            js = ("target.js", "foo.js")

    inject_media(Source.Media, Target)

    assert Target.Media.js == ("bar.js", "target.js", "foo.js")
