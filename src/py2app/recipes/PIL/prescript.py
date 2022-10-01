# Recipe assumes users migrated to
# "Pillow" which always installs as
# "PIL.Image"


def _recipes_pil_prescript(plugins: "list[str]") -> None:
    import sys

    from PIL import Image

    def init() -> None:
        if Image._initialized >= 2:  # type: ignore
            return

        try:
            import PIL.JpegPresets

            sys.modules["JpegPresets"] = PIL.JpegPresets
        except ImportError:
            pass

        for plugin in plugins:
            try:
                try:
                    # First try absolute import through PIL (for
                    # Pillow support) only then try relative imports
                    m = __import__("PIL." + plugin, globals(), locals(), [])
                    m = getattr(m, plugin)
                    sys.modules[plugin] = m
                    continue
                except ImportError:
                    pass

                __import__(plugin, globals(), locals(), [])
            except ImportError:
                print("Image: failed to import")

        if Image.OPEN or Image.SAVE:
            Image._initialized = 2  # type: ignore
            return
        return

    Image.init = init
